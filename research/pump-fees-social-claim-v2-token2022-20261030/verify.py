#!/usr/bin/env python3
"""Independent re-check of this packet: replay every receipt on both images.

usage (inside the packet folder): python3 verify.py --images '{"original": p, "candidate": p}'
Uses only runtime/receipts.jsonl.gz, runtime/report.json.gz, producer.py (for the
replay / snapshot code; the case list is taken from the receipts) and the two images.
Exit 0 = every recorded step and final account state reproduces on its own image,
image sha256 values equal the report, and the report summary is consistent.
"""
import sys
sys.dont_write_bytecode = True
import argparse, gzip, hashlib, json, pathlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import producer  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--images', required=True)
    a = p.parse_args()
    images = producer.load_images(a.images)
    report = json.loads(gzip.decompress((HERE / 'runtime/report.json.gz').read_bytes()))
    receipts = [json.loads(l) for l in gzip.decompress((HERE / 'runtime/receipts.jsonl.gz').read_bytes()).splitlines()]
    problems = []
    for name in ['original', 'candidate']:
        sha = hashlib.sha256(pathlib.Path(images[name]).read_bytes()).hexdigest()
        if sha != report['image_sha256'][name]:
            problems.append(f'{name} image sha256 {sha} != report {report["image_sha256"][name]}')
    if problems:
        print('\n'.join(problems)); sys.exit(1)
    if report['compared_fields'] != producer.COMPARED or report['program_id'] != str(producer.PROGRAM):
        problems.append('compared fields / program id differ from producer.py')
    if report['social_fee_pda']['address'] != str(producer.SOCIAL):
        problems.append('social PDA address differs')
    if len(receipts) != report['case_count'] or [r['case']['name'] for r in receipts] != [c['name'] for c in report['cases']]:
        problems.append('receipt/report case list differs')
    steps_total = 0
    for r, summary in zip(receipts, report['cases']):
        case = r['case']
        replays = {}
        for name in ['original', 'candidate']:
            got_steps, got_final = producer.run_case(images[name], case)
            replays[name] = got_steps
            if len(got_steps) != len(r['steps']):
                problems.append(f'{case["name"]} {name}: step count differs')
            for i, (got, rec) in enumerate(zip(got_steps, r['steps'])):
                if got != rec[name]:
                    problems.append(f'{case["name"]} step {i} ({rec["label"]}) {name}: replay differs from receipt')
            if got_final != r['final_state'][name]:
                problems.append(f'{case["name"]} {name}: final state differs from receipt')
        step_match = [all(o[f] == k[f] for f in producer.COMPARED) for o, k in zip(replays['original'], replays['candidate'])]
        final_match = r['final_state']['original'] == r['final_state']['candidate']
        if [s['match'] for s in r['steps']] != step_match or r['final_match'] != final_match:
            problems.append(f'{case["name"]}: recorded match flags differ from recomputed')
        if summary['match'] != (final_match and all(step_match)) or summary['steps'] != len(r['steps']):
            problems.append(f'{case["name"]}: report summary differs')
        if summary['outcomes'] != [producer.outcome(s) for s in replays['original']] or summary['outcomes_candidate'] != [producer.outcome(s) for s in replays['candidate']]:
            problems.append(f'{case["name"]}: report outcomes differ')
        if summary['cu_original'] != [s['compute_units'] for s in replays['original']] or summary['cu_candidate'] != [s['compute_units'] for s in replays['candidate']]:
            problems.append(f'{case["name"]}: report compute units differ')
        steps_total += len(r['steps'])
    if steps_total != report['step_count']:
        problems.append('step_count differs')
    if report['mismatched_cases'] != [c['name'] for c in report['cases'] if not c['match']]:
        problems.append('mismatched_cases differs')
    if report['cu_mismatched_cases'] != [c['name'] for c in report['cases'] if c['cu_original'] != c['cu_candidate']]:
        problems.append('cu_mismatched_cases differs')
    if problems:
        print('\n'.join(problems[:50])); print(f'FAIL {len(problems)} problems'); sys.exit(1)
    print(json.dumps({'verified_cases': len(receipts), 'verified_steps': steps_total, 'mismatched_cases': report['mismatched_cases'],
                      'cu_mismatched_cases': report['cu_mismatched_cases']}))
    sys.exit(0)


if __name__ == '__main__':
    main()
