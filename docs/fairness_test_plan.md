# BLOCK fairness test plan

This plan defines observable oracles for the confirmed findings and the requested broader assessment. It does not claim every possible fight can be tested. The included `verify_findings.py` has been executed; the additional cases below are planned work for the destination IDE. Existing original tests remain immutable.

## Admission oracles

Tests should invoke public card admission and prediction as well as the internal resolver. A standalone validator passing while the CLI bypasses it is insufficient. Invalid claims must be rejected before prediction or demonstrably receive no unsupported advantage under an explicit documented policy.

| Case | Input or transformation | Required independent assertion |
|---|---|---|
| SLOT-COPY | Copy an existing coordinated bundle; change only ID and prose | No additional admitted slot or score credit; this is the F-001 regression |
| SLOT-SET-ORDER | Reorder unordered capability-set entries or slot-array presentation without changing mechanics | Probability and admitted coordination count are invariant |
| SLOT-DUPLICATE-MEMBERS | Repeat a capability within a bundle or repeat the same semantic bundle under aliases | Reject the invalid representation or normalize without extra credit according to the accepted schema |
| SLOT-VALID-COORDINATION | Distinct evidenced coordination using already known techniques | Accept the legitimate slot; do not demand another technique merely because a new slot is claimed |
| SLOT-COUNT | Declared count differs from admitted entries; counts outside the original one-through-four domain | Reject the inconsistent card; test original authorized boundaries rather than inventing new ones |
| SLOT-COEFFICIENT | Net additional valid coordination with all other modeled factors held constant | The logit changes by the supplied 0.15 exactly once, within the project's floating-point policy |
| SLOT-SWAP | Exchange fighters after a valid slot difference | Contribution changes sign; opponent inverse is not counted twice |
| STYLE-UNSUPPORTED | Select anti-grappling on unchanged Donnell training/techniques | No NULL erasure or trained-style matrix credit; this is the F-002 regression |
| STYLE-ROSTER | Each selected option across the shipped roster and required option registry | Its approved capability requirements resolve; requirements are not inferred merely from the style string |
| CLAIM-AUTHORITY | A caller changes a label, source string or a self-declared trusted flag | Unapproved provenance cannot promote a ranked capability or alter accepted assessment inputs |

Capability sets can be unordered; an execution sequence is ordered. Reversing mechanically meaningful setup order must not be treated as a cosmetic permutation. Use separately constructed reference expectations rather than calling the same normalization function to calculate both actual and expected results.

### Original test conflict check

Inspect `tests/test_slots.py::test_net_slot_term_is_once_in_logit` before tightening admission. It adds a declared slot without changing available techniques. Preserve its valid coefficient claim and the distinction between existing techniques and new coordination. If strict requirements make that exact fixture inadmissible, report the conflict before modifying any original test. No test-name special case or silent legacy exemption is an acceptable repair.

## NULL and reachability oracles

The original contract defines four required conditions: relevance under the ruleset, a viable opponent mechanism, access to the required range/position, and an available technique with prerequisites. Their logical conjunction gives a finite truth table: **2⁴ = 16 combinations**, derived from that contract rather than an invented test quota. Cover every feasible combination; document combinations excluded by actual state constraints.

| Case | Perturbation | Required assertion |
|---|---|---|
| NULL-AND | Toggle each required condition independently | Penalty applies only when all four are true |
| NULL-NONE | Use explicit `kicking.none`, actual JSON NULL, and unknown data as distinct values | Preserve their meanings; neither absence of kicks nor unknown evidence becomes a generic automatic penalty |
| NULL-RULESET | Evaluate boxing and MMA with the same missing tie | Excluded dimensions receive no penalty; applicable weights renormalize |
| NULL-PRECONDITION | Trained submission without ground entry, missing grip, or unavailable setup | A named move alone cannot establish an exploitation path |
| NULL-COUNT | Several available techniques attack one missing dimension | Apply the existing 0.20 term once for that dimension, not once per technique |
| NULL-CONDITIONAL | Locked, gate-partial, gate-complete and already activated capability states | No early ability; one valid activation; repeated or unsupported activation rejected |
| NULL-PREDICTION-SCOPE | Prediction about the initial configuration versus later state-local access | State clearly which time/configuration is assessed; later training cannot retroactively change the original trace |
| NULL-FORGERY | A card removes debt IDs or invents an exploit path in prose | Derive required mechanical debts from admitted facts; authored prose cannot silently erase an obligation |

