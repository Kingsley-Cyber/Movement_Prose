"""§6.1 Kinetic Chain Rules (V18) — DiT-visible body-part link chains.

A kinetic chain is the FOURTH segment of a beat's causal string:

    C02: requires STATE -> preserves LOCKS -> chain: LINK > LINK > LINK > LINK -> causes NEXT

Every LINK is one body part + one visible on-screen verb (pivots, snaps, drives,
whips, extends, lands — never "torque transfers" or any other physics abstraction),
ordered ground-up (feet > knee > hips > torso > shoulder > striking limb) because a
DiT weights word order heavily. A chain is 3-5 links and must END on the impact:
the last link is the one the model draws strongest.

Two separators, two meanings — never mixed:

    ' > '   kinetic chain links, ONLY inside the 'chain:' segment. Layer 2 also
            keeps the pre-existing laban movement chain ("chain":"C01 > C02 > ...")
            whose ' > ' separators are grandfathered in by scan_prompt_v18.
    ' -> '  causal arrows between the four causal-string segments

`chain_frames` (frame offsets such as [0, 2, 3, 4, 5]) is internal metadata the
compiler reads to schedule the link beats. Frame numbers are never emitted into
prompt text: a DiT ignores bare numbers inside prose, they are pure noise.

V18 sub-rules (all reported under validator code V18):

    links      3-5 links, '>' separated, '>' used nowhere else
    body       every link names exactly one acting body part (plus at most one target)
    verb       every link carries a visible action verb
    ground     the chain starts at the ground contact (feet/knee on the floor)
    order      link ranks never decrease: feet > knee > hips > torso > shoulder > limb
    impact     the final link ends on the impact with a terminal verb
    digits     no digits inside a chain segment (frame offsets stay internal)
    abstract   no physics abstractions (torque/momentum/force/...) inside a link
    frames     chain_frames offsets stay internal: never emitted as prompt text
"""

import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

CHAIN_RULE_CODE = "V18"
CHAIN_MIN_LINKS = 3
CHAIN_MAX_LINKS = 5
CHAIN_SEPARATOR = ">"
CHAIN_FRAME_KEY = "chain_frames"
CHAIN_KEY = "chain"
MAX_BODY_PARTS_PER_LINK = 2

# A ground-up chain starts on the floor or explosive hip hinge.
# Rank 1 = ground contact, rank 2 = knee, rank 3 = hips (for fast-start strike chains).
GROUND_CONTACT_MAX_RANK = 3
STRIKING_LIMB_RANK = 7

# Ground-up ranks. Foot/knee/arm tokens are rank 1-6 when they bear or carry the
# body and rank 7 when they ARE the striking limb that finishes the chain, so a
# low sweep ("... > rear heel cuts the ankle") is legal ground-up order.
BODY_PART_RANKS: Dict[str, Tuple[int, ...]] = {
    # rank 1: ground contact (or the finishing leg strike)
    "foot": (1, STRIKING_LIMB_RANK),
    "feet": (1, STRIKING_LIMB_RANK),
    "heel": (1, STRIKING_LIMB_RANK),
    "heels": (1, STRIKING_LIMB_RANK),
    "toe": (1, STRIKING_LIMB_RANK),
    "toes": (1, STRIKING_LIMB_RANK),
    "ball of the foot": (1, STRIKING_LIMB_RANK),
    "sole": (1, STRIKING_LIMB_RANK),
    "ankle": (1, STRIKING_LIMB_RANK),
    "ankles": (1, STRIKING_LIMB_RANK),
    "shin": (1, STRIKING_LIMB_RANK),
    "shins": (1, STRIKING_LIMB_RANK),
    "calf": (1, STRIKING_LIMB_RANK),
    "calves": (1, STRIKING_LIMB_RANK),
    # rank 2: knee hinge (or the finishing knee strike)
    "knee": (2, STRIKING_LIMB_RANK),
    "knees": (2, STRIKING_LIMB_RANK),
    "kneecap": (2, STRIKING_LIMB_RANK),
    "thigh": (2, STRIKING_LIMB_RANK),
    "thighs": (2, STRIKING_LIMB_RANK),
    # rank 3: hips
    "hip": (3,),
    "hips": (3,),
    "pelvis": (3,),
    "waist": (3,),
    "glutes": (3,),
    # rank 4: torso
    "torso": (4,),
    "spine": (4,),
    "chest": (4,),
    "ribs": (4,),
    "ribcage": (4,),
    "back": (4,),
    "trunk": (4,),
    "core": (4,),
    # rank 5: shoulder
    "shoulder": (5,),
    "shoulders": (5,),
    # rank 6: arm chain (rank 7 when it is the striking limb)
    "arm": (6, STRIKING_LIMB_RANK),
    "arms": (6, STRIKING_LIMB_RANK),
    "elbow": (6, STRIKING_LIMB_RANK),
    "elbows": (6, STRIKING_LIMB_RANK),
    "forearm": (6, STRIKING_LIMB_RANK),
    "forearms": (6, STRIKING_LIMB_RANK),
    "wrist": (6, STRIKING_LIMB_RANK),
    "wrists": (6, STRIKING_LIMB_RANK),
    "fist": (6, STRIKING_LIMB_RANK),
    "fists": (6, STRIKING_LIMB_RANK),
    "hand": (6, STRIKING_LIMB_RANK),
    "hands": (6, STRIKING_LIMB_RANK),
    "palm": (6, STRIKING_LIMB_RANK),
    "palms": (6, STRIKING_LIMB_RANK),
    "knuckle": (6, STRIKING_LIMB_RANK),
    "knuckles": (6, STRIKING_LIMB_RANK),
    "glove": (6, STRIKING_LIMB_RANK),
    "gloves": (6, STRIKING_LIMB_RANK),
    # rank 7: head, and the target surface named by an impact link
    "head": (7,),
    "chin": (7,),
    "jaw": (7,),
    "jawline": (7,),
    "cheek": (7,),
    "cheekbone": (7,),
    "temple": (7,),
    "neck": (7,),
    "face": (7,),
    "skull": (7,),
    "nose": (7,),
    "throat": (7,),
}

