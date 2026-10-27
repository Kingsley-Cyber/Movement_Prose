# Style packs: Taekwondo, Capoeira, Catch wrestling, Lethwei and kung fu variants.
# Executed inside build_seeds.py (uses its helpers: new, frames, rec, ARM, SLR).
# Every style = a school (capability) + its techniques + grants of existing techniques
# + combos + (where needed) positions, rulesets, effects and school defense prepends.

STYLE_CAPS = OrderedDict([
    ("taekwondo", "Taekwondo: fast instep round kicks, cut kicks, spinning and jumping kicks, bouncing footwork; hands low, body punches."),
    ("capoeira", "Capoeira: ginga footwork, low evasions (esquiva, negativa), spinning and crescent kicks, sweeps (rasteira), cartwheels, headbutts."),
    ("catch_wrestling", "Catch wrestling: shots and snap-downs, rides, cross-faces and cradles, neck cranks, double wristlocks and leg locks."),
    ("lethwei", "Lethwei (Burmese boxing): the full Muay Thai arsenal bare-knuckle, plus headbutts and clinch throws."),
    ("wing_chun", "Wing Chun: centerline chain punches, hand traps (pak sao, lap sao), deflections (tan sao, bong sao), low stop kicks, elbows."),
    ("hung_gar", "Hung Gar: rooted horse stance, tiger claws, bridge-arm smashes, no-shadow kick, heavy straight and hooking punches."),
    ("bajiquan", "Bajiquan: explosive close-range stomping punches, top elbow, iron-mountain shoulder lean."),
    ("baguazhang", "Baguazhang: circle walking for angles, palm changes, piercing palms, turning throws and leg sweeps."),
    ("tai_chi", "Tai Chi (push hands): redirect and neutralize, then issue power (fa jin) to uproot; palm strikes and deflect-parry-punch."),
    ("shuai_jiao", "Shuai Jiao (Chinese wrestling): quick-grip throws, kick-trips, leg catches; throws and stays standing."),
    ("jeet_kune_do", "Jeet Kune Do: intercepting lead straight, stop kicks, finger jab, trapping into the straight blast; strong side forward."),
])

THR = ["head_straight", "head_hook", "body"]          # exposed after a committed hand strike
KLR = ["single_support", "head_straight"]             # light kick recovery
AIR = lambda t, a, l, lanes, pen: {"takeoff_frames": t, "apex_frames": a, "landing_frames": l, "landing_exposed_lanes": lanes, "landing_penalty": pen}  # noqa: E731

# ---------------------------------------------------------------- Taekwondo
new("fast_roundhouse", "Fast roundhouse (bandal chagi)", "kick", ["taekwondo"], ["kick"], "body", "body", 1.9, "buildup", frames(3, 6, 2, 7), rec("single_leg_recovery", KLR, 0.6),
    side="either", limb="foot", surface="instep", line="lead_round_kick", tsr="opposite_of_limb", energy=0.75, acc=0.06, catch=0.30,
    counters=["check", "kick_catch"], exploits=["body", "tempo"], notes="Snapping instep round kick off either leg; scores fast and retracts fast.")
new("instep_head_kick", "Instep head kick (dollyo chagi)", "kick", ["taekwondo"], ["kick"], "head_hook", "head", 2.9, "impact", frames(5, 8, 3, 11), rec("single_leg_recovery", SLR, 1.0),
    side="rear", limb="foot", surface="instep", line="rear_round_kick", tsr="opposite_of_limb", energy=1.05, acc=0.0, catch=0.10,
    counters=["lean_back", "shell_block"], exploits=["head_hook", "vision"])
new("cut_kick", "Cut kick", "kick", ["taekwondo"], ["kick", "punch"], "body", "body", 1.3, "buildup", frames(2, 5, 2, 5), rec("single_leg_recovery", ["single_support"], 0.4),
    side="lead", limb="foot", surface="sole", line="lead_linear_kick", tsr="center", energy=0.55, acc=0.08, catch=0.25, stop_hit=True,
    counters=["parry", "kick_catch"], exploits=["entry", "tempo"], notes="Lead leg lifts and pushes into the hip or belly to stop an advance.")
new("tornado_kick", "Tornado kick (360 roundhouse)", "kick", ["taekwondo", "acrobatics"], ["kick"], "head_hook", "head", 3.4, "impact", frames(8, 10, 4, 17), rec("airborne_landing_recovery", ["single_support", "entry", "body"], 1.5),
    side="rear", limb="foot", surface="instep", line="spinning", tsr="opposite_of_limb", energy=1.60, acc=-0.12, catch=0.08, vmin="athletic", requires_airborne_training=True,
    airborne=AIR(4, 3, 6, ["single_support", "entry", "body"], 1.3), counters=["evade_step_back", "jam_step"], exploits=["head_hook", "vision"])
new("jumping_back_kick", "Jumping back kick (twimyo dwit chagi)", "kick", ["taekwondo"], ["kick"], "body", "body", 3.5, "impact", frames(7, 9, 4, 16), rec("airborne_landing_recovery", ["single_support", "entry", "head_straight"], 1.4),
    side="rear", limb="heel", surface="heel", line="spinning", tsr="center", energy=1.55, acc=-0.10, catch=0.12, vmin="athletic", requires_airborne_training=True,
    airborne=AIR(3, 3, 5, ["single_support", "entry", "head_straight"], 1.2), counters=["evade_step_back", "pivot"], exploits=["body", "entry"])
