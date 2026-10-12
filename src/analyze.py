"""Turn raw reviews + snapshots + labels into metrics.json — the single source
for every number in the memo, the report page, and the weekly digest."""
import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
SNAPSHOTS = ROOT / "data" / "snapshots"
PROCESSED = ROOT / "data" / "processed"


# ---------- helpers ----------

def wilson(k, n, z=1.96):
    """95% Wilson interval for a proportion — honest error bars on small samples."""
    if n == 0:
        return (None, None)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (round(centre - half, 4), round(centre + half, 4))


def load_reviews(app_id, suffix=""):
    path = RAW / f"{app_id}{suffix}.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, parse_dates=["at", "repliedAt"])
    if df.empty:
        return pd.DataFrame()
    df["content"] = df["content"].fillna("").astype(str)
    df["length"] = df["content"].str.len()
    df["month"] = df["at"].dt.to_period("M").astype(str)
    return df


def latest_snapshot():
    files = sorted(p for p in SNAPSHOTS.glob("*.json"))
    return json.loads(files[-1].read_text(encoding="utf-8")) if files else {"apps": {}}


def r(x, nd=3):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), nd)


# ---------- store-level numbers ----------

def store_view(snap):
    d = snap["apps"].get(config.PRIMARY_APP, {})
    hist = d.get("histogram") or [0] * 5
    n = sum(hist)
    s = sum((i + 1) * c for i, c in enumerate(hist))
    lifetime_mean = s / n if n else None
    shown = round(d.get("score") or 0, 1)
    target = shown + 0.05  # rounding threshold to display the next decimal
    # Upper bound (A8): extra 5-star ratings needed if every rating counted equally.
    k5 = math.ceil((target * n - s) / (5 - target)) if n and lifetime_mean < target else 0
    return {
        "app_id": config.PRIMARY_APP,
        "displayed_score_exact": r(d.get("score"), 4),
        "displayed_score": shown,
        "ratings": d.get("ratings"),
        "text_reviews": d.get("reviews"),
        "histogram": dict(zip(["1", "2", "3", "4", "5"], hist)),
        "histogram_mean": r(lifetime_mean, 4),
        "share_1star_lifetime": r(hist[0] / n, 4) if n else None,
        "next_display_threshold": round(target, 2),
        "gap_to_threshold": r(target - (d.get("score") or 0), 4),
        "extra_5star_needed_upper_bound": k5,
        "extra_5star_as_share_of_daily_riders": r(k5 / config.DAILY_RIDERS, 5) if k5 else 0,
        "ratings_per_daily_rider": r(n / config.DAILY_RIDERS, 4) if n else None,
        "installs": d.get("installs"),
        "version": d.get("version"),
        "updated": d.get("updated"),
        "recent_changes": d.get("recentChanges"),
    }


def benchmark(snap):
    rows = []
    for app_id, meta in config.APPS.items():
        d = snap["apps"].get(app_id)
        if not d or meta["role"] == "driver":
            continue
        row = {"app_id": app_id, "name": meta["name"], "role": meta["role"],
               "score": r(d.get("score"), 3), "displayed": round(d["score"], 1) if d.get("score") else None,
               "ratings": d.get("ratings"), "installs": d.get("installs")}
        rev = load_reviews(app_id)
        if len(rev):
            recent = rev[rev["at"] >= rev["at"].max() - timedelta(days=90)]
            row.update({"reviews_90d": len(recent), "mean_90d": r(recent["score"].mean(), 2),
                        "share_1star_90d": r((recent["score"] == 1).mean(), 3),
                        "reply_rate_90d": r(recent["replyContent"].notna().mean(), 3)})
        rows.append(row)
    rows.sort(key=lambda x: -(x["score"] or 0))
    return rows


# ---------- review-level numbers ----------

def monthly(df):
    g = df.groupby("month")
    out = pd.DataFrame({
        "reviews": g.size(),
        "mean": g["score"].mean().round(3),
        "share_1star": g["score"].apply(lambda s: (s == 1).mean()).round(4),
        "share_5star": g["score"].apply(lambda s: (s == 5).mean()).round(4),
        "short_5star": g.apply(lambda x: ((x["score"] == 5) & (x["length"] <= 20)).sum(), include_groups=False),
        "reply_rate": g["replyContent"].apply(lambda s: s.notna().mean()).round(4),
    }).reset_index()
    end = df["at"].max()
    out["partial"] = (out["month"] == end.strftime("%Y-%m")) & (end.day < end.days_in_month)
    return out


def rolling_28d(df):
    daily = df.set_index("at").sort_index()["score"].resample("D").agg(["sum", "count"])
    roll = daily.rolling("28D").sum()
    roll["mean"] = (roll["sum"] / roll["count"]).round(3)
    roll = roll[roll["count"] >= 20]
    return [{"date": d.strftime("%Y-%m-%d"), "mean": m, "n": int(c)}
            for d, m, c in zip(roll.index, roll["mean"], roll["count"])][-730:]