# Visible on-screen verbs (base forms; 's/es/ed/ing' inflections match too).
VISIBLE_VERBS: Set[str] = {
    "pivot", "snap", "drive", "whip", "extend", "land", "plant", "push", "pull",
    "turn", "twist", "coil", "uncoil", "rise", "drop", "sink", "dip", "roll",
    "slide", "step", "glide", "sweep", "arc", "cross", "open", "close", "tuck",
    "brace", "lock", "slam", "dig", "fold", "buckle", "collapse", "jolt", "lift",
    "straighten", "flex", "hunch", "lean", "cock", "chamber", "thread", "punch",
    "throw", "catch", "stop", "halt", "settle", "square", "spin", "reach", "hook",
    "wrap", "clamp", "press", "cover", "slip", "meet", "cut", "swing", "load",
    "clear", "shoot", "trap", "pin", "rack", "gather", "crash", "bury", "flare",
    "splay", "surge", "pitch", "rock", "bend", "curl", "arch", "follow", "duck",
    "lift", "shelve", "kick", "switch", "hop", "stomp", "tip", "topple", "lunge",
    "skid",
}

# The final link is drawn strongest: it must land the impact, not wind it up.
TERMINAL_IMPACT_VERBS: Set[str] = {
    "land", "connect", "snap", "fold", "buckle", "collapse", "jolt", "sink",
    "slam", "crash", "bury", "dig", "whip", "stop", "catch", "meet", "lock",
    "plant", "settle", "tuck", "press", "wrap", "clamp", "cover", "halt", "rip",
    "slip", "drop", "shoot", "arrive", "pin", "trap", "cut", "thread", "gather",
    "rack", "shelve", "clear", "stomp", "switch",
}

# Physics abstractions are unrenderable: a DiT cannot draw a torque transfer.
FORBIDDEN_ABSTRACTIONS: Set[str] = {
    "torque", "momentum", "impulse", "inertia", "acceleration", "velocity",
    "energy", "force", "forces", "physics", "vector", "vectors", "friction",
    "gravity", "leverage", "biomechanics", "load path", "kinetic energy",
    "power transfer", "transfers",
}


def _build_token_regex(tokens: Sequence[str]) -> "re.Pattern[str]":
    """Word-boundary alternation, longest token first so multi-word parts win."""
    ordered = sorted(tokens, key=len, reverse=True)
    return re.compile(r"\b(?:" + "|".join(re.escape(t) for t in ordered) + r")\b", re.IGNORECASE)


def _build_verb_regex(verbs: Sequence[str]) -> "re.Pattern[str]":
    ordered = sorted(verbs, key=len, reverse=True)
    stem = "|".join(re.escape(v) for v in ordered)
    return re.compile(r"\b(?:" + stem + r")(?:s|es|ed|d|ing)?\b", re.IGNORECASE)