Apply relevant cases to all missing-capability dimensions the schema permits, not only the demonstrated tie. Do not implement unsupported dimensions as silently zero-penalty placeholders. If a dimension has no mechanical meaning for a penalty, document that policy rather than fabricate an exploit.

## Probability and model invariants

The supplied data contains 57 mandatory options and 511 cells. The 11 distinct cards yield **11 × 10 / 2 = 55 unordered pairs**. With the two shipped rulesets, this is **110 pair/ruleset contexts**, or **220 ordered evaluations** when checking exchange symmetry. These are derived finite coverage domains, not confidence claims.

| Case | Scope | Required assertion |
|---|---|---|
| PROB-SWAP | Every shipped pair/ruleset context and generated admissible cards | `P(A,B) + P(B,A)` equals one within the established numerical policy; signed score terms reverse |
| PROB-IDENTICAL | Equal modeled configurations with distinct immutable fighter IDs | Equal probabilities; names and visual descriptions do not create skill |
| PROB-DETERMINISM | Same admitted cards, versions, ruleset and assumptions | Identical score and trace; seed changes selection, not the prediction |
| PROB-ASYMMETRY | All actual asymmetric matrix directions | Both attack/defense directions are resolved once and signed consistently |
| PROB-TRACE | Each score-changing input independently | The entire logit equals explained contributions; no unreported bonus |
| PROB-UNAVAILABLE | Remove the actual trained mechanism while retaining an option label | No unsupported ability credit from the label; other unaffected terms stay stable |
| PROB-NUMERICS | Invalid types, NaN/Infinity, malformed weights and model parameters | Fail explicitly before emitting a misleading or non-finite probability |
| PROB-POLICY | Canonical counter cycles, self-cells and missing dimensions | Preserve reciprocity and conditional non-transitivity; no mandatory higher-tier victory |
| PROB-VERSION | Change model/card evidence or requirements version | Record provenance and prevent comparisons that silently mix incompatible policies |

Retain existing invariant tests where they already cover a requirement. Add only missing oracles. The baseline percentages in the report are observations of the old implementation, not targets to tune the repaired model toward.

## Outcome mode and state tests

| Case | What to exercise | Required assertion |
|---|---|---|
| MODE-ANALYSIS | Ask for assessment without a narrative winner | Prediction, assumptions and uncertainty are returned; generated story marks are not used as independent justification |
| MODE-SAMPLED | Fixed accepted inputs and seed | Reproducible sampled identity; selected winner remains labeled as a model draw |
| MODE-DIRECTED | Author supplies either participating winner | Original prediction unchanged; directed path marked as dramatized and ineligible as empirical result evidence |
| MODE-CONSUMER | Send generated marks or a client-selected rerun to a ranking consumer | No empirical rating update; consumer validates result origin rather than trusting an output label |
| MODE-INDEPENDENT | Only if an independent simulator is explicitly commissioned | Interaction resolution receives no chosen winner; final outcome derives from adjudicated state and accepted rules |
| STATE-SETUP | Generated valid/invalid action sequences | No execution without required setup, training, range, support or earned grip |
| STATE-CONTACT | Trigger anticipation, execution, contact, response and recovery in varied orders | Contact-caused reactions follow contact; anticipation is explicit; blocked/missed contact does not produce landed-hit consequences |
| STATE-PERSISTENCE | Continue after injury, fatigue, attachment and position changes | State consequences persist according to defined mechanics; no unsupported recovery or teleport |
| STATE-REVERSAL | Legal denial/counter paths against an apparent advantage | Allowed responses can affect an actual independent resolver; the conditional story's selected outcome is not offered as proof of that feature |
| VISUAL-TRACE | Existing event-to-shot-to-prompt path after repairs | Preserve identities, anatomical limbs, contact timing, event IDs and semantic continuity |

