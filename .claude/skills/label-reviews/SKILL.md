---
name: label-reviews
description: Label new MoveInSync Play Store reviews into journey stages, attribution, text sentiment and safety flags using the versioned prompt — the no-API-key runner for the classification step. Use when asked to label, classify or tag reviews, or when `python src/labels_io.py status` shows pending chunks.
---

# Label reviews

This is the interactive runner for the classification step. It applies **exactly** the prompt in
`prompts/classify_v1.md` with the codes in `prompts/schema.json` — the same files the production
API runner (`src/classify_api.py`) sends to Claude Sonnet 5.5. Do not improvise new codes.

## Steps
1. Read `prompts/classify_v1.md` and `prompts/schema.json` in full.
2. Export work: `python src/labels_io.py export` (skips anything already labelled or queued).
3. `python src/labels_io.py status` lists pending chunks in `data/labels/queue/`.
4. For each pending `chunk_NNN.jsonl`:
   - Read the whole chunk.
   - Write `chunk_NNN.labels.jsonl` next to it: one JSON object per input line, same order,
     keys `i, st, d, a, se, sf`, nothing else in the file.
   - Judge `se` from the text alone; the stars are shown only so mismatches can be computed later.
5. `python src/labels_io.py import` validates every labels file (ids, codes, one label per review)
   and appends good rows to `data/labels/llm_labels.csv`. Fix and re-import any chunk it rejects.
6. Run `python run.py --skip-scrape` to refresh metrics, the report and the needs-review queue.

## Quality bar
- Every review gets a label; `U` is a valid answer, a guess is not.
- Safety: when in doubt, set `sf: true` — a person reviews every flagged item.
- Labels are never rewritten after import. Corrections go in `data/labels/human_overrides.csv`
  (`reviewId,field,value,reviewer,note`) so the history of who changed what is kept.