_BODY_PART_RE = _build_token_regex(list(BODY_PART_RANKS))
_VISIBLE_VERB_RE = _build_verb_regex(sorted(VISIBLE_VERBS))
_TERMINAL_VERB_RE = _build_verb_regex(sorted(TERMINAL_IMPACT_VERBS))
_ABSTRACTION_RE = _build_token_regex(sorted(FORBIDDEN_ABSTRACTIONS))
_DIGIT_RE = re.compile(r"\d")

# 'chain:' inside the emitted causal string, terminated by the causal arrow.
CHAIN_SEGMENT_RE = re.compile(r"chain:")
CHAIN_SEGMENT_END_RE = re.compile(r"->\s*causes")
# Emitted causal strings: "causal":"C01: requires ... -> causes ..."
CAUSAL_FIELD_RE = re.compile(r'"causal":"(?P<body>[^"]*)"')
# Pre-existing laban movement-chain value in Layer 2 ("chain":"C01_beat > C02_beat").
MOVEMENT_CHAIN_VALUE_RE = re.compile(r'"chain":"([^"]*)"')
# Layer 1 legend placeholders ("MOVEMENT LANGUAGE: <seconds> <performer>").
PLACEHOLDER_TOKEN_RE = re.compile(r"<[^<>]*>")


def split_chain(chain: str) -> List[str]:
    """Split a chain string on the '>' separator into stripped links."""
    return [link.strip() for link in chain.split(CHAIN_SEPARATOR) if link.strip()]


def body_parts_in(link: str) -> List[str]:
    """All body-part tokens in a link, left to right."""
    return [m.group(0).lower() for m in _BODY_PART_RE.finditer(link)]


def actor_ranks(link: str) -> List[int]:
    """Ground-up ranks the acting (first-named) body part may legally occupy."""
    m = _BODY_PART_RE.search(link)
    if not m:
        return []
    return list(BODY_PART_RANKS.get(m.group(0).lower(), ()))


def visible_verbs_in(link: str) -> List[str]:
    return [m.group(0).lower() for m in _VISIBLE_VERB_RE.finditer(link)]


def terminal_verbs_in(link: str) -> List[str]:
    return [m.group(0).lower() for m in _TERMINAL_VERB_RE.finditer(link)]


def abstractions_in(link: str) -> List[str]:
    return [m.group(0).lower() for m in _ABSTRACTION_RE.finditer(link)]


def has_digits(text: str) -> Optional[str]:
    m = _DIGIT_RE.search(text or "")
    return m.group(0) if m else None


def validate_chain_frames(
    frames: Any,
    *,
    owner: str = CHAIN_KEY,
    link_count: int = 0,
    required: bool = False,
) -> List[Tuple[str, str]]:
    """V18 frames: chain_frames offsets are internal, integer, and one per link."""
    errors: List[Tuple[str, str]] = []
    if frames is None or frames == []:
        if required:
            errors.append(
                (
                    CHAIN_RULE_CODE,
                    f"{owner}: missing '{CHAIN_FRAME_KEY}' frame offsets (internal timing, one per link)",
                )
            )
        return errors
    if not isinstance(frames, (list, tuple)):
        return [
            (
                CHAIN_RULE_CODE,
                f"{owner}: '{CHAIN_FRAME_KEY}' must be a list of frame offsets, got {type(frames).__name__}",
            )
        ]
    bad = [f for f in frames if isinstance(f, bool) or not isinstance(f, int) or f < 0]
    if bad:
        errors.append((CHAIN_RULE_CODE, f"{owner}: '{CHAIN_FRAME_KEY}' offsets must be non-negative integers, got {bad}"))
        return errors
    if link_count and len(frames) != link_count:
        errors.append(
            (
                CHAIN_RULE_CODE,
                f"{owner}: '{CHAIN_FRAME_KEY}' has {len(frames)} offsets for {link_count} links (one per link)",
            )
        )
    if frames and frames[0] != 0:
        errors.append((CHAIN_RULE_CODE, f"{owner}: '{CHAIN_FRAME_KEY}' must start at frame offset 0, got {frames[0]}"))
    for i in range(1, len(frames)):
        if frames[i] <= frames[i - 1]:
            errors.append(
                (
                    CHAIN_RULE_CODE,
                    f"{owner}: '{CHAIN_FRAME_KEY}' offsets must strictly increase, got {list(frames)}",
                )
            )
            break
    return errors


