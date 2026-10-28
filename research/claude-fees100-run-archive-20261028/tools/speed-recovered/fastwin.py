#!/usr/bin/env python3
"""Fast, exact drop-in for the repo normalizer (window_map.windows) with a persistent cache.

Library (used by fndiff.py / measure.py / dis.py / fastdiff.py / farm.py):
    import fastwin                      # (tools dir on sys.path, or load by path)
    rows = fastwin.windows(image_bytes) # == window_map.windows(image_bytes), cached by sha256
    fastwin.w, fastwin.m                # the repo's window_map / elf_helpers modules (elf_layout memoized)

What makes it fast (results are unchanged):
  1. elf_helpers.elf_layout is memoized per image object. The reference recomputes it (including a
     sha256 of the whole 1.2 MB image) for every at_address() call: ~7,800 times per fndiff run.
  2. windows() results are cached in memory and on disk (tools/cache/windows/<sha256>.<normver>.pkl);
     normver hashes window_map.py + elf_helpers.py + analyze.py, so a normalizer change invalidates.
  3. A cache miss is computed by fast_windows(), a re-implementation that decodes each window once
     without per-instruction dicts/hex. It is checked against the reference implementation by
     `fastwin.py --selftest IMAGES...` (field-by-field equality of every window). Set
     FASTWIN_REFERENCE=1 to force the reference implementation (still memoized + cached).

CLI:
    python3 -I fastwin.py --selftest IMG.so [IMG2.so ...]   # fast_windows == window_map.windows ?
    python3 -I fastwin.py --warm IMG.so [...]               # precompute cache entries
"""
import hashlib, importlib.util, json, os, pickle, struct, sys, tempfile, time
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
WT = HERE.parents[1] / 'base'
WM_PATH = WT / 'research/fees-composed-frontier188/window_map.py'
ORIG_PATH = WT / 'evidence/original/pump_fees/deployed.so'
CACHE_DIR = Path(os.environ.get('FASTWIN_CACHE', HERE / 'cache' / 'windows'))


def _module(n, p):
    s = importlib.util.spec_from_file_location(n, p); mod = importlib.util.module_from_spec(s); s.loader.exec_module(mod); return mod


w = _module('wm', WM_PATH)
m = w.m
_ref_elf_layout = m.elf_layout


class _Memo:
    """Memoize elf_layout(image) per image object (identity), falling back for unhashable inputs."""
    def __init__(self, fn):
        self.fn = fn; self.cache = {}
    def __call__(self, b):
        k = id(b)
        hit = self.cache.get(k)
        if hit is not None and hit[0] is b:
            return hit[1]
        r = self.fn(b)
        if isinstance(b, bytes):
            if len(self.cache) > 64:
                self.cache.clear()
            self.cache[k] = (b, r)
        return r


if not isinstance(m.elf_layout, _Memo):
    m.elf_layout = _Memo(_ref_elf_layout)
elf_layout = m.elf_layout


def _normver():
    h = hashlib.sha256()
    for p in (WM_PATH, WM_PATH.parent / 'elf_helpers.py', WT / 'scripts/analyze.py'):
        h.update(p.read_bytes())
    h.update(b'fastwin-cache-v1')
    return h.hexdigest()[:16]


NORMVER = _normver()
_mem = {}


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def _cfg(offs, ops, widths, disps):
    """Exact replica of elf_helpers.cfg on decoded arrays."""
    index = {o: i for i, o in enumerate(offs)}
    pending, seen, outside = [0], set(), set()
    while pending:
        offset = pending.pop()
        if offset in seen:
            continue
        i = index.get(offset)
        if i is None:
            outside.add(offset)
            continue
        seen.add(offset)
        opcode = ops[i]
        next_offset = offset + widths[i]
        if opcode == 0x95:
            continue
        if opcode & 7 in (5, 6) and opcode != 0x85:
            pending.append(offset + 8 + disps[i] * 8)
            if opcode == 0x05:
                continue
        pending.append(next_offset)
    return dict(instructions=len(offs), reachable_instructions=len(seen), outside_successors=sorted(outside))


_unpack_hi = struct.Struct('<h').unpack_from
_unpack_imm = struct.Struct('<i').unpack_from


