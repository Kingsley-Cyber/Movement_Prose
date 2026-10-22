# Swanson A→B←C sweep, serendipity slots, review queue (2026-10-22)

Unparked by: Slice 1 done and mechanism vocabulary reviewed (agent, owner delegated). Lexical only, by decision.

## Predictions (written before code)
1. `discover --source <passage>`: B = concepts of kind mechanism or technique linked to A (phase, workflow and plain concepts excluded); C = paragraph or list item ≥ 80 chars, in another article, linked to a technique/mechanism/directive concept, sharing zero content tokens with A outside B's aliases; score = w(A,B)·w(B,C)·ln(N/df(B)) × 1.5 cross-chapter. From the "floaty" rhythm-metrics passage it returns between 3 and 25 hypotheses, at least one cross-chapter, and no bridge through a phase concept.
2. `discover --query "<text>"` seeds A from the top `find` hit and behaves the same.
3. Hypotheses go to `review_queue` in memory (status pending); `resolve` with a relation from the closed set writes an `agent_links` edge with the two passage ids and the bridge concept as evidence. Accepting does not change retrieval until the allocator reads edges.
4. `ask --discover 2` appends a "bridges" group of up to 2 hypotheses after the normal groups; the benchmark is unaffected (recall@10 stays 0.836) because the group is outside the top-k lists.
5. Runtime per discover call under 3 s on the 149-concept index.

## Measured
1. From the floaty rhythm-metrics passage: 8 hypotheses, 8 cross-chapter, 0 through a phase concept (prediction 1: 3–25, ≥ 1 cross, 0 phase → held). First pass of `--query` seeded a 62-char proxy line that links to no mechanism; seeding now prefers a substantive hit (≥ min-chars).
2. `--query` and `--source` share the path (held).
3. `review_queue` + `resolve` → `agent_links` edge with the bridge concept in the note; idempotent enqueue; `unrelated` rejects (held, tested).
4. `ask --discover 2` appends a "bridges" group; benchmark unchanged at 0.836 because the group sits outside the top-k lists (held).
5. Runtime under 3 s per call (tested).

## Honest reading
Bridges are only as good as the concept links: a seed that touches no mechanism or technique concept yields nothing, by design. Hypotheses are pending until resolved; nothing retrieves differently until the allocator reads accepted edges.