def validate_kinetic_chain(
    chain: Any,
    *,
    owner: str = CHAIN_KEY,
    chain_frames: Any = None,
    require_frames: bool = False,
) -> List[Tuple[str, str]]:
    """V18: validate one kinetic chain (card default, beat override, or emitted segment).

    Returns a list of (code, message) tuples; all of them use code V18.
    """
    errors: List[Tuple[str, str]] = []

    if not isinstance(chain, str) or not chain.strip():
        return [
            (
                CHAIN_RULE_CODE,
                f"{owner}: missing kinetic chain (every move card and beat needs a 'chain' string)",
            )
        ]

    links = split_chain(chain)

    if not (CHAIN_MIN_LINKS <= len(links) <= CHAIN_MAX_LINKS):
        errors.append(
            (
                CHAIN_RULE_CODE,
                f"{owner}: kinetic chain has {len(links)} links; rule requires {CHAIN_MIN_LINKS}-{CHAIN_MAX_LINKS}",
            )
        )

    ranks_seen: List[List[int]] = []
    for i, link in enumerate(links, start=1):
        parts = body_parts_in(link)
        ranks = actor_ranks(link)
        verbs = visible_verbs_in(link)
        abstract = abstractions_in(link)

        if not parts:
            errors.append((CHAIN_RULE_CODE, f"{owner}: link {i} '{link}' names no body part"))
        elif len(parts) > MAX_BODY_PARTS_PER_LINK:
            errors.append(
                (
                    CHAIN_RULE_CODE,
                    f"{owner}: link {i} '{link}' names {len(parts)} body parts; keep one acting part (plus at most one target)",
                )
            )
        if not verbs:
            errors.append((CHAIN_RULE_CODE, f"{owner}: link {i} '{link}' has no visible action verb"))
        if abstract:
            errors.append(
                (
                    CHAIN_RULE_CODE,
                    f"{owner}: link {i} '{link}' uses physics abstraction '{abstract[0]}' (must be a visible action)",
                )
            )
        ranks_seen.append(ranks)

    # ground-up start: the chain opens on a ground contact
    if ranks_seen and ranks_seen[0] and min(ranks_seen[0]) > GROUND_CONTACT_MAX_RANK:
        errors.append(
            (
                CHAIN_RULE_CODE,
                f"{owner}: chain must start at the ground (feet/knee on the floor), link 1 '{links[0]}' starts at rank {min(ranks_seen[0])}",
            )
        )

    # ground-up order: link ranks never decrease (greedy lowest legal climb)
    if ranks_seen and all(r for r in ranks_seen):
        current = min(ranks_seen[0])
        for i in range(1, len(ranks_seen)):
            higher = [r for r in ranks_seen[i] if r >= current]
            if not higher:
                errors.append(
                    (
                        CHAIN_RULE_CODE,
                        f"{owner}: ground-up order broken at link {i + 1} '{links[i]}' (rank {min(ranks_seen[i])}) "
                        f"after link {i} '{links[i - 1]}' (rank {current})",
                    )
                )
                break
            current = min(higher)

    # the chain ends on the impact (last link drawn strongest)
    if links and not terminal_verbs_in(links[-1]):
        errors.append(
            (
                CHAIN_RULE_CODE,
                f"{owner}: chain must end on the impact; final link '{links[-1]}' carries no terminal impact verb",
            )
        )

    # frame numbers belong to timing metadata, never to prompt text
    digit = has_digits(chain)
    if digit:
        errors.append(
            (
                CHAIN_RULE_CODE,
                f"{owner}: chain segment contains digit '{digit}' (frame offsets stay in '{CHAIN_FRAME_KEY}', never in prompt text)",
            )
        )

    errors.extend(
        validate_chain_frames(
            chain_frames,
            owner=owner,
            link_count=len(links),
            required=require_frames,
        )
    )
    return errors


def chain_segments(prompt: str) -> List[Tuple[int, int, str]]:
    """Locate every 'chain: ... -> causes' segment in emitted prompt text.

    Returns (start, end, text) spans of the link lists themselves.
    """
    segments: List[Tuple[int, int, str]] = []
    for m in CHAIN_SEGMENT_RE.finditer(prompt):
        tail = prompt[m.end():]
        end_m = CHAIN_SEGMENT_END_RE.search(tail)
        if end_m is None:
            segments.append((m.end(), len(prompt), tail.strip()))
            continue
        end = m.end() + end_m.start()
        segments.append((m.end(), end, prompt[m.end():end].strip()))
    return segments


