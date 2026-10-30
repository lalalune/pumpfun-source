#!/usr/bin/env python3
"""Offline raw-packet/source/capture verifier. Never invokes compiler or SDK tools."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from replay import PACKAGE, check_assets, check_source, command, load, require, tar_members, write_new


def logical_signature(argv):
    result = list(argv)
    roots = {'/source', '/config', '/sdk', '/cargo/registry', '/etc/alternatives', '/target', '/output'}
    seen = []
    for i, arg in enumerate(argv[:-2]):
        if arg in ['--ro-bind', '--bind'] and argv[i + 2] in roots:
            seen.append(argv[i + 2]); result[i + 1] = '<physical:' + argv[i + 2] + '>'
    require(set(seen) == roots and len(seen) == 7, 'expected exactly seven physical mount substitutions')
    return result


def verify(repo, candidate=None, symbols=None):
    repo = Path(repo).resolve(); check_assets(); check_source(repo / 'programs/donation-relay', modes=False)
    recipe = load('recipe.json')
    first = tar_members(PACKAGE / 'measurements/attempt1.tar.gz')
    second = tar_members(PACKAGE / 'measurements/attempt2.tar.gz')
    prep = tar_members(PACKAGE / 'measurements/preparation.tar.gz')
    manifest = json.loads(second['FINAL-MANIFEST.json'])
    require(hashlib.sha256(second['FINAL-MANIFEST.json']).hexdigest()
            == '1a70c1d6a7eeff58449760bc0ef9a8e8cd5cf92ec7fc0e6eac40be0b66ee3991', 'original final seal changed')
    for row in manifest['files']:
        data = second[row['path']]
        require(len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'],
                'raw measured member mismatch: ' + row['path'])
    result = json.loads(second['RESULT.json'])
    require(hashlib.sha256(second['RESULT.json']).hexdigest()
            == '255dd05ff71030f609c67e77fdda034fefae98611a1232c9db962fd3c5dfefd4', 'actual result changed')
    require(result['acceptedColdReproduction'] and result['bothExpectedRawHashesEqual']
            and result['inputsUnchangedAfterBuild'] and result['inputsUnchangedAfterStrip'], 'actual qualification fields disagree')
    require(second['INPUTS-BEFORE.json'] == second['INPUTS-AFTER-BUILD.json']
            == second['INPUTS-AFTER-STRIP.json'], 'actual input profile changed')
    source = {r['path']: r['sha256'] for r in load('source-inputs.json')['files']}
    require(json.loads(second['INPUTS-BEFORE.json'])['sourceHashes'] == source, 'current source differs from cold source')
    for phase in ['build', 'strip']:
        require(result[phase]['returncode'] == 0 and result[phase]['guardFired'] is None
                and result[phase]['lowestFreeBytes'] >= recipe['floorBytes']
                and not result[phase]['ownedProcessGroupRemainedAfterLeaderExit'], 'actual guard/process failure')
    require(result['rootCompilerInvocations'] == result['errorModelCompilerInvocations'] == 1,
            'both local crates were not freshly compiled once')
    original_launch = json.loads(second['LAUNCH.json'])
    generated = command(Path('/path with spaces/replay'), Path('/path with spaces/sdk'), Path('/path with spaces/registry'))
    require(logical_signature(original_launch['command']) == logical_signature(generated),
            'public launcher differs beyond seven physical roots')
    measured_strip = json.loads(second['strip-PROCESS.json'])['argv']
    require(logical_signature(measured_strip)
            == logical_signature(command('/path with spaces/replay', '/path with spaces/sdk',
                                         '/path with spaces/registry', recipe['stripArgv'])),
            'public strip command differs beyond physical roots')
    require(not original_launch['capturedOrExpectedElfsMounted'], 'unexpected captured ELF input')
    fail = json.loads(first['RESULT.json'])
    require(fail['build']['returncode'] == 101 and not fail['acceptedColdReproduction']
            and b'the self-contained linker was requested' in first['build.log'], 'first failure not preserved')
    require(not any(n.endswith('candidate.so') for n in first), 'unexpected first-attempt candidate')
    correction = json.loads(prep['preparation/SDK-HOST-LINKER-CORRECTION.json'])
    require(correction['regularFiles'] == 971 and correction['originalAliases'] == 7,
            'corrected SDK inventory mismatch')
    added = {r['path'] for r in correction['added']}
    prefix = 'rust/lib/rustlib/x86_64-unknown-linux-gnu/bin/gcc-ld'
    require(added == {prefix, prefix + '/ld.lld'}, 'correction exceeds the original missing member/parent')
    require(load('registry-inputs.json')['regularMembers'] == 7968, 'registry member count mismatch')
    cold_candidate, cold_symbols = second['output/candidate.so'], second['output/symbols.so']
    for name, data in [('candidate.so', cold_candidate), ('symbols.so', cold_symbols)]:
        expected = recipe['expectedOutputs'][name]
        require(len(data) == expected['bytes'] and hashlib.sha256(data).hexdigest() == expected['sha256'], 'measured ELF hash mismatch')
    require((candidate is None) == (symbols is None), 'supply both candidate and symbols or neither')
    data = cold_candidate if candidate is None else Path(candidate).read_bytes()
    sym = cold_symbols if symbols is None else Path(symbols).read_bytes()
    require(hashlib.sha256(data).hexdigest() == recipe['expectedOutputs']['candidate.so']['sha256']
            and hashlib.sha256(sym).hexdigest() == recipe['expectedOutputs']['symbols.so']['sha256'], 'supplied ELF differs from canonical bytes')
    capture = (repo / recipe['capture']['repoPath']).read_bytes()
    require(len(capture) == recipe['capture']['bytes']
            and hashlib.sha256(capture).hexdigest() == recipe['capture']['sha256'], 'captured input mismatch')
    spec = importlib.util.spec_from_file_location('_relay_official_analyze', repo / 'scripts/analyze.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    extent = module.elf_layout(capture)['elf_extent']
    require(extent == 818280 and len(data) == extent and data == capture[:extent], 'meaningful ELF bytes differ')
    require(len(capture) - extent == 12168 and not any(capture[extent:]), 'allocation-tail attribution changed')
    return {'status': 'OFFLINE_SOURCE_PACKET_AND_LITERAL_CAPTURE_CHECK_PASS', 'sourceFiles': 60,
            'rawMeasuredMembers': len(manifest['files']), 'exactPhysicalSubstitutions': 7,
            'candidateSHA256': hashlib.sha256(data).hexdigest(), 'symbolsSHA256': hashlib.sha256(sym).hexdigest(),
            'meaningfulBytesLiteralEqual': 818280, 'zeroAllocationSuffixBytes': 12168,
            'wholeCapturedAllocationEqualsCompilerFile': False, 'compilerOrSdkExecutions': 0,
            'newPublicLauncherColdBuildTested': False,
            'suppliedArtifactByteCheckOnly': candidate is not None}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--candidate', type=Path)
    p.add_argument('--symbols', type=Path)
    p.add_argument('--output', type=Path)
    a = p.parse_args(); result = verify(a.repo, a.candidate, a.symbols)
    if a.output: write_new(a.output, result)
    print(json.dumps(result, indent=2))
