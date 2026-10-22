# Benchmark accepted as ground truth, agent-judged (2026-10-22)

Owner delegated the review (DECISIONS.md 2026-10-22). The 32 queries stand as ground truth with `reviewed_by: agent`; the two label-mode queries whose expected ids followed lexical order are replaced by six label-mode queries whose expected ids were chosen by reading the passages.

## Predictions (written before the change)
1. Query file: 30 find + 6 lookup = 36 queries; meta `reviewed_by: agent (owner delegated 2026-10-22)`, `owner_reviewed: false`, `accepted_as_ground_truth: true`.
2. A new all-flags-off baseline on the 36 queries scores lower than 0.740 because label-mode queries chosen by reading are harder for lexical labels: recall@10 between 0.66 and 0.74.
3. `tune-rerank` on the 36 keeps the four current flags and now also keeps `judged_labels`, because judged passages are among the expected ids in the new label-mode queries; final recall@10 ≥ 0.85.
4. The gate test reads the newest baseline file, so the recorded baseline moves with the query set without editing the test.

## Measured
1. 36 queries (30 find, 6 lookup); meta updated (held).
2. All-flags-off baseline on the 36: recall@10 0.678, MRR 0.804 (prediction 2: 0.66–0.74 → held).
3. Tune: judged_labels KEPT (recall 0.826, MRR 0.812 at its step); final flags {"any_word_fallback": true, "per_article_3": true, "no_article_cap": true, "per_block_2": true, "judged_labels": true, "length_floor": true}; default after tune: recall@10 0.836, MRR 0.874 (prediction 3: ≥ 0.85 → MISSED).
4. Gate test reads the newest baseline file (held).

Per-query label-mode results after tune:
- q31 recall 0.75 rr 1.00 missing a094#0018
- q32 recall 0.50 rr 1.00 missing a035#0021, a022#0006
- q33 recall 1.00 rr 1.00
- q34 recall 0.33 rr 1.00 missing a054#0456, a022#0009
- q35 recall 1.00 rr 0.25
- q36 recall 0.50 rr 1.00 missing a035#0029, a054#0357
