#!/usr/bin/env python3
"""Read-only fairness regression probe. Nonzero exit means fairness gaps remain.

This adds no production changes and edits no existing tests. Copied attack inputs
and actual CLI stdout/stderr are saved under --output-dir for inspection.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def manifest(root):
    tracked = []
    for folder in ['engine', 'scripts', 'tests', 'cards', 'schemas', 'data', 'resources', 'docs']:
        tracked.extend(p for p in (root / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    tracked.extend(root / p for p in ['predict.py', 'plan_fight.py', 'README.md', 'pyproject.toml', 'requirements.txt'])
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(tracked) if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    root, out = args.root.resolve(), args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(root))
    from engine.ontology import Knowledge
    from engine.probability import predict
    from engine.capabilities import training, available
    from engine.fight_director import plan
    from engine.event_graph import validate
    before = manifest(root)
    k = Knowledge(root)
    cards = {name: k.card(root / 'cards' / (name + '.json')) for name in ['maleek', 'donnell', 'wrestler']}
    findings, executions = [], []

    def invoke(tag, a, b):
        ap, bp = out / 'inputs' / (tag + '_a.json'), out / 'inputs' / (tag + '_b.json')
        dump(ap, a)
        dump(bp, b)
        result_path = out / (tag + '_prediction.json')
        command = [sys.executable, str(root / 'predict.py'), str(ap), str(bp), '--ruleset', 'mma', '--output', str(result_path)]
        run = subprocess.run(command, cwd=out, capture_output=True, text=True)
        executions.append({'tag': tag, 'command': command, 'exit_code': run.returncode, 'stdout': run.stdout, 'stderr': run.stderr})
        result = json.loads(result_path.read_text()) if run.returncode == 0 else None
        return run.returncode, result

    a, b = cards['wrestler'], cards['donnell']
    original = predict(a, b, knowledge=k)
    clone = copy.deepcopy(a)
    copied_slot = copy.deepcopy(clone['synchronized_capabilities'][0])
    copied_slot['id'] = 'audit_duplicate_slot'
    copied_slot['description'] = 'Copied training, no new synchronized mechanism.'
    clone['synchronized_capabilities'].append(copied_slot)
    clone['slot_count'] += 1
    clone['slot_label'] = 'Triad'
    code, result = invoke('duplicate_slot', clone, b)
    equal_training = training(a) == training(clone)
    equal_techniques = available(k, a, 'mma') == available(k, clone, 'mma')
    violation = code == 0 and result['probability_a'] > original['probability_a'] and equal_training and equal_techniques
    findings.append({'id': 'F-001', 'classification': 'CONFIRMED_DEFECT' if violation else 'NOT_REPRODUCED',
                     'oracle': 'Cloning an existing slot while changing only its ID/description must not earn another synchronization bonus.',
                     'public_cli_accepted': code == 0, 'same_training': equal_training, 'same_available_techniques': equal_techniques,
                     'before_probability': original['probability_a'], 'after_probability': result['probability_a'] if result else None,
                     'extra_logit': result['logit_a'] - original['logit_a'] if result else None,
                     'source': ['engine/ontology.py:72', 'engine/probability.py:18'],
                     'important_distinction': 'Legitimate new coordination may use existing techniques. Equality of the available-technique set alone is not evidence of fraud; this probe copies an existing bundle without a new mechanism.'})

    a, b = cards['donnell'], cards['wrestler']
    original = predict(a, b, knowledge=k)
    label = copy.deepcopy(a)
    label['dimensions']['tie'] = 'tie.anti_grappling'
    code, result = invoke('unearned_tie_label', label, b)
    violation = code == 0 and result['null_effect']['a_count'] < original['null_effect']['a_count'] and training(a) == training(label)
    findings.append({'id': 'F-002', 'classification': 'CONFIRMED_DEFECT' if violation else 'NOT_REPRODUCED',
                     'oracle': 'A style label unsupported by the card\'s training and techniques must not erase an uncovered capability or earn trained-style matrix credit.',
                     'public_cli_accepted': code == 0, 'same_training': training(a) == training(label),
                     'same_available_techniques': available(k, a, 'mma') == available(k, label, 'mma'),
                     'has_anti_grappling_training': 'anti_grappling' in training(label),
                     'before_probability': original['probability_a'], 'after_probability': result['probability_a'] if result else None,
                     'before_null_logit': original['null_effect']['logit'], 'after_null_logit': result['null_effect']['logit'] if result else None,
                     'source': ['engine/ontology.py:66', 'engine/capabilities.py:41', 'engine/matchups.py:9']})

    bad = copy.deepcopy(cards['donnell'])
    bad['dimensions']['hands'] = 'hands.nonexistent_audit_option'
    bad_code, _ = invoke('invalid_id_control', bad, cards['maleek'])
    good = predict(cards['maleek'], cards['donnell'], knowledge=k)
    reverse = predict(cards['donnell'], cards['maleek'], knowledge=k)
    renamed = copy.deepcopy(cards['maleek'])
    renamed['name'] = 'Different display name'
    renamed['appearance']['identity_anchor'] = 'Different visual reference'
    cosmetic = predict(renamed, cards['donnell'], knowledge=k)
    controls = {'invalid_id_rejected': bad_code != 0,
                'probability_complementarity': math.isclose(good['probability_a'] + reverse['probability_a'], 1),
                'display_metadata_does_not_change_probability': good['probability_a'] == cosmetic['probability_a']}

    # Seed 42 is the supplied demonstration; 43 is its adjacent seed to contrast
    # outcomes, not a statistical sample or an estimate of long-run fairness.
    paths = []
    for seed in [42, 43]:
        p = plan(cards['maleek'], cards['donnell'], seed=seed, knowledge=k)
        validation = validate(k, p)
        actors = p['final_state']['actors']
        paths.append({'seed': seed, 'winner': p['selection']['winner_id'], 'probability_maleek': p['prediction']['probability_a'],
                      'marks': {i: a['contact_marks'] + a['control_marks'] for i, a in actors.items()},
                      'validation': validation,
                      'score_increasing_loop_event_ids': [e['id'] for e in p['events'] if e['type'] in ['execution', 'movement'] and e['intent'] == 'Establish a demonstrated contact/control advantage in this conditional outcome path.']})
    findings.append({'id': 'F-003', 'classification': 'CONFIRMED_DESIGN_LIMIT',
                     'oracle': 'Conditional choreography must not be represented as independent evidence that its preselected winner earned a victory.',
                     'source': ['engine/fight_director.py:125', 'engine/fight_director.py:213', 'engine/fight_state.py:237'],
                     'runs': paths,
                     'interpretation': 'Outcome-first planning is allowed by the original predictive/director contract. It is unsuitable as independent adjudication and its manufactured marks must not update empirical rankings.'})
    after = manifest(root)
    preserved = before == after
    report = {'audit_contract': 'Validate the previously reported fairness findings through public CLI and actual planner execution; do not patch the implementation.',
              'root': str(root), 'model_version': k.model['version'], 'knowledge_sha256': k.fingerprint(),
              'fairness_gate_status': 'FAIL' if any(f['classification'] == 'CONFIRMED_DEFECT' for f in findings) else 'NO_PREVIOUS_DEFECT_REPRODUCED',
              'findings': findings, 'controls': controls, 'protected_files_unchanged': preserved,
              'test_hashes_before': {p: h for p, h in before.items() if p.startswith('tests/')},
              'test_hashes_after': {p: h for p, h in after.items() if p.startswith('tests/')},
              'scope_limit': 'These are concrete counterexamples and selected controls, not an exhaustive fairness or statistical calibration proof.'}
    dump(out / 'reproduction_results.json', report)
    dump(out / 'cli_executions.json', executions)
    dump(out / 'protected_manifest_before.json', before)
    dump(out / 'protected_manifest_after.json', after)
    print(json.dumps({'fairness_gate_status': report['fairness_gate_status'], 'findings': [{'id': f['id'], 'classification': f['classification']} for f in findings], 'controls': controls, 'protected_files_unchanged': preserved}, indent=2))
    if not preserved or not all(controls.values()):
        return 2
    return 1 if report['fairness_gate_status'] == 'FAIL' else 0


if __name__ == '__main__':
    raise SystemExit(main())
