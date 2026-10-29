#!/usr/bin/env python3
"""Score an AMM build against the original sell cashback window (0x4c750, 9,024 bytes).

Usage:
  sell_score.py BUILD_OUT_DIR [--disasm] [--json]
BUILD_OUT_DIR must contain candidate.so (stripped) and symbols.so (unstripped).

Reported (JSON):
  sell_raw_equal         candidate sell bytes == original sell bytes (THE GOAL)
  whole_elf_equal        stripped candidate.so == captured original, including length
  allocation_image_equal candidate.so zero-filled to the capture size == original
  unstripped_elf_equal   raw compiler output symbols.so == captured original
  windows_raw_equal      raw-equal physical windows out of 785 (baseline 784)
  lost_windows           non-sell windows that are no longer raw-equal (must be [])
  sell_start/sell_size   candidate cashback symbol location (original 0x4c750 / 9024)
  slot_diffs             differing 8-byte slots at equal offsets inside sell
  align_distance         instruction-level edit distance after masking jump/call offsets
  ja_count/cond_count    unconditional / conditional jumps (original 35 / ?)
  borrow_branch          the instruction pair after the try_borrow_data return check
"""
from pathlib import Path
import argparse
import difflib
import hashlib
import json
import os
import struct
import sys

HERE = Path(__file__).resolve().parent
ORIGINAL = Path(os.environ.get('AMM_SELL_SWARM', HERE.parent)).resolve() / 'infra/original/deployed.so'
ORIGINAL_SHA = '6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7'
SELL_START = 0x4c750
SELL_SIZE = 9024
SCORE_VERSION = 2
sys.path.insert(0, str(HERE))
try:
    import elf_reader  # noqa: E402
except ImportError:  # repository layout: scripts/window_elf_reader.py
    sys.path.insert(0, str(HERE.parent))
    import window_elf_reader as elf_reader  # noqa: E402

ALU = {0x0: 'add', 0x1: 'sub', 0x2: 'mul', 0x3: 'div', 0x4: 'or', 0x5: 'and', 0x6: 'lsh', 0x7: 'rsh',
       0x8: 'neg', 0x9: 'mod', 0xa: 'xor', 0xb: 'mov', 0xc: 'arsh', 0xd: 'end'}
JMP = {0x0: 'ja', 0x1: 'jeq', 0x2: 'jgt', 0x3: 'jge', 0x4: 'jset', 0x5: 'jne', 0x6: 'jsgt', 0x7: 'jsge',
       0x8: 'call', 0x9: 'exit', 0xa: 'jlt', 0xb: 'jle', 0xc: 'jslt', 0xd: 'jsle'}
SIZE = {0x00: 'w', 0x08: 'h', 0x10: 'b', 0x18: 'dw'}


def decode(code, start, size):
    """Yield (offset, length, raw, mnemonic, fields) for a function body."""
    at = start
    end = start + size
    while at < end:
        op, regs, off, imm = struct.unpack_from('<BBhi', code, at)
        dst, src = regs & 0xf, regs >> 4
        cls = op & 7
        if op == 0x18:
            hi = struct.unpack_from('<i', code, at + 12)[0]
            value = (imm & 0xffffffff) | ((hi & 0xffffffff) << 32)
            yield at - start, 16, code[at:at + 16], f'lddw r{dst}, {value:#x}', ('lddw', dst, value)
            at += 16
            continue
        if cls in (4, 7):
            name = ALU.get(op >> 4, f'alu{op >> 4:x}') + ('' if cls == 7 else '32')
            text = f'{name} r{dst}, ' + (f'r{src}' if op & 8 else f'{imm}')
            fields = (name, dst, src if op & 8 else None, None if op & 8 else imm)
        elif cls in (5, 6):
            kind = JMP.get(op >> 4, f'jmp{op >> 4:x}')
            if kind == 'call':
                text = f'call {"internal" if src == 1 else "syscall"} {imm}'
                fields = ('call', src, imm)
            elif kind == 'exit':
                text, fields = 'exit', ('exit',)
            elif kind == 'ja':
                text, fields = f'ja {off:+d}', ('ja', off)
            else:
                name = kind + ('' if cls == 5 else '32')
                rhs = f'r{src}' if op & 8 else f'{imm}'
                text = f'{name} r{dst}, {rhs}, {off:+d}'
                fields = (name, dst, src if op & 8 else None, None if op & 8 else imm, off)
        elif cls == 1:
            text = f'ldx{SIZE[op & 0x18]} r{dst}, [r{src}{off:+d}]'
            fields = ('ldx' + SIZE[op & 0x18], dst, src, off)
        elif cls == 2:
            text = f'st{SIZE[op & 0x18]} [r{dst}{off:+d}], {imm}'
            fields = ('st' + SIZE[op & 0x18], dst, off, imm)
        elif cls == 3:
            text = f'stx{SIZE[op & 0x18]} [r{dst}{off:+d}], r{src}'
            fields = ('stx' + SIZE[op & 0x18], dst, src, off)
        else:
            text, fields = f'op{op:#x}', ('op', op, regs, off, imm)
        yield at - start, 8, code[at:at + 8], text, fields
        at += 8


