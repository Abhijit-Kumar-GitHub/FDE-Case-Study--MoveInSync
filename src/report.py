"""Build the outputs people actually look at:

  docs/index.html          static dashboard (GitHub Pages) — "How are our ratings?"
  docs/needs_review.csv    reviews a person should look at, with the reason
  docs/weekly_digest.md    the short answer, posted weekly as a GitHub Issue
"""
import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
import rules  # noqa: E402
from analyze import wilson  # noqa: E402
from labels_io import load_labels  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
TEMPLATE = Path(__file__).resolve().parent / "report_template.html"

OWNER = {"safety": "Safety desk (24h SLA)", "mismatch": "Product analyst", "possible miss": "Product analyst",
         "unclear": "Product analyst", "unplaced by rules": "Product analyst"}


def labelled_with_fallback():
    """AI/human labels where they exist; keyword rules for everything newer."""
    rev = pd.read_csv(RAW / f"{config.PRIMARY_APP}.csv", parse_dates=["at", "repliedAt"])
    rev["content"] = rev["content"].fillna("").astype(str)
    lab = load_labels()
    df = rev.merge(lab, on="reviewId", how="left") if not lab.empty else rev.assign(stages=None)
    missing = df["stages"].isna()
    if missing.any():
        rl = df.loc[missing].apply(lambda r: rules.classify(r["content"], r["score"]), axis=1, result_type="expand")
        for col in rl.columns:
            df.loc[missing, col] = rl[col]
        df.loc[missing, "labeller"] = "rules-v1"
    df["safety_flag"] = df["safety_flag"].astype(str).str.lower().eq("true")
    return df


def build_queue(df):
    end = df["at"].max()
    recent = df["at"] >= end - timedelta(days=365)
    fresh = df["at"] >= end - timedelta(days=90)
    rows = []
    for _, r in df.iterrows():
        reasons = []
        ai = r.get("labeller") != "rules-v1"
        if not ai and not fresh.loc[_]:
            continue  # rule-only labels are for new reviews; history was AI-labelled where it mattered
        prim = rules.primary_family(r["stages"])
        if r["safety_flag"]:
            reasons.append("safety")
        if recent.loc[_] and ai:
            if (r["score"] <= 2 and r["text_sentiment"] == "pos") or (r["score"] >= 4 and r["text_sentiment"] == "neg"):
                reasons.append("mismatch")
            if prim == "U" and len(r["content"]) >= 80:
                reasons.append("unclear")
            if prim in ("U", "P"):
                rf = rules.families(rules.classify(r["content"], r["score"])["stages"]) - {"U", "P"}
                if rf and len(r["content"]) >= 40:
                    reasons.append("possible miss")
        if not ai and recent.loc[_]:
            if prim == "U" and len(r["content"]) >= 60:
                reasons.append("unplaced by rules")
        if reasons:
            rows.append({"reason": ", ".join(reasons), "owner": OWNER[reasons[0]],
                         "date": r["at"].strftime("%Y-%m-%d"), "stars": int(r["score"]),
                         "version": "" if pd.isna(r["reviewCreatedVersion"]) else r["reviewCreatedVersion"],
                         "text": " ".join(r["content"].split()), "stages": r["stages"],
                         "attribution": r["attribution"], "detail": r.get("detail", ""),
                         "labeller": r.get("labeller", ""), "status": "open", "reviewId": r["reviewId"]})
    q = pd.DataFrame(rows)
    if q.empty:
        return q
    q["prio"] = q["reason"].str.startswith("safety").map({True: 0, False: 1})
    q = q.sort_values(["prio", "date"], ascending=[True, False]).drop(columns="prio")
    return q


