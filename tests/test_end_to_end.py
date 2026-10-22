import copy
import json
import subprocess
import sys
import pytest
from engine.ontology import ROOT, read
from engine.choreography import anatomical, choreograph
from engine.prompt_compiler import shots, compile_shot, validate_visuals
from engine.event_graph import validate


def test_visual_phase_identity_contact_and_prompt_round_trip(fight, knowledge):
    for style in ["realistic", "anime"]:
        c = choreograph(knowledge, fight, style)
        s = shots(knowledge, fight, c)
        prompts = [compile_shot(shot) for shot in s["shots"]]
        assert validate_visuals(knowledge, fight, c, s, prompts)["status"] == "PASS"
        assert sum(shot["duration"] for shot in s["shots"]) == pytest.approx(fight["duration"])
        assert [i for m in c["movements"] for i in m["source_event_ids"]] == [e["id"] for e in fight["events"]]
        assert all([p["phase"] for p in m["phases"]] == ["preparation", "initiation", "execution", "contact", "reaction", "recovery"] for m in c["movements"])
        assert all(prompt["source_event_ids"] == shot["source_event_ids"] for prompt, shot in zip(prompts, s["shots"]))
    assert anatomical("rear shin", "orthodox") == "right shin"
    assert anatomical("rear shin", "southpaw") == "left shin"


@pytest.mark.parametrize("defect", ["contact", "identity", "camera", "order", "prompt"])
def test_visual_validator_rejects_contradictions(fight, knowledge, defect):
    c = choreograph(knowledge, fight)
    s = shots(knowledge, fight, c)
    prompts = [compile_shot(shot) for shot in s["shots"]]
    if defect == "contact":
        next(shot for shot in s["shots"] if shot["contact_timing"])["contact_timing"] = None
    elif defect == "identity":
        s["shots"][0]["characters"][0]["fighter_id"] = "donnell"
    elif defect == "camera":
        s["shots"][0]["camera"]["visibility"] = "hide legs"
    elif defect == "order":
        s["shots"].reverse()
    else:
        prompts[0]["prompt"] = "An unrelated fight."
    with pytest.raises(ValueError):
        validate_visuals(knowledge, fight, c, s, prompts)


def test_public_clis_produce_valid_durable_fights_and_prediction(tmp_path, knowledge):
    output = tmp_path / "prediction.json"
    cmd = [sys.executable, "predict.py", "cards/maleek.json", "cards/donnell.json", "--ruleset", "mma", "--output", str(output)]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    assert read(output)["probability_a"] + read(output)["probability_b"] == 1
    for a, b in [("maleek", "donnell"), ("wrestler", "donnell")]:
        out = tmp_path / a
        p = subprocess.run([sys.executable, "plan_fight.py", "cards/" + a + ".json", "cards/" + b + ".json", "--ruleset", "mma", "--duration", "60", "--seed", "42", "--output-dir", str(out)], cwd=ROOT, capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
        plan = read(out / "fight_plan.json")
        assert validate(knowledge, plan, read(out / "event_graph.json"))["status"] == "PASS"
        assert read(out / "validation_report.json")["visuals"]["status"] == "PASS"
        prompts = [json.loads(line) for line in (out / "video_prompts.jsonl").read_text().splitlines()]
        assert validate_visuals(knowledge, plan, read(out / "choreography.json"), read(out / "shotlist.json"), prompts)["status"] == "PASS"
        assert (out / "explanation.md").stat().st_size > 0
