"""Move reviews in and out of the labelling step, whoever does the labelling.

  export   writes unlabelled reviews into numbered chunks (short local ids keep
           the labeller's output small) under data/labels/queue/
  import   validates every *.labels.jsonl against prompts/schema.json codes and
           appends good rows to data/labels/llm_labels.csv
  status   shows what is labelled, pending, and invalid

The same chunk format feeds the Claude Code skill (.claude/skills/label-reviews)
and the production API runner (src/classify_api.py).
"""
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
LABELS = ROOT / "data" / "labels"
QUEUE = LABELS / "queue"
LLM_LABELS = LABELS / "llm_labels.csv"
OVERRIDES = LABELS / "human_overrides.csv"
SCHEMA = json.loads((ROOT / "prompts" / "schema.json").read_text(encoding="utf-8"))

STAGES = set(SCHEMA["codes"]["stages"])
ATTRIBUTION = set(SCHEMA["codes"]["attribution"])
SENTIMENT = set(SCHEMA["codes"]["sentiment"])
PROMPT_VERSION = SCHEMA["prompt_version"]
MAX_TEXT = 700


def labelled_ids():
    if not LLM_LABELS.exists():
        return set()
    return set(pd.read_csv(LLM_LABELS, usecols=["reviewId"])["reviewId"])


def select_for_labelling(window_days, older_per_month, long_praise_chars=80, seed=7):
    """Everything <=3 stars plus longer 4-5 star reviews inside the window;
    a stratified sample of <=3 star reviews per month before it (for theme trends)."""
    df = pd.read_csv(RAW / f"{config.PRIMARY_APP}.csv", parse_dates=["at"])
    df["content"] = df["content"].fillna("").astype(str)
    df = df[df["content"].str.strip().str.len() > 0]
    cutoff = df["at"].max() - timedelta(days=window_days)
    recent = df[df["at"] >= cutoff]
    recent = recent[(recent["score"] <= 3) | (recent["content"].str.len() > long_praise_chars)]
    recent = recent.assign(sample="window")
    older_start = cutoff - timedelta(days=365 * 3)
    older = df[(df["at"] < cutoff) & (df["at"] >= older_start) & (df["score"] <= 3)].copy()
    older["month"] = older["at"].dt.to_period("M")
    older = (older.groupby("month", group_keys=False)
             .apply(lambda g: g.sample(min(len(g), older_per_month), random_state=seed), include_groups=False)
             .assign(sample="older"))
    chosen = pd.concat([recent, older], ignore_index=True)
    return chosen[~chosen["reviewId"].isin(labelled_ids())].sort_values("at", ascending=False)


def export(window_days, older_per_month, chunk_size):
    QUEUE.mkdir(parents=True, exist_ok=True)
    existing = sorted(QUEUE.glob("chunk_*.jsonl"))
    queued = set()
    for f in existing:
        if not f.name.endswith(".labels.jsonl"):
            queued |= set(json.loads(f.with_suffix(".map.json").read_text())["ids"].values()) \
                if f.with_suffix(".map.json").exists() else set()
    todo = select_for_labelling(window_days, older_per_month)
    todo = todo[~todo["reviewId"].isin(queued)]
    start = len([f for f in existing if not f.name.endswith(".labels.jsonl")]) + 1
    n_chunks = 0
    for c, off in enumerate(range(0, len(todo), chunk_size), start=start):
        part = todo.iloc[off:off + chunk_size]
        name = f"chunk_{c:03d}"
        with open(QUEUE / f"{name}.jsonl", "w", encoding="utf-8") as fh:
            for i, (_, row) in enumerate(part.iterrows(), start=1):
                text = " ".join(row["content"].split())[:MAX_TEXT]
                fh.write(json.dumps({"i": i, "s": int(row["score"]), "t": text}, ensure_ascii=False) + "\n")
        ids = {str(i): rid for i, rid in enumerate(part["reviewId"], start=1)}
        meta = {"ids": ids, "sample": part["sample"].tolist(), "created": datetime.now().isoformat()}
        (QUEUE / f"{name}.map.json").write_text(json.dumps(meta), encoding="utf-8")
        n_chunks += 1
    print(f"exported {len(todo)} reviews into {n_chunks} chunks of <= {chunk_size}")


def validate_line(obj, valid_ids):
    errs = []
    if str(obj.get("i")) not in valid_ids:
        errs.append(f"unknown id {obj.get('i')}")
    st = obj.get("st")
    if not isinstance(st, list) or not st or not set(st) <= STAGES:
        errs.append(f"bad stages {st}")
    if obj.get("a") not in ATTRIBUTION:
        errs.append(f"bad attribution {obj.get('a')}")
    if obj.get("se") not in SENTIMENT:
        errs.append(f"bad sentiment {obj.get('se')}")
    if not isinstance(obj.get("sf"), bool):
        errs.append(f"bad safety flag {obj.get('sf')}")
    d = obj.get("d", "")
    if not isinstance(d, str) or len(d) > 80:
        errs.append("detail missing or too long")
    return errs


