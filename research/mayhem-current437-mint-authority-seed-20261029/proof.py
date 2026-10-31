"""Count the Mayhem `mint-authority` seed string and its 16-byte descriptor.

The merged qualified437 data ledger has not credited this seed. It sits directly
after the uncredited `mint_authority` literal and before binary bytes in the
original image. This packet reads only static bytes: one 14-byte `.rodata`
literal and one 16-byte `.data.rel.ro` descriptor. NUL bytes, following bytes,
adjacent strings and relocation-table bytes are not bounds.
"""
from pathlib import Path
import gzip
import hashlib
import io
import json
import os
import struct
import sys
import tarfile
import tempfile

if not __debug__:
    raise RuntimeError('Assertions are required')

P = Path(__file__).resolve().parent
REPO = next(
    parent for parent in P.parents
    if (parent / 'evidence/original/mayhem/deployed.so').is_file()
)
ORIGINAL = 'evidence/original/mayhem/deployed.so'
CANDIDATE = 'research/mayhem-current437-composition-20261028/builds/first/candidate.so.gz'
ARCHIVE = 'research/mayhem-current437-composition-20261028/source.tar.gz'
BASELINE = 'baseline/sources.json'
sha = lambda data: hashlib.sha256(data).hexdigest()

STRING = dict(original=712415, candidate=690969, length=14, text=b'mint-authority')
DESCRIPTOR = dict(original=727632, candidate=707920, length=14)

sys.path.insert(0, str(REPO / 'scripts'))
from window_elf_reader import Elf  # noqa: E402


def union(intervals):
    out = []
    for start, end in sorted(map(tuple, intervals)):
        assert 0 <= start < end
        if out and start <= out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return out


def measure(intervals):
    return sum(end - start for start, end in intervals)


def section(image, name, address, size):
    item = image.secs[name]
    assert item[1] != 8
    assert item[3] <= address and address + size <= item[3] + item[5]
    return item


def read(image, name, address, size):
    item = section(image, name, address, size)
    start = item[4] + address - item[3]
    return image.b[start:start + size]


def relocation(image, address):
    item = image.secs.get('.rel.dyn')
    assert item is not None
    for position in range(item[4], item[4] + item[5], 16):
        at, info = struct.unpack_from('<QQ', image.b, position)
        if at == address:
            return dict(type=info & 0xffffffff, symbol_index=info >> 32)
    return None


def descriptor(image, address, expected_pointer):
    raw = read(image, '.data.rel.ro', address, 16)
    low, high, length = struct.unpack('<IIQ', raw)
    assert low == 0, 'descriptor low word is not zero'
    assert high == expected_pointer, (high, expected_pointer)
    assert length == DESCRIPTOR['length'], length
    assert relocation(image, address) == dict(type=8, symbol_index=0)
    assert relocation(image, address + 8) is None, 'length half must be raw'
    return dict(
        offset=address,
        raw_hex=raw.hex(),
        low_word=low,
        pointer=high,
        length=length,
        relocation=relocation(image, address),
    )


def elf_from_gzip(path):
    temporary = tempfile.NamedTemporaryFile(delete=False, suffix='.so')
    try:
        temporary.write(gzip.decompress(path.read_bytes()))
        temporary.close()
        return Elf(Path(temporary.name))
    finally:
        try:
            os.unlink(temporary.name)
        except FileNotFoundError:
            pass


def source_context():
    provenance = json.loads((P / 'source-context/provenance.json').read_bytes())
    archive = (REPO / ARCHIVE).read_bytes()
    assert sha(archive) == provenance['source_archive_sha256']
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as handle:
        member = handle.extractfile(provenance['member'])
        assert member is not None
        text = member.read().decode()
    assert provenance['line_text'] in text
    excerpt = (P / 'source-context/mint-authority.rs').read_bytes()
    assert sha(excerpt) == provenance['excerpt_sha256']
    assert provenance['seed'] == STRING['text'].decode()
    return provenance


