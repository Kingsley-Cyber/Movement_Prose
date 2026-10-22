# Mechanism vocabulary candidates (2026-10-22)

## Predictions (written before code)
1. The miner (hyphenated or compound terms, df 3..1% of passages, ≥ 2 chapters, not already an alias) yields 350–450 candidates.
2. Pre-filter A (share of the term's passages that carry unit/number markers: ms, fps, frames, deg, s, px, %, Hz, or a digit) and pre-filter B (share with a moment or slot label at score ≥ 2) separate mechanisms from meta-terms: "motion blur", "camera impulse", "center-of-mass", "time-to-peak" land in the top 50; "peer-reviewed", "natural-language", "provider-specific", "first-class" fall below rank 150.
3. Pre-filter C (the term occurs inside a requires / depends_on / conflicts_with clause or in a passage carrying such an edge) marks 20–60 candidates; those are the terms that would normalise the 138 unnormalised causal clauses.
4. Nothing is written to the index. `docs/mechanism_candidates.md` lists the top 150 with blank accept / reject / kind columns and the count of the remainder.

## Measured
1. 413 candidates from 16,304 prose passages (prediction 1: 350–450, held).
2. With the loose filter (any digit counts) "text-to-video" ranked 1 and "multi-shot" 7; known mechanisms: motion blur 13, camera impulse 85, center-of-mass 101, time-to-peak 290. Meta-terms were absent only because of a hand-written stop list, not the filters (prediction 2: MISSED). The strict filter (number with a unit only) moved the mechanisms' median rank 16 → 13 and the workflow terms' 7 → 12 on 17 probe terms; it is the default now. Only 34 of 413 terms have any unit-bearing passage, so the unit filter is a weak signal in this handbook; the label and causal filters do most of the ordering.
3. 62 candidates sit in or beside a causal clause (prediction 3: 20–60, narrowly missed); 7 occur inside a clause text, which is where normalising the 138 unnormalised clauses would start.
4. Nothing written to the index; `docs/mechanism_candidates.md` lists 150 with blank accept/reject/kind columns (held).

## Honest reading
The pre-filters separate mechanisms from meta-prose only partly. The review document is usable but the owner will reject roughly half of the top 150 (workflow and architecture terms such as cpcs-mx, application-level, research-to-representation). A better lexical signal would be "term appears in a table_row under a slot-labelled heading", which is cheap to add later; not added now to keep the step reviewable as delivered.
