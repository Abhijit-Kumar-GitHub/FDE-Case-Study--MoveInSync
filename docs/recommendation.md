# Play Store ratings: what is actually wrong, and what to fix first

*For MoveInSync Product, Engineering, Support and Transport Operations · Prepared by Abhijit, Forward Deployed Engineer candidate · 13 October 2026 · Public Google Play data through 11 October 2026 · Live monitor: {{DASHBOARD_URL}}*

## The answer

1. **The number is not the problem — yet.** The employee app shows **4.6★** in India (4.639 from 114,880 ratings). Among the 8 employee-commute apps I benchmarked, that is **#2**, behind only Safetrax Commuter (4.72), and MoveInSync has more ratings than the other seven combined. It is **0.011 stars from showing 4.7**.
2. **The problem is what people read.** Written reviews over the last 12 months average **3.84★**, and **24% are 1★**. **9 of the first 10 reviews a visitor sees are 1–2★, and 9 of them have no reply.** MoveInSync stopped replying in mid-2024, falling from about 97% of reviews answered to 3%. Safetrax answers 100% and Routematic 92%.
3. **It is the app, not the cabs.** Of the 1–2★ reviews that name a problem, **73% are about the app itself**. 19% are about the transport service and 1% about employer rules. Late, unassigned or missed cabs come up in under 5%. The four biggest themes are all engineering work: **stability (17%), login (14%), self-booking (11%), interruptions and UI (11%)**.
4. **It is getting worse right now.** Stability complaints rose from 12–16% of negative reviews in the previous three quarters to **25%** in Q3 2026 (statistically significant, p ≈ 0.01), concentrated in versions 12.16–12.19. They include a **false "not installed from Play Store" error** that locks riders out until they reinstall.
5. **Do this week:**
   - stop the false lock-out, and gate releases on crash and review signals
   - restart replying, starting with the reviews visitors see first
   - remove the forced trip-rating wall, and confirm the rating flow complies with Google Play policy (a few riders say it offers only 4 or 5 stars)
   - send safety reports found in reviews to the safety desk within 24 hours

**Expected result:** halving the top four themes would move the written-review average from 3.84 to about **4.0** and cut the 1★ share by about **5 points**. A 30–70% fix gives a range of +0.10 to +0.24. Once those fixes land, asking satisfied riders for a rating at the right moment is what flips the display to **4.7**.

## 1. Where the rating really stands

| App | Rating (India) | Shows | Ratings | Written reviews, last 12 months: average · 1★ share · replied |
|---|---|---|---|---|
| Safetrax Commuter | 4.720 | 4.7 | 24,144 | 2.89★ · 47% · 100% |
| **MoveInSync** | **4.639** | **4.6** | **114,880** | **3.84★ · 24% · 3%** |
| Routematic | 4.339 | 4.3 | 34,914 | 3.51★ · 26% · 92% |
| Five smaller apps | 2.5–3.5 | | 253–4,865 each | |

Three things this table hides:

- **The store number and the written reviews are two different things.**
  - About 1,260 new ratings arrive each month, and only about 1 in 5 comes with text.
  - The silent ratings are overwhelmingly positive: the store's distribution is 86% 5★ and 6% 1★.
  - The written reviews are not: 64% 5★ and 24% 1★.
  - New employees and HR teams evaluating vendors read the written ones.
- **MoveInSync's written reviews are better than the leader's.** Safetrax's written reviews average 2.89★, with 47% 1★, over the same period. Its higher store number must therefore come from silent ratings. It also replies to every review; MoveInSync replies to 3%.
- **The rating is per country.** The same app shows 4.6 in India, **4.3 in the US**, 4.5 in the UK and 4.8 in the UAE. A client's head office abroad sees a different number from riders in India. This memo uses India throughout.

So "lower than it should be" comes down to four measurable gaps:

| Gap | Today | Target in 90 days |
|---|---|---|
| Displayed rating (India) | 4.639, shows 4.6 | ≥ 4.65, shows 4.7 |
| 1★ share of written reviews (28-day rolling) | 24% | ≤ 18% |
| Reply rate on 1–3★ reviews | 3% | ≥ 90% within 48 hours |
| The 10 reviews a visitor sees first, answered | 1 of 10 | 10 of 10 |

## 2. Why: what 769 one- and two-star reviews say

I labelled every 1–2★ written review from the last 12 months (769), every 3★ review, the longer positive ones, and a sample from the three years before: **1,400 in all**. Each label records:
- the stage of the rider's journey
- who would have to fix it
- the sentiment of the words, separately from the stars
- whether the review describes a safety risk

How the labels were made and checked is in Appendix A.

