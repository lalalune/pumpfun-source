#!/usr/bin/env python3
"""ctoracle.py: llc oracle for 0x22a10 admin_cto::execute (experiment only; never a proposal).

  ctoracle.py run <module.ll> <outdir> [--edit edit.py] [--llc-arg X ...]
      llc the module (optionally after edit(fn_text)->fn_text on execute's IR), then score the
      function with the same tokens as target_metric.py: ratio, slots_diff (same size), abstracted
      ratio (frame offsets, add64 frame immediates and jump offsets masked, as segab.py) and bytes.
  ctoracle.py so <unstripped.so>
      score admin_cto from a linked build (control for `run`).

Call tokens: an object file has a relocation on every call (-function-sections); a call to a
known syscall becomes `call -1` (src 1, imm -1 kept), any other call the masked internal form (src 1), which is
what score.normalize gives on the linked .so. lddw with a relocation is masked (section pointer).
"""
import argparse, difflib, json, os, re, runpy, struct, subprocess, sys
from pathlib import Path

H = Path(__file__).resolve().parents[4] / 'harness'
sys.path.insert(0, str(H))
from score import original_windows, sections  # noqa: E402
from win import Cand, insns, ORIG_SECS, demangle  # noqa: E402

SDK = Path.home() / '.cache/solana/v1.44/platform-tools'
LLC = [str(SDK / 'llvm/bin/llc'), '-O3', '-relocation-model=pic', '-mattr=+store-imm,+jmp-ext', '-function-sections']
SYMRE = re.compile(r'_ZN14pump_recovered9admin_cto7execute17h[0-9a-f]+E')
WIN = 0x22a10
SYSCALLS = re.compile(r'^(sol_[a-z0-9_]+|abort)$')


def orig_tokens():
    w = next(w for w in original_windows() if w['start'] == WIN)
    return [x[2] for x in insns(w['raw'], w['start'], ORIG_SECS)], w


def abstract(tok):
    """segab-style abstraction: mask r10 frame offsets, negative add64 immediates, jump offsets."""
    b = bytearray(tok); op = b[0]; dst = b[1] & 15; src = b[1] >> 4; cls = op & 7
    if cls == 1 and src == 10:            # ldx [r10+off]
        b[2:4] = b'\0\0'
    elif cls in (2, 3) and dst == 10:     # st/stx [r10+off]
        b[2:4] = b'\0\0'
    elif op == 0x07 and struct.unpack_from('<i', b, 4)[0] < 0:   # add64 rX, -imm (frame address)
        b[4:8] = b'\0\0\0\0'
    elif cls == 5 and op not in (0x85, 0x95, 0x8d):              # jumps
        b[2:4] = b'\0\0'
    return bytes(b)


def metrics(otok, ctok, nbytes, wbytes):
    sm = difflib.SequenceMatcher(None, otok, ctok, autojunk=False)
    ab = difflib.SequenceMatcher(None, [abstract(t) for t in otok], [abstract(t) for t in ctok], autojunk=False)
    r = {'ratio': round(sm.ratio(), 5), 'abs_ratio': round(ab.ratio(), 5), 'bytes': nbytes, 'insns': len(ctok)}
    if nbytes == wbytes:
        o = b''.join(otok); c = b''.join(ctok)
        r['slots_diff'] = sum(1 for i in range(0, nbytes, 8) if o[i:i + 8] != c[i:i + 8])
    return r