def fast_windows(image):
    """Same result as window_map.windows(image), computed without per-instruction dicts."""
    layout = elf_layout(image)
    section = next(x for x in layout['sections'] if x['name'] == '.text')
    start, end = section['address'], section['address'] + section['size']
    text = m.at_address(image, start, section['size'])
    # whole-.text decode (as the reference does) for call targets / lddw values at instruction starts
    insn_at = {}  # absolute address -> (opcode, src, imm32, lddw_value or None)
    p, n = 0, len(text)
    while p < n:
        op = text[p]
        width = 16 if op == 0x18 else 8
        assert p + width <= n
        insn_at[start + p] = op
        p += width
    relocations = dict(m.relocations(image))
    dyn = w.dynamic_symbols(image)
    starts = {start, struct.unpack_from('<Q', image, 24)[0]}
    starts.update(r['address'] for r in dyn if r['info'] & 15 == 2 and r['index'] and start <= r['address'] < end)
    for address, op in insn_at.items():
        if op == 0x85:
            q = address - start
            if text[q + 1] >> 4 == 1:
                tgt = address + 8 + _unpack_imm(text, q + 4)[0] * 8
                if relocations.get(address, 0) & 0xffffffff != 10 and start <= tgt < end:
                    starts.add(tgt)
    for address, info in relocations.items():
        if info & 0xffffffff != 8:
            continue
        op = insn_at.get(address)
        if op is not None:
            if op == 0x18:
                q = address - start
                value = int.from_bytes(text[q + 4:q + 8] + text[q + 12:q + 16], 'little')
            else:
                value = 0
        else:
            try:
                value = int.from_bytes(m.at_address(image, address, 8), 'little') >> 32
            except StopIteration:
                continue
        if start <= value < end:
            starts.add(value)
    starts = sorted(starts)
    symbols = {r['address']: r for r in m.functions(image)}
    result = []
    for address, stop in zip(starts, starts[1:] + [end]):
        size = stop - address
        raw = m.at_address(image, address, size)
        norm = bytearray(raw)
        annotations = []
        offs, ops, widths, disps = [], [], [], []
        p = 0
        while p < size:
            op = raw[p]
            width = 16 if op == 0x18 else 8
            assert p + width <= size
            offs.append(p); ops.append(op); widths.append(width)
            cls = op & 7
            if cls == 5 or cls == 6:
                disps.append(_unpack_hi(raw, p + 2)[0])
            else:
                disps.append(0)
            absolute = address + p
            info = relocations.get(absolute, 0)
            kind = info & 0xffffffff
            if kind == 10:
                assert op == 0x85
                norm[p + 4:p + 8] = b'\0\0\0\0'
                annotations.append([p, 'import', dyn[info >> 32]['name']])
            elif op == 0x85 and raw[p + 1] >> 4 == 1:
                norm[p + 4:p + 8] = b'\0\0\0\0'
            elif kind == 8:
                assert op == 0x18
                norm[p + 4:p + 8] = b'\0\0\0\0'; norm[p + 12:p + 16] = b'\0\0\0\0'
                annotations.append([p, 'opaque_relocated_pointer'])
            p += width
        signature = hashlib.sha256(bytes(norm) + json.dumps(annotations).encode()).hexdigest()
        sym = symbols.get(address, {})
        result.append(dict(address=address, bytes=size, instructions=len(offs),
            raw_sha256=hashlib.sha256(raw).hexdigest(), signature=signature,
            name=sym.get('name'), symbol_bytes=sym.get('bytes'), cfg=_cfg(offs, ops, widths, disps),
            annotations=annotations))
    return result


def reference_windows(image):
    return w.windows(image)


def windows(image, key=None):
    """Cached window_map.windows(image). key = sha256 hex of image if already known."""
    k = key or sha256(image)
    r = _mem.get(k)
    if r is not None:
        return r
    path = CACHE_DIR / f'{k}.{NORMVER}.pkl'
    try:
        with open(path, 'rb') as f:
            r = pickle.load(f)
        _mem[k] = r
        return r
    except (OSError, EOFError, pickle.UnpicklingError, ValueError):
        pass
    r = reference_windows(image) if os.environ.get('FASTWIN_REFERENCE') else fast_windows(image)
    _mem[k] = r
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=CACHE_DIR, prefix='.tmp-')
        with os.fdopen(fd, 'wb') as f:
            pickle.dump(r, f, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp, path)
    except OSError:
        pass
    return r


_orig = None


def original():
    global _orig
    if _orig is None:
        _orig = ORIG_PATH.read_bytes()
    return _orig


def compare(o, c):
    return w.compare(o, c)


def _selftest(paths):
    ok = True
    for p in paths:
        img = Path(p).read_bytes()
        t0 = time.time(); a = fast_windows(img); t1 = time.time(); b = w.windows(img); t2 = time.time()
        eq = a == b
        if not eq:
            ok = False
            bad = [i for i, (x, y) in enumerate(zip(a, b)) if x != y][:3]
            print(f'MISMATCH {p}: len {len(a)} vs {len(b)}; first differing windows {bad}')
            for i in bad:
                for k in b[i]:
                    if a[i].get(k) != b[i][k]:
                        print('   ', k, repr(a[i].get(k))[:200], '!=', repr(b[i][k])[:200])
        else:
            print(f'ok {len(a)} windows fast {t1-t0:.2f}s reference {t2-t1:.2f}s  {p}')
    return ok


if __name__ == '__main__':
    args = sys.argv[1:]
    if args[:1] == ['--selftest']:
        sys.exit(0 if _selftest(args[1:] or [str(ORIG_PATH)]) else 1)
    elif args[:1] == ['--warm']:
        for p in args[1:] or [str(ORIG_PATH)]:
            t0 = time.time(); r = windows(Path(p).read_bytes()); print(f'{len(r)} windows {time.time()-t0:.2f}s {p}')
    else:
        print(__doc__)