new("double_roundhouse", "Double roundhouse (dubal dangsang)", "kick", ["taekwondo"], ["kick"], "body", "body", 2.6, "buildup", frames(5, 9, 3, 12), rec("airborne_landing_recovery", ["single_support", "entry"], 1.1),
    side="either", limb="foot", surface="instep", line="lead_round_kick", tsr="opposite_of_limb", energy=1.35, acc=0.02, catch=0.15, vmin="athletic", requires_airborne_training=True,
    airborne=AIR(3, 2, 5, ["single_support", "entry"], 0.9), counters=["evade_step_back", "shell_block"], exploits=["body", "tempo"],
    notes="Two quick round kicks with alternating legs in one hop.")
new("bounce_step", "Bounce step", "movement", ["taekwondo"], ["outside", "kick"], "space", "angle", 0.0, "none", frames(2, 5, 0, 3), rec("none", [], 0.1),
    side="none", limb="feet", surface="feet", line="none", tsr="none", energy=0.35, usage="movement", resolution="movement", exploits=["tempo", "angle"],
    notes="Rhythmic bouncing that changes distance and switches the lead leg on the hop.")
new("body_straight_punch", "Body punch (jireugi)", "punch", ["taekwondo", "karate"], ["punch", "close"], "body", "body", 1.4, "buildup", frames(3, 5, 2, 6), rec("short_retract", ["head_hook", "head_straight"], 0.4),
    side="rear", limb="fist", surface="rear_knuckles", line="rear_straight", tsr="center", energy=0.60, acc=0.04, counters=["shell_block", "parry"], exploits=["body", "tempo"])

# ---------------------------------------------------------------- Capoeira
new("ginga", "Ginga", "movement", ["capoeira"], ["outside", "kick", "punch"], "space", "angle", 0.0, "none", frames(2, 6, 0, 3), rec("none", [], 0.15),
    side="none", limb="feet", surface="feet", line="none", tsr="none", energy=0.45, usage="movement", resolution="movement", exploits=["angle", "vision", "tempo"],
    notes="Constant rocking triangle step that hides the timing of every attack.")
new("meia_lua_de_compasso", "Meia-lua de compasso", "kick", ["capoeira"], ["kick"], "head_hook", "head", 3.4, "impact", frames(7, 10, 4, 16), rec("wide_swing_recovery", ["single_support", "entry", "body"], 1.4),
    side="rear", limb="heel", surface="heel", line="spinning", tsr="opposite_of_limb", energy=1.40, acc=-0.08, catch=0.05,
    counters=["jam_step", "evade_step_back"], exploits=["head_hook", "vision"], notes="Drops low with a hand on the floor and spins the rear heel through head height.")
new("armada", "Armada", "kick", ["capoeira"], ["kick"], "head_hook", "head", 3.1, "impact", frames(7, 9, 3, 15), rec("wide_swing_recovery", ["single_support", "entry", "body"], 1.3),
    side="rear", limb="foot", surface="outside_edge", line="spinning", tsr="opposite_of_limb", energy=1.30, acc=-0.08, catch=0.06,
    counters=["evade_step_back", "jam_step"], exploits=["head_hook", "angle"], notes="Standing spinning outside crescent kick.")
new("queixada", "Queixada", "kick", ["capoeira"], ["kick"], "head_hook", "head", 2.6, "impact", frames(5, 8, 3, 12), rec("single_leg_recovery", SLR, 1.0),
    side="rear", limb="foot", surface="outside_edge", line="rear_round_kick", tsr="opposite_of_limb", energy=1.10, acc=-0.04, catch=0.08,
    counters=["lean_back", "evade_step_back"], exploits=["head_hook", "vision"], notes="Outside crescent kick swung across the face.")
new("martelo", "Martelo", "kick", ["capoeira"], ["kick"], "head_hook", "head", 2.8, "impact", frames(5, 8, 3, 11), rec("single_leg_recovery", SLR, 1.0),
    side="rear", limb="foot", surface="instep", line="rear_round_kick", tsr="opposite_of_limb", energy=1.05, acc=0.0, catch=0.12,
    counters=["lean_back", "shell_block"], exploits=["head_hook"], notes="Instep round kick ('hammer').")
new("bencao", "Bênção", "kick", ["capoeira"], ["kick", "punch"], "body", "body", 1.8, "buildup", frames(4, 6, 2, 7), rec("single_leg_recovery", ["single_support", "head_straight"], 0.6),
    side="rear", limb="foot", surface="sole", line="rear_linear_kick", tsr="center", energy=0.80, acc=0.04, catch=0.28, stop_hit=True,
    counters=["parry", "kick_catch"], exploits=["body", "entry"], notes="Front push kick to the chest ('blessing').")
new("rasteira", "Rasteira", "sweep", ["capoeira"], ["kick", "punch"], "single_support", "leg", 1.0, "impact", frames(3, 6, 3, 9), rec("single_leg_recovery", ["single_support", "head_straight", "entry"], 0.7),
    side="either", limb="foot", surface="instep_hook", line="grapple", tsr="defender_lead", energy=0.80, resolution="grapple", result_pos="standing_knockdown",
    counters=["switch_step", "evade_step_back"], exploits=["single_support", "tempo"], notes="From a crouch or after an evasion, hooks the support foot out.")
new("esquiva", "Esquiva", "defense", ["capoeira"], ["kick", "punch"], "head_hook", "space", 0.0, "none", frames(2, 5, 0, 4), rec("none", ["head_uppercut", "body"], 0.25),
    side="none", limb="torso", surface="none", line="none", tsr="none", energy=0.40, usage="defense", resolution="defense", exploits=[])
