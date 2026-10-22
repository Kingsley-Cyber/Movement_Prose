# Timeline

Dates are 2026; times are file timestamps on this Mac where known.

| when | what | evidence |
|---|---|---|
| 10-17 15:37 | `handbook.html` compiled (CPCS Domain Handbook, 3.3 MB, 603 headings); same bytes as `video-compiler-plan/docs/research/handbook/2026-10-17-cpcs-domain-handbook.html`. | sha256 `fdb573b7…` on both |
| 10-20 10:45–10:54 | Research bundle delivered: 64-row SQLite lexicon, validator, examples, engine profiles, lexicon document. | file times; `validation_report.json` fingerprint `275537d8…` |
| 10-20 | Owner pastes the IDE-agent design (4 intent tiers, moment retrieval, taste profiles, YAML IR, bracketed prose). Plan written and approved: bundle-local toolkit; departures recorded (tiers ≠ slots, DB is a lookup, two fighters overlap, frames out of prose, negatives per engine). | plan file; `docs/DECISIONS.md` |
| 10-20 18:37 onward | `agent/` built: catalog, policy, ir, budget, check, emit, taste, engines, propose, fixtures, CLI; policy data; 33 tests; `SHA256SUMS.bundle`; run 001 (strike and block) with two arms. Finding: the bundle's own two-fighter `sequence_plan` fails its validator's actor-keyed duplicate-slot rule; the agent keys on the subject whose body moves. | `agent/`, `runs/001_strike_block/` |
| 10-21 morning | Owner: the handbook is the knowledge base; SQLite is its index. `handbook_index.db` built (21 chapters, 74 sections, 108 articles, 18,120 passages, 37,122 edges, FTS5). Then the knowledge layers: 3,302 blocks, 1,255 duplicate links, 21,625 summaries, 123 concepts linking 12,596 passages, 558 co-occurrence edges; `agent_memory.db` (tags, notes, links, usage). Query CLI: find, lookup, concept, walk, outline, read, near, deps, tag, tagged, note, link, concept-add, usage. 45 tests. | `handbook_index.db` meta; `docs/SCHEMA.md` |
| 10-21 | Owner: no embedding model. Retrieval rated 5/10 as built; gaps verified against code lines. | `docs/DECISIONS.md` |
| 10-21 | Simulations on the real index: diversity, alias expansion, token cost, epistemic rerank, `ask`, relations, budget, measurement state; allocator (quotas, decay, roll-ups, nuance); Swanson bridging in three runs (3,071 → 36 → 3 → 1 real cure); causal-clause normalisation (10 of 148); mechanism-term mining (382 candidates). | `docs/RETRIEVAL.md` |
| 10-21 | Owner locks the architecture (direct, Swanson, alias divergence, causal triples; mechanism vocabulary reviewed; slices by measured gain) and directs Slice 1 then `ask`. | `docs/DECISIONS.md`, `docs/ROADMAP.md` |
| 10-21 | Slice 1 built: FTS quoting fix, alias expansion with specificity, diversity with roll-up counts, matched terms + snippet, budget, short display ids accepted everywhere ids are read. Rank 5 `ask` built. 57 tests. `AGENTS.md`, `docs/` written. | `agent/query.py`, `agent/tests/test_slice1.py` |

| 10-21 goal run | Slice 3a: `check` records `cited` events per resolved handbook_ref; `python3 -m agent bench` (recall@10, MRR, retrieval→citation) over `docs/queries.jsonl`; query caches rekeyed on db path. 61 tests. Folder became a git repo (baseline commit 90828d3). | `agent/bench.py`, `docs/slices/2026-10-21-slice3a.md` |

| 10-21 goal run | Slice 3b: `docs/queries.jsonl`, 32 agent-authored queries (owner_reviewed: false). Baseline recall@10 0.740, MRR 0.787; without alias expansion 0.479; without diversity 0.880. Three queries dropped: the handbook has no passage on cel shading, rim light or kagenashi. | `docs/bench/2026-10-21-*.json`, `docs/slices/2026-10-21-slice3b.md` |

