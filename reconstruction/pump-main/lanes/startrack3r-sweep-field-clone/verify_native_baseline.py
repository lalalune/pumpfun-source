#!/usr/bin/env python3
"""Compare a pinned native score receipt with actual local compiler images.

This does not qualify a native compiler build. The native ELF and full compiler
argv are absent from the cited packet; its scores remain attributed receipts.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tomllib

NATIVE_REV = '7701aaa881adc480447de456ef67d8a64dbd0048'
NATIVE_LANE = 'reconstruction/pump-main/lanes/v3-buy-crossing-layout/'
BASE = '094a06f18df738d41e77070c1a009e135671ac1a'
ORIGINAL = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
INVENTORY = 'fb2c0a47514567d65eb45c1e268dacd5291e4659bb7dceb575a767dc20bcaff8'
SCORER = '99475a567c96c2b8d609857fe96d1ed42058c795f19ac2374968c2905ee1fb3a'
CONTROL = '1c0c18a87121998ee33b66597354dc36923c97deaf258e2acd02a3d5e87315f0'
CANDIDATE = 'c74e553e1af2c3c7823d55dd5f5b57875c07f82b282fa725a2d967029ed027da'


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['repo', 'control-source', 'control', 'candidate', 'original', 'inventory', 'harness', 'work']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--objdump', required=True)
    args = parser.parse_args()

    def git(*arguments):
        return subprocess.check_output(['git', '-C', str(args.repo), *arguments])

    names = ['SUMMARY.json', 'control-source.tar.gz', 'source-inputs.json',
             'control-score.json.gz', 'raw-loss.json', 'control-build.log.gz']
    manifest = json.loads(git('show', NATIVE_REV + ':' + NATIVE_LANE + 'manifest.json'))
    native = {}
    receipts = {}
    for name in names:
        raw = git('show', NATIVE_REV + ':' + NATIVE_LANE + name)
        require(sha(raw) == manifest[name], 'Native manifest mismatch: ' + name)
        native[name] = raw
        receipts[name] = {'sha256': sha(raw), 'bytes': len(raw),
                          'git_blob': git('rev-parse', NATIVE_REV + ':' + NATIVE_LANE + name).decode().strip()}
    summary = json.loads(native['SUMMARY.json'])
    require(summary['base_commit'] == BASE and summary['scorer_sha256'] == SCORER, 'Native base/scorer mismatch')
    native_inputs = json.loads(native['source-inputs.json'])['control']
    archive = {}
    with tarfile.open(fileobj=io.BytesIO(native['control-source.tar.gz'])) as tf:
        for member in tf:
            require(member.isfile(), 'Unexpected non-file archive member')
            path = PurePosixPath(member.name)
            require(not path.is_absolute() and '..' not in path.parts and path.as_posix() not in archive,
                    'Unsafe or duplicate archive path')
            archive[path.as_posix()] = tf.extractfile(member).read()
    require({p: sha(b) for p, b in archive.items()} == native_inputs, 'Native archive differs from source inventory')
    local_inputs = {p.relative_to(args.control_source).as_posix(): sha(p.read_bytes())
                    for p in sorted(args.control_source.rglob('*')) if p.is_file()}
    require(len(local_inputs) == len(native_inputs) == 71, 'Incomplete source snapshot')
    common = sorted(set(local_inputs) & set(native_inputs))
    same = [p for p in common if local_inputs[p] == native_inputs[p]]
    different = [p for p in common if local_inputs[p] != native_inputs[p]]
    require(len(same) == 68 and different == ['programs/pump/Cargo.toml'], 'Unexpected source difference')
    rust = [p for p in native_inputs if p.endswith('.rs')]
    require(len(rust) == 64 and all(p in same for p in rust), 'Rust sources differ')
    np = tomllib.loads(archive['programs/pump/Cargo.toml'].decode())
    lp = tomllib.loads((args.control_source / 'programs/pump/Cargo.toml').read_text())
    lr = tomllib.loads((args.control_source / 'Cargo.toml').read_text())
    require({k: v for k, v in np.items() if k not in ['workspace', 'profile']} == lp,
            'Package configuration differs beyond workspace/profile placement')
    require(np['profile'] == lr['profile'], 'Release profiles differ')
    require(archive['programs/pump/Cargo.lock'] == (args.control_source / 'Cargo.lock').read_bytes(), 'Lockfile differs')

    original, inventory = args.original.read_bytes(), args.inventory.read_bytes()
    require(sha(original) == ORIGINAL and sha(inventory) == INVENTORY, 'Original inputs differ')
    require(sha((args.harness / 'score.py').read_bytes()) == SCORER, 'Scorer differs')
    require(sha(args.control.read_bytes()) == CONTROL and sha(args.candidate.read_bytes()) == CANDIDATE,
            'Unexpected local compiler image')
    args.work.mkdir(parents=True, exist_ok=False)
    base = args.work / 'base'; base.mkdir()
    (base / 'original.so').write_bytes(original)
    (base / 'functions.tsv').write_bytes(inventory)
    sys.path.insert(0, str(args.harness))
    import score
    score.BASE = base
    score.OBJDUMP = args.objdump
    windows = score.original_windows()
    universe = {w['start'] for w in windows}
    widths = {w['start']: w['bytes'] for w in windows}
    native_score = json.loads(gzip.decompress(native['control-score.json.gz']))
    ns = {int(k): v for k, v in native_score['windows'].items()}
    cs = score.score(args.control)
    ps = score.score(args.candidate)
    require(len(universe) == 1035 and set(ns) == set(cs) == set(ps) == universe, 'Incomplete membership inventory')
    for address, value in ns.items():
        require(type(value['normalized']) is bool and type(value['raw']) is bool, 'Invalid native membership')
        require(value['bytes'] == widths[address], 'Native receipt window width differs')
    comparisons = {}
    for label, measured in [('local_control', cs), ('local_composition', ps)]:
        comparisons[label] = {}
        for field in ['normalized', 'raw']:
            native_set = {a for a, v in ns.items() if v[field]}
            local_set = {a for a, v in measured.items() if v[field]}
            require(len(native_set) == summary['scores']['control'][field], 'Native count receipt mismatch')
            comparisons[label][field] = {'native': len(native_set), 'local': len(local_set),
                'common': len(native_set & local_set),
                'native_only': [hex(a) for a in sorted(native_set - local_set)],
                'local_only': [hex(a) for a in sorted(local_set - native_set)]}
    discrepancies = {hex(a): {'bytes': ns[a]['bytes'], 'native_symbols': ns[a]['symbols'],
                              'local_control_symbols': cs[a]['symbols'], 'local_composition_symbols': ps[a]['symbols']}
                     for a in sorted(universe) if len({ns[a]['raw'], cs[a]['raw'], ps[a]['raw']}) > 1}
    report = {'result': 'PASS', 'native_receipt_revision': NATIVE_REV, 'base_revision': BASE,
        'native_elf_replayed': False, 'native_full_argv_available': False,
        'native_image_receipt': summary['images']['control'],
        'local_images_replayed': {'control': CONTROL, 'composition': CANDIDATE},
        'source': {'native_files': 71, 'local_files': 71, 'same_paths_and_bytes': same,
                   'all_rust_files_equal': rust, 'different_common_paths': different,
                   'native_only': sorted(set(native_inputs) - set(local_inputs)),
                   'local_only': sorted(set(local_inputs) - set(native_inputs)),
                   'package_fields_equal': True, 'release_profiles_equal': True,
                   'lockfile_bytes_equal': True,
                   'native_workspace': np['workspace'], 'local_workspace': lr['workspace']},
        'comparison': comparisons, 'raw_discrepancies': discrepancies, 'native_inputs': receipts,
        'scope': 'Native scores and image hashes are attributed to PR1669, not independently replayed native evidence. Local compiler images are freshly rescored across all 1035 windows. Source equality does not isolate host, dependencies, Cargo identity, flags or toolchain. Local composition gains do not qualify native no-loss or whole-image identity.'}
    (args.work / 'verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'result': 'PASS', 'comparison': comparisons, 'equal_rust_sources': len(rust),
                      'native_elf_replayed': False}, indent=2))


if __name__ == '__main__':
    main()