new("negativa", "Negativa", "defense", ["capoeira"], ["kick", "punch"], "head_hook", "space", 0.0, "none", frames(3, 6, 0, 6), rec("none", ["head_uppercut", "body", "entry"], 0.4),
    side="none", limb="whole body", surface="none", line="none", tsr="none", energy=0.50, usage="defense", resolution="defense", exploits=[],
    notes="Drops to the floor under the attack, ready to sweep.")
new("au", "Aú (cartwheel)", "movement", ["capoeira", "acrobatics"], ["kick", "punch"], "space", "angle", 0.0, "none", frames(3, 8, 0, 6), rec("airborne_landing_recovery", ["single_support", "entry"], 0.6),
    side="none", limb="hands and feet", surface="none", line="none", tsr="none", energy=0.90, usage="movement", resolution="movement", vmin="athletic", requires_airborne_training=True,
    airborne=AIR(3, 3, 4, ["single_support", "entry"], 0.6), exploits=["angle"], notes="Cartwheel to change angle or escape a corner; flows into au batido.")

# ---------------------------------------------------------------- Catch wrestling (+ leg-entanglement position)
new("cross_face", "Cross-face", "control", ["catch_wrestling", "wrestling"], ["ground"], "ground", "head", 0.6, "control", frames(3, 8, 3, 6), rec("none", [], 0.25),
    side="lead", limb="forearm", surface="forearm_across_face", line="ground", tsr="grip_side", energy=0.90, resolution="grapple",
    requires_position=["half_guard:top", "side_control:top", "turtle:top"], counters=["hip_escape"], exploits=["ground"],
    notes="Forearm driven across the face to turn the head away; kills the bottom player's escapes.")
new("cradle", "Cradle", "control", ["catch_wrestling", "wrestling"], ["ground"], "ground", "hips", 0.6, "control", frames(5, 12, 4, 8), rec("none", [], 0.35),
    side="both", limb="arms", surface="cradle_grip", line="ground", tsr="grip_side", energy=1.20, resolution="grapple", result_pos="side_control",
    requires_position=["turtle:top", "half_guard:top"], counters=["hip_escape"], exploits=["ground"])
new("neck_crank", "Neck crank", "submission", ["catch_wrestling"], ["clinch", "ground"], "ground", "neck_arm", 3.6, "submission", frames(6, 13, 6, 10), rec("none", [], 0.35),
    side="both", limb="arms", surface="forearm_and_head_control", line="ground", tsr="none", joint="neck", energy=1.20, resolution="submission",
    requires_position=["front_headlock", "side_control:top", "back_control:top", "turtle:top"], counters=["submission_escape"], exploits=["ground"])
new("keylock", "Keylock (americana)", "submission", ["catch_wrestling", "bjj"], ["ground"], "ground", "neck_arm", 3.5, "submission", frames(6, 14, 6, 10), rec("none", [], 0.35),
    side="both", limb="arms", surface="figure_four_bent_arm", line="ground", tsr="grip_side", joint="shoulder", energy=1.10, resolution="submission",
    requires_position=["side_control:top", "mount:top"], counters=["submission_escape"], exploits=["ground"])
new("leg_entry", "Leg-entanglement entry", "control", ["catch_wrestling", "bjj"], ["ground"], "ground", "leg", 0.3, "control", frames(4, 10, 3, 7), rec("none", ["head_straight"], 0.35),
    side="both", limb="legs", surface="hooks_on_leg", line="ground", tsr="defender_lead", energy=1.00, resolution="grapple", result_pos="leg_entanglement",
    requires_position=["closed_guard:bottom", "half_guard:bottom", "half_guard:top", "scramble"], counters=["leg_pummel_escape"], exploits=["ground", "single_support"])
new("toe_hold", "Toe hold", "submission", ["catch_wrestling", "judo"], ["ground"], "ground", "leg", 3.4, "submission", frames(6, 13, 6, 10), rec("none", [], 0.35),
    side="both", limb="hands", surface="figure_four_on_foot", line="ground", tsr="grip_side", joint="ankle", energy=1.10, resolution="submission",
    requires_position=["leg_entanglement:bottom", "half_guard:top"], counters=["submission_escape"], exploits=["ground"])
new("heel_hook", "Heel hook", "submission", ["catch_wrestling"], ["ground"], "ground", "leg", 4.0, "submission", frames(6, 12, 6, 10), rec("none", [], 0.4),
    side="both", limb="arms", surface="heel_cupped_in_elbow", line="ground", tsr="grip_side", joint="knee", energy=1.20, resolution="submission",
    requires_position=["leg_entanglement:bottom"], counters=["submission_escape"], exploits=["ground"])
new("ankle_lock", "Straight ankle lock", "submission", ["catch_wrestling", "bjj", "judo"], ["ground"], "ground", "leg", 3.2, "submission", frames(6, 12, 6, 10), rec("none", [], 0.35),
    side="both", limb="arms", surface="wrist_under_achilles", line="ground", tsr="grip_side", joint="ankle", energy=1.05, resolution="submission",
    requires_position=["leg_entanglement:bottom"], counters=["submission_escape"], exploits=["ground"])
new("leg_pummel_escape", "Clear the legs", "escape", ["basic_movement", "bjj", "wrestling", "catch_wrestling", "anti_grappling"], ["ground"], "ground", "space", 0.0, "none", frames(4, 10, 2, 7), rec("none", ["head_straight"], 0.35),
    side="both", limb="legs and hands", surface="frames", line="ground", tsr="none", energy=1.00, usage="both", resolution="grapple", result_pos="standing_neutral",
    requires_position=["leg_entanglement:top"], exploits=[], notes="Hides the heel, pummels the legs free and stands; odds come from grappling profiles.")

