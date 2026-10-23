"""Compile `LBN-2.3-ADV v3` (10s Pillar Fight with Kawarimi Substitution, Props & Force-Event Melee)
into the LATENT SAKUGA Causal-Readability Arms:
  1. `lbn23_pillar_fight_arm_C1_contract.txt` (6-Layer Scene Contract with Prop Ledger & Kawarimi Stand-In)
  2. `lbn23_pillar_fight_arm_D_scene_stack.txt` (2-Layer Scene Stack: Header + Layer 1 Synchronized Timeline + Layer 2 JSON Scene Graph)
  3. `lbn23_pillar_fight_arm_C3_tight.txt` (Ultra-Tight HARD-Invariant Floor, Zero Digits)
  4. `lbn23_pillar_fight_intent_ir_and_trace.json` (Full Loss-Audited Trace + Internal Biomechanics)
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, List

PROMPT_DIR = Path(__file__).parent / "prompts"
ORIG_COMPILER_PATH = Path(__file__).resolve().parent.parent.parent / "scripts" / "sakuga_compiler.py"


def _load_sakuga_compiler() -> Any:
    spec = importlib.util.spec_from_file_location("sakuga_compiler_gold", ORIG_COMPILER_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_lbn23_pillar_fight() -> Dict[str, Any]:
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)

    shot_contract = (
        "10s anime fight clip, 24fps, moonlit stone courtyard ninja arena with a tall carved stone pillar rising vertically on the right-center stage plane, "
        "drifting night mist, crisp silver moonlight rim-lighting, and deep indigo courtyard shadows. "
        "STYLE: Pure 2D cel-shaded hand-drawn anime, high-speed shinobi martial-arts sakuga animation on twos, crisp angular anatomical linework, "
        "flat two-tone high-contrast cel shadows, heavy anatomical ink outlines on Fighter A and Fighter B, broken sketchy ink on active smear limbs and rope-dart whip arcs only, "
        "clean ultra-thick ink on impact holds. Not 3D, not CGI, not live action, not photoreal. "
        "SCREEN GEOMETRY LOCK: Maintain strict 180-degree front-hemisphere camera geometry (zero camera-cut axis flips) — Fighter A starts on screen-left, physically crosses behind B at 4.40s, "
        "plants on the right-side stone pillar at 7.00s, and rebounds to finish on screen-left over prone Fighter B on screen-right, with zero on-screen text, numbers, or HUD."
    )

    state_and_props_contract = (
        "ENTITY COUNT, OUTFIT & PROP CONTINUITY LOCK: Exactly TWO shinobi fighters and SIX tracked props with strict single-instance conservation (never duplicated, never teleported). "
        "Fighter A (agile shinobi striker): dark high-collar shinobi flak coat trailing behind, forearm wraps, dark shinobi trousers, strapped sandals; begins inverted high in mid-air above the stone pillar with rope dart holstered at left hip, smoke pellet at waist, and wooden substitution log concealed inside coat. "
        "Fighter B (heavy armored rogue shinobi): sleeveless charcoal combat vest over scarred broad shoulders, reinforced forearm bracers, dark hakama trousers; begins grounded at the base of the courtyard holding the single iron kunai in reverse grip in his right hand and three steel shuriken holstered in his right thigh pouch. "
        "PROP LEDGER INVARIANTS (6 TRACKED PROPS): "
        "(1) SINGLE KUNAI: Held by B in reverse grip (0.00s-2.00s, with a feint slash at 0.50s as A lands on the pillar top, then hurled sharply upward by B at 2.00s) -> kicked and deflected spinning high into the air by A's right foot after a 0.50s flight (2.50s) -> caught falling out of the air by A's right hand (6.60s-8.00s) -> driven by A's right hand deep into B's right shoulder where it stays embedded to the end (8.50s-10.00s). "
        "(2) SINGLE ROPE DART: Holstered at A's left hip (0.00s-3.00s) -> drawn into A's left hand on crouch landing (3.00s) -> whipped by A's left hand to wrap tightly around B's right shoulder (7.50s-7.60s) -> pulled taut to drag B toward the pillar and slam him (8.00s-10.00s). "
        "(3) SINGLE SMOKE PELLET: Carried at A's waist (0.00s-3.70s) -> detonated at 3.70s in a crisp white smoke burst to trigger the Kawarimi substitution. "
        "(4) WOODEN SUBSTITUTION LOG (KAWARIMI STAND-IN): Concealed in A's coat (0.00s-3.70s) -> stands upright as a full-body-height wooden stand-in in A's exact spot (3.70s-4.40s) to absorb B's right palm strike at 4.00s before toppling to the stone floor as A reappears behind B at 4.40s. "
        "(5) THREE SHURIKEN: Holstered on B's right thigh (0.00s-5.50s) -> thrown in a downward fan volley by B while airborne (5.50s) -> pass cleanly over A's low ground slide (5.90s) and embed firmly into the stone pillar face (6.30s-10.00s). "
        "(6) STONE PILLAR: Solid vertical stone column anchored on the right-center stage plane from floor to 8 meters high; A lands near its top and sprints straight down its vertical face (0.60s-1.60s), three shuriken embed into its stone face (6.30s), and B hurls A's body against its right-side face where A's feet plant to rebound (7.00s)."
    )

    observation_contract = (
        "CAMERA & SILHOUETTE VISIBILITY CONTRACT: Every beat must account for all nineteen body parts (head, torso, pelvis, upper-arms, forearms, hands, thighs, shins, and feet) with both left and right arms clearly separate from the torso in silhouette. "
        "Execute dynamic front-hemisphere Sakuga camera choreography: high-angle crane drop following A's inverted descent onto the pillar (0.0s-0.6s), vertical tracking tilt as A sprints down the pillar face and launches off (0.6s-1.6s), "
        "tight low-angle profile hold on A's right-foot kunai deflection spark (2.5s), wide low static framing exposing the smoke burst, upright wooden log stand-in, B's palm strike into the log, and A's reappearance behind B (3.7s-4.4s), "
        "medium-close side profile on A's rising right knee into B's spine (4.7s), low tracking dolly as A slides underneath the airborne shuriken volley and cartwheels left (5.5s-6.3s), "
        "tight close-up on B's two-hand catch on A's left elbow and circular throw into the pillar face (6.6s-7.0s), medium tracking shot on A's rope-dart wrap around B's right shoulder and taut drag (7.5s-8.2s), "
        "slow-motion tight profile impact on A driving the kunai into B's right shoulder (8.5s), ground-level wide shockwave framing as A slams B prone into the courtyard stones (8.75s-9.0s), and slow dolly-in on A's final low crouch over prone B (9.0s-10.0s)."
    )

    contract_beats: List[str] = [
        "- Beat 1 (0.00s-1.60s | INVERTED DROP, KUNAI FEINT & VERTICAL PILLAR SPRINT): [View: high-angle crane drop transitioning to vertical tracking tilt down the stone pillar face] "
        "A begins coiled upside-down high in mid-air above the courtyard with both arms extended overhead and both legs tucked, while B stands grounded below in a wide guard holding the single iron kunai in reverse grip in his right hand. "
        "At 0.50s, B whips his right arm forward in a sharp upward kunai feint to track A's descent; at 0.60s, A lands both feet high on the vertical face of the stone pillar, turns upright with his coat trailing, and sprints straight down the vertical pillar face from 0.60s to 1.60s toward B. "
        "[License: vertical descent streak on A's drop only; keep A's inverted silhouette, B's tracking arm, and the vertical pillar sprint crisp and solid; puff of stone dust at 0.60s pillar foot-plant]",

        "- Beat 2 (1.60s-3.00s | PILLAR LAUNCH, 2.00s UPWARD KUNAI THROW, 2.50s MID-AIR FOOT DEFLECTION & CROUCH LANDING): [View: fast tracking push-in locking into a tight low-angle profile impact frame at 2.50s] "
        "At 1.60s, A kicks off the stone pillar face into a fast ballistic dive toward B; at 2.00s, B twists his torso and hurls the single kunai sharply upward at diving A. "
        "At 2.50s (after a fast 0.50s upward blade flight), before the rising kunai can intersect A's torso, A twists his hips in mid-air with his left leg tucked and whips his extended right foot flat across the blade — A's right foot strikes the kunai cleanly in profile (strike contact clearly visible with zero torso overlap), deflecting the single kunai spinning end-over-end high into the air above the courtyard. "
        "At 3.00s, A lands on both feet in a low grounded crouch and draws the rope dart from his left hip into his left hand while B braces his forearms forward. "
        "[License: brief broken-ink smear on A's kicking right leg during the 2.30s-2.50s swing only; restore solid anatomy at 2.50s contact, punctuate with a 3-frame hit-stop hold and bright metallic spark ring AFTER foot-to-kunai contact, and clear the spark immediately so the upward-spinning kunai trajectory stays visible]",

        "- Beat 3 (3.70s-4.40s | KAWARIMI WOODEN LOG SUBSTITUTION & B PALM STRIKE INTO STAND-IN LOG): [View: wide low front-hemisphere framing keeping the substitution spot and B's strike lane completely unobstructed] "
        "At 3.70s, A detonates his waist smoke pellet and vanishes in a crisp puff of white smoke, leaving an upright full-body-height wooden substitution log standing directly in A's place as a physical stand-in so the frame never suffers a missing-actor gap. "
        "At 4.00s, B lunges forward and drives a heavy open-palm strike with his right hand squarely into the chest of the wooden substitution log (strike contact clearly visible against the bark); only after B's palm impacts the log does the log shudder and tip toward the stones while A materializes crouched directly behind B's flank at 4.40s with both feet planted. "
        "[License: crisp expanding smoke ring at 3.70s that clears immediately to reveal the solid wooden log before B's 4.00s palm strike; zero ghost limbs or half-merged bodies]",

        "- Beat 4 (4.55s-5.10s | FE1 RISING RIGHT KNEE TO SPINE & INVERTED BACKFLIP APEX): [View: medium-close side-profile framing exposing A's rising knee and B's spine, craning up with A's backflip] "
        "From his crouched reappearance behind B at 4.55s, A plants his left pillar leg, coils his torso with his left forearm in high guard and right fist extended back for counterbalance, and at 4.70s drives his bent right knee forcefully upward and forward into B's mid-spine; "
        "A's right knee connects cleanly against B's spine (strike contact clearly visible in side profile), and only after contact at 4.72s does B's spine flex forward, his torso fold, his arms fling forward, and both feet lift off the stones as B is launched airborne. "
        "Riding the upward rebound from 4.70s to 5.10s, A whips into a full backward somersault, reaching an inverted head-down apex above the courtyard with both legs tucked. "
        "[License: keep A's bent striking knee, standing left leg, head, and torso razor-sharp with zero knee smear blur; punctuate 4.70s contact with a 3-frame hit-stop hold and blunt shock ring AFTER knee-to-spine impact, then allow a clean rotational tuck streak along A's 4.90s-5.10s backflip arc]",

        "- Beat 5 (5.50s-6.30s | AIRBORNE SHURIKEN VOLLEY, LOW GROUND SLIDE & LEFT CARTWHEEL RECOVERY): [View: low lateral tracking dolly following A's slide under the shuriken trajectories to the stone pillar] "
        "At 5.50s, while still suspended mid-air from the knee launch, B twists his torso and hurls a fan volley of three steel shuriken from his right hand downward toward A. "
        "Landing from his backflip at 5.90s, A drops his pelvis low to the flagstones with both legs extended flat and slides smoothly underneath the incoming shuriken trajectories; at 6.30s, the three shuriken pass over A's back and embed firmly into the stone pillar face as B lands in a braced crouch, while A plants his left hand on the stones and executes a crisp ninety-degree forward cartwheel to his left to springs back up facing B. "
        "[License: straight metallic glint trails on the three flying shuriken and a low dust trail behind A's sliding heels; keep all four limbs distinct during the 6.30s left-hand cartwheel plant]",

        "- Beat 6 (6.60s-7.05s | FE2 TWO-HAND ELBOW CATCH, WRING LOCK & THROW INTO STONE PILLAR): [View: tight close-up on the elbow bind at 6.60s-6.80s whip-panning in profile to the stone pillar impact at 7.00s] "
        "As A lunges in from his cartwheel at 6.60s while snatching the falling kunai out of the air with his right hand, B plants his right foot, coils his heavy torso, and clamps both hands around A's incoming left elbow at 6.80s (acquire grapple contact clearly visible with both of B's hands locked on A's left elbow joint); "
        "immediately after the 6.80s lock, A's left elbow is pinned, his torso is wrenched sideways, and his feet lift off the floor as B pivots circularly through 7.00s and hurls A across the courtyard into the stone pillar face, where A absorbs the collision by planting both feet flat against the vertical stone column. "
        "[License: 2-frame grapple lock pause at 6.80s, fast ballistic streak on A's thrown trajectory from 6.90s-7.00s while B's throwing stance stays solid, and a 3-frame hit-stop hold with stone-crack dust burst AFTER A's feet slam onto the pillar face at 7.00s]",

        "- Beat 7 (7.50s-8.20s | ROPE-DART SHOULDER WRAP & FE4 TAUT TETHER DRAG): [View: medium-close tracking shot keeping the taut rope-dart line between A's left hand and B's right shoulder unbroken] "
        "Rebounding off the stone pillar at 7.50s, A whips the rope dart from his left hand across the gap; at 7.60s, the rope dart wraps tightly around B's right shoulder (acquire tether contact clearly visible with metallic wrap spark). "
        "At 8.00s, A lands grounded on his planted left foot holding the captured kunai in his right hand, anchors the taut rope-dart line in his extended left hand, and wrenches backward and rotational-forward through 8.20s — pulling the rope taut and dragging B's stumbling body forward toward the base of the pillar. "
        "[License: whip-arc smear on the rope-dart cord between 7.40s-7.50s only; once wrapped at 7.60s, keep the taut rope line crisp and continuous between A's left hand and B's right shoulder]",

        "- Beat 8 (8.30s-9.05s | FE3 KUNAI DRIVE INTO RIGHT SHOULDER & FE4 FULL-BODY GROUND SLAM): [View: tight slow-motion side-profile impact frame at 8.50s widening to a ground-level shockwave view at 8.75s-9.00s] "
        "As B is dragged off-balance into close range at 8.30s, A coils his torso with his left arm holding tension and drives the single iron kunai in his right fist downward and forward at 8.42s; at 8.50s, A's kunai penetrates deep into B's right shoulder (penetrate strike contact clearly visible in profile), causing B's shoulder to jerk and his head to snap back at 8.53s while the kunai remains embedded in B's right shoulder. "
        "Without resetting momentum, A uses the taut rope-dart tether and his downward body weight at 8.75s to slam B's entire body violently into the stone courtyard floor (release/slam contact clearly visible); at 8.77s, B's body compresses flat against the flagstones with limbs splayed and remains prone and motionless from 9.00s to 10.00s (B never stands after the knockdown). "
        "[License: brief slow-motion window (8.40s-8.60s) with a 4-frame hit-stop hold and crimson/white impact spark strictly AFTER the kunai enters B's right shoulder at 8.50s, followed at 8.75s-9.00s by a 5-frame ground-slam hit-stop hold and expanding radial stone-dust shockwave ring AFTER B's torso hits the floor]",
    ]

    animation_license = (
        "SAKUGA FX, SMEAR & HIT-STOP LAYER: Contrast brief coiled anticipation holds (2.40s pre-deflect, 4.55s pre-knee, 6.60s pre-throw, 8.30s pre-kunai) with whip-fast transfers and heavy multi-frame impact holds (2.50s, 4.70s, 7.00s, 8.50s, 9.00s). "
        "Restrict broken-ink smear stretching strictly to the active striking limb or rope-dart cord during transfer; keep heads, torsos, standing pillar legs, and non-striking guards razor-sharp and solid, restoring full anatomical proportions immediately at contact. "
        "Fire all spark rings, smoke bursts, and radial floor-dust shockwaves strictly AT or AFTER visible contact and clear them immediately so the physical recoil and prop ownership remain unobstructed. "
        "NEGATIVE GUARDRAILS: no missing limbs, no limb merging or L/R swapping during spins/somersaults/cartwheels, no kawarimi vanish without the full-body wooden substitution log stand-in, no duplicated or teleporting kunai, no reaction before contact, no stance reset between the 8.50s kunai impale and 8.75s floor slam, no B standing up after the 8.77s ground-slam knockdown."
    )

    closure_contract = (
        "From 9.00s to 10.00s, end on a slow dolly-in as Fighter A holds a low, balanced shinobi crouch on screen-left with both feet planted flat, left hand relaxed forward, and both arms clearly separate from his torso in silhouette, "
        "while Fighter B lies prone and motionless face-down on the flagstones on screen-right with the single kunai still embedded in his right shoulder and the three shuriken embedded in the stone pillar behind them as courtyard dust settles in the moonlight."
    )

    # 1. Build Arm C1 (6-Part Directorial Scene Contract)
    arm_c1_text = (
        f"SHOT & STYLE CONTRACT\n{shot_contract}\n\n"
        f"ENTITY, PROP LEDGER & INITIAL STATE\n{state_and_props_contract}\n\n"
        f"CAMERA & OBSERVATION LAYER\n{observation_contract}\n\n"
        f"SYNCHRONIZED CAUSAL BEATS (Preparation -> Commitment -> Named Contact -> Consequence -> Recovery)\n"
        + "\n".join(contract_beats)
        + f"\n\nSAKUGA FX & ANIMATION LICENSE LAYER\n{animation_license}\n\n"
        f"TERMINAL CLOSURE\n{closure_contract}"
    )

    # 2. Build Arm D (2-Layer Scene Stack: Header + Layer 1 Synchronized Timeline + Layer 2 JSON Scene Graph)
    layer1_lines = [
        "MOVEMENT LANGUAGE: <timestamp> <exchange>: SUPPORT & WEIGHT TRANSFER (grounded/pillar/airborne support; NO SUPPORT = airborne) | "
        "ALL-19-PARTS 4-LIMB SILHOUETTE (head, torso, pelvis, L_arm, R_arm, L_leg, R_leg — every limb tracked, Kawarimi uses full-body wooden log stand-in at 3.70s-4.40s) | "
        "PROP LEDGER STATE (kunai, rope_dart, smoke_pellet, substitution_log, 3_shuriken, pillar) | "
        "SYNCHRONIZED CAUSE -> CONTACT -> POST-CONTACT REACTION.",
        "0.00s-0.60s E01 (INVERTED_DROP_AND_PILLAR_SPRINT vs REVERSE_GRIP_KUNAI_THROW): "
        "A [0.00s NO SUPPORT airborne inverted high above pillar -> 0.60s SUPPORT both feet planted high on vertical stone pillar face, sprinting straight down | head forward, torso forward, pelvis level, L_arm:back extended open, R_arm:forward extended open, L_leg:forward planted flat, R_leg:back extended pushing] "
        "<-> B [SUPPORT both feet planted wide on courtyard floor | head forward, torso forward twist, L_arm:forward folded open, R_arm:forward extended open throwing upward, L_leg:forward planted flat, R_leg:back planted flat] | "
        "PROPS [kunai: B_right_hand reverse_grip -> 0.50s thrown upward in flight toward A; rope_dart: A_left_hip; smoke_pellet: A_waist; substitution_log: A_coat; 3_shuriken: B_right_thigh] | "
        "EVENT: B hurls the single kunai upward at 0.50s as A lands high on the stone pillar at 0.60s and sprints straight down its vertical face toward B.",
        "1.60s-3.00s E02 (AIRBORNE_FOOT_KUNAI_DEFLECT_AND_CROUCH_LAND vs UPWARD_THROW_FOLLOW_THROUGH): "
        "A [1.60s pushes off pillar -> NO SUPPORT airborne diving arc -> 2.50s mid-air side-twist kick -> 3.00s SUPPORT both feet planted in low crouch | at 2.50s: head forward, torso side-twist, L_arm:out extended open, R_arm:forward folded fist, L_leg:tucked folded pointed, R_leg:extended flat striking kunai] "
        "<-> B [SUPPORT both feet planted | R_arm extended high in throw follow-through -> 2.60s both arms braced forward-high] | "
        "PROPS [kunai: 2.50s deflected upward spinning end-over-end by A's right foot; rope_dart: 3.00s drawn from A_left_hip into A_left_hand] | "
        "EVENT (STRIKE / DEFLECT): At 2.50s (hold 3f), A's extended right foot strikes the incoming kunai mid-air in clear profile, deflecting it spinning high into the air with a metallic spark ring; at 3.00s A lands in a low crouch and draws the rope dart into his left hand.",
        "3.70s-4.40s E03 (KAWARIMI_WOODEN_LOG_SUBSTITUTION vs B_PALM_STRIKE_INTO_LOG): "
        "A [3.70s cpcs:absent via Kawarimi smoke burst; FULL-BODY UPRIGHT WOODEN SUBSTITUTION LOG stands in A's exact place from 3.70s-4.40s -> 4.40s A reappears crouched behind B's flank with SUPPORT both feet planted | L_arm:forward folded open, R_arm:forward folded open, L_leg:forward planted flat, R_leg:back planted flat] "
        "<-> B [SUPPORT both feet planted | 4.00s torso twists forward, L_arm:back folded fist, R_arm:forward extended open palm striking log, L_leg:forward planted, R_leg:back planted] | "
        "PROPS [smoke_pellet: 3.70s deployed white smoke burst; substitution_log: 3.70s stands upright in A's place -> 4.00s struck by B's right palm -> 4.40s tips to floor] | "
        "EVENT (SUBSTITUTE & STRIKE): At 3.70s A vanishes in smoke and the upright wooden log stands in his place; at 4.00s B drives a heavy right palm strike into the wooden log (not A), and at 4.40s A reappears crouched directly behind B.",
        "4.55s-5.10s E04 (FE1_RISING_RIGHT_KNEE_TO_SPINE_AND_BACKFLIP vs B_LAUNCHED_AIRBORNE): "
        "A [4.55s FE1 windup on planted left leg -> 4.65s hip-to-knee upward drive -> 4.70s FE1 CONTACT right knee into B's spine -> 4.70s-5.10s NO SUPPORT airborne 360-degree backward somersault to inverted apex | at 4.70s: L_arm:guard folded open, R_arm:back extended fist, L_leg:forward planted flat, R_leg:forward folded knee driving up; at 5.10s: inverted head down, both arms overhead extended, both legs tucked] "
        "<-> B [4.70s-4.72s NO SUPPORT launched airborne by knee impact | spine flexes forward, torso folds, both feet lift off floor, both arms fling forward] | "
        "PROPS [kunai: spinning at high apex above courtyard; rope_dart: retained in A_left_hand] | "
        "EVENT (FE1 STRIKE): At 4.70s (hold 3f), A drives his rising right knee into B's spine; only after contact at 4.72s does B fold forward and launch off his feet while A rebounds into an inverted backflip at 5.10s.",
        "5.50s-6.30s E05 (LOW_GROUND_SLIDE_AND_LEFT_CARTWHEEL vs AIRBORNE_SHURIKEN_VOLLEY_INTO_PILLAR): "
        "A [5.90s SUPPORT both feet sliding low across flagstones under shuriken -> 6.30s left hand plants for 90-degree forward cartwheel left | at 5.90s: pelvis low, both arms forward folded, both legs extended flat sliding; at 6.30s: torso side-inverted, L_arm:down planted, R_arm:overhead extended, L_leg:tucked, R_leg:extended] "
        "<-> B [5.50s NO SUPPORT airborne twisting torso, R_arm extended throwing 3 shuriken downward -> 6.30s SUPPORT both feet land in braced crouch] | "
        "PROPS [3_shuriken: 5.50s thrown by B in flight -> 5.90s pass over A's low slide -> 6.30s embed firmly into stone pillar face] | "
        "EVENT (EVASION): At 5.50s airborne B throws three shuriken; at 5.90s A slides flat underneath the volley as the three shuriken embed into the stone pillar at 6.30s, and A cartwheels left onto his feet.",
        "6.60s-7.05s E06 (AIRBORNE_KUNAI_CATCH_AND_PILLAR_WALL_PLANT vs FE2_TWO_HAND_ELBOW_CATCH_AND_THROW): "
        "A [6.60s lunges in while R_hand catches falling kunai mid-air -> 6.80s left elbow locked by B, feet lifted off ground -> 7.00s hurled into stone pillar face, SUPPORT both feet plant flat on vertical pillar face | at 7.00s: head back, torso extended, both arms back extended, both legs forward planted on pillar] "
        "<-> B [6.60s FE2 windup -> 6.65s plants right foot, drives both hands to A's left elbow -> 6.80s FE2 CONTACT both hands lock A's left elbow -> 7.00s-7.05s circular hip-and-shoulder throw hurling A into pillar] | "
        "PROPS [kunai: 6.60s caught falling mid-air by A_right_hand and retained; pillar: 7.00s absorbs A's wall-plant impact] | "
        "EVENT (FE2 ACQUIRE & THROW): As A catches the falling kunai in his right hand at 6.60s, B clamps both hands onto A's left elbow at 6.80s (hold 2f) and hurls A circularly into the stone pillar face at 7.00s (hold 3f), where A plants both feet against the stone.",
        "7.50s-8.20s E07 (ROPE_DART_SHOULDER_WRAP_AND_FE4_TAUT_DRAG vs B_DRAGGED_TOWARD_PILLAR): "
        "A [7.50s rebounds off pillar -> 7.60s L_hand whips rope dart wrapping B's right shoulder -> 8.00s-8.20s SUPPORT grounded on planted left foot, FE4 drive pulling taut rope dart to drag B | L_arm:forward extended holding taut rope, R_arm:back extended fist holding kunai, L_leg:forward planted flat, R_leg:back extended] "
        "<-> B [7.60s right shoulder wrapped by rope dart -> 8.00s-8.20s SUPPORT feet stumbling forward as body is dragged toward pillar, both arms back extended] | "
        "PROPS [rope_dart: 7.60s wraps tightly around B_right_shoulder and remains taut to 10.00s; kunai: held ready in A_right_hand] | "
        "EVENT (ACQUIRE & MAINTAIN TETHER): At 7.50s-7.60s (hold 2f), A whips the rope dart from his left hand to wrap B's right shoulder, then lands at 8.00s-8.20s and drags B forward along the taut tether toward the pillar.",
        "8.30s-9.05s E08 (FE3_KUNAI_SHOULDER_IMPALE_AND_FE4_FLOOR_SLAM vs B_IMPALED_AND_SLAMMED_PRONE): "
        "A [8.30s FE3 windup coiling torso -> 8.42s plants left foot, drives R_hand kunai down-forward -> 8.50s FE3 CONTACT kunai penetrates B's right shoulder -> 8.75s FE4 CONTACT full-body downward slam driving B into stone floor -> 9.00s SUPPORT both feet in low shinobi crouch] "
        "<-> B [8.50s-8.53s right shoulder impaled by kunai, torso jerks, head snaps back -> 8.75s-8.77s slammed flat into stone floor with dust burst -> 9.00s-10.00s SUPPORT prone motionless on floor] | "
        "PROPS [kunai: 8.50s driven by A_right_hand into B_right_shoulder where it remains embedded through 10.00s; rope_dart: taut between A_left_hand and B_right_shoulder] | "
        "EVENT (FE3 PENETRATE & FE4 SLAM): At 8.50s (hold 4f, slow-motion), A drives the kunai deep into B's right shoulder where it stays embedded; without resetting stance, A wrenches the taut rope dart at 8.75s-9.00s (hold 5f) to slam B's body prone into the flagstones with a radial dust shockwave.",
        "9.00s-10.00s TERMINAL_HOLD: A [SUPPORT low shinobi crouch on screen-left facing right | both feet planted flat, both arms separate from torso in silhouette] "
        "<-> B [SUPPORT prone motionless on stone floor on screen-right | kunai embedded in right shoulder, never stands after knockdown] | "
        f"CLOSURE: {closure_contract}",
    ]

    layer2_scene_graph: Dict[str, Any] = {
        "name": "lbn23adv_10s_pillar_fight_latent_sakuga_stack",
        "schema": "LATENT-SAKUGA-SCENE-STACK-1.0",
        "fps": 24,
        "duration": 10.0,
        "environment_and_lighting": "moonlit stone courtyard ninja arena with an 8-meter vertical carved stone pillar on the right-center stage plane, drifting night mist, silver moonlight rim-lighting, and deep indigo shadows",
        "screen_geometry": "180_degree_camera_hemisphere_locked: A starts on screen_left, physically crosses behind B at 4.40s, plants on the right-side stone pillar at 7.00s, and rebounds to finish on screen_left over prone B on screen_right (zero camera-cut axis flips).",
        "body_invariants": "ALL_19_PARTS_PRESENT (head, torso, pelvis, upper-arm L/R, forearm L/R, hand L/R, thigh L/R, shin L/R, foot L/R). Occlusion allowed; deletion forbidden. At 3.70s-4.40s Kawarimi substitution, the upright full-body wooden substitution log stands in A's exact place so no limb or actor slot is missing.",
        "negative": (
            "no 3D CGI, no mocap stiffness, no floaty physics, no distant wide shots, no on-screen text or numbers, no HUD, "
            "no extra fighters, no cloned A or B, no extra props beyond 1 kunai, 1 rope dart, 1 smoke pellet, 1 substitution log, 3 shuriken, and 1 stone pillar, "
            "no missing limbs, no limb merge, no L/R limb swap, no limb duplication during spins/somersaults/cartwheels, "
            "no kawarimi vanish without the full-body wooden log stand-in, no kunai teleporting or duplication, "
            "no full-body blur during smears, no reaction before contact, no zero-width strikes, no stance reset between the 8.50s kunai impale and 8.75s floor slam, no B standing after the 8.77s ground-slam knockdown"
        ),
        "conservation_laws": [
            "CONSERVE_SEMANTICALLY: prioritize continuous shinobi weight transfer, 5-phase force-event width (windup -> drive -> contact -> reaction -> follow-through), weapon ownership continuity, and causal order over isolated poses",
            "single_kunai_ownership_continuity: B reverse-grip (0.00s-2.00s, feint at 0.50s, upward throw at 2.00s) -> A right-foot deflect upward spin after 0.50s flight (2.50s) -> A right-hand mid-air catch (6.60s) -> A drives into B right shoulder (8.50s) -> embedded in B right shoulder (8.50s-10.00s)",
            "kawarimi_full_body_stand_in: at 3.70s A vanishes in smoke and the upright wooden substitution log immediately occupies A's spot to receive B's 4.00s palm strike before A reappears behind B at 4.40s",
            "accent_after_contact_rule: impact sparks, smoke bursts, and radial dust rings fire strictly at or after visible contact and clear immediately so recoil and prop trajectories remain visible",
            "terminal_knockdown_law: B never stands upright after the 8.75s-8.77s ground slam and remains prone and motionless from 9.00s to 10.00s",
        ],
        "laban": {
            "A": {
                "fighting_style": "shinobi_acrobatic_melee_and_rope_dart",
                "chain": "E01_inverted_drop_and_pillar_sprint > E02_pillar_launch_and_foot_kunai_deflect > E03_kawarimi_log_swap_and_flank_reappear > E04_FE1_rising_right_knee_and_backflip > E05_low_slide_under_shuriken_and_left_cartwheel > E06_midair_kunai_catch_and_pillar_wall_plant > E07_rope_dart_shoulder_wrap_and_FE4_drag > E08_FE3_kunai_shoulder_impale_and_FE4_ground_slam > E09_low_crouch_final_hold",
                "effort": {"weight": "strong_snappy", "time": "sudden_explosive", "space": "direct_close_range", "flow": "continuous_recoil_bound_at_impacts"},
            },
            "B": {
                "fighting_style": "heavy_rogue_shinobi_weapons_and_grapple",
                "chain": "E01_reverse_grip_kunai_upward_throw > E02_upward_follow_through_and_brace > E03_palm_strike_into_substitution_log > E04_FE1_spine_struck_launched_airborne > E05_airborne_three_shuriken_volley_and_land > E06_FE2_two_hand_elbow_catch_and_pillar_throw > E07_right_shoulder_wrapped_and_dragged > E08_FE3_shoulder_impaled_and_FE4_slammed_prone > E09_prone_motionless_final",
                "effort": {"weight": "heavy_crushing", "time": "sustained_to_sudden", "space": "direct", "flow": "bound"},
            },
        },
        "prop_tracks": {
            "kunai": [
                {"t": "0.00s", "owner": "B_right_hand", "state": "held in reverse grip"},
                {"t": "0.50s", "owner": "airborne_flight", "state": "thrown upward by B toward descending A"},
                {"t": "2.50s", "owner": "airborne_deflected", "state": "struck by A's right foot and deflected spinning end-over-end high above the courtyard"},
                {"t": "6.60s", "owner": "A_right_hand", "state": "caught falling out of the air by A's right hand during grapple entry"},
                {"t": "8.50s-10.00s", "owner": "B_right_shoulder_embedded", "state": "driven deep into B's right shoulder by A's right hand and retained embedded in B's shoulder to 10.00s"},
            ],
            "rope_dart": [
                {"t": "0.00s-3.00s", "owner": "A_left_hip", "state": "holstered at A's left hip"},
                {"t": "3.00s-7.50s", "owner": "A_left_hand", "state": "drawn into A's left hand on crouch landing"},
                {"t": "7.60s-10.00s", "owner": "A_left_hand_to_B_right_shoulder", "state": "wrapped tightly around B's right shoulder and pulled taut by A's left hand to drag and slam B"},
            ],
            "smoke_pellet_and_substitution_log": [
                {"t": "0.00s-3.70s", "owner": "A_waist_and_coat", "state": "carried by A"},
                {"t": "3.70s-4.40s", "owner": "courtyard_stand_in", "state": "smoke pellet bursts; upright full-body wooden substitution log stands in A's exact spot and absorbs B's 4.00s right palm strike"},
                {"t": "4.40s-10.00s", "owner": "courtyard_floor", "state": "log tips onto stones as A reappears behind B"},
            ],
            "shuriken_volley_3": [
                {"t": "0.00s-5.50s", "owner": "B_right_thigh_pouch", "state": "holstered"},
                {"t": "5.50s-6.30s", "owner": "airborne_volley", "state": "thrown downward by airborne B, passing over A's 5.90s low ground slide"},
                {"t": "6.30s-10.00s", "owner": "stone_pillar_embedded", "state": "all three shuriken embedded firmly in the stone pillar face"},
            ],
            "stone_pillar": [
                {"t": "0.60s-1.60s", "interaction": "A lands near top, sprints straight down vertical face, and kicks off"},
                {"t": "6.30s", "interaction": "three shuriken embed into pillar face"},
                {"t": "7.00s", "interaction": "B hurls A into pillar face; A plants both feet on pillar to rebound"},
            ],
        },
        "synchronized_exchanges": [
            {
                "t": "0.00s-0.60s",
                "exchange": "E01_inverted_drop_and_pillar_sprint_vs_kunai_throw",
                "A_state": "inverted airborne coil above pillar -> lands both feet on pillar face at 0.60s and sprints straight down",
                "contact": {"operation": "release_projectile_and_surface_plant", "visibility_target": "correct_visible", "event": "B releases reverse-grip kunai upward at 0.50s; A plants both feet on the stone pillar at 0.60s and sprints down"},
                "B_state": "grounded wide stance -> twists torso at 0.50s to throw kunai upward at A",
            },
            {
                "t": "1.60s-3.00s",
                "exchange": "E02_pillar_launch_and_midair_foot_kunai_deflect",
                "A_state": "launches off pillar face at 1.60s -> side-twist right-foot kick at 2.50s -> lands in grounded crouch at 3.00s drawing rope dart into left hand",
                "contact": {"operation": "strike_deflect", "visibility_target": "correct_visible", "event": "A's flat right foot strikes the rising kunai mid-air at 2.50s (hold 3f), deflecting it spinning high into the air"},
                "B_state": "completes upward throw follow-through -> braces both forearms forward at 2.60s",
            },
            {
                "t": "3.70s-4.40s",
                "exchange": "E03_kawarimi_wooden_log_stand_in_and_flank_reappear",
                "A_state": "vanishes in smoke at 3.70s leaving full-body upright wooden log stand-in -> reappears crouched behind B at 4.40s",
                "contact": {"operation": "strike_stand_in", "visibility_target": "correct_visible", "event": "B's right palm strikes the upright wooden substitution log at 4.00s (accent 3); log shudders and tips as A reappears behind B at 4.40s"},
                "B_state": "lunges forward at 4.00s driving right open palm into the substitution log",
            },
            {
                "t": "4.55s-5.10s",
                "exchange": "E04_FE1_rising_right_knee_to_spine_and_backflip",
                "A_state": "4.55s loads right knee and coils torso on planted left leg -> 4.65s drives hip-to-knee up-forward -> 4.70s strikes B's spine -> 4.70s-5.10s 360-degree backward somersault to inverted apex",
                "contact": {"operation": "strike", "visibility_target": "correct_visible", "event": "FE1 (4.55s-4.85s): A's right knee strikes B's mid-spine at 4.70s (hold 3f); at 4.72s B's spine flexes forward, torso folds, and feet lift airborne"},
                "B_state": "launched airborne at 4.70s-4.85s, spine flexed forward and arms flung forward",
            },
            {
                "t": "5.50s-6.30s",
                "exchange": "E05_airborne_shuriken_volley_vs_low_slide_and_cartwheel",
                "A_state": "5.90s slides low on flagstones underneath shuriken -> 6.30s plants left hand for 90-degree forward cartwheel left",
                "contact": {"operation": "projectile_embed", "visibility_target": "correct_visible", "event": "B throws three shuriken mid-air at 5.50s; A slides underneath at 5.90s; three shuriken embed into the stone pillar face at 6.30s"},
                "B_state": "5.50s throws three shuriken while airborne -> 6.30s lands in grounded brace",
            },
            {
                "t": "6.60s-7.05s",
                "exchange": "E06_FE2_two_hand_elbow_catch_and_throw_into_pillar",
                "A_state": "6.60s right hand catches falling kunai mid-air -> 6.80s left elbow locked by B -> 7.00s hurled into stone pillar face, planting both feet on the stone",
                "contact": {"operation": "acquire_and_throw", "visibility_target": "correct_visible", "event": "FE2 (6.60s-7.05s): B clamps both hands onto A's left elbow at 6.80s (hold 2f), wrenches A off his feet at 6.82s, and hurls A into the stone pillar face at 7.00s (hold 3f)"},
                "B_state": "6.60s loads both hands -> 6.80s locks A's left elbow -> 7.00s-7.05s circular throw follow-through",
            },
            {
                "t": "7.50s-8.20s",
                "exchange": "E07_rope_dart_shoulder_wrap_and_FE4_taut_drag",
                "A_state": "7.50s rebounds off pillar -> 7.60s wraps rope dart around B's right shoulder -> 8.00s-8.20s plants left foot and pulls taut rope dart to drag B toward pillar",
                "contact": {"operation": "acquire_and_maintain", "visibility_target": "correct_visible", "event": "Rope dart wraps B's right shoulder at 7.60s (hold 2f) and stays taut from A's left hand to B's right shoulder as A drags B at 8.00s-8.20s"},
                "B_state": "7.60s right shoulder captured by rope dart -> 8.00s-8.20s dragged forward off-balance toward pillar",
            },
            {
                "t": "8.30s-9.05s",
                "exchange": "E08_FE3_kunai_shoulder_impale_and_FE4_ground_slam",
                "A_state": "8.30s coils torso -> 8.42s drives right-hand kunai down-forward -> 8.50s impales B's right shoulder -> 8.75s slams B into stone floor -> 9.00s-10.00s settles in low crouch",
                "contact": {"operation": "penetrate_and_slam", "visibility_target": "correct_visible", "event": "FE3 (8.30s-8.60s): A drives kunai into B's right shoulder at 8.50s (hold 4f, slow-motion) where it remains embedded; FE4 (8.75s-9.05s): A slams B's body into the stone floor at 8.75s-9.00s (hold 5f) with radial dust burst"},
                "B_state": "8.53s shoulder impaled, torso jerks, head snaps back -> 8.77s compressed flat against stone floor -> 9.00s-10.00s prone motionless",
            },
        ],
        "camera": [
            {"t": "0.00s-0.60s", "shot": "high_angle_crane_drop_to_vertical_pillar_track", "framing": "tracks A's inverted drop onto the stone pillar top and vertical sprint down its face while keeping B's upward kunai throw visible below", "preserve_axis": True},
            {"t": "1.60s-2.50s", "shot": "fast_push_in_to_tight_low_angle_kunai_deflect", "framing": "exposes A's right foot striking and deflecting the kunai mid-air in clear profile", "preserve_axis": True, "accent_timing": "3-frame hit-stop hold and metallic spark ring strictly AFTER 2.50s foot-to-kunai contact"},
            {"t": "3.70s-4.40s", "shot": "wide_low_front_hemisphere_kawarimi_stage_view", "framing": "shows the 3.70s smoke burst, the upright full-body wooden log stand-in, B's 4.00s palm strike into the log, and A's 4.40s reappearance behind B", "preserve_axis": True},
            {"t": "4.70s-5.10s", "shot": "medium_close_side_profile_knee_strike_to_backflip_crane", "framing": "exposes A's rising right knee into B's spine at 4.70s and cranes up with A's 360-degree backflip apex at 5.10s", "preserve_axis": True, "accent_timing": "3-frame hit-stop hold and blunt shock ring strictly AFTER 4.70s knee-to-spine contact"},
            {"t": "5.50s-6.30s", "shot": "low_lateral_tracking_slide_and_cartwheel", "framing": "tracks A sliding flat underneath B's airborne three-shuriken volley at 5.90s and cartwheeling left at 6.30s as the shuriken embed in the pillar", "preserve_axis": True},
            {"t": "6.60s-7.00s", "shot": "tight_grapple_bind_to_profile_pillar_wall_slam", "framing": "shows A catching the falling kunai in his right hand as B locks A's left elbow with both hands at 6.80s and hurls A into the stone pillar face at 7.00s", "preserve_axis": True, "accent_timing": "2-frame grapple hold at 6.80s; 3-frame hit-stop hold and stone-crack dust burst strictly AFTER 7.00s pillar impact"},
            {"t": "7.50s-8.20s", "shot": "medium_close_rope_dart_wrap_and_taut_drag_track", "framing": "keeps the rope-dart wrap around B's right shoulder at 7.60s and the taut tether line between A's left hand and B's shoulder unobstructed", "preserve_axis": True},
            {"t": "8.50s-9.00s", "shot": "slow_motion_tight_profile_kunai_impale_to_wide_ground_slam_shockwave", "framing": "captures A driving the kunai into B's right shoulder in slow motion at 8.50s, then widens for the full-body floor slam at 8.75s-9.00s", "preserve_axis": True, "accent_timing": "slow-motion 0.25x window (8.40s-8.60s) with 4-frame hit-stop hold AFTER kunai impale, followed by 5-frame hit-stop hold and radial dust shockwave ring AFTER floor slam"},
            {"t": "9.00s-10.00s", "shot": "slow_dolly_in_terminal_crouch_over_prone_B", "framing": "locks on A's low shinobi crouch on screen-left and prone B on screen-right with the kunai embedded in B's shoulder as dust settles", "preserve_axis": True},
        ],
        "anime": {
            "style": "2D cel-shaded hand-drawn anime, flat two-tone shadows, heavy anatomical ink outlines, broken sketchy ink on active smear limbs only, ultra-thick clean ink on impact holds (2.50s, 4.70s, 7.00s, 8.50s, 9.00s)",
            "impact_moments": ["0.60s", "1.60s", "2.50s", "4.00s", "4.70s", "6.80s", "7.00s", "7.60s", "8.50s", "8.75s", "9.00s"],
            "smear_frames": [
                "0.00s-0.60s: A vertical drop streak toward pillar top only; A inverted body stays solid",
                "1.40s-1.60s: A ballistic push-off arc streak only; stone pillar stays solid",
                "2.30s-2.50s: A right leg deflect kick arc smear only; head, torso, and tucked left leg stay solid, restoring exact anatomy at 2.50s kunai contact",
                "4.55s-4.70s: ZERO smear on A's bent rising right knee (keep knee, standing left leg, and torso razor-sharp)",
                "4.90s-5.10s: A backward somersault tuck rotation streak only; courtyard floor stays solid",
                "5.70s-5.90s: A low ground slide speed streak only; flying shuriken and floor stay solid",
                "6.10s-6.30s: A left-cartwheel leg arc smear only; planted left arm and torso stay solid",
                "6.90s-7.00s: A thrown ballistic streak toward pillar only; B's throwing stance stays solid",
                "7.40s-7.50s: rope-dart whip arc smear only; A and B bodies stay solid",
                "8.30s-8.50s: A right-hand kunai drive streak only; B's right shoulder stays solid, restoring exact anatomy at 8.50s impale",
                "8.65s-8.75s: A downward slam transfer streak only; B's body compresses solidly against floor at 8.75s",
            ],
            "speed_lines": ["0.00s-0.60s", "1.40s-1.60s", "2.30s-2.50s", "4.90s-5.10s", "5.70s-5.90s", "6.90s-7.00s", "8.30s-8.50s", "8.65s-8.75s"],
            "time_remap": {"8.40s-8.60s": "0.25x slow-motion impact window as A drives the kunai into B's right shoulder"},
            "anticipation_holds": ["2.40s_pre_kunai_deflect_chamber", "4.55s_FE1_knee_windup_coil", "6.60s_FE2_elbow_catch_load", "8.30s_FE3_kunai_drive_coil"],
            "fx": {
                "0.60s": "stone_pillar_top_landing_dust_puff (fires AFTER A's feet plant on pillar)",
                "1.60s": "pillar_push_off_dust_burst (fires AFTER A launches off pillar face)",
                "2.50s": "kunai_deflect_metallic_spark_ring (fires strictly AFTER A's right foot strikes kunai and clears immediately)",
                "3.70s": "kawarimi_white_smoke_burst (clears immediately to reveal upright wooden substitution log stand-in)",
                "4.00s": "wood_bark_impact_shudder on substitution log (fires AFTER B's right palm strikes log)",
                "4.70s": "FE1_knee_spine_blunt_impact_shock_ring (fires strictly AFTER A's right knee hits B's spine and clears for B's airborne fold)",
                "5.90s": "ground_slide_flagstone_dust_trail",
                "6.30s": "three_shuriken_stone_pillar_embed_sparks_and_cartwheel_dust",
                "7.00s": "stone_pillar_wall_plant_crack_and_dust_burst (fires strictly AFTER A's feet slam onto pillar face)",
                "7.60s": "rope_dart_shoulder_wrap_metallic_spark",
                "8.50s": "FE3_kunai_shoulder_impale_crimson_and_white_spark_flash (fires strictly AFTER kunai penetrates B's right shoulder)",
                "8.75s-9.00s": "FE4_ground_slam_radial_shockwave_dust_ring (fires strictly AFTER B's body slams into courtyard flagstones)",
                "9.00s-10.00s": "settling_courtyard_dust_motes_and_moonlight_rim_glow",
            },
            "line_rule": "heavy anatomical ink outlines on A and B, broken/sketchy outlines ONLY on active smear limbs and rope-dart whip arc, ultra-thick clean ink on held impact moments ['2.50s', '4.70s', '7.00s', '8.50s', '9.00s']",
        },
        "rules": (
            f"{shot_contract} {state_and_props_contract} "
            "At 0.50s B throws the reverse-grip kunai upward as A lands on the stone pillar at 0.60s and sprints down its face; "
            "at 1.60s A launches off the pillar and at 2.50s deflects the kunai upward with his right foot before landing in a crouch at 3.00s and drawing his rope dart; "
            "at 3.70s A vanishes in a Kawarimi smoke burst leaving an upright full-body wooden log stand-in that absorbs B's 4.00s palm strike; "
            "at 4.40s A reappears crouched behind B and at 4.70s drives a rising right knee into B's spine (FE1), launching B airborne while A backflips at 5.10s; "
            "at 5.50s airborne B throws three shuriken as A slides underneath at 5.90s and cartwheels left at 6.30s while the shuriken embed in the pillar; "
            "at 6.60s A catches the falling kunai in his right hand as B catches A's left elbow with both hands at 6.80s (FE2) and throws A into the pillar face at 7.00s; "
            "at 7.50s-7.60s A wraps B's right shoulder with the rope dart, drags B toward the pillar at 8.00s-8.20s (FE4), drives the kunai into B's right shoulder at 8.50s (FE3), "
            "and slams B prone into the stone floor at 8.75s-9.00s (FE4). "
            + closure_contract
        ),
    }

    arm_d_text = (
        f"{shot_contract}\n{state_and_props_contract}\n\n"
        "=== LAYER 1: SYNCHRONIZED BILATERAL SUPPORT, 19-PART SILHOUETTE, PROP LEDGER & FORCE-EVENT TIMELINE ===\n"
        + "\n".join(layer1_lines)
        + "\n\n=== LAYER 2: LATENT-SAKUGA-SCENE-STACK KINEMATIC, PROP, CAMERA & ANIME FX SCENE GRAPH ===\n"
        + json.dumps(layer2_scene_graph, indent=2)
    )

    # 3. Build Arm C3 (Ultra-Tight HARD-Invariant Floor with Supporting Style/Prop/FX Contract, Zero Digits)
    arm_c3_text = (
        "Continuous hand-drawn anime ninja fight in a moonlit stone courtyard with a tall vertical stone pillar on the right-center plane — "
        "high-speed cel-shaded shinobi sakuga on twos, crisp angular anatomical linework, flat two-tone cel shadows, heavy anatomical ink outlines, broken sketchy ink on active smear limbs only, ultra-thick ink on impact holds. "
        "Two shinobi fighters and six strictly conserved props (single iron kunai, single rope dart, single smoke pellet, upright wooden substitution log, three steel shuriken, and vertical stone pillar): Fighter A (dark shinobi coat, rope dart at left hip, smoke pellet at waist, wooden substitution log) begins inverted high above the stone pillar; "
        "Fighter B (sleeveless combat vest, reverse-grip iron kunai in right hand, three shuriken on right thigh) stands grounded below. "
        "Maintain front-hemisphere camera geometry with zero camera-cut axis flips, keeping all nineteen body parts and both arms distinct in silhouette and no on-screen text.\n\n"
        "B feints upward with his reverse-grip kunai as A lands high on the vertical stone pillar face, turns upright with coat trailing, and sprints straight down the pillar toward B. "
        "As A launches off the pillar into a diving arc, B hurls the single kunai sharply upward; A whips his flat right foot across the rising blade in mid-air, and after foot-to-blade contact the kunai deflects spinning high above the courtyard as A lands in a low crouch and draws the rope dart into his left hand. "
        "A detonates his smoke pellet and vanishes in a white smoke burst, leaving an upright full-body wooden substitution log standing in his exact spot; B drives a heavy right palm strike into the wooden log, and after bark contact the log tips over as A materializes crouched behind B's flank. "
        "Planting his left leg, A drives a rising right knee squarely into B's mid-spine; only after knee-to-spine contact does B fold forward and lift airborne while A rebounds into an inverted backward somersault. "
        "While airborne, B hurls three shuriken downward; A lands in a low ground slide underneath the volley as all three shuriken embed into the stone pillar face, then A plants his left hand and cartwheels left onto his feet. "
        "As A lunges in and catches the falling kunai mid-air in his right hand, B clamps both hands onto A's left elbow; after locking the elbow joint, B pivots and hurls A into the stone pillar face, where A plants both feet flat against the stone. "
        "Rebounding off the pillar, A whips the rope dart from his left hand to wrap tightly around B's right shoulder, lands grounded, and pulls the taut rope dart to drag B stumbling toward the pillar. "
        "Coiling his torso, A drives the kunai in his right hand deep into B's right shoulder; after the blade impales the shoulder and remains embedded there, A wrenches the taut rope dart without resetting stance and slams B's body flat into the stone floor.\n\n"
        "Contrast brief coiled holds with whip-fast transfers; keep A's rising knee razor-sharp with zero knee smear, restrict broken-ink smears to the kicking leg, rope dart, and kunai drive, "
        "and fire metallic sparks, smoke bursts, slow-motion shoulder impale, and the radial floor-slam dust shockwave strictly after visible contact so recoil stays unobstructed. "
        "Close on a slow dolly-in with A holding a low shinobi crouch on screen-left and B lying prone and motionless on screen-right with the single kunai embedded in his right shoulder."
    )

    # 4. Build Golden Format 1: Original 05:34 (`SAKUGA-MLLM-3.1-CAUSAL` Compact JSON + Top Header)
    golden_0534_header = (
        f"{shot_contract} {state_and_props_contract} "
        "Render as one physically continuous combat event where every movement emerges visibly from the force and momentum of the previous state; no on-screen text, no numbers, no HUD, and no coordinate labels."
    )
    golden_0534_json: Dict[str, Any] = {
        "name": "lbn23adv_10s_pillar_fight_gold_master_31_causal",
        "schema": "SAKUGA-MLLM-3.1-CAUSAL",
        "fps": 24,
        "duration": 10.0,
        "axes": "Y_up, metres, ground y=0, stage 12x12x10m, vertical stone pillar at x=6.0 (0m to 8m high), A on screen_left facing right, B on screen_right facing left",
        "screen_geometry": "180_degree_camera_rule_locked: Fighter A stays on screen_left facing right and Fighter B stays on screen_right facing left across all 10.0s. Never flip left-right screen sides via camera cuts.",
        "negative": layer2_scene_graph["negative"],
        "conservation_laws": layer2_scene_graph["conservation_laws"],
        "laban": layer2_scene_graph["laban"],
        "beats": [
            "inverted_drop_and_pillar_sprint_vs_kunai_throw",
            "pillar_launch_and_midair_foot_kunai_deflect",
            "kawarimi_wooden_log_swap_and_palm_strike_into_log",
            "FE1_rising_right_knee_to_spine_and_backflip",
            "airborne_shuriken_volley_vs_low_slide_and_cartwheel",
            "FE2_two_hand_elbow_catch_and_pillar_wall_throw",
            "rope_dart_shoulder_wrap_and_FE4_taut_drag",
            "FE3_kunai_shoulder_impale_and_FE4_floor_slam",
        ],
        "A_beats": [
            {
                "t": 0.0,
                "beat": "inverted_drop_and_pillar_sprint_vs_kunai_throw",
                "causal": "C01: init_inverted_airborne_drop_above_pillar -> causes: C02_foot_plant_on_vertical_pillar_face_at_0.60s",
                "pos": [3.5, 7.5, 0.0],
                "vel": [3.8, -0.5, 0.0],
                "axis": "head:down_inverted_to_forward_on_pillar, torso:neutral_to_forward_sprint, facing:right, screen_side:left",
                "arc": "vertical_drop_to_downward_pillar_face_sprint",
                "support": "0.00s NO_SUPPORT_airborne -> 0.60s both_feet_planted_on_vertical_stone_pillar_face",
                "limbs": "0.00s: L_arm & R_arm overhead extended open, L_leg & R_leg tucked folded pointed; 0.60s: L_arm back extended, R_arm forward extended, L_leg forward planted on pillar, R_leg back pushing",
                "pose": "A begins coiled upside-down high above the stone pillar with rope dart at left hip, smoke pellet at waist, and substitution log in coat; as B throws the reverse-grip kunai upward at 0.50s, A lands both feet high on the vertical stone pillar face at 0.60s and sprints straight down toward B.",
            },
            {
                "t": 1.6,
                "beat": "pillar_launch_and_midair_foot_kunai_deflect",
                "causal": "C02: requires: C01_downward_pillar_sprint_momentum -> timing: BEFORE_RISING_KUNAI_INTERSECTION -> causes: C03_right_foot_deflects_kunai_spinning_high_at_2.50s_and_crouch_land_at_3.00s",
                "pos": [5.0, 2.5, -0.5],
                "vel": [-1.2, -1.8, 0.0],
                "axis": "head:forward_yaw_-90, torso:side_twist_-30, facing:right, screen_side:left",
                "arc": "ballistic_pillar_launch_into_horizontal_right_foot_deflect_kick",
                "support": "1.60s-2.50s NO_SUPPORT_airborne -> 3.00s both_feet_planted_in_low_crouch",
                "contact": "pre:A_launches_off_pillar_whipping_right_foot_at_rising_kunai -> hit:A_right_foot_strikes_kunai_midair_at_2.50s_zero_torso_overlap -> post:kunai_deflected_spinning_high_into_air_as_A_lands_crouched_at_3.00s_drawing_rope_dart_into_left_hand",
                "limbs": "2.50s: L_arm out extended open, R_arm forward folded fist, L_leg tucked folded pointed, R_leg extended flat striking kunai; 3.00s: both feet planted in low crouch, L_hand holding rope_dart",
                "pose": "IMPACT FRAME at 2.50s (hold 3f). Launching off the pillar at 1.60s, A whips his extended right foot across the rising kunai at 2.50s in clear profile, deflecting the blade spinning high into the air in a burst of metallic sparks before landing in a low crouch at 3.00s and drawing the rope dart into his left hand.",
            },
            {
                "t": 3.7,
                "beat": "kawarimi_wooden_log_swap_and_palm_strike_into_log",
                "causal": "C03: requires: C02_crouch_smoke_pellet_detonation -> causes: C04_upright_wooden_log_absorbs_B_palm_strike_at_4.00s_and_A_reappears_behind_B_at_4.40s",
                "pos": [4.7, 1.1, -0.4],
                "vel": [0.0, 0.0, 0.0],
                "axis": "3.70s: upright_full_body_wooden_substitution_log_stand_in -> 4.40s: A_crouched_behind_B_facing_right",
                "arc": "kawarimi_smoke_substitution_to_flank_reappearance",
                "support": "3.70s-4.40s substitution_log_upright_on_floor -> 4.40s A_both_feet_planted_behind_B",
                "contact": "pre:A_detonates_smoke_pellet_at_3.70s_leaving_upright_wooden_log_stand_in -> hit:B_right_palm_strikes_wooden_substitution_log_at_4.00s -> post:log_shudders_and_tips_as_A_reappears_crouched_behind_B_at_4.40s",
                "limbs": "3.70s-4.40s: full-body wooden log stand-in occupies A's exact slot (zero missing-limb frame gap); 4.40s: A both arms forward folded open, both legs planted in crouch",
                "pose": "At 3.70s A vanishes in a crisp white smoke burst, leaving an upright full-body wooden substitution log in his exact spot; at 4.00s B drives a heavy right palm strike into the wooden log, and at 4.40s A materializes crouched directly behind B's flank.",
            },
            {
                "t": 4.55,
                "beat": "FE1_rising_right_knee_to_spine_and_backflip",
                "causal": "C04: requires: C03_flank_reappearance_and_planted_left_leg_coil -> causes: C05_FE1_right_knee_launches_B_airborne_at_4.70s_and_A_rebounds_into_360_backflip_at_5.10s",
                "pos": [4.5, 1.4, -0.4],
                "vel": [0.3, 1.8, 0.0],
                "axis": "4.70s: torso_forward_twist_20_knee_drive -> 5.10s: inverted_head_down_360_backward_somersault",
                "arc": "FE1_upward_hip_to_knee_drive_into_360_backward_somersault",
                "support": "4.55s-4.65s left_foot_planted_pillar_leg -> 4.70s-5.10s NO_SUPPORT_airborne_backflip",
                "contact": "pre:4.55s_FE1_windup_loads_right_knee -> drive:4.65s_hips_drive_right_knee_up_forward -> hit:4.70s_A_right_knee_strikes_B_mid_spine_high_blunt -> post:4.72s_B_spine_flexes_forward_and_launches_airborne_while_A_backflips_to_inverted_apex_at_5.10s",
                "limbs": "4.70s: L_arm high guard folded, R_arm back extended fist, L_leg planted flat, R_leg folded knee driving into B spine (ZERO knee smear); 5.10s: inverted head-down, both arms overhead, both legs tucked",
                "pose": "IMPACT FRAME at 4.70s (hold 3f). Coiling on his planted left leg at 4.55s, A drives a razor-sharp rising right knee squarely into B's mid-spine at 4.70s; only after contact at 4.72s does B fold forward and launch airborne while A rebounds into a 360-degree backward somersault at 5.10s.",
            },
            {
                "t": 5.5,
                "beat": "airborne_shuriken_volley_vs_low_slide_and_cartwheel",
                "causal": "C05: requires: C04_backflip_descent + B_airborne_shuriken_volley_at_5.50s -> timing: BEFORE_SHURIKEN_INTERSECTION -> causes: C06_low_slide_under_volley_at_5.90s_and_left_cartwheel_recovery_at_6.30s",
                "pos": [3.8, 0.6, -0.5],
                "vel": [-1.2, 0.0, 0.0],
                "axis": "5.90s: pelvis_low_ground_slide -> 6.30s: torso_side_inverted_90deg_left_cartwheel",
                "arc": "low_flagstone_slide_into_left_hand_planted_cartwheel",
                "support": "5.90s both_feet_sliding_low_on_floor -> 6.30s left_hand_planted_cartwheel_to_feet",
                "contact": "evasion_corridor: A_slides_at_y=0.6m_as_B_3_shuriken_fly_overhead_and_embed_into_stone_pillar_face_at_6.30s",
                "limbs": "5.90s: both arms forward folded, both legs extended flat sliding; 6.30s: L_arm down planted on floor, R_arm overhead extended, L_leg tucked, R_leg extended",
                "pose": "As airborne B hurls three shuriken downward at 5.50s, A lands at 5.90s in a low ground slide underneath the volley; at 6.30s all three shuriken embed into the stone pillar face as A plants his left hand and cartwheels left onto his feet.",
            },
            {
                "t": 6.6,
                "beat": "FE2_two_hand_elbow_catch_and_pillar_wall_throw",
                "causal": "C06: requires: C05_cartwheel_entry_and_falling_kunai_descent -> causes: C07_A_catches_kunai_in_right_hand_at_6.60s_as_B_locks_A_left_elbow_at_6.80s_and_throws_A_onto_pillar_at_7.00s",
                "pos": [5.9, 2.8, -0.5],
                "vel": [1.7, 1.0, 0.0],
                "axis": "6.80s: torso_twist_forced_by_elbow_lock -> 7.00s: head_back_torso_extended_feet_planted_on_pillar",
                "arc": "midair_kunai_catch_into_circular_thrown_arc_onto_vertical_pillar_face",
                "support": "6.60s-6.95s NO_SUPPORT_airborne_thrown -> 7.00s both_feet_planted_flat_on_vertical_stone_pillar_face",
                "contact": "pre:6.60s_A_right_hand_catches_falling_kunai_as_B_loads_hands -> hit:6.80s_B_both_hands_lock_A_left_elbow -> post:6.82s_A_feet_lift_and_B_hurls_A_into_stone_pillar_face_at_7.00s_where_A_plants_both_feet",
                "limbs": "6.60s: R_hand snatches falling kunai, L_arm caught by B's two hands; 7.00s: both arms back extended open, both legs extended forward planted flat on stone pillar face",
                "pose": "IMPACT FRAME at 6.80s (hold 2f) & 7.00s (hold 3f). As A snatches the falling kunai out of the air with his right hand at 6.60s, B clamps both hands onto A's left elbow at 6.80s and pivots circularly to hurl A into the stone pillar face at 7.00s, where A plants both feet flat against the stone.",
            },
            {
                "t": 7.5,
                "beat": "rope_dart_shoulder_wrap_and_FE4_taut_drag",
                "causal": "C07: requires: C06_pillar_wall_rebound_and_rope_dart_in_left_hand -> causes: C08_rope_dart_wraps_B_right_shoulder_at_7.60s_and_FE4_drags_B_toward_pillar_at_8.00s_8.20s",
                "pos": [4.5, 1.8, -0.5],
                "vel": [-0.5, -0.4, 0.0],
                "axis": "head:forward_yaw_-30, torso:forward_twist_10_taut_pull, facing:right, screen_side:left",
                "arc": "pillar_rebound_whip_wrap_into_grounded_rotational_drag",
                "support": "7.50s NO_SUPPORT_rebound -> 8.00s-8.20s left_foot_planted_flat_driving_FE4_drag",
                "contact": "pre:7.50s_A_whips_rope_dart_from_left_hand -> hit:7.60s_rope_dart_wraps_tightly_around_B_right_shoulder -> post:8.00s_8.20s_A_plants_left_foot_and_pulls_taut_rope_dart_dragging_B_toward_pillar",
                "limbs": "L_arm forward extended holding taut rope dart tethered to B's right shoulder; R_arm back extended fist holding captured kunai; L_leg forward planted flat; R_leg back extended",
                "pose": "Rebounding off the pillar at 7.50s, A whips the rope dart from his left hand to wrap tightly around B's right shoulder at 7.60s (hold 2f), then lands grounded on his left foot at 8.00s-8.20s (FE4) and wrenches the taut rope line to drag B stumbling toward the pillar.",
            },
            {
                "t": 8.3,
                "beat": "FE3_kunai_shoulder_impale_and_FE4_floor_slam",
                "causal": "C08: requires: C07_taut_rope_dart_drag_and_kunai_in_right_hand -> causes: C09_FE3_kunai_impales_B_right_shoulder_at_8.50s_and_FE4_slams_B_prone_at_8.75s_9.00s",
                "pos": [4.9, 1.5, -0.4],
                "vel": [0.4, -0.8, 0.0],
                "axis": "8.50s: torso_forward_twist_-25_kunai_drive -> 8.75s: full_body_downward_slam -> 9.00s: low_shinobi_crouch",
                "arc": "FE3_down_forward_kunai_stab_chained_directly_into_FE4_downward_ground_slam",
                "support": "left_foot_planted_driving_stab_and_slam -> 9.00s-10.00s both_feet_planted_in_low_crouch",
                "contact": "pre:8.30s_FE3_windup_coils_torso -> hit1:8.50s_A_right_hand_drives_kunai_deep_into_B_right_shoulder_retained -> hit2:8.75s_9.00s_FE4_A_wrenches_taut_rope_dart_slamming_B_flat_onto_stone_floor -> post:B_remains_prone_motionless_to_10.00s",
                "limbs": "8.50s: L_arm holding taut rope dart, R_arm extended driving kunai into B's right shoulder; 8.75s: both arms wrenching downward for floor slam; 9.00s-10.00s: low crouch, both arms separate from torso in silhouette",
                "pose": "IMPACT FRAME at 8.50s (hold 4f, slomo 0.25x) & 8.75s-9.00s (hold 5f). At 8.50s A drives the kunai in his right hand deep into B's right shoulder where it stays embedded; without resetting stance, A wrenches the taut rope dart at 8.75s-9.00s to slam B's entire body prone into the courtyard stones in a radial dust shockwave, holding a low crouch through 10.00s.",
            },
        ],
        "B_track": [
            {"t": 0.0, "pos": [4.5, 0.9, 0.0], "axis": "facing:left, screen_side:right", "support": "both_feet_planted_wide", "action": "reverse_grip_kunai_upward_throw_at_0.50s", "pose": "stands grounded on screen-right holding the kunai in reverse grip in his right hand and three shuriken on his right thigh; at 0.50s twists torso and throws the kunai upward toward A"},
            {"t": 2.0, "pos": [4.5, 0.9, 0.0], "axis": "facing:left, screen_side:right", "support": "both_feet_planted", "action": "upward_throw_follow_through_and_guard_brace", "pose": "completes high upward throwing arc with right arm as A's right foot deflects the kunai at 2.50s, then braces both forearms forward"},
            {"t": 4.0, "pos": [4.5, 0.9, 0.0], "axis": "torso:forward_twist_-15, facing:left, screen_side:right", "support": "both_feet_planted", "contact": "B_right_palm -> strikes_upright_wooden_substitution_log_at_4.00s", "action": "grounded_palm_strike_into_substitution_log", "pose": "drives a heavy right open-palm strike squarely into the upright wooden substitution log standing in A's place at 4.00s as A reappears crouched behind B at 4.40s"},
            {"t": 4.7, "pos": [4.5, 1.5, 0.0], "axis": "head:back, torso:folded_forward_spine_flexed, screen_side:right", "support": "NO_SUPPORT_airborne_launched", "contact": "B_mid_spine -> struck_by_A_FE1_rising_right_knee_at_4.70s", "action": "FE1_reacts_spine_flex_and_airborne_launch_at_4.72s", "pose": "only after A's right knee strikes B's mid-spine at 4.70s, B's spine flexes forward at 4.72s, his torso folds, his arms fling forward, and both feet lift airborne"},
            {"t": 5.5, "pos": [4.3, 1.2, 0.0], "axis": "torso:forward_twist_-25, facing:left, screen_side:right", "support": "5.50s NO_SUPPORT_airborne -> 6.30s both_feet_planted_brace", "action": "airborne_three_shuriken_volley_into_pillar", "pose": "while airborne at 5.50s, twists torso and hurls all three shuriken downward toward A; lands in a grounded brace at 6.30s as the three shuriken embed into the stone pillar face"},
            {"t": 6.6, "pos": [4.5, 0.9, 0.0], "axis": "torso:rotational_wring_throw, facing:left, screen_side:right", "support": "both_feet_planted_right_foot_post", "contact": "B_both_hands -> lock_A_left_elbow_at_6.80s_and_throw_A_into_pillar_at_7.00s", "action": "FE2_elbow_catch_and_circular_pillar_throw", "pose": "plants right foot at 6.65s, clamps both hands around A's left elbow at 6.80s, wrenches A off his feet, and hurls A circularly into the vertical stone pillar face at 7.00s"},
            {"t": 7.6, "pos": [5.0, 0.9, 0.0], "axis": "torso:pulled_forward_off_balance, screen_side:right", "support": "feet_stumbling_forward", "contact": "B_right_shoulder -> wrapped_by_A_rope_dart_at_7.60s_and_dragged_at_8.00s_8.20s", "action": "FE4_reacts_right_shoulder_wrapped_and_dragged", "pose": "right shoulder is wrapped tightly by A's rope dart at 7.60s; at 8.00s-8.20s B is yanked off-balance and dragged stumbling toward the stone pillar"},
            {"t": 8.5, "pos": [5.3, 0.2, 0.0], "axis": "8.53s: shoulder_jerk_head_snap_back -> 8.77s-10.00s: spine_flat_prone_on_ground", "support": "8.75s-10.00s prone_motionless_on_stone_floor", "contact": "B_right_shoulder -> impaled_by_A_kunai_at_8.50s_and_body_slammed_prone_at_8.75s_9.00s", "action": "FE3_shoulder_impaled_and_FE4_slammed_prone_final", "pose": "only after A drives the kunai deep into B's right shoulder at 8.50s does B's shoulder jerk and head snap back at 8.53s with the kunai remaining embedded; at 8.75s-9.00s B is slammed flat onto the stone floor and remains prone and motionless through 10.00s"},
        ],
        "kunai": layer2_scene_graph["prop_tracks"]["kunai"],
        "rope_dart": layer2_scene_graph["prop_tracks"]["rope_dart"],
        "smoke_pellet_and_substitution_log": layer2_scene_graph["prop_tracks"]["smoke_pellet_and_substitution_log"],
        "shuriken_volley_3": layer2_scene_graph["prop_tracks"]["shuriken_volley_3"],
        "stone_pillar": layer2_scene_graph["prop_tracks"]["stone_pillar"],
        "camera": layer2_scene_graph["camera"],
        "anime": layer2_scene_graph["anime"],
        "rules": layer2_scene_graph["rules"],
    }
    gold_mod = _load_sakuga_compiler()
    golden_0534_json_only = gold_mod.format_sakuga_prompt(golden_0534_json, "").lstrip()
    golden_0534_text = f"{golden_0534_header}\n\n{golden_0534_json_only}"

    # 4b. Combined Arm C1 (6-Part Translated Directorial Contract) + SAKUGA-MLLM-3.1-CAUSAL JSON
    c1_plus_sakuga_mllm_causal_text = (
        f"{arm_c1_text}\n\n"
        "=== SAKUGA-MLLM-3.1-CAUSAL SCENE GRAPH ===\n"
        f"{golden_0534_json_only}"
    )

    # 5. Build Golden Format 2: Extreme (`sakuga_Xperiment` 2-Layer Unrolled Fluid Stack)
    xperiment_layer1_lines = [
        "=== LAYER 1: CONTINUOUS SUPPORT, FORCE-EVENT & PROP TIMELINE (Labanotation-as-Words) ===",
        "MOVEMENT LANGUAGE: <seconds> <performer> (<frames>): SUPPORT (what bears weight, lead/rear weight split %, and Center of Gravity CoG; NO SUPPORT = airborne) | bilateral 19-part limb placement & torso rotation (both L_arm and R_arm separate from torso in silhouette; Kawarimi at 3.70s uses upright full-body wooden log stand-in) | PROPS (kunai, rope_dart, smoke_pellet, substitution_log, 3_shuriken, pillar) | CHAIN (ground-up kinetic link sequence) & Easing Curve | 5-phase force event (windup -> drive -> CONTACT -> reacts -> follow-through). A is always screen-left; B is always screen-right.",
        "0.00 A (14f): NO SUPPORT (airborne inverted at 7.5m high above pillar) -> 0.60s SUPPORT both feet planted on vertical stone pillar face (70/30 lead/rear split, CoG driving_down_pillar_face) | L_arm:overhead extended open -> back extended open; R_arm:overhead extended open -> forward extended open (both arms separate from torso in silhouette); L_leg:tucked folded -> forward planted flat on pillar; R_leg:tucked folded -> back extended pushing | PROPS: rope_dart holstered at left hip, smoke_pellet at waist, substitution_log in coat | CHAIN: inverted airborne drop > both feet plant high on vertical stone pillar > hips turn 0-deg upright > legs sprint straight down vertical pillar face | Easing: burst_launch_snap_lock | E01 PILLAR_DROP_AND_VERTICAL_SPRINT (effort FLICK): A drops inverted from high above, plants both feet on the vertical stone pillar face at 0.60s, and sprints straight down the pillar toward B.",
        "0.00 B (14f): SUPPORT both feet planted wide on courtyard floor (55/45 lead/rear weight split, CoG centered_to_front_foot) | L_arm:forward folded open guard; R_arm:reverse-grip kunai chambered -> 0.50s whips forward-upward extended open to release kunai (both arms separate from torso in silhouette); L_leg:forward planted flat; R_leg:back planted flat | PROPS: kunai in R_hand reverse grip (0.00s) -> thrown upward at A (0.50s); 3_shuriken holstered on right upper leg | CHAIN: rear foot braces > torso twists 10-deg forward > right shoulder whips upward > right hand releases kunai on upward trajectory | Easing: snap_snap_hold_snap | E01 GROUNDED_KUNAI_UPWARD_THROW (effort PUNCH): At 0.50s B twists his torso and hurls the reverse-grip kunai upward toward A descending the pillar.",
        "1.60 A (22f): SUPPORT feet push off pillar -> NO SUPPORT (airborne diving arc) -> 2.50s mid-air right-foot kunai deflect (accent 3, hold 3f) -> 3.00s SUPPORT both feet planted in low crouch (50/50 split, CoG low_centered) | L_arm:out extended open for mid-air balance; R_arm:forward folded fist (both arms separate from torso in silhouette); L_leg:tucked folded pointed; R_leg:whips extended flat striking kunai at 2.50s -> 3.00s both legs planted in crouch as L_hand draws rope_dart | PROPS: R_foot deflects kunai spinning high into air at 2.50s; L_hand draws rope_dart from left hip at 3.00s | CHAIN: feet kick off stone pillar > torso side-twists -30-deg in mid-air > right hip whips flat right foot across kunai > lands crouched on both feet | Easing: snap_snap_hold_snap | E02 AIRBORNE_KUNAI_DEFLECT_KICK (hold 3f, effort PUNCH): A launches off the pillar at 1.60s, strikes the rising kunai cleanly with his right foot at 2.50s to send it spinning high overhead, and lands in a grounded crouch at 3.00s drawing the rope dart into his left hand.",
        "2.00 B (24f): SUPPORT both feet planted on courtyard floor (60/40 lead/rear weight split, CoG over_lead_foot) | L_arm:forward folded open; R_arm:up extended open completing throw follow-through -> 2.60s both forearms braced forward-high (both arms separate from torso in silhouette); L_leg:forward planted flat; R_leg:back planted flat | PROPS: kunai deflected high overhead by A's foot at 2.50s | CHAIN: right arm finishes high upward follow-through > torso settles > both forearms lock in high guard | Easing: sudden_jolt_settle | E02 UPWARD_THROW_FOLLOW_THROUGH: B finishes his high upward throw follow-through and braces his guard as the deflected kunai spins upward.",
        "3.70 A (17f): 3.70s KAWARIMI SUBSTITUTION (smoke_pellet bursts; upright full-body wooden substitution_log stands in A's exact place from 3.70s-4.40s so all 19 body-part slots remain filled) -> 4.40s SUPPORT both feet planted crouched behind B's flank (45/55 weight split, CoG coiled_low) | 3.70s log stand-in: upright full-body mimic; 4.40s A: L_arm:forward folded open, R_arm:forward folded open, L_leg:forward planted flat, R_leg:back planted flat | PROPS: smoke_pellet deployed at 3.70s; substitution_log stands in A's place at 3.70s and absorbs B's 4.00s palm strike; rope_dart in A_left_hand | CHAIN: smoke pellet detonates > wooden log occupies A's stance to take B's hit > A materializes crouched behind B's flank at 4.40s | Easing: burst_launch_snap_lock | E03 KAWARIMI_LOG_SUBSTITUTION: At 3.70s A vanishes in white smoke leaving a full-body upright wooden log in his place, then reappears crouched directly behind B at 4.40s.",
        "4.00 B (10f): SUPPORT both feet planted wide (80/20 lead/rear weight split, CoG lunging_over_lead_foot) | L_arm:back folded fist; R_arm:drives forward extended open palm squarely into chest of upright wooden substitution_log (accent 3, hold 3f; both arms separate from torso in silhouette); L_leg:forward planted flat; R_leg:back planted flat | PROPS: R_hand strikes wooden substitution_log at 4.00s | CHAIN: rear foot drives hip twist -15-deg > right shoulder surges forward > right open palm slams into wooden log bark | Easing: snap_snap_hold_snap | E03 GROUNDED_PALM_STRIKE_INTO_LOG (hold 3f, effort PUNCH): At 4.00s B drives a heavy right palm strike into the wooden substitution log, knocking the log askew just as A reappears behind him.",
        "4.55 A (14f): 4.55s SUPPORT left foot planted pillar leg (90/10 split, CoG driving_upward) -> 4.70s-5.10s NO SUPPORT (airborne 360-deg backward somersault to inverted apex) | 4.55s-4.70s: L_arm:high guard folded open, R_arm:back extended fist counterbalance, L_leg:planted flat, R_leg:folded knee driving up into B's spine (ZERO knee smear); 5.10s: inverted head-down, both arms overhead extended, both legs tucked | PROPS: rope_dart in L_hand; kunai spinning high overhead | CHAIN: 4.55s FE1 windup coils torso 20-deg on left leg > 4.65s FE1 drive thrusts hip-to-knee up-forward > 4.70s FE1 CONTACT right knee strikes B's mid-spine > 4.85s-5.10s A rebounds into 360-deg backward somersault | Easing: snap_snap_hold_snap | FE1 RISING_KNEE_STRIKE_AND_BACKFLIP (hold 3f, effort PUNCH): A loads his right knee at 4.55s, drives it squarely into B's spine at 4.70s, and rides the rebound into an inverted backward somersault at 5.10s.",
        "4.70 B (10f): NO SUPPORT (launched airborne by A's knee impact at 4.70s, CoG airborne_displaced_forward_up) | L_arm:flung forward-out extended open; R_arm:flung forward-out extended open (both arms separate from torso in silhouette); L_leg:forward extended pointed off floor; R_leg:back extended pointed off floor | CHAIN: 4.70s mid-spine absorbs high blunt knee impulse > 4.72s FE1 reacts: spine flexes forward > torso folds > both feet lift airborne > arms fling forward | Easing: sudden_jolt_settle | FE1 SPINE_STRUCK_AIRBORNE_LAUNCH: Only after A's right knee hits B's spine at 4.70s, B's spine flexes forward at 4.72s and B is launched off his feet.",
        "5.50 A (19f): 5.90s SUPPORT both feet forward-low sliding across flagstones (CoG low_sliding) -> 6.30s L_hand plants for 90-deg forward cartwheel left (NO SUPPORT airborne arc to feet) | 5.90s: pelvis low, both arms forward folded open, both legs extended flat sliding under shuriken; 6.30s: torso side-inverted, L_arm:down extended planted on floor, R_arm:overhead extended open, L_leg:tucked, R_leg:extended | PROPS: evades 3_shuriken overhead at 5.90s | CHAIN: lands from backflip into low flagstone slide > ducks under shuriken fan > plants left hand at 6.30s > whips legs through 90-deg left cartwheel | Easing: burst_launch_snap_lock | E05 LOW_GROUND_SLIDE_AND_CARTWHEEL (effort PRESS -> SLASH): A slides low across the stones at 5.90s underneath B's shuriken volley, then plants his left hand at 6.30s and cartwheels left onto his feet.",
        "5.50 B (19f): 5.50s NO SUPPORT (airborne) -> 6.30s SUPPORT both feet planted in grounded brace (60/40 weight split, CoG braced_low) | 5.50s: torso twists -25-deg mid-air, L_arm:forward folded, R_arm:whips forward extended throwing 3_shuriken; 6.30s: both arms forward folded in brace, both legs planted | PROPS: throws shuriken_1 + shuriken_2 + shuriken_3 at 5.50s -> all 3 embed into vertical stone pillar face at 6.30s | CHAIN: twists torso in mid-air > whips right arm downward releasing 3 shuriken > lands on both feet in braced crouch as shuriken embed in pillar | Easing: snap_snap_hold_snap | E05 AIRBORNE_SHURIKEN_VOLLEY_AND_LAND (effort PUNCH -> PRESS): While airborne at 5.50s B hurls three shuriken downward; they pass over A's slide and embed into the stone pillar face at 6.30s as B lands braced.",
        "6.60 A (11f): 6.60s NO SUPPORT lunging in while R_hand catches descending kunai -> 6.82s feet lifted off ground by B's elbow lock -> 7.00s SUPPORT both feet plant flat on vertical stone pillar face (hold 3f) | 6.60s: L_arm forward caught by B, R_arm snatches falling kunai; 7.00s: head back yaw 30, torso extended, both arms back extended open, both legs forward extended planted flat on pillar face | PROPS: R_hand catches falling kunai at 6.60s and retains it; feet plant on stone pillar at 7.00s | CHAIN: snatches falling kunai in right hand > 6.82s FE2 reacts: left elbow locked, torso twist-forced, feet lifted > 7.00s slams feet-first onto vertical stone pillar face | Easing: sudden_jolt_settle | FE2 ELBOW_LOCKED_AND_PILLAR_WALL_PLANT (hold 3f, effort PRESS): A catches the falling kunai in his right hand at 6.60s just as B locks A's left elbow at 6.80s and hurls A into the stone pillar face at 7.00s, where A plants both feet against the stone.",
        "6.60 B (11f): SUPPORT both feet planted wide on courtyard floor (35/65 -> 75/25 rotational weight transfer, CoG grounded_pivot_post) | L_arm:forward extended surrounding A's left elbow; R_arm:forward extended surrounding A's left elbow (both arms separate from torso in silhouette); L_leg:forward planted flat; R_leg:planted firm pivot post | CHAIN: 6.60s FE2 windup loads both hands and coils torso -25-deg > 6.65s FE2 drive plants right foot and drives hands to A's left elbow > 6.80s FE2 CONTACT both hands lock A's left elbow (hold 2f) > 7.05s FE2 follow-through whips circularly hurling A into pillar | Easing: snap_snap_hold_snap | FE2 ELBOW_CATCH_AND_PILLAR_THROW (hold 2f at 6.80s, effort WRING): B clamps both hands onto A's left elbow at 6.80s, wrenches A off his feet, and hurls A circularly into the stone pillar face at 7.00s.",
        "7.50 A (17f): 7.50s NO SUPPORT rebounding off pillar -> 7.60s rope_dart wraps B's right shoulder (hold 2f) -> 8.00s-8.20s SUPPORT left foot planted flat on floor driving FE4 drag (75/25 split, CoG pulling_back_and_rotational) | L_arm:forward extended holding taut rope_dart line; R_arm:back extended fist holding captured kunai (both arms separate from torso in silhouette); L_leg:forward planted flat; R_leg:back extended pointed | PROPS: L_hand whips rope_dart to wrap B's right shoulder at 7.60s (held taut for 2.4s); R_hand holds kunai | CHAIN: kicks off stone pillar > left hand whips rope dart around B's right shoulder at 7.60s > lands on left foot at 8.00s > 8.10s FE4 drive pulls taut rope backward-rotational | Easing: snap_snap_hold_snap | E07 ROPE_DART_WRAP_AND_FE4_TAUT_DRAG (hold 2f, effort WRING): Rebounding off the pillar at 7.50s, A wraps B's right shoulder with the rope dart at 7.60s, lands on his left foot at 8.00s, and wrenches the taut tether through 8.20s to drag B toward the pillar.",
        "7.60 B (15f): SUPPORT both feet stumbling forward under rope-dart pull (85/15 weight pitched over toes, CoG dragged_off_balance) | L_arm:back extended open; R_arm:back extended open with right shoulder wrapped by taut rope_dart; L_leg:forward stumbling; R_leg:back extended | PROPS: right shoulder wrapped by A's rope_dart from 7.60s-10.00s | CHAIN: right shoulder bound by rope wrap at 7.60s > taut tether yanks shoulder forward at 8.00s-8.20s > torso pitches forward toward pillar | Easing: sudden_jolt_settle | E07 SHOULDER_WRAPPED_AND_DRAGGED: B's right shoulder is bound by the rope dart at 7.60s and B is dragged stumbling toward the pillar at 8.00s-8.20s.",
        "8.30 A (18f): SUPPORT left foot planted flat driving FE3 kunai stab and FE4 ground slam (85/15 weight split, CoG driving_down_forward) | 8.30s-8.50s: L_arm:forward folded holding taut rope, R_arm:drives forward extended plunging kunai into B's right shoulder (hold 4f, slomo 0.25x); 8.75s-9.00s: both arms wrenching downward for FE4 full-body slam (hold 5f) | PROPS: R_hand drives kunai deep into B's right shoulder at 8.50s (kunai remains embedded in B's shoulder to 10.00s); L_hand pulls taut rope_dart | CHAIN: 8.30s FE3 windup coils torso -25-deg > 8.42s FE3 drive plants left foot and drives right hand kunai down-forward > 8.50s FE3 CONTACT kunai penetrates B's right shoulder > without stance reset, 8.75s FE4 CONTACT wrenches taut rope and body weight downward to slam B into floor | Easing: snap_snap_hold_snap | FE3 KUNAI_SHOULDER_IMPALE_AND_FE4_FLOOR_SLAM (hold 4f at 8.50s, hold 5f at 8.75s-9.00s): At 8.50s A drives the kunai deep into B's right shoulder where it stays embedded, then immediately wrenches the taut rope dart at 8.75s-9.00s to slam B's entire body flat into the stone floor.",
        "8.50 B (13f): 8.50s SUPPORT staggering -> 8.75s-9.05s SUPPORT prone flat on courtyard stone floor (CoG compressed_on_floor) | 8.53s: right shoulder jerks from kunai impale, head snaps back; 8.77s-9.05s: torso compressed flat against flagstones, both arms and legs splayed prone | PROPS: kunai embedded in right shoulder from 8.50s-10.00s | CHAIN: 8.50s right shoulder impaled by kunai > 8.53s FE3 reacts: shoulder jerks, torso twists, head snaps back > 8.75s FE4 slam hits floor > 8.77s FE4 reacts: body compresses flat against stones with radial dust shockwave | Easing: sudden_jolt_settle | FE3_AND_FE4 IMPALED_AND_SLAMMED_PRONE: Only after the kunai penetrates B's right shoulder at 8.50s does B's shoulder jerk and head snap back; at 8.75s-9.00s B is slammed flat onto the courtyard stones.",
        "9.00 A (24f): SUPPORT both feet planted in low balanced shinobi crouch on screen-left | L_arm:forward folded open; R_arm:forward folded open (both arms separate from torso in silhouette); L_leg:forward planted flat; R_leg:back planted flat | follow-through crouch hold to 10.00s.",
        "9.00 B (24f): SUPPORT prone motionless face-down on stone floor on screen-right | kunai remains embedded in right shoulder, three shuriken embedded in stone pillar | final prone state hold to 10.00s (B never stands after knockdown).",
    ]

    xperiment_layer2_json = dict(golden_0534_json)
    xperiment_layer2_json["name"] = "lbn23adv_10s_pillar_fight_sakuga_xperiment"
    xperiment_layer2_json["schema"] = "sakuga_Xperiment"
    xperiment_layer2_formatted = gold_mod.format_sakuga_prompt(xperiment_layer2_json, "").lstrip()

    golden_extreme_text = (
        f"{golden_0534_header}\n\n"
        + "\n".join(xperiment_layer1_lines)
        + "\n\n=== LAYER 2: sakuga_Xperiment KINEMATIC & CAMERA SCENE GRAPH ===\n"
        + xperiment_layer2_formatted
    )

    trace_payload = {
        "schema": "LATENT-SAKUGA-1.0",
        "source_score": "LBN-2.3-ADV v3 (pillar fight with substitution, force-event melee)",
        "internal_only_biomechanics_not_emitted_in_prose": {
            "stage_dimensions_m": [12, 12, 10],
            "pillar_plane": "x=6, height=0..8m",
            "A_locations_xyz": [
                [3.5, 0.0, 7.5], [5.8, 0.0, 7.2], [5.9, -0.3, 4.5], [5.5, -0.6, 3.2],
                [5.0, -0.5, 2.5], [4.5, -0.5, 1.5], [4.8, -0.4, 0.9], [4.7, -0.4, 1.1],
                [4.4, -0.4, 1.1], [4.5, -0.4, 1.4], [4.0, -0.5, 2.2], [4.3, -0.5, 1.8],
                [3.8, -0.5, 0.6], [3.5, -0.4, 1.5], [4.5, -0.3, 1.8], [5.9, -0.5, 2.8],
                [4.8, -0.6, 2.2], [4.5, -0.5, 1.8], [4.9, -0.4, 1.5], [5.3, -0.4, 0.7],
            ],
            "force_events_validated": ["FE1_knee_strike_4.55_4.85", "FE2_elbow_catch_throw_6.60_7.05", "FE3_kunai_drive_8.30_8.60", "FE4_drag_slam_8.00_9.05"],
        },
        "arm_metrics": {
            "c1_plus_sakuga_mllm_causal": {
                "word_count": len(c1_plus_sakuga_mllm_causal_text.split()),
                "utf8_byte_count": len(c1_plus_sakuga_mllm_causal_text.encode("utf-8")),
                "sha256": hashlib.sha256(c1_plus_sakuga_mllm_causal_text.encode("utf-8")).hexdigest()[:16],
            },
            "golden_0534_causal": {
                "word_count": len(golden_0534_text.split()),
                "utf8_byte_count": len(golden_0534_text.encode("utf-8")),
                "sha256": hashlib.sha256(golden_0534_text.encode("utf-8")).hexdigest()[:16],
            },
            "golden_extreme_xperiment": {
                "word_count": len(golden_extreme_text.split()),
                "utf8_byte_count": len(golden_extreme_text.encode("utf-8")),
                "sha256": hashlib.sha256(golden_extreme_text.encode("utf-8")).hexdigest()[:16],
            },
            "arm_C1_contract": {
                "word_count": len(arm_c1_text.split()),
                "utf8_byte_count": len(arm_c1_text.encode("utf-8")),
                "sha256": hashlib.sha256(arm_c1_text.encode("utf-8")).hexdigest()[:16],
            },
            "arm_D_scene_stack": {
                "word_count": len(arm_d_text.split()),
                "utf8_byte_count": len(arm_d_text.encode("utf-8")),
                "sha256": hashlib.sha256(arm_d_text.encode("utf-8")).hexdigest()[:16],
            },
            "arm_C3_tight": {
                "word_count": len(arm_c3_text.split()),
                "utf8_byte_count": len(arm_c3_text.encode("utf-8")),
                "sha256": hashlib.sha256(arm_c3_text.encode("utf-8")).hexdigest()[:16],
            },
        },
    }

    (PROMPT_DIR / "lbn23_pillar_fight_c1_plus_sakuga_mllm_causal.txt").write_text(
        c1_plus_sakuga_mllm_causal_text + "\n", encoding="utf-8"
    )
    (PROMPT_DIR / "lbn23_pillar_fight_golden_0534_causal.txt").write_text(golden_0534_text + "\n", encoding="utf-8")
    (PROMPT_DIR / "lbn23_pillar_fight_golden_extreme_xperiment.txt").write_text(golden_extreme_text + "\n", encoding="utf-8")
    (PROMPT_DIR / "lbn23_pillar_fight_arm_C1_contract.txt").write_text(arm_c1_text + "\n", encoding="utf-8")
    (PROMPT_DIR / "lbn23_pillar_fight_arm_D_scene_stack.txt").write_text(arm_d_text + "\n", encoding="utf-8")
    (PROMPT_DIR / "lbn23_pillar_fight_arm_C3_tight.txt").write_text(arm_c3_text + "\n", encoding="utf-8")
    (PROMPT_DIR / "lbn23_pillar_fight_intent_ir_and_trace.json").write_text(
        json.dumps(trace_payload, indent=2) + "\n", encoding="utf-8"
    )
    return trace_payload


if __name__ == "__main__":
    res = build_lbn23_pillar_fight()
    print(json.dumps(res["arm_metrics"], indent=2))
