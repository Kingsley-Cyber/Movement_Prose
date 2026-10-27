# handoff_seed — companion to FIGHT_SIMULATOR_V2_1_CODING_AGENT_HANDOFF.md

Copy this folder to the repo root. Everything here was generated from `Kingsley-Cyber/Movement_Prose`
at `0d0734d` and validated (see `validation_report.json`).

| Path | Contents | Phase |
|---|---|---|
| `schemas/` | 9 extended v2 schemas (additive drop-in replacements) + 4 new ones | P1b (replace schema and data in the same commit) |
| `data/` | target `model_v2.json`, `option_behaviors.json`, `techniques_v2.json`, `positions.json`, `rulesets_v2.json`, `combinations_v2.json`, `debt_registry_v2.json`, `capabilities_v2.json` | P1a–P1b |
| `cards_proposed/` | the 12 cards with the §8.10 proposals applied — owner review only, never copied without approval | P2 |
| `style_templates/` | 11 starter cards: Taekwondo, Capoeira, Catch wrestling, Lethwei, Wing Chun, Hung Gar, Bajiquan, Baguazhang, Tai Chi, Shuai Jiao, Jeet Kune Do | P1b+ |
| `reference/` | constant registry with source lines, option additions (incl. style preset proposals, D20), card fix proposals, capability grants, seed counts, literal inventory | P1a+ |
| `validation_report.json` | additivity proof, target validation, slot-validator findings, existing-test guards, availability parity, style-template checks, rank-field checks | all |
| `tools/` | the generators (`regenerate.sh <repo@0d0734d>`) — provenance only | — |
| `stress_test/` | rank & mastery stress test (D23, handoff §7.18): harness, experiment runner, analyses, fitted results, tables and figures behind `RANK_MASTERY_STRESS_TEST.md`; `reproduce.sh` re-runs it against a checkout at `0d0734d` | P13 |

Rules that matter most: tests are immutable; cards stay `"version": "block-2"`; `data/debt_registry.json`
is never edited; option count stays 57; the target data fails the current schemas and passes the
extended ones, so swap them together.