| 10-22 goal run | Slice 3c: flagged rerank + diversity parameters, `tune-rerank` greedy gate; kept any_word_fallback, no_article_cap, per_block_2, length_floor; recall@10 0.740 → 0.875, MRR 0.787 → 0.866; 67 tests. | `agent/data/rerank.json`, `docs/bench/2026-10-22-after-3c.json`, `docs/slices/2026-10-21-slice3c.md` |

| 10-22 goal run | Mechanism vocabulary: `python3 -m agent mine-mechanisms` (413 candidates; strict unit filter, label filter, causal-clause filter) → `docs/mechanism_candidates.md`, 150 rows with blank accept/reject/kind for the owner; nothing added to the index. | `agent/mechanism.py`, `docs/slices/2026-10-22-mechanism-candidates.md` |

| 10-22 goal run | Unparked "agent-judged labels": `agent_labels` memory table, `label`/`labels` commands, `judged_labels` retrieval flag; 14 labels (8 assertions, 6 corrections). Gate dropped the flag (MRR 0.802 → 0.771 on two label-mode queries); off by default. 70 tests. | `docs/slices/2026-10-22-judged-labels.md` |

| 10-22 goal run | Step 5 audit: judged labels was the only parked item with its trigger met; after it none is met (Swanson needs the owner's vocabulary review; the rest need the ingest review queue). Run stopped; no stop condition fired. | `docs/slices/2026-10-22-step5-parked-check.md` |

| 10-22 goal run 2 | Owner delegated reviews (DECISIONS.md). Mechanism vocabulary marked by the agent: 26 new concepts + 11 alias additions, 89 rejections with reasons (`agent/data/mechanism_marks.json`); index builder merges agent concepts; rebuild → 149 concepts, 15105 links. Bench after rebuild 0.875 / 0.881. | `docs/slices/2026-10-22-mechanism-review.md` |

| 10-22 goal run 2 | Benchmark accepted as ground truth (agent-reviewed, owner delegated): 36 queries, six label-mode ones chosen by reading. Baseline v2 (flags off) 0.678 / 0.804; after tune 0.836 / 0.874; judged_labels kept. | `docs/slices/2026-10-22-benchmark-accepted.md` |

| 10-22 goal run 2 | Swanson sweep live: `discover`, `queue`, `resolve`, `ask --discover`; review_queue in memory; floaty seed → 8 hypotheses (8 cross-chapter). | `agent/discover.py`, `docs/slices/2026-10-22-swanson-sweep.md` |

| 10-22 goal run 2 | 14 hypotheses resolved by the agent (12 accepted → agent_links: 6 extends, 3 refines, 1 analogous_mechanism, 1 compensates_for, 1 restates; 2 rejected as broad-alias bridges; discovery now requires a specific alias). Allocator built behind a flag; gate dropped it (0.734 / 0.704). | `docs/slices/2026-10-22-allocator.md` |

| 10-22 goal run 2 | Causal triples live: `causal` command, 37 seeded (seed:catalog 34, seed:handbook 3); closure, compensations and isomorphism queries. | `agent/causal.py`, `docs/slices/2026-10-22-causal-triples.md` |

| 10-22 goal run 2 | Audit: all parked items with met triggers built; only ingest-triggered items remain (no second input). Run stopped; nothing blocked; nothing waiting on the owner except renders. | `docs/slices/2026-10-22-run2-audit.md` |

| 10-22 | Retrieval verification: rebuild, `verify` command (25 checks pass), suite 83 OK, benchmark reproduces 0.836 / 0.874 and 0.678 / 0.804, all commands under 0.1 s. | `docs/slices/2026-10-22-retrieval-verification.md` |

| 10-22 | Run 002: `runs/002_rooftop_cage_fight/prompt.json`, the owner's ten-beat rooftop fight re-authored as JSON with the surfaced handbook rules as fields and per-beat provenance; whip pan moved off the contact. Unrendered. | `runs/002_rooftop_cage_fight/` |

| 10-22 | Hypotheses tested then built: typed specimens (`language` column, `specimens`), diversity knobs (5 axes × 3, words only, `variants`, `ask --knob`), module relations (25 seeded, `propose --follow`; recovers 33–37% of run 001 supporting rows, opt-in). | `docs/slices/2026-10-22-knobs-specimens-relations.md` |

## What has not happened

No render. No row, passage, label or prompt is proven. `runs/001_strike_block/SCORECARD.md` is blank.
