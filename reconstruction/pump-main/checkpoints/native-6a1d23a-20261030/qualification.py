#!/usr/bin/env python3
"""Frozen6a source/build qualification using the UNMODIFIED maintained scorer.

No compiler is run. Historical score files are comparison references, never proof
of the incoming ELF's source. A hosted-run/archive authentication is a separate
coordinator responsibility; this checks the internally bound source/build record.
"""
import argparse
import csv
import difflib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import struct
import sys
import tarfile

HEAD = None  # Explicit immutable --source-head; never inferred from a branch name.
ORIGINAL = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
INPUT_PATHS = (
    'reconstruction/harness/score.py',
    'reconstruction/harness/llvm_tools.py',
    'reconstruction/harness/elf_symbols.py',
    'reconstruction/base/functions.tsv',
    'reconstruction/pump-main/baseline/score.json',
    'reconstruction/pump-main/baseline/rescore.json',
)

TARGETS = {
    0x5b3b0: (18584, r'15multi_hop_curve8swap_hop17h[0-9a-f]{16}E$'),
    0x72810: (7832, r'5sweep7execute17h[0-9a-f]{16}E$'),
    0x6cd78: (8544, r'11legacy_sell22process_cashback_inner17h[0-9a-f]{16}E$'),
    0x77940: (8832, r'8cashback8claim_v217h[0-9a-f]{16}E$'),
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    # Duplicate JSON keys must not silently select one provenance assertion.
    def unique(pairs):
        out = {}
        for key, value in pairs:
            need(key not in out, f'duplicate JSON key: {key}')
            out[key] = value
        return out
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique)


PROOF = None
UNVERIFIED_TOOLCHAIN = []


def git_file(repo, head, path):
    location = repo / ('controller/' + path if head != HEAD else path)
    data = location.read_bytes()
    mode, expected = PROOF.lookup(head, path)
    need(blob_id(data) == expected, f'Git blob differs: {path}')
    return data


