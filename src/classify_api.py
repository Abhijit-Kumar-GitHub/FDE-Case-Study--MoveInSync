"""Production runner for the classification step: Claude Sonnet 5.5 via the
Message Batches API (50% cheaper; a daily/weekly job is not latency-sensitive).

Same prompt and codes as the Claude Code skill (prompts/classify_v1.md +
prompts/schema.json); same chunk format and validation as src/labels_io.py.

  python src/classify_api.py --dry-run   # build the batch, print tokens and cost; no key needed
  python src/classify_api.py             # needs ANTHROPIC_API_KEY; aborts above config.API_BUDGET_USD

Not executed in this submission (no API key was available): the dry run and the
response parser are tested; the live call follows the SDK docs.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
import labels_io  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PROMPT = (ROOT / "prompts" / "classify_v1.md").read_text(encoding="utf-8").split("\n---\n", 1)[1]
SCHEMA = json.loads((ROOT / "prompts" / "schema.json").read_text(encoding="utf-8"))

PRICE_IN, PRICE_OUT = 2.00, 10.00          # Claude Sonnet 5.5, USD per million tokens
BATCH_DISCOUNT = 0.5
CHARS_PER_TOKEN = 4                         # rough; good enough for a budget guard
OUT_TOKENS_PER_REVIEW = 40
REVIEWS_PER_REQUEST = 100


def system_prompt():
    codes = "\n".join(f"- {k}: {v}" for k, v in SCHEMA["codes"]["stages"].items())
    attr = "\n".join(f"- {k}: {v}" for k, v in SCHEMA["codes"]["attribution"].items())
    return f"{PROMPT}\n\n## Stage codes\n{codes}\n\n## Attribution codes\n{attr}\n"


def build_requests(chunks):
    """chunks: list of (name, [line dicts]) -> Message Batches request dicts."""
    sys_prompt = system_prompt()
    reqs = []
    for name, lines in chunks:
        body = "\n".join(json.dumps(l, ensure_ascii=False) for l in lines)
        reqs.append({
            "custom_id": name,
            "params": {
                "model": config.API_MODEL,
                "max_tokens": max(2000, OUT_TOKENS_PER_REVIEW * len(lines) * 2),
                # Classification needs no extended reasoning: Sonnet 5.5 turns thinking off
                # with "between_tools" (accepted at effort high or below).
                "thinking": {"type": "between_tools"},
                "output_config": {"effort": "low",
                                  "format": {"type": "json_schema", "schema": SCHEMA["json_schema"]}},
                "system": sys_prompt,
                "messages": [{"role": "user", "content": f"Label every review in this chunk.\n\n{body}"}],
            },
        })
    return reqs


def estimate(reqs):
    tin = sum((len(r["params"]["system"]) + len(r["params"]["messages"][0]["content"])) / CHARS_PER_TOKEN for r in reqs)
    n_reviews = sum(r["params"]["messages"][0]["content"].count('"i":') for r in reqs)
    tout = n_reviews * OUT_TOKENS_PER_REVIEW
    usd = (tin * PRICE_IN + tout * PRICE_OUT) / 1e6 * BATCH_DISCOUNT
    return {"requests": len(reqs), "reviews": n_reviews, "input_tokens": int(tin), "output_tokens": int(tout), "usd": round(usd, 3)}


def parse_message(message):
    """Return (labels, problem). `message` is a Messages API response object."""
    if getattr(message, "stop_reason", None) == "refusal":
        return [], "refusal"
    if getattr(message, "stop_reason", None) == "max_tokens":
        return [], "truncated"
    text = next((b.text for b in message.content if getattr(b, "type", "") == "text"), "")
    try:
        return json.loads(text)["labels"], None
    except (json.JSONDecodeError, KeyError) as exc:
        return [], f"unparseable: {exc}"


def pending_chunks():
    """Export new work into the shared queue, then read back the chunks that have no labels yet."""
    labels_io.export(config.LABEL_WINDOW_DAYS, older_per_month=0, chunk_size=REVIEWS_PER_REQUEST)
    out = []
    for f in sorted(labels_io.QUEUE.glob("chunk_*.jsonl")):
        if f.name.endswith(".labels.jsonl") or (labels_io.QUEUE / f"{f.stem}.labels.jsonl").exists():
            continue
        out.append((f.stem, [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]))
    return out


def what_if_chunks(days):
    """In-memory chunks for every written review in the last `days` days — prices a full
    relabel without touching the queue."""
    import pandas as pd
    df = pd.read_csv(labels_io.RAW / f"{config.PRIMARY_APP}.csv", parse_dates=["at"])
    df = df[df["at"] >= df["at"].max() - pd.Timedelta(days=days)]
    df = df[df["content"].fillna("").str.strip().str.len() > 0]
    lines = [{"i": i + 1, "s": int(r.score), "t": " ".join(str(r.content).split())[:labels_io.MAX_TEXT]}
             for i, r in enumerate(df.itertuples())]
    return [(f"whatif_{k // REVIEWS_PER_REQUEST:03d}", lines[k:k + REVIEWS_PER_REQUEST])
            for k in range(0, len(lines), REVIEWS_PER_REQUEST)]


def run(dry_run=False, what_if_days=None):
    chunks = what_if_chunks(what_if_days) if what_if_days else pending_chunks()
    if not chunks:
        print("nothing new to label")
        return
    reqs = build_requests(chunks)
    est = estimate(reqs)
    print(f"{est['reviews']} reviews in {est['requests']} requests -> ~{est['input_tokens']:,} input + "
          f"~{est['output_tokens']:,} output tokens -> ~${est['usd']} ({config.API_MODEL}, Batch API)")
    if dry_run:
        return est
    if est["usd"] > config.API_BUDGET_USD:
        sys.exit(f"estimated ${est['usd']} exceeds budget ${config.API_BUDGET_USD}; raise API_BUDGET_USD to proceed")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY not set — use the rules fallback or the /label-reviews skill")

    import anthropic  # optional dependency, only needed for live runs

    client = anthropic.Anthropic()
    batch = client.messages.batches.create(requests=reqs)
    print(f"batch {batch.id} submitted")
    while True:
        batch = client.messages.batches.retrieve(batch.id)
        if batch.processing_status == "ended":
            break
        time.sleep(30)
    problems = []
    for result in client.messages.batches.results(batch.id):  # results arrive in any order: key by custom_id
        if result.result.type != "succeeded":
            problems.append((result.custom_id, result.result.type))
            continue
        labels, problem = parse_message(result.result.message)
        if problem:
            problems.append((result.custom_id, problem))  # refused/garbled chunks stay pending -> skill or rules + human queue
            continue
        path = labels_io.QUEUE / f"{result.custom_id}.labels.jsonl"
        path.write_text("\n".join(json.dumps(l, ensure_ascii=False) for l in labels) + "\n", encoding="utf-8")
    labels_io.import_labels(labeller=f"{config.API_MODEL} (Batch API)")
    if problems:
        print("chunks needing attention:", problems)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--what-if-days", type=int, help="price relabelling every review from the last N days (implies --dry-run)")
    a = p.parse_args()
    run(dry_run=a.dry_run or bool(a.what_if_days), what_if_days=a.what_if_days)
