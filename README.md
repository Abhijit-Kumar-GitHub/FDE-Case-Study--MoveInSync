# MoveInSync · Play Store ratings monitor

A recommendation on why MoveInSync's Play Store ratings are where they are and what to fix first, plus the
pipeline that keeps answering **"How are our Play Store ratings?"** every day without anyone running it.

| | |
|---|---|
| **The recommendation** (start here) | [`docs/recommendation.md`](docs/recommendation.md) · [web](https://abhijit-kumar-github.github.io/FDE-Case-Study--MoveInSync/recommendation.html) · [PDF](docs/recommendation.pdf) |
| **Slides** (9, with speaker notes) | [`docs/deck.pptx`](docs/deck.pptx) · [PDF](docs/deck.pdf) |
| **Live dashboard** | https://abhijit-kumar-github.github.io/FDE-Case-Study--MoveInSync/ |
| **Fix-first backlog** (imports into Jira or Linear) | [`docs/backlog.csv`](docs/backlog.csv) |
| **Needs-review queue** | [`docs/needs_review.csv`](docs/needs_review.csv) |
| **This week's digest** | [`docs/weekly_digest.md`](docs/weekly_digest.md), also posted weekly as a GitHub Issue |
| **Replies, ready to post** (REP-1, done on day 0) | [`docs/reply_drafts.md`](docs/reply_drafts.md) · full queue [`docs/reply_queue.csv`](docs/reply_queue.csv) |
| **How I got here** (decisions, checks, corrections) | [`docs/process.md`](docs/process.md) |

## The short version

- **The headline rating isn't behind the market.** The employee app shows **4.6★** in India (4.639, 114,880 ratings). That's #2 of the 8 employee-commute apps benchmarked, and it's 0.011 stars from showing 4.7.
- **Written reviews are harsher.** Over the last 12 months they average **3.84★** and **24% are 1★**. 9 of the first 10 reviews a visitor sees are 1–2★ and unanswered. Replies stopped in mid-2024.
- **The app is to blame, not the cabs.** **73%** of specific complaints are about the app itself. The biggest themes are stability (17%), login and home address (15%), interruptions and UI (11%), and self-booking (10%).
- **There's a live stability regression.** It spans versions 12.16–12.19 and includes a false "not installed from Play Store" lock-out.

## Run it

```bash
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py                 # scrape -> label new reviews -> metrics -> dashboard, queue, digest
python run.py --skip-scrape   # rebuild from data on disk
python run.py --memo          # also re-render the recommendation (HTML; PDF if Edge or Chrome is installed)
python -m pytest -q tests
```

**The scheduled job** is [`.github/workflows/refresh.yml`](.github/workflows/refresh.yml).
- **Every day at 07:00 IST** it records the store rating, pulls new reviews, labels them, rebuilds the dashboard and commits the results.
- **Every Monday** it opens a digest Issue. The Issue is labelled `regression` if a release is flagged.
- **Pages:** GitHub Pages serves `docs/`.

**One-time setup after forking or creating the repo:**
1. Settings → Pages → Deploy from a branch → `main` / `/docs`.
2. Settings → Actions → General → Workflow permissions → **Read and write**, so the job can commit and open Issues.
3. Optional: add an `ANTHROPIC_API_KEY` secret to label new reviews with Claude Sonnet 5.5 instead of keyword rules.
4. Actions → Ratings monitor → Run workflow, to run it once by hand.

## How it works

```
Google Play (public)                           prompts/classify_v1.md + schema.json  (versioned)
  │  src/scrape.py  daily snapshot + new reviews          │
  ▼                                                       ▼
data/raw/*.csv ─► label each NEW review once ─► data/labels/llm_labels.csv (+ human_overrides.csv)
                   • ANTHROPIC_API_KEY set  → src/classify_api.py  (Claude Sonnet 5.5, Batch API, budget cap)
                   • no key                 → src/rules.py keyword rules (free)
                   • interactive            → /label-reviews skill in Claude Code (how this submission was labelled)
  ▼
src/analyze.py + src/themes_metrics.py ─► data/processed/metrics.json  (every number in the memo comes from here)
  ▼
src/report.py ─► docs/index.html · docs/needs_review.csv · docs/weekly_digest.md · docs/backlog.csv
```

### Labels

**What each review gets:**
- **`stages`:** up to 3 of 30 journey codes, following the brief's journey: login → roster → **self-booking** → allocation → notifications → tracking → boarding → ride → complaint handling. Three cross-cutting codes cover stability, UI/interruptions and workplace features.
- **`attribution`:** who would have to fix it: app, operations, employer policy, or mixed.
- **`text_sentiment`:** judged on the words only, so it can be compared with the stars.
- **`safety_flag`.**

**How labels are handled:**
- Each review is labelled once and never relabelled, so trends don't shift when a model changes.
- The queue gets: stars that contradict the words, reviews the AI couldn't place, and every safety flag.
- A person's corrections go in `data/labels/human_overrides.csv`. They always win, and they become the gold set.

**How this submission's labels were made:**
- Claude (Opus 5.5) labelled 1,400 reviews through Claude Code, using the same prompt and schema as the production runner. That covers every 1–3★ review from the last 12 months, the longer positive ones, and 12 a month from the three years before.
- Every chunk passed `labels_io.py import` validation.
- **Human audit:** a person checked 50 randomly chosen labels and every safety flag (`data/labels/gold_audit.csv`).
  - **Random labels: 47 of 50 right (94%; 95% interval 84–98%).** Two of the three misses were the same rule: routing complaints had been attributed to operations alone, though MoveInSync's own engine plans the routes.
  - **Safety flags: 28 of 30 confirmed (93%).** 18 of the 28 describe a specific incident; 10 are general claims ("unsafe for women") without detail. Lost property and "misbehaviour" with no detail were wrongly flagged.
  - **The audit changed the codebook (v1.1):** routing and pickup-time complaints are now `mixed`, and home-address problems have their own code (`J1.address`). They had been scattered across two others. The new rules were applied to all 1,400 labels as recorded overrides (`data/labels/human_overrides.csv`), so every change is traceable. The headline finding (73% about the app) did not move.

### Cost of the AI step

These are measured on real review text with `python src/classify_api.py --what-if-days N`, using Claude Sonnet 5.5 through the Batch API:

| Volume | Reviews | Cost |
|---|---|---|
| A typical week | 66 | ~$0.02 |
| A month | 243 | ~$0.06 |
| A whole year, relabelled | 2,848 | ~$0.68 |

The cost is predictable before anything is sent: the runner counts the new reviews, estimates tokens, and aborts above `config.API_BUDGET_USD`. Thinking is off (`between_tools`) and output is a fixed JSON schema, so output length per review is bounded. Haiku vs Sonnet should be chosen by accuracy on the audited gold set, not by price; at these volumes the difference is cents.

### How good the free fallback is

The keyword rules (`src/rules.py`) are built for **precision over recall**:
- a theme fires only when its words appear together with a complaint
- a 4–5★ review with no complaint cue counts as praise
- generic phrases ("app not working") count only when nothing more specific matched
- anything the rules can't place is left for a person

They were tuned on 70% of the audited labels and are scored on the other **30% (420 reviews), which tuning never saw**. Reproduce with `python src/evaluate_rules.py`.
- **Precision** = of the reviews the rules flag with a theme, the share the AI labels agree with.
- **Recall** = of the AI's labels, the share the rules also catch.

| Theme | Precision | Recall | Before tuning (precision) |
|---|---|---|---|
| Allocation & routing | 1.00 | 0.36 | 0.67 |
| Ride & drop | 1.00 | 0.60 | 0.71 |
| Login & home address | 0.97 | 0.69 | 0.93 |
| Issue reporting & support | 0.94 | 0.38 | 0.83 |
| UI & interruptions | 0.92 | 0.49 | 0.76 |
| Self-booking | 0.86 | 0.41 | 0.86 |
| App stability & speed | 0.83 | 0.69 | 0.65 |
| Live tracking & ETA | 0.76 | 0.70 | 0.59 |
| Pickup & boarding | 0.76 | 0.55 | 0.76 |
| Notifications | 0.75 (8 flags) | 0.33 | 0.75 |
| **All themes** | **0.86** | **0.55** | **0.74** |

**What these numbers mean:**
- **Precision reaches 0.90 or more for 5 of 10 themes,** and overall it rose from 0.74 to 0.86.
- **Recall is deliberately modest.** The rules leave 45% of reviews unplaced rather than guess.
- **Per-theme accuracy isn't reported,** because it comes out at 0.92–0.99 for almost any rule set: most reviews don't mention a given theme.
- **The ceiling is the reference.** The AI labels the rules are compared with were 94% right in the human audit.

So the rules are good for counting trends cheaply and routing reviews to a person. They don't replace the AI step, which is why the design uses both. Tuning further on this data would start fitting the test set rather than improving the rules.

## How teams use it

- **Weekly, 15 minutes:** the release owner, the support lead and an operations rep read the digest Issue.
  - Release watch goes to the release owner.
  - The queue goes to Support.
  - Safety items go to the safety desk within 24 hours.
- **Any time:** ask Claude Code *"how are our ratings?"* or *"how did 12.19 do?"*. The `ratings-report` skill (`.claude/skills/ratings-report`) answers from this repo's data.
- **Replies:** Support works down `docs/reply_queue.csv`. The `draft-replies` skill drafts the next batch, specific and within Play's 350-character limit, for a person to check and post.
- **Correcting a label:** add a row to `data/labels/human_overrides.csv` (`reviewId,field,value,reviewer,note`).

## Repo layout

```
config.py                 apps tracked, storefront, windows, model, budget
run.py                    one-command refresh
prompts/                  classify_v1.md (the prompt) · schema.json (codes + JSON schema)
src/scrape.py             snapshot + incremental reviews (no usernames stored)
src/labels_io.py          export chunks · validate + import labels · overrides · audit sample
src/classify_api.py       production labeller (Sonnet 5.5 Batch API) · --dry-run / --what-if-days
src/rules.py              keyword rules: free fallback and second opinion (precision-first)
src/evaluate_rules.py     scores the rules on a held-out split of the audited labels
src/analyze.py            store view, trends, versions (Wilson intervals), replies, visitor view, benchmark
src/themes_metrics.py     journey heat map, attribution, clusters, gating evidence, impact model, rules eval
src/report.py             dashboard, queue, digest, backlog.csv
src/memo.py               recommendation.md -> HTML/PDF
src/deck.js               slide deck from metrics.json (pptxgenjs)
.claude/skills/           label-reviews · ratings-report · draft-replies
data/                     raw reviews, daily snapshots, labels, metrics
docs/                     GitHub Pages: dashboard, recommendation, backlog, queue, digest
tests/                    fast checks (rules, validation, API parsing, statistics)
```

## Assumptions and limitations

All nine assumptions (A1–A9) are listed in the recommendation's Appendix B. The main ones:
- **Ratings are per country.** India is used throughout; India 4.64, US 4.32. Rating counts are global.
- **Written reviews are English-language reviews from all countries.** Google returns the same reviews whichever country is requested (tested), so these figures aren't India-only. They approximate all ratings but don't equal them; about 1 in 5 new ratings has text.
- **The displayed distribution is weighted.** Google weights recent ratings, so the "~3,600 extra 5★" figure is indicative.
- **Release dates are approximate.** A version's date is when it first appears in reviews.
- **Public data has gaps.** Device, OS and client aren't visible, which is why each backlog item has a day-1 check against Play Console and internal logs.

## Tools used

Python (google-play-scraper, pandas), Plotly.js, GitHub Actions and Pages, and Claude Code. Claude Code was used for analysis, labelling the reviews with the versioned prompt, writing the code, and drafting. All public data; no usernames are stored.
