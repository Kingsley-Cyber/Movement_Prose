# Schema

Three SQLite files. The first is delivered and frozen; the second is derived and rebuilt from scratch; the third grows and is never rebuilt.
Row counts are from the databases as built on 2026-10-21.

## Delivered lexicon (`ai_video_compiler.db`)

- **semantic_directives** (64 rows): ` directive_id VARCHAR(64) PRIMARY KEY, archetype VARCHAR(32) NOT NULL, sub_genre VARCHAR(32) NOT NULL, slot_id VARCHAR(32) NOT NULL, moment_type VARCHAR(32) NOT NULL, prompt_snippet TEXT NOT NULL, negative_snippet TEXT NOT NULL, mechanical_guidance TEXT NOT NULL `

## Derived index (`handbook_index.db`)

- **concept_directives** (208 rows): `concept_id TEXT, directive_id TEXT, relation TEXT, PRIMARY KEY (concept_id, directive_id, relation)`
- **concept_edges** (588 rows): `from_concept TEXT, to_concept TEXT, relation TEXT, weight INTEGER, evidence TEXT, PRIMARY KEY (from_concept, to_concept, relation)`
- **concept_fts** (123 rows): `concept_id UNINDEXED, label, aliases, tokenize='porter unicode61'`
- **concept_passages** (12596 rows): `concept_id TEXT, passage_id TEXT, weight INTEGER, matched TEXT, PRIMARY KEY (concept_id, passage_id)`
- **concepts** (123 rows): `concept_id TEXT PRIMARY KEY, label TEXT, kind TEXT, aliases TEXT, description TEXT, source TEXT`
- **directive_conflicts** (24 rows): `directive_id TEXT, other_id TEXT, PRIMARY KEY (directive_id, other_id)`
- **directive_passages** (535 rows): `directive_id TEXT, passage_id TEXT, score INTEGER, PRIMARY KEY (directive_id, passage_id)`
- **directive_requires** (17 rows): `directive_id TEXT, token TEXT, satisfier_directive_id TEXT`
- **handbook_articles** (108 rows): `article_id TEXT PRIMARY KEY, section_id TEXT, ordinal INTEGER, title TEXT, src TEXT, cpcs_id TEXT, kind TEXT, epistemic TEXT, words INTEGER`
- **handbook_blocks** (3302 rows): `block_id TEXT PRIMARY KEY, article_id TEXT, ordinal INTEGER, heading_path TEXT, title TEXT, passage_count INTEGER, chars INTEGER, first_passage_id TEXT, last_passage_id TEXT`
- **handbook_chapters** (21 rows): `chapter_id TEXT PRIMARY KEY, ordinal INTEGER, title TEXT, domain TEXT`
- **handbook_edges** (59799 rows): `from_kind TEXT, from_id TEXT, to_kind TEXT, to_id TEXT, relation TEXT, evidence TEXT, PRIMARY KEY (from_kind, from_id, to_kind, to_id, relation)`
- **handbook_fts** (18120 rows): `passage_id UNINDEXED, text, heading_path, article_title, tokenize='porter unicode61'`
- **handbook_meta** (17 rows): `key TEXT PRIMARY KEY, value TEXT`
- **handbook_passages** (18120 rows): `passage_id TEXT PRIMARY KEY, article_id TEXT, ordinal INTEGER, kind TEXT, heading_path TEXT, text TEXT, chars INTEGER, sha256 TEXT, moment_type TEXT, moment_score INTEGER, moment_terms TEXT, slot_id TEXT, slot_score INTEGER, slot_terms TEXT, intent_tier INTEGER, tier_name TEXT, block_id TEXT`
- **handbook_sections** (74 rows): `section_id TEXT PRIMARY KEY, chapter_id TEXT, ordinal INTEGER, title TEXT, domain TEXT`
- **moment_edges** (6 rows): `from_moment TEXT, to_moment TEXT, PRIMARY KEY (from_moment, to_moment)`
- **moments** (6 rows): `moment_type TEXT PRIMARY KEY, ordinal INTEGER`
- **slots** (8 rows): `slot_id TEXT PRIMARY KEY, ordinal INTEGER, intent_tier INTEGER, tier_name TEXT`
- **summaries** (21625 rows): `node_kind TEXT, node_id TEXT, level TEXT, text TEXT, source TEXT, created_at TEXT, PRIMARY KEY (node_kind, node_id, level, source)`
- **summary_fts** (21625 rows): `node_kind UNINDEXED, node_id UNINDEXED, text, tokenize='porter unicode61'`
- **taste_profile_directives** (140 rows): `taste_id TEXT, slot_id TEXT, directive_id TEXT, mark TEXT, PRIMARY KEY (taste_id, directive_id)`
- **taste_profiles** (3 rows): `taste_id TEXT PRIMARY KEY, human_vibe_tags TEXT, laban_effort_preset TEXT, default_cadence TEXT, camera_taste TEXT, shading_taste TEXT, sub_genre_hint TEXT, evidence_status TEXT`

## Agent memory (`agent_memory.db`)