def versions(df):
    v = df.dropna(subset=["reviewCreatedVersion"])
    rows = []
    for ver, g in v.groupby("reviewCreatedVersion"):
        n = len(g)
        if n < config.MIN_VERSION_N:
            continue
        k1 = int((g["score"] == 1).sum())
        lo, hi = wilson(k1, n)
        rows.append({"version": ver, "n": n, "first_seen": g["at"].min().strftime("%Y-%m-%d"),
                     "last_seen": g["at"].max().strftime("%Y-%m-%d"),
                     "mean": r(g["score"].mean(), 3), "share_1star": r(k1 / n, 4),
                     "share_1star_ci": [lo, hi]})
    rows.sort(key=lambda x: x["first_seen"])
    return {"coverage": r(len(v) / len(df), 3) if len(df) else None, "versions": rows}


def windows(df):
    end = df["at"].max()
    out = {}
    for label, days in [("last_30d", 30), ("last_90d", 90), ("last_365d", 365), ("all", None)]:
        w = df if days is None else df[df["at"] >= end - timedelta(days=days)]
        n = len(w)
        k1 = int((w["score"] == 1).sum())
        out[label] = {"n": n, "mean": r(w["score"].mean(), 3),
                      "share_1star": r(k1 / n, 4) if n else None, "share_1star_ci": wilson(k1, n),
                      "share_5star": r((w["score"] == 5).mean(), 4) if n else None,
                      "dist": {str(s): int((w["score"] == s).sum()) for s in range(1, 6)}}
    out["data_end"] = end.strftime("%Y-%m-%d")
    out["data_start"] = df["at"].min().strftime("%Y-%m-%d")
    return out


def replies(df):
    rep = df[df["replyContent"].notna()].copy()
    rep["latency_h"] = (rep["repliedAt"] - rep["at"]).dt.total_seconds() / 3600
    rep = rep[rep["latency_h"] >= 0]  # "at" is the last edit time, so edited reviews can look replied-before-written
    end = df["at"].max()
    recent = df[df["at"] >= end - timedelta(days=90)]
    top = rep["replyContent"].str.strip().value_counts().head(5)
    return {
        "reply_rate_all": r(df["replyContent"].notna().mean(), 4),
        "reply_rate_90d": r(recent["replyContent"].notna().mean(), 4),
        "reply_rate_by_star_90d": {str(s): r(recent[recent["score"] == s]["replyContent"].notna().mean(), 4)
                                   for s in range(1, 6)},
        "median_latency_hours": r(rep["latency_h"].median(), 1),
        "median_latency_hours_90d": r(rep[rep["at"] >= end - timedelta(days=90)]["latency_h"].median(), 1),
        "share_identical_replies": r(1 - rep["replyContent"].str.strip().nunique() / len(rep), 4) if len(rep) else None,
        "top_reply_texts": [{"text": t[:300], "count": int(c)} for t, c in top.items()],
    }


def visitor_view():
    path = RAW / f"{config.PRIMARY_APP}__most_relevant.csv"
    if not path.exists():
        return None
    mr = pd.read_csv(path, parse_dates=["at"])
    first = mr.head(10)
    return {
        "n": len(mr),
        "mean_top10": r(first["score"].mean(), 2),
        "mean_top40": r(mr["score"].mean(), 2),
        "share_1_2star_top10": r((first["score"] <= 2).mean(), 2),
        "share_1_2star_top40": r((mr["score"] <= 2).mean(), 2),
        "top10": [{"rank": int(x["rank"]), "score": int(x["score"]), "date": x["at"].strftime("%Y-%m-%d"),
                   "thumbs": int(x["thumbsUpCount"]), "text": str(x["content"])[:400],
                   "replied": bool(pd.notna(x["replyContent"]))} for _, x in first.iterrows()],
    }


def hindi_share(df_en):
    hi = load_reviews(config.PRIMARY_APP, "__hi")
    if hi.empty:
        return None
    start = hi["at"].min()
    en_same = df_en[df_en["at"] >= start]
    return {"hi_reviews": len(hi), "since": start.strftime("%Y-%m-%d"),
            "en_reviews_same_period": len(en_same),
            "hi_share": r(len(hi) / (len(hi) + len(en_same)), 4),
            "hi_mean": r(hi["score"].mean(), 2)}


def phase1():
    snap = latest_snapshot()
    df = load_reviews(config.PRIMARY_APP)
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "store": store_view(snap),
        "benchmark": benchmark(snap),
        "windows": windows(df),
        "monthly": monthly(df).to_dict("records"),
        "rolling_28d": rolling_28d(df),
        "versions": versions(df),
        "replies": replies(df),
        "visitor_view": visitor_view(),
        "hindi": hindi_share(df),
    }


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    metrics = phase1()
    try:
        import themes_metrics  # added once labels exist
        metrics.update(themes_metrics.compute())
    except ImportError:
        pass
    out = PROCESSED / "metrics.json"
    out.write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")
    print(f"wrote {out}")
    return metrics


if __name__ == "__main__":
    main()