def blob_id(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def source_tree(repo):
    out = {}
    for path, (mode, blob) in PROOF.leaves(HEAD, 'programs/pump').items():
        need(mode == '100644', f'unsupported source mode: {path}')
        data = git_file(repo, HEAD, path)
        out[path] = {'mode': mode, 'gitBlob': blob, 'sha256': sha(data),
                     'bytes': len(data), 'data': data}
    need(len(out) == 99, 'frozen source inventory differs')
    return out


def compact(source):
    return {key: {'sha256': row['sha256'], 'bytes': row['bytes']}
            for key, row in source.items()}


def compiled_projection(source):
    # Exact text transform in maintained fastbuild.stage; not an alternate recipe.
    text = source['programs/pump/Cargo.toml']['data'].decode()
    ps, ws = text.index('[profile.release]'), text.index('[workspace]')
    need(ps < ws and not text[ws + len('[workspace]'):].strip(), 'unexpected manifest layout')
    profile = text[ps:ws].strip() + '\n'
    data = {key: row['data'] for key, row in source.items()
            if key not in ('programs/pump/Cargo.toml', 'programs/pump/Cargo.lock')}
    data['programs/pump/Cargo.toml'] = (text[:ps].rstrip() + '\n').encode()
    data['Cargo.toml'] = ('[workspace]\nmembers = ["programs/pump"]\nresolver = "2"\n\n' + profile).encode()
    data['Cargo.lock'] = source['programs/pump/Cargo.lock']['data']
    return {key: {'data': value, 'sha256': sha(value), 'bytes': len(value)}
            for key, value in data.items()}


def verify_tar(path, expected):
    observed = {}
    with tarfile.open(path, 'r:gz') as archive:
        for member in archive:
            need(member.isfile() and member.name in expected, f'unexpected archive entry: {member.name}')
            need(member.name not in observed, f'duplicate archive entry: {member.name}')
            need(member.mode == 0o644, f'archive mode differs: {member.name}')
            data = archive.extractfile(member).read()
            observed[member.name] = {'sha256': sha(data), 'bytes': len(data)}
    need(observed == compact(expected), f'archive source content/set differs: {path.name}')


def frozen_inputs(repo, original):
    bindings = {}
    for path in INPUT_PATHS:
        data = git_file(repo, HEAD, path)
        digest = sha(data)
        actual = repo / path
        need(actual.is_file() and sha(actual.read_bytes()) == digest,
             f'missing/modified materialized scorer input: {path}')
        bindings[path] = {'sha256': digest, 'gitBlob': blob_id(data)}
    ob = original.read_bytes()
    need(sha(ob) == ORIGINAL, 'captured original ELF hash differs')
    source = source_tree(repo)
    baseline = read_json(repo / 'reconstruction/pump-main/baseline/score.json')['windows']
    rescore = read_json(repo / 'reconstruction/pump-main/baseline/rescore.json')
    rows = [r for r in csv.DictReader(io.StringIO((repo / 'reconstruction/base/functions.tsv').read_text()), delimiter='\t')
            if r['program'] == 'pump' and r['variant'] == 'selected']
    expected = {int(r['original_start']): int(r['bytes']) for r in rows}
    need(len(rows) == len(expected) == 1035, 'original inventory is not 1035 unique windows')
    for other in (baseline, rescore['windows']):
        need(set(map(int, other)) == set(expected), 'baseline window membership differs')
        for key, row in other.items():
            need(type(row['normalized']) is bool and type(row['raw']) is bool,
                 'non-boolean baseline membership')
            need(row['bytes'] == expected[int(key)] and (not row['raw'] or row['normalized']),
                 'invalid baseline length/raw membership')
    for key in baseline:
        need(all(baseline[key][field] == rescore['windows'][key][field]
                 for field in ('normalized', 'raw', 'bytes')), 'frozen baseline and rescore disagree')
    historical = {'label': 'frozen Git baseline/rescore reference, NOT the incoming source build',
        'symbols_sha256': rescore['summary']['candidate_sha256'],
        'normalized': sum(r['normalized'] for r in baseline.values()),
        'raw': sum(r['raw'] for r in baseline.values()), 'total': len(baseline)}
    need(historical['normalized'] == rescore['summary']['normalized'] and historical['raw'] == rescore['summary']['raw'], 'historical counts differ from bound rescore')
    return source, baseline, expected, bindings, historical, ob


def artifact_provenance(args, source):
    root = args.artifact_dir
    need((root / 'RESULT.json').is_file(), 'missing build provenance: RESULT.json')
    result = read_json(root / 'RESULT.json')
    need(result['base'] == HEAD, f'stale result source: {result["base"]}')
    need(result.get('gitSourceManifest') == 'program-source-inputs.json'
         and result.get('builderSourceManifest') == 'source-inputs.json',
         'distinct Git/builder source manifest names must be explicit')
    required = ['baseline-input.json', 'RESULT.json', 'program-source-inputs.json',
        'source-inputs.json', 'compiled-workspace-inputs.json',
        'program-source.tar.gz', 'compiled-workspace.tar.gz', 'build.json', 'cold-build.log',
        'build.log', 'commands.jsonl', 'controller-inputs.json', 'toolchain-source-inputs.json',
        'registry-source-inputs.json', 'tool-inputs.json', 'host.json', 'bootstrap-before.log',
        'bootstrap-after.log', 'score.json', 'unstripped.so', 'candidate.so']
    for name in required:
        need((root / name).is_file(), f'missing build provenance: {name}')
    bm = read_json(root / 'baseline-input.json')
    need(bm['path'] == 'reconstruction/pump-main/baseline/score.json' and bm['sha256'] == sha(git_file(args.repo, HEAD, bm['path'])), 'historical baseline binding differs')
    for field in ('sourceUnchanged', 'registrySourceUnchanged', 'coldTarget'):
        need(result.get(field) is True, f'build invariant missing/false: {field}')
    sm = read_json(root / 'program-source-inputs.json')
    need(sm['base'] == HEAD, 'source manifest base differs')
    listed = {}
    for row in sm['files']:
        path = row['path']
        need(path not in listed, f'duplicate source input: {path}')
        listed[path] = {k: row[k] for k in ('mode', 'gitBlob', 'sha256', 'bytes')}
    need(listed == {p: {k: r[k] for k in ('mode', 'gitBlob', 'sha256', 'bytes')}
                    for p, r in source.items()}, 'source manifest does not equal all frozen6a files')
    verify_tar(root / 'program-source.tar.gz', source)
    compiled = compiled_projection(source)
    need(read_json(root / 'compiled-workspace-inputs.json') == compact(compiled),
         'compiled workspace manifest differs from exact staging projection')
    verify_tar(root / 'compiled-workspace.tar.gz', compiled)
    build = read_json(root / 'build.json')
    builder_source = read_json(root / 'source-inputs.json')
    need(builder_source.get('schema') == 'pump-source-inputs-v1', 'builder snapshot schema differs')
    expected_builder_rows = sorted([
        {'path': path.removeprefix('programs/pump/'), 'bytes': row['bytes'],
         'executable': bool(int(row['mode'], 8) & 0o111), 'sha256': row['sha256']}
        for path, row in source.items()], key=lambda row: row['path'])
    need(builder_source.get('files') == expected_builder_rows,
         'actual builder snapshot differs from complete Git source vector')
    encoded = json.dumps(builder_source['files'], sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False).encode('utf-8')
    need(sha(encoded) == builder_source.get('sha256') == build.get('source_sha256')
         == result.get('builderSourceSha256'), 'builder source aggregate/build/result binding differs')
    cold_text = (root / 'cold-build.log').read_text()
    build_records = []
    for marker in re.finditer(r'(?m)^\{', cold_text):
        try:
            value, end = json.JSONDecoder().raw_decode(cold_text[marker.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and 'runtime_valid' in value and 'unstripped_sha256' in value:
            build_records.append(value)
    need(build_records == [build], 'cold build/result records disagree or are ambiguous')
    for field in ('ok', 'runtime_valid'):
        need(build.get(field) is True, f'cold build invariant missing/false: {field}')
    need(build.get('stack_warnings') == [], 'stack warnings are not empty')
    need(build.get('recipe') == 'identity' and build.get('triple') == 'sbpf-solana-solana', 'recipe differs')
    need('exceeded max offset' not in (root / 'build.log').read_text(), 'build log has stack overflow diagnostic')
    for filename, a, b in [('unstripped.so', 'unstrippedSha256', 'unstripped_sha256'),
                          ('candidate.so', 'candidateSha256', 'candidate_sha256')]:
        digest = sha((root / filename).read_bytes())
        need(result.get(a) == digest and build.get(b) == digest, f'ELF/build hash differs: {filename}')
    controller = read_json(root / 'controller-inputs.json')
    need(args.controller_head and args.runner_git_path and args.workflow_git_path,
         'exact controller checkout and runner/workflow Git paths are required')
    need(controller.get('checkout') == args.controller_head, 'controller checkout differs')
    need(controller.get('recipe') == 'identity' and controller.get('triple') == 'sbpf-solana-solana',
         'controller recipe differs')
    need(controller.get('gitSourceManifest') == result['gitSourceManifest']
         and controller.get('builderSourceManifest') == result['builderSourceManifest'],
         'controller/result source manifest names differ')
    for field, path in [('runnerSha256', args.runner_git_path), ('workflowSha256', args.workflow_git_path)]:
        need(controller[field] == sha(git_file(args.repo, args.controller_head, path)),
             f'controller source pin differs: {field}')
    toolchain = read_json(root / 'toolchain-source-inputs.json')
    need(toolchain['base'] == HEAD and toolchain['files'], 'missing/stale toolchain source map')
    mapped = {}
    for row in toolchain['files']:
        path = row['path']
        need(path not in mapped, f'duplicate toolchain source: {path}')
        mode, blob = PROOF.lookup(HEAD, path)
        need(blob == row['gitBlob'], f'toolchain Git blob differs: {path}')
        if (args.repo / path).is_file():
            data = git_file(args.repo, HEAD, path)
            need(row['sha256'] == sha(data) and row['bytes'] == len(data),
                 f'toolchain bytes differ: {path}')
        else:
            UNVERIFIED_TOOLCHAIN.append(path)
        mapped[path] = row['sha256']
    for path in (*INPUT_PATHS, 'reconstruction/harness/fastbuild.py',
                 'reconstruction/harness/build_process.py', 'reconstruction/harness/source_inputs.py',
                 'reconstruction/harness/pump_physical_source_wrapper.py'):
        need(path in mapped, f'missing toolchain/scorer binding: {path}')
    tools = read_json(root / 'tool-inputs.json')
    need(bool(tools), 'empty tool map')
    external = {}
    for path, digest in tools.items():
        need(re.fullmatch('[0-9a-f]{64}', digest), f'invalid tool digest: {path}')
        if not path.startswith('/'):
            need(path in mapped and digest == mapped[path], f'build-tool Git hash differs: {path}')
        else:
            external[path] = digest
    need(len(external) == 5, 'expected five external SDK/hybrid executable hash records')
    suffixes = ('v1.44/platform-tools/rust/bin/rustc',
                'hybrid144/rust/bin/rustc', 'v1.44/platform-tools/rust/bin/cargo',
                'v1.44/platform-tools/llvm/bin/llvm-objcopy',
                'v1.52/platform-tools/llvm/bin/llvm-objdump')
    matched = {}
    for suffix in suffixes:
        candidates = [v for k, v in external.items() if k.endswith(suffix)]
        need(len(candidates) == 1, f'missing/ambiguous executable record: {suffix}')
        matched[suffix] = candidates[0]
    need(matched[suffixes[0]] == matched[suffixes[1]], 'hybrid rustc is not the native Mac rustc bytes')
    registry = read_json(root / 'registry-source-inputs.json')
    need(registry and all(isinstance(k, str) and re.fullmatch('[0-9a-f]{64}', v)
                         for k, v in registry.items()), 'invalid registry hash map')
    host = read_json(root / 'host.json')
    need(host['base'] == HEAD and host['platform'].startswith('macOS-') and host['machine'] == 'arm64',
         'host/source record is not the native Mac control')
    commands = [json.loads(line) for line in (root / 'commands.jsonl').read_text().splitlines() if line.strip()]
    names = [row.get('name') for row in commands]
    need(all(names.count(n) == 1 for n in ('bootstrap-before', 'fetch-locked', 'cold-build', 'bootstrap-after', 'score')),
         'missing/ambiguous command chain')
    need(all(row.get('returncode') == 0 for row in commands), 'nonzero recorded command')
    need(names.index('bootstrap-before') < names.index('cold-build') < names.index('bootstrap-after') < names.index('score'),
         'build/SDK/score command order differs')
    cold = commands[names.index('cold-build')]['command']
    need(cold[cold.index('--recipe') + 1] == 'identity', 'cold command recipe differs')
    for n in ('bootstrap-before.log', 'bootstrap-after.log'):
        text = (root / n).read_text()
        need('SDK verified (full,' in text and 'Linux v1.44 sbpf target libraries verified (25 rlibs)' in text,
             f'missing full SDK/target-library check: {n}')
    return {name: {'bytes': (root / name).stat().st_size, 'sha256': sha((root / name).read_bytes())}
            for name in required}, result


def load_scorer(repo, original, output):
    # Exact maintained code in an isolated input projection. No monkeypatch of
    # scorer globals or functions: BASE resolves normally to authenticated links.
    replay = output / 'scorer-replay/reconstruction'
    harness, base = replay / 'harness', replay / 'base'
    harness.mkdir(parents=True)
    base.mkdir()
    for name in ('score.py', 'llvm_tools.py', 'elf_symbols.py'):
        src, dst = repo / 'reconstruction/harness' / name, harness / name
        shutil.copyfile(src, dst)
        need(sha(dst.read_bytes()) == sha(src.read_bytes()), 'scorer projection differs')
    (base / 'original.so').symlink_to(original.resolve())
    (base / 'functions.tsv').symlink_to((repo / 'reconstruction/base/functions.tsv').resolve())
    path = harness / 'score.py'
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location('maintained_pump_score', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tokens(data):
    out = []
    i = 0
    while i < len(data):
        n = 16 if data[i] == 0x18 else 8
        need(i + n <= len(data), 'truncated BPF instruction')
        out.append(data[i:i+n])
        i += n
    return out


def residual(original, candidate, onorm, cnorm):
    slots = []
    for i in range(0, max(len(original), len(candidate)), 8):
        a, b, an, bn = original[i:i+8], candidate[i:i+8], onorm[i:i+8], cnorm[i:i+8]
        slots.append({'offset': i, 'original_raw': a.hex(), 'candidate_raw': b.hex(),
            'original_normalized': an.hex(), 'candidate_normalized': bn.hex(),
            'raw_equal': a == b, 'normalized_equal': an == bn,
            'raw_different_byte_offsets': [i+j for j in range(max(len(a), len(b))) if a[j:j+1] != b[j:j+1]],
            'normalized_different_byte_offsets': [i+j for j in range(max(len(an), len(bn))) if an[j:j+1] != bn[j:j+1]]})
    seq = difflib.SequenceMatcher(None, tokens(onorm), tokens(cnorm), autojunk=False)
    return {'interpretation': 'positional 8-byte slot comparison; sequence alignment is diagnostic only, NOT operation correspondence or scorer acceptance',
        'original_bytes': len(original), 'candidate_bytes': len(candidate),
        'raw_different_bytes': sum(len(s['raw_different_byte_offsets']) for s in slots),
        'normalized_different_bytes': sum(len(s['normalized_different_byte_offsets']) for s in slots),
        'raw_different_slots': sum(not s['raw_equal'] for s in slots),
        'normalized_different_slots': sum(not s['normalized_equal'] for s in slots),
        'normalized_instruction_sequence_ratio': seq.ratio(),
        'normalized_instruction_sequence_opcodes': [list(v) for v in seq.get_opcodes()], 'slots': slots}


def run(args):
    source, baseline, expected, pins, historical, ob = frozen_inputs(args.repo, args.original)
    controller_pins = None
    if any((args.controller_head, args.runner_git_path, args.workflow_git_path)):
        need(all((args.controller_head, args.runner_git_path, args.workflow_git_path)),
             'all three explicit controller arguments are required together')
        need(bool(re.fullmatch('[0-9a-f]{40}', args.controller_head)), 'controller must be a full commit SHA')
        controller_pins = {'checkout': args.controller_head, 'files': {}}
        for path in (args.runner_git_path, args.workflow_git_path):
            data = git_file(args.repo, args.controller_head, path)
            controller_pins['files'][path] = {'sha256': sha(data), 'gitBlob': blob_id(data), 'bytes': len(data)}
    base_report = {'source_head': HEAD, 'original_sha256': ORIGINAL, 'input_bindings': pins,
        'expected_controller': controller_pins,
        'source_tree': PROOF.lookup(HEAD, 'programs/pump')[1],
        'source_input_vector': {p: {k: r[k] for k in ('mode', 'gitBlob', 'bytes', 'sha256')} for p, r in source.items()},
        'source_files': len(source), 'compiled_workspace_files': len(compiled_projection(source)),
        'historical_reference': historical,
        'focus_historical_membership': {hex(a): baseline[str(a)] for a in TARGETS},
        'limits': ['No compiler, runtime or Rust candidate executed.',
            'Historical baseline is not a measurement of the incoming source commit.',
            'Hosted identity is retained metadata; optional physical SDK/registry checks are reported separately.']}
    if args.inspect_only:
        return base_report
    need(args.artifact_dir, '--artifact-dir is required unless --inspect-only')
    provenance, result = artifact_provenance(args, source)
    scorer = load_scorer(args.repo, args.original, args.output)
    actual, scored_hash = scorer.score_with_hash(args.artifact_dir / 'unstripped.so')
    need(scored_hash == result['unstrippedSha256'], 'scored ELF snapshot differs from authenticated build')
    need(set(actual) == set(expected), 'fresh scorer membership does not contain all 1035 windows')
    recorded = read_json(args.artifact_dir / 'score.json')
    need(recorded['windows'] == {str(k): v for k, v in actual.items()}, 'recorded census differs from fresh scorer')
    rows, gains, losses, raw_gains, raw_losses = [], [], [], [], []
    for start in sorted(actual):
        before, after = baseline[str(start)], actual[start]
        need(after['bytes'] == expected[start], 'fresh score byte length differs')
        for field, plus, minus in [('normalized', gains, losses), ('raw', raw_gains, raw_losses)]:
            if after[field] and not before[field]: plus.append(hex(start))
            if before[field] and not after[field]: minus.append(hex(start))
        rows.append({'original_start': hex(start), 'bytes': expected[start],
            'historical_normalized': before['normalized'], 'current_normalized': after['normalized'],
            'normalized_retained': not before['normalized'] or after['normalized'],
            'historical_raw': before['raw'], 'current_raw': after['raw'],
            'raw_retained': not before['raw'] or after['raw'], 'current_symbols': after['symbols']})
    digest = sha((args.artifact_dir / 'unstripped.so').read_bytes())
    summary = {'candidate_sha256': digest, 'normalized': sum(v['normalized'] for v in actual.values()),
        'raw': sum(v['raw'] for v in actual.values()), 'total': len(actual),
        'matched_text_bytes': sum(v['bytes'] for v in actual.values() if v['normalized']),
        'gains': gains, 'losses': losses, 'raw_gains': raw_gains, 'raw_losses': raw_losses}
    need(recorded['summary'] == summary and result['summary'] == summary, 'recorded summaries differ from actual scorer')
    cb = (args.artifact_dir / 'unstripped.so').read_bytes()
    need(sha(cb) == scored_hash, 'ELF changed during analysis')
    cs, os_ = scorer.sections(cb), scorer.sections(ob)
    fns = scorer.candidate_functions(args.artifact_dir / 'unstripped.so')
    focus = {}
    for start, (n, pattern) in TARGETS.items():
        matches = [(a, length, name) for a, length, name in fns if re.search(pattern, name)]
        need(len({(a, n) for a, n, _ in matches}) == 1, f'focus symbol missing/ambiguous: {start:#x}')
        a, length, _ = matches[0]
        op = scorer.body(ob, os_, start, n)
        cp = scorer.body(cb, cs, a, length)
        report = residual(op, cp, scorer.normalize(op, start, os_), scorer.normalize(cp, a, cs))
        report.update({'original_start': hex(start), 'candidate_start': hex(a),
            'candidate_symbols': [m[2] for m in matches], 'original_body_sha256': sha(op),
            'candidate_body_sha256': sha(cp), 'official_membership': actual[start]})
        focus[hex(start)] = report
    (args.output / 'memberships.json').write_text(json.dumps(rows, indent=2, sort_keys=True)+'\n')
    (args.output / 'focus-residuals.json').write_text(json.dumps(focus, indent=2, sort_keys=True)+'\n')
    base_report.update({'current_summary': summary, 'all_historical_normalized_retained': not losses,
        'all_historical_raw_retained': not raw_losses, 'artifact_provenance_files': provenance,
        'actual_builder_source_sha256': result['builderSourceSha256'],
        'unstripped_original_elf_equal': cb == ob,
        'stripped_original_elf_equal': (args.artifact_dir / 'candidate.so').read_bytes() == ob,
        'unstripped_bytes': len(cb), 'stripped_bytes': (args.artifact_dir / 'candidate.so').stat().st_size,
        'focus_summary': {key: {k: v for k, v in value.items() if k not in ('slots', 'normalized_instruction_sequence_opcodes')}
                          for key, value in focus.items()}})
    return base_report

