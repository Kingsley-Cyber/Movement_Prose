# Roadmap

Slices are ordered by measured gain per cost (RETRIEVAL.md). A slice is done when its tests are green and the invariants in AGENTS.md hold. Nothing is "ready" until the owner renders.

## Done
- **Slice 1** (10-21): FTS quoting, alias expansion with specificity, diversity with `(+N in block)`, matched terms + snippet, `--budget`, short display ids.
- **Slice 2** (10-21): `ask` entry point.
- **Knobs, specimens, relations** (10-22): style knobs with one-change variants; typed code specimens; module relations with `propose --follow` (opt-in, 25 edges).
- **Causal triples** (10-22): closed predicates, 37 seeded, closure and isomorphism queries.
- **Allocator** (10-22): built behind `allocator`; gate dropped it (recall 0.734 vs 0.826); available via `--spread`.
- **Swanson sweep + review queue** (10-22): `discover`/`queue`/`resolve`, `ask --discover`.
- **Judged labels** (10-22): memory table + commands + flag; flag off until owner-reviewed label-mode queries reward it.
- **Slice 3c** (10-22): flagged rerank and diversity parameters gated by `tune-rerank`; defaults in `agent/data/rerank.json`; recall@10 0.740 → 0.875, MRR 0.787 → 0.866.
- **Slice 3b** (10-21): `docs/queries.jsonl` drafted (32 queries, unreviewed); baseline recall@10 0.740.
- **Slice 3a** (10-21): `cited` usage events from `check`; `bench` command (recall@10, MRR, retrieval→citation) over `docs/queries.jsonl`.

## Next
- **Nothing runnable without a second input.** Everything below "Parked" that is not marked done waits for the research-folder ingest. The owner's only pending action is rendering run 001.

- **Slice 3, ground truth.** (a) done; (b) drafted by the agent, awaiting owner review; `docs/queries.jsonl`: ≈30 owner-labelled queries with expected passage ids, including cross-alias ones ("impact hold", "floaty deceleration"); (c) `python3 -m agent bench` → recall@10, MRR, retrieval-to-citation rate; (d) minimal static rerank only: promote SOURCE_EVIDENCE, demote deep-research prompts, specimens and superseded, and the Sbase fixes the simulation showed (kind weight, multi-alias bonus, length floor, label agreement), each accepted only if recall@10 does not drop.
- **Mechanism vocabulary review: done by the agent (owner delegated 10-22).** 26 new concepts, 11 alias additions; marks and reasons in `agent/data/mechanism_marks.json`; index rebuilt. Unparks the Swanson sweep.

## Parked, with the trigger that unparks each
| item | trigger |
|---|---|
| Content-hash passage ids, sources ledger, revision diff, near-duplicate scoring, placement vote, inbox chapter | the research-folder ingest (a second input exists) |
| (done 10-22) Swanson sweep: `discover`, `queue`, `resolve`, `ask --discover` | — |
| (built 10-22, flag off by gate) Allocator: `query.allocate`, `find --spread`; revisit with a coverage metric | owner wants coverage to outrank recall |
| (done 10-22) Causal triples: `causal seed|add|closure|compensations|isomorph` | — |
| (done 10-22) six label-mode queries chosen by reading; judged_labels flag re-gated | — |
| Embeddings | never (owner decision); the recall benchmark would be the only thing that could reopen the question, and the decision stands |

## Rules carried into every slice
No schema change without a SCHEMA.md update. No ranking weight without a benchmark number. No label without evidence. No deletion in memory, only supersession.
