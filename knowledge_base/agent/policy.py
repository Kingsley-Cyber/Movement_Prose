"""Priority classes, budget classes, suppression policy and prerequisite satisfiers."""
import json
from pathlib import Path

from . import DATA_DIR

CLASSES = ("locked", "required", "high", "medium", "low", "optional")
REASONS = ("low_observability", "provider_unsupported", "redundant", "conflicting",
           "lower_priority", "already_encoded_by_stronger_control", "token_budget")
BUDGET_CLASSES = ("dominant_action", "camera_move", "camera_static", "secondary_body", "material_response", "none")
SUBJECT_KINDS = ("actor", "target", "both", "scene")
SCENE = "scene"


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class Policy(object):
    def __init__(self, data_dir=DATA_DIR):
        data_dir = Path(data_dir)
        self.budget = _load(data_dir / "budget_classes.json")
        self.priority = _load(data_dir / "priority_defaults.json")
        self.prereq = _load(data_dir / "prerequisites.json")
        self.classes = tuple(self.priority["classes"])
        self.reasons = tuple(self.priority["reasons"])
        self.locked_ids = frozenset(self.priority["locked_ids"])
        self.locked_authored_slots = frozenset(self.priority.get("locked_authored_slots", []))
        self.limits = self.budget["limits"]
        self.camera_count_exempt = frozenset(self.budget.get("camera_count_exempt", []))

    # --- budget -----------------------------------------------------------
    def budget_entry(self, directive_id):
        return self.budget["classes"].get(directive_id, {"class": "none", "subject": "actor", "reason": "unclassified"})

    def budget_class(self, directive_id):
        return self.budget_entry(directive_id)["class"]

    def subject_kind(self, directive_id):
        return self.budget_entry(directive_id)["subject"]

    def subjects_of(self, selection, directive_id):
        """Entity ids whose body this selection moves (or ['scene'])."""
        kind = self.subject_kind(directive_id)
        if kind == "actor":
            return [selection.actor_id] if selection.actor_id else []
        if kind == "target":
            return [selection.target_id] if selection.target_id else []
        if kind == "both":
            return [x for x in (selection.actor_id, selection.target_id) if x]
        return [SCENE]

    # --- priority ---------------------------------------------------------
    def is_locked(self, directive_id):
        return directive_id in self.locked_ids

    def default_priority(self, directive):
        override = self.priority.get("row_overrides", {}).get(directive.directive_id)
        if override:
            return override
        return self.priority["table"][directive.slot_id][directive.moment_type]

    def effective_priority(self, selection, directive):
        if self.is_locked(directive.directive_id):
            return "locked"
        return selection.priority or self.default_priority(directive)

    def may_suppress(self, priority, reason):
        allowed = self.priority["suppression_policy"].get(priority, [])
        if allowed == "any":
            return reason in self.reasons
        return reason in allowed

    # --- prerequisites ------------------------------------------------------
    def satisfiers(self, token):
        return list(self.prereq["satisfiers"].get(token, []))

    def known_token(self, token):
        return token in self.prereq["satisfiers"]
