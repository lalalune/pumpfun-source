"""Verify this source/comparison packet; broad raw reports are deliberately not published."""
import argparse
import base64
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ORIGINAL = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
GAINS = {'0x83c00', '0x144508', '0x147ba0'}
CU = re.compile(r'^Program [1-9A-HJ-NP-Za-km-z]+ consumed [0-9]+ of [0-9]+ compute units$')
SITES = re.compile(r'\b(?:require(?:_[A-Za-z0-9_]+)?|error|err|panic|assert(?:_eq|_ne)?|debug_assert(?:_eq|_ne)?|file|line|column)!|\.\s*(?:unwrap|expect)\s*\(')
FOCUSED = {'focused.json.gz': (123, 369, 102, 672), 'crossings.json.gz': (6, 18, 0, 18)}
CROSSINGS = {operation + '_' + quote + '_post_complete_crossing'
             for operation in ('buy_v3', 'buy_exact_quote_in_v3')
             for quote in ('native', 'token', 'token2022')}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if raw[:2] == b'\x1f\x8b' else raw)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def sites(text):
    return [dict(token=m.group(), line=text.count('\n', 0, m.start()) + 1,
                 column=m.start() - text.rfind('\n', 0, m.start())) for m in SITES.finditer(text)]


def logical_sources(record, key, directory):
    recorded_root = Path(record['environment']['RUSTC_WRAPPER']).parent.parent
    return {str((recorded_root / name).relative_to(directory)): digest for name, digest in record[key].items()}


def staged_sources(primary):
    text = (ROOT / 'programs/pump/Cargo.toml').read_text()
    start, end = text.index('[profile.release]'), text.index('[workspace]')
    profile = text[start:end].strip() + '\n'
    crate = text[:start].rstrip() + '\n'
    workspace = '[workspace]\nmembers = ["programs/pump"]\nresolver = "2"\n\n' + profile
    result = {'programs/pump/' + key: value for key, value in primary.items() if key not in ('Cargo.toml', 'Cargo.lock')}
    result.update({'Cargo.lock': primary['Cargo.lock'], 'Cargo.toml': sha(workspace.encode()), 'programs/pump/Cargo.toml': sha(crate.encode())})
    need(primary['Cargo.toml'] == sha(text.encode()), 'unchanged primary manifest')
    return result


def selected(record, images):
    audit = record['independent']
    need(audit['admitted_images_sha256'] == dict(original=ORIGINAL, parent=images['control']['symbols'], proposal=images['candidate']['symbols']), 'selected images')
    need(not audit['whole_elf_equal'] and not audit['complete_recursive_call_or_data_closure'], 'selected scope')
    for name, count in [('create_v2', 125), ('sweep', 37), ('v3_execute_buy', 22), ('sell_v2', 80), ('buy', 29)]:
        target = audit['targets'][name]
        calls = target['calls']
        need(len(calls) == count, 'selected call census ' + name)
        if name == 'sweep':
            need(Counter(tuple(c['original_body']) for c in calls) == Counter(tuple(c['proposal_body']) for c in calls), 'Sweep callee multiset')
        else:
            bad = [c for c in calls if c['original_body'] != c['proposal_body']]
            need(not bad or (name == 'buy' and len(bad) == 1 and bad[0]['offset'] == 2600 and bad[0]['known_residual'] and bad[0]['original_body'][0] == 2120 and bad[0]['proposal_body'][0] == 2136), 'selected callee identity ' + name)
        need(target['complete_normalized_equal'] == (name in ('v3_execute_buy', 'sell_v2', 'buy')), 'selected body equality ' + name)
        need(all(r['decoded'] and r['equal'] for r in target['typed_references']), 'typed references ' + name)
    need(sum(len(t['typed_references']) for t in audit['targets'].values()) == 49 and not audit['unresolved_references'], 'typed reference census')
    for name in ('create_v2', 'sweep'):
        metrics = record['metrics']['targets'][name]['metrics']
        need(metrics['union']['ratio'] > metrics['parent']['ratio'] and not metrics['union']['normalized_equal'], 'partial improvement ' + name)
    need(record['metrics']['text_size_delta'] == 0, 'whole text size')