The original state/graph/visual tests already cover several invalid transitions. Keep them. For broader sequence interactions, use a small independent reference state model and generated legal/illegal actions. [Hypothesis's stateful approach](https://hypothesis.readthedocs.io/en/latest/stateful.html) is one available method. Save failing examples and the actual generated domains; use the destination project's declared CI execution policy instead of inventing a sampling budget.

Choosing a favorable seed after observing outcomes is selection bias, not a defect in the random-number generator. A ranked consumer needs accepted-input/run provenance before outcomes are exposed. A creative local CLI may still permit reruns when those outputs are excluded from empirical adjudication.

## Assessment profile and tier tests

Tiers and ranking are proposed capabilities, not current implementations. Define their scales and evidence before numerical tests. No default tier count or score boundaries are authorized in this handoff.

| Case | Required assertion |
|---|---|
| ASSESS-UNKNOWN | Missing proficiency, measurements or history remains explicitly unknown/unrated; no zero, novice or average value is silently injected |
| ASSESS-UNITS | Equivalent unit conversions preserve the modeled physical quantity and results; invalid or incompatible units are rejected |
| ASSESS-DOMAIN | Proficiency in one capability does not automatically grant another; tendency ratings never become mastery ratings |
| ASSESS-EVIDENCE | A score/label cannot change accepted capability without the required approved evidence; CANON is never relabeled observed research |
| ASSESS-LABEL | Cosmetic changes to a displayed tier, title, name or school do not add a second bonus to already modeled factors |
| ASSESS-CONTEXT | Ruleset and matchup conditions remain explicit; a stronger rating does not override legal capabilities or erase counter relationships |
| ASSESS-SENSITIVITY | Quantified effects have defined directional/mechanical expectations in controlled contexts; no universal “increase every attribute and always win” oracle |
| ASSESS-DOUBLE-COUNT | The same training/evidence cannot independently earn duplicate style, slot, proficiency, tier and historical-rating credit without an explicit fitted or authored policy explaining overlap |

Test labels against their approved rubric, not arbitrary point cutoffs invented by the implementing agent. Decide any interval, prior or binning policy from relevant evidence or an authoritative project contract and record its provenance.

## Ranking and calibration tests

| Case | Required assertion |
|---|---|
| RANK-ORIGIN | Only admissible independently recorded outcomes update empirical ratings; generated or director-selected results are rejected |
| RANK-REPLAY | Re-ingesting the same accepted result is idempotent; corrections and withdrawals are traceable under the accepted ledger policy |
| RANK-POOL | Ratings identify ruleset and population; incomparable contexts are not silently mixed |
| RANK-UNCERTAINTY | Unrated characters remain uncertain; updates and inactivity obey the selected method, not invented constants |
| RANK-FICTION | Approved fictional CANON standings remain separate from observed empirical standings |
| CAL-HOLDOUT | No training/assessment leakage from future results, duplicated matches or generated stories into held-out evaluation |
| CAL-RELIABILITY | Assess probability reliability alongside proper scores and relevant uncertainty; a low Brier score alone does not prove calibration |
| CAL-CLAIMS | If outcome data or evaluation is absent, outputs retain the uncalibrated label and do not publish fabricated rank confidence |

These cases do not prescribe a ranking algorithm. Glicko-2 and TrueSkill are candidates to evaluate, with their parameters and assumptions taken from the chosen method and application evidence. The current BLOCK engine supplies neither the result ledger nor the calibration evidence needed to claim an accurate empirical ranking.

## Test the tests and the port

In a disposable implementation copy, deliberately remove each new admission gate or allow a generated result into ranking. The relevant new regression must fail. Do not mutate existing test files, suppress failures, or copy production calculations into the expected-result oracle. This checks that the test can detect the failure it claims to cover.

Run destination-native entrypoints as well as the original BLOCK CLIs. Cover source-root independence, CLI/import resolution, canonical schema references, documentation commands and backfill dry-run/apply/idempotence. The frozen recovery release must not reintroduce the invalid duplicate slot, unsupported style credit or obsolete source paths. Keep existing authored content and report competing values rather than overwriting them.

For statistical selection checks, derive any sample size, error tolerance and acceptance criterion from a declared statistical design or existing project policy. Report observed counts. Do not choose a favorable set of seeds or confuse repeated deterministic generation with independent empirical validation.

## Exit evidence for the next IDE

The destination must provide public-entrypoint rejection/no-credit evidence for both exploits, preservation of legitimate cards/coordination, original-suite and new-test results, admitted-configuration traces, and explicit separation of narrative from ranked evidence. Tiers/ranking remain unreleased until their own stated requirements and data are proven. Record untested domains instead of claiming exhaustive coverage.
