# AGENTS.md — how to work in this folder

Read this first, then `agent/README.md`, then `docs/DECISIONS.md`. Decisions are locked; do not re-open them.

## What this is
A bundle-local prompt agent and a SQLite knowledge index for anime-action video prompting. Three databases:
- `ai_video_compiler.db` — the delivered 64-row lexicon. Never modified. `SHA256SUMS.bundle` freezes it and the ten other delivered files.
- `handbook_index.db` — derived from `~/Downloads/handbook.html` and the bundle. Rebuilt from scratch by `python3 -m agent index-handbook <html>`.
- `agent_memory.db` — tags, notes, links, concepts added by the agent, and the usage log. Never rebuilt. Keyed on index ids.

## Invariants (check before every commit)
1. `shasum -a 256 -c SHA256SUMS.bundle` → all OK.
2. `python3 -I validate_anime_seed.py --db ai_video_compiler.db` → `status: pass`, fingerprint `275537d8f7c8d4bcb5a82c0d28ccf7efb5e6f6c3b8153ae35fecd971f99df639`.
3. `python3 -m unittest discover -s agent/tests` → OK (check the exit status; do not pipe it into `tail` without `set -o pipefail`).
3b. `python3 -m agent verify` → PASS (integrity + backfill: FTS/summaries/concepts/memory references).
4. No embedding model, no network calls, no pip packages: Python 3.9 stdlib only (no `X | Y`, no `match`).
5. Every relation or label written to memory carries evidence (a span, a sentence, a reason). No silent labels: `label` refuses an empty reason; use `none` to record that no label applies instead of deleting a lexical one.

## Daily commands (run from this folder on macOS / Mac Studio, Linux, or Windows)
- Tests: `python3 -m unittest discover -s agent/tests` (or `python -m unittest discover -s agent/tests` on Windows)
- Rebuild index (≈13 s): `python3 -m agent index-handbook /path/to/handbook.html`, then `python3 -m agent verify` (note: `verify` passes even when the original `handbook.html` path is offline on another machine as long as `source_sha256` is recorded in `handbook_meta`)
- Query: `find`, `lookup`, `ask`, `concept`, `walk`, `outline`, `read`, `near`, `deps` (see `agent/README.md`)
- Prompt pipeline: `propose` → write `runs/<n>_<slug>/ir.json` → `check` → `emit`

## How to change things
- A new concept or alias: `python3 -m agent concept-add <id> "<label>" --alias ... --kind mechanism|technique|concept`, then rebuild the index to link passages. Edit `SEED_CONCEPTS` in `agent/knowledge.py` only for seeds that should ship with the index.
- A new policy value (priority, budget class, prerequisite satisfier): edit `agent/data/*.json`; tests pin the counts.
- A new engine profile: `agent/data/engine_profiles_extra.json`; the bundle's `engine_profiles.json` stays untouched.
- A new run: copy the shape of `runs/001_strike_block/`; `ask.md`, `ir.json`, arms, `SCORECARD.md` blank until rendered.
- A schema change to the index: edit `SCHEMA` in `agent/handbook.py` or `SCHEMA_INDEX` in `agent/knowledge.py`, bump nothing else, rebuild, update `docs/SCHEMA.md`.
- A schema change to memory: add `CREATE TABLE IF NOT EXISTS` to `SCHEMA_MEMORY`; never drop or rename a memory table.

## What a developer should do before touching retrieval
Read `docs/RETRIEVAL.md` for what is live, what is designed, and the measured numbers behind the order. Ranking and diversity defaults live in `agent/data/rerank.json` and change only through `python3 -m agent tune-rerank`, which keeps a flag only if recall@10 on `docs/queries.jsonl` does not drop; `agent/tests/test_slice3c.py` enforces that the defaults never score below the recorded baseline. A new candidate change is a new flag in `query.RERANK_FLAGS`, not an edit to the defaults.

## Where things are written down
- `docs/DECISIONS.md` — locked owner decisions.
- `docs/SCHEMA.md` — every table, column and relation.
- `docs/RETRIEVAL.md` — stages, allocator, discovery, measurements.
- `docs/TIMELINE.md` — what was designed and built, when, with the numbers.
- `docs/ROADMAP.md` — slices, parked items, unpark triggers.