| Stage of the journey | Share of 1–2★ reviews | Who would fix it | What riders say |
|---|---|---|---|
| App stability & speed | 17% | App | Crashes; won't open after updates; false "not installed from Play Store"; slow loading |
| Onboarding & login | 14% | App | OTP not arriving (6.4%); logged out again and again (5.9%); "not registered" with no explanation |
| Self-booking | 11% | App, sometimes employer rules | Bookings failing or vanishing; can't edit without cancelling; confusing two-step flow; cut-offs |
| UI & interruptions | 11% | App | Redesign harder to use; terms on every open; forced trip ratings; permission nags |
| Issue reporting & support | 10% | Operations and app | Helpdesk unreachable; complaints with no status; can't rate a bad trip |
| Pickup & boarding | 9% | Mixed | Can't reach the driver; wrongly marked no-show; cab late; QR or OTP problems |
| Allocation & routing | 9% | Operations | Long pooled routes; very early pickups; cab not assigned |
| Live tracking & ETA | 9% | App | Stale location; ETA jumping; map zoom resetting |
| Notifications | 5% | App | Cab details missing or late, or too many alerts |
| Ride & drop | 3% | Operations | Driver behaviour; late drops |
| Too vague to place ("worst app") | 24% | — | — |

Shares overlap, because one review can mention several stages.

**The five failures the brief names, measured** (share of 1–2★ reviews):
- app glitch: 17%
- booking fails: 11%
- wrong route: 5%
- late, unassigned or missed cab: 4.7% (late cab alone: 2.5%)
- safety concern: 3%

### Finding 1: a stability regression is live now

| Share of ≤3★ reviews about… | Q4 2025 | Q1 2026 | Q2 2026 | Q3 2026 |
|---|---|---|---|---|
| App stability & speed | 16% | 12% | 16% | **25%** |
| Onboarding & login | 20% | 17% | 14% | 8% |

- **Where it comes from:** versions 12.16.0, 12.17.0 and 12.19.0 carry it. Stability is 32%, 22% and 31% of their negative reviews.
- **The current version is worse than average:** 12.19.0 has 31% 1★ reviews against a 24% baseline. That isn't statistically significant yet, so it's on watch.
- **The false lock-out is new and growing:** 9 of the 12 "not installed from Play Store" reviews ever written appeared in Jul–Sep 2026.
  > "showing that it can't open as it is not downloaded from playstore. in last 3 weeks I uninstall an installed it for 10 times due to the same error" (2★, Aug 2026)
- **It has happened before, at larger scale:** in Q4 2023, 43 reviews reported a false "cannot be opened on a rooted device" block on ordinary phones. Two waves of the same failure suggest a pattern: a device or install check that blocks the app whenever it isn't sure keeps locking out legitimate riders.
- **Fixes do show up in reviews.** Login complaints fell from 20% to 8% after a spike in October 2025. That spike would have been caught in its first week by the monitor described in section 4.

### Finding 2: self-booking, the step that matters most, has lost clarity

Booking problems are 11% of negative reviews.

> "Booking a shuttle is now a 2 step process previously it used to be 1. I got confused and thought I had booked a cab while I hadn't." (1★, Jul 2026, v12.14.1)
>
> "I booked on a Sunday and automatically the date was of Tuesday instead of Monday." (1★, May 2026)
>
> "It was showing me … whole booking is cancelled. Now I called transport, they are very rudely telling that I didn't cancel before cut off." (1★, Dec 2025)

Employer rules, such as cut-offs, booking windows and waitlists, directly cause only 1–2% of reviews. But when the app accepts an action and a rule reverses it later, the app takes the blame.

### Finding 3: riders are interrupted on the way to their trip

- **Interruptions riders describe:**
  - terms accepted "more than 500 times"
  - a full-screen banner on every launch
  - microphone permission nags
  - a seat-belt confirmation placed in front of the boarding OTP
  - a mandatory trip rating that blocks the current trip: *"I have to mandatorily give a review of the previous ride before I can access current ride details"* (1★, Mar 2026)
- **Forced rating requests cost stars.** 20 reviews in 12 months complain about forced or repeated rating requests. One rider lowered their store rating from 5 to 3 because of it.
- **A policy risk to check on day 1.** Three reviews point at the in-app rating step:
  - one says it offers "only 4 or 5 stars" (Jul 2026, v12.15.0)
  - one says it was "not accepting until I gave 5 star" (Dec 2025)
  - one asks to stop the "Play Store review" prompt after every ride (Jul 2026)

  If any in-app step decides who gets sent to the Play Store prompt, that is *review gating*, which Google Play prohibits. Three reviews aren't proof, but checking takes an hour.

### Finding 4: nobody answers, so complaints go public

