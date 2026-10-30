"""Admission checks for scorer inputs and report destinations."""
import json
from pathlib import Path
import struct


def sections(blob):
    if len(blob) < 64 or blob[:7] != b'\x7fELF\x02\x01\x01':
        raise ValueError('expected ELF64 little-endian version 1')
    shoff = struct.unpack_from('<Q', blob, 40)[0]
    stride, count, names_index = struct.unpack_from('<HHH', blob, 58)
    if stride != 64 or not count or names_index >= count or shoff < 64 or shoff + stride * count > len(blob):
        raise ValueError('invalid or truncated ELF section table')
    headers = [struct.unpack_from('<IIQQQQIIQQ', blob, shoff + i * stride) for i in range(count)]
    names = headers[names_index]
    if names[1] != 3 or names[4] + names[5] > len(blob):
        raise ValueError('invalid section-name string table')
    strings = blob[names[4]:names[4] + names[5]]
    result = {}
    for h in headers:
        if h[0] >= len(strings): raise ValueError('section name out of bounds')
        end = strings.find(b'\0', h[0])
        if end < 0: raise ValueError('unterminated section name')
        try: name = strings[h[0]:end].decode('utf-8')
        except UnicodeDecodeError as exc: raise ValueError('invalid section name encoding') from exc
        if name in result: raise ValueError('duplicate section name: ' + name)
        if h[1] != 8 and h[4] + h[5] > len(blob): raise ValueError('truncated section payload: ' + name)
        if h[3] + h[5] > 1 << 64: raise ValueError('section address overflow')
        if name == '.text' and h[1] != 1: raise ValueError('.text must be file-backed PROGBITS')
        result[name] = {'addr': h[3], 'offset': h[4], 'size': h[5]}
    if '.text' not in result: raise ValueError('missing .text section')
    return result


def unique(items):
    result = {}
    for key, value in items:
        if key in result: raise ValueError('duplicate JSON field: ' + key)
        result[key] = value
    return result


def baseline(path):
    document = json.loads(Path(path).read_text(), object_pairs_hook=unique)
    if not isinstance(document, dict) or not isinstance(document.get('windows'), (dict, list)):
        raise ValueError('baseline requires a windows object or list')
    windows = document['windows']; result = {}
    rows = windows.items() if isinstance(windows, dict) else ((row.get('start'), row) if isinstance(row, dict) else (None, row) for row in windows)
    for address, row in rows:
        if isinstance(address, bool) or not isinstance(address, (str, int)) or not isinstance(row, dict): raise ValueError('invalid baseline window')
        start = int(address, 16 if isinstance(address, str) and address.startswith('0x') else 10) if isinstance(address, str) else address
        size = row.get('bytes')
        if start < 0 or start in result or type(size) is not int or size <= 0: raise ValueError('invalid/duplicate baseline range')
        if isinstance(windows, list):
            matches = row.get('normalized_matches')
            if not isinstance(matches, list): raise ValueError('normalized_matches must be a list')
            normalized, raw = bool(matches), row.get('raw_match')
        else: normalized, raw = row.get('normalized'), row.get('raw')
        if type(normalized) is not bool or type(raw) is not bool or (raw and not normalized): raise ValueError('invalid baseline membership flags')
        result[start] = {'normalized': normalized, 'raw': raw, 'bytes': size}
    return result


def same_domain(current, base):
    if not base: return  # explicit empty baseline retains initial-inventory behavior
    if current.keys() != base.keys(): raise ValueError('baseline/current window memberships have different address domains')
    if any(current[k]['bytes'] != base[k]['bytes'] for k in current): raise ValueError('baseline/current window sizes differ')


def report_destination(output, inputs):
    if output is None: return
    output = Path(output)
    for value in inputs:
        path = Path(value)
        if output.resolve() == path.resolve() or (output.exists() and path.exists() and output.samefile(path)):
            raise ValueError('report destination aliases an input: ' + str(path))
