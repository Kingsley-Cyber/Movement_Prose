"""The intermediate representation: the bundle's event and occurrence records plus priority and authored text."""
import json
from collections import namedtuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

from . import MOMENTS, SLOTS

Finding = namedtuple("Finding", "level code message event_id directive_id")
SCHEMA_VERSION = 1
CLAUSES = ("SHOT AND DURATION", "SUBJECT AND ACTION", "PERFORMANCE", "TIMING", "CAMERA AND PRESENTATION", "NEGATIVES")


def finding(level, code, message, event_id=None, directive_id=None):
    return Finding(level, code, message, event_id, directive_id)


@dataclass
class Clip:
    editorial_fps: int = 24
    duration_seconds: float = 3.0
    frame_count: int = 72


@dataclass
class Event:
    event_id: str
    actor_id: str
    moment_type: str
    start_frame: int
    end_frame: int
    target_id: Optional[str] = None
    depends_on: Optional[str] = None
    inherit_from: Optional[str] = None
    declared_prerequisites: List[str] = field(default_factory=list)


@dataclass
class Selection:
    directive_id: str
    event_id: str
    start_frame: int
    end_frame: int
    actor_id: Optional[str] = None
    target_id: Optional[str] = None
    priority: Optional[str] = None
    suppressed_reason: Optional[str] = None


@dataclass
class Authored:
    event_id: str
    slot_id: str
    text: str
    clause: str = "SUBJECT AND ACTION"
    priority: Optional[str] = None
    budget_class: Optional[str] = None
    origin: str = "authored"
    why: str = ""
    handbook_refs: List[str] = field(default_factory=list)


@dataclass
class IR:
    request: str
    scene_context: str
    entities: Dict[str, str]
    clip: Clip
    events: List[Event]
    selections: List[Selection]
    authored: List[Authored] = field(default_factory=list)
    contact_origins: Dict[str, str] = field(default_factory=dict)
    editorial_operations: List[dict] = field(default_factory=list)
    taste_profile_id: Optional[str] = None
    matched_tags: List[str] = field(default_factory=list)
    engine_profile_id: str = "generic_web_ui"
    schema_version: int = SCHEMA_VERSION

    def event(self, event_id):
        for e in self.events:
            if e.event_id == event_id:
                return e
        return None

    def events_in_order(self):
        return sorted(self.events, key=lambda e: (e.start_frame, e.end_frame, e.event_id))

    def active_selections(self):
        return [s for s in self.selections if not s.suppressed_reason]


def frames_to_seconds(frame, fps):
    return round(float(frame) / float(fps), 3)


# --- shape validation (hand-rolled; no jsonschema on this machine) -------------
def _is_int(x):
    return type(x) is int