def read_elf(path):
    blob = Path(path).read_bytes()
    shoff, = struct.unpack_from('<Q', blob, 0x28); shentsize, shnum, shstrndx = struct.unpack_from('<HHH', blob, 0x3a)
    secs = []
    for i in range(shnum):
        name, typ, flags, addr, off, size, link, info, align, entsize = struct.unpack_from('<IIQQQQIIQQ', blob, shoff + i * shentsize)
        secs.append(dict(name=name, type=typ, off=off, size=size, link=link, info=info, entsize=entsize))
    strtab = secs[shstrndx]
    for s in secs:
        s['name'] = blob[strtab['off'] + s['name']:blob.index(b'\0', strtab['off'] + s['name'])].decode()
    symtab = next(s for s in secs if s['type'] == 2)
    sstr = secs[symtab['link']]
    syms = []
    for i in range(symtab['size'] // 24):
        nm, info, other, shndx, value, size = struct.unpack_from('<IBBHQQ', blob, symtab['off'] + i * 24)
        n = blob[sstr['off'] + nm:blob.index(b'\0', sstr['off'] + nm)].decode()
        syms.append(dict(name=n, shndx=shndx, value=value, size=size, type=info & 15))
    return blob, secs, syms


def obj_tokens(objpath, sym=None):
    blob, secs, syms = read_elf(objpath)
    s = next(x for x in syms if (x['name'] == sym if sym else SYMRE.fullmatch(x['name'])) and x['shndx'] not in (0, 0xfff1))
    sec = secs[s['shndx']]
    raw = blob[sec['off'] + s['value']:sec['off'] + s['value'] + s['size']]
    rel = {}
    for r in secs:
        if r['type'] == 9 and r['info'] == s['shndx']:   # SHT_REL
            for i in range(r['size'] // 16):
                off, info = struct.unpack_from('<QQ', blob, r['off'] + i * 16)
                rel[off - s['value']] = syms[info >> 32]
    toks = []; i = 0
    while i < len(raw):
        n = 16 if raw[i] == 0x18 else 8
        t = bytearray(raw[i:i + n])
        if t[0] == 0x18 and i in rel:
            t[4:8] = bytes(4); t[12:16] = bytes(4)
        elif t[0] == 0x85:
            r = rel.get(i)
            if r is not None and SYSCALLS.match(r['name']):
                t = bytearray(b'\x85\x10\x00\x00\xff\xff\xff\xff')
            elif r is not None or (t[1] >> 4) == 1:
                t = bytearray(b'\x85\x10\x00\x00\x00\x00\x00\x00')
        toks.append(bytes(t)); i += n
    return toks, raw, s['name']


def so_tokens(path):
    c = Cand(path)
    s, n, nm = next((s, n, nm) for s, n, nm in c.funcs if SYMRE.fullmatch(nm) or demangle(nm).endswith('admin_cto::execute'))
    return [x[2] for x in insns(c.fn(s, n), s, c.secs)], n


def fn_bounds(mod, sym):
    i = mod.index('define ', mod.index('@' + sym + '(') - 300)
    i = mod.rindex('\ndefine ', 0, mod.index('@' + sym + '(')) + 1
    j = mod.index('\n}\n', i) + 3
    return i, j


def run(module, outdir, edit=None, llc_args=(), quiet=False):
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    mod = Path(module).read_text()
    sym = SYMRE.search(mod).group(0)
    if edit:
        i, j = fn_bounds(mod, sym)
        ns = runpy.run_path(edit)
        fn2 = ns['edit'](mod[i:j]) if 'edit' in ns else mod[i:j]
        mod2 = mod[:i] + fn2 + mod[j:]
        if 'edit_module' in ns:
            mod2 = ns['edit_module'](mod2)
        assert mod2 != mod, 'edit changed nothing'
        (outdir / 'm.ll').write_text(mod2); src = outdir / 'm.ll'
    else:
        src = Path(module)
    r = subprocess.run(LLC + list(llc_args) + [str(src), '-filetype=obj', '-o', str(outdir / 'm.o')], capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-3000:]); return None
    ctok, raw, _ = obj_tokens(outdir / 'm.o', sym)
    otok, w = orig_tokens()
    m = metrics(otok, ctok, len(raw), w['bytes'])
    (outdir / 'metrics.json').write_text(json.dumps(m) + '\n')
    (outdir / 'fn.bin').write_bytes(b''.join(ctok))
    if edit and not os.environ.get('KEEP_LL'):
        (outdir / 'm.ll').unlink()
    if not quiet:
        print(json.dumps(m))
    return m


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest='cmd', required=True)
    a = sp.add_parser('run'); a.add_argument('module'); a.add_argument('outdir'); a.add_argument('--edit'); a.add_argument('--llc-arg', action='append', default=[])
    b = sp.add_parser('so'); b.add_argument('so')
    c = sp.add_parser('cmp'); c.add_argument('so'); c.add_argument('obj')
    x = ap.parse_args()
    if x.cmd == 'run':
        run(x.module, x.outdir, x.edit, x.llc_arg)
    elif x.cmd == 'so':
        otok, w = orig_tokens(); ctok, n = so_tokens(x.so)
        print(json.dumps(metrics(otok, ctok, n, w['bytes'])))
    else:
        a, _ = so_tokens(x.so); b, _, _ = obj_tokens(x.obj)
        print('tokens equal' if a == b else f'DIFFER: {sum(1 for p, q in zip(a, b) if p != q)} of {len(a)}/{len(b)}')


if __name__ == '__main__':
    main()