def import_labels(labeller):
    done = labelled_ids()
    new_rows, problems = [], 0
    for lab in sorted(QUEUE.glob("chunk_*.labels.jsonl")):
        name = lab.name.replace(".labels.jsonl", "")
        meta = json.loads((QUEUE / f"{name}.map.json").read_text())
        ids = meta["ids"]
        seen, rows, errs = set(), [], []
        for ln, line in enumerate(lab.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                errs.append(f"line {ln}: invalid JSON ({exc})")
                continue
            e = validate_line(obj, ids)
            if str(obj.get("i")) in seen:
                e.append(f"duplicate id {obj.get('i')}")
            if e:
                errs.append(f"line {ln}: " + "; ".join(e))
                continue
            seen.add(str(obj["i"]))
            rows.append({"reviewId": ids[str(obj["i"])], "stages": "|".join(obj["st"]),
                         "detail": obj.get("d", ""), "attribution": obj["a"],
                         "text_sentiment": obj["se"], "safety_flag": obj["sf"]})
        missing = set(ids) - seen
        if missing:
            errs.append(f"{len(missing)} reviews not labelled: {sorted(missing, key=int)[:10]}")
        if errs:
            problems += 1
            print(f"{name}: REJECTED")
            for e in errs[:15]:
                print("   ", e)
            continue
        fresh = [r for r in rows if r["reviewId"] not in done]
        for r in fresh:
            r.update({"labeller": labeller, "prompt_version": PROMPT_VERSION,
                      "labelled_at": datetime.now().isoformat(timespec="seconds")})
        new_rows += fresh
        done |= {r["reviewId"] for r in fresh}
        print(f"{name}: ok ({len(fresh)} new)")
    if new_rows:
        out = pd.DataFrame(new_rows)
        out.to_csv(LLM_LABELS, mode="a", header=not LLM_LABELS.exists(), index=False)
    print(f"imported {len(new_rows)} labels; {problems} chunk(s) need fixing")
    return problems == 0


def load_labels():
    """AI labels with human corrections applied on top (corrections always win)."""
    if not LLM_LABELS.exists():
        return pd.DataFrame()
    labels = pd.read_csv(LLM_LABELS).drop_duplicates("reviewId", keep="last")
    if OVERRIDES.exists():
        ov = pd.read_csv(OVERRIDES)
        for _, o in ov.iterrows():
            mask = labels["reviewId"] == o["reviewId"]
            if mask.any() and o["field"] in labels.columns:
                labels.loc[mask, o["field"]] = o["value"]
                labels.loc[mask, "human_corrected"] = True
    return labels


def audit_sample(n, seed):
    """A random sample of AI labels plus every safety flag, for a person to check.
    Fill `verdict` with ok / wrong and, if wrong, the right `correct_stages`."""
    labels = load_labels()
    rev = pd.read_csv(RAW / f"{config.PRIMARY_APP}.csv", usecols=["reviewId", "content", "score", "at"])
    df = labels.merge(rev, on="reviewId")
    safety = df[df["safety_flag"].astype(str).str.lower() == "true"]
    rest = df.drop(safety.index).sample(n, random_state=seed)
    out = pd.concat([rest.assign(why="random"), safety.assign(why="safety flag")])
    out = out.assign(text=out["content"].map(lambda t: " ".join(str(t).split())),
                     verdict="", correct_stages="", note="")
    cols = ["why", "reviewId", "score", "text", "stages", "attribution", "text_sentiment",
            "safety_flag", "detail", "verdict", "correct_stages", "note"]
    path = LABELS / "gold_audit.csv"
    out[cols].to_csv(path, index=False, encoding="utf-8-sig")
    print(f"wrote {path} ({len(rest)} random + {len(safety)} safety)")


def status():
    chunks = [f for f in sorted(QUEUE.glob("chunk_*.jsonl")) if not f.name.endswith(".labels.jsonl")]
    labelled = [f for f in chunks if (QUEUE / f"{f.stem}.labels.jsonl").exists()]
    print(f"chunks: {len(chunks)} exported, {len(labelled)} have labels; "
          f"{len(labelled_ids())} reviews imported")
    pending = [f.stem for f in chunks if f not in labelled]
    if pending:
        print("pending:", ", ".join(pending))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("--window-days", type=int, default=config.LABEL_WINDOW_DAYS)
    e.add_argument("--older-per-month", type=int, default=15)
    e.add_argument("--chunk-size", type=int, default=150)
    i = sub.add_parser("import")
    i.add_argument("--labeller", default="claude-opus-5-5 (Claude Code session)")
    sub.add_parser("status")
    au = sub.add_parser("audit-sample")
    au.add_argument("--n", type=int, default=50)
    au.add_argument("--seed", type=int, default=13)
    a = p.parse_args()
    if a.cmd == "export":
        export(a.window_days, a.older_per_month, a.chunk_size)
    elif a.cmd == "import":
        sys.exit(0 if import_labels(a.labeller) else 1)
    elif a.cmd == "audit-sample":
        audit_sample(a.n, a.seed)
    else:
        status()
