---
name: draft-replies
description: Draft specific, honest developer replies to unanswered MoveInSync Play Store reviews, most-visible first, within Google Play's 350-character limit. Use when asked to reply to reviews, clear the reply queue, or prepare replies for Support.
---

# Draft replies

Support posts the replies; this skill prepares them. The goal is the REP-1 target: every 1–3★ review
answered within 48 hours, the reviews a visitor sees first before anything else.

## Steps
1. `python run.py` (or `--skip-scrape`) to refresh `docs/reply_queue.csv`. It is ordered: visible on the
   listing first, then safety, then upvotes, then recency.
2. Take the top rows with an empty `draft_reply` (default 20). Read each review in full and its `themes`.
3. Write one draft per review into `data/labels/reply_drafts.json` under `drafts`, keyed by `reviewId`:
   `{"rank_when_drafted": <visible_rank or null>, "reply": "<text>", "chars": <len>}`.
4. Re-run `python src/report.py`. It rejects any draft over 350 characters and rebuilds
   `docs/reply_drafts.md` for Support.

## How a reply must read
- **Specific:** name the rider's actual problem in their terms. Never paste one template across reviews.
- **Honest:** never claim a fix, version or date you have not verified. Put anything only MoveInSync can
  confirm in `[confirm: …]`. Support fills or deletes it before posting.
- **Useful:** one next step. Either update to a named version (if confirmed), a workaround, or the channel
  `app@moveinsync.com` with the detail you need (trip date, city/site, phone model).
- **Right owner:** rules set by the employer (cut-offs, booking windows, calling disabled, nodal points)
  → say so plainly and route to their transport desk. Don't blame the rider or the client.
- **Safety:** if the review describes a safety risk, do not draft a public reply. Mark the row for the safety
  desk (SAFE-1). Their reply follows the incident process.
- **Old reviews:** acknowledge the delay ("sorry this went unanswered for so long"). They stay visible for years.
- ≤ 350 characters, no emojis, no personal data, no internal ticket IDs.
