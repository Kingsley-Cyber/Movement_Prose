# Codebase Intent Gap Analysis

**Verdict:** FAIL
**Repository:** /Users/king/Documents/Codex/2026-10-22/g/block_fight_engine
**Plan:** Confirm fairness findings and prepare remediation, tests and assessment guidance for movement prose e2e
**Revision:** Supplied block-1 working directory; no Git repository or commit is present
**Audited at:** 2026-10-22, using the client date

The current engine is not ready to act as an authoritative ranked-match judge. Two public-CLI counterexamples show unsupported card claims increasing assessed win probability. Its original tests still pass. The audit deliverable is complete; the production defects remain open for the destination IDE.

## Intent Contract

Confirm the earlier findings through executable evidence, preserve the original code and tests, distinguish defects from permitted storytelling, and provide an implementable repair and test plan. Explain whether tiers or ranking are necessary without inventing scores, thresholds, sample sizes or new coefficients.

The original engine contract permits seeded winner selection followed by conditional choreography. This audit adds a question about using those outputs for fair assessment. A probability draw selecting the less favored fighter is not itself an error. Card admission that awards unsupported capability credit is a defect. Presenting a constructed narrative score as independent evidence of merit would misuse the current design.

Acceptance for this handoff is a reproducible finding, a source location, an expected-behavior oracle and a smallest repair for each confirmed issue. `TEST_PLAN.md` specifies broader planned coverage. No finite suite can establish every possible fighter, fight state, random stream or future implementation.

## Actual Runtime

The public path is `predict.py → engine.probability.predict → Knowledge.card → matchups.evaluate / null_seams → logistic probability`. `Knowledge.card` checks canonical option IDs, slot counts, unique slot IDs and technique training. It does not establish whether separate slot IDs describe distinct coordination, or whether a selected style is supported by the training that its scoring presumes.

The direction path is `plan_fight.py → fight_director.plan → state reducer → graph replay → choreography / prompts`. The winner is selected at `engine/fight_director.py:125`. At line 213 the planner adds scoring actions until that selected winner has more contact/control marks. State replay checks the consistency of that constructed sequence; it does not independently decide who should win.

### Confirmed findings

| Finding | Public behavior | Consequence |
|---|---|---|
| F-001 Duplicate synchronization claim | Copying an existing Imani slot, with a fresh ID and description, is accepted. Training and available techniques remain equal. Probability against Donnell increases from **50.479152% to 54.219110%**; logit increases by the specified **0.15**. | Self-declared duplicate coordination can earn another slot bonus. |
| F-002 Unsupported style selection | Changing Donnell's NULL tie to `tie.anti_grappling`, without adding training or techniques, is accepted. His probability against Imani increases from **49.520848% to 55.498506%**. The NULL logit changes from **−0.20 to 0**, and style matrices also change. | A label erases a missing capability and obtains style credit without its supporting ability. |
| F-003 Outcome-first choreography | Seed 42 selects Maleek and produces marks 3–2; adjacent seed 43 selects Donnell and produces marks 3–1. Maleek's underlying model probability stays **48.521265%**. | These are conditional stories. Their marks must not validate the prediction or update an empirical ranking. This is a confirmed design boundary, not a violation of the original outcome-selection contract. |

These are changes in probability, not guaranteed wins. They are exploitable admission defects if users may submit or change cards. Centrally authored cards reduce that exposure, but do not establish model calibration or make inconsistent cards sound.

**Slot qualification matters:** unchanged available techniques alone do not prove a slot is fraudulent. A fighter can coordinate existing techniques in a genuinely new way. F-001 copies an existing bundle with no new coordination mechanism. Repair must validate distinct coordination rather than demand a new martial art or move for every slot.

### Design limits relevant to assessment

The model's weights, lane scores and adaptation ratios are authored assumptions. The code explicitly labels the probability uncalibrated. The schema and score path do not include individual proficiency estimates, measured mass/reach, a results ledger or an uncertainty-bearing ranking model. Damage and fatigue are tracked semantically; they are not a validated physiological performance model.

The default planner records contacts as landed even after an attempted defense. Its selected-winner branch controls the narrative. This is consistent with authoring a permitted path, but it cannot support a claim that actions independently generated the result. Source: `engine/fight_director.py:57`, especially lines 69–76.

