# Mechanism vocabulary candidates (for owner review)

Mined 2026-10-22 from 16304 prose passages: 350 candidates after filters; top 150 listed, 200 more omitted.

Rule: hyphenated or '<word> <mechanism noun>' terms; df 3..1%; >= 2 chapters; not an alias; META_STOP removed; score = 0.5*chapters + 3*unit_share + 2*label_share + min(causal,5) + 0.5 if hyphenated

unit = share of the term's passages carrying numbers or units (ms, fps, frames, deg, s, px, %, Hz); label = share with a moment/slot label ≥ 2; causal = passages with a requires/depends_on/conflicts_with edge + clauses containing the term.

Reviewed by agent (owner delegated 2026-10-22). Accepted terms are concept aliases in agent memory and are linked in the index on rebuild.


## Accepted (now concept aliases; excluded from the candidate table below because the miner skips known aliases)

| concept | kind | aliases |
|---|---|---|
| `contact_physics` Contact physics | mechanism | relative velocity, surface contact, hand contact, sticking contact, tangential velocity |
| `contact_timing` Contact timing | mechanism | before contact, after contact, during contact, contact onset, contact frame, initial contact, contact transfer, staged contact, without contact, near-contact, near contact |
| `near_miss` Near-miss | mechanism | near-miss, near miss, whiff, miss point, apex without contact |
| `push_in` Push-in / dolly-in | technique | push-in, push in, dolly-in, dolly in, pull-out, push-in/pull-out |
| `close_up` Close-up framing | technique | close-up, close up, medium close-up, tight framing |
| `low_angle` Low-angle view | technique | low-angle, low angle, worm's-eye |
| `wide_angle` Wide-angle lens | technique | wide-angle, wide angle, close-wide lens, close_wide_lens |
| `focal_length` Focal length | technique | focal-length, focal length, lens choice, telephoto compression |
| `motion_blur` Motion blur | technique | motion blur, motion-blur, blur streak |
| `key_pose` Key pose | technique | key-pose, key pose, key drawing, held key |
| `inbetween` In-betweens | technique | in-between, in-betweens, inbetween, inbetweens, tween |
| `micro_pause` Micro-pause | technique | micro-pause, micro-pauses, micro pause, pre-emphasis pause |
| `reaction_timing` Reaction timing | mechanism | reaction onset, perception delay, reaction delay, reaction time |
| `support_contact` Support contact | mechanism | load-bearing, support contact, foot-contact, foot contact, heel strike, foot plant |
| `push_off` Push-off | mechanism | push-off, push off, drive off the rear foot, compression/push-off |
| `soft_tissue` Soft-tissue response | mechanism | soft-tissue, soft tissue, jiggle, tissue response |
| `rigid_body` Rigid-body physics | mechanism | rigid-body, rigid body |
| `kinematics` Kinematic quantities | mechanism | angular velocity, velocity profile, acceleration profile, time-to-peak, jerk, deceleration ramp |
| `screen_space` Screen space | concept | screen-space, screen space, image-space, image-plane, image plane |
| `reference_frame` Reference frame | concept | coordinate frame, reference frame, world-space, world space, actor-relative, camera-relative, root-relative |
| `screen_direction` Screen direction | concept | left-to-right, screen direction, screen-direction, 180-degree line |
| `multi_actor` Multi-actor scene | concept | multi-actor, two-actor, two actors, two fighters |
| `hand_object` Hand-object interaction | concept | hand-object, human-object, hand-object contact, hand object interaction |
| `tempo_grid` Tempo grid | technique | tempo curve, phase lock, musical grid, beat grid |
| `t2v` Text-to-video | workflow | text-to-video, text to video, t2v |
| `v2v` Video-to-video | workflow | video-to-video, video to video, v2v, reference-video driving |
| `kinetic_chain` | alias addition | proximal-to-distal, proximal to distal |
| `weight_transfer` | alias addition | center-of-mass |
| `camera_shake` | alias addition | camera impulse, impact impulse |
| `impact_flash` | alias addition | one-frame flash, impact-frame |
| `i2v` | alias addition | first-frame |
| `first_last_frame` | alias addition | last-frame, first-and-last |
| `slow_motion` | alias addition | time-warp |

## Remaining candidates (rejected unless marked)

