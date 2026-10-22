# Retrieval

What is live, what is designed, and the measurements behind the order. Numbers are from simulations run against the real index on 2026-10-21 (scripts kept in the session scratchpad; the results are recorded here).

## Live (Slice 1 + `ask`, 2026-10-21)

1. **Understand.** `query.resolve_concepts`: exact alias containment first, then the concept FTS; at most two concepts for `find`/`lookup`, four for `ask`. `query.label_scores`: every moment and slot label with its matched terms.
2. **Candidates.** `query.fts_query` quotes plain text (phrase OR all-words, every word quoted, so hyphens never reach the FTS parser). `expand_query` adds the *specific* aliases of the resolved concepts: an alias is specific when it matches at most 2% of passages (`ALIAS_MAX_SHARE`); weight = 1 / (1 + ln(1 + df)). Label lookups use the length-penalised term score `(moment_score + slot_score) / (1 + chars/400)`.
3. **Clean.** `same_text` duplicates removed; `diversify` caps one hit per block and two per article and attaches `(+N in block …)` / `(+N in article)` to the kept hit so density is still visible.
4. **Explain and trim.** Each hit: short id, score, moment/slot with scores, `via` (which alias or the query matched), FTS `snippet()` with matched words bracketed, the passage's matched label terms, a one-line summary (agent note if any). `--budget` trims whole hits; `--cite` adds the full citation.
5. **`ask`.** One call: direct hits, one group per resolved concept through its specific aliases, one group for the top moment × slot labels, directives (implemented_by + id-word overlap, with priority and budget class), gaps (words no handbook passage mentions; words no catalog row mentions), taste.

### Slice 3c defaults (2026-10-22)
`agent/data/rerank.json` holds the flags the greedy tune kept (rule: keep iff recall@10 does not drop on `docs/queries.jsonl`, MRR breaks ties). Kept: `any_word_fallback` (when all-words-AND returns fewer than the fetch size, append any-word OR results, marked "(any-word)"), `no_article_cap`, `per_block_2` (diversity = at most two hits per block, roll-up counts for the rest, no article cap), `length_floor` (passages under 40 chars ×0.7). Dropped for costing recall: `kind_weight`, `multi_alias_bonus`, `epistemic_weight`, `label_agreement`. Change the defaults only through `python3 -m agent tune-rerank`; `agent/tests/test_slice3c.py` fails if the default configuration scores below the recorded baseline.

Benchmark state: baseline 0.740 / 0.787 → after 3c 0.875 / 0.866 (recall@10 / MRR, 32 agent-authored queries, unreviewed).

### Judged labels (2026-10-22, flag off by default)
`agent_labels` holds agent-judged moment/slot labels with a required reason (14 so far: 8 assertions, 6 corrections of wrong lexical labels using `none`). Behind the `judged_labels` flag, label-mode lookups put judged passages first and drop passages judged `none`; hits show `impact*`. The gate dropped the flag (recall unchanged 0.875, MRR 0.802 → 0.771) because the two label-mode benchmark queries follow lexical order; it stays off until the owner-reviewed queries reward it.

### Knobs, specimens, relations (2026-10-22)
- **Knobs** (`agent/data/knobs.json`, `knobs`, `variants`, `ask --knob`): five style axes (Laban profile, exposure cadence, smear policy, impact accent, camera behaviour), three verbalised options each, words only; each option names its passages and preferred rows. One-change variants of a JSON prompt for render comparisons.
- **Specimens** (`specimens --language yaml|json|xml --text … --heading …`): the handbook's typed code blocks as schemas and templates.
- **Module relations** (`relations seed|add|list|follow`, `propose --follow N`): the handbook's temporal-coupling vocabulary over directives, authored with evidence (25 seeded). Measured on run 001: follow recovers 33–37% of the hand-selected supporting rows from the primary actions alone (52% of the causal/temporal ones). Opt-in until the edge set grows.

## Measured (why the order is what it is)