No production repair is included in this handoff. The original archive also remains the earlier implementation; this bundle supersedes its broad fitness claims for ranked assessment, not its source files.

## Gap Matrix

| ID | Requirement | Expected evidence | Observed evidence | Status | Impact | Dependency | Smallest remediation | Verifier |
|---|---|---|---|---|---|---|---|---|
| REQ-001 | Award synchronization credit only for distinct admitted coordination | Duplicate claims rejected or contribute no extra credit | F-001; CLI exit 0; engine/ontology.py:72 and engine/probability.py:18 | PARTIAL | Blocks fair admission of submitted cards | Define a slot's semantic identity and evidence | Validate distinct supported coordination before applying the existing coefficient | verify_findings.py and planned slot-admission cases |
| REQ-002 | Bind selected styles and NULL coverage to actual capabilities | Unsupported style cannot remove a missing capability | F-002; CLI exit 0; engine/ontology.py:66 and engine/capabilities.py:41 | PARTIAL | Can reverse the model favorite without new training | Canonical requirements for each relevant option | Resolve one supported combat configuration used by scoring and execution | verify_findings.py and planned style-binding truth tables |
| REQ-003 | Preserve complementary probabilities and cosmetic invariance | Swap and display-metadata controls succeed | entrypoint: verify_findings.py calls predict; wiring: matchups.evaluate and probability.predict; outcome: controls true in reproduction_results.json; verification:PASS | WORKING | Existing mathematical protections worth preserving | Same ruleset and model | Preserve these invariants during repairs | Supplied controls and original prediction tests |
| REQ-004 | Preserve honest seeded/director storytelling labels | Original prediction retained and selected outcome explicit | entrypoint: plan; wiring: selection and graph validation; outcome: two distinct seeded paths validate with unchanged probabilities; verification:PASS | WORKING | Supports conditional choreography within its stated scope | Fixed cards and seed | Retain this path; prohibit ranking consumers from treating its score as independent evidence | F-003 and original director-mode tests |
| REQ-005 | Independently adjudicate outcomes from interactions if that feature is requested | No selected winner is passed into interaction resolution | plan receives/chooses winner before exchanges; source search found no independent adjudication path | MISSING | Current scene ledger cannot prove deserved victory | Explicit decision to build an independent simulator | Do not expose an independent-judge claim; build such a path only under an explicit accepted contract | Planned mode-separation and causal-resolution cases |
| REQ-006 | Quantify person-specific ability and physical context | Defined units, provenance and uncertainty for modeled inputs | rg over engine, schemas and model found authored tendencies but no physical/proficiency assessment model | MISSING | Style similarity can conceal ability or size differences | Evidence and approved modeling policy | Introduce only the assessment inputs that have defined meanings and evidence | Planned assessment-profile cases |
| REQ-007 | Maintain a results-based contextual ranking with uncertainty | Admissible independent results and traceable rating updates | No ranking/results ledger exists in the inspected runtime | MISSING | Generated stories cannot support empirical rankings | Legitimate outcomes and chosen rating policy | Keep characters unrated until admissible records exist | Planned ranking-ledger cases |
| REQ-008 | Establish calibration before interpreting percentages as observed win frequencies | Held-out outcomes and calibration evaluation | engine/probability.py:53 explicitly reports no empirical calibration | MISSING | Numerical precision can be mistaken for demonstrated accuracy | Independent relevant outcome data | Preserve the uncalibrated label; evaluate before making calibrated claims | Planned reliability and proper-score evaluation |
| REQ-009 | Preserve existing tests during diagnosis | Current original suite passes and hashes match | entrypoint: python -m pytest -q; wiring: original suite; outcome: 58 passed in 70.94s and hashes equal; verification:PASS | WORKING | Prevents masking a defect by changing tests | Existing test contract | Preserve tests; resolve any actual contract conflict explicitly | evidence/original_suite_run.json |

## Directory Contract

This audit inspects the source working directory. It does not claim the destination `movement prose e2e` was inspected, migrated or repaired.

Keep the destination repository as the single Git/project root. Resolve owners and collisions there before importing source. Expected owners in the supplied layout are:

| Owner | Contract |
|---|---|
| `engine/ontology.py`, schemas and existing capability resolver | Card admission and a supported resolved configuration |
| `engine/probability.py`, `engine/matchups.py`, `data/model.json` | Auditable scoring and the unchanged specified slot/NULL coefficients |
| `engine/fight_director.py`, `engine/event_graph.py` | Conditional narrative and its semantic verification |
| Existing destination assessment/ranking owner, if present | Independent result provenance and any ranking updates |
| Canonical data and `resources/recovery.json` | Versioned valid content, safe backfill and no reintroduction of inadmissible claims |

Prefer an existing resolver over a second validation engine. All scoring and execution must consume the same admitted capability facts. Do not scatter style requirements among separate CLI, prediction and planner implementations.

### Existing test contract that the next IDE must inspect

`tests/test_slots.py:7` adds a declared slot using `basic_movement` without changing available techniques, then asserts the supplied 0.15 logit increment. This tests the coefficient, not evidence of earned coordination. It is not the same as the exact copied-slot probe.

Do not interpret the proposed repair as “new slot requires a new technique”; that would reject legitimate coordination and could conflict with this original test. First define admissible coordination. If the resulting policy contradicts the original fixture, stop the affected change, report the exact conflict, and request explicit permission before any test edit. Do not add a bypass for that test, weaken assertions, or silently exempt untrusted production cards.

## Remediation Order

### Admit supported cards

Specify what proves a distinct synchronized bundle: canonical component techniques, their simultaneous/sequential coordination, prerequisites, and accepted evidence. Ignore IDs, descriptions and unordered set order when detecting an exact duplicate. Preserve ordered action sequences where their order has mechanical meaning. Define which selected options require particular training or execution support.

Implement those rules through the current admission/resolution path. Reject an inconsistent submitted card with an explanation before calculating probability. Apply the original 0.15 coefficient only to admitted distinct slots. Compute NULL coverage from admitted capabilities and actual legal access, not the presence of a style string. Retain the specified 0.20 term once per reachable missing dimension.

Exit evidence: both CLI exploits fail closed or receive no unsupported extra credit; approved cards and positive examples of distinct coordination remain usable. Preserve probability symmetry, original checks and provenance. Any changed canonical card requires an explicit CANON revision, not invented training presented as verified fact.

### Separate assessment from conditional storytelling

Assessment should expose the uncalibrated estimate, evidence and uncertainty. A sampled winner is a draw from that model, not proof that fighter is better. Director-controlled and sampled choreography remain explicitly conditional. A higher layer must not ingest their manufactured contact marks as independent observations or empirical rating evidence.

Freeze card versions, ruleset, model and selection policy before an outcome is exposed. Where a ranked service is introduced, it must control its accepted run and seed policy; letting a participant choose a favorable rerun is not neutral adjudication. Do not invent a retry quota. The original local storytelling CLI can continue to allow creative reruns because its output remains narrative.

An independent interaction simulator would require its own accepted mechanics and outcome policy. Merely deleting the final score-increasing loop would not make the preceding winner-conditioned exchanges neutral. Do not claim that a renamed mode or another random draw creates a physical simulator.

### Add assessment profiles only with defined evidence

**A single power tier is not needed to fix the confirmed defects.** For the broader assessment request, use distinguishable inputs:

| Quantity | Representation and purpose | Avoid |
|---|---|---|
| Capability proficiency | Per-capability or per-technique assessment with scale definition, evidence, context and uncertainty | Treating a style label or more slots as mastery |
| Physical context | Values with units and provenance, such as mass and reach, only when the mechanics actually consume them | Adding unexplained size bonuses or inventing absent measurements |
| Coordination | Distinct admitted relationships among known techniques; slot count remains the existing coordination concept | Counting cosmetic copies or substituting technique count for coordination |
| Current condition | Explicit fatigue/injury state with defined consequences if modeled | Calling current contact marks medical damage or treating fatigue as already calibrated |
| Competitive standing | Results-based rating within a defined ruleset/population, with uncertainty | Treating rank as a guarantee of victory or feeding generated wins back as evidence |

These are separate quantities, not a request to add every conceivable statistic. Introduce a field only when its meaning, source and effect on a live requirement are defined. Missing evidence stays unknown or unrated; it must not silently become novice, zero, average, or maximum uncertainty with an invented numeric value.

If tiers are displayed, derive them from an approved rubric or relevant data. Their number, names, boundaries, priors and numerical effects are unresolved policy choices. This report supplies none. A label should not itself grant another scoring bonus. The existing 1–5 tendency ratings describe styles and must not be relabeled as individual skill.