def flags(cohort):
    """Check saved physical capacities and their one-to-one original assignments."""
    official, strict = cohort['official'], cohort['injective']
    windows = strict['windows']
    need(len(windows) == 1035 and len({r['start'] for r in windows}) == 1035, 'window census')
    with (ROOT / 'reconstruction/base/functions.tsv').open() as stream:
        expected = {(int(r['original_start']), int(r['original_end']) - int(r['original_start']))
                    for r in csv.DictReader(stream, delimiter='\t') if r['program'] == 'pump' and r['variant'] == 'selected'}
    need({(r['start'], r['bytes']) for r in windows} == expected, 'original window boundaries')
    need(set(official['windows']) == {str(r['start']) for r in windows}, 'official census')
    spans = {(r['start'], r['bytes']): r for r in strict['candidates']}
    need(len(spans) == len(strict['candidates']), 'duplicate physical span')
    groups = {kind: defaultdict(set) for kind in ('raw', 'normalized')}
    for span, row in spans.items():
        for kind in groups:
            groups[kind][row['bytes'], row[kind + '_sha256']].add(span)
    used, result = set(), {}
    for row in windows:
        key = str(row['start'])
        for kind in groups:
            eligible = groups[kind].get((row['bytes'], row[kind + '_sha256']), set())
            need({tuple(s) for s in row['eligible_' + kind + '_spans']} == eligible, 'eligible spans ' + key)
            need(official['windows'][key][kind] == bool(eligible), 'official membership ' + key)
        span = tuple(row['allocated_span']) if row['allocated_span'] else None
        need(span is None or (span in groups['normalized'][row['bytes'], row['normalized_sha256']] and span not in used), 'noninjective assignment ' + key)
        if span:
            used.add(span)
        raw = bool(span and spans[span]['raw_sha256'] == row['raw_sha256'])
        need(raw == row['allocated_raw_equal'], 'allocated raw ' + key)
        result[key] = dict(normalized=bool(span), raw=raw)
        need(result[key] == {k: official['windows'][key][k] for k in ('normalized', 'raw')}, 'capacity loses membership ' + key)
    for kind in groups:
        originals = Counter((r['bytes'], r[kind + '_sha256']) for r in windows)
        capacity = sum(min(count, len(groups[kind].get(key, ()))) for key, count in originals.items())
        measured = sum(r[kind] for r in result.values())
        need(measured == capacity == strict['summary'][kind] == official['summary'][kind], 'capacity count ' + kind)
    return result


def membership_gate(base, candidate):
    need(set(base) == set(candidate) and len(base) == 1035, 'comparison census')
    for address, old in base.items():
        for kind in ('normalized', 'raw'):
            need(not old[kind] or candidate[address][kind], 'lost ' + kind + ' ' + hex(int(address)))
    gains = {hex(int(k)) for k in base if candidate[k]['normalized'] and not base[k]['normalized']}
    need(gains == GAINS, 'normalized gain set ' + repr(gains))


def actual_flags(path):
    """Use the unchanged official normalizer, with fresh original bytes and physical aliases."""
    score = module('five_function_official_score', ROOT / 'reconstruction/harness/score.py')
    original = (ROOT / 'evidence/original/pump/deployed.so').read_bytes()
    need(sha(original) == ORIGINAL, 'original ELF')
    candidate = Path(path).read_bytes()
    os_, cs = score.sections(original), score.sections(candidate)
    groups = {kind: defaultdict(list) for kind in ('raw', 'normalized')}
    physical = set()
    for start, size, _ in score.candidate_functions(path):
        if (start, size) in physical:
            continue
        physical.add((start, size))
        raw = score.body(candidate, cs, start, size)
        for kind, data in [('raw', raw), ('normalized', score.normalize(raw, start, cs))]:
            groups[kind][size, sha(data)].append((start, size))
    windows = {}
    with (ROOT / 'reconstruction/base/functions.tsv').open() as stream:
        for row in csv.DictReader(stream, delimiter='\t'):
            if row['program'] == 'pump' and row['variant'] == 'selected':
                start, end = int(row['original_start']), int(row['original_end'])
                raw = score.body(original, os_, start, end - start)
                windows[str(start)] = {kind: (end - start, sha(data)) for kind, data in
                                      [('raw', raw), ('normalized', score.normalize(raw, start, os_))]}
    used, assigned = set(), {}
    for kind in ('raw', 'normalized'):
        for key, row in sorted(windows.items(), key=lambda item: int(item[0])):
            if key in assigned:
                continue
            available = sorted(set(groups[kind].get(row[kind], ())) - used)
            if available:
                assigned[key] = available[0]
                used.add(available[0])
    result = {key: dict(normalized=key in assigned, raw=bool(key in assigned and assigned[key] in groups['raw'].get(row['raw'], ()))) for key, row in windows.items()}
    measured = score.score(path)
    need(all(result[str(k)] == {name: value[name] for name in ('normalized', 'raw')} for k, value in measured.items()), 'official/physical remeasurement differs')
    return result