# ---------------------------------------------------------------- Lethwei
new("clinch_headbutt", "Clinch headbutt", "punch", ["lethwei"], ["clinch"], "head_straight", "head", 2.9, "impact", frames(3, 5, 3, 7), rec("short_retract", ["head_uppercut"], 0.5),
    side="none", limb="forehead", surface="forehead", line="none", tsr="center", energy=0.80, acc=0.04, cut=0.25,
    counters=["pummel", "clinch_break"], exploits=["clinch", "head_straight"])
new("lunging_headbutt", "Lunging headbutt", "punch", ["lethwei"], ["close", "punch"], "head_straight", "head", 3.2, "impact", frames(5, 6, 3, 10), rec("extended_arm_recovery", ["head_uppercut", "body", "entry"], 0.9),
    side="none", limb="forehead", surface="forehead", line="none", tsr="center", energy=1.00, acc=-0.06, cut=0.25,
    counters=["straight_knee", "jam_step"], exploits=["entry", "head_straight"], notes="Ducks in behind a feint and drives the forehead into the face.")

# ---------------------------------------------------------------- Wing Chun
new("chain_punch", "Chain punches (lin wan kuen)", "punch", ["wing_chun", "jeet_kune_do"], ["punch", "close"], "head_straight", "head", 1.9, "buildup", frames(2, 6, 3, 6), rec("short_retract", ["head_hook", "body"], 0.45),
    side="both", limb="fists", surface="vertical_fist", line="lead_straight", tsr="center", energy=0.90, acc=0.10,
    counters=["shell_block", "bob_weave", "pivot"], exploits=["head_straight", "tempo"], notes="Rapid alternating vertical-fist punches down the centerline while stepping in.")
new("pak_sao", "Pak sao (slapping trap)", "grip", ["wing_chun", "jeet_kune_do"], ["punch", "close"], "head_straight", "head", 0.0, "control", frames(2, 4, 1, 4), rec("short_retract", ["head_hook"], 0.25),
    side="lead", limb="palm", surface="palm", line="lead_straight", tsr="center", energy=0.40, acc=0.06,
    counters=["retreat", "pivot"], exploits=["head_straight", "tempo"], notes="Slaps the lead arm down and pins it for the follow-up punch.")
new("lap_sao", "Lap sao (pulling trap)", "grip", ["wing_chun"], ["punch", "close"], "head_straight", "head", 0.0, "control", frames(3, 5, 2, 5), rec("short_retract", ["head_hook", "body"], 0.3),
    side="lead", limb="hand", surface="wrist_grip", line="lead_straight", tsr="center", energy=0.50, acc=0.04,
    counters=["retreat", "pivot"], exploits=["head_straight", "single_support"], notes="Grabs and yanks the lead wrist to pull the opponent onto the strike.")
new("bong_sao", "Bong sao (wing arm)", "defense", ["wing_chun"], ["punch", "close"], "head_hook", "space", 0.0, "none", frames(2, 4, 0, 3), rec("none", ["body"], 0.2),
    side="lead", limb="forearm", surface="forearm_edge", line="none", tsr="none", energy=0.30, usage="defense", resolution="defense", exploits=[])
new("tan_sao", "Tan sao (dispersing hand)", "defense", ["wing_chun"], ["punch", "close"], "head_straight", "space", 0.0, "none", frames(2, 4, 0, 3), rec("none", ["head_hook"], 0.2),
    side="lead", limb="palm up forearm", surface="forearm", line="none", tsr="none", energy=0.30, usage="defense", resolution="defense", exploits=[])

# ---------------------------------------------------------------- Hung Gar
new("tiger_claw", "Tiger claw (fu jow)", "punch", ["hung_gar"], ["punch", "close"], "head_straight", "head", 2.2, "impact", frames(4, 6, 3, 8), rec("extended_arm_recovery", ARM, 0.6),
    side="rear", limb="palm and fingers", surface="clawed_palm", line="rear_straight", tsr="center", energy=0.85, acc=0.02, cut=0.10,
    counters=["parry", "shell_block"], exploits=["head_straight", "vision"])
new("bridge_smash", "Bridge smash (kiu sau)", "elbow", ["hung_gar"], ["punch", "close"], "head_hook", "head", 2.4, "impact", frames(4, 6, 3, 8), rec("short_retract", ["body", "head_straight"], 0.5),
    side="rear", limb="forearm", surface="forearm_bridge", line="elbow", tsr="opposite_of_limb", energy=0.95, acc=0.0,
    counters=["shell_block"], exploits=["head_hook", "clinch"], notes="Hardened forearm smashes through the guard.")
new("no_shadow_kick", "No-shadow kick (mo ying geuk)", "kick", ["hung_gar"], ["kick", "punch"], "body", "body", 2.0, "impact", frames(2, 5, 2, 7), rec("single_leg_recovery", KLR, 0.6),
    side="rear", limb="foot", surface="ball_of_foot", line="rear_linear_kick", tsr="center", energy=0.80, acc=0.08, catch=0.22,
    counters=["parry", "kick_catch"], exploits=["body", "vision"], notes="A front kick launched from behind the hands with no wind-up.")

# ---------------------------------------------------------------- Bajiquan
new("stomp_thrust_punch", "Stomp punch (chong chui)", "punch", ["bajiquan"], ["punch", "close"], "body", "body", 2.6, "impact", frames(4, 5, 3, 9), rec("extended_arm_recovery", ["head_hook", "head_straight"], 0.7),
    side="rear", limb="fist", surface="fist_face", line="rear_straight", tsr="center", energy=1.05, acc=0.0,
    counters=["shell_block", "pivot"], exploits=["body", "entry"], notes="Explosive stamping step driving a short straight punch through the trunk.")