- **Replies stopped in June–July 2024.** Before that, 98.6% of 1★ reviews got an answer, although 63% of all replies used the same template text.
- **The complaint path itself is a theme.** 10% of negative reviews are about it: the helpdesk is unreachable, complaints get no status, and there's no way to dispute a false no-show or rate a badly routed trip.
- **Safety reports sit unanswered in public.** 24 reviews in 12 months were flagged as possible safety risks, including harassment, rash driving, women dropped alone at night, and SOS blocked by pop-ups or forced logouts. A person still has to confirm each one.

### What is not the problem

- **Stars contradicting words:** only 1.6% of reviews, so the stars can be trusted.
- **Reviews in other languages:** negligible in volume.
- **Operations:** a real problem but a minority, at 19% of specific complaints (routing, late cabs, drivers). These belong with the transport desks (OPS-1), not the app team.

## 3. What to do, in order

| When | ID | Do this | Owner | Effort | Success metric |
|---|---|---|---|---|---|
| This week | INT-1 | Stop false "not installed from Play Store" lock-outs: never block launch on an unsure verdict; add a kill-switch | Android | S | Integrity reviews 9 → 0 next quarter |
| This week | REL-1 | Staged rollouts that halt automatically on crash, ANR or review regressions | Release owner | M | No regressed version reaches 100% |
| This week | REP-1 | Reply to every 1–3★ review within 48h, top 20 visible first, with the actual fix (**drafts for those 20 are ready**: reply_drafts.md) | Support | S, ongoing | ≥ 90% replied; top 10 all answered |
| This week | RAT-1 | Make trip rating skippable; remove any star pre-filter before the Play prompt | Product + Legal | S | Forced-rating complaints → 0 |
| This week | SAFE-1 | Safety reports in reviews → safety desk, reply and incident within 24h | Safety desk | S | 100% actioned in 24h |
| 30 days | LOG-1 | Keep riders signed in (silent token refresh, offline trip card, biometric unlock) | Identity + Android | M | Session complaints < 1% |
| 30 days | LOG-2 | Reliable OTP with fallback channels; say why login failed | Identity | M | Login complaints −70% |
| 30 days | BOOK-1 | Unambiguous booking: confirmation and receipt, no auto date change, edit without cancel | Product | M | Booking share 11% → < 5% |
| 30 days | BOOK-2 | Show employer rules (cut-offs, windows) at the moment they apply | Product | S | Rule disputes halved |
| 30 days | INT-2 | Terms once per version, non-blocking banners, permissions on demand, OTP before the seat-belt check | Product | S | Interruption complaints → ~0 |
| 90 days | TRK-1 | Honest tracking: label stale positions, live-position ETA, keep zoom, bring back co-rider sequence | Android + driver app | L | Tracking share < 5% |
| 90 days | LOOP-1 | In-app complaints with status, no-show disputes, routing to transport desks | Product + Support + Ops | M | Support share halved |
| 90 days | OPS-1 | Weekly digest of service complaints, by city and site, for transport desks | Operations | M | Ops complaints trend down |
| 90 days | ASK-1 | Play In-App Review only after an on-time trip, at most every 90 days, no filtering | Product | S | Display crosses 4.7 |

Every item has its evidence, likely cause, exact change, acceptance criteria and day-1 check in **backlog.csv**, which imports straight into Jira or Linear. How the analysis was done and checked, including what I corrected along the way, is in **process.md**.

**Why this order:**
- **This week** stops active damage: a regression shipping now, a public page nobody answers, and a prompt that may break policy. None of it needs new features.
- **30 days** fixes the top complaint themes.
- **Asking for ratings comes last on purpose.** Prompting riders before the crashes and logouts are fixed would invite more 1★ reviews.

### Expected impact

| Theme fixed | 1–2★ reviews (12 months) | Written-review average gain if 30% / 50% / 70% fixed |
|---|---|---|
| App stability & speed | 107 | +0.03 / +0.05 / +0.08 |
| Onboarding & login | 101 | +0.03 / +0.05 / +0.07 |
| Self-booking | 70 | +0.02 / +0.04 / +0.05 |
| UI & interruptions | 68 | +0.02 / +0.03 / +0.05 |
| **All four** | **346** | **+0.10 / +0.17 / +0.24, taking 3.84 to 3.94 / 4.01 / 4.08** |

At the 50% level, the 1★ share drops by about 5 points. The model assumes that riders whose problem is fixed would write 4★ instead (A6).

The displayed store rating moves more slowly, because it includes about 115,000 older ratings; the daily snapshot will show how fast. Crossing 4.65 takes on the order of a few thousand extra 5★ ratings: about 3,600 if every rating counted equally, and fewer given that Google weights recent ratings more. That is roughly three months of today's rating volume, or 0.25% of daily riders asked once (ASK-1).

## 4. Keeping the answer current

