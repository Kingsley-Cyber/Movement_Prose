import hashlib
import json
import os
import tempfile
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    """Stable JSON and same-directory atomic replacement."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if path.exists() and path.read_text() == data:
        return
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".block-")
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(data)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class Knowledge:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.index = read(self.root / "data/engine_index.json")
        self.options = self.keyed(self.index["options"])
        self.techniques = self.keyed(read(self.root / "data/techniques.json")["techniques"])
        self.debts = self.keyed(read(self.root / "data/debt_registry.json")["debts"])
        self.relationships = self.keyed(read(self.root / "data/counter_graph.json")["relationships"])
        self.matrices = self.keyed(read(self.root / "data/matchups.json")["matrices"])
        self.cells = {m: {(c["row_id"], c["column_id"]): c for c in v["cells"]}
                      for m, v in self.matrices.items()}
        self.model = read(self.root / "data/model.json")
        self.sources = self.keyed(read(self.root / "data/sources.json")["sources"])
        self.claims = self.keyed(read(self.root / "data/claims.json")["claims"])
        self.pipeline = read(self.root / "data/pipeline.json")

    @staticmethod
    def keyed(records):
        ids = [x["id"] for x in records]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate canonical ID")
        return {x["id"]: x for x in records}

    def schema(self, name, value):
        jsonschema.validate(value, read(self.root / "schemas" / (name + ".schema.json")))

    def fingerprint(self):
        digest = hashlib.sha256()
        for path in sorted((self.root / "data").rglob("*.json")):
            digest.update(str(path.relative_to(self.root)).encode())
            digest.update(path.read_bytes())
        return digest.hexdigest()

    def card(self, value):
        if isinstance(value, (str, Path)):
            p = Path(value)
            if not p.exists():
                if (self.root / p).exists():
                    p = self.root / p
                elif (self.root / "cards" / f"{value}.json").exists():
                    p = self.root / "cards" / f"{value}.json"
                elif (self.root / "cards" / "v2" / f"{value}.json").exists():
                    p = self.root / "cards" / "v2" / f"{value}.json"
            card = read(p)
        else:
            card = value
        schema_name = "fighter_card_v2" if card.get("version") == "block-2" else "fighter_card"
        self.schema(schema_name, card)
        from .capabilities import KNOWN_CAPABILITIES, admitted_slots, option_supported, training
        if card.get("provenance", {}).get("classification") != "CANON":
            raise ValueError("fighter card provenance classification must be CANON")
        for dim, ident in card["dimensions"].items():
            if ident is not None and (ident not in self.options or self.options[ident]["dimension"] != dim):
                raise ValueError("invalid dimension reference: " + str(ident))
            if ident is not None and not option_supported(self, card, ident):
                raise ValueError("unsupported dimension option for card training: " + str(ident))
        if len(card["synchronized_capabilities"]) != card["slot_count"]:
            raise ValueError("slot count differs from synchronized bundles")
        if len({s["id"] for s in card["synchronized_capabilities"]}) != card["slot_count"]:
            raise ValueError("duplicate synchronized slot")
        for s in card["synchronized_capabilities"]:
            caps = s.get("capabilities") or []
            if len(caps) != len(set(caps)):
                raise ValueError("duplicate capability within synchronized slot: " + s["id"])
            if any(c not in KNOWN_CAPABILITIES for c in caps):
                raise ValueError("unknown capability in synchronized slot: " + s["id"])
            if card.get("version") == "block-2" and len(caps) > 2:
                raise ValueError("block-2 slot budget exceeded (max 2 schools per slot): " + s["id"])
        if len(admitted_slots(card, self)) != card["slot_count"]:
            raise ValueError("duplicate synchronized capability bundle")
        labels = {1: "Brawler", 2: "Two-piece", 3: "Triad", 4: "Anomaly"}
        if card["slot_label"] != labels[card["slot_count"]]:
            raise ValueError("invalid slot label")
        for tid in card["active_techniques"]:
            if tid not in self.techniques:
                raise ValueError("unknown technique: " + tid)
            if not set(self.techniques[tid]["required_capabilities"]) & training(card):
                raise ValueError("technique without training: " + tid)
        for debt in card["exploitable_seams"]:
            if debt not in self.debts or self.debts[debt]["option_id"] not in card["dimensions"].values():
                raise ValueError("invalid card debt reference: " + debt)
        expected_debts = {
            d for opt_id in card["dimensions"].values() if opt_id for d in self.options[opt_id]["exploitable_debt_ids"]
        }
        if not expected_debts <= set(card["exploitable_seams"]):
            raise ValueError("missing required option debt in exploitable_seams")
        for ability in card["conditional_abilities"]:
            if not ability["trained"]:
                raise ValueError("conditional training must be declared")
            if not ability["gates"]:
                raise ValueError("conditional ability requires gates")
            for tid in ability["techniques"]:
                if tid not in self.techniques:
                    raise ValueError("unknown conditional technique: " + tid)
        return card
