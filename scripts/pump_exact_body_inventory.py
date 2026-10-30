#!/usr/bin/env python3
"""Raw local body equality for the captured main Pump's inferred windows.

No call, pointer, constant, register, or source-location byte is normalized.
Matching a local window does not prove its runtime callee or data referents.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

from pump_quote_control_function_match import sections, candidate_functions, function_body, protect_report_output, resolve_objdump

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / 'evidence/original/pump/deployed.so'
ARCHIVED_WINDOWS = Path('repro/reconstruction-status-2026-10-26/functions.tsv')
CHECKED_IN_WINDOWS = Path('reconstruction/base/functions.tsv')
EXPECTED_ORIGINAL = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
WINDOW_COLUMNS = {'program', 'variant', 'original_start', 'original_end'}


def window_inventory(root=None):
    """Return the archived window table, or the checked-in inventory."""
    root = ROOT if root is None else Path(root)
    archived = root / ARCHIVED_WINDOWS
    if archived.is_file():
        return archived
    checked_in = root / CHECKED_IN_WINDOWS
    if checked_in.is_file():
        return checked_in
    raise FileNotFoundError('no Pump window inventory')


def selected_windows(stream):
    """Return (original_start, original_end) pairs for selected Pump windows.

    A duplicated required column is ambiguous: DictReader silently resolves it
    last-wins, so a second program column could admit a row the first column
    excludes, and a second original_start could substitute a different window
    than the first column describes. Reject such inventories instead of
    silently picking one column.
    """
    reader = csv.DictReader(stream, delimiter='\t')
    fieldnames = reader.fieldnames or []
    if any(fieldnames.count(name) > 1 for name in WINDOW_COLUMNS):
        raise ValueError('window inventory has duplicate required columns')
    windows = []
    for row in reader:
        if row['program'] != 'pump' or row['variant'] != 'selected':continue
        windows.append((int(row['original_start']), int(row['original_end'])))
    return windows


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    if not __debug__:
        raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True, help='Unstripped main Pump source build')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--objdump', default=str(Path.home()/'.cache/solana/v1.52/platform-tools/llvm/bin/llvm-objdump'))
    args = parser.parse_args()
    args.objdump = resolve_objdump(args.objdump)
    windows = window_inventory()
    protect_report_output(args.output, [ORIGINAL, args.candidate, windows, Path(__file__)], args.objdump)
    original, candidate = ORIGINAL.read_bytes(), args.candidate.read_bytes()
    assert sha(original) == EXPECTED_ORIGINAL
    original_sections, candidate_sections = sections(original), sections(candidate)
    os = original_sections['.text']
    counterparts = {}
    for address, size, name in candidate_functions(args.candidate, args.objdump, '.', image=candidate):
        raw = function_body(candidate, candidate_sections, address, size)
        counterparts.setdefault((size, sha(raw)), []).append({'address':address, 'symbol':name})
    rows = []
    # Hash the parsed bytes, not a later re-read of the inventory path.
    window_bytes = windows.read_bytes()
    with io.TextIOWrapper(io.BytesIO(window_bytes)) as stream:
        bounds = selected_windows(stream)
    for start, end in bounds:
        raw = function_body(original, original_sections, start, end-start)
        matches=counterparts.get((end-start,sha(raw)),[])
        rows.append({'original_start':start,'original_end':end,'bytes':end-start,
                     'sha256':sha(raw),'raw_counterparts':matches})
    assert len(rows)==1035
    assert rows[0]['original_start']==os['addr'] and rows[-1]['original_end']==os['addr']+os['size']
    assert all(a['original_end']==b['original_start'] for a,b in zip(rows,rows[1:]))
    result={'scope':__doc__,'original_sha256':sha(original),'candidate_sha256':sha(candidate),
            'window_inventory_sha256':sha(window_bytes),'script_sha256':sha(Path(__file__).read_bytes()),
            'helper_sha256':sha((ROOT/'scripts/pump_quote_control_function_match.py').read_bytes()),
            'objdump_sha256':sha(Path(args.objdump).read_bytes()),
            'candidate_bytes':len(candidate),'original_text_bytes':os['size'],
            'original_windows':len(rows),'raw_equal_windows':sum(bool(r['raw_counterparts']) for r in rows),
            'raw_equal_text_bytes':sum(r['bytes'] for r in rows if r['raw_counterparts']),
            'whole_file_equal':original==candidate,'windows':rows}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('scope','windows')},indent=2))


if __name__=='__main__':main()