new("top_elbow", "Top elbow (ding zhou)", "elbow", ["bajiquan"], ["close", "clinch"], "body", "body", 2.8, "impact", frames(3, 5, 3, 8), rec("short_retract", ["head_hook", "head_straight"], 0.5),
    side="rear", limb="elbow", surface="elbow_point", line="elbow", tsr="center", energy=0.95, acc=0.04,
    counters=["pummel", "shell_block"], exploits=["body", "entry", "clinch"])
new("iron_mountain_lean", "Iron mountain lean (tie shan kao)", "punch", ["bajiquan"], ["close", "clinch"], "body", "body", 2.4, "impact", frames(4, 6, 3, 10), rec("wide_swing_recovery", ["head_hook", "entry", "body"], 0.9),
    side="rear", limb="shoulder and back", surface="shoulder_back", line="none", tsr="center", energy=1.20, acc=-0.02,
    counters=["jam_step", "pivot"], exploits=["entry", "clinch"], notes="Steps through and slams the shoulder and back into the opponent's chest.")

# ---------------------------------------------------------------- Baguazhang
new("circle_walk", "Circle walking (tang ni bu)", "movement", ["baguazhang"], ["kick", "punch", "close"], "space", "angle", 0.0, "none", frames(3, 7, 0, 4), rec("none", [], 0.1),
    side="none", limb="feet", surface="feet", line="none", tsr="none", energy=0.40, usage="movement", resolution="movement", exploits=["angle", "vision"])
new("single_palm_change", "Single palm change", "punch", ["baguazhang"], ["punch", "close"], "head_hook", "head", 2.0, "impact", frames(4, 6, 3, 8), rec("extended_arm_recovery", ARM, 0.55),
    side="lead", limb="palm", surface="palm_heel", line="lead_round", tsr="opposite_of_limb", energy=0.80, acc=0.04, counters=["shell_block", "parry"], exploits=["angle", "head_hook"])
new("piercing_palm", "Piercing palm (chuan zhang)", "punch", ["baguazhang"], ["punch"], "head_straight", "head", 1.8, "impact", frames(3, 5, 2, 6), rec("extended_arm_recovery", ARM, 0.5),
    side="lead", limb="palm", surface="fingertips_palm_edge", line="lead_straight", tsr="center", energy=0.65, acc=0.08, counters=["parry", "slip"], exploits=["head_straight", "vision", "tempo"])
new("turning_throw", "Turning throw", "takedown", ["baguazhang"], ["close", "clinch"], "clinch", "body", 2.4, "impact", frames(4, 9, 3, 11), rec("sprawled_shot_recovery", ["head_uppercut", "clinch"], 0.9),
    side="both", limb="arms and hips", surface="shoulder_turn", line="grapple", tsr="grip_side", energy=1.10, resolution="grapple", result_pos="standing_knockdown",
    counters=["whizzer", "pummel"], exploits=["clinch", "angle"], notes="Turns behind the opponent's shoulder and spins them to the floor while staying upright.")

# ---------------------------------------------------------------- Tai Chi
new("push_hands_redirect", "Redirect (hua jin)", "defense", ["tai_chi"], ["punch", "close", "clinch"], "head_straight", "space", 0.0, "none", frames(2, 5, 0, 4), rec("none", ["body"], 0.2),
    side="both", limb="forearms and waist", surface="forearms", line="none", tsr="none", energy=0.35, usage="defense", resolution="defense", exploits=[],
    notes="Sticks to the incoming arm and turns the waist to lead the force past, leaving the attacker off balance.")
new("fa_jin_push", "Fa jin push", "punch", ["tai_chi"], ["punch", "close", "clinch"], "body", "body", 0.8, "impact", frames(3, 5, 2, 7), rec("short_retract", ["head_straight"], 0.45),
    side="both", limb="palms", surface="both_palms", line="none", tsr="center", energy=0.90, acc=0.04, usage="both",
    counters=["jam_step", "pummel"], exploits=["entry", "wall", "tempo"], notes="Short explosive push from the legs that sends the opponent back off balance.")
new("brush_knee_palm", "Brush knee, push palm", "punch", ["tai_chi"], ["punch", "close"], "head_straight", "head", 1.9, "impact", frames(4, 6, 3, 8), rec("extended_arm_recovery", ARM, 0.5),
    side="rear", limb="palm", surface="palm_heel", line="rear_straight", tsr="center", energy=0.75, acc=0.05, usage="both", counters=["parry", "shell_block"], exploits=["recovery", "head_straight"])
new("deflect_parry_punch", "Deflect, parry and punch", "punch", ["tai_chi"], ["punch"], "head_straight", "head", 1.9, "impact", frames(4, 5, 3, 7), rec("extended_arm_recovery", ARM, 0.45),
    side="rear", limb="fist", surface="vertical_fist", line="rear_straight", tsr="center", energy=0.70, acc=0.06, usage="both", counters=["slip", "shell_block"], exploits=["recovery", "head_straight"])

