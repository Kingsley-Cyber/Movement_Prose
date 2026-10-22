#!/usr/bin/env python3
"""Dedicated, Protected CLI for the Original `05:34` (`e91c686`) `SAKUGA-MLLM-3.1-CAUSAL`
Single-Layer Prompt Template + Knowledge Base Pre-Intent Pipeline.

This script leaves `scripts/sakuga_compiler.py` 100% untouched and byte-identical to `e91c686`,
while giving the original `SAKUGA-MLLM-3.1-CAUSAL` schema its own isolated code path that:
  1. Queries `knowledge_base/` PRIOR to semantic intent (`agent.query.ask`, `agent.propose`,
     `agent.relations.follow`, `agent.causal.closure`, `agent.knobs`, and `handbook_index.db`),
  2. Compiles either an original `05:34` `SAKUGA-MLLM-3.1-CAUSAL` spec/template (`compile-spec`)
     OR a beat-sheet (`compile-beatsheet`) into a pure `05:34` `SAKUGA-MLLM-3.1-CAUSAL` single-layer prompt,
  3. Enforces the 17-Decision original linter (`scripts/sakuga_compiler.py` `lint_clip`) with 0 errors and 0 warnings
     and verifies zero `sakuga_Xperiment` / Layer-1 key leakage.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fight_move_system.composer import compose_clips
from fight_move_system.original_causal_compiler import (
    ORIGINAL_TEMPLATE_PATH,
    assert_pure_0534_causal_spec,
    compile_beatsheet_to_original_0534_causal,
    compile_original_causal_spec_with_kb,
    load_original_sakuga_compiler_module,
    verify_original_compiler_protection,
)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sakuga_original_kb",
        description="Protected 05:34 (e91c686) SAKUGA-MLLM-3.1-CAUSAL Single-Layer Compiler + Knowledge Base Pre-Intent Bridge",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ver = sub.add_parser(
        "verify-protection",
        help="Verify scripts/sakuga_compiler.py is byte-identical to e91c686 (05:34) and lint the 05:34 template",
    )

    p_spec = sub.add_parser(
        "compile-spec",
        help="Query KB prior to semantic intent and compile an original 05:34 SAKUGA-MLLM-3.1-CAUSAL spec or template",
    )
    p_spec.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=ORIGINAL_TEMPLATE_PATH,
        help="Path to 05:34 SAKUGA-MLLM-3.1-CAUSAL JSON/template (default: templates/sakuga_mllm_3_1_causal_0534_template.json)",
    )
    p_spec.add_argument("--taste", choices=["clean", "nakamura"], default="clean", help="Original 05:34 taste preset")
    p_spec.add_argument(
        "--style",
        choices=["cel_default", "genga", "sumi_ink", "trigger_neon", "retro_90s", "ufotable"],
        default="cel_default",
        help="Original 05:34 animation style preset",
    )
    p_spec.add_argument("--kb-taste", type=str, default="heavy, brutal, old school", help="Knowledge Base taste profile")
    p_spec.add_argument("--knob", action="append", default=None, help="KB diversity knob axis=option")
    p_spec.add_argument("--kb-report-out", type=Path, default=None, help="Optional path to write pre-intent KB query JSON")
    p_spec.add_argument("-o", "--out", type=Path, default=None, help="Optional output file path")

    p_bs = sub.add_parser(
        "compile-beatsheet",
        help="Query KB prior to semantic intent and compile a beat-sheet into a pure 05:34 SAKUGA-MLLM-3.1-CAUSAL single-layer prompt",
    )
    p_bs.add_argument("input", type=Path, help="Path to beat-sheet JSON")
    p_bs.add_argument("--taste", choices=["clean", "nakamura"], default="clean", help="Original 05:34 taste preset")
    p_bs.add_argument(
        "--style",
        choices=["cel_default", "genga", "sumi_ink", "trigger_neon", "retro_90s", "ufotable"],
        default="cel_default",
        help="Original 05:34 animation style preset",
    )
    p_bs.add_argument("--kb-taste", type=str, default="heavy, brutal, old school", help="Knowledge Base taste profile")
    p_bs.add_argument("--knob", action="append", default=None, help="KB diversity knob axis=option")
    p_bs.add_argument("--kb-report-out", type=Path, default=None, help="Optional path to write pre-intent KB query JSON")
    p_bs.add_argument("-o", "--out", type=Path, default=None, help="Optional output file path")

    args = parser.parse_args(argv)

    if args.cmd == "verify-protection":
        ok, info = verify_original_compiler_protection()
        orig = load_original_sakuga_compiler_module()
        spec, header = orig.load_clip_file(ORIGINAL_TEMPLATE_PATH)
        prompt = orig.format_sakuga_prompt(orig.order_spec_causally(spec), header)
        errs, warns = assert_pure_0534_causal_spec(spec, prompt)
        report = {
            "sakuga_compiler_e91c686_protected": ok,
            "sha256_or_error": info,
            "template_path": str(ORIGINAL_TEMPLATE_PATH),
            "lint_errors": errs,
            "lint_warnings": warns,
            "ok": bool(ok and not errs and not warns),
        }
        print(json.dumps(report, indent=2))
        return 0 if report["ok"] else 1

    if args.cmd == "compile-spec":
        prompt, spec, kb_priors, errs, warns = compile_original_causal_spec_with_kb(
            args.input,
            taste=args.taste,
            style=args.style,
            kb_taste=args.kb_taste,
            knobs_spec=args.knob,
        )
        for w in warns:
            print(f"[WARN] {w}", file=sys.stderr)
        if errs:
            for e in errs:
                print(f"[ERROR] {e}", file=sys.stderr)
            return 1
        if args.kb_report_out:
            args.kb_report_out.write_text(json.dumps(kb_priors, indent=2) + "\n", encoding="utf-8")
        if args.out:
            args.out.write_text(prompt + "\n", encoding="utf-8")
            print(
                f"[COMPILED 05:34 SAKUGA-MLLM-3.1-CAUSAL] Wrote pure single-layer prompt to {args.out} "
                f"(KB directives surfaced: {len(kb_priors.get('directives', []))}, pulled relations: {len(kb_priors.get('pulled_relations', []))})"
            )
        else:
            print(prompt)
        return 0

    if args.cmd == "compile-beatsheet":
        data = json.loads(args.input.read_text(encoding="utf-8"))
        clips, _ = compose_clips(data)
        prompts: List[str] = []
        last_kb = {}
        for clip in clips:
            prompt, spec, kb_priors, val_res = compile_beatsheet_to_original_0534_causal(
                clip,
                taste=args.taste,
                style=args.style,
                kb_taste=args.kb_taste,
                knobs_spec=args.knob,
            )
            last_kb = kb_priors
            for code, msg in val_res.warnings:
                print(f"[WARN] [{code}] {msg}", file=sys.stderr)
            if not val_res.ok:
                for code, msg in val_res.errors:
                    print(f"[ERROR] [{code}] {msg}", file=sys.stderr)
                return 1
            prompts.append(prompt)
        full_out = "\n\n---\n\n".join(prompts)
        if args.kb_report_out:
            args.kb_report_out.write_text(json.dumps(last_kb, indent=2) + "\n", encoding="utf-8")
        if args.out:
            args.out.write_text(full_out + "\n", encoding="utf-8")
            print(
                f"[COMPILED 05:34 SAKUGA-MLLM-3.1-CAUSAL] Wrote pure single-layer prompt to {args.out} "
                f"(KB directives surfaced: {len(last_kb.get('directives', []))}, pulled relations: {len(last_kb.get('pulled_relations', []))})"
            )
        else:
            print(full_out)
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
