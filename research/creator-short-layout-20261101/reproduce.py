import argparse, hashlib, importlib.util, json, subprocess, tempfile
from pathlib import Path

def reproduce(repo, revision=None):
    spec = importlib.util.spec_from_file_location('creator_fixture', repo / 'tests/test_creator_assignment_captured.py')
    t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
    for path, digest in t.ELF_SHA256.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    cases = t.truncated_creator_cases()
    checker = t.CreatorAssignmentCapturedTests()
    hashes = {}
    with tempfile.TemporaryDirectory(prefix='creator-short-') as temporary:
        root = Path(temporary)
        for name in ('creator_assignment.rs', 'creator_assignment_host.rs'):
            relative = 'programs/pump/recovered/' + name
            raw = subprocess.check_output(['git', 'show', revision + ':' + relative], cwd=repo) if revision else (repo / relative).read_bytes()
            (root / name).write_bytes(raw); hashes[relative] = hashlib.sha256(raw).hexdigest()
        host = root / 'host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(root / 'creator_assignment_host.rs'), '-o', str(host)], check=True)
        checker.host = host
        rows = []
        answers = checker.host_answers(cases)
        assert len(answers) == len(cases)
        for item, answer in zip(cases, answers):
            captured = t.run_captured(item)
            try: checker.assert_matches(item, answer, captured)
            except AssertionError as error: mismatch = str(error)
            else: mismatch = None
            rows.append({'input': t.host_line(item), 'host': answer, 'captured': captured, 'mismatch': mismatch})
    return {'revision': revision or 'working-tree', 'source_sha256': hashes, 'captured_sha256': list(t.ELF_SHA256.values())[0], 'cases': len(rows), 'mismatches': sum(r['mismatch'] is not None for r in rows), 'rows': rows}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Native creator model versus signed captured Pump; no Metaplex program loaded.')
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2]); parser.add_argument('--revision'); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); result = reproduce(args.repo.resolve(), args.revision)
    args.output.write_text(json.dumps(result, indent=2, default=lambda b: b.hex()) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'rows'}, indent=2))