| question | result |
|---|---|
| Diversity in old top-10 | identical text 4%, same block 13%, same article 32%; ten distinct hits reachable by rank 9 → small gain, kept as a safety net |
| Alias expansion | querying by a secondary alias reached a median of 1 linked passage raw vs 86 expanded; 22 of 51 seed concepts went from 0 hits to many |
| Broad aliases | phase concepts (impact 2,773 passages, on_ones 1,185) matched through "contact", "ones", "frame"; one concept hop multiplied reach 345× (6 → 4,251) → specificity cap required |
| Dead concepts | 68 of 123 concepts linked to nothing (every directive concept, crash_zoom): titles never occur verbatim → alias repair is a review task |
| Token cost | citation + one-liner averaged 348 chars vs 128 for the passage → short display ids, citation on demand |
| Epistemic rerank | 0% of top-10 hits came from deep-research/specimen articles; 66% had no usable epistemic status → nothing to act on today |
| `ask` on plain requests | moment/slot scores 1–2; request vocabulary (slip, hook, dodge, slash, kick) hits no concept → gap list is the useful part until the vocabulary grows |
| Diversity cost (3b/3c) | block cap 1 + article cap 2 = 0.740 recall; article cap off 0.792; block cap 2 = 0.875; no diversity 0.880 → kept block cap 2 with roll-ups, no article cap |
| Sbase quality (open) | bm25 favours short table rows: two fragments outrank the hands-contact card's definition of hit-stop. Fix belongs to Slice 3 (kind weight, multi-alias bonus, length floor, label agreement) after the recall benchmark exists |

## Designed, not built

**Allocator (Stage 3 of the owner's spec) — BUILT 2026-10-22 behind the `allocator` flag, gate-dropped (recall 0.734 / MRR 0.704 vs 0.826 / 0.812).** `query.allocate`; `find --spread --per-concept`; footer `coverage: concept shown/candidates (articles)`; nuance hop reads accepted `agent_links`. Original design note follows. `Sfinal = Sbase · decay(block, article, spread) + γ·nuance`. Coverage first (every resolved concept's top passage), per-concept quotas proportional to relevance share (min 2), remaining slots by penalised score, roll-ups instead of omissions, `same_text` collapse only, `--spread` 0..1, `--per-concept`, coverage footer (shown / linked per concept, articles reached), `--more concept:X`, 1–2 reserved serendipity slots. Simulated: quotas and footer worked; decay never fired (hits already in distinct blocks); γ never fired (the index holds 0 `refines/contradicts/extends/restates/revises` edges). Build after the review queue exists.

**Discovery (Swanson A→B←C, lexical) — LIVE since 2026-10-22** as `python3 -m agent discover --source <passage> | --query "<text>" [--enqueue]`, `queue`, `resolve <id> <relation>`, and `ask --discover N`. B = concepts of kind mechanism or technique (149 concepts after the vocabulary review), C = substantive (paragraph/list item ≥ 80 chars), technique-linked, another article, zero shared content tokens with A outside B; cross-chapter bonus 1.5; score = w(A,B)·w(B,C)·IDF(B). Simulated from a "floaty" symptom: 3,071 candidates raw → 36 with cure constraints → 3 with domain vocabulary → 1 genuine cross-chapter cure (rhythm metrics → temporal-causality intervention via "settle"). Outputs are hypotheses for the review queue; accepted ones become `analogous_mechanism` / `bridged_by` edges in memory.

**Alias divergence (the lexical stand-in for a neural layer).** Two passages, same concept via different aliases, zero shared tokens → candidate `extends`/`refines`, never `restates`. Ceiling: it cannot find a bridge nobody has named. No embedding model (DECISIONS.md).

**Causal triples — LIVE since 2026-10-22** as `python3 -m agent causal add|seed|list|closure|compensations|isomorph` over `mem.causal_triples` (37 seeded). Closed predicates (amplifies, dampens, triggers, inhibits, requires, breaks, compensates_for) between concepts, authored in review with evidence; transitive closure in SQL. Only 10 of the handbook's 148 lexical causal clauses normalise to a concept today, so this cannot be auto-extracted. Relational isomorphism (same two-edge predicate chain) is a pattern query over that table once a few hundred triples exist.

**Mechanism vocabulary.** Mining hyphenated/compound terms (df 3..1%, ≥ 2 chapters, not already an alias) yields 382 candidates mixing mechanisms ("motion blur", "camera impulse", "center-of-mass") with meta-terms ("natural-language", "peer-reviewed"). Pre-filter by proximity to unit/directive markers and to causal clauses, then review; accepted terms get `kind = mechanism`.

**Measurement (Slice 3).** Record `cited` events when `check` resolves `handbook_refs`; a labelled query file (≈30 queries with expected passage ids); recall@10 and a retrieval-to-citation rate. Only then tune Sbase.