def demangle_map(symbols):
    names = {f['start']: f['name'] for f in symbols.funcs}
    try:
        import subprocess
        raw = sorted(set(names.values()))
        out = subprocess.run(['c++filt'], input='\n'.join(raw), capture_output=True, text=True).stdout.splitlines()
        if len(out) == len(raw):
            table = dict(zip(raw, out))
            names = {k: table[v] for k, v in names.items()}
    except Exception:
        pass
    return names


def listing(elf, start, size, names=None):
    rows = list(decode(elf.b, start, size))
    by_off = {r[0]: i for i, r in enumerate(rows)}
    out = []
    for i, (off, length, raw, text, fields) in enumerate(rows):
        target = None
        if fields[0] in ('ja',) or (fields[0].startswith('j') and len(fields) == 5):
            target = off + length + fields[-1] * 8
        if fields[0] == 'call' and fields[1] == 1:
            target = ('call', start + off + 8 + fields[2] * 8)
            if names:
                text = f"{text}  ; {target[1]:#x} {names.get(target[1], '?')}"
        elif isinstance(target, int):
            text = f"{text}  ; -> {target:#06x}"
        out.append({'off': off, 'len': length, 'raw': raw.hex(), 'text': text, 'fields': fields, 'target': target})
    return out


def normalized_tokens(rows):
    """Instruction tokens with branch displacements replaced by relative block labels.

    Calls keep their absolute target (callee identity matters); lddw keeps its value.
    """
    targets = sorted({r['target'] for r in rows if isinstance(r['target'], int)})
    label = {t: f'L{i}' for i, t in enumerate(targets)}
    tokens = []
    for r in rows:
        f = r['fields']
        if isinstance(r['target'], int):
            tokens.append(' '.join(map(str, f[:-1])) + ' ->' + label[r['target']])
        elif isinstance(r['target'], tuple):
            tokens.append(f'call {r["target"][1]:#x}')
        else:
            tokens.append(' '.join(map(str, f)))
    return tokens


def find_sell(symbols):
    hits = [f for f in symbols.funcs if '4sell8cashback' in f['name']]
    if len(hits) != 1:
        raise SystemExit(f'expected one sell cashback symbol, found {len(hits)}')
    return hits[0]


