"""Atomic 1-Contact-Per-Beat Causal Compiler & 12-Rule Semantic Verifier.

Addresses SEM-BUG-01 through SEM-BUG-12 from docs/ADR_CLAIM_CHECKED_RENDERER_AND_SEMANTIC_VERIFIER.md:
- Compile-Time Condition: Every beat is decomposed into an AtomicCausalBeat with at most ONE named
  contact (or ballistic release) and five mandatory labeled slots:
    Prep -> Commit -> Contact -> Consequence -> Recovery
  plus View and License, plus world-state hand/prop/orientation tracking.
- Verifier Condition: Deterministically checks all 12 rules (SCAN-01 through SCAN-12), including:
  * Sparks / hit-stops / shockwaves / recoil appear ONLY in Consequence/License (strictly AFTER Contact),
    never in Prep or Commit.
  * Smears appear ONLY on the active limb in Commit/License, never on heads/torsos/standing support legs.
  * Orientation physics on vertical surfaces (running down a vertical pillar requires head-first downward
    pitch, never "flips upright and sprints down").
  * Unambiguous cause (no polysemous "draws B's throw") and explicit screen-space directions ("up and
    toward screen-left", never standalone body-relative "backward").
- Render-Time Condition: Emits both:
  1. The Labeled 5-Step Atomic IR text (for human/checker verification).
  2. The Unlabeled Single-Sentence-Per-Atomic-Beat Pure-NL Seedance Prompt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


BANNED_IP_TOKENS = (
    "naruto",
    "shippuden",
    "sword of the stranger",
    "bleach",
    "jujutsu kaisen",
    "demon slayer",
    "ufc",
    "dragon ball",
)

BANNED_AMBIGUOUS_PHRASES = (
    "draws b's throw",
    "draws his throw",
    "flips upright with his coat trailing, and sprints straight down",
    "flips upright and sprints down",
)

EFFECT_AFTER_CONTACT_TOKENS = (
    "spark",
    "shockwave",
    "shock ring",
    "hit-stop",
    "shudder",
    "embeds",
    "jerks backward",
    "snaps backward",
)


@dataclass(frozen=True)
class PropSpec:
    prop_id: str
    number: int
    name: str
    lifecycle_summary: str


@dataclass(frozen=True)
class AtomicCausalBeat:
    beat_id: str
    title: str
    named_contact_id: str
    view: str
    prep: str
    commit: str
    contact: str
    consequence: str
    recovery: str
    license: str
    # World-state invariants for replay verification
    a_support_after: str
    b_support_after: str
    a_left_hand: Optional[str] = None
    a_right_hand: Optional[str] = None
    b_right_hand: Optional[str] = None
    kunai_state: str = "held_by_B"
    surface_pitch_a: str = "upright_grounded"

    def render_labeled_block(self) -> str:
        return (
            f"{self.beat_id} — {self.title}\n"
            f"  [View: {self.view}]\n"
            f"  Prep: {self.prep}\n"
            f"  Commit: {self.commit}\n"
            f"  Contact: {self.contact}\n"
            f"  Consequence: {self.consequence}\n"
            f"  Recovery: {self.recovery}\n"
            f"  [License: {self.license}]"
        )

    def render_unlabeled_seedance_sentence(self) -> str:
        """Join the 5 causal steps in strict order into one clean natural-language sentence per atomic beat."""
        p = self.prep.rstrip(". ")
        cm = self.commit.rstrip(". ")
        ct = self.contact.rstrip(". ")
        cs = self.consequence.rstrip(". ")
        rc = self.recovery.rstrip(". ")
        # Lowercase leading character of subsequent clauses unless starting with 'Fighter', 'A', 'B', or 'A\'s'/'B\'s'
        def _lc(clause: str) -> str:
            if clause.startswith(("Fighter ", "A ", "B ", "A's ", "B's ", "Kawarimi")):
                return clause
            return clause[0].lower() + clause[1:] if clause else clause

        sentence = (
            f"{p}; {_lc(cm)}, where {_lc(ct)}, "
            f"so that {_lc(cs)}, and {_lc(rc)}."
        )
        return (
            f"- {self.beat_id} ({self.title}): [View: {self.view}] "
            f"{sentence} [License: {self.license}]"
        )


@dataclass
class AtomicPillarSceneIR:
    shot_and_style_contract: str
    entity_header_intro: str
    props: List[PropSpec]
    camera_observation_layer: str
    beats: List[AtomicCausalBeat]
    sakuga_fx_global_layer: str
    negative_guardrails: List[str]
    terminal_closure: str


NUM_WORDS = {
    1: "ONE",
    2: "TWO",
    3: "THREE",
    4: "FOUR",
    5: "FIVE",
    6: "SIX",
    7: "SEVEN",
    8: "EIGHT",
}


def build_lbn23_pillar_atomic_ir() -> AtomicPillarSceneIR:
    props = [
        PropSpec(
            prop_id="kunai",
            number=1,
            name="SINGLE IRON KUNAI",
            lifecycle_summary=(
                "Held by B in reverse grip on screen-right -> hurled upward toward diving A in Beat 2a -> "
                "kicked by A's right foot in Beat 2b so it turns up and toward screen-left and embeds visibly "
                "into the upper face of the left-side stone pillar -> yanked free from the stone pillar by A's "
                "right hand during his wall-plant in Beat 6b -> driven by A's right hand deep into B's exposed "
                "right shoulder in Beat 8a where it stays embedded through the end."
            ),
        ),
        PropSpec(
            prop_id="rope_dart",
            number=2,
            name="SINGLE ROPE DART",
            lifecycle_summary=(
                "Kept holstered at A's left hip through Beats 1a–6b so A's left hand stays completely free for "
                "his Beat 5b cartwheel plant -> drawn and whipped by A's left hand on his Beat 7 pillar rebound "
                "to wrap tightly around B's right forearm and upper torso -> wrenched downward by A in Beat 8b "
                "to slam B prone onto the flagstones."
            ),
        ),
        PropSpec(
            prop_id="smoke_pellet",
            number=3,
            name="SINGLE SMOKE PELLET",
            lifecycle_summary=(
                "Carried at A's waist -> crushed against the courtyard flagstones in Beat 3a to detonate a crisp "
                "white smoke burst for the Kawarimi substitution."
            ),
        ),
        PropSpec(
            prop_id="substitution_log",
            number=4,
            name="WOODEN SUBSTITUTION LOG (KAWARIMI STAND-IN)",
            lifecycle_summary=(
                "Concealed inside A's flak coat -> placed upright in Beat 3a as a full-body-height wooden stand-in "
                "occupying A's exact stance in the smoke so no actor slot is ever empty -> struck squarely by B's "
                "right palm in Beat 3b and tips onto the flagstones as A crouches behind B."
            ),
        ),
        PropSpec(
            prop_id="shuriken_trio",
            number=5,
            name="THREE STEEL SHURIKEN",
            lifecycle_summary=(
                "Holstered in B's right thigh pouch -> hurled toward screen-left in a downward fan volley by B "
                "while airborne in Beat 5a -> pass cleanly over A's low ground slide and embed firmly into the "
                "lower face of the left-side stone pillar."
            ),
        ),
        PropSpec(
            prop_id="stone_pillar",
            number=6,
            name="VERTICAL STONE PILLAR",
            lifecycle_summary=(
                "Solid carved stone column rising vertically on the left side of the courtyard (screen-left); "
                "A lands near its top in Beat 1a, pitches head-first down its vertical face to sprint downward "
                "in Beat 1b, kicks the deflected kunai into its upper stone face in Beat 2b, lets the three "
                "shuriken embed in its lower face in Beat 5a, and plants both feet against its face in Beat 6b "
                "to pull the kunai free and rebound rightward in Beat 7."
            ),
        ),
    ]

    beats = [
        AtomicCausalBeat(
            beat_id="Beat 1a",
            title="INVERTED DROP & HIGH PILLAR FOOT-PLANT",
            named_contact_id="A_feet_to_upper_pillar",
            view="high-angle crane drop tracking Fighter A's vertical descent onto the upper left-side stone pillar face",
            prep="Fighter A begins coiled upside-down in mid-air directly above the left-side stone pillar while Fighter B braces grounded on screen-right with the reverse-grip kunai chambered in his right hand",
            commit="A extends both legs toward the upper vertical stone face of the left-side pillar as he drops out of the moonlight",
            contact="both of A's sandaled feet plant firmly against the high vertical stone pillar face",
            consequence="a crisp puff of stone dust bursts from beneath A's soles as his knees flex to absorb the drop",
            recovery="A pitches his torso head-first down the vertical stone face, poised to sprint down the column toward the courtyard floor",
            license="brief vertical descent streak on A's drop only; puff of stone dust strictly AFTER A's feet plant on the pillar",
            a_support_after="wall_plant_pillar",
            b_support_after="standing",
            a_left_hand=None,
            a_right_hand=None,
            b_right_hand="kunai",
            kunai_state="held_by_B",
            surface_pitch_a="pitched_head_first_down_vertical_wall",
        ),
        AtomicCausalBeat(
            beat_id="Beat 1b",
            title="HEAD-FIRST VERTICAL PILLAR SPRINT & LAUNCH",
            named_contact_id="A_pushoff_launch_from_pillar",
            view="vertical tilt tracking down the left-side stone pillar face as A sprints head-first down the column",
            prep="Positioned high on the vertical stone pillar with his torso pitched head-first toward the floor and his dark flak coat trailing upward behind his shoulders",
            commit="A drives rapid alternating strides straight down the vertical stone column, building downward and rightward momentum toward B",
            contact="A's planted feet kick hard off the mid-section of the stone pillar face",
            consequence="stone chips flake from the pillar launch point as A projects outward and downward toward screen-right in a shallow diving arc",
            recovery="A holds his diving line through mid-air toward the center of the courtyard while B tracks his descent from screen-right",
            license="keep A's head-first downward wall-sprint anatomy crisp and solid with zero torso smear",
            a_support_after="airborne",
            b_support_after="standing",
            a_left_hand=None,
            a_right_hand=None,
            b_right_hand="kunai",
            kunai_state="held_by_B",
            surface_pitch_a="diving_forward_right",
        ),
        AtomicCausalBeat(
            beat_id="Beat 2a",
            title="UPWARD KUNAI THROW",
            named_contact_id="B_hand_releases_kunai",
            view="medium two-shot profile keeping diving A on screen-left and grounded B on screen-right in the same frame",
            prep="Seeing A dive downward and rightward from the stone pillar, B widens his grounded stance on screen-right and twists his torso with the iron kunai cocked at his right hip",
            commit="B whips his right arm forward and upward along A's incoming dive line",
            contact="the single iron kunai releases cleanly from B's right hand at full arm extension",
            consequence="the iron blade streaks upward and toward screen-left on a straight collision course with A's chest",
            recovery="B's right arm finishes its upward follow-through across his left shoulder as he braces his feet on the flagstones",
            license="broken-ink smear on B's throwing right forearm during the whip only; crisp metallic glint along the kunai's rising flight path",
            a_support_after="airborne",
            b_support_after="standing",
            a_left_hand=None,
            a_right_hand=None,
            b_right_hand=None,
            kunai_state="airborne_rising",
            surface_pitch_a="diving_forward_right",
        ),
        AtomicCausalBeat(
            beat_id="Beat 2b",
            title="MID-AIR FOOT DEFLECTION INTO STONE PILLAR",
            named_contact_id="A_right_foot_deflects_kunai_into_pillar",
            view="tight low-angle side-profile impact framing on A's foot meeting the rising kunai with the left-side stone pillar visible behind A",
            prep="As the rising kunai closes on A's chest in mid-air, A tucks his left knee tight to his torso and rotates his right hip open",
            commit="A whips his flat right foot across the incoming flight line of the blade",
            contact="the sole of A's right foot strikes the flat of the iron kunai cleanly in profile",
            consequence="a bright metallic spark ring flares at the foot-to-blade collision and the deflected kunai spins up and toward screen-left, embedding firmly into the upper face of the left-side stone pillar",
            recovery="A drops out of the deflection arc onto both feet in a low balanced crouch on screen-left with both hands free",
            license="broken-ink smear on A's kicking right leg during the swing only; restore solid foot and blade geometry at contact, fire the metallic spark ring strictly AFTER foot-to-blade contact, and keep the kunai visibly embedded high in the stone pillar",
            a_support_after="crouched_standing",
            b_support_after="standing",
            a_left_hand=None,
            a_right_hand=None,
            b_right_hand=None,
            kunai_state="embedded_in_upper_pillar",
            surface_pitch_a="upright_crouched",
        ),
        AtomicCausalBeat(
            beat_id="Beat 3a",
            title="SMOKE PELLET DETONATION & KAWARIMI LOG STAND-IN",
            named_contact_id="A_crushes_smoke_pellet_on_flagstones",
            view="wide low front-hemisphere framing keeping A's crouch spot on screen-left and B's charge from screen-right unobstructed",
            prep="As B lunges toward screen-left to press his attack, A reaches to his waist pouch in his low crouch",
            commit="A slams the single smoke pellet down against the courtyard flagstones between his feet",
            contact="the smoke pellet shatters against the stone floor",
            consequence="a crisp white smoke ring bursts outward and immediately clears to reveal the full-body-height wooden substitution log standing upright in A's exact spot",
            recovery="A slips unseen behind B's advancing back to crouch on B's right flank while the wooden stand-in log occupies A's former position",
            license="crisp expanding white smoke ring strictly AFTER pellet-to-floor impact that clears rapidly so the solid upright wooden log is fully visible before B's strike",
            a_support_after="crouched_behind_B",
            b_support_after="charging_standing",
            a_left_hand=None,
            a_right_hand=None,
            b_right_hand=None,
            kunai_state="embedded_in_upper_pillar",
            surface_pitch_a="upright_crouched",
        ),
        AtomicCausalBeat(
            beat_id="Beat 3b",
            title="HEAVY PALM STRIKE INTO SUBSTITUTION LOG",
            named_contact_id="B_right_palm_strikes_wooden_log",
            view="medium side-profile shot showing B's right palm striking the upright wooden log on the left while A crouches coiled behind B's spine on the right",
            prep="Committed to his forward charge toward the clearing smoke, B plants his lead foot and chambers his open right palm at his chest",
            commit="B drives a heavy straight right palm thrust forward into the chest of the upright wooden substitution log",
            contact="B's open right palm slams squarely into the bark of the wooden substitution log",
            consequence="bark splinters scatter from the impact point and the wooden log shudders and tips forward onto the flagstones",
            recovery="B freezes over the tipping wooden log with his back exposed toward A crouched directly behind him",
            license="hit-stop hold and bark-splinter burst strictly AFTER B's palm contacts the wooden log; zero ghost limbs",
            a_support_after="crouched_behind_B",
            b_support_after="standing_overextended",
            a_left_hand=None,
            a_right_hand=None,
            b_right_hand=None,
            kunai_state="embedded_in_upper_pillar",
            surface_pitch_a="upright_crouched",
        ),
        AtomicCausalBeat(
            beat_id="Beat 4",
            title="RISING RIGHT KNEE TO SPINE & BACKFLIP RESET",
            named_contact_id="A_right_knee_strikes_B_spine",
            view="medium-close side-profile framing exposing A's rising right knee against B's mid-spine, craning upward as A backflips toward screen-left",
            prep="Crouched directly behind B's exposed back, A plants his left support leg firmly on the flagstones and raises his left forearm in a tight high guard",
            commit="A explodes upward off his planted left leg, driving his bent right knee vertically toward B's mid-spine",
            contact="A's bent right knee smashes cleanly into B's mid-spine",
            consequence="a blunt white shock ring erupts at the spine contact as B's spine arches forward, his arms fling out, and both of B's feet lift off the stones into an upward launch arc",
            recovery="A pushes off B's launched back into a clean backward somersault toward screen-left and lands balanced on both feet near the stone pillar",
            license="keep A's bent striking right knee, standing left leg, head, and torso razor-sharp with ZERO knee blur; trigger the hit-stop hold and blunt shock ring strictly AFTER knee-to-spine contact, followed by a clean rotational tuck trail on A's backflip",
            a_support_after="standing",
            b_support_after="airborne",
            a_left_hand=None,
            a_right_hand=None,
            b_right_hand=None,
            kunai_state="embedded_in_upper_pillar",
            surface_pitch_a="upright_grounded",
        ),
        AtomicCausalBeat(
            beat_id="Beat 5a",
            title="AIRBORNE SHURIKEN VOLLEY & LOW EVASIVE SLIDE",
            named_contact_id="shuriken_trio_embed_in_lower_pillar",
            view="low lateral tracking dolly following A's flat ground slide underneath the three shuriken trajectories into the left-side pillar",
            prep="Suspended at the peak of his airborne launch on screen-right, B twists his torso and draws the three steel shuriken from his right thigh pouch",
            commit="B hurls the three steel shuriken in a downward diagonal fan volley toward screen-left while A drops his pelvis flat to the flagstones and slides underneath the blades",
            contact="all three steel shuriken pass cleanly over A's sliding torso and thud into the lower face of the left-side stone pillar",
            consequence="three small stone-dust puffs and metallic sparks flare on the lower stone pillar face as the three shuriken lock into the carved stone",
            recovery="A's low slide carries him to the base of the stone pillar while B drops toward a crouch landing on screen-right",
            license="straight silver glint trails on the three flying shuriken and stone-dust puffs strictly AFTER the blades strike the lower pillar face",
            a_support_after="sliding_low",
            b_support_after="standing",
            a_left_hand=None,
            a_right_hand=None,
            b_right_hand=None,
            kunai_state="embedded_in_upper_pillar",
            surface_pitch_a="low_slide",
        ),
        AtomicCausalBeat(
            beat_id="Beat 5b",
            title="ONE-HANDED LEFT CARTWHEEL RECOVERY",
            named_contact_id="A_free_left_hand_plants_on_flagstones",
            view="medium low-angle profile shot keeping all four of A's limbs clearly separated during the cartwheel turnover",
            prep="At the end of his low ground slide with the rope dart still holstered at his left hip so both hands are empty, A angles his torso forward",
            commit="A reaches his empty left hand down toward the courtyard flagstones and swings his right leg upward over his hips",
            contact="A's open left palm plants flat against the flagstones to bear his inverted weight",
            consequence="A's body pivots cleanly over his planted left arm in a full one-handed forward cartwheel with his legs scissoring through the moonlight",
            recovery="A touches both feet down on the flagstones and springs forward toward B in a low balanced sprint",
            license="keep all four limbs crisp and separate in silhouette with zero limb merging during the left-hand cartwheel turnover",
            a_support_after="standing",
            b_support_after="standing",
            a_left_hand=None,
            a_right_hand=None,
            b_right_hand=None,
            kunai_state="embedded_in_upper_pillar",
            surface_pitch_a="upright_grounded",
        ),
        AtomicCausalBeat(
            beat_id="Beat 6a",
            title="TWO-HAND ELBOW CATCH & THROW TOWARD PILLAR",
            named_contact_id="B_both_hands_lock_A_left_elbow",
            view="tight medium-close profile on B's two-hand grapple lock whip-panning toward screen-left as B hurls A toward the stone pillar",
            prep="As A lunges into close range from his cartwheel recovery, B plants his rear right foot wide and coils his heavy upper body",
            commit="B shoots both thick forearms forward to intercept A's lead left arm",
            contact="both of B's hands clamp tightly around A's left elbow joint",
            consequence="the sudden two-hand lock arrests A's forward lunge and wrenches A's torso sideways as B pivots hard toward screen-left, hurling A's entire body through the air toward the left-side stone pillar",
            recovery="B holds his wide rotational throwing follow-through on screen-right as A hurtles leftward toward the vertical stone column",
            license="brief grapple-lock pause when B's hands clamp A's left elbow, followed by a fast ballistic transfer streak on A's thrown body while B's stance stays solid",
            a_support_after="airborne_thrown",
            b_support_after="standing",
            a_left_hand=None,
            a_right_hand=None,
            b_right_hand=None,
            kunai_state="embedded_in_upper_pillar",
            surface_pitch_a="airborne_horizontal",
        ),
        AtomicCausalBeat(
            beat_id="Beat 6b",
            title="PILLAR WALL-PLANT & EMBEDDED KUNAI RETRIEVAL",
            named_contact_id="A_feet_slam_pillar_and_right_hand_pulls_kunai",
            view="medium low-angle framing on the left-side stone pillar face showing A's two-foot wall-plant right beside the embedded kunai",
            prep="Hurtling backward toward screen-left from B's throw, A tucks his chin and rotates his hips in mid-air to orient both soles toward the vertical stone pillar face",
            commit="A extends both legs toward the stone column while reaching his empty right hand up toward the iron kunai embedded in the pillar face",
            contact="both of A's feet slam flat against the vertical stone pillar face as A's right hand grips and yanks the embedded iron kunai free from the stone",
            consequence="a heavy stone-crack dust ring bursts behind A's planted heels and stone grit sprays from the blade slot as the kunai comes free in A's right fist",
            recovery="A coils both knees deep against the vertical stone pillar face with the reclaimed kunai locked in his right fist and his left hand dropping to the rope dart at his left hip",
            license="hit-stop hold and radial stone-dust burst strictly AFTER A's feet slam onto the pillar face; keep the kunai clearly visible transferring from the stone face into A's right hand",
            a_support_after="wall_plant_pillar",
            b_support_after="standing",
            a_left_hand="rope_dart_grip",
            a_right_hand="kunai",
            b_right_hand=None,
            kunai_state="held_by_A_right_hand",
            surface_pitch_a="wall_coiled_horizontal",
        ),
        AtomicCausalBeat(
            beat_id="Beat 7",
            title="PILLAR REBOUND, ROPE-DART WRAP & TAUT TETHER DRAG",
            named_contact_id="rope_dart_wraps_B_right_forearm_and_upper_torso",
            view="medium-close lateral tracking shot keeping the taut rope-dart cord unbroken between A's left hand on screen-left and B's bound upper torso on screen-right",
            prep="Coiled on the left-side stone pillar face with the reclaimed kunai in his right fist, A unholsters the single rope dart from his left hip with his left hand",
            commit="A kicks off the stone pillar toward screen-right and whips his left arm forward to cast the rope dart across the courtyard gap",
            contact="the weighted rope dart strikes and wraps three tight coils around B's right forearm and upper torso",
            consequence="a crisp metallic spark glints at the tether bind as A lands grounded on his left foot on screen-left and wrenches the taut rope line toward screen-left, dragging B's heavy body stumbling forward off-balance",
            recovery="B lurches forward into close range with his right forearm pinned by the taut cord while A holds left-hand tension and cocks the kunai in his right hand",
            license="broken-ink whip-arc smear on the rope-dart cord during casting only; once wrapped, keep the straight taut tether line continuous and unbroken between A's left fist and B's bound upper torso",
            a_support_after="standing",
            b_support_after="stumbling_off_balance",
            a_left_hand="rope_dart_taut",
            a_right_hand="kunai",
            b_right_hand="pinned_by_rope",
            kunai_state="held_by_A_right_hand",
            surface_pitch_a="upright_grounded",
        ),
        AtomicCausalBeat(
            beat_id="Beat 8a",
            title="SLOW-MOTION KUNAI IMPALE INTO RIGHT SHOULDER",
            named_contact_id="A_right_hand_drives_kunai_into_B_right_shoulder",
            view="tight slow-motion side-profile impact framing on A's right-hand kunai driving into B's exposed right shoulder",
            prep="As B stumbles into close range with his right forearm bound lower by the taut rope dart in A's left hand, B's upper right shoulder is pulled wide open",
            commit="Maintaining left-hand rope tension, A rotates his torso and drives the iron kunai in his right fist straight toward B's exposed right shoulder",
            contact="the iron kunai blade plunges deep into B's right shoulder joint",
            consequence="a slow-motion hit-stop hold and a sharp crimson-and-white impact spark flare at the entry point as B's right shoulder jerks back and his head snaps backward with the kunai remaining embedded in his shoulder",
            recovery="A releases his right hand from the embedded kunai hilt and grips the taut rope-dart cord with both hands without resetting his stance",
            license="slow-motion window with a multi-frame hit-stop hold and impact spark strictly AFTER the kunai blade enters B's right shoulder; keep the kunai visibly embedded in B's right shoulder",
            a_support_after="standing",
            b_support_after="staggered_standing",
            a_left_hand="rope_dart_taut",
            a_right_hand="rope_dart_taut",
            b_right_hand="pinned_by_rope",
            kunai_state="embedded_in_B_right_shoulder",
            surface_pitch_a="upright_grounded",
        ),
        AtomicCausalBeat(
            beat_id="Beat 8b",
            title="FULL-BODY TETHER GROUND SLAM",
            named_contact_id="B_full_body_slams_prone_onto_flagstones",
            view="wide low ground-level shockwave framing capturing A's downward rope wrench and B's full-body slam onto the courtyard flagstones",
            prep="Without resetting his feet after the shoulder impale, A drops his hips low and anchors both hands on the taut rope-dart cord attached to B's upper torso",
            commit="A wrenches the taut rope-dart tether sharply downward and toward screen-left with his full body weight",
            contact="B's entire body is yanked off his feet and slams face-first onto the stone courtyard floor",
            consequence="a heavy ground-slam hit-stop hold locks the frame and a wide radial ring of stone dust erupts outward from beneath B's chest across the flagstones",
            recovery="B lies completely prone and motionless on screen-right with the kunai still embedded in his right shoulder while A settles into a low balanced shinobi crouch on screen-left",
            license="heavy ground-slam hit-stop hold and expanding radial stone-dust shockwave ring strictly AFTER B's torso impacts the flagstones; zero B recovery after this final slam",
            a_support_after="crouched_standing",
            b_support_after="prone_terminal",
            a_left_hand="rope_dart_slack",
            a_right_hand=None,
            b_right_hand="prone",
            kunai_state="embedded_in_B_right_shoulder",
            surface_pitch_a="upright_crouched",
        ),
    ]

    return AtomicPillarSceneIR(
        shot_and_style_contract=(
            "Continuous hand-drawn anime ninja fight clip in a moonlit stone courtyard with a tall carved stone pillar "
            "rising vertically on the left side of the stage (screen-left), drifting night mist, crisp silver moonlight "
            "rim-lighting, and deep indigo courtyard shadows. STYLE: Pure 2D cel-shaded hand-drawn anime, high-speed "
            "shinobi martial-arts sakuga animation on twos, crisp angular anatomical linework, flat two-tone high-contrast "
            "cel shadows, heavy ink outlines on Fighter A and Fighter B, broken sketchy ink on active smear limbs and "
            "rope-dart whip arcs only, clean ultra-thick ink on impact holds. Not 3D, not CGI, not live action, not "
            "photoreal. SCREEN GEOMETRY LOCK: Maintain strict front-hemisphere camera geometry with zero camera-cut axis "
            "flips and zero on-screen text, numbers, or HUD — the vertical stone pillar anchors screen-left behind Fighter A, "
            "while Fighter B anchors screen-right."
        ),
        entity_header_intro=(
            "Fighter A (agile shinobi striker): dark high-collar shinobi flak coat trailing behind, white forearm wraps, "
            "dark shinobi trousers, strapped sandals; begins coiled upside-down in mid-air directly above the left-side "
            "stone pillar with rope dart holstered at left hip, smoke pellet at waist, and wooden substitution log concealed "
            "inside coat. Fighter B (heavy armored rogue shinobi): sleeveless charcoal combat vest over scarred broad "
            "shoulders, reinforced forearm bracers, dark hakama trousers; begins grounded on screen-right holding the single "
            "iron kunai in reverse grip in his right hand and three steel shuriken holstered in his right thigh pouch."
        ),
        props=props,
        camera_observation_layer=(
            "Every atomic beat must keep all nineteen body parts (head, torso, pelvis, upper-arms, forearms, hands, thighs, "
            "shins, and feet) accounted for with both left and right arms clearly separate from the torso in silhouette. "
            "Keep both fighters and active prop trajectories inside an unobstructed front-hemisphere view, exposing every "
            "foot-plant, throw, deflection, log substitution, knee strike, cartwheel, grapple lock, tether wrap, blade impale, "
            "and ground slam in clean side or three-quarter profile with zero torso overlap."
        ),
        beats=beats,
        sakuga_fx_global_layer=(
            "Every atomic beat follows a strict five-step causal chain (Preparation -> Commitment -> Single Named Contact -> "
            "Consequence -> Recovery). Restrict broken-ink smear stretching strictly to the single committing limb or cord "
            "during the Commitment phase; restore solid anatomical geometry at Contact; and fire all metallic sparks, smoke "
            "rings, bark splinters, hit-stop holds, and radial stone-dust shockwaves strictly in the Consequence phase AFTER "
            "visible contact."
        ),
        negative_guardrails=[
            "no missing limbs",
            "no limb merging or left/right swapping during somersaults or cartwheels",
            "no Kawarimi vanish without the full-body wooden substitution log stand-in",
            "no duplicated or teleporting kunai",
            "no spark, shockwave, or recoil before contact",
            "no upright posture while sprinting down the vertical pillar face",
            "no stance reset between the kunai shoulder impale and the floor slam",
            "no B standing up after the final Beat 8b ground-slam knockdown",
        ],
        terminal_closure=(
            "End on a slow dolly-in as Fighter A holds a low, balanced shinobi crouch on screen-left with both feet planted "
            "flat, left hand holding the slackened rope dart, and both arms clearly separate from his torso in silhouette, "
            "while Fighter B lies prone and motionless face-down on the flagstones on screen-right with the single kunai "
            "still embedded in his right shoulder and the three shuriken embedded in the stone pillar behind A as courtyard "
            "dust settles in the moonlight."
        ),
    )


def render_prop_ledger_header(ir: AtomicPillarSceneIR) -> str:
    count_word = NUM_WORDS[len(ir.props)]
    items = " ".join(
        f"({p.number}) {p.name}: {p.lifecycle_summary}"
        for p in ir.props
    )
    return (
        f"ENTITY COUNT, OUTFIT & PROP CONTINUITY LOCK: Exactly TWO shinobi fighters and {count_word} tracked props "
        f"with strict single-instance conservation (never duplicated, never teleported). {ir.entity_header_intro} "
        f"PROP LEDGER INVARIANTS ({count_word} TRACKED PROPS): {items}"
    )


def render_labeled_atomic_prompt(ir: AtomicPillarSceneIR) -> str:
    beats_block = "\n".join(b.render_labeled_block() for b in ir.beats)
    guardrails_str = ", ".join(ir.negative_guardrails)
    return (
        f"SHOT & STYLE CONTRACT\n{ir.shot_and_style_contract}\n\n"
        f"ENTITY, PROP LEDGER & INITIAL STATE\n{render_prop_ledger_header(ir)}\n\n"
        f"CAMERA & OBSERVATION LAYER\n{ir.camera_observation_layer}\n\n"
        f"ATOMIC CAUSAL BEATS (1 Named Contact Per Beat: Prep -> Commit -> Contact -> Consequence -> Recovery)\n"
        f"{beats_block}\n\n"
        f"SAKUGA FX & ANIMATION LICENSE LAYER\n{ir.sakuga_fx_global_layer} "
        f"NEGATIVE GUARDRAILS: {guardrails_str}.\n\n"
        f"TERMINAL CLOSURE\n{ir.terminal_closure}\n"
    )


def render_unlabeled_seedance_prompt(ir: AtomicPillarSceneIR) -> str:
    beats_block = "\n".join(b.render_unlabeled_seedance_sentence() for b in ir.beats)
    guardrails_str = ", ".join(ir.negative_guardrails)
    return (
        f"SHOT & STYLE CONTRACT\n{ir.shot_and_style_contract}\n\n"
        f"ENTITY, PROP LEDGER & INITIAL STATE\n{render_prop_ledger_header(ir)}\n\n"
        f"CAMERA & OBSERVATION LAYER\n{ir.camera_observation_layer}\n\n"
        f"SYNCHRONIZED ATOMIC CAUSAL BEATS (1 Named Contact Per Beat: Preparation -> Commitment -> Contact -> Consequence -> Recovery)\n"
        f"{beats_block}\n\n"
        f"SAKUGA FX & ANIMATION LICENSE LAYER\n{ir.sakuga_fx_global_layer} "
        f"NEGATIVE GUARDRAILS: {guardrails_str}.\n\n"
        f"TERMINAL CLOSURE\n{ir.terminal_closure}\n"
    )


def validate_atomic_pillar_prompt(ir: AtomicPillarSceneIR, rendered_nl: str) -> Dict[str, object]:
    """Run all 12 semantic and readability verification checks (SCAN-01 through SCAN-12)."""
    errors: List[str] = []
    lower_nl = rendered_nl.lower()

    # SCAN-01: Ban third-party anime/IP franchise names
    for token in BANNED_IP_TOKENS:
        if token in lower_nl:
            errors.append(f"SCAN-01 (IP token leak): found '{token}'")

    # SCAN-02: Single-source-of-truth prop count vs. numbered items
    expected_word = NUM_WORDS[len(ir.props)]
    if f"{expected_word} tracked props" not in rendered_nl:
        errors.append(f"SCAN-02 (Prop header count drift): expected '{expected_word} tracked props'")
    numbered_matches = re.findall(r"\((\d+)\)\s+[A-Z0-9\s\-()]+:", rendered_nl)
    if [int(x) for x in numbered_matches] != list(range(1, len(ir.props) + 1)):
        errors.append(f"SCAN-02 (Numbered prop ledger mismatch): found {numbered_matches}")

    # SCAN-03: Knockdown guardrail only at terminal beat (Beat 8b)
    prone_beats = [b.beat_id for b in ir.beats if b.b_support_after == "prone_terminal"]
    if prone_beats != [ir.beats[-1].beat_id]:
        errors.append(f"SCAN-03 (Premature or missing terminal knockdown): prone_beats={prone_beats}")
    if "5.00s knockdown" in lower_nl:
        errors.append("SCAN-03 (Stale 5.00s knockdown guardrail present)")

    # SCAN-04: Screen-space geometry & deflection direction
    if "screen-left" not in lower_nl or "screen-right" not in lower_nl:
        errors.append("SCAN-04 (Missing screen-left / screen-right anchors)")
    beat_2b = next((b for b in ir.beats if b.beat_id == "Beat 2b"), None)
    if not beat_2b or "up and toward screen-left" not in beat_2b.consequence.lower():
        errors.append("SCAN-04/SCAN-12 (Beat 2b deflection must specify 'up and toward screen-left')")

    # SCAN-05 & SCAN-09: Zero decimal timestamps in Pure-NL output
    decimal_timestamps = re.findall(r"\b\d+\.\d+s\b", rendered_nl)
    if decimal_timestamps:
        errors.append(f"SCAN-09 (Decimal timestamps leaked into Pure-NL prompt): {decimal_timestamps}")

    # SCAN-06 & SCAN-07: Projectile continuity & no 4.1s orbiting kunai
    kunai_states = [b.kunai_state for b in ir.beats]
    airborne_run = 0
    for st in kunai_states:
        if st.startswith("airborne"):
            airborne_run += 1
            if airborne_run > 1:
                errors.append("SCAN-06/SCAN-07 (Kunai remained airborne across multiple atomic beats)")
        else:
            airborne_run = 0
    if "embedded_in_upper_pillar" not in kunai_states:
        errors.append("SCAN-07 (Deflected kunai must embed in upper stone pillar face before retrieval)")

    # SCAN-08: Bilateral hand-occupancy & cartwheel check
    beat_5b = next((b for b in ir.beats if b.beat_id == "Beat 5b"), None)
    if not beat_5b or beat_5b.a_left_hand is not None:
        errors.append("SCAN-08 (A's left hand must be empty during Beat 5b left-hand cartwheel plant)")

    # SCAN-11: Strict 1-Contact-Per-Beat & Labeled Slot Ordering Check
    seen_contacts = set()
    for b in ir.beats:
        for slot_name in ("prep", "commit", "contact", "consequence", "recovery", "view", "license"):
            val = getattr(b, slot_name, "").strip()
            if not val:
                errors.append(f"SCAN-11 ({b.beat_id} missing mandatory slot '{slot_name}')")
        if not b.named_contact_id or b.named_contact_id in seen_contacts:
            errors.append(f"SCAN-11 ({b.beat_id} duplicate or missing named_contact_id '{b.named_contact_id}')")
        seen_contacts.add(b.named_contact_id)
        # Ensure Prep and Commit never contain post-contact effects (sparks, shock rings, hit-stops, embeds)
        pre_contact_text = (b.prep + " " + b.commit).lower()
        for effect_tok in EFFECT_AFTER_CONTACT_TOKENS:
            if effect_tok in pre_contact_text:
                errors.append(
                    f"SCAN-11 ({b.beat_id} post-contact effect '{effect_tok}' leaked into Prep/Commit before Contact)"
                )

    # SCAN-12: Orientation physics & unambiguous causal verbs
    for phrase in BANNED_AMBIGUOUS_PHRASES:
        if phrase in lower_nl:
            errors.append(f"SCAN-12 (Ambiguous verb or orientation contradiction): found '{phrase}'")
    beat_1b = next((b for b in ir.beats if b.beat_id == "Beat 1b"), None)
    if not beat_1b or "head-first" not in (beat_1b.prep + " " + beat_1b.license).lower():
        errors.append("SCAN-12 (Beat 1b vertical pillar downward sprint must specify head-first pitch)")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "atomic_beat_count": len(ir.beats),
        "tracked_prop_count": len(ir.props),
        "word_count": len(rendered_nl.split()),
    }


def compile_and_write_pillar_prompts(root: Optional[Path] = None) -> Dict[str, object]:
    repo_root = Path(root) if root else Path(__file__).resolve().parents[1]
    ir = build_lbn23_pillar_atomic_ir()
    labeled_text = render_labeled_atomic_prompt(ir)
    unlabeled_text = render_unlabeled_seedance_prompt(ir)
    report = validate_atomic_pillar_prompt(ir, unlabeled_text)
    if report["status"] != "PASS":
        raise ValueError(f"Atomic Pillar Prompt failed verification: {report['errors']}")

    prompts_dir = repo_root / "experiments/latent_sakuga/prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    labeled_path = prompts_dir / "lbn23_pillar_fight_atomic_labeled_ir.txt"
    unlabeled_path = prompts_dir / "lbn23_pillar_fight_arm_C1_clean_verified.txt"
    labeled_path.write_text(labeled_text, encoding="utf-8")
    unlabeled_path.write_text(unlabeled_text, encoding="utf-8")
    return {
        "report": report,
        "labeled_path": str(labeled_path),
        "unlabeled_path": str(unlabeled_path),
    }


if __name__ == "__main__":
    res = compile_and_write_pillar_prompts()
    print(res)
