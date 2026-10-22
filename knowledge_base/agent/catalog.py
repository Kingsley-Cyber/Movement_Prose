"""Read-only access to the bundle's 64 directives, joined with the JSON catalog fields."""
import json
import sqlite3
from collections import namedtuple
from pathlib import Path

from . import BUNDLE_DIR, CANONICAL_FINGERPRINT, COLUMNS, PLACEHOLDER, seed

Directive = namedtuple("Directive", list(COLUMNS) + ["mechanics", "catalog"])

FALLBACK_SLOT_ORDER = ["subject_anchor", "environment", "primary_action", "secondary_motion",
                       "temporal_cadence", "camera_optics", "lighting", "material_shading"]


class CatalogError(RuntimeError):
    pass


def open_readonly(db_path):
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.execute("PRAGMA query_only=ON")
    return connection


def load_slot_order(bundle_dir=BUNDLE_DIR):
    path = Path(bundle_dir) / "example_payloads.json"
    if path.exists():
        order = json.loads(path.read_text(encoding="utf-8")).get("slot_order")
        if order:
            return list(order)
    return list(FALLBACK_SLOT_ORDER)


class Catalog(object):
    def __init__(self, directives, fingerprint, slot_order):
        self._by_id = dict((d.directive_id, d) for d in directives)
        self._fingerprint = fingerprint
        self.slot_order = list(slot_order)
        self._slot_rank = dict((s, i) for i, s in enumerate(self.slot_order))
        self._conflicts = {}
        for d in directives:
            for other in d.mechanics.get("conflicts_with", []) or []:
                self._conflicts.setdefault(d.directive_id, set()).add(other)
                self._conflicts.setdefault(other, set()).add(d.directive_id)

    @property
    def ids(self):
        return sorted(self._by_id)

    def __len__(self):
        return len(self._by_id)

    def __contains__(self, directive_id):
        return directive_id in self._by_id

    def get(self, directive_id):
        try:
            return self._by_id[directive_id]
        except KeyError:
            raise CatalogError("unknown directive_id: %s" % directive_id)

    def rows(self, slot=None, moment=None, sub_genre=None):
        out = [d for d in self._by_id.values()
               if (slot is None or d.slot_id == slot)
               and (moment is None or d.moment_type == moment)
               and (sub_genre is None or d.sub_genre == sub_genre)]
        out.sort(key=lambda d: (self._slot_rank.get(d.slot_id, 99), d.moment_type, d.directive_id))
        return out

    def conflicts(self, directive_id):
        return set(self._conflicts.get(directive_id, ()))

    def requires(self, directive_id):
        return list(self.get(directive_id).mechanics.get("requires", []) or [])

    def placeholders(self, directive_id):
        d = self.get(directive_id)
        names = set()
        for text in (d.prompt_snippet, d.negative_snippet):
            for match in PLACEHOLDER.finditer(text):
                names.add(match.group(0).strip("{} \t"))
        return frozenset(names)

    def preferred_route(self, directive_id):
        return self.get(directive_id).mechanics.get("preferred_route")

    def fingerprint(self):
        return self._fingerprint


def load_catalog(bundle_dir=BUNDLE_DIR, verify_fingerprint=True):
    bundle_dir = Path(bundle_dir)
    connection = open_readonly(bundle_dir / "ai_video_compiler.db")
    try:
        rows = connection.execute(
            "SELECT " + ", ".join(COLUMNS) + " FROM semantic_directives WHERE archetype='anime_action' ORDER BY directive_id"
        ).fetchall()
    finally:
        connection.close()
    fingerprint = seed.fingerprint([tuple(r) for r in rows])
    if verify_fingerprint and fingerprint != CANONICAL_FINGERPRINT:
        raise CatalogError("catalog fingerprint %s != canonical %s" % (fingerprint, CANONICAL_FINGERPRINT))
    catalog_doc = json.loads((bundle_dir / "anime_directives.json").read_text(encoding="utf-8"))
    records = catalog_doc["directives"] if isinstance(catalog_doc, dict) else catalog_doc
    extra = dict((r["directive_id"], r.get("catalog", {})) for r in records)
    directives = []
    for r in rows:
        values = list(r)
        mechanics = json.loads(values[7])
        directives.append(Directive(*(values + [mechanics, extra.get(values[0], {})])))
    return Catalog(directives, fingerprint, load_slot_order(bundle_dir))