| # | term | df | ch | unit | label | causal | example | accept | reject | kind |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `cpcs-mx` | 88 | 4 | 0.00 | 0.17 | 5 | a054#0205: cpcs-mx can store or derive: |  | project name |  |
| 2 | `research-to-representation` | 5 | 3 | 0.00 | 0.00 | 4 | a033#0002: perform a research-to-representation closure pass over the facs/laban  |  | process term |  |
| 3 | `panel contact` | 6 | 2 | 0.00 | 0.33 | 4 | a039#0135: represent slider motion, panel contact transfer, panel rotation, gusse |  | bag-spec specific |  |
| 4 | `application-level` | 5 | 2 | 0.00 | 0.00 | 4 | a031#1997: gemini structured outputs improve parseability, but official guidance  |  | software architecture |  |
| 5 | `four-second` | 3 | 2 | 0.00 | 0.00 | 4 | a104#0096: clipping uses absolute times based on the video’s internal metadata an |  | duration literal |  |
| 6 | `multi-shot` | 30 | 8 | 0.00 | 0.43 | 0 | a086#0135: single-shot versus multi-shot generation; |  | workflow structure, not a mechanism |  |
| 7 | `post-generation` | 9 | 7 | 0.11 | 0.44 | 0 | a041#0054: post-generation edit. |  | pipeline stage |  |
| 8 | `motion-capture` | 9 | 4 | 0.00 | 0.33 | 2 | a031#0612: retrieval from motion-capture libraries; |  | data source |  |
| 9 | `two-frame` | 4 | 2 | 0.50 | 1.00 | 0 | a054#0293: use two-frame anticipation hold; |  | duration fragment; the hold itself is hit_stop |  |
| 10 | `video-understanding` | 3 | 2 | 0.67 | 0.67 | 0 | a031#2793: [s67] google ai for developers. (2026). video understanding: gemini ap |  | API product |  |
| 11 | `physical contact` | 15 | 7 | 0.00 | 0.53 | 0 | a104#0239: whether the effect hides physical contact; |  |  |  |
| 12 | `provider-facing` | 9 | 6 | 0.00 | 0.00 | 1 | a036#0432: render concise provider-facing instructions. |  | provenance/role |  |
| 13 | `high-confidence` | 7 | 6 | 0.00 | 0.00 | 1 | a024#0203: rather than treated as a high-confidence primitive. |  | epistemic grading |  |
| 14 | `real-time` | 4 | 4 | 0.00 | 0.50 | 1 | a031#2805: [s79] fang, h.-s., li, j., tang, h., xu, c., zhu, h., xiu, y., li, y.- |  | systems term |  |
| 15 | `one-frame` | 11 | 4 | 0.09 | 0.82 | 0 | a054#0131: one-frame flash at the same exposure; |  | bare duration; 'one-frame flash' added to impact_flash |  |
| 16 | `video-generation` | 11 | 7 | 0.00 | 0.18 | 0 | a053#0295: https://developers.openai.com/api/docs/guides/video-generation |  | product category |  |
| 17 | `every frame` | 9 | 6 | 0.00 | 0.67 | 0 | a036#0083: joint positions at every frame; |  | generic |  |
| 18 | `shot-level` | 6 | 5 | 0.00 | 0.67 | 0 | a055#0407: / decomposition / controls complexity / riskprofile + policy / compile |  | architecture level |  |
| 19 | `state-transition` | 6 | 5 | 0.00 | 0.17 | 1 | a055#0798: the state-transition system governs execution. |  | software model |  |
| 20 | `physics-based` | 13 | 5 | 0.00 | 0.15 | 1 | a031#0619: physics-based control; |  | adjective |  |
| 21 | `camera-motion` | 9 | 6 | 0.00 | 0.33 | 0 | a054#0924: camera-motion readability; |  | generic |  |
| 22 | `pre-emphasis` | 3 | 2 | 0.67 | 0.33 | 0 | a030#0062: pre-emphasis pause 200–300ms before the payload word or the reveal (th |  |  |  |
| 23 | `project-specific` | 18 | 3 | 0.00 | 0.06 | 2 | a033#0058: possible project-specific numeric encoding; |  | provenance |  |
| 24 | `machine-readable` | 19 | 5 | 0.00 | 0.00 | 1 | a031#1819: visible or machine-readable provenance; |  | format |  |
| 25 | `single-pass` | 4 | 2 | 0.50 | 0.00 | 1 | a016#0310: veo 3.1 gained video extension in vertex ai, and seedance 2.5 supports |  | pipeline |  |
| 26 | `implementation-ready` | 3 | 3 | 0.00 | 0.00 | 2 | a107#0134: provide a concise implementation-ready list of: |  | process |  |
| 27 | `evidence-backed` | 5 | 4 | 0.00 | 0.20 | 1 | a032#0664: evidence-backed information; |  | epistemic |  |
| 28 | `execution-carrier` | 9 | 3 | 0.00 | 0.44 | 1 | a053#0322: cpcs concepts affected: runway prompt compiler; duration selection; ex |  | architecture |  |
| 29 | `time-indexed` | 15 | 6 | 0.07 | 0.07 | 0 | a032#0253: affect trajectories should be represented as time-indexed points or se |  | data shape |  |
| 30 | `aspect-ratio` | 3 | 2 | 0.33 | 0.67 | 0 | a031#1310: variant plan — which audience, platform, language, duration, and aspec |  | delivery format |  |
| 31 | `pose-conditioned` | 5 | 3 | 0.00 | 0.40 | 1 | a104#0035: compilation into text-to-video, image-to-video, pose-conditioned, rig- |  | workflow; too thin to carry |  |
| 32 | `round-trip` | 14 | 6 | 0.00 | 0.14 | 0 | a032#0468: round-trip comparison. |  | testing |  |
| 33 | `full-body` | 16 | 3 | 0.00 | 0.38 | 1 | a015#0317: full-body acting, |  | generic |  |
| 34 | `high-frequency` | 8 | 4 | 0.00 | 0.62 | 0 | a022#0020: sharp high-frequency transient; |  | generic |  |
| 35 | `sling-bag` | 4 | 4 | 0.25 | 0.25 | 0 | a053#0003: for the sling-bag failure, the most reliable stack is: |  | spec-specific prop |  |
| 36 | `optical-flow` | 11 | 5 | 0.00 | 0.36 | 0 | a054#0692: optical-flow or motion-field priors; |  | analysis method |  |
| 37 | `per-frame` | 11 | 5 | 0.00 | 0.36 | 0 | a031#0644: per-frame text/symbol tokens; |  | data shape |  |
| 38 | `contact-aware` | 9 | 2 | 0.11 | 0.44 | 1 | a031#0398: contact-aware kinematic cleanup; |  | adjective |  |
| 39 | `body-part` | 19 | 6 | 0.00 | 0.11 | 0 | a054#0674: body-part style; |  | generic |  |
| 40 | `multi-view` | 9 | 3 | 0.00 | 0.33 | 1 | a031#0752: calibrated multi-view video; |  | capture setup |  |
| 41 | `end-to-end` | 3 | 3 | 0.00 | 0.33 | 1 | a031#1737: end-to-end controllable video models; |  | ML term |  |
| 42 | `ground-truth` | 3 | 3 | 0.00 | 0.33 | 1 | a032#0951: the detector output may be useful for verification without being promo |  | evaluation |  |
| 43 | `reference-video` | 16 | 5 | 0.00 | 0.31 | 0 | a031#1735: reference-video driving; |  |  |  |
| 44 | `structured-output` | 12 | 4 | 0.00 | 0.00 | 1 | a060#0371: strict structured-output constraints can degrade reasoning-intensive t |  | API feature |  |
| 45 | `high-value` | 8 | 6 | 0.00 | 0.00 | 0 | a055#0108: this is high-value because: |  | generic |  |
| 46 | `time-based` | 7 | 2 | 0.00 | 0.00 | 2 | a104#0198: use time-based metadata for broad scene segmentation. extract: |  | generic |  |
| 47 | `variable frame` | 4 | 3 | 0.00 | 1.00 | 0 | a047#0005: repeated rounding causes drift, especially across long sequences or va |  | fragment |  |
| 48 | `left-foot` | 4 | 2 | 0.00 | 1.00 | 0 | a031#1502: final left-foot plant is locked to the recognition beat; |  | instance |  |
| 49 | `persuasive arc` | 4 | 2 | 0.50 | 0.50 | 0 | a031#1936: / sequence pass / 0.2–1 fps or full long-context video / story, topic, |  | narrative, not motion |  |
| 50 | `provider-control` | 4 | 3 | 0.00 | 0.25 | 1 | a100#0047: source: src-014 (user research return, staged) — gap_answer_03 §curren |  | provenance |  |
| 51 | `world-state` | 4 | 2 | 0.00 | 1.00 | 0 | a064#0022: research a world-state representation containing: |  | architecture |  |
| 52 | `high-acceleration` | 3 | 2 | 0.00 | 1.00 | 0 | a047#0007: a fast tempo can still contain a long micro-pause; a slow scene can co |  | adjective |  |
| 53 | `focus-related` | 3 | 2 | 0.00 | 1.00 | 0 | a102#0004: documented camera concepts include locked camera, handheld, tracking,  |  | fragment |  |
| 54 | `off-center` | 3 | 2 | 0.00 | 1.00 | 0 | a077#0119: trigger. an actor lands off-center, is struck, or changes direction sh |  | fragment |  |
| 55 | `phone-like` | 3 | 2 | 0.00 | 1.00 | 0 | a031#2283: phone-like vertical framing; |  | format |  |
| 56 | `micro-event` | 3 | 2 | 0.00 | 1.00 | 0 | a104#0145: / micro-event / brief accent / blink, breath, caption pop / impact fla |  | editorial grammar |  |
| 57 | `re-establish` | 3 | 2 | 0.00 | 1.00 | 0 | a079#0033: primary intervention — l5 (shot decomposition). do not combine an orbi |  | fragment |  |
| 58 | `text-only` | 9 | 5 | 0.00 | 0.22 | 0 | a034#0074: text-only prompt: |  | input mode |  |
| 59 | `whole-body` | 22 | 5 | 0.00 | 0.18 | 0 | a031#2341: 2d whole-body pose; |  | generic |  |
| 60 | `frame-exact` | 6 | 3 | 0.00 | 0.67 | 0 | a036#0088: frame-exact exposure and cut timing; |  | adjective |  |
| 61 | `act-two` | 5 | 2 | 0.20 | 0.60 | 0 | a099#0048: [s056] runway (2026), performance capture with act-two. locator: input |  | product |  |
| 62 | `high-fidelity` | 13 | 4 | 0.00 | 0.38 | 0 | a054#0021: natural movement and high-fidelity ugc |  | adjective |  |
| 63 | `free-form` | 8 | 5 | 0.00 | 0.12 | 0 | a060#0361: if a provider accepts only free-form prompting and exposes no event-ti |  | prompt style |  |
| 64 | `human-readable` | 9 | 5 | 0.00 | 0.11 | 0 | a024#0112: for authored human-readable direction: |  | format |  |
| 65 | `under-specified` | 5 | 3 | 0.00 | 0.60 | 0 | a036#0004: five mechanisms are missing or under-specified: |  | adjective |  |
| 66 | `shot-duration` | 5 | 3 | 0.00 | 0.60 | 0 | a031#2198: shot-duration distribution; |  | statistic |  |
| 67 | `frame-accurate` | 5 | 3 | 0.00 | 0.60 | 0 | a068#0037: frame-accurate audio-event synchronization; |  | adjective |  |
| 68 | `re-entry` | 6 | 4 | 0.00 | 0.33 | 0 | a086#0098: off-screen exits and re-entry. |  | fragment |  |
| 69 | `high-speed` | 3 | 2 | 0.00 | 0.33 | 1 | a020#0025: / trained high-speed kick / distal striking-point speed / 10.0–18.0 m/ |  | adjective |  |
| 70 | `cross-attention` | 3 | 2 | 0.00 | 0.33 | 1 | a031#0139: adapter features, cross-attention conditions, or adaptive-normalizatio |  | ML internals |  |
| 71 | `turn-taking` | 8 | 4 | 0.12 | 0.12 | 0 | a064#0089: turn-taking; |  | dialogue, not motion |  |
| 72 | `time-varying` | 12 | 4 | 0.00 | 0.25 | 0 | a031#0164: for au (i), cpcs defines the time-varying activation: |  | math |  |
| 73 | `append-only` | 11 | 5 | 0.00 | 0.00 | 0 | a057#0569: human override is append-only and superseding: |  | data policy |  |
| 74 | `inverse-dynamics` | 9 | 3 | 0.00 | 0.00 | 1 | a020#0055: inverse-dynamics residuals where dynamics are estimated; |  | analysis method |  |
| 75 | `side-specific` | 9 | 5 | 0.00 | 0.00 | 0 | a056#0083: side-specific joints; |  | schema term |  |
| 76 | `mixed-content` | 7 | 5 | 0.00 | 0.00 | 0 | a032#0475: mixed-content possibilities. |  | generic |  |
| 77 | `contact-guided` | 7 | 5 | 0.00 | 0.00 | 0 | a022#0046: [s038] cg-hoi authors (2024), contact-guided human-object interaction  |  | paper name |  |
| 78 | `long-duration` | 6 | 3 | 0.00 | 0.50 | 0 | a031#1921: long-duration narrative beats. |  | adjective |  |
| 79 | `long-horizon` | 6 | 3 | 0.00 | 0.50 | 0 | a060#0538: long-horizon capsule sufficiency across scenes/edits; |  | adjective |  |
| 80 | `research-backed` | 6 | 3 | 0.00 | 0.00 | 1 | a055#0143: these should be research-backed mappings or explicitly marked hypothes |  | epistemic |  |
| 81 | `cg-hoi` | 5 | 5 | 0.00 | 0.00 | 0 | a022#0046: [s038] cg-hoi authors (2024), contact-guided human-object interaction  |  | paper name |  |
| 82 | `fail-closed` | 5 | 3 | 0.00 | 0.00 | 1 | a024#0030: fail-closed or explicit degradation for unsupported required controls. |  | policy |  |
| 83 | `model-agnostic` | 5 | 3 | 0.00 | 0.00 | 1 | a060#0038: these are low-regret, model-agnostic infrastructure: |  | adjective |  |
| 84 | `cross-shot` | 4 | 4 | 0.00 | 0.25 | 0 | a031#2321: / wrong actor identity / occlusion or cut / track confidence; cross-sh |  | adjective |  |
| 85 | `camera-control` | 4 | 3 | 0.00 | 0.50 | 0 | a101#0002: kling's camera-control documentation exposes explicit camera movement  |  | API feature |  |
| 86 | `provider-neutral` | 4 | 4 | 0.00 | 0.25 | 0 | a057#0444: / canonical score authority / exact resolved provider-neutral control  |  | adjective |  |
| 87 | `model-dependent` | 4 | 3 | 0.00 | 0.00 | 1 | a030#0076: mouth to phonemes (model-dependent — keep the line short + clear so it |  | adjective |  |
| 88 | `strike-like` | 4 | 3 | 0.00 | 0.50 | 0 | a054#0451: reach or strike-like extension; |  | adjective |  |
| 89 | `event-time` | 4 | 4 | 0.00 | 0.25 | 0 | a031#2717: shot-boundary and event-time error; |  | schema |  |
| 90 | `partial-order` | 4 | 2 | 0.00 | 0.75 | 0 | a054#1198: / temporal_relations / partial-order dependencies |  | data structure |  |
| 91 | `causes drift` | 3 | 2 | 0.00 | 1.00 | 0 | a047#0005: repeated rounding causes drift, especially across long sequences or va |  | verb phrase |  |
| 92 | `martial-arts` | 3 | 3 | 0.00 | 0.00 | 1 | a036#0545: larger martial-arts move-name dictionaries; |  | domain label |  |
| 93 | `first frame` | 21 | 4 | 0.05 | 0.38 | 0 | a016#0218: / initial composition / first frame |  |  |  |
| 94 | `on-screen` | 6 | 3 | 0.17 | 0.17 | 0 | a104#0342: caption timing and on-screen text. |  |  |  |
| 95 | `phase-specific` | 6 | 3 | 0.17 | 0.17 | 0 | a054#1287: / timing_transform / phase-specific retime |  |  |  |
| 96 | `field-specific` | 3 | 2 | 0.00 | 0.67 | 0 | a031#1061: where (\oplus) is a field-specific merge operator. “more specific wins |  |  |  |
| 97 | `head-locked` | 3 | 2 | 0.00 | 0.67 | 0 | a009#0026: / camera (c) / shot size, angle, movement, lens character / pov_policy |  |  |  |
| 98 | `mid-stance` | 3 | 2 | 0.00 | 0.67 | 0 | a016#0009: / mid-stance / center of mass passes above support / “the pelvis trave |  |  |  |
| 99 | `when contact` | 3 | 3 | 0.00 | 0.67 | 0 | a053#0147: / shot size / extreme close-up, close-up, medium shot, wide shot / use |  |  |  |
| 100 | `floor contact` | 3 | 3 | 0.00 | 0.67 | 0 | a016#0088: the basketball falls under gravity, compresses subtly at floor contact |  |  |  |
| 101 | `seven-phase` | 3 | 2 | 0.00 | 0.67 | 0 | a046#0002: the cpcs seven-phase sequence and the bml sync points are different ta |  |  |  |
| 102 | `meaning-bearing` | 3 | 2 | 0.00 | 0.67 | 0 | a019#0007: / 4 / stroke / meaning-bearing apex, target acquisition, or contact /  |  |  |  |
| 103 | `py-feat` | 3 | 2 | 0.00 | 0.67 | 0 | a098#0023: / facs au � openface 2.x / py-feat / face frames / per-frame au intens |  |  |  |
| 104 | `reverse-compiled` | 3 | 2 | 0.00 | 0.67 | 0 | a031#0054: rq9. how can a known reference video be decomposed into a confidence-  |  |  |  |
| 105 | `band-limited` | 3 | 2 | 0.00 | 0.67 | 0 | a043#0010: handheld_impulse primitive parameters: amplitude, frequency_hz, impact |  |  |  |
| 106 | `structure-from-motion` | 3 | 2 | 0.00 | 0.67 | 0 | a031#2809: [s83] schönberger, j. l., & frahm, j.-m. (2016). structure-from-motion |  |  |  |
| 107 | `shot-scale` | 3 | 2 | 0.00 | 0.67 | 0 | a031#2135: approximate shot-scale label with confidence. |  |  |  |
| 108 | `around contact` | 3 | 3 | 0.00 | 0.67 | 0 | a054#0894: momentum change around contact; |  |  |  |
| 109 | `collision-free` | 3 | 2 | 0.00 | 0.67 | 0 | a068#0033: collision-free geometry or support mechanics; |  |  |  |
| 110 | `camera-side` | 13 | 4 | 0.00 | 0.15 | 0 | a054#1080: step-in and camera-side strike-like action; |  |  |  |
| 111 | `step-in` | 10 | 3 | 0.00 | 0.40 | 0 | a104#0525: step-in; |  |  |  |
| 112 | `three-dimensional` | 5 | 3 | 0.00 | 0.40 | 0 | a054#0326: shape flow, directional shaping, and carving-like three-dimensional ad |  |  |  |
| 113 | `lower-body` | 5 | 3 | 0.00 | 0.40 | 0 | a032#0381: upper body movement coordinated with lower-body/ground relationship; |  |  |  |
| 114 | `general-purpose` | 5 | 3 | 0.00 | 0.40 | 0 | a031#2165: whisper is a general-purpose speech-recognition model supporting multi |  |  |  |
| 115 | `gaze-target` | 7 | 4 | 0.00 | 0.14 | 0 | a031#1593: gaze-target accuracy; |  |  |  |
| 116 | `machine-checkable` | 8 | 4 | 0.00 | 0.12 | 0 | a005#0018: native job: resolved, exact, machine-checkable truth — timings, boolea |  |  |  |
| 117 | `pre-line` | 4 | 2 | 0.25 | 0.25 | 0 | a030#0016: / breathless / no inhale, no phrasing / pre-line breath + breath at th |  |  |  |
| 118 | `off-screen` | 9 | 4 | 0.00 | 0.11 | 0 | a031#2035: an off-screen threat; |  |  |  |
| 119 | `two-person` | 7 | 3 | 0.14 | 0.14 | 0 | a031#1649: for two-person or human–object scenes, evaluate: |  |  |  |
| 120 | `dust burst` | 7 | 2 | 0.00 | 0.86 | 0 | a104#0575: dust burst; |  |  |  |
| 121 | `counter-motion` | 5 | 2 | 0.00 | 0.60 | 0 | a036#0255: counter-motion must name: |  |  |  |
| 122 | `head-pose` | 11 | 4 | 0.00 | 0.09 | 0 | a031#1592: head-pose error; |  |  |  |
| 123 | `rolling-shutter` | 6 | 3 | 0.00 | 0.33 | 0 | a031#2054: e. stabilization and rolling-shutter artifacts. |  |  |  |
| 124 | `multi-surface` | 3 | 3 | 0.00 | 0.33 | 0 | a036#0211: / grip / maintained multi-surface stick contact with intentional reten |  |  |  |
| 125 | `per-event` | 3 | 3 | 0.00 | 0.33 | 0 | a104#0016: / jsonl / append-only evidence, per-frame and per-event records, audit |  |  |  |
| 126 | `skilled-action` | 3 | 3 | 0.00 | 0.33 | 0 | a024#0083: / anticipation / preparatory movement before primary action / research |  |  |  |
| 127 | `computer-vision` | 3 | 3 | 0.00 | 0.33 | 0 | a024#0087: / camera.intrinsics / optical/image-formation parameters / established |  |  |  |
| 128 | `re-identification` | 3 | 3 | 0.00 | 0.33 | 0 | a064#0059: show atomic state transitions for movement, grasp/release, wardrobe/we |  |  |  |
| 129 | `arm-length` | 3 | 3 | 0.00 | 0.33 | 0 | a031#2284: arm-length perspective; |  |  |  |
| 130 | `hard-code` | 3 | 3 | 0.00 | 0.33 | 0 | a068#0025: the cheapest reliable intervention is provider/task specific. cpcs sho |  |  |  |
| 131 | `lead-times` | 9 | 2 | 0.00 | 0.56 | 0 | a097#0009: / lpr-002 / l2 attention/gaze / what/how / saccade durations, eyes→hea |  |  |  |
| 132 | `large-scale` | 7 | 3 | 0.00 | 0.29 | 0 | a021#0047: [s030] haiyang liu et al. (2022), beat: a large-scale semantic and emo |  |  |  |
| 133 | `prompt-only` | 17 | 3 | 0.06 | 0.18 | 0 | a031#0963: a textual summary for prompt-only models; |  |  |  |
| 134 | `joint-limit` | 12 | 4 | 0.00 | 0.00 | 0 | a054#0649: joint-limit violations; |  |  |  |
| 135 | `movement-analysis` | 9 | 4 | 0.00 | 0.00 | 0 | a032#0805: the bridge is not another movement-analysis ontology. |  |  |  |
| 136 | `human-authored` | 8 | 4 | 0.00 | 0.00 | 0 | a031#1739: human-authored keyframe or motion-capture reference where available. |  |  |  |
| 137 | `text-to-motion` | 8 | 4 | 0.00 | 0.00 | 0 | a031#0614: text-to-motion diffusion; |  |  |  |
| 138 | `re-extraction` | 7 | 4 | 0.00 | 0.00 | 0 | a031#2356: re-extraction; |  |  |  |
| 139 | `medium-high` | 7 | 4 | 0.00 | 0.00 | 0 | a023#0042: / shape / medium-high / body volume/axes, but mode interpretation cont |  |  |  |
| 140 | `per-shot` | 6 | 3 | 0.17 | 0.00 | 0 | a005#0039: uniqueness: ordered structure with rich per-shot performance direction |  |  |  |
| 141 | `co-motion` | 6 | 2 | 0.00 | 0.00 | 1 | a038#0195: qualitative co-motion or relative motion; |  |  |  |
| 142 | `coordinate-frame` | 5 | 4 | 0.00 | 0.00 | 0 | a055#0006: coordinate-frame discipline; |  |  |  |
| 143 | `cross-subject` | 5 | 2 | 0.00 | 0.00 | 1 | a033#0061: cross-subject normalization; |  |  |  |
| 144 | `re-solving` | 5 | 4 | 0.00 | 0.00 | 0 | a054#0175: a root path should not be “corrected” independently after joint genera |  |  |  |
| 145 | `human-reviewed` | 4 | 3 | 0.00 | 0.25 | 0 | a104#0359: human-reviewed event frame. |  |  |  |
| 146 | `re-run` | 4 | 3 | 0.00 | 0.25 | 0 | a018#0032: scale: time- or amplitude-warp, then re-run contact, joint-limit, and  |  |  |  |
| 147 | `hard-cut` | 4 | 3 | 0.00 | 0.25 | 0 | a038#0309: encode ug-008 twice: the truthful hard-cut depiction and a separately  |  |  |  |
| 148 | `human-review` | 4 | 4 | 0.00 | 0.00 | 0 | a038#0307: what human-review rubric will promote this staged proposal into curate |  |  |  |
| 149 | `close-ups` | 4 | 3 | 0.00 | 0.25 | 0 | a086#0115: close-ups; |  |  |  |
| 150 | `joint-angle` | 4 | 3 | 0.00 | 0.25 | 0 | a020#0054: joint-angle margins; |  |  |  |