def verify_images(original, candidate):
    for image, pointer, descriptor_offset in (
        (original, STRING['original'], DESCRIPTOR['original']),
        (candidate, STRING['candidate'], DESCRIPTOR['candidate']),
    ):
        assert read(image, '.rodata', pointer, STRING['length']) == STRING['text']
        row = descriptor(image, descriptor_offset, pointer)
        assert row['pointer'] == pointer
    original_string = read(original, '.rodata', STRING['original'], STRING['length'])
    candidate_string = read(candidate, '.rodata', STRING['candidate'], STRING['length'])
    assert original_string == candidate_string == STRING['text']
    original_descriptor = descriptor(original, DESCRIPTOR['original'], STRING['original'])
    candidate_descriptor = descriptor(candidate, DESCRIPTOR['candidate'], STRING['candidate'])
    return dict(
        summary=dict(
            string_bytes=STRING['length'],
            descriptor_bytes=16,
            descriptor_raw_bytes=8,
            descriptor_mapped_bytes=8,
            new_payload_bytes=STRING['length'] + 16,
        ),
        string=dict(
            original_ptr=STRING['original'],
            candidate_ptr=STRING['candidate'],
            length=STRING['length'],
            text=STRING['text'].decode(),
            original_hex=original_string.hex(),
            candidate_hex=candidate_string.hex(),
        ),
        descriptor=dict(
            original=original_descriptor,
            candidate=candidate_descriptor,
        ),
    )


def inspect():
    original = Elf(REPO / ORIGINAL)
    candidate = elf_from_gzip(REPO / CANDIDATE)
    return dict(verify_images(original, candidate), source_context=source_context())


def baseline_union(packet=P):
    sources = json.loads((packet / BASELINE).read_bytes())
    assert sources['baseline_commit'] == '907d3980'
    assert sources['payload_covered_bytes'] == 23834
    assert sources['payload_total_bytes'] == 26180
    sections = {}
    for section_name, total, expected_covered in (
        ('.rodata', 18396, 16722),
        ('.data.rel.ro', 7784, 7112),
    ):
        raw = []
        mapped = []
        covered = []
        for path, digest in sources['deltas'].items():
            data = (REPO / path).read_bytes()
            assert sha(data) == digest, path
            delta = json.loads(data)
            item = next(row for row in delta['sections'] if row['section'] == section_name)
            raw.extend(item['raw_intervals'])
            mapped.extend(item['mapped_intervals'])
            covered.extend(item['covered_intervals'])
        raw = union(raw)
        mapped = union(mapped)
        covered = union(covered)
        assert union(raw + mapped) == covered, section_name
        assert measure(covered) == expected_covered, section_name
        assert all(0 <= start < end for start, end in covered)
        sections[section_name] = dict(
            section=section_name,
            total_bytes=total,
            raw_intervals=raw,
            mapped_intervals=mapped,
            covered_intervals=covered,
            raw_equal_bytes=measure(raw),
            pointer_only_bytes=measure(covered) - measure(raw),
            covered_bytes=measure(covered),
        )
    assert sum(item['covered_bytes'] for item in sections.values()) == 23834
    return sections


def coverage(report, packet=P):
    sections = []
    for name, old in baseline_union(packet).items():
        raw = list(old['raw_intervals'])
        mapped = list(old['mapped_intervals'])
        if name == '.rodata':
            raw.append([STRING['original'], STRING['original'] + STRING['length']])
        elif name == '.data.rel.ro':
            raw.append([DESCRIPTOR['original'] + 8, DESCRIPTOR['original'] + 16])
            mapped.append([DESCRIPTOR['original'], DESCRIPTOR['original'] + 8])
        else:
            raise AssertionError(name)
        raw = union(raw)
        mapped = union(mapped)
        covered = union(raw + mapped)
        sections.append(dict(
            section=name,
            total_bytes=old['total_bytes'],
            raw_intervals=raw,
            mapped_intervals=mapped,
            covered_intervals=covered,
            raw_equal_bytes=measure(raw),
            pointer_only_bytes=measure(covered) - measure(raw),
            covered_bytes=measure(covered),
            new_bytes=measure(covered) - old['covered_bytes'],
        ))
    by_name = {item['section']: item for item in sections}
    assert by_name['.rodata']['new_bytes'] == 14
    assert by_name['.data.rel.ro']['new_bytes'] == 16
    total = sum(item['covered_bytes'] for item in sections)
    assert total == 23864
    return dict(
        scope='One observed mint-authority seed string and its 16-byte descriptor; no code site, allocation extent or relocation-table byte is claimed.',
        baseline_commit=json.loads((packet / BASELINE).read_bytes())['baseline_commit'],
        baseline_deltas=json.loads((packet / BASELINE).read_bytes())['deltas'],
        baseline_payload_bytes=23834,
        baseline_rodata_bytes=16722,
        baseline_data_rel_ro_bytes=7112,
        sections=sections,
        new_payload_bytes=sum(item['new_bytes'] for item in sections),
        new_rodata_bytes=by_name['.rodata']['new_bytes'],
        new_data_rel_ro_bytes=by_name['.data.rel.ro']['new_bytes'],
        payload_covered_bytes=total,
        payload_total_bytes=26180,
    )


