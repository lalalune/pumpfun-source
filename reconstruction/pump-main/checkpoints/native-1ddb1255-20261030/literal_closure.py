#!/usr/bin/env python3
"""Literal byte closure for the frozen 1ddb1255 native control, not a scorer."""
import argparse
import collections
import csv
import hashlib
import importlib.util
import io
import json
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
SOURCE_BASE = '1ddb12553ccdb4ed45407ffe53f12f4644be172a'
ORIGINAL_SHA256 = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
CANDIDATE_SHA256 = 'b1cc01495e331a220d1c150c9be21810f172118e45bc45201fe223a8bf783703'
SYMBOLS_SHA256 = '481ba72865f36b52b3cc27e824ef3762a0baff5509c48135aa627fb927418c2b'
DEPENDENCIES = {
    'scripts/analyze.py': {'gitBlob': '411ea9a66206cdccd718b99c791f06c97f2a41e7',
        'sha256': '6218ab2fd3d5cc716a3ae7987fdd2398e56cebdc7d8d1ad1970fdf43d3199e06'},
    'reconstruction/base/functions.tsv': {'gitBlob': '774a1acb30f1cf4e017dd0ca8bf61fa33cf46880',
        'sha256': 'fb2c0a47514567d65eb45c1e268dacd5291e4659bb7dceb575a767dc20bcaff8'},
}
CTO = (0x22a10, 0x22a10 + 27400)
HEADER_FIELDS = ('type', 'machine', 'version', 'entry', 'phoff', 'shoff', 'flags',
                 'ehsize', 'phentsize', 'phnum', 'shentsize', 'shnum', 'shstrndx')
SECTION_FIELDS = ('name_index', 'type', 'flags', 'address', 'offset', 'size',
                  'link', 'info', 'alignment', 'entry_size')
