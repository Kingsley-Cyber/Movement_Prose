# Allocator: coverage-first quotas, soft decay, roll-ups, nuance hop (2026-10-22)

Unparked by: the review queue produced editorial edges (12 accepted hypotheses → `agent_links` with evidence).

## Predictions (written before code)
1. Behind a new flag `allocator`, text-mode results are allocated instead of truncated: every resolved concept's top hit first (coverage), per-concept quotas proportional to relevance share (min 1), remaining slots by score × decay where decay = (1 − λ_block·spread·n_block)(1 − λ_article·spread·n_article) with λ_block 0.35, λ_article 0.15, spread default 0.5; dropped same-block hits roll up as `(+N in block)`; a candidate with an accepted `agent_links` edge to an already-chosen hit gets γ = +0.05 and the hit is annotated with the relation.
2. `--spread` and `--per-concept` on `find`/`lookup`; a coverage footer per concept (shown / linked, articles reached).
3. Gate: the tune keeps `allocator` only if recall@10 does not drop below 0.836. Prediction: kept, recall 0.836–0.86, MRR within ±0.02; the nuance hop fires on at most 2 of 36 queries because only 12 edges exist.
4. 1,500-char budgets hold: the footer costs under 200 characters.

## Measured
1. Built as specified behind `allocator`: coverage first, quotas by relevance mass (min 1), decayed free slots, roll-ups, nuance hop over `agent_links` with annotation, coverage footer, `--spread`, `--per-concept` (held; 3 unit tests + 1 live test).
2. Gate: at its step the flag scored recall@10 0.734, MRR 0.704 against 0.826 / 0.812 without it → **dropped** (prediction 3: MISSED). Cause, read from the per-query rows: coverage-first puts a weak concept's best hit at rank 1 (MRR falls), and the query group's quota takes slots from the dominant concept (recall falls). Default retrieval after this step is unchanged: 0.836 / 0.874.
3. The nuance hop fired on no benchmark query: the 12 edges connect passages that the benchmark does not pair.
4. Footer under 200 chars (held).

## Honest reading
The allocator does what the owner's spec says, and the spec's goal (coverage of every named concept with roll-ups) is exactly what the benchmark penalises, because the benchmark rewards the strongest concept's passages at the top. Both are legitimate; the gate rule says the default follows recall. It stays available: `find --spread 1.0` with the flag set in rerank.json, or by passing `rerank={"allocator": True}` in code. Revisit with a coverage-oriented metric (concepts covered in top-k) alongside recall if the owner wants coverage to win.
