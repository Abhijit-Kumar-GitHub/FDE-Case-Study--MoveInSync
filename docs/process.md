# How I got here

The decisions behind the recommendation, what I checked, and what I got wrong first and corrected.
For tools and reproducibility, see the [README](../README.md).

## 1. Framing before data

Four lines in the brief shaped the plan:

- **"The step that matters most: the employee books their own ride."** Self-booking gets its own section, not one theme among many.
- **430+ enterprise customers.** It's B2B2C, so employers set rules like cut-offs and booking windows that riders blame on the app. I added "employer policy" as a third owner next to app and operations.
- **"Not a one-time ask."** The answer had to be a monitor that keeps answering, not a single report.
- **"Lower than they should be."** Compared to what? I checked that before reading any reviews.

## 2. Testing the premise first

- **Benchmark.** I pulled the listing figures for MoveInSync and 7 employee-commute competitors. MoveInSync came out #2 of the 8, with more ratings than the other seven combined. So the useful question became "what does *should be* mean?" I turned it into four measurable gaps (memo, section 1).
- **Ratings differ by country.** Archived copies of the listing (Wayback Machine) showed values that didn't fit together: 4.32 in 2022, 3.33 in 2024, 4.36 in July 2026, against 4.64 live.
  - The archive crawls from the US, and the Play Store shows each country its own rating: India 4.64, US 4.32, UK 4.49, UAE 4.82.
  - So I didn't build a rating history from the archive. I only used its rating *counts*, which are global, to estimate the monthly inflow.
- **The rounding rule.** 3.49 displays as 3.5 and 4.557 as 4.6, so the Play Store rounds rather than truncates. That gives "0.011 stars from showing 4.7".

## 3. Reading before counting

- **The first taxonomy missed the biggest pattern.** I read a sample of recent negative reviews before fixing the codes. The draft I started from had no place for forced re-login and OTP failures, or for launch interruptions (terms on every open, banners, forced trip ratings), so I split those out.
- **Commute jargon.** In this app, "login" and "logout" usually mean the trip to the office and the trip home. "Logout cab was late" is a cab complaint, not a sign-in problem. The keyword rules and a test guard against this.

## 4. Labelling with AI, and keeping it honest

- **A versioned prompt, not a chat.** `prompts/classify_v1.md` and `schema.json` are the artifact: the same prompt and codes for this interactive run and for the production API runner.
- **What was labelled.** 1,400 reviews in 10 chunks: every 1–3★ review from the last 12 months, the longer positive ones, and a sample from the three years before. A script validated every chunk (IDs, allowed codes, one label per review) before import.
- **A second opinion.** Free keyword rules run independently. Reviews where the AI said "unclear", stars that contradict the words, and every safety flag go to a person. I tuned the rules for precision on 70% of the audited labels and scored them on the other 30%, which tuning never saw. Overall precision rose from 0.74 to 0.86 (0.90 or more for 5 of 10 themes), and recall settled at 0.55. I stopped there: going further would have meant fitting the test set.
- **A person checks the AI.** I hand-checked 50 random labels and all 30 safety flags.
  - **Labels:** 47 of 50 were right (94%).
  - **Safety flags:** 28 of 30 were genuine, and 18 of those describe a specific incident.
  - **Two of the three label misses were one rule:** I had attributed routing complaints to operations alone, but the brief says *the system* plans the route. MoveInSync's own routing engine, configured with the operations team, is behind them.
  - **The notes also exposed a gap in the codebook:** home-address problems (wrong pin, can't change it, not synced from the company portal) had no code of their own and were split across two others.
  - **I fixed both as codebook v1.1 and applied them to all 1,400 labels as recorded overrides,** rather than correcting only the rows I happened to check. The core finding (73% of specific complaints are about the app) held.
- **Cost was measured, not guessed.** A dry run on real review text prices the production path at about $0.02 a week.

## 5. A second pass over every claim

Before finalising, I re-tested each headline claim against the raw data and re-read the code that produced it. That pass changed:

| What I first had | What the check showed | Change |
|---|---|---|
| Written reviews described as "India storefront" | Requesting India and US returns the identical newest 200 reviews; Google doesn't split reviews by country | Described as English-language reviews from all countries. Store rating and "most relevant" order stay India-specific (tested: they differ). |
| 23 forced-rating complaints | The pattern also matched "accu**rate**" and "frust**rating**" | 20, with word boundaries |
| "Rooted device" lock-outs: a handful in 2023 | Counted from the labelled sample; the full data has 43 in Q4 2023 | INT-1 now cites both waves (2023 rooted check, 2026 installer check) |
| "Late cabs: 2.5% of complaints" | Too narrow; easy to call cherry-picked | Late, unassigned or missed cabs: 4.7%, still small |
| Safety flags from the keyword rules: 474 | They fired on praise ("super safe") and on "c**rash**es" | Risk words only, word boundaries, ≤3★ or negative text: 30 items |
| Gating-evidence search | Matched "only 48 hours" | Tightened; three real reviews remain, framed as a check, not a finding |
| Reply latency | Negative for edited reviews (Google's date is the last edit) | Excluded those reviews |
| Trend charts | Included half of the current month | Partial month left out |
| "#2 of 8 employee-commute apps", "the only record of the rating" | Overreach | "of the 8 benchmarked"; "Google doesn't publish it; this record is free" |
| Q3 stability jump | Needed a test, not an eyeball | Two-proportion test: z = 2.6, p ≈ 0.01 |

## 6. Doing, not only recommending

- **REP-1 drafts.** Replies to the 20 reviews visitors see first are already drafted (`reply_drafts.md`). They're specific, under Google Play's 350-character limit, and use `[confirm: …]` for anything only MoveInSync can verify.
- **A monitor that keeps answering.** It runs daily and posts the weekly answer as a GitHub Issue, so "How are our ratings?" never needs someone to start an analysis.

## Tools

- **Python:** google-play-scraper, pandas
- **Dashboard:** Plotly.js
- **Automation and hosting:** GitHub Actions and Pages
- **PDF:** headless Microsoft Edge
- **Claude Code (Claude Opus 5.5):** planning, writing code, labelling reviews with the versioned prompt, and drafting

Every number in the memo traces to `data/processed/metrics.json`, and every quote is verbatim.
