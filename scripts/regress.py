"""Single acceptance command; records real exit codes, stdout and stderr across BLOCK + Movement_Prose."""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.ontology import ROOT, write


def main():
    commands = [
        ["scripts/audit_coverage.py", "--output", "reports/final_integrity_report.json"],
        ["scripts/backfill.py", "--dry-run"],
        ["scripts/backfill.py", "--apply"],
        ["scripts/backfill.py", "--verify"],
        ["scripts/verify_findings.py", "--root", ".", "--output-dir", "reports/fairness_after_repair"],
        ["-m", "pytest", "-q"],
        ["-m", "fight_move_system.cli", "kb-verify"],
        ["scripts/sakuga_original_kb.py", "verify-protection"],
        ["predict.py", "cards/maleek.json", "cards/donnell.json", "--ruleset", "mma", "--output", "outputs/example_fights/prediction.json"],
        ["plan_fight.py", "cards/maleek.json", "cards/donnell.json", "--ruleset", "mma", "--duration", "60", "--seed", "42", "--output-dir", "outputs/example_fights/maleek_vs_donnell", "--movement-prose"],
        ["plan_fight.py", "cards/wrestler.json", "cards/donnell.json", "--ruleset", "mma", "--duration", "60", "--seed", "42", "--output-dir", "outputs/example_fights/two_slot_upset", "--movement-prose"],
    ]
    records = []
    for args in commands:
        cmd = [sys.executable] + args
        run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        records.append({"command": cmd, "exit_code": run.returncode, "stdout": run.stdout, "stderr": run.stderr})
        print("PASS" if run.returncode == 0 else "FAIL", "python " + " ".join(args), flush=True)
        if args[:2] == ["-m", "pytest"] or run.returncode:
            print(run.stdout, run.stderr, flush=True)
        if run.returncode:
            break
    status = "PASS" if len(records) == len(commands) and all(r["exit_code"] == 0 for r in records) else "FAIL"
    write(ROOT / "reports/execution_evidence.json", {"status": status, "executions": records})
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