"How are our ratings?" is now answered automatically ({{REPO_URL}}):

- **Daily:**
  - a scheduled job pulls the listing and any new reviews
  - it records the store rating, labels the new reviews and refreshes the dashboard
  - Google doesn't publish a country's rating history (paid tools sell it), so this free daily record starts on 12 Oct 2026
- **Weekly:** a digest is posted as a GitHub Issue. It covers:
  - the rating
  - last week against the previous four
  - the top complaint themes
  - release watch: a version is flagged when its 1★ share is significantly above baseline
  - the reply rate
  - how many reviews need a person
- **Needs-review queue:** safety reports (within 24 hours), stars that contradict the words, and reviews the AI couldn't place.
- **Cadence:** a 15-minute weekly review using the digest, with the release owner, the support lead and an operations representative. The same monitor tracks every backlog item's success metric.
- **Cost:**
  - **without an API key:** it runs free on keyword rules
  - **with a key:** Claude Sonnet 5.5 labels new reviews through the Batch API. Measured on real review text, that is about $0.02 for a typical week (66 reviews), and about $0.70 to relabel a whole year. Each review is labelled only once.

## 5. Questions for day 1

1. **Play Console:** what are the crash, ANR and startup-failure rates for 12.16–12.19? How do ratings break down by version and device?
2. **The install/integrity check:** how does it decide, and what happens when the verdict isn't available?
3. **The rating prompt:** is the Play In-App Review API used? What triggers it, and is there any in-app star step before it?
4. **Sessions:** why do they expire — our token lifetime or a client's SSO policy? Which clients are affected?
5. **OTP:** what is the delivery success rate by operator and by channel?
6. **Replies:** who owned review replies until mid-2024, and why did it stop?
7. **Routing reviews to sites:** can a review be mapped to a client or site (app flavour, account email) so it reaches the right transport desk?

## 6. What not to do

- **Don't incentivise reviews or pre-filter who gets asked.** Both break Google Play policy and can get ratings removed.
- **Don't paste one template on every review.** Answer the specific issue, and come back when it's fixed.
- **Don't push for more ratings before the fixes land.** The stability, login and interruption fixes come first.
- **Don't mix up app bugs and operations complaints.** The labels say which is which, so each goes to the team that can fix it.

---

### Appendix A: how this was done

- **Data:** public Google Play data. Store ratings and the "most relevant" ordering are from the India storefront. Written reviews are English-language reviews from all countries, because Google returns the same reviews whichever country is requested (tested).
  - **Employee app** (com.moveinsync.ets): 24,315 written reviews (Mar 2014 – Oct 2026), the listing's rating and distribution, and the 40 reviews shown first.
  - **Comparisons:** seven competitor apps and two driver apps.
  - **History:** archived copies of the listing (Wayback Machine) for the growth in rating count.
- **Labelling:**
  - **What was labelled:** 1,400 reviews, using a versioned prompt (`prompts/classify_v1.md`) with 30 journey codes, plus who would fix it, text sentiment and a safety flag.
  - **Who labelled:** Claude (Opus 5.5, through Claude Code). {{AUDIT_SENTENCE}}
  - **The free fallback:** keyword rules agree with the AI's main theme 69% of the time; per theme, 62–94% of what the rules flag matches the AI labels. They also act as a second opinion for the review queue.
- **Statistics:**
  - version comparisons use 95% Wilson intervals and need at least 30 reviews
  - the impact figures come from a simple counterfactual, not a forecast
- **Tools:**
  - **Python:** google-play-scraper, pandas, Plotly
  - **Claude Code:** analysis, labelling and code
  - **GitHub:** Actions for the scheduled job, Pages for the dashboard

### Appendix B: assumptions

- **A1:** "Written reviews" means English-language reviews with text, from all countries; Google doesn't split reviews by country. Most riders are in India, but the figures aren't India-only. They approximate all ratings but don't equal them.
- **A2:** A version's release date is approximated by when it first appears in reviews.
- **A3:** The brief's 1.5M daily riders is used only to give a sense of scale.
- **A4:** Labels were produced by Claude through Claude Code using the production prompt, not by the production Sonnet runner. Accuracy comes from a person checking a random sample.
- **A5:** Effort estimates are judgement calls.
- **A6:** The impact model assumes a fix removes 30–70% of a theme's 1–2★ reviews, and that those riders would write 4★ instead.
- **A7:** Only English reviews are analysed. Hindi-language reviews are negligible in volume.
- **A8:** Google Play rounds to one decimal. The "about 3,600 extra 5★" figure treats the displayed distribution as raw counts. Google weights recent ratings and localises by country, so the figure is indicative only.
- **A9:** Ratings differ by country storefront, while rating counts are global. India is used throughout.
