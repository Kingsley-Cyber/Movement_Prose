"""Engine profiles: the bundle's descriptive profiles merged with agent-local additions."""
import json
from pathlib import Path

from . import BUNDLE_DIR, DATA_DIR


class EngineError(RuntimeError):
    pass


def load_engine_profiles(bundle_dir=BUNDLE_DIR, data_dir=DATA_DIR):
    profiles = {}
    for path in (Path(bundle_dir) / "engine_profiles.json", Path(data_dir) / "engine_profiles_extra.json"):
        if path.exists():
            for p in json.loads(path.read_text(encoding="utf-8")).get("profiles", []):
                profiles[p["profile_id"]] = p
    return profiles


def get_profile(profiles, profile_id):
    try:
        return profiles[profile_id]
    except KeyError:
        raise EngineError("unknown engine profile: %s (known: %s)" % (profile_id, ", ".join(sorted(profiles))))


def negatives_status(profile):
    """active | conditional | inactive | unverified | none"""
    status = (profile.get("negative_active") or {}).get("status", "") or ""
    if status.startswith("verified"):
        return "active"
    if status.startswith("conditional"):
        return "conditional"
    if status.startswith("inactive"):
        return "inactive"
    if status == "none" or not profile.get("negative_field"):
        if status in ("", "none"):
            return "none"
    return "unverified"


def dispatch_status(profile):
    """ok | retired | exact_target_required | draft_only"""
    status = profile.get("status", "")
    if status.startswith("retired"):
        return "retired"
    if status == "exact_target_required":
        return "exact_target_required"
    if status == "documented_product_capabilities_only":
        return "draft_only"
    return "ok"


def duration_limit(profile):
    return profile.get("documented_max_generation_seconds")


def frame_note(profile, frame_count):
    contract = (profile.get("frame_rate") or {}).get("frame_count_contract", "")
    if "4n+1" in contract and frame_count is not None and (frame_count - 1) % 4 != 0:
        return "frame_count %d is not 4n+1 (%s)" % (frame_count, contract)
    return None