# ---------------------------------------------------------------- Shuai Jiao
new("quick_grip_throw", "Quick-grip throw", "takedown", ["shuai_jiao"], ["close", "clinch"], "clinch", "body", 2.6, "impact", frames(3, 8, 3, 10), rec("sprawled_shot_recovery", ["head_uppercut", "clinch"], 0.85),
    side="both", limb="arms and hips", surface="sleeve_or_arm_grip", line="grapple", tsr="grip_side", energy=1.15, acc=0.04, resolution="grapple", result_pos="standing_knockdown",
    counters=["whizzer", "pummel"], exploits=["clinch", "single_support"], notes="Grips and throws in one beat; the thrower stays on his feet.")
new("kick_into_throw", "Kick-trip (ti)", "sweep", ["shuai_jiao"], ["punch", "close", "clinch"], "single_support", "leg", 1.6, "impact", frames(3, 7, 3, 9), rec("single_leg_recovery", ["single_support", "head_straight"], 0.6),
    side="lead", limb="shin and foot", surface="shin_hook", line="grapple", tsr="defender_lead", energy=0.90, resolution="grapple", result_pos="standing_knockdown",
    counters=["switch_step", "check"], exploits=["single_support", "clinch"])

# ---------------------------------------------------------------- Jeet Kune Do
new("lead_straight_intercept", "Intercepting lead straight", "punch", ["jeet_kune_do"], ["punch", "kick"], "head_straight", "head", 1.8, "impact", frames(2, 4, 2, 5), rec("short_retract", ["body"], 0.35),
    side="lead", limb="fist", surface="vertical_fist", line="lead_straight", tsr="center", energy=0.60, acc=0.12, usage="both", stop_hit=True,
    counters=["parry", "slip"], exploits=["entry", "tempo", "head_straight"], notes="The fastest tool to the nearest target, thrown as the opponent starts to move.")
new("finger_jab", "Finger jab", "punch", ["jeet_kune_do", "wing_chun"], ["punch", "kick"], "head_straight", "vision", 0.6, "buildup", frames(2, 4, 1, 5), rec("short_retract", ["body"], 0.3),
    side="lead", limb="fingertips", surface="fingertips", line="lead_straight", tsr="center", energy=0.50, acc=0.10,
    counters=["parry", "slip"], exploits=["vision", "entry"], notes="Eye jab. Street only.")

# ---------------------------------------------------------------- grants of existing techniques to the new schools
STYLE_GRANTS = {
    "taekwondo": ["side_kick", "front_kick", "axe_kick", "spinning_back_kick", "spinning_hook_kick", "question_mark_kick", "jumping_switch_kick", "flying_side_kick", "shell_block"],
    "capoeira": ["side_kick", "headbutt", "foot_sweep"],
    "catch_wrestling": ["double_leg", "single_leg", "ankle_pick", "snap_down", "ride", "kimura", "guillotine", "rear_naked_choke", "arm_triangle", "take_back", "pass_guard",
                        "advance_to_mount", "sprawl", "whizzer", "technical_standup", "hip_escape", "escape", "body_lock", "body_lock_takedown", "suplex", "underhook", "collar_tie", "pummel"],
    "lethwei": ["headbutt", "outside_trip", "inside_trip", "hip_throw"],
    "wing_chun": ["oblique_kick", "horizontal_elbow", "parry"],
    "hung_gar": ["cross", "hook", "body_hook", "uppercut", "low_kick", "front_kick", "shell_block", "parry"],
    "bajiquan": ["cross", "uppercut", "horizontal_elbow", "uppercut_elbow", "pummel", "shell_block"],
    "baguazhang": ["foot_sweep", "parry"],
    "tai_chi": ["parry"],
    "shuai_jiao": ["outside_trip", "inside_trip", "hip_throw", "foot_sweep", "kick_catch", "caught_kick_dump", "collar_tie", "underhook", "body_lock", "pummel", "whizzer"],
    "jeet_kune_do": ["jab", "cross", "hook", "side_kick", "oblique_kick", "parry", "slip"],
}
STYLE_GRANT_FROM = {"lethwei": "muay_thai"}   # lethwei also grants everything muay_thai grants
STYLE_POSITION_EXTRA = {"pass_guard": ["leg_entanglement:top"]}

# ---------------------------------------------------------------- effects (applied when the technique succeeds; §7.17)
STYLE_EFFECTS = {
    "ginga": [{"target": "opponent", "effect": "attention", "value": "feinted", "chance": 0.30, "exchanges": 1}],
    "bounce_step": [{"target": "self", "effect": "stance_switch", "chance": 0.50}],
    "circle_walk": [{"target": "opponent", "effect": "outside_angle", "chance": 0.35, "exchanges": 1}],
    "bencao": [{"target": "opponent", "effect": "push_back", "value": 1}],
    "pak_sao": [{"target": "opponent", "effect": "lane_penalty", "lanes": ["head_straight", "head_hook"], "value": 0.9, "exchanges": 1}],
    "lap_sao": [{"target": "opponent", "effect": "lane_penalty", "lanes": ["head_straight", "head_hook", "head_uppercut"], "value": 0.7, "exchanges": 1},
                {"target": "opponent", "effect": "balance", "value": "compromised"}],
    "tiger_claw": [{"target": "opponent", "effect": "vision", "value": -0.4, "exchanges": 2}],
    "bridge_smash": [{"target": "opponent", "effect": "lane_penalty", "lanes": ["head_straight", "head_hook"], "value": 0.6, "exchanges": 1}],
    "stomp_thrust_punch": [{"target": "opponent", "effect": "balance", "value": "compromised", "chance": 0.35}],
    "top_elbow": [{"target": "opponent", "effect": "balance", "value": "compromised", "chance": 0.50}],
    "iron_mountain_lean": [{"target": "opponent", "effect": "balance", "value": "off_base"}, {"target": "opponent", "effect": "push_back", "value": 1}],
    "piercing_palm": [{"target": "opponent", "effect": "vision", "value": -0.3, "exchanges": 1}],
    "push_hands_redirect": [{"target": "opponent", "effect": "balance", "value": "compromised"}],
    "fa_jin_push": [{"target": "opponent", "effect": "push_back", "value": 1}, {"target": "opponent", "effect": "balance", "value": "off_base"}],
    "finger_jab": [{"target": "opponent", "effect": "vision", "value": -0.8, "exchanges": 3}],
    "cross_face": [{"target": "opponent", "effect": "skill_penalty", "skills": ["bottom_game", "stand_up"], "value": 0.4, "exchanges": 2}],
    "negativa": [{"target": "self", "effect": "low_posture", "exchanges": 1}],
    "shove": [{"target": "opponent", "effect": "push_back", "value": 1}],
}
EFFECT_TYPES = ["attention", "outside_angle", "push_back", "lane_penalty", "balance", "vision", "skill_penalty", "stance_switch", "low_posture"]

