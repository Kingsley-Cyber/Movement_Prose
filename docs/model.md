# Model and state contract

The version in `data/model.json` owns quantitative assumptions. All numerical tendencies and probabilities are authored BLOCK rules. The engine has no empirical calibration dataset.

## Matchup calculation

Each option has explicit `answers` and `exposes` lanes. For a same-dimension cell, the base edge is half of the row's fraction of reachable column exposures minus the column's fraction of row exposures. A self-match cancels. This preserves reciprocity and permits non-transitive cycles. A zero explains either disjoint lanes or balanced opposing access.

For hands/defense versus targeting/kicking, the base edge is `(covered attack lanes - exposed attack lanes) / number of attack lanes`. A positive value favors the defending row. The executable calculation filters out attack lanes for which the attacking card has no trained legal attack. One configuration does not grant another school’s movements.

The MMA adaptation replaces the boxing cover set with its recorded MMA cover set. For a specific entry or leg exposure, susceptibility is multiplied by the ratio of boxing readiness to MMA readiness. This is an explicitly authored sensitivity rule, not an estimate of takedown or kick success. It applies to the named exposure only. Ratings never sum to a power score.

For same-dimension matrices, evaluate A's row against B's column once. For asymmetric matrices, calculate `(edge(A row, B column) - edge(B row, A column)) / 2`. This creates a signed edge for A while counting neither direction twice. A missing card selection contributes no matrix edge; only the conditional NULL rule can penalize it.

Normalize weights over matrices legal under the ruleset. Boxing therefore excludes tie and kicking matrices and divides each remaining weight by the remaining total. The largest weight belongs to mentality; stance and tie follow, then their cross interaction. All weights and their rationale are in configuration.

Let `M` be the sum of normalized signed matrix contributions. Let `sA - sB` be the net synchronized slots. Let `nA` and `nB` count distinct NULL dimensions with a legal trained opponent entry and a reachable range. Then:

```
zA = M + 0.15 * (sA - sB) + 0.20 * (nB - nA)
P(A) = 1 / (1 + exp(-zA))
P(B) = 1 - P(A)
```

The 0.15 and 0.20 coefficients come directly from the supplied specification. No separate bonus is added for the opponent's inverse calculation. A reachable NULL is counted once per missing dimension even if several attacks can exploit it. A locked conditional skill is unavailable. Its future gate is reported as a possible mitigation. Shared-range compatibility allows sequencing; disjoint preferred ranges require explicit movement. It adds no unexplained scalar bonus.

Reachability means a potential legal path exists, not that the opponent cannot stop it. Standing ranges are connected by measured adjacent staging steps. Ground debt access needs a trained takedown or guard-entry technique. A fighter with no such technique cannot acquire a ground exploit by description alone.

## Direction and replay

Outcome selection samples an explicit seed in sorted fighter-ID order. Swapping input order preserves the sampled identity. Director-controlled mode changes only the selected path, never the prediction.

The planner uses all ten required tactical phases. It obtains attack candidates from actual reachable debts or a conditional NULL, stages their range, emits their required setups, then records execution, attempted defense, explicit contact, reaction and recovery. The library’s pivot-to-low-kick transition can follow an established angle if the target debt and technique are available. Grappling paths continue from actual top/bottom or collar control rather than returning to unrelated striking.

Each event has a causal predecessor and snapshots. The reducer owns state changes. Validation recomputes every transition and compares stored states and effects. It rejects unknown identities, unavailable techniques, missing setups/contacts, early reactions, nonadjacent moves, unearned grips, altered injury state and false outcomes. It also recalculates the original prediction.

The condensed exhibition decision must be supported by the selected fighter’s greater recorded contact/control marks. These marks are qualitative narrative accounting units. A finite measured deficit determines any additional exchange; there is no hardcoded named winner or arbitrary retry budget. This is a conditional choreography path after sampling, not a stochastic biomechanical fight simulator.

World x/y coordinates use meters; x increases to screen right, y away from the fixed camera side. Lead/rear actions are translated to anatomical left/right using orientation at execution. Staging distances and arena geometry are explicit CANON configuration. Time slices derive from requested duration divided by the emitted event count. Timing and poses require physical review before production animation.

## Research boundary

The source registry records exact URLs, publishers, access dates, applicable claims and limitations. England Boxing supplies the range/tempo/angle drill context; USA Wrestling supplies listed entries, ties and rides; the IJF defines the small outer reap; Evolve provides possible counter sequences; ABC supplies the legal subset. Thomas Green supplies cultural context for 52s, and Lyte Burly supplies a contemporary practitioner’s self-description. Neither verifies BLOCK shield mechanics, Uno, 52-Dutch, numerical scores or universal lineage.

Counter edges and debt paths are inferred or CANON relationships. Source-backed technique existence never implies a scientifically measured matchup advantage. Weakly non-losing rows are disclosed by the audit along with incoming cross-dimensional counters. No option beats all others in its dimension, and every option has exploitable debts.
