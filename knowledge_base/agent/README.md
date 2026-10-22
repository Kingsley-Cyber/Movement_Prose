# agent/ — bundle-local prompt agent

A stdlib-only Python 3.9 toolkit that sits next to the bundle and never modifies it
(`SHA256SUMS.bundle` freezes the eleven delivered files). It reads `ai_video_compiler.db`
read-only, checks an IR against the bundle validator's own composition rules plus a
priority/budget policy, and projects the IR to prose. It renders nothing.

Run everything from the bundle root:

```bash
python3 -m unittest discover -s agent/tests
```

```bash
python3 -m agent propose "hero slips a wide swing and lands a rising left hook" --taste "heavy, brutal, old school" --duration 5
```

```bash
python3 -m agent check runs/001_strike_block
```

```bash
python3 -m agent emit runs/001_strike_block --engine generic_web_ui --arm arm_B_compiled
```

```bash
python3 -m agent show runs/001_strike_block
```

Pipeline: you type a request → `propose` lists the catalog's candidate rows per event × slot
(a lookup, not a search) with default priority, budget class and taste mark → the model in the
IDE writes `runs/<n>_<slug>/ir.json` (events, selections, authored text for what no row covers)
→ `check` applies the rules → `emit` writes `prompt.txt`, `post_plan.json`, `receipt.json`
(and `negative.txt` only where the engine profile says the negative field is active).

Policy data lives in `agent/data/`: `budget_classes.json` (each of the 64 rows: budget class and
whose body it moves), `priority_defaults.json` (six cpcs classes, locked rows, suppression
reasons), `prerequisites.json` (which rows satisfy a `requires` token), `taste_profiles.json`
(three untested profiles, joinable to row ids), `engine_profiles_extra.json` (`generic_web_ui`).

`check --key actor` reproduces the bundle validator's duplicate-slot rule verbatim; the default
`--key subject` keys on whose body a row moves, which is what lets the bundle's own two-fighter
`sequence_plan` pass. Every row is an untested prompt candidate; `runs/*/SCORECARD.md` is where
render verdicts go.

## Handbook index and knowledge layers

`python3 -m agent index-handbook ~/Downloads/handbook.html` builds `handbook_index.db` (derived, rebuilt from
scratch each time). `agent_memory.db` holds what the agent adds (tags, usage log, its own summaries, concepts
and links) and is never rebuilt. The bundle's `ai_video_compiler.db` stays untouched.

Granularity, top down: chapter → section → article (source path, cpcs id, kind, epistemic status from the
article banner) → block (consecutive passages under one heading) → passage (paragraph, list item, table row,
code, quote). Every passage carries a lexical moment label, slot label and the paste's intent tier with the
matched terms as evidence, a sha256, and an auto one-line summary. Typed edges: contains, next, links_to,
cites_card, cites_source, requires / depends_on / conflicts_with (sentence evidence), same_text (duplicates).
Concepts: seeded equivalent-term sets (hit-stop = impact hold = contact hold = freeze frame …) plus one per
directive, linked to passages through FTS alias matches, with co-occurrence, precedes, conflicts_with and
implemented_by edges. The directive side (requires, conflicts, directive→passage links, taste profiles) sits in
the same database so one query answers both.

Token-efficient queries (compact lines; expand on demand). `find`/`lookup` quote your text for FTS5, expand it through the
specific aliases of the concepts it names, remove duplicates, cap one hit per block and two per article with `(+N in block)`
counts, and print short ids (`a035#0067`; `read`, `near`, `handbook_refs` accept them). Flags: `--budget N`, `--cite`,
`--no-expand`, `--no-diversify`, `--all-kinds`.

```bash
python3 -m agent ask "one straight punch and a forearm block, camera locked on the contact" --taste "raw street brawl"
```

```bash
python3 -m agent find "freeze frame" --budget 1200
```

```bash
python3 -m agent lookup --moment impact --slot temporal_cadence --limit 5
```

```bash
python3 -m agent concept hit_stop
```

```bash
python3 -m agent walk --slot camera_optics --per-moment 2
```

