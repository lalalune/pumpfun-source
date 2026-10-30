from pathlib import Path
import csv, gzip, hashlib, json, struct, sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from pump_compare_function_bytes import body, normalize
from pump_quote_control_function_match import sections


def functions(blob):
    shoff = struct.unpack_from('<Q', blob, 0x28)[0]
    entsize, count, names_idx = struct.unpack_from('<HHH', blob, 0x3a)
    headers = [struct.unpack_from('<IIQQQQIIQQ', blob, shoff + i * entsize) for i in range(count)]
    names = headers[names_idx]
    def string(table, offset):
        start = table[4] + offset
        return blob[start:blob.index(b'\0', start)].decode()
    text_index = next(i for i, h in enumerate(headers) if string(names, h[0]) == '.text')
    for h in headers:
        if h[1] != 2:
            continue
        for k in range(h[5] // 24):
            nm, info, _, sec, addr, size = struct.unpack_from('<IBBHQQ', blob, h[4] + 24 * k)
            if info & 15 == 2 and sec == text_index and size:
                yield addr, size, string(headers[h[6]], nm)


def census(path):
    blob = Path(path).read_bytes()
    cs = sections(blob)
    index = {}
    for start, size, name in functions(blob):
        raw = body(blob, cs, start, size)
        norm, _ = normalize(raw, start, cs)
        index.setdefault((size, hashlib.sha256(norm).hexdigest()), []).append({
            'start': start, 'symbol': name, 'raw_sha256': hashlib.sha256(raw).hexdigest()})
    original = (ROOT / 'evidence/original/pump/deployed.so').read_bytes()
    os_ = sections(original)
    windows = []
    with (ROOT / 'repro/reconstruction-status-2026-10-26/functions.tsv').open() as stream:
        for row in csv.DictReader(stream, delimiter='\t'):
            if row['program'] != 'pump' or row['variant'] != 'selected':
                continue
            start, end = int(row['original_start']), int(row['original_end'])
            raw = body(original, os_, start, end - start)
            norm, _ = normalize(raw, start, os_)
            matches = index.get((end - start, hashlib.sha256(norm).hexdigest()), [])
            digest = hashlib.sha256(raw).hexdigest()
            windows.append({'start': start, 'end': end, 'bytes': end - start,
                'raw_sha256': digest, 'normalized_matches': matches,
                'raw_match': any(m['raw_sha256'] == digest for m in matches)})
    assert len(windows) == 1035
    return {'candidate_sha256': hashlib.sha256(blob).hexdigest(), 'windows': windows,
        'counts': {'total': len(windows), 'normalized': sum(bool(w['normalized_matches']) for w in windows),
            'raw': sum(w['raw_match'] for w in windows),
            'unmatched': sum(not w['normalized_matches'] for w in windows),
            'matched_text_bytes': sum(w['bytes'] for w in windows if w['normalized_matches'])}}


if __name__ == '__main__':
    report = census(sys.argv[1])
    Path(sys.argv[2]).write_bytes(gzip.compress(json.dumps(report, sort_keys=True).encode(), mtime=0))
    print(json.dumps(report['counts']))