- **agent_concepts** (0 rows): `concept_id TEXT PRIMARY KEY, label TEXT, kind TEXT, aliases TEXT, description TEXT, created_at TEXT, created_by TEXT`
- **agent_links** (0 rows): `from_kind TEXT, from_id TEXT, to_kind TEXT, to_id TEXT, relation TEXT, note TEXT, created_at TEXT, created_by TEXT, PRIMARY KEY (from_kind, from_id, to_kind, to_id, relation)`
- **agent_summaries** (1 rows): `node_kind TEXT, node_id TEXT, level TEXT, text TEXT, created_at TEXT, created_by TEXT, PRIMARY KEY (node_kind, node_id, level)`
- **node_tags** (1 rows): `node_kind TEXT, node_id TEXT, tag TEXT, weight REAL, note TEXT, created_at TEXT, created_by TEXT, PRIMARY KEY (node_kind, node_id, tag)`
- **tag_aliases** (0 rows): `alias TEXT PRIMARY KEY, tag TEXT`
- **tag_fts** (1 rows): `tag UNINDEXED, text, tokenize='porter unicode61'`
- **tags** (1 rows): `tag TEXT PRIMARY KEY, description TEXT, created_at TEXT, created_by TEXT`
- **usage_events** (39 rows): `event_id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, run_id TEXT, action TEXT, node_kind TEXT, node_id TEXT, context TEXT`
- **used_with** (666 rows): `a_kind TEXT, a_id TEXT, b_kind TEXT, b_id TEXT, count INTEGER, last_at TEXT, PRIMARY KEY (a_kind, a_id, b_kind, b_id)`

`handbook_passages.language` (2026-10-22): for `kind = code`, the fenced-block language (yaml, json, xml, text, bash, python, mermaid, jsonl); `handbook.specimens()` queries it.

## Identity

- `handbook_articles.article_id` = the article's `id` attribute in `handbook.html` (`src-…`), de-duplicated with `-dup`.
- `handbook_blocks.block_id` = `<article_id>/b<ordinal>`; a block is the run of passages under one heading path.
- `handbook_passages.passage_id` = `<article_id>#<ordinal>` (positional: see ROADMAP, parked "content-hash ids").
- Short display ids: `a<article ordinal>#<ordinal>` and `a<ordinal>/b<ordinal>`; `query.resolve_id` maps them back. Canonical ids are what the tables store.
- `concepts.concept_id`: seed slugs (`hit_stop`) or `directive:<directive_id>`.

## Relations (handbook_edges.relation)

| relation | from → to | source |
|---|---|---|
| contains | chapter→section→article→block→passage | tree |
| next | passage → passage | document order inside an article |
| links_to | passage → anchor id | `<a href="#…">` in the body |
| cites_card | passage → article (when the card is in the handbook) or card id | `cpcs.*` mentions in text |
| cites_source | passage → `SRC-nnn` / `S0nn` | citation tokens in text |
| requires / depends_on / conflicts_with | passage → clause text | lexical sentence match; evidence = the sentence |
| same_text | passage → passage | identical sha256 (≥ 40 chars) |

`concepts.source` is `seed`, `catalog`, `agent`, or `seed+agent` when an agent entry in `mem.agent_concepts` with the same id extended a seed's aliases at rebuild.

Concept relations (`concept_edges.relation`): `co_occurs` (weight = passages sharing both), `precedes` (phase order), `conflicts_with` (from directive mechanics). `concept_directives.relation`: `is`, `phase_of`, `implemented_by`.
Vocabulary tables `moments`, `moment_edges`, `slots` hold the phase order and the paste's slot→tier mapping as rows.

## Labels

`moment_type` / `slot_id` / `intent_tier` on every passage are lexical: term-hit counts from `MOMENT_TERMS` and `SLOT_TERMS` in `agent/handbook.py`, with the matched terms stored as evidence (`moment_terms`, `slot_terms`). They are proposals, not judgments; see RETRIEVAL.md for the measured consequences.

## Memory tables

`tags`, `tag_aliases`, `node_tags`, `tag_fts`, `usage_events` → `used_with`, `agent_summaries` (override auto summaries), `agent_concepts`, `agent_links`, `module_relations` (id, source, relation ∈ precedes|lags|synchronizes_with|peaks_with|holds_during|releases_after|triggered_by|requires_setup|reacts_to, target, offset, evidence, passage_id, confidence, created_at, created_by; unique on source,relation,target), `causal_triples` (id, subject_concept, predicate ∈ amplifies|dampens|triggers|inhibits|requires|breaks|compensates_for, object_concept, evidence, passage_id, confidence, created_at, created_by; unique on subject,predicate,object), `review_queue` (id, kind, a_id, b_concept, c_id, score, evidence, status pending|accepted|rejected, relation, note, created_at, resolved_at, resolved_by, source; unique on kind,a,b,c), and since 2026-10-22 `agent_labels` (node_kind, node_id, moment_type, slot_id, intent_tier, reason, confidence, created_at, created_by; `none` = no label applies; reason required). Keyed on index ids; attached to the read-only index connection as `mem` by `query.open_all()`.