def wire(encoded):
    from solders.transaction import Transaction, VersionedTransaction
    raw = base64.b64decode(encoded, validate=True)
    try:
        tx = Transaction.from_bytes(raw)
    except ValueError:
        tx = VersionedTransaction.from_bytes(raw)
    checks = tx.verify_with_results()
    need(bytes(tx) == raw and checks and all(checks), 'transaction signature')
    return len(checks)


def focused(report, expected, images):
    claimed = tuple(expected[k] for k in ('cases', 'target_executions', 'bootstrap_executions', 'signature_fields'))
    need(claimed in FOCUSED.values(), 'fixed focused cohort counts')
    need(report['images_sha256'] == images, 'focused image binding')
    rows = report['cases']
    need(len(rows) == expected['cases'] and len({(r['case']['group'], r['case']['name']) for r in rows}) == len(rows), 'focused census')
    targets = bootstraps = signatures = 0
    for row in rows:
        need(set(row['runs']) == {'original', 'control', 'candidate'}, 'focused roles')
        for role, run in row['runs'].items():
            sends = run['sends']
            actual_targets = [s for s in sends if s['phase'] == 'target']
            need(len(actual_targets) == 1 and run['target'] == actual_targets[0], 'focused target receipt')
            targets += 1
            for send in sends:
                need(send['phase'] in ('target', 'bootstrap'), 'send phase')
                bootstraps += send['phase'] == 'bootstrap'
                count = wire(send['transaction_base64'])
                signatures += count
                need(count == send['signature_verification']['signature_count'], 'signature count')
                pump = images['original'] if row['case']['driver'] == 'sweep' and send['phase'] == 'bootstrap' else images[role]
                need(send['active_program_sha256']['6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'] == pump, 'loaded Pump image')
                load = send['captured_loader_loads'][-1]
                need(load['elf_sha256'] == pump and load['elf_prefix_unchanged'] and load['zero_allocation_tail'], 'captured loader')
            original = row['runs']['original']
            need(len(sends) == len(original['sends']), 'focused send census')
            for left, right in zip(original['sends'], sends):
                for field in ('phase', 'error', 'before', 'after', 'events', 'inner', 'return_data', 'transaction_base64'):
                    need(left[field] == right[field], 'focused comparison ' + field)
                need([s for s in left['logs'] if not CU.fullmatch(s)] == [s for s in right['logs'] if not CU.fullmatch(s)], 'focused ordered logs')
            need(run.get('create_wire') == original.get('create_wire'), 'created curve wire')
        need(not row['control_differences'] and not row['candidate_differences'], 'focused recorded mismatch')
    need((targets, bootstraps, signatures) == (expected['target_executions'], expected['bootstrap_executions'], expected['signature_fields']), 'focused totals')
    need((report['target_execution_count'], report['bootstrap_execution_count'], report['signature_fields']) == (targets, bootstraps, signatures), 'focused claimed totals')
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, help='Actual combined unstripped ELF; rescore all windows')
    parser.add_argument('--stripped', type=Path, help='Actual combined loadable ELF')
    args = parser.parse_args()
    need(__debug__, 'Run without Python -O; imported existing tools use assertions')
    summary = read(HERE / 'SUMMARY.json')
    need(summary['complete'], 'packet is not sealed')
    need(summary['original_sha256'] == ORIGINAL, 'original pin')
    need(sha((ROOT / 'evidence/original/pump/deployed.so').read_bytes()) == ORIGINAL, 'actual original ELF')
    for name, digest in summary['artifacts'].items():
        path = HERE / name
        need(path.resolve().is_relative_to(HERE) and not path.is_symlink(), 'artifact path')
        need(sha(path.read_bytes()) == digest, 'artifact hash ' + name)
    for name, digest in summary['tools'].items():
        need(sha((ROOT / name).read_bytes()) == digest, 'tool pin ' + name)
    sources = read(HERE / 'records/sources.json.gz')
    sys.path.insert(0, str(ROOT / 'scripts'))
    from source_manifest_guard import strict_manifest
    current = strict_manifest(ROOT / 'programs/pump', ROOT / 'programs/pump', ROOT)
    current = {str(Path(k).relative_to('programs/pump')): v for k, v in current.items()}
    need(current == sources['candidate']['primary'] and len(current) == 70, 'current compiler inputs')
    cohorts = {'control', 'candidate', 'repeat'}
    need(set(sources) == cohorts | {'source_sites'}, 'source cohorts')
    for cohort in cohorts:
        need(len(sources[cohort]['primary']) == 70 and len(sources[cohort]['compiled']) == 71, '70/71 source census')
        need(sources[cohort]['compiled'] == staged_sources(sources[cohort]['primary']), 'primary/workspace overlay ' + cohort)
    need(sources['candidate'] == sources['repeat'], 'repeat sources')
    for name, expected in sources['source_sites'].items():
        need(sites((ROOT / 'programs/pump' / name).read_text()) == expected, 'Source coordinates ' + name)
    builds = read(HERE / 'records/builds.json.gz')
    need(set(builds['cohorts']) == cohorts, 'build cohorts')
    for name, records in builds['cohorts'].items():
        report = records['comparison']
        need(report['returncode'] == 0 and report['source_unchanged'] and report['target_libraries_unchanged'], 'build success ' + name)
        need(report['source_sha256'] == report['source_after_sha256'] == records['attempt']['source_sha256'], 'build source immutability ' + name)
        primary = logical_sources(report, 'primary_source_sha256', Path(report['primary_source_directory']))
        compiled = logical_sources(report, 'source_sha256', Path(report['source_directory']).parents[1])
        need(dict(primary=primary, compiled=compiled) == sources[name], 'actual source-map binding ' + name)
        need(report['comparison']['candidate_sha256'] == summary['images'][name]['stripped'], 'stripped build binding ' + name)
        need(report['unstripped_sha256'] == summary['images'][name]['symbols'], 'symbols build binding ' + name)
    need(summary['images']['candidate'] == summary['images']['repeat'], 'repeat whole ELF hashes')
    memberships = read(HERE / 'records/memberships.json.gz')
    need(set(memberships) == cohorts, 'membership cohorts')
    base = flags(memberships['control'])
    combined = flags(memberships['candidate'])
    membership_gate(base, combined)
    need(flags(memberships['repeat']) == combined, 'repeat memberships')
    need(sum(v['normalized'] for v in combined.values()) == 1027 and sum(v['raw'] for v in combined.values()) == 277, 'membership totals')
    selected(read(HERE / 'records/selected-audit.json.gz'), summary['images'])
    runtime = read(HERE / 'records/runtime-summary.json.gz')
    need(runtime['complete'] and runtime['broad']['raw_payload_published'] is False, 'runtime disclosure')
    for name, cases in [('broad', 10468), ('extensions', 126)]:
        need(runtime[name]['cases'] == cases and runtime[name]['mismatches'] == 0 and runtime[name]['strict_log_mismatches'] == 0, 'runtime attestation ' + name)
    images = dict(original=ORIGINAL, control=summary['images']['control']['stripped'], candidate=summary['images']['candidate']['stripped'])
    need({c['file'] for c in runtime['focused']['cohorts']} == set(FOCUSED) and len(runtime['focused']['cohorts']) == 2, 'focused report set')
    rows = []
    for cohort in runtime['focused']['cohorts']:
        need(tuple(cohort[k] for k in ('cases', 'target_executions', 'bootstrap_executions', 'signature_fields')) == FOCUSED[cohort['file']], 'pinned focused counts')
        rows += focused(read(HERE / 'records' / cohort['file']), cohort, images)
    need(Counter(r['case']['group'] for r in rows) == dict(create=33, sweep=28, v3=44, sell=24), 'focused groups')
    need(len(rows) == runtime['focused']['cases'] == 129, 'combined focused census')
    need((runtime['focused']['target_executions'], runtime['focused']['bootstrap_executions'], runtime['focused']['signature_fields']) == (387, 102, 690), 'pinned focused totals')
    crossings = [r for r in rows if r['case']['name'] in CROSSINGS]
    need(len(crossings) == 6 and {r['case']['name'] for r in crossings} == CROSSINGS, 'crossing census')
    tags = {hashlib.sha256(('event:' + name).encode()).digest()[:8] for name in ('TradeEvent', 'CompleteEvent', 'PostCompleteBuyEvent')}
    for row in crossings:
        original = row['runs']['original']['target']
        event_tags = {base64.b64decode(line.removeprefix('Program data: '), validate=True)[:8] for line in original['events']}
        need(original['error'] is None and tags <= event_tags, 'successful crossing events')
    if args.binary:
        measured = actual_flags(args.binary)
        membership_gate(base, measured)
        need(measured == combined, 'actual per-window memberships')
        need(sha(args.binary.read_bytes()) == summary['images']['candidate']['symbols'], 'actual symbols ELF hash')
    if args.stripped:
        need(sha(args.stripped.read_bytes()) == summary['images']['candidate']['stripped'], 'actual stripped ELF hash')
    print(json.dumps(dict(verified=True, primary_inputs=70, compiled_inputs=71, windows=1035,
                          normalized=1027, raw=277, focused_cases=runtime['focused']['cases'],
                          focused_signatures_reverified=True, actual_elf_rescored=bool(args.binary),
                          broad_raw_public=False, broad_runtime_independently_rechecked=False)))


if __name__ == '__main__':
    main()