Glicko-2 represents rating, deviation and volatility; it is a candidate for uncertainty-bearing one-versus-one ranking after admissible outcomes exist. TrueSkill also models uncertainty and accommodates draws and teams. Neither source validates BLOCK probabilities or supplies fighter attributes. Choose a method for the actual data and context, rather than installing both. [Glickman's specification](https://www.glicko.net/glicko/glicko2.pdf), [Microsoft's original TrueSkill publication](https://www.microsoft.com/en-us/research/publication/trueskilltm-a-bayesian-skill-rating-system/).

Keep published fictional CANON standings separate from observed empirical results. An approved fictional ledger can support a labeled fictional ranking, but it must not become evidence of real-world accuracy. Explain any combination of historical rating, measured proficiency and style features so the same evidence is not credited repeatedly.

### Prove coverage and calibration honestly

Execute the planned admission, invariant, mode and state tests in `TEST_PLAN.md`, preserving existing tests. Use finite enumeration where the domain is finite, plus generated inputs and model-based transition sequences where it is not. Hypothesis documents generation and checking of interacting stateful action sequences; using that method is a recommendation, not an already installed or executed test suite. [Hypothesis stateful testing](https://hypothesis.readthedocs.io/en/latest/stateful.html).

Before calibrated probability claims, use held-out relevant outcomes, leakage controls and reliability analysis. Brier/log loss measure more than calibration alone, so a favorable score does not by itself establish reliable percentages. No dataset, score cutoff, bin count or required sample size is invented here. [Probability calibration documentation](https://scikit-learn.org/stable/modules/calibration.html).

### Close the destination handoff

Inspect the destination repository and governing instructions. Integrate within its actual root and native entrypoints. Update its documentation, schema/data versions, frozen recovery content and safe backfill scope. Run destination checks and unchanged original tests, then demonstrate both original matchups and declared outcome modes. Verify operation without the old absolute source path. The destination IDE must report its actual evidence and remaining gaps.

### Rejected scope claims

- “All possibilities are tested”: arbitrary future cards and continuous fight states are not a finite enumerated domain.
- Another universal power score or arbitrary tier cutoffs: neither closes the demonstrated admission gaps.
- Guaranteed victories for higher ranks, or tuning the Maleek example to a preferred percentage: inconsistent with conditional counters and honest validation.
- Weakening tests or suppressing the fairness probe's failing exit: would hide the finding rather than fix it.
- A full physical simulator or ranking service as a prerequisite to repair two validation defects: unnecessary for that repair; require a separate accepted capability contract.

## Verification Record

Actual executed findings and commands are in `evidence/cli_executions.json`, `evidence/reproduction_results.json` and `evidence/original_suite_run.json`.

```sh
block_fight_engine/.venv/bin/python \
  outputs/BLOCK_FAIRNESS_HANDOFF/verify_findings.py \
  --root block_fight_engine \
  --output-dir outputs/BLOCK_FAIRNESS_HANDOFF/evidence
# Exit 1: F-001 and F-002 confirmed; F-003 design boundary confirmed.

# Executed from the original project root:
.venv/bin/python -m pytest -q
# Exit 0: 58 passed in 70.94s.
```

The two adversarial prediction CLI calls both exited 0 and saved complete traces. An invalid-option control was rejected. Probability complementarity and display-name invariance controls passed. Protected source/data/test hashes before and after the probe matched; the original-suite run also preserved its test hashes. Source excerpts are captured in `evidence/source_evidence.json`.

The same executable probe checks already-known counterexamples. Its nonzero current result is a failing fairness gate, not a claim that validation execution failed. The broader planned tests and ranking methods have not been implemented or run.

## Residual Unknowns

The source defects remain unpatched. No new proficiency tiers, numerical fighter assessments, independent simulator, ranking ledger or calibration system has been added.

The destination repository's actual layout, authority rules for submitted cards, source of admissible results, accepted proficiency rubric and ranking population remain unknown. The next IDE must inspect or define those inputs before claiming a repair or ranking release. Self-declared evidence fields cannot verify a person's ability; admission needs an external authority or explicitly labeled author-approved CANON.

Fixing F-001/F-002 will close demonstrated scoring loopholes. It will not establish real-world win accuracy, physical correctness, or exhaustive fairness.
