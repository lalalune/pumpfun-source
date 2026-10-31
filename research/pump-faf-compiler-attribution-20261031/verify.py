"""Read-only replay of preserved frozen FAF compiler evidence; no SDK, network or compiler."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import io
import json
import re
import struct
import tarfile

BASE = 'faf99624250b4e60107790f7edabf6609f709885'
SOURCE = '29a8df2d7e12b379a9dc515d5a84eaaf051729da62350a54996a0077015f0c8a'
SYMBOL = b'_ZN14pump_recovered9admin_cto7execute17h3bd6d7f34f2e30d7E'
ARCHIVES = {'reference': ('ac71b05401e38551fcd30aca8a310773adad5eb3355a8f5d5faa940c4cababb0', 43),
            'diagnostic': ('6db5fdcda290350e6c46a9b1c0d41b0336f29817d5165866fbcfb30ce52675a5', 47)}
STAGES = [('After', 'finalize-isel'), ('Before', 'greedy'), ('After', 'greedy'),
          ('After', 'virtregrewriter'), ('After', 'block-placement')]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


class Packet:
    def __init__(self, path, manifest):
        require(file_sha(path) == manifest['archive']['sha256']
                and path.stat().st_size == manifest['archive']['bytes'], 'packet transport differs')
        self.manifest, self.data = manifest, {}
        with tarfile.open(path, 'r:xz') as archive:
            for item in archive:
                name = PurePosixPath(item.name)
                require(item.isfile() and not name.is_absolute() and '..' not in name.parts
                        and item.name not in self.data and item.name in manifest['members'],
                        'unsafe, duplicate or unregistered packet member')
                expected = manifest['members'][item.name]
                require(item.size == expected['bytes'], 'packet member size differs')
                blob = archive.extractfile(item).read()
                require(sha(blob) == expected['sha256'], 'packet member hash differs: ' + item.name)
                self.data[item.name] = blob
        require(set(self.data) == set(manifest['members']), 'packet member census differs')

    def read(self, name):
        return self.data[name]


class Artifact:
    def __init__(self, packet, kind):
        self.packet, self.prefix, self.reads = packet, kind + '/', set()
        require(packet.manifest['sourceArtifacts'][kind]['originalZipSha256'] == ARCHIVES[kind][0],
                kind + ' original transport binding differs')
        require(sum(name.startswith(self.prefix) for name in packet.data) == ARCHIVES[kind][1],
                kind + ' original artifact member census differs')

    def read(self, name):
        self.reads.add(name)
        return self.packet.read(self.prefix + name)

    def json(self, name):
        return json.loads(self.read(name))


def sections(raw):
    require(raw[:6] == b'\x7fELF\x02\x01', 'ELF must be 64-bit little-endian')
    header = struct.unpack_from('<16sHHIQQQIHHHHHH', raw)
    offset, width, count, strings_index = header[6], header[11], header[12], header[13]
    require(width == 64 and count > 0 and strings_index < count
            and offset + width * count <= len(raw), 'unsupported ELF section table')
    rows = [struct.unpack_from('<IIQQQQIIQQ', raw, offset + i * width) for i in range(count)]
    names_row = rows[strings_index]
    names = raw[names_row[4]:names_row[4] + names_row[5]]
    result = {}
    for row in rows:
        end = names.find(b'\0', row[0])
        require(end >= row[0], 'bad ELF section name')
        name = names[row[0]:end].decode('utf-8')
        require(name not in result and row[4] + row[5] <= len(raw), 'bad ELF section extent')
        result[name] = {'data': raw[row[4]:row[4] + row[5]], 'address': row[3]}
    return result


def symbols(ss):
    raw, strings = ss['.symtab']['data'], ss['.strtab']['data']
    require(len(raw) % 24 == 0, 'bad symbol table size')
    result = []
    for offset in range(0, len(raw), 24):
        name, info, other, section, value, size = struct.unpack_from('<IBBHQQ', raw, offset)
        end = strings.find(b'\0', name)
        require(end >= name, 'bad symbol name')
        result.append((strings[name:end], info, other, section, value, size))
    return result


def verify_tar(data, expected):
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        members = archive.getmembers()
        require(len(members) == len(expected) and {x.name for x in members} == set(expected),
                'archived source/workspace member set differs')
        for item in members:
            require(item.isfile(), 'nonregular archived compiler input')
            blob = archive.extractfile(item).read()
            row = expected[item.name]
            executable = row.get('executable', row.get('mode') == '100755')
            require(len(blob) == row['bytes'] and sha(blob) == row['sha256']
                    and bool(item.mode & 0o111) == executable, 'archived compiler input differs: ' + item.name)


def verify(reference, actual, manifest):
    for artifact, prefix, checkout, count in [
            (reference, 'reference-ops/', '50ebec8188201e8e8bf8f484f2b6b44e3387e121', 3),
            (actual, 'ops/', '39da3bb8c71dd83685c2c8584669ef0e67f8e6bf', 4)]:
        operational = artifact.json('operational-inputs.json')
        require(operational['checkout'] == checkout and len(operational['files']) == count,
                'frozen operational binding differs')
        for row in operational['files']:
            raw = artifact.packet.read(prefix + row['path'])
            blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            require(sha(raw) == row['sha256'] and len(raw) == row['bytes']
                    and blob == row['gitBlob'], 'operational input differs')
    # Authenticate retained source vectors and real maintained staging; no Git hydration.
    vectors = ['program-source-inputs.json', 'toolchain-source-inputs.json',
               'source-inputs.json', 'compiled-workspace-inputs.json']
    for name in vectors:
        require(actual.json(name) == reference.json(name), 'reference vector differs: ' + name)
    source = actual.json('source-inputs.json')
    encoded = json.dumps(source['files'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    program = actual.json('program-source-inputs.json')
    core = actual.json('toolchain-source-inputs.json')
    stage = actual.json('compiled-workspace-inputs.json')
    require(source['sha256'] == sha(encoded) == SOURCE and len(source['files']) == 141,
            'selected source seal differs')
    require(program['base'] == core['base'] == BASE and len(program['files']) == 141
            and len(core['files']) == 236 and len(stage) == 142, 'frozen input census differs')
    verify_tar(actual.read('program-source.tar.gz'), {x['path']: x for x in program['files']})
    verify_tar(actual.read('compiled-workspace.tar.gz'), stage)

    stripped = actual.read('candidate.so')
    require(stripped == reference.read('candidate.so'), 'complete stripped ELF differs')
    candidate, baseline = actual.read('unstripped.so'), reference.read('unstripped.so')
    require(candidate != baseline, 'strict native unstripped failure unexpectedly changed')
    cs, bs = sections(candidate), sections(baseline)
    require(set(cs) == set(bs), 'section census differs')
    differing = [name for name in cs if cs[name]['data'] != bs[name]['data']]
    require(set(differing) == {'.symtab', '.strtab'}, 'executable/data section payload differs')
    xs, ys = symbols(cs), symbols(bs)
    require(len(xs) == len(ys), 'symbol census differs')
    require(sum(x != y for x, y in zip(xs, ys)) == 696
            and all(x[1:] == y[1:] for x, y in zip(xs, ys)),
            'unstripped symbol differences are not exactly696 names')
    target = [x for x in xs if x[0] == SYMBOL and x[1] & 15 == 2]
    require(len(target) == 1 and target == [x for x in ys if x[0] == SYMBOL and x[1] & 15 == 2]
            and target[0][-2:] == (0x22a10, 27400), 'CTO symbol extent differs')

    saved, saved_ref = actual.json('score.json'), reference.json('score.json')
    require(saved['windows'] == saved_ref['windows'] and len(saved['windows']) == 1035,
            'complete official score rows differ')
    summary, ref_summary = saved['summary'], saved_ref['summary']
    difference = {key for key in summary.keys() | ref_summary.keys() if summary.get(key) != ref_summary.get(key)}
    require(difference == {'candidate_sha256'} and summary['candidate_sha256'] == sha(candidate)
            and ref_summary['candidate_sha256'] == sha(baseline), 'score summary failure reason differs')
    require(summary['total'] == 1035 and summary['raw'] == summary['normalized'] == 1034,
            'saved official score census differs')

    # Keep the strict native failure and original parser miss intact.
    native, capture = actual.json('DIAGNOSTIC-COMPARISON.json'), actual.json('capture-result.json')
    require(native['attributionQualified'] is False and capture['captureComplete'] is False
            and native['fullElfHashesEqual'] == {'stripped': True, 'unstripped': False}
            and capture['machineDumps'] == [] and capture['allRequestedStagesObserved'] is False,
            'original failed receipts were changed')
    require(capture['buildOk'] and capture['compilerCompleted'] and capture['sourceUnchanged']
            and len(capture['calls']) == 1, 'actual compiler/source admission differs')
    require(actual.json('FAILURE.json')['message'] ==
            'diagnostic output/capture differs; baseline attribution is not qualified',
            'original final failure record differs')
    raw = actual.read('build.log')
    require(sha(raw) == capture['rawBuildLogSha256'], 'raw compiler log differs')
    require(not re.search(rb'(?m)^\*\*\* IR Dump ', raw), 'original parser miss is not reproduced')
    headings = list(re.finditer(rb'(?m)^# \*\*\* IR Dump (Before|After) [^\r\n]+', raw))
    require(len(headings) == len(STAGES), 'actual LLVM stage census differs')
    metadata = manifest.get('machineFunctions')
    require(isinstance(metadata, list) and len(metadata) == len(STAGES),
            'complete five-stage metadata required')
    derived, dump_rows = {}, []
    for index, (heading, (timing, stage), expected) in enumerate(zip(headings, STAGES, metadata)):
        filename = f'{index + 1:02d}-{timing.lower()}-{stage}.txt'
        require(isinstance(expected, dict)
                and (expected.get('timing'), expected.get('pass'), expected.get('file')) ==
                (timing, stage, filename), 'stage metadata timing/pass/file differs')
        end = headings[index + 1].start() if index + 1 < len(headings) else len(raw)
        blob = raw[heading.start():end]
        require(('IR Dump ' + timing + ' ').encode() in heading.group()
                and ('(' + stage + ')').encode() in heading.group(), 'actual stage heading differs')
        require(blob.count(b'# Machine code for function ' + SYMBOL + b':') == 1
                and blob.count(b'# End machine code for function ' + SYMBOL + b'.') == 1,
                'incomplete target machine function')
        require((heading.start(), end, len(blob), sha(blob)) ==
                (expected['rawLogStart'], expected['rawLogEnd'], expected['bytes'], expected['sha256']),
                'exact stage slice differs')
        require(blob == actual.packet.read('derived/' + expected['file']),
                'retained offline dump is not the exact original log slice')
        derived[expected['file']] = blob
        dump_rows.append({'timing': timing, 'pass': stage, 'bytes': len(blob), 'sha256': sha(blob)})
    require(len(capture['llvmIr']) == 1, 'expected exactly one raw LLVM module')
    module = actual.read(capture['llvmIr'][0]['file'])
    require(sha(module) == capture['llvmIr'][0]['sha256'] == manifest['optimizedTarget']['rawModuleSha256'],
            'raw LLVM module differs')
    start = re.search(rb'(?m)^define[^\n]*@' + re.escape(SYMBOL) + rb'\(', module)
    require(start is not None, 'target definition missing')
    closing = re.search(rb'(?m)^\}', module[start.start():])
    require(closing is not None, 'target definition incomplete')
    end = start.start() + closing.end()
    target_ir = module[start.start():end]
    expected = manifest['optimizedTarget']
    require((start.start(), end, len(target_ir), sha(target_ir)) ==
            (expected['rawModuleStart'], expected['rawModuleEnd'], expected['bytes'], expected['sha256']),
            'optimized target slice differs')
    require(target_ir == actual.packet.read('derived/admin-cto.ll'),
            'retained optimized target is not the exact full module slice')
    derived['admin-cto.ll'] = target_ir
    witnesses = manifest['witnesses']
    require(isinstance(witnesses, list) and len(witnesses) == 50,
            'complete fifty-witness metadata required')
    for witness in witnesses:
        lines = derived[witness['file']].decode('utf-8').splitlines()
        line = witness['line']
        require(type(line) is int and 1 <= line <= len(lines), 'compiler witness line out of bounds')
        require(lines[line - 1] == witness['text'], 'compiler witness differs: ' + witness['claim'])
    return {'scope': 'Frozen FAF artifact evidence only; original strict native FAILURE preserved.',
        'sourceBase': BASE, 'sourceFiles': 141, 'coreFiles': 236, 'stagedFiles': 142,
        'sourceSha256': SOURCE, 'completeStrippedElfEqual': True, 'strippedSha256': sha(stripped),
        'completeUnstrippedElfEqual': False, 'actualUnstrippedSha256': sha(candidate),
        'differingSectionPayloads': sorted(differing),
        'symbolSemanticDifferences': 696, 'symbolDifferencesOnlyNames': True,
        'all1035SavedOfficialRowsEqual': True, 'summaryDifferenceKeys': sorted(difference),
        'offlineCompleteMachineStages': dump_rows, 'optimizedTargetSha256': sha(target_ir),
        'exactLineWitnessesVerified': len(manifest['witnesses']),
        'workerEvidenceScope': 'Exact retained worker bytes authenticated;50 selected event/sweep compiler-line joins replayed. Remaining worker analyses are prior evidence, not freshly reexecuted.',
        'selectedMembersRead': {'reference': sorted(reference.reads), 'diagnostic': sorted(actual.reads)},
        'compilerOrSdkOrRuntimeExecuted': False, 'scorerExecuted': False,
        'limits': 'No full unstripped identity, independent score recomputation, original LLVM lifetime recovery, allocation optimality, source gain or later-main claim.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, default=Path(__file__).with_name('evidence.tar.xz'))
    args = parser.parse_args()
    manifest = json.loads(Path(__file__).with_name('manifest.json').read_text())
    require(manifest['schema'] == 'frozen-faf-compiler-evidence-v1'
            and manifest['sourceBase'] == BASE and manifest['preservedNativeOutcome'] == 'failure',
            'wrong frozen packet schema/source/outcome')
    packet = Packet(args.artifact, manifest)
    result = verify(Artifact(packet, 'reference'), Artifact(packet, 'diagnostic'), manifest)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