PROGRAM_FIELDS = ('type', 'flags', 'offset', 'vaddr', 'paddr', 'filesz', 'memsz', 'alignment')


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def _parser(repo):
    for name, expected in DEPENDENCIES.items():
        require(sha((repo / name).read_bytes()) == expected['sha256'], 'dependency differs: ' + name)
    spec = importlib.util.spec_from_file_location('_native_1ddb_analyze', repo / 'scripts/analyze.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.elf_layout


def _image(data, layout):
    result = layout(data)
    result['header'] = dict(zip(HEADER_FIELDS, struct.unpack_from('<HHIQQQIHHHHHH', data, 16)))
    h = result['header']
    result['sectionHeaders'] = [dict(zip(SECTION_FIELDS, struct.unpack_from('<IIQQQQIIQQ', data,
        h['shoff'] + i * h['shentsize']))) for i in range(h['shnum'])]
    result['programHeaders'] = [dict(zip(PROGRAM_FIELDS, struct.unpack_from('<IIQQQQQQ', data,
        h['phoff'] + i * h['phentsize']))) for i in range(h['phnum'])]
    return result


def _section(image, name):
    matches = [s for s in image['sections'] if s['name'] == name]
    require(len(matches) == 1, 'expected one section: ' + name)
    return matches[0]


def _payload(data, image, name):
    s = _section(image, name)
    return data[s['offset']:s['offset'] + s['size']]


def _relocations(data, image):
    s = _section(image, '.rel.dyn')
    require(s['type'] == 9 and s['size'] % 16 == 0, 'expected ELF64 REL records')
    return [struct.unpack_from('<QQ', data, i) for i in range(s['offset'], s['offset'] + s['size'], 16)]


def _inside(row):
    return CTO[0] <= row[0] < CTO[1]


def _lddw_targets(data, image, rows):
    t = _section(image, '.text')
    values = []
    for address, info in rows:
        if info & 0xffffffff != 8 or not _inside((address, info)):
            continue
        offset = t['offset'] + address - t['address']
        require(data[offset] == 0x18 and data[offset + 8] == 0, 'type-8 CTO site is not LDDW')
        values.append(struct.unpack_from('<I', data, offset + 4)[0]
                      | struct.unpack_from('<I', data, offset + 12)[0] << 32)
    return collections.Counter(values)


def _changes(old, new):
    return {key: [old[key], new[key]] for key in old if old[key] != new[key]}


def _region(offset, image, original):
    h = image['header']
    if offset < h['ehsize']:
        return 'ELF header'
    if h['phoff'] <= offset < h['phoff'] + h['phentsize'] * h['phnum']:
        return 'program headers'
    if h['shoff'] <= offset < h['shoff'] + h['shentsize'] * h['shnum']:
        return 'section headers'
    for s in image['sections']:
        if s['type'] == 8 or not s['offset'] <= offset < s['offset'] + s['size']:
            continue
        if s['name'] == '.text' and original:
            address = s['address'] + offset - s['offset']
            return '.text CTO' if CTO[0] <= address < CTO[1] else '.text outside CTO'
        return s['name']
    return 'internal gap' if offset < image['elf_extent'] else 'beyond meaningful extent'


def _closure(original, candidate, inventory, layout):
    """Analyze supplied bytes; private test seam omits public fixed-file hash admission."""
    o, c = _image(original, layout), _image(candidate, layout)
    require(o['elf_extent'] == 1934800 and c['elf_extent'] == len(candidate) == 1934832,
            'frozen meaningful extents differ')
    require(len(original) == 10485715 and not any(original[o['elf_extent']:]), 'original allocation tail differs')
    ot, ct = _section(o, '.text'), _section(c, '.text')
    require(ot == ct and ot['offset'] == ot['address'] == 288 and ot['size'] == 1792208,
            'frozen .text geometry differs')
    windows = sorted((int(r['original_start']), int(r['original_end']))
        for r in csv.DictReader(io.StringIO(inventory.decode()), delimiter='\t')
        if r['program'] == 'pump' and r['variant'] == 'selected')
    cursor = ot['address']
    same = []
    for lo, hi in windows:
        require(lo == cursor and hi > lo, 'original windows do not exactly tile .text')
        cursor = hi
        same.append(original[lo:hi] == candidate[lo:hi])
    require(len(windows) == 1035 and cursor == 1792496, 'original window coverage differs')
    require([w for w, equal in zip(windows, same) if not equal] == [CTO],
            'a body outside CTO differs at its original file offset')
    payloads = {}
    for name in ['.rodata', '.data.rel.ro', '.dynsym', '.dynstr', '.shstrtab']:
        a, b = _payload(original, o, name), _payload(candidate, c, name)
        require(a == b, 'literal section payload differs: ' + name)
        payloads[name] = {'bytes': len(a), 'sha256': sha(a), 'literalEqual': True,
            'originalOffset': _section(o, name)['offset'], 'candidateOffset': _section(c, name)['offset']}
    require(original[:16] == candidate[:16], 'ELF identity differs')
    require(_changes(o['header'], c['header']) == {'shoff': [1934224, 1934256]}, 'unexpected ELF-header field change')
    require(len(o['programHeaders']) == len(c['programHeaders']) == 4, 'program-header count differs')
    ph = [_changes(a, b) for a, b in zip(o['programHeaders'], c['programHeaders'])]
    require(ph == [{}, {}, {'filesz': [99096, 99128], 'memsz': [99096, 99128]}, {}], 'unexpected program-header field change')
    require(len(o['sectionHeaders']) == len(c['sectionHeaders']) == 9, 'section-header count differs')
    sh = [_changes(a, b) for a, b in zip(o['sectionHeaders'], c['sectionHeaders'])]
    require(sh == [{}, {}, {}, {}, {}, {}, {}, {'size': [98352, 98384]}, {'offset': [1934152, 1934184]}],
            'unexpected section-header field change')
    dynamic = lambda b, m: list(struct.iter_unpack('<qQ', _payload(b, m, '.dynamic')))
    od, cd = dynamic(original, o), dynamic(candidate, c)
    require(len(od) == len(cd) == 11, 'dynamic-entry count differs')
    dynamic_changes = [[list(a), list(b)] for a, b in zip(od, cd) if a != b]
    require(dynamic_changes == [[[18, 98352], [18, 98384]], [[0x6ffffffa, 5877], [0x6ffffffa, 5879]]],
            'unexpected dynamic record change')
    ro, rc = _relocations(original, o), _relocations(candidate, c)
    outside_o, outside_c = [r for r in ro if not _inside(r)], [r for r in rc if not _inside(r)]
    require(len(ro) == 6147 and len(rc) == 6149 and len(outside_o) == len(outside_c) == 6060
            and outside_o == outside_c, 'outside-CTO relocation record sequence differs')
    removed = collections.Counter(ro) - collections.Counter(rc)
    added = collections.Counter(rc) - collections.Counter(ro)
    require(sum(removed.values()) == 74 and sum(added.values()) == 76
            and all(_inside(r) for r in list(removed) + list(added)), 'unexpected relocation delta')
    po, pc = _lddw_targets(original, o, ro), _lddw_targets(candidate, c, rc)
    target_delta = {str(v): [po[v], pc[v]] for v in po.keys() | pc.keys() if po[v] != pc[v]}
    require(sum(po.values()) == 84 and sum(pc.values()) == 86
            and target_delta == {'1824824': [9, 11]}, 'unexpected CTO LDDW target multiplicity')
    counts = collections.Counter()
    extent = max(o['elf_extent'], c['elf_extent'])
    for i in range(extent):
        if i >= o['elf_extent'] or i >= c['elf_extent'] or original[i] != candidate[i]:
            counts[(_region(i, o, True), _region(i, c, False))] += 1
    total = sum(counts.values())
    require(total == 23426, 'literal physical-offset difference count differs')
    return {'sourceBase': SOURCE_BASE, 'scope': 'Frozen 1ddb control only; no latest-main, mechanism, window gain or runtime claim',
        'original': {'fullBytes': len(original), 'meaningfulBytes': o['elf_extent'],
            'meaningfulSHA256': sha(original[:o['elf_extent']]), 'zeroAllocationTailBytes': 8550915},
        'candidateMeaningfulBytes': c['elf_extent'], 'wholeMeaningfulELFEqual': False,
        'allPhysicalPositionsCompared': extent, 'differingOrMissingPositions': total,
        'literalRegions': [{'original': a, 'candidate': b, 'positions': n} for (a, b), n in counts.items()],
        'windows': {'total': 1035, 'sameOriginalOffsets': sum(same), 'onlyUnequalRange': list(CTO),
            'nonCTOTextLiteralBytes': 1764808, 'CTODifferingBytes': sum(original[i] != candidate[i] for i in range(*CTO))},
        'equalSectionPayloads': payloads, 'elfHeaderChanges': {'shoff': [1934224, 1934256]},
        'programHeaderChanges': ph, 'sectionHeaderChanges': sh, 'dynamicRecordChanges': dynamic_changes,
        'relocations': {'original': 6147, 'candidate': 6149, 'CTOOriginal': 87, 'CTOCandidate': 89,
            'outsideCTORecords': 6060, 'outsideCTOSequenceLiteralEqual': True,
            'removedCTORecords': 74, 'addedCTORecords': 76,
            'CTOType8Original': 84, 'CTOType8Candidate': 86, 'onlyTargetMultiplicityChange': target_delta},
        'comparisonMasksOrBinaryWrites': False, 'compilerSdkOrScorerExecutions': 0}


def verify_literal(repo, candidate):
    repo, candidate = Path(repo), Path(candidate)
    layout = _parser(repo)
    original = (repo / 'evidence/original/pump/deployed.so').read_bytes()
    emitted = candidate.read_bytes()
    require(sha(original) == ORIGINAL_SHA256, 'captured original hash differs')
    require(sha(emitted) == CANDIDATE_SHA256, 'frozen candidate hash differs')
    report = _closure(original, emitted, (repo / 'reconstruction/base/functions.tsv').read_bytes(), layout)
    report.update(originalSHA256=sha(original), candidateSHA256=sha(emitted), dependencies=DEPENDENCIES)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--json', type=Path)
    a = p.parse_args()
    report = verify_literal(a.repo, a.candidate)
    rendered = json.dumps(report, indent=2) + '\n'
    if a.json:
        with a.json.open('x') as stream:
            stream.write(rendered)
    print(rendered, end='')


if __name__ == '__main__':
    main()
