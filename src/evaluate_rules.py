"""How good is the free keyword fallback? Scores src/rules.py against the audited AI labels.

The rules were tuned on a fixed 70% "dev" split; numbers are reported on the other 30%
("test"), which tuning never looked at. Precision = of the reviews the rules flag with a
theme, the share the AI labels agree with. Recall = of the reviews the AI gave a theme,
the share the rules also catch. (Per-theme accuracy is not reported: most reviews lack
any given theme, so it is ~0.95 for almost any rule set.)

  python src/evaluate_rules.py            # held-out test split
  python src/evaluate_rules.py dev X1 J6  # dev split, with false positives/negatives for the named themes
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rules  # noqa: E402
from labels_io import RAW, load_labels  # noqa: E402

import config  # noqa: E402  (path set by labels_io)

FAMS = ["J1", "J3", "J4", "J5", "J6", "J7", "J8", "J9", "X1", "X2"]
SEED, TEST_FRAC = 2026, 0.30


def splits():
    lab = load_labels()
    rev = pd.read_csv(RAW / f"{config.PRIMARY_APP}.csv", usecols=["reviewId", "content", "score"])
    df = lab.merge(rev, on="reviewId")
    test = df.sample(frac=TEST_FRAC, random_state=SEED)
    return df.drop(test.index), test


def evaluate(d, show=(), n=12):
    d = d.copy()
    d["ai"] = d["stages"].map(rules.families)
    d["ru"] = d.apply(lambda r: rules.families(rules.classify(r["content"], r["score"])["stages"]), axis=1)
    rows, tp_all, fl_all, ai_all = [], 0, 0, 0
    for f in FAMS:
        ai = d["ai"].map(lambda s: f in s)
        ru = d["ru"].map(lambda s: f in s)
        tp = int((ai & ru).sum())
        tp_all, fl_all, ai_all = tp_all + tp, fl_all + int(ru.sum()), ai_all + int(ai.sum())
        rows.append({"family": f, "ai_n": int(ai.sum()), "rules_n": int(ru.sum()),
                     "precision": round(tp / ru.sum(), 2) if ru.sum() else None,
                     "recall": round(tp / ai.sum(), 2) if ai.sum() else None})
        if f in show:
            for title, part in (("false positives", d[ru & ~ai]), ("false negatives", d[ai & ~ru])):
                print(f"\n=== {f} {title} ({len(part)})")
                for _, r in part.head(n).iterrows():
                    print(f"  AI={r['stages']:<28} | {' '.join(str(r['content']).split())[:150]}")
    return {"by_family": rows, "n": len(d),
            "micro_precision": round(tp_all / fl_all, 3) if fl_all else None,
            "micro_recall": round(tp_all / ai_all, 3) if ai_all else None,
            "primary_found": round(d.apply(lambda r: rules.primary_family(r["stages"]) in r["ru"], axis=1).mean(), 3),
            "unplaced": round(d["ru"].map(lambda s: s <= {"U", "P"}).mean(), 3)}


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "test"
    dev, test = splits()
    res = evaluate(dev if which == "dev" else test, show=set(sys.argv[2:]))
    print(pd.DataFrame(res["by_family"]).to_string(index=False))
    print({k: v for k, v in res.items() if k != "by_family"})
