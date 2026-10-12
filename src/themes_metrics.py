"""Theme-level metrics from labelled reviews (AI labels + human corrections).

Everything here is computed on the trailing 12 months of written reviews unless
noted; the "older" stratified sample is only used for share-based trends.
"""
import math
import re
import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
import rules  # noqa: E402
from labels_io import load_labels  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

FAMILY_LABELS = {
    "J1": "Onboarding & login", "J2": "Roster & shift", "J3": "Self-booking",
    "J4": "Allocation & routing", "J5": "Notifications", "J6": "Live tracking & ETA",
    "J7": "Pickup & boarding", "J8": "Ride & drop", "J9": "Issue reporting & support",
    "X1": "App stability & speed", "X2": "UI & interruptions", "X3": "Workplace features",
    "P": "Praise", "U": "Unclear / vague",
}
JOURNEY_ORDER = ["J1", "J2", "J3", "J4", "J5", "J6", "J7", "J8", "J9", "X1", "X2", "X3", "U"]

CLUSTERS = {
    # name: (description, regex on review text, optional stage filter)
    "integrity_false_positive": ("False 'not installed from Play Store' / 'rooted device' lock-outs",
                                 r"not (been )?(installed|downloaded) (from|thru|through|in) (the )?play ?store|install(ed)? from (the )?play ?store|rooted", None),
    "forced_rating": ("Forced / repeated trip-rating or review prompts",
                      r"\brat(e|ed|es|ing|ings)\b|\breview|\bfeedback", "X2.interrupt"),
    "policy_prompt": ("Terms / transport-policy acceptance on every open",
                      r"terms|polic|agree|disclaimer|t ?& ?c", "X2.interrupt"),
    "permission_nag": ("Permission nagging (microphone, phone, notifications)",
                       r"permission|microphone|\bmic\b", None),
    "seatbelt_prompt": ("Seat-belt confirmation in front of the boarding OTP",
                        r"seat ?belt|buckle", None),
    "offline_gap": ("Works only on Wi-Fi / mobile data, or no offline cache",
                    r"wi-?fi|mobile data|offline|no (internet|network)|without internet|sim internet|airtel", None),
}
GATING = re.compile(r"only.{0,25}\b(4|5|four|five)\b\s*(or|stars?|&)|until (i|we) (gave|give) 5|not accepting until|"
                    r"manipulat\w*\s+survey|(1|one)[ -]?stars?.{0,40}(deleted|removed)|review is deleted|"
                    r"feedback.{0,60}disappear", re.I)


def _codes(s):
    return [c for c in str(s).split("|") if c]


def _quotes(df, n=3):
    d = df.copy()
    d["clean"] = d["content"].map(lambda t: " ".join(str(t).split()))
    d = d[d["clean"].str.len().between(50, 400)]
    d = d.sort_values(["thumbsUpCount", "at"], ascending=False).head(n)
    return [{"stars": int(x["score"]), "date": x["at"].strftime("%Y-%m-%d"), "thumbs": int(x["thumbsUpCount"]),
             "text": x["clean"], "version": None if pd.isna(x["reviewCreatedVersion"]) else str(x["reviewCreatedVersion"])}
            for _, x in d.iterrows()]


def load_joined():
    lab = load_labels()
    if lab.empty:
        return pd.DataFrame()
    rev = pd.read_csv(ROOT / "data" / "raw" / f"{config.PRIMARY_APP}.csv", parse_dates=["at"])
    df = lab.merge(rev, on="reviewId", how="inner")
    df["codes"] = df["stages"].map(_codes)
    df["fams"] = df["codes"].map(lambda cs: sorted({c.split(".")[0] for c in cs}))
    df["primary"] = df["codes"].map(lambda cs: cs[0])
    df["primary_fam"] = df["primary"].str.split(".").str[0]
    df["safety_flag"] = df["safety_flag"].astype(str).str.lower().eq("true")
    return df