def check(packet=P, root=REPO):
    paths = list(packet.rglob('*'))
    assert not any(path.is_symlink() for path in paths), 'packet symlink'
    assert all(path.is_file() or path.is_dir() for path in paths), 'packet special file'
    found = {
        str(path.relative_to(packet)): sha(path.read_bytes())
        for path in paths
        if path.is_file()
        and path.name != 'manifest.json'
        and '__pycache__' not in path.parts
        and path.suffix != '.pyc'
    }
    assert found == json.loads((packet / 'manifest.json').read_bytes()), 'packet inventory differs'
    pins = json.loads((packet / 'inputs.json').read_bytes())
    for path, digest in pins.items():
        relative = Path(path)
        assert not relative.is_absolute() and '..' not in relative.parts
        assert sha((root / relative).read_bytes()) == digest, path
    report = inspect()
    assert report == json.loads(gzip.decompress((packet / 'observations.json.gz').read_bytes())), 'fresh observations differ'
    delta = coverage(report, packet)
    assert delta == json.loads((packet / 'coverage-delta.json').read_bytes()), 'coverage delta differs'
    summary = report['summary']
    assert (
        summary['string_bytes'], summary['descriptor_bytes'],
        summary['descriptor_raw_bytes'], summary['descriptor_mapped_bytes'],
        summary['new_payload_bytes'],
    ) == (14, 16, 8, 8, 30)
    assert (
        delta['baseline_payload_bytes'], delta['new_payload_bytes'],
        delta['payload_covered_bytes'], delta['payload_total_bytes'],
    ) == (23834, 30, 23864, 26180)
    by_name = {item['section']: item for item in delta['sections']}
    assert (
        by_name['.rodata']['new_bytes'],
        by_name['.rodata']['covered_bytes'],
        by_name['.rodata']['total_bytes'],
    ) == (14, 16736, 18396)
    assert (
        by_name['.data.rel.ro']['new_bytes'],
        by_name['.data.rel.ro']['covered_bytes'],
        by_name['.data.rel.ro']['total_bytes'],
    ) == (16, 7128, 7784)
    assert report['string']['text'] == 'mint-authority'
    assert report['descriptor']['original']['pointer'] == 712415
    assert report['descriptor']['candidate']['pointer'] == 690969
    assert report['descriptor']['original']['relocation'] == dict(type=8, symbol_index=0)
    assert report['descriptor']['candidate']['relocation'] == dict(type=8, symbol_index=0)
    return summary


def seal(packet=P, root=REPO):
    packet = Path(packet)
    report = inspect()
    (packet / 'observations.json.gz').write_bytes(
        gzip.compress(json.dumps(report, separators=(',', ':')).encode(), mtime=0)
    )
    (packet / 'coverage-delta.json').write_text(
        json.dumps(coverage(report), indent=2) + '\n'
    )
    inventory = {
        str(path.relative_to(packet)): sha(path.read_bytes())
        for path in sorted(packet.rglob('*'))
        if path.is_file()
        and path.name != 'manifest.json'
        and '__pycache__' not in path.parts
        and path.suffix != '.pyc'
    }
    (packet / 'manifest.json').write_text(json.dumps(inventory, indent=2) + '\n')
    return report['summary']


if __name__ == '__main__':
    print(json.dumps(seal(), indent=2))
