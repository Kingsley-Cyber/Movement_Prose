-- Anime action directives, research snapshot 2026-10-20.
-- 64 authored prompt candidates; 8 per slot; all 6 moments in every slot.
-- No generation benchmark has been run. Sources and evidence limits: sources.json.
-- SQLite 3.24.0+ for ON CONFLICT DO UPDATE. No JSON extension needed to import.
-- Preserves the requested 8-column table. mechanical_guidance is JSON stored as TEXT.
-- Re-running refreshes these 64 aa_* IDs, including locally edited versions of them.
-- Other IDs are not updated or deleted. Use a copy of an existing DB to inspect a merge.
-- A single multi-row INSERT makes the seed content one statement-level operation.
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS semantic_directives (
    directive_id VARCHAR(64) PRIMARY KEY,
    archetype VARCHAR(32) NOT NULL,
    sub_genre VARCHAR(32) NOT NULL,
    slot_id VARCHAR(32) NOT NULL,
    moment_type VARCHAR(32) NOT NULL,
    prompt_snippet TEXT NOT NULL,
    negative_snippet TEXT NOT NULL,
    mechanical_guidance TEXT NOT NULL
);

INSERT INTO semantic_directives (
    directive_id, archetype, sub_genre, slot_id, moment_type, prompt_snippet, negative_snippet, mechanical_guidance
) VALUES
-- Readable loaded silhouette | subject_anchor | anticipation
(
    'aa_subject_loaded_silhouette',
    'anime_action',
    'grounded_martial_arts',
    'subject_anchor',
    'anticipation',
    'During the windup, keep {actor} recognizable by the same face, hair outline and costume panels. Separate both forearms from the torso in silhouette; draw taut diagonal folds across the loaded shoulder while the supporting foot remains visible.',
    'merged forearms, costume redesign, hair topology changes, detached sleeves',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Hold the readable preparation drawing for 4 editorial frames before release; this is an authored starting recipe.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Three-quarter full-body view; keep the supporting foot and striking arm visible.","preferred_route":"prompt_plus_reference","validation":"Compare face, hair and costume landmarks before and after the hold; both arm silhouettes stay legible.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Angular graphic pose | subject_anchor | execution
(
    'aa_subject_angular_pose',
    'anime_action',
    'shonen_impact',
    'subject_anchor',
    'execution',
    'On the decisive action drawing, construct {actor} from bold wedges: a triangular torso, a sharply bent leading elbow and a clean zigzag line of action. Keep the face and costume markings identifiable inside the angular silhouette.',
    'rounded clay anatomy, melted elbows, changing costume symbols, plush surface shading',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Use one emphatic action drawing between readable entry and exit drawings; its hold is set by the beat.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Use a three-quarter view that separates the elbow from the ribcage.","preferred_route":"prompt_plus_reference","validation":"The pose reads as one actor with connected joints and the same costume after the exaggeration.","conflicts_with":[],"sources":["I_TRIGGER","P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Bounded impact deformation | subject_anchor | impact
(
    'aa_subject_elastic_contact',
    'anime_action',
    'shonen_impact',
    'subject_anchor',
    'impact',
    'At the contact beat, compress {target}''s torso into a short graphic curve and stretch the far contour with the force direction. Preserve the connected neck, shoulders, pelvis and limb roots, then restore the established body design on the next readable pose.',
    'detached pelvis, permanent stretched torso, duplicated shoulders, disconnected neck',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Limit the deformation to 1 or 2 editorial frames; restore the model in the recoil pose.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Hold a side or three-quarter view so the deformation follows the visible incoming force.","preferred_route":"pose_reference_or_post","validation":"Check joint connectivity on the effect drawing and restored proportions immediately afterward.","conflicts_with":[],"sources":["I_OHIRA","P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Recoil identity anchor | subject_anchor | recoil
(
    'aa_subject_recoil_identity',
    'anime_action',
    'cyberpunk_cqc',
    'subject_anchor',
    'recoil',
    'As {target} recoils, preserve the same jaw contour, hair clumps, glove shape and jacket seam map. Keep the struck shoulder joined to the chest and the elbow visibly connected to its forearm throughout the backward bend.',
    'face substitution, shoulder separation, fused glove and sleeve, mirrored costume panels',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Use readable recoil keys; maintain landmarks on every held or passing drawing.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep the struck side visible; avoid a simultaneous orbit through the contact axis.","preferred_route":"prompt_plus_reference","validation":"Track the same shoulder, elbow, glove and three face landmarks through the recoil.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Stable costume attachment points | subject_anchor | follow_through
(
    'aa_subject_costume_attachment',
    'anime_action',
    'grounded_martial_arts',
    'subject_anchor',
    'follow_through',
    'During {actor}''s follow-through, keep the belt fixed to the waist, cuffs fixed to the wrists and collar fixed to the neck. Preserve the same garment panel boundaries while the torso turns; the fabric remains a distinct layer over the body.',
    'sliding belt, migrating cuffs, collar fused into skin, costume panel swaps',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Carry the attachment landmarks continuously across the follow-through keys.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Use enough medium-wide space to see waist and wrists.","preferred_route":"prompt_plus_reference","validation":"Inspect belt, collar and cuff attachment points through the body rotation.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Restore the model after exaggeration | subject_anchor | recovery
(
    'aa_subject_recovery_model',
    'anime_action',
    'grounded_martial_arts',
    'subject_anchor',
    'recovery',
    'In the recovery pose, return {actor} to the established face proportions, hand size and full body silhouette. Keep the same hairstyle, costume damage and left-right markings; the final readable pose matches the character established before the exchange.',
    'residual stretched limbs, reset costume damage, swapped left-right markings, new hairstyle',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Hold a restored key for 4 editorial frames, with any breathing authored separately.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Finish at a view that exposes the face, hands and stance.","preferred_route":"prompt_plus_reference","validation":"Compare the recovery key to the pre-action reference while preserving newly caused damage.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Extreme foreshortened fist | subject_anchor | execution
(
    'aa_subject_foreshortened_fist',
    'anime_action',
    'shonen_impact',
    'subject_anchor',
    'execution',
    'As {actor}''s punch approaches the viewpoint, enlarge the near fist dramatically while the forearm tapers back to the same connected elbow. Keep the far shoulder and torso readable behind it; the hand keeps its original glove design and one coherent knuckle silhouette.',
    'detached floating fist, swollen glove after the punch, additional forearms, finger knots',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Use 1 or 2 strongly foreshortened drawings bracketed by readable anatomy.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Use a deliberate near-lens strike view; resolve to a normal-scale key after passage.","preferred_route":"pose_reference_or_post","validation":"Trace fist-to-elbow-to-shoulder continuity and verify apparent scale returns with depth.","conflicts_with":[],"sources":["I_KANADA","P_LENS"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Transient multiple-contour smear | subject_anchor | execution
(
    'aa_subject_multiple_limb_smear',
    'anime_action',
    'supernatural_speed',
    'subject_anchor',
    'execution',
    'For one transition drawing of {actor}''s rapid strike, show the leading arm plus two faint drawn contour echoes along its previous arc. All echoes belong to that same moving arm; the next clean drawing contains the original two arms and one unchanged face.',
    'persistent extra arms, detached limb copies, duplicated faces, permanent ghost bodies',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Use a single editorial smear drawing; clear every contour echo on the next clean key.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep a fixed readable action plane; avoid overlapping the echoes with the opponent''s face.","preferred_route":"post_or_drawn_reference","validation":"Count real limbs before and after the smear; check that echoes disappear immediately.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Quiet ground before release | environment | anticipation
(
    'aa_env_preimpact_quiet',
    'anime_action',
    'grounded_martial_arts',
    'environment',
    'anticipation',
    'Before the release, preserve the courtyard floor in its established state, keeping pre-existing cracks, tile boundaries and loose stones fixed. Leave a clear patch of ground beneath {actor}''s support foot so the upcoming displacement has a stable visual reference.',
    'premature explosion, drifting floor texture, moving horizon, floating support stones',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"environment_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Keep the environment unchanged throughout the anticipation interval.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Preserve a stable floor landmark in the frame.","preferred_route":"prompt_plus_reference","validation":"Verify no damage or airborne debris appears before the triggering contact.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Directional speed background | environment | execution
(
    'aa_env_speed_void',
    'anime_action',
    'supernatural_speed',
    'environment',
    'execution',
    'During the dash only, replace distant scenery with flat parallel streaks along the travel axis, sweeping opposite {actor}''s screen travel. Keep the immediate ground plane and contact shadows readable; restore the established distant scenery when the dash finishes.',
    'randomly oriented streaks, streaks painted over the face, permanent missing scenery, tunnel of smoke',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"background_layers_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Bound the speed background to the travel interval; return on the arrival key.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Maintain the same screen travel direction across entry and exit.","preferred_route":"post_or_reference","validation":"Confirm streak direction opposes travel and the environment returns to the same location.","conflicts_with":["aa_env_layered_parallax"],"sources":["P_SPEED_LINES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Contact-origin ground fracture | environment | impact
(
    'aa_env_radial_fracture',
    'anime_action',
    'shonen_impact',
    'environment',
    'impact',
    'At {contact_origin}, split the struck stone surface into a few sharp radial cracks that originate at the exact contact point. The crack network expands outward while the surrounding undamaged floor retains its original perspective and texture.',
    'cracks before contact, fracture on the wrong surface, liquid stone, entire ground melting',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"contact_surface_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Start the first visible crack on the contact frame; enlarge it only afterward.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep the contact point and first crack junction visible.","preferred_route":"contact_reference_or_post","validation":"Check that damage begins at the contact anchor and never precedes it.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":["contact_event_on_solid_surface"],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Cubic debris fan | environment | recoil
(
    'aa_env_yutapon_cubes',
    'anime_action',
    'shonen_impact',
    'environment',
    'recoil',
    'After the surface breaks, eject a limited cluster of angular cuboid stone fragments from {contact_origin}. Show flat faces and crisp corners; larger blocks follow readable outward arcs while a few smaller chips trail behind. The debris remains separate from both fighters.',
    'rounded gravel soup, liquid rubble, endless multiplying cubes, fighter converted into blocks',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"debris_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Begin after contact; stagger fragment motion across the recoil interval.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Use a side or three-quarter view with negative space around the debris fan.","preferred_route":"reference_or_post","validation":"Trace every major block back to the damaged surface; check stable shape and finite count.","conflicts_with":[],"sources":["I_NAKAMURA"],"requires":["surface_fracture_event"],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Layered dust billow | environment | follow_through
(
    'aa_env_layered_dust',
    'anime_action',
    'shonen_impact',
    'environment',
    'follow_through',
    'From the damaged ground, roll a low dust front outward in distinct flat lobes while a softer upper plume rises behind it. Keep a readable opening around the fighters'' silhouettes; the dust follows the debris event and gradually loses density.',
    'opaque full-screen fog, dust before impact, boiling liquid ground, smoke attached to the face',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"environment_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Start after the fracture; let the heavier front slow before the upper plume disperses.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep the dust source and at least one fighter outline visible.","preferred_route":"reference_or_post","validation":"Check source continuity, silhouette visibility and decreasing density after the burst.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":["surface_fracture_event"],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Persistent debris and damage | environment | recovery
(
    'aa_env_debris_settle',
    'anime_action',
    'shonen_impact',
    'environment',
    'recovery',
    'As the exchange settles, keep the new crater, cracks and fallen blocks in their established positions. Let only the last few small chips bounce to rest; the thinning dust reveals the same damaged ground beneath the recovering fighters.',
    'restored pristine ground, disappearing blocks, new unexplained crater, perpetual dust eruption',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"environment_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Use diminishing chip bounces, then a stable environmental hold.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Retain visible damage landmarks into the closing view.","preferred_route":"prompt_plus_reference","validation":"Match crater and large-block positions between recoil and recovery.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":["established_damage_state"],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Depth-separated background parallax | environment | execution
(
    'aa_env_layered_parallax',
    'anime_action',
    'mecha_aerobatics',
    'environment',
    'execution',
    'During the lateral pursuit, move nearby structural beams fastest across the frame, the middle-distance buildings more slowly and the distant skyline slowest. Preserve each layer''s shape and the same horizon while {actor} remains clearly separated from the background.',
    'all layers sliding at one speed, bending buildings, moving horizon independent of camera, liquid scenery',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"background_layers_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Maintain consistent parallax through the whole tracked interval; no cadence reset midshot.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Pair with a single lateral tracking move; keep the background depth order fixed.","preferred_route":"prompt_plus_reference","validation":"Compare landmark screen displacement across foreground, midground and background.","conflicts_with":["aa_env_speed_void"],"sources":["P_CAMERA","I_ITANO"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Grounded skid gouge | environment | recoil
(
    'aa_env_skid_gouge',
    'anime_action',
    'grounded_martial_arts',
    'environment',
    'recoil',
    'As {target} slides backward, carve a narrow continuous gouge directly beneath the contacting heel. Push small chips outward along the two edges of the track; the groove begins at the landing point and ends where the foot stops.',
    'groove ahead of the foot, floating skid, disconnected track, shoe fused into stone',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Extend the track only while the heel moves in contact with the ground.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Use a low three-quarter view that shows the contacting heel and the track behind it.","preferred_route":"contact_reference_or_post","validation":"Track heel contact and groove endpoint on each sampled frame.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":["heel_ground_contact_interval"],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Load the support before striking | primary_action | anticipation
(
    'aa_action_weight_load',
    'anime_action',
    'grounded_martial_arts',
    'primary_action',
    'anticipation',
    'Before striking, {actor} lowers the pelvis over the rear support leg, bends the rear knee and draws the striking elbow back. The chest turns slightly away from {target}; the rear foot keeps firm ground contact until the forward drive begins.',
    'floating planted foot, sliding support heel, knee bending backward, strike before weight load',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Use a compact loading interval followed by a 4-frame held key; customize to the shot.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Frame both feet and the loaded hip in a three-quarter full-body view.","preferred_route":"prompt_plus_reference","validation":"Verify support contact and visible load before forward travel.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Hip-led straight punch | primary_action | execution
(
    'aa_action_hip_led_punch',
    'anime_action',
    'grounded_martial_arts',
    'primary_action',
    'execution',
    '{actor} drives from the rear foot and rotates the pelvis toward {target}; the shoulder follows, then the fist extends along one clear path. Keep the opposite hand near the face and finish the strike without locking the elbow backward.',
    'arm detached from torso, reversed elbow, fist teleporting between poses, support foot skating',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Use closer pose spacing at launch and wider spacing toward contact; timing is authored.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Use a three-quarter or side view to show hip-to-shoulder sequencing.","preferred_route":"prompt_plus_reference","validation":"Observe ordered pelvis, shoulder and fist motion with a continuous fist path.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Readable forearm block | primary_action | impact
(
    'aa_action_forearm_block',
    'anime_action',
    'cyberpunk_cqc',
    'primary_action',
    'impact',
    'At the contact beat, {target} meets {actor}''s incoming forearm with the outside of one raised forearm. Show the two distinct limbs touching at one visible point; the defender''s elbow remains bent and both torsos stay separated.',
    'merged fighters, fused forearms, contact across empty space, palm passing through wrist',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"actor_target_contact","editorial_timeline_fps":24,"editorial_recipe":"Align contact and any effect to the same editorial frame; hold 2 frames only if the shot uses hit-stop.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep the contact point unobscured in a side or three-quarter medium-wide view.","preferred_route":"contact_reference_or_post","validation":"Verify the same two named limbs meet at one contact and separate afterward.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Absorb force with a recovery step | primary_action | recoil
(
    'aa_action_absorb_recoil',
    'anime_action',
    'grounded_martial_arts',
    'primary_action',
    'recoil',
    'After contact, {target}''s struck shoulder moves backward first; the torso follows and one foot steps behind to catch the weight. Keep the other foot as a temporary pivot, then settle the pelvis over the widened stance.',
    'reaction before contact, sliding both feet, backward knee, torso moving without the struck shoulder',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Start recoil after contact; author the catch step before the body reaches its final position.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep both feet and the struck shoulder visible.","preferred_route":"prompt_plus_reference","validation":"Confirm impact precedes recoil and the new support foot lands before the final settle.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Continuous strike follow-through | primary_action | follow_through
(
    'aa_action_followthrough_arc',
    'anime_action',
    'grounded_martial_arts',
    'primary_action',
    'follow_through',
    'After the strike reaches its contact or authored miss point, {actor}''s shoulder and torso continue a short distance along the established arc. The arm decelerates with the body turn while the support foot pivots; the motion finishes before the guard is rebuilt.',
    'instant pose reset, reversed follow-through, elbow hyperextension, pivot foot sliding sideways',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Use progressively tighter spacing as the motion decelerates; overlap defender recoil if required.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Preserve the action side and show the pivoting support foot when possible.","preferred_route":"prompt_plus_reference","validation":"Check that the post-contact path continues the incoming direction before slowing.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Return to balanced guard | primary_action | recovery
(
    'aa_action_guard_recovery',
    'anime_action',
    'grounded_martial_arts',
    'primary_action',
    'recovery',
    'After the motion has finished, {actor} brings the striking hand back toward the face, squares the stance toward {target} and settles the pelvis between the supporting feet. Finish in a stable guard with a small visible breath.',
    'instant teleport to idle, endlessly repeated punch, floating feet, frozen distorted hand',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Reserve a real recovery interval after follow-through rather than extending the attack key.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Use a medium-wide view that shows stance and guard.","preferred_route":"prompt_plus_reference","validation":"Confirm the hand returns by a visible path and both feet support the final stance.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Discrete vanish and arrival | primary_action | execution
(
    'aa_action_flash_step',
    'anime_action',
    'supernatural_speed',
    'primary_action',
    'execution',
    'In a fixed view, {actor} launches from the marked starting point, vanishes for a brief interval and reappears at the marked destination facing {target}. Preserve the same body, costume and travel direction; one clear departure pose precedes one clear arrival pose.',
    'persistent duplicate fighter, multiple simultaneous arrivals, costume replacement, unintended crossfade',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Author departure, absence and arrival as separate editorial states; 2/1/2 frames is only a trial recipe.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Lock the camera and keep both departure and arrival positions in frame.","preferred_route":"post_or_keyframe_sequence","validation":"Count one actor before and after; confirm destination and facing match the plan.","conflicts_with":["aa_camera_lateral_track","aa_camera_falling_track","aa_camera_whip_reacquire","aa_camera_crash_zoom"],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Mecha evasion among converging missiles | primary_action | execution
(
    'aa_action_itano_evasion',
    'anime_action',
    'mecha_aerobatics',
    'primary_action',
    'execution',
    '{actor} banks across the frame and rolls through a clear gap between incoming missile paths. Keep the fuselage or torso orientation continuous as the missiles curve past; preserve one readable evasion trajectory instead of unrelated spins.',
    'teleporting vehicle, disconnected wings, random tumbling, missiles passing through the body',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Resolve rapid near-camera passes with distinct poses; do not impose global twos.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Plan one continuous chase view; retain a horizon or other depth reference at entry.","preferred_route":"trajectory_reference_or_post","validation":"Trace actor orientation and each near-miss path through the chosen gap.","conflicts_with":[],"sources":["I_ITANO"],"requires":["authored_actor_path","distinct_missile_paths"],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Cloth lags the loading motion | secondary_motion | anticipation
(
    'aa_secondary_cloth_lag',
    'anime_action',
    'grounded_martial_arts',
    'secondary_motion',
    'anticipation',
    'As {actor} draws back into the windup, the loose jacket hem initially lags behind the torso, then catches up in a small fold. Keep the collar and cuffs attached; the fabric movement remains subordinate to the loaded body pose.',
    'cloth moving before the body, detached jacket, endless flag flapping, fabric fused with hands',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Delay the hem response by an authored 2-frame offset from the torso key.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep the hem separate from the legs in silhouette.","preferred_route":"prompt_plus_reference","validation":"Compare torso and hem motion starts; check fixed attachment points.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Hair clump snap and lag | secondary_motion | execution
(
    'aa_secondary_hair_snap',
    'anime_action',
    'supernatural_speed',
    'secondary_motion',
    'execution',
    'As {actor} accelerates, the existing hair clumps trail opposite the head''s motion, then snap toward their resting shape when the head changes speed. Keep the same clump count and scalp attachment throughout the action.',
    'new hair strands growing, detached wig, hair fused into speed lines, scalp sliding',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Offset hair response after head acceleration; resolve the clumps on clean keys.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Use enough silhouette separation to distinguish hair from the background.","preferred_route":"prompt_plus_reference","validation":"Track scalp anchors and the direction of lag relative to head travel.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Contact-centered shock ring | secondary_motion | impact
(
    'aa_secondary_contact_ring',
    'anime_action',
    'shonen_impact',
    'secondary_motion',
    'impact',
    'At the instant of contact, emit one thin drawn shock ring from {contact_origin}. Expand it outward across the local contact plane, tapering its line weight as it grows; the ring fades before the next major action and remains separate from the fighters.',
    'persistent halo, ring around the wrong fighter, multiple unplanned rings, opaque energy disc',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"contact_effect","editorial_timeline_fps":24,"editorial_recipe":"Trigger on contact; expand over an authored 3-to-6-frame editorial interval.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep the origin visible and use an angle that shows the ring''s planar ellipse.","preferred_route":"post_effect","validation":"Verify exact origin, a single ring and a finite fade-out.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Cape overshoot after body reversal | secondary_motion | recoil
(
    'aa_secondary_cape_overshoot',
    'anime_action',
    'shonen_impact',
    'secondary_motion',
    'recoil',
    'When {target}''s torso reverses under the hit, the cape continues briefly along its previous path, then folds around the new body direction. Keep the shoulder fasteners fixed and the cape behind the limbs rather than swallowing their silhouettes.',
    'cape welded to hands, detached shoulder fasteners, cloth reversing before impact, opaque body-covering sheet',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Let the cape reverse after the torso; reduce amplitude as the recoil ends.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Show the shoulders and free edge of the cape.","preferred_route":"prompt_plus_reference","validation":"Observe the torso reversal before the free cape edge reverses.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Blade-attached tapering contrail | secondary_motion | follow_through
(
    'aa_secondary_weapon_contrail',
    'anime_action',
    'cyberpunk_cqc',
    'secondary_motion',
    'follow_through',
    'As {actor}''s blade finishes its swing, leave a thin curved ribbon following the blade tip''s recent path. The ribbon is widest nearest the moving tip and fades along its older end; the physical blade stays single, rigid and attached to the gripping hand.',
    'duplicate solid blades, trail disconnected from weapon, glowing ribbon through the face, hand fused to hilt',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Keep the trail short and decay it after the blade slows; do not persist into recovery.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Show the blade arc in a side or three-quarter view with clear space behind it.","preferred_route":"trajectory_reference_or_post","validation":"Trace the ribbon head to the blade tip and verify one physical weapon.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Damped cloth settle | secondary_motion | recovery
(
    'aa_secondary_cloth_settle',
    'anime_action',
    'grounded_martial_arts',
    'secondary_motion',
    'recovery',
    'As {actor} reaches the recovered stance, let the jacket hem make one small overshoot and a smaller return before resting. Keep the shoulders and cuffs fixed; the cloth settles while the body maintains a quiet breathing pose.',
    'endless cloth flutter, floating sleeve anchors, garment snapping to a new design, repeated large cape waves',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Use decreasing displacement on successive settle keys; exact duration is shot-dependent.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep the free fabric edge in frame through the settle.","preferred_route":"prompt_plus_reference","validation":"Check that the last fabric excursion is smaller than the previous one.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Graphic flame-dragon contour | secondary_motion | execution
(
    'aa_secondary_kanada_flame_dragon',
    'anime_action',
    'supernatural_speed',
    'secondary_motion',
    'execution',
    'Along the authored attack path, curl the flame effect into a long angular dragon-like silhouette with a pointed head and tapering tail. Build it from flat interlocking tongues of color and sharp contour breaks, keeping it a drawn energy effect separate from the attacker.',
    'realistic scaled animal, volumetric smoke creature, flame fused into actor, permanent solid dragon',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Shape successive effect keys along a clear arc; hold the recognizable head briefly.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Use a wide three-quarter view that reveals the head-to-tail gesture.","preferred_route":"drawn_reference_or_post","validation":"Verify the flame remains an effect and the body does not transform into a creature.","conflicts_with":[],"sources":["I_TRIGGER"],"requires":["authored_attack_path"],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Angular contact star | secondary_motion | impact
(
    'aa_secondary_angular_impact_star',
    'anime_action',
    'shonen_impact',
    'secondary_motion',
    'impact',
    'On contact, place a sharp asymmetrical starburst exactly at {contact_origin}. Use a few long tapered spikes aligned with the force direction and shorter cross-spikes; the graphic burst clears immediately so both contacting limbs remain readable afterward.',
    'persistent star object, burst before contact, full-screen opaque explosion, rounded jelly splat',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"contact_effect","editorial_timeline_fps":24,"editorial_recipe":"Limit the star to 1 or 2 editorial frames, then clear it.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep the burst centered on visible contact rather than the middle of the frame.","preferred_route":"post_effect","validation":"Check onset against contact and verify limbs are visible again on the next clean key.","conflicts_with":[],"sources":["I_FAURE"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Tension hold then burst | temporal_cadence | anticipation
(
    'aa_time_hold_then_burst',
    'anime_action',
    'shonen_impact',
    'temporal_cadence',
    'anticipation',
    'Let the preparation pose register as a deliberate still hold, then release into a sudden short acceleration. The pause belongs before movement; preserve a clear contrast between restrained anticipation and fast execution.',
    'uniform motion speed, constant slow motion, interpolated drift during the hold, repeated micro-windups',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Trial recipe at 24 editorial fps: 4-frame anticipation hold, then 2-frame launch transition; adapt to readability.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep the camera quiet during the tension hold.","preferred_route":"editorial_exposure_control","validation":"Measure the held-pose duration and verify the launch follows it without crossfading.","conflicts_with":[],"sources":["P_TIMING","P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Selective ones within twos | temporal_cadence | execution
(
    'aa_time_mixed_exposures',
    'anime_action',
    'shonen_impact',
    'temporal_cadence',
    'execution',
    'Use clearly held drawings through the readable poses, then use a brief run of distinct fast-transition drawings during the strike. Return to held drawings once the action resolves; preserve the intentional difference in drawing cadence.',
    'uniform optical-flow smoothing, blended in-between frames, identical cadence across every phase, motionless strike',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"At 24 editorial fps, hold selected character drawings for 2 frames; use 1-frame drawings only at chosen fast transitions.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep camera motion independent from character exposure changes.","preferred_route":"editorial_exposure_control","validation":"Inspect character exposures frame by frame; do not infer twos from export fps alone.","conflicts_with":[],"sources":["P_TIMING","P_RETIME"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Brief contact hit-stop | temporal_cadence | impact
(
    'aa_time_contact_hitstop',
    'anime_action',
    'shonen_impact',
    'temporal_cadence',
    'impact',
    'Pause the contacting fighters on the clearest contact drawing for a brief beat, then release into recoil and follow-through. Keep their relative contact position fixed during the pause; secondary effects may continue only if separately authored.',
    'recoil before touch, prolonged frozen clip, blended contact frames, continued fist penetration during pause',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"actor_target_contact","editorial_timeline_fps":24,"editorial_recipe":"Trial recipe: hold the contact drawing for 2 frames on a 24fps editorial timeline; generation text alone is insufficient.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Lock the camera through the contact hold unless camera shake is a separate planned overlay.","preferred_route":"editorial_exposure_control","validation":"Confirm contact is established before the hold and motion resumes afterward.","conflicts_with":["aa_camera_crash_zoom"],"sources":["P_TIMING"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Fast displacement then controlled catch | temporal_cadence | recoil
(
    'aa_time_recoil_spacing',
    'anime_action',
    'grounded_martial_arts',
    'temporal_cadence',
    'recoil',
    'Make {target}''s first recoil displacement brisk, followed by progressively smaller changes as the recovering foot catches the body. Preserve the visible order of hit, backward motion, support step and deceleration.',
    'constant-speed sliding, reaction before impact, sudden end freeze, repeated backward bounces',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Author wide position spacing immediately after impact, tightening spacing toward the support catch.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep a stable framing reference so changes in displacement remain visible.","preferred_route":"pose_reference_or_retime","validation":"Plot the struck shoulder''s screen displacement and check it reduces during the catch.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Staggered follow-through timing | temporal_cadence | follow_through
(
    'aa_time_overlap_offsets',
    'anime_action',
    'shonen_impact',
    'temporal_cadence',
    'follow_through',
    'Let {actor}''s torso finish before the loose hair and cloth complete their trailing motion. Offset the secondary peaks so the body turn, hair snap and fabric settle do not all stop on the same drawing.',
    'all parts freezing simultaneously, cloth leading the torso, unrelated repeated oscillation',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Trial offsets at 24 editorial fps: torso finish at t, hair peak at t+1, fabric peak at t+2; adjust to material and shot.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep the relevant torso and free fabric edges visible.","preferred_route":"reference_or_layered_post","validation":"Compare peak times rather than assigning one global end time to every moving part.","conflicts_with":[],"sources":["P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Quiet moving hold | temporal_cadence | recovery
(
    'aa_time_moving_hold',
    'anime_action',
    'grounded_martial_arts',
    'temporal_cadence',
    'recovery',
    'Finish with a readable recovered pose held long enough to register, while a small chest breath and a final cloth settle preserve life. Keep the gesture and center of balance stable during these subtle changes.',
    'total mannequin freeze, large idle sway, looping attack restart, drifting feet',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Trial recipe: 6-to-12-frame closing hold with separately authored subtle motion; do not repeatedly interpolate the whole body.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Settle the camera before the final hold.","preferred_route":"reference_or_editorial_hold","validation":"Check stable feet and gesture while only the planned breathing and cloth channels move.","conflicts_with":[],"sources":["P_TIMING","P_PRINCIPLES"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Depth-dependent missile cadence | temporal_cadence | execution
(
    'aa_time_itano_depth',
    'anime_action',
    'mecha_aerobatics',
    'temporal_cadence',
    'execution',
    'Give the nearest fast missiles the most continuous visible motion; let more distant missile groups use broader held spacing. As a missile approaches the viewpoint, its cadence becomes more continuous while its path remains easy to trace.',
    'identical stutter in every depth layer, missile teleportation, fused trails, near-camera motion frozen on long holds',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Itano describes near missiles on ones, middle on twos, far on threes, with depth transitions; translate into explicit layered exposure control.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"For missile-following pans, prioritize continuous camera-relative motion.","preferred_route":"layered_editorial_exposure_control","validation":"Inspect near, middle and far layers separately and track cadence changes with depth.","conflicts_with":[],"sources":["I_ITANO"],"requires":["distinct_missile_paths","depth_layer_assignments"],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Stepped pose snapping | temporal_cadence | execution
(
    'aa_time_pose_snapping',
    'anime_action',
    'shonen_impact',
    'temporal_cadence',
    'execution',
    'Move through a small set of strongly differentiated action poses with decisive transitions. Let each silhouette read briefly, then snap to the next authored pose; preserve a continuous overall attack direction across the sharp changes.',
    'soft morph between silhouettes, random jump cuts, unrelated pose order, uniform floaty easing',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Trial recipe: 2-frame pose, 1-frame transition, 2-frame pose; authored keys are required for exact timing.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep a consistent action axis so pose changes read as movement rather than shot changes.","preferred_route":"editorial_exposure_control","validation":"Check pose order and direction while confirming no blended intermediate is inserted.","conflicts_with":[],"sources":["P_TIMING","I_KANADA"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Low-angle restrained Dutch view | camera_optics | anticipation
(
    'aa_camera_low_tilt',
    'anime_action',
    'shonen_impact',
    'camera_optics',
    'anticipation',
    'Frame the loaded fighter from slightly below waist height in a three-quarter full-body view, with a modest diagonal horizon. Keep the face, striking arm and both feet inside the frame; maintain this composition during the windup.',
    'uncontrolled rolling horizon, cropped support feet, extreme facial stretch, constant orbit',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Establish the tilt before the anticipation and hold it through the tension beat.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"One low-angle composition; no simultaneous pan or crash zoom during the hold.","preferred_route":"prompt_plus_reference","validation":"Check that all required body landmarks remain inside the image.","conflicts_with":[],"sources":["P_CAMERA","P_LENS"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Lateral action tracking | camera_optics | execution
(
    'aa_camera_lateral_track',
    'anime_action',
    'cyberpunk_cqc',
    'camera_optics',
    'execution',
    'Track sideways with {actor} at a steady relative distance, keeping the leading hand and intended contact area inside a medium-wide frame. Let the background move laterally while the action axis and the fighters'' left-right order remain clear.',
    'unmotivated orbit, axis crossing, subject slipping out of frame, camera pulling away from contact',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Begin tracking before the fastest movement and avoid a new camera acceleration at contact.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Use one lateral tracking path; preserve screen direction.","preferred_route":"prompt_plus_reference","validation":"Measure actor framing and verify the contact area never leaves the frame.","conflicts_with":[],"sources":["P_CAMERA"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Contact readability lock | camera_optics | impact
(
    'aa_camera_contact_lock',
    'anime_action',
    'grounded_martial_arts',
    'camera_optics',
    'impact',
    'Hold a stable side or three-quarter medium-wide camera at the contact beat. Keep both contacting limbs, the defender''s torso and enough ground for balance in view; give the exact touch point a clear silhouette against the background.',
    'whip pan across impact, hidden contact point, cropped hands, sudden lens change',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"actor_target_contact","editorial_timeline_fps":24,"editorial_recipe":"Reserve a stable window around contact; an exact duration belongs to the editorial plan.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Lock framing across entry, contact and first separation.","preferred_route":"prompt_plus_reference","validation":"Verify the touch and first separation can be seen without inferring them from a flash.","conflicts_with":["aa_camera_crash_zoom"],"sources":["P_CAMERA"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Synchronous falling-subject track | camera_optics | recoil
(
    'aa_camera_falling_track',
    'anime_action',
    'mecha_aerobatics',
    'camera_optics',
    'recoil',
    'Descend with the falling {target}, keeping a stable relative framing while the surrounding structure rises through the image. Preserve the target''s orientation changes and a consistent world-down direction; leave space below for the planned landing.',
    'reversed gravity, camera and body falling at unrelated rates, target leaving frame, random horizon spins',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Keep camera velocity coordinated with the fall; change it only for the planned landing reveal.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Choose a downward tracking path with a visible environmental depth reference.","preferred_route":"camera_reference_or_post","validation":"Track target screen position and verify scenery motion is consistent with descent.","conflicts_with":[],"sources":["P_CAMERA","I_ITANO"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Whip pan with a readable destination | camera_optics | follow_through
(
    'aa_camera_whip_reacquire',
    'anime_action',
    'cyberpunk_cqc',
    'camera_optics',
    'follow_through',
    'After the initial action is readable, whip the camera along its established direction, briefly reducing the background to streaks aligned with the pan direction. End on the planned destination and hold a clean frame of {target}; keep the arrival view on the same action side.',
    'endless camera spin, lost destination, axis reversal, all-frame blur',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Trial transition: 2-to-4 editorial pan frames followed by a clear destination hold.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Specify start view, pan direction and settled end view; do not place critical contact inside the blur.","preferred_route":"camera_reference_or_post","validation":"Verify both start and destination views, and that no required contact is hidden in transit.","conflicts_with":[],"sources":["P_CAMERA","P_RETIME"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Decelerate into a settled frame | camera_optics | recovery
(
    'aa_camera_recovery_settle',
    'anime_action',
    'grounded_martial_arts',
    'camera_optics',
    'recovery',
    'Ease the camera to a complete stop as {actor} completes recovery, ending in a medium-wide composition that shows the guard and supporting feet. Keep the final horizon and subject size stable during the closing hold.',
    'endless drift, unwanted zoom, horizon wobble, cropped final stance',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Finish camera deceleration before the final held pose is evaluated.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"End on an explicit stationary framing target.","preferred_route":"prompt_plus_reference","validation":"Compare horizon and subject scale over the closing frames.","conflicts_with":[],"sources":["P_CAMERA"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Barrel-distorted incoming-strike view | camera_optics | execution
(
    'aa_camera_incoming_wide',
    'anime_action',
    'shonen_impact',
    'camera_optics',
    'execution',
    'Place the viewpoint close to the incoming strike so the near fist dominates the foreground and the connected arm recedes steeply toward the torso. Add deliberate barrel curvature near the frame edges while keeping the contact path and central face readable.',
    'severed foreground hand, rubber room deformation, permanent body enlargement, random lens breathing',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Limit the strongest distortion to the near pass, then restore the chosen baseline view.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"This record deliberately combines near-camera perspective with barrel distortion; use a lens reference for both effects.","preferred_route":"lens_reference_or_post","validation":"Check connected anatomy, stable central subject and consistent curvature at the edges.","conflicts_with":[],"sources":["P_LENS"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Crash zoom onto a contact | camera_optics | impact
(
    'aa_camera_crash_zoom',
    'anime_action',
    'shonen_impact',
    'camera_optics',
    'impact',
    'Once the contact point is established, rapidly tighten the framing toward it, then stop at a readable close view. Keep the zoom centered on that same point; preserve the original viewing direction and the distinct boundaries of both contacting limbs.',
    'dolly through bodies, contact outside frame, endless zoom, merged hands at close range',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"actor_target_contact","editorial_timeline_fps":24,"editorial_recipe":"Trial recipe: a 2-to-4-frame editorial zoom following established contact; exact crop is a post task.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Choose an optical-style zoom or a post crop; do not combine with a contact-lock directive in the same interval.","preferred_route":"post_camera_transform","validation":"Check the zoom center and final limb separation frame by frame.","conflicts_with":["aa_camera_contact_lock"],"sources":["P_LENS","P_CAMERA"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Hard graphic key shadow | lighting | anticipation
(
    'aa_light_hard_shadow',
    'anime_action',
    'cyberpunk_cqc',
    'lighting',
    'anticipation',
    'During the preparation, illuminate {actor} from one fixed side and place a crisp, unsoftened shadow shape across the opposite cheek and torso. Keep the lit and shadow regions stable as the pose holds, preserving readable eyes and costume edges.',
    'soft airbrushed face gradient, migrating light source, glossy plastic highlights, flickering shadow boundaries',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Maintain one light direction throughout the held preparation.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep the key-light side readable in the chosen three-quarter view.","preferred_route":"prompt_plus_reference","validation":"Compare cheek and torso shadow direction across the hold.","conflicts_with":["aa_light_kagenashi"],"sources":["P_LIGHTING"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Thin rim separating fast silhouettes | lighting | execution
(
    'aa_light_thin_rim',
    'anime_action',
    'mecha_aerobatics',
    'lighting',
    'execution',
    'Use a narrow bright rim along the side of {actor} facing the fixed backlight, separating the moving silhouette from the dark background. Keep the interior colors flat; the rim follows visible edges instead of filling the body with glow.',
    'full-body neon fill, blooming outline hiding limbs, rim on every unrelated edge, glossy bevels',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Maintain rim direction during travel; avoid random per-frame light changes.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep silhouette edges distinct from bright background effects.","preferred_route":"prompt_plus_reference","validation":"Check rim placement against the declared backlight and preserved limb boundaries.","conflicts_with":[],"sources":["P_LIGHTING"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Backlight silhouette flash | lighting | impact
(
    'aa_light_silhouette_flash',
    'anime_action',
    'supernatural_speed',
    'lighting',
    'impact',
    'At contact, a brief light from behind the fighters turns their visible fronts into clean dark silhouettes while preserving the gap between their heads and limbs. Return to the established scene lighting immediately after the flash.',
    'silhouette remaining after impact, fused black body mass, repeated strobe, erased limb gaps',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"contact_light_event","editorial_timeline_fps":24,"editorial_recipe":"Use one authored 1-to-2-frame illumination event; restore baseline on the next clean key.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Choose a view where both silhouettes and the contact point remain distinguishable.","preferred_route":"post_lighting_or_composite","validation":"Check flash onset, silhouette separation and full lighting restoration.","conflicts_with":[],"sources":["P_LIGHTING"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Contact-light falloff | lighting | recoil
(
    'aa_light_recoil_falloff',
    'anime_action',
    'supernatural_speed',
    'lighting',
    'recoil',
    'As {target} recoils away from the brief contact light, reduce that light''s contribution on the retreating side of the face and jacket. Keep the original scene key intact; the transient illumination fades without changing the material colors.',
    'new permanent palette, unrelated pulsing lights, total scene blackout, glow attached to skin',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Begin falloff after the flash and restore baseline by the end of recoil.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Preserve the spatial relationship between the contact light and the retreating target.","preferred_route":"post_lighting_or_composite","validation":"Verify only the transient light decays while scene key and material identity remain.","conflicts_with":[],"sources":["P_LIGHTING"],"requires":["prior_contact_light_event"],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Localized spark illumination | lighting | follow_through
(
    'aa_light_sparks_local',
    'anime_action',
    'cyberpunk_cqc',
    'lighting',
    'follow_through',
    'Let the few sparks from the contact cast brief small patches of warm light on nearby glove and jacket surfaces as they pass. Keep the illumination local to each spark''s position; the distant background retains its established lighting.',
    'global strobe, light patches unrelated to sparks, all surfaces becoming metallic, permanent orange tint',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Tie each illumination pulse to the corresponding passing spark; fade with it.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep the sparks and affected nearby surfaces in the same readable view.","preferred_route":"post_lighting_or_composite","validation":"Check that light pulses follow spark proximity rather than random frame flicker.","conflicts_with":[],"sources":["P_LIGHTING"],"requires":["existing_spark_event"],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Restore the established scene key | lighting | recovery
(
    'aa_light_restore_key',
    'anime_action',
    'grounded_martial_arts',
    'lighting',
    'recovery',
    'During recovery, restore the same key-light direction and shadow policy established before the clash, with shadow placement following the new pose. Keep any new physical damage visible, but let the temporary attack illumination finish so the final guard reads under stable scene lighting.',
    'lingering attack glow, random light-source change, reset surface damage, alternating bright and dark frames',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Complete transient light decay before the recovery hold.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"End where the key-light side and final guard remain visible.","preferred_route":"prompt_plus_reference","validation":"Compare pre-action and recovery light direction while retaining new damage.","conflicts_with":[],"sources":["P_LIGHTING"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Kagenashi-style form-shadow suppression | lighting | execution
(
    'aa_light_kagenashi',
    'anime_action',
    'shonen_impact',
    'lighting',
    'execution',
    'For this action beat, suppress interior form-shadow patches on {actor} and let flat local colors plus the outer contour carry the pose. Keep the face and costume markings readable; ground contact shadows may remain as a separate environmental cue.',
    'soft volumetric body shading, new interior cel-shadow bands, glossy skin highlights, lost outline',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"actor_rendering_override","editorial_timeline_fps":24,"editorial_recipe":"Apply only to the selected actor and beat; restore the chosen shadow policy afterward.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Use a clear silhouette and color separation because interior shadow is intentionally reduced.","preferred_route":"reference_or_composite","validation":"Inspect actor interior shadow removal separately from preserved ground/contact cues.","conflicts_with":["aa_light_hard_shadow","aa_material_two_tone_cel"],"sources":["I_KAGENASHI"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Directional lightning illumination | lighting | impact
(
    'aa_light_directional_lightning',
    'anime_action',
    'supernatural_speed',
    'lighting',
    'impact',
    'When the authored lightning strike flashes, light only the fighter surfaces facing its visible origin and cast crisp shadows away from it. Keep the flash brief and preserve recognizable facial and costume boundaries under the high contrast.',
    'light from the wrong direction, prolonged full-white frame, random repeated lightning, missing facial contour',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"light_event","editorial_timeline_fps":24,"editorial_recipe":"One authored illumination pulse at the lightning event; restore the previous key afterward.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Show the light origin or an unambiguous illuminated side.","preferred_route":"post_lighting_or_composite","validation":"Compare highlight side and cast-shadow direction against the event origin.","conflicts_with":[],"sources":["P_LIGHTING"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Two-tone cel construction | material_shading | anticipation
(
    'aa_material_two_tone_cel',
    'anime_action',
    'shonen_impact',
    'material_shading',
    'anticipation',
    'Render the held preparation with solid local-color fills and one sharply bounded darker shade per material. Preserve consistent black contours, simple readable folds and distinct skin, fabric and metal color regions.',
    'airbrushed gradients, clay skin, photoreal pores, muddy textured fills, glossy plastic fabric',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Keep palette and contour weight stable through the hold.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Use a readable mid or full-body composition so contour and fill boundaries remain visible.","preferred_route":"prompt_plus_reference","validation":"Inspect crisp fill boundaries and stable colors on consecutive frames.","conflicts_with":["aa_light_kagenashi"],"sources":["P_TOON"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Controlled contour line boil | material_shading | execution
(
    'aa_material_controlled_line_boil',
    'anime_action',
    'shonen_impact',
    'material_shading',
    'execution',
    'Allow a slight hand-redrawn variation in the ink contour from drawing to drawing while preserving {actor}''s pose structure, facial landmarks and costume boundaries. Keep the interior color fills stable so the contour feels alive without the body changing shape.',
    'silhouette crawling, face deformation, flickering fill colors, excessive scratch noise, rigid vector perfection',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Vary ink only on new drawings; hold it unchanged during repeated exposure of the same drawing.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep framing stable enough to distinguish contour variation from camera shake.","preferred_route":"drawn_reference_or_post","validation":"Verify small contour variation without systematic landmark drift or fill flicker.","conflicts_with":[],"sources":["P_LINE_BOIL"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Monochrome graphic impact frame | material_shading | impact
(
    'aa_material_monochrome_impact',
    'anime_action',
    'shonen_impact',
    'material_shading',
    'impact',
    'On the single designated contact drawing, replace the normal palette with stark black and white shapes and a few directional ink cuts around the collision. Keep the contacting limbs recognizable, then restore the established colors on the next clean drawing.',
    'permanent grayscale sequence, muddy gray gradients, unreadable merged bodies, crossfaded palette transition',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"contact_frame_render_override","editorial_timeline_fps":24,"editorial_recipe":"Use 1 editorial frame unless a deliberate 2-frame accent is authored; composite for exact placement.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep the same camera and contact geometry through the palette change.","preferred_route":"post_palette_effect","validation":"Confirm contact alignment, recognizable limbs and immediate palette restoration.","conflicts_with":["aa_material_inverted_impact","aa_material_charcoal_impact"],"sources":["I_FAURE","P_TOON","P_TIMING"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Expressive rough ink during recoil | material_shading | recoil
(
    'aa_material_expressive_rough',
    'anime_action',
    'shonen_impact',
    'material_shading',
    'recoil',
    'During the strongest recoil drawing, use energetic broken ink strokes and a few searching contour lines that follow the force through {target}''s body. Keep joint connections and facial identity readable; return to the established clean contour treatment when the pose resolves.',
    'random scribbles hiding anatomy, disconnected joints, permanent dirty texture, new facial features',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Limit rough treatment to the chosen recoil accent keys, with clean keys before and after.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Prefer a readable three-quarter silhouette over overlapping front-on limbs.","preferred_route":"drawn_reference_or_post","validation":"Check that expressive lines describe the existing body instead of replacing it.","conflicts_with":[],"sources":["I_OHIRA","I_HASHIMOTO"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Flat-shaded debris faces | material_shading | follow_through
(
    'aa_material_flat_debris_faces',
    'anime_action',
    'shonen_impact',
    'material_shading',
    'follow_through',
    'Give each existing angular stone fragment two or three flat face colors separated by crisp edges. Preserve the fragment''s shape and material as it turns; use clean drawn silhouettes instead of pebbled photoreal texture.',
    'glossy plastic cubes, rounded melting edges, changing fragment material, noisy photogrammetry texture',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"debris_material_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Update face shading only as the existing fragment rotates under the established light.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Keep large fragments readable against the dust and sky.","preferred_route":"prompt_plus_reference","validation":"Track the same major fragment silhouette and verify stable stone colors.","conflicts_with":[],"sources":["I_NAKAMURA","P_TOON"],"requires":["existing_debris_objects"],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Restore local colors and contour weight | material_shading | recovery
(
    'aa_material_restore_palette',
    'anime_action',
    'shonen_impact',
    'material_shading',
    'recovery',
    'In the recovered pose, restore the exact established costume colors, skin colors and contour weight after any impact treatment. Preserve new dirt, tears and damage as localized changes while the rest of the character returns to the baseline cel rendering.',
    'lingering inverted colors, entire outfit recolored, erased battle damage, changing outline thickness',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"bound_actor_and_beat","editorial_timeline_fps":24,"editorial_recipe":"Complete restoration on the first clean recovery key and keep it stable.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Use a stable closing view suitable for comparing the model and palette.","preferred_route":"prompt_plus_reference","validation":"Compare known color patches and contour weight while checking persistent damage.","conflicts_with":[],"sources":["P_TOON"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Single inverted-palette accent | material_shading | impact
(
    'aa_material_inverted_impact',
    'anime_action',
    'supernatural_speed',
    'material_shading',
    'impact',
    'At the designated contact frame, invert the established image colors for one sharp graphic accent while preserving the same silhouettes and geometry. Immediately return to the normal palette; keep this as an image treatment rather than a change to the fighters'' materials.',
    'permanent inverted costume, gradual color dissolve, new objects during flash, repeated strobing',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"contact_frame_render_override","editorial_timeline_fps":24,"editorial_recipe":"One editorial frame; implement as an explicit postproduction color inversion.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Preserve identical framing across the inversion.","preferred_route":"post_palette_effect","validation":"Compare geometry before, during and after, and confirm only the chosen frame is inverted.","conflicts_with":["aa_material_monochrome_impact","aa_material_charcoal_impact"],"sources":["P_TIMING"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
),

-- Charcoal-style impact accent | material_shading | impact
(
    'aa_material_charcoal_impact',
    'anime_action',
    'shonen_impact',
    'material_shading',
    'impact',
    'For the designated impact drawing, replace polished contours with forceful charcoal-like black strokes on a pale field. Concentrate the marks around the collision and line of action while preserving distinct heads and limb roots; restore clean cel rendering immediately afterward.',
    'all-frame charcoal filter, random illegible scribble, fused faces, permanent paper texture, blended accent frame',
    '{"schema_version":1,"evidence_status":"untested_prompt_candidate","scope":"contact_frame_render_override","editorial_timeline_fps":24,"editorial_recipe":"Use one authored accent drawing, optionally held for a second editorial frame.","engine_parameters":{"motion_scale":null,"native_fps":null,"policy":"Resolve against the selected model, version and endpoint; these nulls are not API arguments."},"camera_rule":"Retain the established contact composition and readable limb separation.","preferred_route":"drawn_reference_or_post","validation":"Verify the accent is localized in time and the original scene resumes with the same contact state.","conflicts_with":["aa_material_monochrome_impact","aa_material_inverted_impact"],"sources":["I_HASHIMOTO","I_FAURE","P_TIMING"],"requires":[],"conflict_policy":"Apply declared conflicts only to overlapping intervals and affected scopes. The list is curated and non-exhaustive."}'
)
ON CONFLICT(directive_id) DO UPDATE SET
    archetype=excluded.archetype,
    sub_genre=excluded.sub_genre,
    slot_id=excluded.slot_id,
    moment_type=excluded.moment_type,
    prompt_snippet=excluded.prompt_snippet,
    negative_snippet=excluded.negative_snippet,
    mechanical_guidance=excluded.mechanical_guidance;

CREATE INDEX IF NOT EXISTS idx_aa_directives_lookup
ON semantic_directives(archetype, slot_id, moment_type, sub_genre);
COMMIT;