```bash
python3 -m agent outline chapter ch-04
```

```bash
python3 -m agent read block "src-additional-continous-combat-state-md/b051"
```

```bash
python3 -m agent near "src-additional-continous-combat-state-md#0315"
```

```bash
python3 -m agent deps aa_env_yutapon_cubes
```

Growing it: `tag <tag> <kind> <id>`, `tagged <tag>`, `note <kind> <id> "<one line>"`, `link <kind> <id> <relation>
<kind> <id>`, `concept-add <id> "<label>" --alias …` write to `agent_memory.db`. Every `emit` records the
directives, cited passages and taste profile it used, and `usage` shows the most-used nodes and what a node was
used with, so co-citation becomes a link over time. Authored text in an IR cites passages through
`handbook_refs`; `check` rejects unknown ids and the receipt carries each citation.

## Documents
`../AGENTS.md` (how to work here), `../docs/DECISIONS.md` (locked), `../docs/SCHEMA.md`, `../docs/RETRIEVAL.md` (live, measured, designed), `../docs/TIMELINE.md`, `../docs/ROADMAP.md`.

## Benchmark and tuning
```bash
python3 -m agent bench --label check
```
```bash
python3 -m agent tune-rerank
```
`bench` scores retrieval over `docs/queries.jsonl` (recall@10, MRR, retrieval→citation). `tune-rerank` adds the flags in `query.RERANK_FLAGS` one at a time and keeps each only if recall@10 does not drop, writing `agent/data/rerank.json`, which `find`, `lookup` and `ask` read as their defaults.

## Judged labels
```bash
python3 -m agent label a035#0027 --moment impact --slot temporal_cadence --reason "defines hit-stop, a contact-beat timing device" --confidence 0.9
```
`--moment none` or `--slot none` records that no label applies (a correction). `labels` lists them. Retrieval uses them only when the `judged_labels` flag is on in `agent/data/rerank.json` (decided by `tune-rerank`).

## Discovery (Swanson A→B←C)
```bash
python3 -m agent discover --query "floaty deceleration" --enqueue
```
```bash
python3 -m agent queue --text
```
```bash
python3 -m agent resolve 3 compensates_for --note "long deceleration is the symptom; the intervention is explicit event nodes with prerequisite edges"
```
`discover` bridges a seed passage A through mechanism/technique concepts B to cure passages C in other articles that share no content tokens with A. Hypotheses go to `review_queue`; `resolve` with a relation (analogous_mechanism, compensates_for, extends, refines, contradicts, restates, unrelated) writes an `agent_links` edge with evidence. `ask --discover 2` appends two hypotheses as a serendipity group.

## Causal triples
```bash
python3 -m agent causal seed
```
```bash
python3 -m agent causal closure "directive:aa_env_yutapon_cubes"
```
```bash
python3 -m agent causal add hit_stop amplifies impact_flash --evidence "a035#0067: impact frame then hit-stop" --passage a035#0067
```
Predicates: amplifies, dampens, triggers, inhibits, requires, breaks, compensates_for. `closure` walks requires/triggers/amplifies with a recursive CTE; `compensations <concept>` finds X→concept←Y cures; `isomorph` lists two-edge chains with the same predicate sequence.

## Verify
```bash
python3 -m agent verify
```
Read-only integrity and backfill checks over the index and memory (25 checks); run after every rebuild and before every commit.

## Knobs, specimens, relations
```bash
python3 -m agent knobs
```
```bash
python3 -m agent variants runs/002_rooftop_cage_fight --axis smear_policy
```
```bash
python3 -m agent specimens --language yaml --text "contact" --show 200
```
```bash
python3 -m agent relations follow aa_action_hip_led_punch --depth 2
```
`knobs` lists five style axes with three verbalised options each; `variants` writes one-change JSON prompts along one axis; `ask --knob axis=option` appends an option's prose. `specimens` lists typed code blocks (schemas, templates). `relations` holds the handbook's temporal-coupling vocabulary over directives with evidence; `propose --follow 1` pulls supporting rows per beat through them.
