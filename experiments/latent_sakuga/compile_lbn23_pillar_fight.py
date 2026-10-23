"""Compile `LBN-2.3-ADV v3` (10s Pillar Fight with Kawarimi Substitution, Props & Force-Event Melee)
into the LATENT SAKUGA Causal-Readability Arms:
  1. `lbn23_pillar_fight_arm_C1_contract.txt` (6-Layer Scene Contract with Prop Ledger & Kawarimi Stand-In)
  2. `lbn23_pillar_fight_arm_D_scene_stack.txt` (2-Layer Scene Stack: Header + Layer 1 Synchronized Timeline + Layer 2 JSON Scene Graph)
  3. `lbn23_pillar_fight_arm_C3_tight.txt` (Ultra-Tight HARD-Invariant Floor, Zero Digits)
  4. `lbn23_pillar_fight_intent_ir_and_trace.json` (Full Loss-Audited Trace + Internal Biomechanics)
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

PROMPT_DIR = Path(__file__).parent / "prompts"


def build_lbn23_pillar_fight() -> Dict[str, Any]:
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)

    shot_contract = (
        "10s anime fight clip, 24fps, moonlit stone courtyard ninja arena with a tall carved stone pillar rising vertically on the right-center stage plane, "
        "drifting night mist, crisp silver moonlight rim-lighting, and deep indigo courtyard shadows. "
        "STYLE: Pure 2D cel-shaded hand-drawn anime, Naruto Shippuden and Sword of the Stranger style high-speed ninja sakuga animation on twos, "
        "flat two-tone high-contrast cel shadows, heavy anatomical ink outlines on Fighter A and Fighter B, broken sketchy ink on active smear limbs and rope-dart whip arcs only, "
        "clean ultra-thick ink on impact holds. Not 3D, not CGI, not live action, not photoreal. "
        "SCREEN GEOMETRY LOCK: Maintain strict 180-degree front-hemisphere camera geometry — Fighter A stays on screen-left facing right and Fighter B stays on screen-right facing left "
        "with zero camera-cut side swaps and zero on-screen text, numbers, or HUD."
    )

    state_and_props_contract = (
        "ENTITY COUNT, OUTFIT & PROP CONTINUITY LOCK: Exactly TWO shinobi fighters and SIX tracked props with strict single-instance conservation (never duplicated, never teleported). "
        "Fighter A (agile shinobi striker): dark high-collar shinobi flak coat trailing behind, forearm wraps, dark shinobi trousers, strapped sandals; begins inverted high in mid-air above the stone pillar with rope dart holstered at left hip, smoke pellet at waist, and wooden substitution log concealed inside coat. "
        "Fighter B (heavy armored rogue shinobi): sleeveless charcoal combat vest over scarred broad shoulders, reinforced forearm bracers, dark hakama trousers; begins grounded at the base of the courtyard holding the single iron kunai in reverse grip in his right hand and three steel shuriken holstered in his right thigh pouch. "
        "PROP LEDGER INVARIANTS: "
        "(1) SINGLE KUNAI: Held by B in reverse grip (0.0s-0.5s) -> thrown upward at A (0.5s) -> kicked and deflected spinning high into the air by A's right foot (2.5s) -> caught falling out of the air by A's right hand (6.6s-8.0s) -> driven by A's right hand deep into B's right shoulder where it stays embedded to the end (8.5s-10.0s). "
        "(2) SINGLE ROPE DART: Holstered at A's left hip (0.0s-3.0s) -> drawn into A's left hand on crouch landing (3.0s) -> whipped by A's left hand to wrap tightly around B's right shoulder (7.5s-7.6s) -> pulled taut to drag B toward the pillar and slam him (8.0s-10.0s). "
        "(3) SMOKE PELLET & WOODEN SUBSTITUTION LOG (KAWARIMI STAND-IN): At 3.7s A deploys the smoke pellet and vanishes in a white smoke burst while a full-body-height upright wooden substitution log immediately occupies A's exact spot (3.7s-4.4s) to absorb B's palm strike at 4.0s before toppling to the stone floor as A reappears behind B at 4.4s. "
        "(4) THREE SHURIKEN: Holstered on B's right thigh (0.0s-5.5s) -> thrown in a fan volley by B while airborne (5.5s) -> pass cleanly over A's low ground slide (5.9s) and embed firmly into the stone pillar face (6.3s-10.0s). "
        "(5) STONE PILLAR: Solid vertical stone column anchored on the right-center stage plane from floor to high overhead; A lands near its top and sprints straight down its vertical face (0.6s-1.6s), three shuriken embed into its stone face (6.3s), and B hurls A's body against its face where A's feet plant to rebound (7.0s)."
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
        "- Beat 1 (0.00s-0.60s | INVERTED DROP, KUNAI THROW & PILLAR SPRINT): [View: high-angle crane drop transitioning to vertical tracking tilt down the stone pillar face] "
        "A begins coiled upside-down high in mid-air above the courtyard with both arms extended overhead and both legs tucked, while B stands grounded below in a wide guard holding the single iron kunai in reverse grip in his right hand. "
        "At 0.50s, B twists his torso and hurls the kunai upward toward A; at 0.60s, A lands both feet high on the vertical face of the stone pillar, turns upright with his coat trailing, and sprints straight down the pillar face toward B. "
        "[License: vertical descent streak on A's drop only; keep A's inverted silhouette, B's throwing arm, and the rising kunai crisp and solid; puff of stone dust at 0.60s pillar foot-plant]",

        "- Beat 2 (1.60s-3.00s | PILLAR LAUNCH, MID-AIR FOOT DEFLECTION OF KUNAI & CROUCH LANDING): [View: fast tracking push-in locking into a tight low-angle profile impact frame at 2.50s] "
        "At 1.60s, A kicks off the stone pillar face into a fast ballistic dive toward B while B's throwing arm finishes its upward follow-through. "
        "At 2.50s, before the rising kunai can intersect A's torso, A twists his hips in mid-air with his left leg tucked and whips his extended right foot flat across the blade — A's right foot strikes the kunai cleanly in profile (strike contact clearly visible with zero torso overlap), deflecting the single kunai spinning end-over-end high into the air above the courtyard. "
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
        "NEGATIVE GUARDRAILS: no missing limbs, no limb merging or L/R swapping during spins/somersaults/cartwheels, no kawarimi vanish without the full-body wooden substitution log stand-in, no duplicated or teleporting kunai, no reaction before contact, no stance reset between the 8.50s kunai impale and 8.75s floor slam, no B standing up after 5.00s knockdown."
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
        "screen_geometry": "180_degree_camera_hemisphere_locked_for_all_10s: Fighter A stays on screen_left facing right and Fighter B stays on screen_right facing left throughout all 10.0 seconds with zero camera-cut side swaps.",
        "body_invariants": "ALL_19_PARTS_PRESENT (head, torso, pelvis, upper-arm L/R, forearm L/R, hand L/R, thigh L/R, shin L/R, foot L/R). Occlusion allowed; deletion forbidden. At 3.70s-4.40s Kawarimi substitution, the upright full-body wooden substitution log stands in A's exact place so no limb or actor slot is missing.",
        "negative": (
            "no 3D CGI, no mocap stiffness, no floaty physics, no distant wide shots, no on-screen text or numbers, no HUD, "
            "no extra fighters, no cloned A or B, no extra props beyond 1 kunai, 1 rope dart, 1 smoke pellet, 1 substitution log, 3 shuriken, and 1 stone pillar, "
            "no missing limbs, no limb merge, no L/R limb swap, no limb duplication during spins/somersaults/cartwheels, "
            "no kawarimi vanish without the full-body wooden log stand-in, no kunai teleporting or duplication, "
            "no full-body blur during smears, no reaction before contact, no zero-width strikes, no stance reset between the 8.50s kunai impale and 8.75s floor slam, no B standing after 5.00s"
        ),
        "conservation_laws": [
            "CONSERVE_SEMANTICALLY: prioritize continuous shinobi weight transfer, 5-phase force-event width (windup -> drive -> contact -> reaction -> follow-through), weapon ownership continuity, and causal order over isolated poses",
            "single_kunai_ownership_continuity: B reverse-grip (0.0s) -> B upward throw (0.5s) -> A right-foot deflect upward spin (2.5s) -> A right-hand mid-air catch (6.6s) -> A drives into B right shoulder (8.5s) -> embedded in B right shoulder (8.5s-10.0s)",
            "kawarimi_full_body_stand_in: at 3.70s A vanishes in smoke and the upright wooden substitution log immediately occupies A's spot to receive B's 4.00s palm strike before A reappears behind B at 4.40s",
            "accent_after_contact_rule: impact sparks, smoke bursts, and radial dust rings fire strictly at or after visible contact and clear immediately so recoil and prop trajectories remain visible",
            "terminal_knockdown_law: B never stands upright after the 4.70s spine-knee launch and remains prone and motionless from 9.00s to 10.00s",
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
        "Naruto Shippuden and Sword of the Stranger style high-speed sakuga on twos, flat two-tone cel shadows, heavy anatomical ink outlines, broken sketchy ink on active smear limbs only, ultra-thick ink on impact holds. "
        "Two shinobi fighters and six strictly conserved props: Fighter A (screen-left, dark shinobi coat, rope dart at left hip, smoke pellet at waist, wooden substitution log) begins inverted high above the stone pillar; "
        "Fighter B (screen-right, sleeveless combat vest, reverse-grip iron kunai in right hand, three shuriken on right thigh) stands grounded below. "
        "Maintain front-hemisphere camera geometry keeping all nineteen body parts and both arms distinct in silhouette with no side swaps and no on-screen text.\n\n"
        "B hurls the single kunai upward as A lands high on the vertical stone pillar face, turns upright with coat trailing, and sprints straight down the pillar toward B. "
        "A launches off the pillar into a diving arc and whips his flat right foot across the rising kunai in mid-air; after foot-to-blade contact, the kunai deflects spinning high above the courtyard as A lands in a low crouch and draws the rope dart into his left hand. "
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
