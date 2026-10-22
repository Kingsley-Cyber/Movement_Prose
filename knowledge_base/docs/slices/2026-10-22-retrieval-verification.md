# Retrieval test and index backfill verification (2026-10-22)

Owner: "test retrieval and ensure any backfill index you have to do is completed."

## Backfill
Index rebuilt from `handbook.html` with agent memory merged. `python3 -m agent verify` (new, read-only, exit 1 on any failure) — 25 checks, all pass:
SQLite integrity of both files; index sha matches the source html; FTS rows = passages (18,120); every passage has a block; one-line summaries cover every passage, block, article, section and chapter; concept FTS rows = concepts (149); all 33 agent concept entries present in the index, every agent concept linked to passages, all 7 alias additions merged into their seed concepts; no orphan passage edges; every memory row that names a passage (labels, tags, notes, usage, review queue, links) resolves; every directive named in usage exists; every concept named in causal triples exists; rerank flags all known.
Counts: passages 18,120 · blocks 3,302 · concepts 149 · concept_passages 15,105 · edges 59,799 · judged labels 14 · agent links 12 · causal triples 37 · review queue 12 accepted / 2 rejected · usage events 39.

## Retrieval
- Test suite: 83 tests, OK (exit status checked, not piped away).
- Benchmark, default flags: recall@10 0.836, MRR 0.874 — identical to the recorded after-accepted run. All flags off: 0.678 / 0.804, identical to baseline v2.
- Timed live calls (15 commands incl. find with hyphen and fallback, label lookups with judged labels first, ask with four concepts, ask --discover, walk, concept pages for seed and agent concepts, near, read, outline, discover, allocator flag): max 0.09 s, total 0.19 s.

## Verdict
Index and memory are consistent and fully backfilled; retrieval reproduces its recorded numbers. Nothing is proven about video output: no render exists.