def digest(metrics, df, queue):
    s = metrics["store"]
    snaps = pd.read_csv(ROOT / "data" / "snapshots" / "history.csv")
    snaps = snaps[snaps["app_id"] == config.PRIMARY_APP].sort_values("date")
    prev = snaps.iloc[-2] if len(snaps) > 1 else None
    end = df["at"].max()
    last7 = df[df["at"] > end - timedelta(days=7)]
    base = df[(df["at"] <= end - timedelta(days=7)) & (df["at"] > end - timedelta(days=35))]
    win = df[df["at"] > end - timedelta(days=28)]
    neg28 = win[win["score"] <= 2]
    fam_counts = {}
    for st in neg28["stages"].dropna():
        for f in rules.families(st):
            if f not in ("U", "P"):
                fam_counts[f] = fam_counts.get(f, 0) + 1
    import themes_metrics as tm
    top = sorted(fam_counts.items(), key=lambda kv: -kv[1])[:4]
    base_1 = metrics["windows"]["last_365d"]["share_1star"]

    lines = [f"# How are our Play Store ratings? — {end:%d %b %Y}", ""]
    delta = ""
    if prev is not None:
        d = s["displayed_score_exact"] - prev["score"]
        delta = f" (unchanged since {prev['date']})" if abs(d) < 0.0005 else f" ({d:+.3f} since {prev['date']})"
    lines += [f"**Store rating (India): {s['displayed_score_exact']:.3f}★ — shows {s['displayed_score']}**{delta} · "
              f"{s['ratings']:,} ratings · {s['gap_to_threshold']:.3f} away from showing {s['next_display_threshold'] + 0.05:.1f}", ""]
    if len(last7):
        lines.append(f"- **Last 7 days:** {len(last7)} written reviews, average {last7['score'].mean():.2f}★, "
                     f"{(last7['score'] == 1).mean():.0%} one-star (prior 4 weeks: {base['score'].mean():.2f}★, "
                     f"{(base['score'] == 1).mean():.0%} one-star).")
    if top:
        lines.append("- **Top complaint themes (1–2★, last 28 days):** " +
                     ", ".join(f"{tm.FAMILY_LABELS.get(f, f)} ({n})" for f, n in top) + ".")
    # Release watch.
    watch = []
    for ver, g in df[df["at"] > end - timedelta(days=60)].dropna(subset=["reviewCreatedVersion"]).groupby("reviewCreatedVersion"):
        if len(g) < 20:
            continue
        k = int((g["score"] == 1).sum())
        lo, hi = wilson(k, len(g))
        share = k / len(g)
        if lo is not None and lo > base_1:
            watch.append(f"🚨 **{ver}**: {share:.0%} one-star (95% CI {lo:.0%}–{hi:.0%}) vs {base_1:.0%} baseline, n={len(g)} — regression")
        elif share > base_1 + 0.05:
            watch.append(f"👀 {ver}: {share:.0%} one-star vs {base_1:.0%} baseline, n={len(g)} — watch (not yet significant)")
    lines.append("- **Release watch:** " + ("; ".join(watch) if watch else "no version is above baseline.") )
    rr = win["replyContent"].notna().mean() if len(win) else 0
    lines.append(f"- **Developer replies (last 28 days):** {rr:.0%} of reviews answered.")
    if not queue.empty:
        open_safety = int(queue["reason"].str.contains("safety").sum())
        recent_q = queue[pd.to_datetime(queue["date"]) > end - timedelta(days=28)]
        lines.append(f"- **Needs a person:** {len(recent_q)} new in the last 28 days "
                     f"({int(recent_q['reason'].str.contains('safety').sum())} safety) · {open_safety} safety items on file.")
    lines += ["", f"Dashboard: {config.PAGES_URL} · "
              "Queue: needs_review.csv · Replies: reply_drafts.html · Method: README", ""]
    return "\n".join(lines)


def page(metrics, queue, digest_md):
    payload = dict(metrics)
    payload["queue_top"] = queue.head(15).to_dict("records") if not queue.empty else []
    payload["queue_counts"] = queue["reason"].str.split(", ").explode().value_counts().to_dict() if not queue.empty else {}
    payload["digest_md"] = digest_md
    payload["repo_url"] = config.REPO_URL
    html = TEMPLATE.read_text(encoding="utf-8")
    blob = json.dumps(payload, default=str, ensure_ascii=False).replace("</", "<\\/")
    return html.replace("__METRICS_JSON__", blob)


REPLY_LIMIT = 350  # Google Play's cap on a developer reply