STYLE_DEFENDS = {
    "esquiva": (["kick_high", "hook", "straight"], ["body_punch", "knee", "takedown", "kick_low"], "evaded", {}),
    "negativa": (["kick_high", "hook"], ["knee", "takedown", "kick_low"], "evaded", {}),
    "bong_sao": (["hook", "straight", "body_punch"], ["kick_low", "kick_high", "takedown", "uppercut"], "blocked", {}),
    "tan_sao": (["straight"], ["hook", "kick_low", "kick_body", "takedown", "knee"], "evaded", {}),
    "push_hands_redirect": (["straight", "hook", "body_punch", "clinch_entry"], ["kick_low", "kick_high", "knee", "takedown"], "evaded", {}),
}
STYLE_INCOMING_OVERRIDE = {"iron_mountain_lean": "clinch_entry", "fa_jin_push": "clinch_entry"}

# School defense prepends: a trained school's signature defenses go first in the defense list (§7.6)
STYLE_DEFENSE_PREPEND = {
    "capoeira": {"kick_high": ["esquiva", "negativa"], "hook": ["esquiva"], "straight": ["esquiva"], "kick_body": ["negativa"]},
    "wing_chun": {"straight": ["tan_sao"], "hook": ["bong_sao"], "body_punch": ["bong_sao"]},
    "tai_chi": {"straight": ["push_hands_redirect"], "hook": ["push_hands_redirect"], "body_punch": ["push_hands_redirect"], "clinch_entry": ["push_hands_redirect"]},
}

# ---------------------------------------------------------------- legality additions
OPEN_HAND_OR_FOUL = ["tiger_claw", "piercing_palm", "finger_jab"]          # clawing, throat and eye strikes
PALMS = ["single_palm_change", "brush_knee_palm"]                          # open-hand strikes: not in gloved sports
STYLE_BANNED = {
    "boxing": ["clinch_headbutt", "lunging_headbutt", "iron_mountain_lean", "fa_jin_push"] + OPEN_HAND_OR_FOUL + PALMS,
    "kickboxing": ["clinch_headbutt", "lunging_headbutt", "iron_mountain_lean", "pak_sao", "lap_sao"] + OPEN_HAND_OR_FOUL + PALMS,
    "muay_thai": ["clinch_headbutt", "lunging_headbutt", "iron_mountain_lean"] + OPEN_HAND_OR_FOUL + PALMS,
    "mma": ["clinch_headbutt", "lunging_headbutt"] + OPEN_HAND_OR_FOUL,
}
STYLE_ALLOWED = {"muay_thai": ["kick_into_throw"]}
LETHWEI_RULESET = {
    "legal_kinds": ["movement", "feint", "punch", "elbow", "kick", "knee", "defense", "grip", "sweep"],
    "allowed_techniques": ["clinch_break", "outside_trip", "inside_trip", "hip_throw", "body_lock_takedown", "sanda_sweep", "quick_grip_throw", "turning_throw"],
    "banned_techniques": ["snap_down", "sprawl", "submission_escape", "pak_sao", "lap_sao"] + OPEN_HAND_OR_FOUL,
    "clinch": {"allowed": True, "referee_break_after_exchanges": None, "allowed_grips": "all", "note": "Clinch fighting with headbutts, knees and throws; separated when it stalls."},
    "ground": {"allowed": False, "on_knockdown": "standing_count", "on_sweep": "reset_standing_with_score"},
    "environment": "ring", "default_rounds": 5, "default_round_s": 180,
    "decision_weights": {"clean_strikes": 0.20, "damage": 0.45, "control": 0.05, "aggression": 0.30},
    "notes": ("Modern (World Lethwei Championship) rules: bare knuckle with wraps, headbutts legal, judged if no finish "
              "(aggression, damage, strikes, blood drawn), 3 knockdowns in a round or 4 in the fight end it. Traditional rules (owner option D21): "
              "knockout-only with a draw at the final bell, and a 2-minute knockout time-out once per fighter except in the last round."),
}
EQUIPMENT = {
    "boxing": {"gloves": True, "punch_damage_multiplier": 1.0, "cut_chance_bonus": 0.0},
    "kickboxing": {"gloves": True, "punch_damage_multiplier": 1.0, "cut_chance_bonus": 0.0},
    "muay_thai": {"gloves": True, "punch_damage_multiplier": 1.0, "cut_chance_bonus": 0.0},
    "mma": {"gloves": True, "punch_damage_multiplier": 1.0, "cut_chance_bonus": 0.02},
    "street": {"gloves": False, "punch_damage_multiplier": 1.10, "cut_chance_bonus": 0.08},
    "lethwei": {"gloves": False, "punch_damage_multiplier": 1.10, "cut_chance_bonus": 0.08},
}
KNOCKDOWN_RULES = {"boxing": {"per_round_limit": 3, "per_fight_limit": None}, "kickboxing": {"per_round_limit": 3, "per_fight_limit": None},
                   "muay_thai": {"per_round_limit": 3, "per_fight_limit": None}, "lethwei": {"per_round_limit": 3, "per_fight_limit": 4},
                   "mma": {"per_round_limit": None, "per_fight_limit": None}, "street": {"per_round_limit": None, "per_fight_limit": None}}
