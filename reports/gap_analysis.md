# Codebase Intent Gap Analysis

**Verdict:** PASS
**Repository:** /Users/king/Documents/Codex/2026-10-22/g/block_fight_engine
**Plan:** reports/requested_specification.txt
**Revision:** New project; no pre-existing Git revision
**Audited at:** 2026-10-22 (America/Denver)

## Intent Contract
Executable offline engine with the specified full knowledge coverage, deterministic prediction, conditional capability reasoning, causal fight planning and traceable cinematic prompts. Proof requires actual CLI output and negative/invariant tests.

## Actual Runtime
predict.py loads JSON and validates cards, evaluates signed edges, slots and reachable NULLs, then writes the trace. plan_fight.py calls the predictor, planner, reducer, graph verifier, choreography and prompt compiler, then persists validated packages. scripts/regress.py traverses these public paths. The baseline workspace contained no files or tests.

## Gap Matrix
| ID | Requirement | Expected evidence | Observed evidence | Status | Impact | Dependency | Smallest remediation | Verifier |
|---|---|---|---|---|---|---|---|---|
| REQ-001 | Research and ontology | 57 complete options and source/claim registry | entrypoint: scripts/audit_coverage.py; wiring: engine.audit.audit; outcome: 57 complete options and source/claim registry; verification:PASS in reports/execution_evidence.json | WORKING | Required engine path | Canonical JSON and documented Python environment | Closed by the shipped implementation | python scripts/regress.py (exit 0) |
| REQ-002 | Fighter cards | 11 schema-valid cards and explicit locked capabilities | entrypoint: predict.py; wiring: Knowledge.card and capabilities.available; outcome: 11 schema-valid cards and explicit locked capabilities; verification:PASS in reports/execution_evidence.json | WORKING | Required engine path | Canonical JSON and documented Python environment | Closed by the shipped implementation | python scripts/regress.py (exit 0) |
| REQ-003 | Matchup matrices | 511 valid cells, both asymmetric directions and normalized weights | entrypoint: predict.py; wiring: engine.matchups.evaluate; outcome: 511 valid cells, both asymmetric directions and normalized weights; verification:PASS in reports/execution_evidence.json | WORKING | Required engine path | Canonical JSON and documented Python environment | Closed by the shipped implementation | python scripts/regress.py (exit 0) |
| REQ-004 | Counter/debt graph | Conditional graph, operational debts and reciprocal links | entrypoint: scripts/audit_coverage.py; wiring: engine.audit.audit; outcome: Conditional graph, operational debts and reciprocal links; verification:PASS in reports/execution_evidence.json | WORKING | Required engine path | Canonical JSON and documented Python environment | Closed by the shipped implementation | python scripts/regress.py (exit 0) |
| REQ-005 | Prediction | Deterministic complementary probabilities with auditable terms | entrypoint: predict.py; wiring: engine.probability.predict; outcome: Deterministic complementary probabilities with auditable terms; verification:PASS in reports/execution_evidence.json | WORKING | Required engine path | Canonical JSON and documented Python environment | Closed by the shipped implementation | python scripts/regress.py (exit 0) |
| REQ-006 | Backfill | Dry-run, missing-field restoration, preserved conflicts and idempotence | entrypoint: scripts/backfill.py; wiring: backfill and audit; outcome: Dry-run, missing-field restoration, preserved conflicts and idempotence; verification:PASS in reports/execution_evidence.json | WORKING | Required engine path | Canonical JSON and documented Python environment | Closed by the shipped implementation | python scripts/regress.py (exit 0) |
| REQ-007 | Fight planning | Ten tactical phases and seeded/director-controlled paths | entrypoint: plan_fight.py; wiring: fight_director.plan and fight_state.apply; outcome: Ten tactical phases and seeded/director-controlled paths; verification:PASS in reports/execution_evidence.json | WORKING | Required engine path | Canonical JSON and documented Python environment | Closed by the shipped implementation | python scripts/regress.py (exit 0) |
| REQ-008 | Event graph | Causal snapshots and state/effect replay | entrypoint: plan_fight.py; wiring: event_graph.graph and validate; outcome: Causal snapshots and state/effect replay; verification:PASS in reports/execution_evidence.json | WORKING | Required engine path | Canonical JSON and documented Python environment | Closed by the shipped implementation | python scripts/regress.py (exit 0) |
| REQ-009 | Choreography | Six movement phases with anatomical limbs and persistent consequences | entrypoint: plan_fight.py; wiring: choreography.choreograph; outcome: Six movement phases with anatomical limbs and persistent consequences; verification:PASS in reports/execution_evidence.json | WORKING | Required engine path | Canonical JSON and documented Python environment | Closed by the shipped implementation | python scripts/regress.py (exit 0) |
| REQ-010 | Prompt compilation | Event-linked shots and model-agnostic JSONL prompts | entrypoint: plan_fight.py; wiring: prompt_compiler.shots, compile_shot and validate_visuals; outcome: Event-linked shots and model-agnostic JSONL prompts; verification:PASS in reports/execution_evidence.json | WORKING | Required engine path | Canonical JSON and documented Python environment | Closed by the shipped implementation | python scripts/regress.py (exit 0) |
| REQ-011 | Regression and demonstrations | 58 passing tests and both validated 60-second fights | entrypoint: scripts/regress.py; wiring: subprocess execution of audit, recovery, pytest and CLIs; outcome: 58 passing tests and both validated 60-second fights; verification:PASS in reports/execution_evidence.json | WORKING | Required engine path | Canonical JSON and documented Python environment | Closed by the shipped implementation | python scripts/regress.py (exit 0) |

## Directory Contract
data/ and cards/ own live canon. schemas/ owns payload validation. engine/ owns pure reasoning and semantic transitions. scripts/ owns command execution and recovery. resources/ contains the frozen recovery release only. tests/ is immutable after its initial definition. reports/ and outputs/ are derived evidence and deliverables. No paid service or secondary database is introduced.

## Remediation Order
The empty-repository gap was closed in dependency order: researched canonical data into a working predictor; state/replay into executable fight direction and prompts; recovery and original tests into the two complete demonstration paths. No remaining implementation slice is admitted by the contract.

## Verification Record
58 passed in 72.77s (0:01:12). All eight regression subprocesses exited 0. reports/execution_evidence.json preserves their exact commands, stdout and stderr. The first evaluation found duplicate reciprocal records and an out-of-range feint; production data/setup ordering were corrected, then the original tests passed unchanged.

## Residual Unknowns
Win probabilities remain uncalibrated. Motion is semantically validated staging without a physical solver. Remote video reproduction and reference image generation are outside the required offline prompt output. These boundaries are disclosed in each package.
