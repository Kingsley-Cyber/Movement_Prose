# Run 001: one strike and one block

**Request.** One strike and one block: A prepares, drives one straight strike, B blocks with a forearm at a visible contact point, A finishes while B recoils into a support step, both recover their guard.

**Why this fixture.** It is the first empirical gate in the lexicon (section 9): one strike and one block, small and independent, before any dense fight. The events are the bundle's own `sequence_plan` (7 events, 72 frames at 24 fps, 3 s): A prepares (0.0-0.5 s), A strikes (0.5-1.0 s), forearm contact at 1.0 s held two frames, A's follow-through and B's recoil overlap, both recover their guard by 3.0 s.

**Arms.**
- `arm_A_baseline/prompt.txt`: the bundle's `text_candidate`, verbatim.
- `arm_B_compiled/prompt.txt`: the agent's projection of `ir.json` for `generic_web_ui` (no negatives folded in). `post_plan.json` carries the hold, accent and overlay frames; `receipt.json` the manifest.
- Engine folders (`ltx_video_098_distilled_default/`, `wan21_t2v_diffusers/`) show the negatives routing for a target without and with an active negative field.

**Acceptance (lexicon section 9).** Distinct named forearms meet visibly; recoil begins after contact; two actors persist. Compare baseline action versus action plus explicit contact staging.

**Status.** Nothing rendered. Every row is an untested prompt candidate. Fill `SCORECARD.md` after rendering.
