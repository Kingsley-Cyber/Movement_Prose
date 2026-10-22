import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.ontology import Knowledge, write
from engine.fight_director import plan
from engine.event_graph import graph, validate
from engine.choreography import choreograph
from engine.prompt_compiler import shots, compile_shot, validate_visuals


def deliver(a, b, ruleset, duration, seed, output_dir, winner=None, style="realistic", knowledge=None, movement_prose=False):
    k = knowledge or Knowledge()
    result = plan(a, b, ruleset, duration, seed, winner, k)
    event_graph = graph(result)
    choreography = choreograph(k, result, style)
    shotlist = shots(k, result, choreography)
    prompts = [compile_shot(s) for s in shotlist["shots"]]
    report = {"events": validate(k, result, event_graph), "visuals": validate_visuals(k, result, choreography, shotlist, prompts)}
    out = Path(output_dir)
    for name, value in [("fight_plan", result), ("event_graph", event_graph), ("choreography", choreography),
                        ("shotlist", shotlist), ("prediction", result["prediction"]), ("validation_report", report)]:
        write(out / (name + ".json"), value)
    (out / "video_prompts.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False, allow_nan=False) + "\n" for p in prompts))
    text = ["# " + " versus ".join(c["name"] for c in result["cards"]), "", result["conclusion"], "", result["selection"]["label"],
            "", "Probability is uncalibrated. Ruleset: " + ruleset + ". Seed: " + str(seed) + ". Duration: " + str(duration) + " seconds.", ""]
    phase = None
    for e in result["events"]:
        if e["phase"] != phase:
            phase = e["phase"]
            text += ["## " + phase.replace("_", " ").capitalize(), ""]
        if e["type"] in ["assessment", "movement", "execution", "contact", "activation", "adjustment", "resolution", "aftermath"]:
            text += [f"{e['timestamp']:.2f}s [{e['id']}] {e['actor_id']}: {e['intent']}", ""]
    text += [result["fidelity"], "", "Use shotlist.json as the authoritative staging. Prompt prose cannot guarantee a video model reproduces it.", ""]
    (out / "explanation.md").write_text("\n".join(text))
    if movement_prose:
        from fight_move_system.block_bridge import compile_block_fight_to_movement_prose
        mp_res = compile_block_fight_to_movement_prose(
            result,
            choreography=choreography,
            output_dir=out / "movement_prose",
            use_kb_priors=True,
        )
        report["movement_prose"] = {
            "status": "PASS" if mp_res["fluid_stack"]["passed"] and mp_res["original_0534_causal"]["passed"] else "FAIL",
            "clip_id": mp_res["clip_id"],
            "fluid_stack_length": mp_res["fluid_stack"]["prompt_length"],
            "original_0534_causal_length": mp_res["original_0534_causal"]["prompt_length"],
            "output_dir": str(out / "movement_prose"),
        }
    return result, report


def main():
    p = argparse.ArgumentParser(description="Seeded BLOCK semantic fight direction")
    p.add_argument("fighter_a")
    p.add_argument("fighter_b")
    p.add_argument("--ruleset", choices=["mma", "boxing"], default="mma")
    p.add_argument("--duration", type=float, default=60, help="Seconds; specification demonstration uses 30–60")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--winner", help="Participating fighter ID; explicitly dramatized director-controlled mode")
    p.add_argument("--style", choices=["realistic", "anime"], default="realistic")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--movement-prose", action="store_true", help="Also compile the planned BLOCK fight into Movement_Prose 2-Layer Fluid Stack and protected 05:34 SAKUGA-MLLM-3.1-CAUSAL prompts")
    args = p.parse_args()
    result, report = deliver(
        args.fighter_a,
        args.fighter_b,
        args.ruleset,
        args.duration,
        args.seed,
        args.output_dir,
        args.winner,
        args.style,
        movement_prose=args.movement_prose,
    )
    print(json.dumps({"selection": result["selection"], "validation": report, "output_dir": args.output_dir}, indent=2))


if __name__ == "__main__":
    main()
