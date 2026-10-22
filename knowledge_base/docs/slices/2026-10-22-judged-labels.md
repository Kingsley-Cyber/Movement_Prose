# Agent-judged labels beside the lexical ones (2026-10-22)

Unparked by: the recall benchmark exists (ROADMAP trigger). Scope kept small enough to be reviewable.

## Predictions (written before code)
1. A memory table `agent_labels` (passage → judged moment / slot / tier, reason required, confidence, who, when) and a `label` command; the index tables do not change.
2. Retrieval reads judged labels only behind a `judged_labels` flag: label-mode lookups union judged passages (first) with lexical ones; hits show a judged label as `impact*`. `tune-rerank` decides whether the flag ships.
3. Of the ~80 benchmark expected passages, 15–35 carry no lexical moment or slot label; I judge those with a one-line reason each. Nothing else is labelled.
4. With the flag on, the two label-mode queries (q31, q32) do not lose recall and at least one gains; overall recall@10 stays ≥ 0.875, so the flag is kept.

## Measured
1. `agent_labels` in `agent_memory.db` (reason required; `none` records that no moment or slot applies, which corrects a wrong lexical label); `label` / `labels` commands. Index tables unchanged (held).
2. Flag `judged_labels`: label-mode lookups put judged passages first and drop passages judged `none`; hits show `impact*`. Tested (held).
3. 74 distinct expected passages, 30 without a lexical moment or slot (held). Judged 14: 8 assertions (hit-stop definition → impact/temporal_cadence; floatiness → follow_through; snappiness → execution; wind-up → anticipation/primary_action; speed lines → execution; causal secondary motion → follow_through; kinetic chain and weight transfer → execution/primary_action) and 6 corrections to wrong lexical labels (negative-prompt passage was slot secondary_motion; a planner-constraint passage was camera_optics; two Laban state rows and the budget header were slots from the word "time"/"action"; a symptom list was moment recovery). The other 16 carry no moment or slot and were left unlabelled rather than forced.
4. Gate: recall@10 0.740 → 0.875 (unchanged), MRR 0.802 → 0.771; the flag was dropped (prediction 4: MISSED). Cause: the benchmark has two label-mode queries and their expected order follows the lexical ranking, so promoting the judged hit-stop definition to rank 1 in q31 halves that query's reciprocal rank.

## Honest reading
The mechanism is correct and the labels are evidence-backed, but the benchmark cannot yet reward judged labels: it needs label-mode queries whose expected ids were chosen by reading, not by the lexical order (q31/q32 were). When the owner reviews `docs/queries.jsonl`, rerun `tune-rerank`; the flag is in `RERANK_FLAGS` and will be kept the moment it does not lower recall or MRR.