def scan_prompt_v18(prompt: str) -> List[Tuple[str, str]]:
    """V18 text-level gates on compiled prompt text.

    1. A bare '>' (never the '>' of a '->' causal arrow) may only appear: inside a
       'chain:' segment (kinetic chain links), inside the pre-existing laban
       movement-chain values ("chain":"C01... > C02...") that Layer 2 has carried
       since Decision 19, or inside a '<placeholder>' legend token. Anywhere else
       it is an error.
    2. Every chain segment passes the link rules and carries no digit.
    3. chain_frames offsets never leak into prompt text.
    4. Every move causal string keeps its four segments: requires -> preserves -> chain -> causes.
    """
    errors: List[Tuple[str, str]] = []
    segments = chain_segments(prompt)
    spans = [(start, end) for start, end, _ in segments]
    # The laban entity chain is a pre-existing canonical '>' site in Layer 2 (it
    # lists beat codes, not body parts), so it is exempt from the separator rule
    # — and from the link rules, which apply to 'chain:' segments only.
    spans.extend((m.start(1), m.end(1)) for m in MOVEMENT_CHAIN_VALUE_RE.finditer(prompt))
    # Layer 1 'CHAIN:' segments also carry ground-up '>' links.
    for m in re.finditer(r"CHAIN:\s*([^|\n]+)", prompt):
        spans.append((m.start(1), m.end(1)))
    # Layer 1 legend tokens like '<seconds>' close with a '>'; that is notation,
    # not a separator.
    spans.extend((m.start(0), m.end(0)) for m in PLACEHOLDER_TOKEN_RE.finditer(prompt))

    for start, end, text in segments:
        if text == "":
            errors.append((CHAIN_RULE_CODE, "Emitted causal string has an empty 'chain:' segment"))
            continue
        errors.extend(
            validate_kinetic_chain(
                text,
                owner="Emitted Layer 2 causal chain",
                chain_frames=None,
            )
        )

    for i, ch in enumerate(prompt):
        if ch != CHAIN_SEPARATOR:
            continue
        if i > 0 and prompt[i - 1] == "-":
            # The '>' of a '->' causal arrow is not a chain separator.
            continue
        if not any(start <= i < end for start, end in spans):
            errors.append(
                (
                    CHAIN_RULE_CODE,
                    f"'{CHAIN_SEPARATOR}' used outside a 'chain:' segment at offset {i} "
                    "(use '->' for causal arrows, '>' only between chain links)",
                )
            )

    if CHAIN_FRAME_KEY in prompt:
        errors.append(
            (
                CHAIN_RULE_CODE,
                f"'{CHAIN_FRAME_KEY}' leaked into emitted prompt text (frame offsets stay internal timing metadata)",
            )
        )

    for m in CAUSAL_FIELD_RE.finditer(prompt):
        body = m.group("body")
        if not body.startswith("C"):
            errors.append(
                (CHAIN_RULE_CODE, f"causal string is missing its C-code prefix: '{body[:80]}'")
            )
            continue
        if "requires" not in body:
            # Terminal hold beats ("C11_hold: maintains ...") are not four-segment
            # move causals; only their C-code prefix is required.
            continue
        missing = [
            marker
            for marker in (" -> preserves ", " -> chain: ", " -> causes ")
            if marker not in body
        ]
        if missing:
            errors.append(
                (
                    CHAIN_RULE_CODE,
                    f"causal string is missing segments {missing}: '{body[:80]}'",
                )
            )

    return errors


def build_causal_string(code: str, requires: str, preserves: str, chain: str, causes: str) -> str:
    """Build the four-segment causal string with the kinetic chain as segment four."""
    return (
        f"{code}: requires {requires} -> preserves {preserves} -> "
        f"chain: {chain} -> causes {causes}"
    )


__all__ = [
    "BODY_PART_RANKS",
    "CHAIN_FRAME_KEY",
    "CHAIN_KEY",
    "CHAIN_MAX_LINKS",
    "CHAIN_MIN_LINKS",
    "CHAIN_RULE_CODE",
    "CHAIN_SEPARATOR",
    "FORBIDDEN_ABSTRACTIONS",
    "TERMINAL_IMPACT_VERBS",
    "VISIBLE_VERBS",
    "actor_ranks",
    "abstractions_in",
    "body_parts_in",
    "build_causal_string",
    "chain_segments",
    "has_digits",
    "scan_prompt_v18",
    "split_chain",
    "terminal_verbs_in",
    "validate_chain_frames",
    "validate_kinetic_chain",
    "visible_verbs_in",
]