---
name: ratings-report
description: Answer "How are our Play Store ratings?" and follow-ups (how did version X do, what are riders complaining about this week, is anything regressing) for the MoveInSync employee app, from this repo's data. Use whenever someone asks about the app's ratings, reviews, a release's reception, or the needs-review queue.
---

# Ratings report

Answer from data, not memory. Every number you quote must come from a file below.

## Refresh first
- `python run.py` (needs network; ~2 min). If offline or asked for "last known", use `python run.py --skip-scrape`.
- With `ANTHROPIC_API_KEY` set, new reviews are labelled by the production runner; otherwise keyword
  rules label them. If many new reviews were rule-labelled and precision matters, offer to run the
  `label-reviews` skill.

## Where the answers are
| Question | Source |
|---|---|
| The headline answer | `docs/weekly_digest.md` (store rating, last 7 days vs prior 4 weeks, top themes, release watch, replies, queue) |
| Store rating history | `data/snapshots/history.csv` (daily, India storefront; the series starts 2026-10-12) |
| Trends, versions, benchmark, replies, visitor view | `data/processed/metrics.json` (`windows`, `monthly`, `versions`, `benchmark`, `replies`, `visitor_view`) |
| Themes, attribution, clusters, impact | `metrics.json` → `themes` |
| A specific version or date range | filter `data/raw/com.moveinsync.ets.csv` on `reviewCreatedVersion` / `at`; join labels from `data/labels/llm_labels.csv` |
| What needs a person | `docs/needs_review.csv` (safety first) |

## How to answer
1. Lead with one sentence: the store rating (exact and as shown), and whether written reviews got
   better or worse than the prior 4 weeks.
2. Then at most three bullets: biggest complaint theme now, any release flagged in release watch
   (say "watch" vs "regression" exactly as the digest does), and open safety items.
3. For a version question, give n, 1★ share with its 95% interval (`analyze.wilson`), the 12-month
   baseline, and the top themes for that version. Say so if n < 30.
4. Quote at most two reviews, verbatim, with stars and date.
5. Never present rule-labelled themes as precise; say "keyword-rule estimate" when they are.
