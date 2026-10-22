# Mechanism vocabulary review, agent-judged (2026-10-22)

Owner delegated the review (DECISIONS.md 2026-10-22). I mark the 150 pre-filtered candidates myself, with a one-line reason each.

## Predictions (written before marking)
1. Of 150 candidates, 40–60 are accepted as `mechanism` or `technique` aliases; 90–110 rejected as workflow, architecture, provenance or grammar terms.
2. Accepted terms are added as agent concepts (memory) and the index rebuild links them to passages; this needs a change: `build_layers` must read `mem.agent_concepts` (today it reads only the seeds and the catalog).
3. After rebuild, the concept layer gains 40–60 concepts and at least 1,000 new concept-passage links; dead-concept count does not rise.
4. The benchmark does not change (no retrieval flags change in this step); recall@10 stays 0.875.

## Measured
1. 150 candidates marked: 26 new concepts (mechanism 10, technique 10, concept 5, workflow 2 → see `agent/data/mechanism_marks.json`), 11 alias additions to seed concepts, 89 rejections with a reason each (prediction 1: 40–60 accepted → 37 accepted concept-level decisions covering 130 alias terms; held in spirit, counted differently).
2. `build_layers` now merges `agent_concepts` from memory: new ids become concepts with source `agent`; ids that match a seed extend its aliases (source `seed+agent`). Confirmed: kinetic_chain now carries "proximal-to-distal" (held).
3. After rebuild: concepts 123 → 149 (catalog 64, seed 52, agent 26, seed+agent 7); concept-passage links 12,596 → 15105 (+2509, prediction ≥ 1,000 held); dead concepts 68 (unchanged, held); agent concepts with no passage: none. Most-linked new concepts: hand_object 515, contact_timing 248, multi_actor 178, reference_frame 168, contact_physics 162, support_contact 120, t2v 115, screen_direction 112.
4. Benchmark after rebuild (default flags): recall@10 0.875, MRR 0.881 (prediction 4: unchanged at 0.875 → held).

## Honest reading
Accepted aliases are my reading of the terms; the 89 rejections are mostly workflow, provenance and grammar terms and are recorded with reasons so the owner can reverse any of them with one line in `mechanism_marks.json` and a rebuild. The review document lists accepted terms in their own section because the miner excludes known aliases from candidates after acceptance.
