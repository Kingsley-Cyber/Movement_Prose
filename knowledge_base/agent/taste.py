"""Vibe-word matching to taste profiles, and taste-ranked (never filtered) candidate rows."""
import json
import re
from pathlib import Path

from . import DATA_DIR

_TOKEN = re.compile(r"[a-z0-9]+")


def tokens(text):
    return _TOKEN.findall((text or "").lower().replace("-", " ").replace("_", " "))


def bigrams(toks):
    return set(zip(toks, toks[1:]))


def load_profiles(path=None):
    path = Path(path) if path else Path(DATA_DIR) / "taste_profiles.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    return dict((p["taste_id"], p) for p in doc["profiles"])


def match(text, profiles):
    """Ranked [(taste_id, score, matched_tags)]; empty when nothing matches."""
    toks = tokens(text)
    tset, bset = set(toks), bigrams(toks)
    results = []
    for taste_id, profile in profiles.items():
        score, hits = 0, []
        for tag in profile.get("human_vibe_tags", []):
            ttoks = tokens(tag)
            if len(ttoks) == 1 and ttoks[0] in tset:
                score += 1
                hits.append(tag)
            elif len(ttoks) > 1 and tuple(ttoks) in bset:
                score += 2
                hits.append(tag)
        if score:
            results.append((taste_id, score, hits))
    results.sort(key=lambda r: (-r[1], r[0]))
    return results


def best(text, profiles):
    """The single best taste_id, or None when nothing matches or the top two tie."""
    ranked = match(text, profiles)
    if not ranked:
        return None
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return None
    return ranked[0][0]


def mark(directive_id, profile):
    if profile is None:
        return "neutral"
    if directive_id in profile.get("avoid_directives", []):
        return "avoid"
    for ids in profile.get("preferred_directives", {}).values():
        if directive_id in ids:
            return "preferred"
    return "neutral"


def rank(rows, profile, sub_genre=None):
    """Order rows preferred -> neutral -> avoid (sub-genre hint first within a mark). Never drops a row."""
    order = {"preferred": 0, "neutral": 1, "avoid": 2}
    hint = sub_genre or (profile or {}).get("sub_genre_hint")

    def key(d):
        return (order[mark(d.directive_id, profile)], 0 if hint and d.sub_genre == hint else 1, d.directive_id)

    return [(d, mark(d.directive_id, profile)) for d in sorted(rows, key=key)]