def score(out_dir, want_disasm=False):
    out = Path(out_dir)
    original = elf_reader.Elf(ORIGINAL)
    if hashlib.sha256(original.b).hexdigest() != ORIGINAL_SHA:
        raise SystemExit('original image hash mismatch')
    candidate = elf_reader.Elf(out / 'candidate.so')
    symbols = elf_reader.Elf(out / 'symbols.so')
    sell = find_sell(symbols)
    whole = candidate.b == original.b
    allocation_equal = (len(candidate.b) <= len(original.b)
                        and original.b[:len(candidate.b)] == candidate.b
                        and not any(original.b[len(candidate.b):]))
    o_sell = original.b[SELL_START:SELL_START + SELL_SIZE]
    c_sell = candidate.b[sell['start']:sell['start'] + sell['size']]
    sell_equal = sell['start'] == SELL_START and sell['size'] == SELL_SIZE and o_sell == c_sell
    windows = list(zip(original.entries, original.entries[1:] + [original.hi]))
    equal = [original.b[a:z] == candidate.b[a:z] for a, z in windows]
    lost = [hex(a) for (a, z), ok in zip(windows, equal) if not ok and a != SELL_START]
    # Pair windows by order on relocation/call-masked bytes: a sell size change shifts every
    # later window without being a regression of those functions.
    c_windows = list(zip(candidate.entries, candidate.entries[1:] + [candidate.hi]))
    lost_norm = None
    if len(c_windows) == len(windows):
        lost_norm = [hex(a) for (a, z), (x, y) in zip(windows, c_windows)
                     if a != SELL_START and original.normalized[a:z] != candidate.normalized[x:y]]
    names = demangle_map(symbols) if want_disasm else None
    o_rows = listing(original, SELL_START, SELL_SIZE, names)
    c_rows = listing(candidate, sell['start'], sell['size'], names)
    o_tok, c_tok = normalized_tokens(o_rows), normalized_tokens(c_rows)
    matcher = difflib.SequenceMatcher(None, o_tok, c_tok, autojunk=False)
    distance = sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != 'equal')
    slot_diffs = sum(1 for i in range(0, min(len(o_sell), len(c_sell)), 8) if o_sell[i:i + 8] != c_sell[i:i + 8])
    borrow = {}
    for name, rows in (('original', o_rows), ('candidate', c_rows)):
        window = [r for r in rows if 0xcd0 <= r['off'] <= 0xd10]
        borrow[name] = [f"{r['off']:#x} {r['text']}" for r in window]
    report = {
        'build': str(out), 'score_version': SCORE_VERSION,
        'candidate_sha256': hashlib.sha256(candidate.b).hexdigest(),
        'unstripped_sha256': hashlib.sha256(symbols.b).hexdigest(),
        'sell_raw_equal': sell_equal, 'whole_elf_equal': whole,
        'allocation_image_equal': allocation_equal,
        'unstripped_elf_equal': symbols.b == original.b,
        'original_bytes': len(original.b), 'candidate_bytes': len(candidate.b),
        'unstripped_bytes': len(symbols.b),
        'allocation_padding_bytes': len(original.b) - len(candidate.b) if allocation_equal else None,
        'windows_raw_equal': sum(equal), 'windows_total': len(windows), 'lost_windows': lost,
        'candidate_windows': len(c_windows),
        'lost_windows_normalized': lost_norm,
        'sell_start': hex(sell['start']), 'sell_size': sell['size'],
        'slot_diffs': slot_diffs, 'align_distance': distance,
        'ja_count': {'original': sum(r['fields'][0] == 'ja' for r in o_rows),
                     'candidate': sum(r['fields'][0] == 'ja' for r in c_rows)},
        'cond_count': {'original': sum(isinstance(r['target'], int) and r['fields'][0] != 'ja' for r in o_rows),
                       'candidate': sum(isinstance(r['target'], int) and r['fields'][0] != 'ja' for r in c_rows)},
        'borrow_branch': borrow,
    }
    if want_disasm:
        lines = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for k in range(i2 - i1):
                    lines.append(f"  {o_rows[i1 + k]['off']:#06x} {c_rows[j1 + k]['off']:#06x}  {o_rows[i1 + k]['text']}")
            else:
                for k in range(i1, i2):
                    lines.append(f"- {o_rows[k]['off']:#06x}         {o_rows[k]['text']}")
                for k in range(j1, j2):
                    lines.append(f"+        {c_rows[k]['off']:#06x}  {c_rows[k]['text']}")
        (out / 'sell-align.diff').write_text('\n'.join(lines) + '\n')
        (out / 'sell-original.s').write_text('\n'.join(f"{r['off']:#06x}  {r['raw']:<32} {r['text']}" for r in o_rows) + '\n')
        (out / 'sell-candidate.s').write_text('\n'.join(f"{r['off']:#06x}  {r['raw']:<32} {r['text']}" for r in c_rows) + '\n')
        report['disasm'] = [str(out / 'sell-align.diff'), str(out / 'sell-original.s'), str(out / 'sell-candidate.s')]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('out_dir')
    parser.add_argument('--disasm', action='store_true')
    args = parser.parse_args()
    print(json.dumps(score(args.out_dir, args.disasm), indent=1))


if __name__ == '__main__':
    main()
