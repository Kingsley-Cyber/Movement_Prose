# Diversity knobs, typed specimens, module relations (2026-10-22)

Owner: "check the code and test your hypothesis; if you see a gain and need, implement it and update documentation." Pasted design: relation-following module retrieval, diversity knobs with verbalization maps, code blocks as schemas.

## Tested before building
- Taste profiles carry an effort quality and preferred rows per slot; no style axes with options → knobs are new capability.
- The parser drops `<code class="language-…">`: 1,185 text, 315 json, 253 yaml, 22 xml blocks are indexed as untyped `code` passages → typing them is a one-column change.
- Temporal coupling vocabulary (precedes, lags, synchronizes_with, peaks_with, holds_during, releases_after, triggered_by) is defined in a013 (Temporal Coupling) and a032; structured example edges exist only as a short `coordination:` YAML list between generic events (gaze_shift precedes head_orientation, breath_hold holds_during anticipation, exhale synchronizes_with action_release, facs.au4 peaks_with action_apex). Nothing links our 64 rows. Relation-following must be authored with evidence; its gain is measured below.

## Predictions (written before code)
1. `handbook_passages.language` + `specimens` command: 315 json + 253 yaml + 22 xml typed; `specimens --language yaml --text contact` returns the contact-contract templates; retrieval benchmark unchanged (code excluded by default).
2. Knobs: five axes (laban_profile, exposure_cadence, smear_policy, impact_accent, camera_behavior), three options each, prose in words only; `variants <run_dir> --axis X` writes one JSON prompt per option that differs from the base in exactly one grammar field; no knob prose trips `NUMERIC_IN_PROMPT`.
3. Module relations: a memory table with the seven temporal relations plus requires_setup and reacts_to, seeded with the handbook's example edges (source handbook) and ~14 authored directive-level edges (each citing a passage). `propose --follow` pulls supporting rows per beat from a beat's primary action. Measured gain: given only run 001's primary_action rows, follow recovers at least 40% of the other 31 hand-selected rows (prediction: 40–60%). Below 40% the feature stays off by default and is recorded as low value.

## Measured
1. Specimens: `language` column on passages; 313 json, 252 yaml, 22 xml, 24 bash, 6 python, 2 mermaid, 1 jsonl, 1,196 text blocks typed. `specimens --language yaml --text contact` returns the contact state-machine and contact-contract templates (a055#0556, a036#0227, a031#1552). Benchmark unchanged (held).
2. Knobs: `agent/data/knobs.json`, five axes × three options, prose checked for fps/frame/amplitude numbers (none). `variants <run> --axis X` writes three one-change JSON prompts; each differs from the base in exactly one `animation_grammar` field (tested on run 002). `ask --knob axis=option` appends the option's prose with its passages and preferred rows (held).
3. Relations: `module_relations` in memory with the handbook's seven temporal relations plus requires_setup and reacts_to; seeded 25 (5 handbook example edges between generic events, 20 authored directive edges, each citing a passage). `propose --follow N` pulls supporting rows per beat from its primary actions. Measured on run 001 (6 primary-action seeds, 30 other hand-selected rows): depth 1 recovers 10 (33%), depth 2 recovers 11 (37%), one extra pull (`aa_secondary_contact_ring`, a reasonable add). Prediction 3 (≥ 40%) MISSED on the full set → follow stays opt-in. Nine of the 30 rows are lighting, shading and static-environment skin that causal/temporal relations should not pull; on the 21 causal/temporal rows recovery is 52%.

## Honest reading
Knobs and specimens are straightforward wins. Relation-following works as designed but its edge set is young (25); growing it from future runs' selections, not by tuning to run 001, is the honest path. The pasted design's offer of a BeautifulSoup parser was redundant; its knob examples carried frame numbers, which the lexicon rule forbids in prose, so the shipped knob prose is words only.
