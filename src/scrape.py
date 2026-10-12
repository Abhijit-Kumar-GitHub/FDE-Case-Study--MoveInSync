"""Pull public Play Store data: a metadata snapshot per app plus reviews.

Incremental: reviews already on disk (keyed by reviewId) are not fetched again,
so the scheduled job only pays for what is new. Usernames and avatars are not
stored — the analysis never needs to know who wrote a review.
"""
import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from google_play_scraper import Sort, app as app_details, reviews

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
SNAPSHOTS = ROOT / "data" / "snapshots"
IST = timezone(timedelta(hours=5, minutes=30))

REVIEW_COLUMNS = [
    "reviewId", "content", "score", "thumbsUpCount", "reviewCreatedVersion",
    "appVersion", "at", "replyContent", "repliedAt",
]
SNAPSHOT_FIELDS = [
    "title", "score", "ratings", "reviews", "histogram", "installs", "realInstalls",
    "version", "updated", "released", "recentChanges", "developer",
]


def _retry(fn, *args, tries=4, **kwargs):
    for attempt in range(tries):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # network hiccups, throttling
            if attempt == tries - 1:
                raise
            wait = 2 ** attempt * 3
            print(f"  retry in {wait}s after: {exc}", flush=True)
            time.sleep(wait)


def _clean(batch):
    rows = [{k: r.get(k) for k in REVIEW_COLUMNS} for r in batch]
    df = pd.DataFrame(rows, columns=REVIEW_COLUMNS)
    for col in ("at", "repliedAt"):
        df[col] = pd.to_datetime(df[col])
    return df


def snapshot(app_ids=None):
    """Record today's store figures. The displayed-rating history is not public,
    so this file series is the only way to track it over time."""
    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    today = datetime.now(IST).strftime("%Y-%m-%d")
    out = {"captured_at": datetime.now(IST).isoformat(), "apps": {}}
    for app_id in app_ids or config.APPS:
        try:
            d = _retry(app_details, app_id, lang=config.LANG, country=config.COUNTRY)
        except Exception as exc:
            print(f"  snapshot failed for {app_id}: {exc}", flush=True)
            continue
        out["apps"][app_id] = {k: d.get(k) for k in SNAPSHOT_FIELDS}
        print(f"  {app_id}: score={d.get('score')} ratings={d.get('ratings')}", flush=True)
    path = SNAPSHOTS / f"{today}.json"
    path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")

    # Flat history table for charts and the digest.
    hist_path = SNAPSHOTS / "history.csv"
    rows = []
    for app_id, d in out["apps"].items():
        h = d.get("histogram") or [None] * 5
        rows.append({"date": today, "app_id": app_id, "score": d.get("score"),
                     "ratings": d.get("ratings"), "reviews": d.get("reviews"),
                     **{f"stars_{i + 1}": h[i] for i in range(5)}})
    new = pd.DataFrame(rows)
    if hist_path.exists():
        old = pd.read_csv(hist_path)
        old = old[old["date"] != today]
        new = pd.concat([old, new], ignore_index=True)
    new.to_csv(hist_path, index=False)
    return out


def scrape_reviews(app_id, history_days=None, lang=None, suffix="", max_reviews=200_000):
    """Page through newest-first reviews until we reach ones already stored,
    pass the history cutoff, or run out."""
    RAW.mkdir(parents=True, exist_ok=True)
    lang = lang or config.LANG
    path = RAW / f"{app_id}{suffix}.csv"
    existing = pd.read_csv(path, parse_dates=["at", "repliedAt"]) if path.exists() else pd.DataFrame(columns=REVIEW_COLUMNS)
    known = set(existing["reviewId"])
    cutoff = datetime.now() - timedelta(days=history_days) if history_days else None

    frames, token, fetched = [], None, 0
    while fetched < max_reviews:
        batch, token = _retry(reviews, app_id, lang=lang, country=config.COUNTRY,
                              sort=Sort.NEWEST, count=200, continuation_token=token)
        if not batch:
            break
        df = _clean(batch)
        fresh = df[~df["reviewId"].isin(known)]
        frames.append(fresh)
        fetched += len(df)
        oldest = df["at"].min()
        if fetched % 2000 == 0 or len(df) < 200:
            print(f"  {app_id}{suffix}: {fetched} fetched, oldest {oldest:%Y-%m-%d}", flush=True)
        if len(fresh) == 0 and known:
            break  # caught up with what we already have
        if cutoff is not None and oldest < cutoff:
            break
        if token is None or len(df) < 200:
            break
        time.sleep(0.4)

    parts = [f for f in [existing] + frames if len(f)]
    combined = pd.concat(parts, ignore_index=True) if parts else existing
    combined = combined.drop_duplicates("reviewId", keep="last")
    if cutoff is not None:
        combined = combined[combined["at"] >= cutoff]
    combined = combined.sort_values("at", ascending=False)
    combined.to_csv(path, index=False)
    print(f"  {app_id}{suffix}: {len(combined)} stored ({len(combined) - len(existing):+d} new)", flush=True)
    return combined


def most_relevant(app_id, n):
    """The reviews a visitor sees first on the listing."""
    batch, _ = _retry(reviews, app_id, lang=config.LANG, country=config.COUNTRY,
                      sort=Sort.MOST_RELEVANT, count=n)
    df = _clean(batch)
    df.insert(0, "rank", range(1, len(df) + 1))
    df["fetched_at"] = datetime.now(IST).isoformat()
    df.to_csv(RAW / f"{app_id}__most_relevant.csv", index=False)
    print(f"  {app_id}: top {len(df)} most-relevant saved", flush=True)
    return df


def run(app_ids=None, with_extras=True):
    app_ids = app_ids or list(config.APPS)
    print("Snapshot:", flush=True)
    snapshot(app_ids)
    print("Reviews:", flush=True)
    for app_id in app_ids:
        try:
            scrape_reviews(app_id, history_days=config.APPS[app_id]["history"])
        except Exception as exc:
            print(f"  reviews failed for {app_id}: {exc}", flush=True)
    if with_extras:
        most_relevant(config.PRIMARY_APP, config.MOST_RELEVANT_COUNT)
        try:
            scrape_reviews(config.PRIMARY_APP, lang="hi", suffix="__hi",
                           max_reviews=config.HINDI_SAMPLE_COUNT)
        except Exception as exc:
            print(f"  hindi sample failed: {exc}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apps", nargs="*", help="package ids (default: all in config)")
    parser.add_argument("--no-extras", action="store_true", help="skip most-relevant and Hindi pulls")
    args = parser.parse_args()
    run(args.apps, with_extras=not args.no_extras)