def write_reply_queue(df):
    """REP-1, operational: unanswered 1-3 star reviews in the order a person should answer them.
    What visitors see first comes first, then safety, then upvotes, then recency."""
    import themes_metrics as tm
    drafts_path = ROOT / "data" / "labels" / "reply_drafts.json"
    drafts = json.loads(drafts_path.read_text(encoding="utf-8"))["drafts"] if drafts_path.exists() else {}
    mr_path = RAW / f"{config.PRIMARY_APP}__most_relevant.csv"
    visible = pd.read_csv(mr_path)[["reviewId", "rank"]] if mr_path.exists() else pd.DataFrame(columns=["reviewId", "rank"])
    end = df["at"].max()
    pool = df[(df["score"] <= 3) & df["replyContent"].isna()]
    pool = pool.merge(visible, on="reviewId", how="left")
    pool = pool[pool["rank"].notna() | (pool["at"] >= end - timedelta(days=90))].copy()
    pool["visible"] = pool["rank"].notna()
    pool = pool.sort_values(["visible", "safety_flag", "rank", "thumbsUpCount", "at"],
                            ascending=[False, False, True, False, False])
    rows = []
    for i, (_, r) in enumerate(pool.iterrows(), start=1):
        d = drafts.get(r["reviewId"], {})
        reply = d.get("reply", "")
        if len(reply) > REPLY_LIMIT:
            raise ValueError(f"draft for {r['reviewId']} is {len(reply)} chars; Play allows {REPLY_LIMIT}")
        themes = sorted({tm.FAMILY_LABELS.get(f, f) for f in rules.families(r["stages"]) if f not in ("U", "P")})
        rows.append({"priority": i, "visible_rank": "" if pd.isna(r["rank"]) else int(r["rank"]),
                     "safety": bool(r["safety_flag"]), "date": r["at"].strftime("%Y-%m-%d"), "stars": int(r["score"]),
                     "helpful_votes": int(r["thumbsUpCount"]), "version": "" if pd.isna(r["reviewCreatedVersion"]) else r["reviewCreatedVersion"],
                     "themes": "; ".join(themes), "review": " ".join(r["content"].split()),
                     "draft_reply": reply, "draft_chars": len(reply) if reply else "",
                     "needs_confirmation": "[confirm" in reply, "reviewId": r["reviewId"]})
    q = pd.DataFrame(rows)
    q.to_csv(DOCS / "reply_queue.csv", index=False, encoding="utf-8-sig")

    lines = ["# Reply drafts: the reviews visitors see first", "",
             "For Support (REP-1). Reviews are in the order Play shows them to visitors ('most relevant', which favours reviews with many 'helpful' votes). "
             "Each draft is specific to the review and within Google Play's 350-character limit. "
             "Fill every `[confirm: …]` with a checked fact (or delete the clause) before posting. "
             "Post the reply, then come back to the same review when the fix ships. Riders can update their rating.", "",
             f"Full prioritised queue (all unanswered 1–3★ reviews): `reply_queue.csv`, {len(q)} reviews.", ""]
    for _, r in q[q["draft_reply"] != ""].iterrows():
        lines += [f"## #{r['visible_rank']} on the listing · {'★' * r['stars']}{'☆' * (5 - r['stars'])} · {r['date']} · {r['helpful_votes']} found this helpful", "",
                  f"> {r['review'][:600]}{'…' if len(r['review']) > 600 else ''}", "",
                  f"**Draft reply** ({r['draft_chars']} chars{', needs confirmation' if r['needs_confirmation'] else ''}):", "",
                  r["draft_reply"], ""]
    (DOCS / "reply_drafts.md").write_text("\n".join(lines), encoding="utf-8")
    return q


def write_backlog():
    """docs/backlog.json -> docs/backlog.csv (columns map straight onto a Jira/Linear CSV import)."""
    src = DOCS / "backlog.json"
    if not src.exists():
        return
    items = json.loads(src.read_text(encoding="utf-8"))
    rows = []
    for t in items:
        desc = (f"Evidence: {t['evidence']}\n\nLikely cause: {t['hypothesis']}\n\nChange: {t['change']}\n\n"
                f"Acceptance criteria: {t['acceptance']}\n\nSuccess metric: {t['metric']}\n\nCheck on day 1: {t['day1']}")
        rows.append({"Issue key": t["id"], "Summary": t["title"], "Priority": t["priority"], "Labels": "play-ratings " + t["horizon"].split(" (")[0].lower().replace(" ", "-"),
                     "Component": t["owner"], "Horizon": t["horizon"], "Effort (assumed)": t["effort"], "Description": desc})
    pd.DataFrame(rows).to_csv(DOCS / "backlog.csv", index=False, encoding="utf-8-sig")


def main(owner="OWNER"):
    DOCS.mkdir(exist_ok=True)
    write_backlog()
    metrics = json.loads((PROCESSED / "metrics.json").read_text(encoding="utf-8"))
    df = labelled_with_fallback()
    queue = build_queue(df)
    queue.to_csv(DOCS / "needs_review.csv", index=False, encoding="utf-8-sig")
    replies = write_reply_queue(df)
    metrics["reply_queue"] = {"open": len(replies), "visible_unanswered": int((replies["visible_rank"] != "").sum()),
                              "drafted": int((replies["draft_reply"] != "").sum())}
    md = digest(metrics, df, queue)
    (DOCS / "weekly_digest.md").write_text(md, encoding="utf-8")
    (DOCS / "index.html").write_text(page(metrics, queue, md), encoding="utf-8")
    import memo
    memo.render_docs()
    print(f"queue: {len(queue)} rows · digest + dashboard written to docs/")
    return md


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "OWNER")