REST_S = {"boxing": 60, "kickboxing": 60, "muay_thai": 120, "mma": 60, "street": 0, "lethwei": 120}

# ---------------------------------------------------------------- positions and transitions
STYLE_POS = [("leg_entanglement", "ground", "ground", ["bottom", "top"], {"bottom": 0.5, "top": 0.0})]
STYLE_TR = [
    ("closed_guard", "bottom", "leg_entry", "leg_entanglement", "bottom", "sweep_ground", ["pass_guard"]),
    ("half_guard", "bottom", "leg_entry", "leg_entanglement", "bottom", "sweep_ground", ["pass_guard"]),
    ("half_guard", "top", "leg_entry", "leg_entanglement", "bottom", "control", ["leg_pummel_escape"]),
    ("scramble", "neutral", "leg_entry", "leg_entanglement", "bottom", "scramble", []),
    ("leg_entanglement", "top", "leg_pummel_escape", "standing_neutral", "neutral", "stand_up", ["heel_hook"]),
    ("leg_entanglement", "top", "pass_guard", "half_guard", "top", "pass", ["leg_entry"]),
]
STYLE_OUTCOME_TR = [
    ("leg_entanglement", "bottom", "heel_hook", "scramble", "neutral", "submission", [], "failed attempt (defender escaped): both scramble"),
    ("leg_entanglement", "bottom", "toe_hold", "half_guard", "bottom", "submission", [], "failed attempt (defender escaped): defender settles on top in half guard"),
    ("leg_entanglement", "bottom", "ankle_lock", "half_guard", "bottom", "submission", [], "failed attempt (defender escaped): defender settles on top in half guard"),
]

# ---------------------------------------------------------------- combinations
STYLE_COMBOS = [
    ("tkd_cut_round", ["cut_kick", "fast_roundhouse"], "taekwondo", 0.07, 2),
    ("tkd_round_to_head", ["fast_roundhouse", "instep_head_kick"], "taekwondo", 0.06, 2),
    ("tkd_bounce_double", ["bounce_step", "double_roundhouse"], "taekwondo", 0.05, 2),
    ("capoeira_esquiva_rasteira", ["esquiva", "rasteira"], "capoeira", 0.10, 2),
    ("capoeira_negativa_rasteira", ["negativa", "rasteira"], "capoeira", 0.10, 2),
    ("capoeira_ginga_armada", ["ginga", "armada"], "capoeira", 0.06, 2),
    ("capoeira_queixada_compasso", ["queixada", "meia_lua_de_compasso"], "capoeira", 0.06, 2),
    ("catch_crossface_crank", ["cross_face", "neck_crank"], "catch_wrestling", 0.08, 2),
    ("catch_entry_heel_hook", ["leg_entry", "heel_hook"], "catch_wrestling", 0.08, 2),
    ("catch_snap_crank", ["snap_down", "neck_crank"], "catch_wrestling", 0.07, 2),
    ("lethwei_cross_headbutt", ["cross", "lunging_headbutt"], "lethwei", 0.06, 2),
    ("lethwei_headbutt_knee", ["clinch_headbutt", "knee_head_clinch"], "lethwei", 0.07, 2),
    ("wing_chun_pak_chain", ["pak_sao", "chain_punch"], "wing_chun", 0.10, 2),
    ("wing_chun_lap_chain", ["lap_sao", "chain_punch"], "wing_chun", 0.10, 2),
    ("hung_gar_bridge_claw", ["bridge_smash", "tiger_claw"], "hung_gar", 0.08, 2),
    ("baji_stomp_elbow", ["stomp_thrust_punch", "top_elbow"], "bajiquan", 0.07, 2),
    ("baji_elbow_lean", ["top_elbow", "iron_mountain_lean"], "bajiquan", 0.08, 2),
    ("bagua_circle_palm", ["circle_walk", "single_palm_change"], "baguazhang", 0.07, 2),
    ("bagua_palm_throw", ["single_palm_change", "turning_throw"], "baguazhang", 0.07, 2),
    ("tai_chi_redirect_palm", ["push_hands_redirect", "brush_knee_palm"], "tai_chi", 0.10, 2),
    ("tai_chi_redirect_push", ["push_hands_redirect", "fa_jin_push"], "tai_chi", 0.10, 2),
    ("shuai_catch_dump", ["kick_catch", "caught_kick_dump"], "shuai_jiao", 0.10, 2),
    ("shuai_trip_throw", ["kick_into_throw", "quick_grip_throw"], "shuai_jiao", 0.07, 2),
    ("jkd_intercept_stop_kick", ["lead_straight_intercept", "oblique_kick"], "jeet_kune_do", 0.07, 2),
    ("jkd_trap_blast", ["pak_sao", "chain_punch"], "jeet_kune_do", 0.10, 2),
    ("jkd_finger_jab_cross", ["finger_jab", "cross"], "jeet_kune_do", 0.08, 2),
]
