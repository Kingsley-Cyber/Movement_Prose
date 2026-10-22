"""Diversity knobs: style axes with verbalised options; one-change variants of a JSON prompt."""
import json
import re
from collections import OrderedDict
from pathlib import Path

from . import DATA_DIR

KNOBS_PATH = Path(DATA_DIR) / "knobs.json"
NUMERIC_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:fps|frames?|ms|px|%)\b|\b\d+(?:\.\d+)?x\b", re.I)


def load(path=KNOBS_PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def axes(knobs=None):
    knobs = knobs or load()
    return OrderedDict((a, list(v["options"])) for a, v in knobs["axes"].items())


def option(knobs, axis, name):
    try:
        return knobs["axes"][axis]["options"][name]
    except KeyError:
        raise KeyError("unknown knob %s=%s; axes: %s" % (axis, name, json.dumps(axes(knobs))))


def check_prose(knobs=None):
    """Knob prose must verbalise consequences, never carry fps/frame/amplitude numbers."""
    knobs = knobs or load()
    bad = []
    for a, v in knobs["axes"].items():
        for name, o in v["options"].items():
            if NUMERIC_RE.search(o["prose"]):
                bad.append("%s=%s" % (a, name))
    return bad


def apply(prompt, axis, name, knobs=None):
    """Return a copy of a JSON prompt (run-002 shape) with one animation_grammar field replaced by the option's prose."""
    knobs = knobs or load()
    o = option(knobs, axis, name)
    field = knobs["field_map"][axis]
    out = json.loads(json.dumps(prompt), object_pairs_hook=OrderedDict)
    grammar = out.setdefault("animation_grammar", OrderedDict())
    entry = grammar.setdefault(field, OrderedDict())
    if isinstance(entry, dict):
        entry["rule"] = o["prose"]
        if axis == "laban_profile":
            entry["A"] = o["prose"]
            entry["B"] = o["prose"]
    else:
        grammar[field] = OrderedDict([("rule", o["prose"])])
    out["variant"] = OrderedDict([("axis", axis), ("option", name), ("changed_field", "animation_grammar." + field), ("from", o.get("from", [])), ("prefers", o.get("prefers", []))])
    return out


def write_variants(run_dir, axis, base_name="prompt.json", knobs=None):
    knobs = knobs or load()
    run_dir = Path(run_dir)
    base = json.loads((run_dir / base_name).read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)
    written = []
    for name in knobs["axes"][axis]["options"]:
        v = apply(base, axis, name, knobs)
        path = run_dir / ("variant_%s_%s.json" % (axis, name))
        path.write_text(json.dumps(v, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        written.append(path)
    return written


def changed_fields(a, b, prefix=""):
    """Dotted paths whose values differ between two JSON objects (ignores the variant block)."""
    out = []
    keys = set(a) | set(b)
    for k in sorted(keys):
        if k == "variant":
            continue
        va, vb = a.get(k), b.get(k)
        if isinstance(va, dict) and isinstance(vb, dict):
            out += changed_fields(va, vb, prefix + k + ".")
        elif va != vb:
            out.append(prefix + k)
    return out