def compute():
    df = load_joined()
    if df.empty:
        return {}
    rev = pd.read_csv(ROOT / "data" / "raw" / f"{config.PRIMARY_APP}.csv", parse_dates=["at"])
    end = rev["at"].max()
    start = end - timedelta(days=365)
    win_all = rev[rev["at"] >= start]
    w = df[df["at"] >= start]
    neg = w[w["score"] <= 2]
    n_neg = len(neg)
    out = {"themes": {}}
    T = out["themes"]
    T["window"] = {"start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d"),
                   "written_reviews": len(win_all), "reviews_1_2star": int((win_all["score"] <= 2).sum()),
                   "labelled_1_2star": n_neg, "labelled_total_window": len(w), "labelled_total": len(df)}

    # Journey heat map: share of 1-2 star reviews mentioning each family.
    fam_rows = []
    for f in JOURNEY_ORDER:
        m = neg[neg["fams"].map(lambda fs: f in fs)]
        p = neg[neg["primary_fam"] == f]
        if not len(m):
            continue
        attr = m["attribution"].value_counts(normalize=True).round(3).to_dict()
        fam_rows.append({"family": f, "label": FAMILY_LABELS[f], "mentions": len(m),
                         "share_mentions": round(len(m) / n_neg, 4), "primary": len(p),
                         "share_primary": round(len(p) / n_neg, 4), "attribution": attr})
    T["families"] = sorted(fam_rows, key=lambda r: -r["mentions"])

    # Codes (sub-issues).
    code_counts = {}
    for cs in neg["codes"]:
        for c in cs:
            code_counts[c] = code_counts.get(c, 0) + 1
    T["codes"] = [{"code": c, "family": FAMILY_LABELS[c.split(".")[0]], "mentions": n,
                   "share": round(n / n_neg, 4)} for c, n in sorted(code_counts.items(), key=lambda kv: -kv[1])]

    # Who would have to fix it.
    T["attribution_1_2star"] = neg["attribution"].value_counts().to_dict()
    specific = neg[neg["primary_fam"] != "U"]
    T["attribution_1_2star_specific"] = specific["attribution"].value_counts(normalize=True).round(3).to_dict()
    T["share_unclear_1_2star"] = round((neg["primary_fam"] == "U").mean(), 4)

    # The five failure types the case study names.
    def share(mask):
        return {"n": int(mask.sum()), "share": round(mask.mean(), 4)}
    T["named_failures"] = {
        "late_cab": share(neg["codes"].map(lambda cs: "J7.late" in cs)),
        # Broader and harder to argue with: late, never came, not assigned, or late/missed drop.
        "cab_late_or_missing": share(neg["codes"].map(lambda cs: any(c in cs for c in ("J7.late", "J4.alloc", "J8.drop")))),
        "any_service_issue": share(neg["fams"].map(lambda fs: bool({"J4", "J8"} & set(fs)))
                                   | neg["codes"].map(lambda cs: "J7.late" in cs or "J7.noshow" in cs)),
        "wrong_route": share(neg["codes"].map(lambda cs: "J4.route" in cs)),
        "booking_fails": share(neg["codes"].map(lambda cs: any(c.startswith("J3.") for c in cs))),
        "app_glitch": share(neg["fams"].map(lambda fs: "X1" in fs)),
        "safety_concern": share(neg["safety_flag"]),
    }

    # Specific clusters (12 months, all stars) — the ticket-sized problems.
    clusters = {}
    for name, (desc, rx, stage) in CLUSTERS.items():
        pat = re.compile(rx, re.I)
        m = w["content"].fillna("").map(lambda t: bool(pat.search(t)))
        if stage:
            m &= w["codes"].map(lambda cs: stage in cs)
        sub = w[m]
        clusters[name] = {"description": desc, "n_12m": len(sub), "n_12m_1_2star": int((sub["score"] <= 2).sum()),
                          "share_of_1_2star": round(int((sub["score"] <= 2).sum()) / n_neg, 4) if n_neg else None,
                          "quotes": _quotes(sub[sub["score"] <= 3])}
    # Integrity lock-outs across ALL written reviews, not just the labelled sample (recurring pattern).
    pat = re.compile(CLUSTERS["integrity_false_positive"][1], re.I)
    allint = rev[rev["content"].fillna("").map(lambda t: bool(pat.search(t)))].copy()
    allint["kind"] = allint["content"].str.contains("rooted", case=False).map({True: "rooted-device check", False: "installer check"})
    clusters["integrity_false_positive"]["history"] = (
        allint.groupby([allint["at"].dt.to_period("Q").astype(str), "kind"]).size().rename("n").reset_index()
        .to_dict("records"))
    T["clusters"] = clusters

    # Sub-issue counts for the biggest families (12 months, 1-2 star).
    T["login_breakdown"] = {c: code_counts.get(c, 0) for c in ["J1.session", "J1.otp", "J1.other"]}
    T["booking_breakdown"] = {c: code_counts.get(c, 0) for c in ["J3.fail", "J3.window", "J3.steps", "J3.modify", "J3.other"]}
    T["pickup_breakdown"] = {c: code_counts.get(c, 0) for c in ["J7.late", "J7.noshow", "J7.contact", "J7.board"]}

    # Review-gating evidence (all labelled history): flagged for a policy check, not a conclusion.
    gate = df[df["content"].fillna("").map(lambda t: bool(GATING.search(t)))]
    rate_prompt = df[df["codes"].map(lambda cs: "X2.interrupt" in cs)
                     & df["content"].str.contains(r"\brat(?:e|ed|es|ing|ings)\b|\breview|\bfeedback", case=False, na=False)]
    T["rating_prompt"] = {
        "complaints_forced_or_repeated_12m": int((rate_prompt["at"] >= start).sum()),
        "possible_gating_reviews": [{"date": x["at"].strftime("%Y-%m-%d"), "stars": int(x["score"]),
                                     "text": " ".join(str(x["content"]).split())[:400]} for _, x in gate.iterrows()],
        "play_store_prompt_mentions": [{"date": x["at"].strftime("%Y-%m-%d"), "stars": int(x["score"]),
                                        "text": " ".join(str(x["content"]).split())[:300]}
                                       for _, x in df[df["content"].str.contains(r"play ?store review", case=False, na=False)].iterrows()],
    }

    # Stars vs words.
    lo_pos = w[(w["score"] <= 2) & (w["text_sentiment"] == "pos")]
    hi_neg = w[(w["score"] >= 4) & (w["text_sentiment"] == "neg")]
    T["mismatch"] = {"low_star_positive_text": len(lo_pos), "high_star_negative_text": len(hi_neg),
                     "share_of_labelled_window": round((len(lo_pos) + len(hi_neg)) / len(w), 4) if len(w) else None,
                     "examples_low_pos": [" ".join(str(t).split())[:160] for t in lo_pos["content"].head(5)],
                     "examples_high_neg": [" ".join(str(t).split())[:200] for t in hi_neg["content"].head(5)]}

    # Safety.
    saf = df[df["safety_flag"]]
    T["safety"] = {"flagged_12m": int((saf["at"] >= start).sum()), "flagged_total": len(saf),
                   "share_of_1_2star_12m": round(neg["safety_flag"].mean(), 4)}

    # Quarterly family shares among labelled <=3 star reviews (window + stratified older sample).
    le3 = df[df["score"] <= 3].copy()
    le3["q"] = le3["at"].dt.to_period("Q").astype(str)
    trend = []
    for q, g in le3.groupby("q"):
        if len(g) < 40:
            continue
        row = {"quarter": q, "n": len(g)}
        for f in ["J1", "J3", "J4", "J6", "J7", "J9", "X1", "X2"]:
            row[f] = round(g["fams"].map(lambda fs: f in fs).mean(), 3)
        trend.append(row)
    T["quarterly_trend"] = trend

    # Monthly share for the families most likely to move with releases (last 24 months).
    recent = le3[le3["at"] >= end - timedelta(days=730)].copy()
    recent["m"] = recent["at"].dt.to_period("M").astype(str)
    monthly = []
    for m, g in recent.groupby("m"):
        monthly.append({"month": m, "n": len(g),
                        "J1.session": round(g["codes"].map(lambda cs: "J1.session" in cs).mean(), 3),
                        "J1.otp": round(g["codes"].map(lambda cs: "J1.otp" in cs).mean(), 3),
                        "X1": round(g["fams"].map(lambda fs: "X1" in fs).mean(), 3),
                        "X2.interrupt": round(g["codes"].map(lambda cs: "X2.interrupt" in cs).mean(), 3)})
    T["monthly_release_sensitive"] = monthly

    # Which versions carry which complaints (window, <=3 star, n>=25).
    wv = w[(w["score"] <= 3)].dropna(subset=["reviewCreatedVersion"])
    vrows = []
    for v, g in wv.groupby("reviewCreatedVersion"):
        if len(g) < 25:
            continue
        vrows.append({"version": str(v), "n": len(g), "first_seen": g["at"].min().strftime("%Y-%m-%d"),
                      **{f: round(g["fams"].map(lambda fs: f in fs).mean(), 3) for f in ["J1", "J3", "J6", "X1", "X2"]}})
    T["versions_by_theme"] = sorted(vrows, key=lambda r: r["first_seen"])

    # Quotes for the top sub-issues.
    T["quotes"] = {c["code"]: _quotes(neg[neg["codes"].map(lambda cs: c["code"] in cs)])
                   for c in T["codes"][:14] if c["code"] not in ("U", "P")}

    # Impact model (A6): if a fix removed x% of a family's 1-2 star reviews and those
    # riders wrote 4 stars instead, how much would the written-review average move?
    n_text = len(win_all)
    cur_mean = win_all["score"].mean()
    impact = []
    for r in T["families"]:
        if r["family"] in ("U", "P"):
            continue
        g = neg[neg["primary_fam"] == r["family"]]
        if not len(g):
            continue
        gain = (4 - g["score"].mean()) * len(g) / n_text
        impact.append({"family": r["family"], "label": r["label"], "primary_1_2star": len(g),
                       "delta_mean_30": round(0.3 * gain, 3), "delta_mean_50": round(0.5 * gain, 3),
                       "delta_mean_70": round(0.7 * gain, 3),
                       "one_star_share_drop_50": round(0.5 * int((g["score"] == 1).sum()) / n_text, 4)})
    T["impact"] = {"current_written_mean_12m": round(cur_mean, 3), "written_reviews_12m": n_text,
                   "by_family": sorted(impact, key=lambda r: -r["delta_mean_50"])}

    # How good is the free fallback? Rules vs AI labels on everything labelled.
    df["r_fams"] = df.apply(lambda x: rules.families(rules.classify(x["content"], x["score"])["stages"]), axis=1)
    ev = []
    for f in ["J1", "J3", "J4", "J5", "J6", "J7", "J8", "J9", "X1", "X2"]:
        ai = df["fams"].map(lambda fs: f in fs)
        ru = df["r_fams"].map(lambda fs: f in fs)
        tp = int((ai & ru).sum())
        ev.append({"family": f, "label": FAMILY_LABELS[f], "ai_n": int(ai.sum()), "rules_n": int(ru.sum()),
                   "precision": round(tp / ru.sum(), 2) if ru.sum() else None,
                   "recall": round(tp / ai.sum(), 2) if ai.sum() else None})
    out["rules_eval"] = {"by_family": ev,
                         "primary_found": round(df.apply(lambda x: x["primary_fam"] in x["r_fams"], axis=1).mean(), 3)}
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(compute(), indent=1, default=str)[:6000])
