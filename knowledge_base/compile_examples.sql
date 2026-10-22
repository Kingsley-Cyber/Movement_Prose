-- Deterministic selection manifests, not arbitrary GROUP BY picks.
-- Bind actor/target/contact placeholders in application code before sending prose.
-- Concatenate ordered rows in application code; do not rely on implicit group_concat order.

-- windup_eight_slots
WITH selected(ordinal, directive_id) AS (VALUES
  (1, 'aa_subject_loaded_silhouette'),
  (2, 'aa_env_preimpact_quiet'),
  (3, 'aa_action_weight_load'),
  (4, 'aa_secondary_cloth_lag'),
  (5, 'aa_time_hold_then_burst'),
  (6, 'aa_camera_low_tilt'),
  (7, 'aa_light_hard_shadow'),
  (8, 'aa_material_two_tone_cel')
)
SELECT selected.ordinal, d.slot_id, d.moment_type, d.directive_id,
       d.prompt_snippet, d.negative_snippet, d.mechanical_guidance
FROM selected JOIN semantic_directives AS d USING (directive_id)
WHERE d.archetype = 'anime_action'
ORDER BY selected.ordinal;

-- travel_eight_slots
WITH selected(ordinal, directive_id) AS (VALUES
  (1, 'aa_subject_angular_pose'),
  (2, 'aa_env_layered_parallax'),
  (3, 'aa_action_hip_led_punch'),
  (4, 'aa_secondary_hair_snap'),
  (5, 'aa_time_mixed_exposures'),
  (6, 'aa_camera_lateral_track'),
  (7, 'aa_light_thin_rim'),
  (8, 'aa_material_controlled_line_boil')
)
SELECT selected.ordinal, d.slot_id, d.moment_type, d.directive_id,
       d.prompt_snippet, d.negative_snippet, d.mechanical_guidance
FROM selected JOIN semantic_directives AS d USING (directive_id)
WHERE d.archetype = 'anime_action'
ORDER BY selected.ordinal;

-- recovery_eight_slots
WITH selected(ordinal, directive_id) AS (VALUES
  (1, 'aa_subject_recovery_model'),
  (2, 'aa_env_debris_settle'),
  (3, 'aa_action_guard_recovery'),
  (4, 'aa_secondary_cloth_settle'),
  (5, 'aa_time_moving_hold'),
  (6, 'aa_camera_recovery_settle'),
  (7, 'aa_light_restore_key'),
  (8, 'aa_material_restore_palette')
)
SELECT selected.ordinal, d.slot_id, d.moment_type, d.directive_id,
       d.prompt_snippet, d.negative_snippet, d.mechanical_guidance
FROM selected JOIN semantic_directives AS d USING (directive_id)
WHERE d.archetype = 'anime_action'
ORDER BY selected.ordinal;

-- block_contact_overrides
WITH selected(ordinal, directive_id) AS (VALUES
  (3, 'aa_action_forearm_block'),
  (4, 'aa_secondary_angular_impact_star'),
  (5, 'aa_time_contact_hitstop'),
  (6, 'aa_camera_contact_lock'),
  (8, 'aa_material_monochrome_impact')
)
SELECT selected.ordinal, d.slot_id, d.moment_type, d.directive_id,
       d.prompt_snippet, d.negative_snippet, d.mechanical_guidance
FROM selected JOIN semantic_directives AS d USING (directive_id)
WHERE d.archetype = 'anime_action'
ORDER BY selected.ordinal;