def validate_shape(doc):
    out = []
    err = lambda code, msg, ev=None, d=None: out.append(finding("error", code, msg, ev, d))
    if not isinstance(doc, dict):
        err("SHAPE", "IR must be a JSON object")
        return out
    for key in ("request", "scene_context", "entities", "clip", "events", "selections"):
        if key not in doc:
            err("SHAPE", "missing required key: %s" % key)
    if out:
        return out
    if doc.get("schema_version", SCHEMA_VERSION) != SCHEMA_VERSION:
        err("SHAPE", "schema_version must be %d" % SCHEMA_VERSION)
    for key in ("request", "scene_context"):
        if not isinstance(doc[key], str):
            err("SHAPE", "%s must be text" % key)
    if not isinstance(doc["entities"], dict) or not doc["entities"] or not all(
            isinstance(k, str) and isinstance(v, str) and v.strip() for k, v in doc["entities"].items()):
        err("SHAPE", "entities must be a nonempty object of id -> description text")
    clip = doc["clip"]
    if not isinstance(clip, dict):
        err("SHAPE", "clip must be an object")
    else:
        if not _is_int(clip.get("editorial_fps")) or clip["editorial_fps"] <= 0:
            err("SHAPE", "clip.editorial_fps must be a positive integer")
        if not _is_int(clip.get("frame_count")) or clip["frame_count"] <= 0:
            err("SHAPE", "clip.frame_count must be a positive integer")
        if not isinstance(clip.get("duration_seconds"), (int, float)) or clip["duration_seconds"] <= 0:
            err("SHAPE", "clip.duration_seconds must be a positive number")
    if not isinstance(doc["events"], list) or not doc["events"]:
        err("SHAPE", "events must be a nonempty array")
    else:
        for e in doc["events"]:
            if not isinstance(e, dict):
                err("SHAPE", "event must be an object")
                continue
            ev = e.get("event_id")
            for key in ("event_id", "actor_id", "moment_type"):
                if not isinstance(e.get(key), str) or not e[key].strip():
                    err("SHAPE", "event %s: %s must be nonempty text" % (ev, key), ev)
            if e.get("moment_type") not in MOMENTS:
                err("SHAPE", "event %s: moment_type %r not in %s" % (ev, e.get("moment_type"), sorted(MOMENTS)), ev)
            if not (_is_int(e.get("start_frame")) and _is_int(e.get("end_frame")) and 0 <= e["start_frame"] < e["end_frame"]):
                err("SHAPE", "event %s: frames must be integers with 0 <= start_frame < end_frame" % ev, ev)
            if e.get("declared_prerequisites") is not None and not (
                    isinstance(e["declared_prerequisites"], list) and all(isinstance(x, str) for x in e["declared_prerequisites"])):
                err("SHAPE", "event %s: declared_prerequisites must be an array of text" % ev, ev)
    if not isinstance(doc["selections"], list):
        err("SHAPE", "selections must be an array")
    else:
        for s in doc["selections"]:
            if not isinstance(s, dict):
                err("SHAPE", "selection must be an object")
                continue
            d = s.get("directive_id")
            if not isinstance(d, str) or not isinstance(s.get("event_id"), str):
                err("SHAPE", "selection needs directive_id and event_id text", s.get("event_id"), d)
            if not (_is_int(s.get("start_frame")) and _is_int(s.get("end_frame")) and 0 <= s["start_frame"] < s["end_frame"]):
                err("SHAPE", "selection %s: frames must be integers with 0 <= start_frame < end_frame" % d, s.get("event_id"), d)
    for a in doc.get("authored", []) or []:
        if not isinstance(a, dict) or not isinstance(a.get("text"), str) or not a["text"].strip():
            err("SHAPE", "authored entries need text")
            continue
        if a.get("slot_id") not in SLOTS:
            err("SHAPE", "authored slot_id %r not in %s" % (a.get("slot_id"), sorted(SLOTS)), a.get("event_id"))
        if a.get("clause", "SUBJECT AND ACTION") not in CLAUSES:
            err("SHAPE", "authored clause %r not in %s" % (a.get("clause"), CLAUSES), a.get("event_id"))
        refs = a.get("handbook_refs", []) or []
        if not isinstance(refs, list) or not all(isinstance(x, str) and x.strip() for x in refs):
            err("SHAPE", "authored handbook_refs must be an array of passage ids", a.get("event_id"))
    if doc.get("contact_origins") is not None and not isinstance(doc["contact_origins"], dict):
        err("SHAPE", "contact_origins must be an object of event_id -> text")
    return out


def from_dict(doc):
    clip = Clip(**doc["clip"])
    events = [Event(**e) for e in doc["events"]]
    selections = [Selection(**s) for s in doc["selections"]]
    authored = [Authored(**a) for a in doc.get("authored", []) or []]
    return IR(request=doc["request"], scene_context=doc["scene_context"], entities=dict(doc["entities"]),
              clip=clip, events=events, selections=selections, authored=authored,
              contact_origins=dict(doc.get("contact_origins", {}) or {}),
              editorial_operations=list(doc.get("editorial_operations", []) or []),
              taste_profile_id=doc.get("taste_profile_id"), matched_tags=list(doc.get("matched_tags", []) or []),
              engine_profile_id=doc.get("engine_profile_id", "generic_web_ui"),
              schema_version=doc.get("schema_version", SCHEMA_VERSION))


def to_dict(ir):
    return asdict(ir)


def load_ir(path):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    problems = validate_shape(doc)
    if problems:
        raise ValueError("IR shape errors: " + "; ".join(f.message for f in problems))
    return from_dict(doc)


def save_ir(path, ir):
    Path(path).write_text(json.dumps(to_dict(ir), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def substitute(text, selection, ir):
    """Bind {actor}, {target} and {contact_origin} from the selection's own ids; unknown names stay as-is."""
    from . import PLACEHOLDER

    def repl(match):
        name = match.group(0).strip("{} \t")
        if name == "actor":
            return ir.entities.get(selection.actor_id or "", match.group(0))
        if name == "target":
            return ir.entities.get(selection.target_id or "", match.group(0))
        if name == "contact_origin":
            return ir.contact_origins.get(selection.event_id, match.group(0))
        return match.group(0)

    return PLACEHOLDER.sub(repl, text)
