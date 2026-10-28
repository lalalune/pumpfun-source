#!/usr/bin/env python3
"""relayout.py - regenerate the Fees layout recipe (ordered.ld) after a source change.

usage:
  python3 -I relayout.py --old-ld OLD/ordered.ld --old-map OLD.map --old-symbols OLD-symbols.so \
                         --new-map NEW.map --new-symbols NEW-symbols.so --out NEW/ordered.ld [--report R.json]
  python3 -I relayout.py --check --old-ld NEW/ordered.ld --new-map BUILT.map --new-symbols BUILT-symbols.so

OLD = the trusted reference build (its ordered.ld, its link map and symbols ELF), e.g. the frontier
      (shared/frontier/w582/ordered.ld + frontier/container/w582.map + w582-container-symbols.so).
NEW = ANY link of the changed source (normally a cbuild/lbuild with the stale OLD ordered.ld): only its
      map and symbols ELF are read, so the layout used for that link does not matter.

What it does
  1. Atoms = complete compiler-emitted input sections (map rows of .text/.rodata/.data.rel.ro, per
     owning object/archive member). Each atom gets a content identity computed from the linked image:
       text: the repo window normalizer's signature (call / syscall / relocated-lddw operands masked,
             import names kept), all alias names (mergefunc), names with the legacy hash removed;
       data: bytes with relocated pointer fields masked + recursive target identities.
  2. OLD atoms are bound to NEW atoms in passes (first match wins, each atom bound once):
       exact selector (object + section name; never for ordinal names .L__unnamed_N / <internal>),
       unique alias-name sets without hashes, unique content identity, graph propagation through the
       call/lddw/pointer edges of already-bound pairs (lockstep for equal bodies, difflib-aligned for
       changed bodies), unique dehashed names, recursive call/pointer "colors" for groups that are still
       ambiguous, and finally stable order inside equal-identity groups (reported).
  3. Layout: every bound atom keeps its OLD position (the OLD .text order is the original window order,
     so matched functions stay at their window); OLD atoms with no NEW counterpart are dropped; a NEW
     function whose normalized signature equals an original window takes that window's slot (the
     displaced occupant becomes an extra); remaining new functions are appended after the 585 window
     slots (where the extra event-data body sits today); new data atoms take the slot of a dropped OLD
     atom with the same size and referencing site, else they are appended (reported: whole-ELF risk).
  4. The OLD script's skeleton (PHDRS, catch-alls, /DISCARD/) is kept byte-for-byte; only selectors change.

--check verifies a script against the map of a link that USED it: every selector matched exactly one
input section, nothing fell through to the catch-alls, and section order equals selector order.
"""
import argparse, bisect, collections, difflib, hashlib, importlib.util, json, re, struct, sys
from pathlib import Path
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2] if (Path(__file__).resolve().parents[2] / 'base').is_dir() else \
    Path('/Users/shawwalters/fees100-run')
def _module(n, p):
    s = importlib.util.spec_from_file_location(n, p); mod = importlib.util.module_from_spec(s); s.loader.exec_module(mod); return mod
w = _module('wm', R / 'base/research/fees-composed-frontier188/window_map.py'); m = w.m
import functools
m.elf_layout = functools.lru_cache(maxsize=16)(m.elf_layout)
ORIG_PATH = R / 'base/evidence/original/pump_fees/deployed.so'
OUTS = ('.text', '.rodata', '.data.rel.ro')
MAPRE = re.compile(r'\s*([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+(\d+)\s+(\S+):\((\.[^)]*)\)\s*')
SYMRE = re.compile(r'\s*([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+(\d+)\s{9,}(\S.*)$')
OUTRE = re.compile(r'\s*([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+(\d+)\s(\.\S+)$')
SELRE = re.compile(r'^(\s*)\*(\S*)\("([^"\n]+)"\)\s*$')
dehash = lambda s: re.sub(r'17h[0-9a-f]{16}E', '17h_E', s)
ORDINAL = re.compile(r'\.L__unnamed_\d+$|^\.(rodata|data\.rel\.ro)\.cst\d+$|^\.rodata\.str')
H = lambda *x: hashlib.sha256(json.dumps(x, default=str).encode()).hexdigest()[:24]

def owner(path):
    name = path.rsplit('/', 1)[-1]
    return '*' + (name[:-1].replace('(', ':') if '(' in name else name) if path != '<internal>' else '*'

# ----------------------------------------------------------------------------- inputs
def parse_map(text):
    """input sections of .text/.rodata/.data.rel.ro in link order (+ the symbol lines under each)."""
    rows = []; out = None
    for line in text.splitlines():
        mo = OUTRE.fullmatch(line)
        if mo and not line.startswith(' ' * 20):
            out = mo[5]; continue
        mm = MAPRE.fullmatch(line)
        if mm:
            if out in OUTS:
                rows.append(dict(out=out, address=int(mm[1], 16), size=int(mm[3], 16), align=int(mm[4]),
                                 path=mm[5], owner=owner(mm[5]), section=mm[6], syms=[]))
            continue
        ms = SYMRE.fullmatch(line)
        if ms and rows and rows[-1]['out'] == out:
            rows[-1]['syms'].append(ms[5].strip())
    return rows

def parse_ld(text):
    """-> (lines, {out: [(line_index, owner, section)]})"""
    lines = text.splitlines(True); sel = collections.defaultdict(list); cur = None
    for i, line in enumerate(lines):
        st = line.strip()
        mo = re.match(r'(\.\S+)\s*:\s*\{', st)
        if mo: cur = mo[1]; continue
        if st.startswith('}'): cur = None; continue
        ms = SELRE.match(line)
        if ms and cur:
            sel[cur].append((i, '*' + ms[2] if ms[2] else '*', ms[3]))
    return lines, sel

class Image:
    def __init__(self, img, rows):
        self.img = img; self.rows = rows
        L = m.elf_layout(img)
        self.secs = {s['name']: s for s in L['sections']}
        self.rel = dict(m.relocations(img)); self.relpos = sorted(a for a, k in self.rel.items() if k & 0xffffffff == 8)
        self.dyn = w.dynamic_symbols(img)
        self.fnames = collections.defaultdict(list)
        for f in m.functions(img): self.fnames[f['address']].append(f['name'])
        self.atoms = []
        for r in rows:
            a = dict(r); a['kind'] = 'f' if r['out'] == '.text' else 'd'; a['idx'] = len(self.atoms)
            self.atoms.append(a)
        self.starts = [a['address'] for a in self.atoms]
        self.by_start = {}
        for a in self.atoms:
            if a['size']: self.by_start.setdefault((a['kind'], a['address']), a)
        self._sig = {}; self._dkey = {}; self._df = {}
    def atom_at(self, addr):
        j = bisect.bisect_right(self.starts, addr) - 1
        while j >= 0 and self.atoms[j]['address'] == addr and not self.atoms[j]['size']: j -= 1
        if j >= 0 and self.atoms[j]['address'] <= addr < self.atoms[j]['address'] + max(1, self.atoms[j]['size']):
            return self.atoms[j], addr - self.atoms[j]['address']
        return None, None
    def names(self, a):
        if a['kind'] != 'f': return []
        nm = list(self.fnames.get(a['address'], []))
        sec = re.sub(r'^\.text\.(unlikely\.|startup\.|hot\.)?', '', a['section'])
        if sec and sec not in nm: nm.append(sec)
        return nm
    def body(self, a):
        """window-normalizer signature + edges of a text atom."""
        if a['idx'] in self._sig: return self._sig[a['idx']]
        addr, size = a['address'], a['size']
        rows = m.instructions(self.img, addr, size) if size else []
        norm, ann, calls, refs, masked, shape = bytearray(), [], [], [], [], []
        for r in rows:
            raw = bytearray.fromhex(r['raw']); at = addr + r['offset']; info = self.rel.get(at, 0)
            if info & 0xffffffff == 10:
                raw[4:8] = bytes(4); ann.append([r['offset'], 'import', self.dyn[info >> 32]['name']])
            elif 'call_target' in r:
                raw[4:8] = bytes(4); calls.append((r['offset'], r['call_target']))
            elif info & 0xffffffff == 8:
                raw[4:8] = raw[12:16] = bytes(4); ann.append([r['offset'], 'opaque_relocated_pointer'])
                refs.append((r['offset'], r['lddw_value']))
            norm.extend(raw); masked.append(bytes(raw).hex())
            cls = r['opcode'] & 7
            if cls in (1, 2, 3, 5, 6) and r['opcode'] not in (0x85, 0x95):  # branch / memory displacement
                raw[2:4] = bytes(2)
            shape.append(bytes(raw).hex())
        sig = hashlib.sha256(bytes(norm) + json.dumps(ann).encode()).hexdigest()
        res = dict(sig=sig, calls=calls, refs=refs, masked=masked, shape=shape, offsets=[r['offset'] for r in rows])
        self._sig[a['idx']] = res; return res
    def dfields(self, a):
        """(masked bytes, [(offset, target address)]) of a data atom."""
        if a['idx'] in self._df: return self._df[a['idx']]
        self._df[a['idx']] = r = self._dfields(a); return r
    def _dfields(self, a):
        at, size = a['address'], a['size']
        raw = bytearray(m.at_address(self.img, at, size)) if size else bytearray()
        fields = []
        for p in self.relpos[bisect.bisect_left(self.relpos, at):bisect.bisect_left(self.relpos, at + size)]:
            q = p - at
            if q + 8 > size: continue
            lo, hi = struct.unpack_from('<II', raw, q); raw[q:q + 8] = bytes(8); fields.append((q, hi))
        return bytes(raw), fields
    def target_desc(self, addr, depth):
        a, off = self.atom_at(addr)
        if a is None: return ('ext', addr - self.secs['.text']['address'] if False else None)
        if a['kind'] == 'f': return ('f', self.body(a)['sig'] if depth else 'f', off)
        return ('d', self.dkey(a, depth - 1) if depth > 0 else (a['size'],), off)
    def dkey(self, a, depth=3):
        k = (a['idx'], depth)
        if k in self._dkey: return self._dkey[k]
        raw, fields = self.dfields(a)
        if a['owner'] == '*':
            res = H('merged', a['section'], a['size'])  # merged pools: identity = section name
        else:
            res = H(a['size'], raw.hex(), [(q, self.target_desc(t, depth)) for q, t in fields])
        self._dkey[k] = res; return res
    def ident(self, a):
        return ('f', self.body(a)['sig']) if a['kind'] == 'f' else ('d', self.dkey(a))

# ----------------------------------------------------------------------------- binding
class Binder:
    def __init__(self, O, N):
        self.O, self.N = O, N; self.fw = {}; self.bw = {}; self.why = {}
    def bind(self, a, b, why):
        if a['idx'] in self.fw or b['idx'] in self.bw: return False
        if a['kind'] != b['kind'] or a['out'] != b['out']: return False
        self.fw[a['idx']] = b['idx']; self.bw[b['idx']] = a['idx']; self.why[a['idx']] = why; return True
    def free_old(self): return [a for a in self.O.atoms if a['idx'] not in self.fw and a['size']]
    def free_new(self): return [b for b in self.N.atoms if b['idx'] not in self.bw and b['size']]
    def unique(self, keyf, why):
        ko = collections.defaultdict(list); kn = collections.defaultdict(list)
        for a in self.free_old():
            k = keyf(self.O, a)
            if k is not None: ko[k].append(a)
        for b in self.free_new():
            k = keyf(self.N, b)
            if k is not None: kn[k].append(b)
        n = 0
        for k, xs in ko.items():
            if len(xs) == 1 and len(kn.get(k, [])) == 1: n += self.bind(xs[0], kn[k][0], why)
        return n
    def edge(self, ta, tb, why, loose=False):
        a, oa = self.O.atom_at(ta); b, ob = self.N.atom_at(tb)
        if a is None or b is None or a['kind'] != b['kind'] or oa != ob: return 0
        if a['owner'] == '*' or b['owner'] == '*': return 0
        if a['idx'] in self.fw or b['idx'] in self.bw: return 0
        if a['kind'] == 'd' and (a['size'] != b['size'] or self.O.dkey(a, 1) != self.N.dkey(b, 1)): return 0
        if a['kind'] == 'f' and not loose and self.O.body(a)['sig'] != self.N.body(b)['sig'] and \
                set(map(dehash, self.O.names(a))).isdisjoint(map(dehash, self.N.names(b))): return 0
        return self.bind(a, b, why)
    def propagate(self, loose=False):
        """loose: a call site at the same offset of an UNCHANGED caller binds its (otherwise unbound) callees even
        when their names and bodies differ (e.g. a handler body that moved into a differently named function)."""
        done = set(); total = 0
        while True:
            todo = [i for i in self.fw if i not in done]
            if not todo: return total
            for i in todo:
                done.add(i); a = self.O.atoms[i]; b = self.N.atoms[self.fw[i]]
                if a['kind'] == 'f':
                    x, y = self.O.body(a), self.N.body(b)
                    if x['sig'] == y['sig']:
                        pairs = list(zip(x['calls'], y['calls'])) + list(zip(x['refs'], y['refs']))
                    else:  # changed body: only edges inside equal masked blocks
                        sm = difflib.SequenceMatcher(None, x['masked'], y['masked'], autojunk=False)
                        ok = set()
                        for blk in sm.get_matching_blocks():
                            for k in range(blk.size): ok.add((x['offsets'][blk.a + k], y['offsets'][blk.b + k]))
                        cx = dict(x['calls'] + x['refs']); cy = dict(y['calls'] + y['refs'])
                        pairs = [((p, cx[p]), (q, cy[q])) for p, q in ok if p in cx and q in cy]
                    lockstep = x['sig'] == y['sig']
                    for (p, t), (q, u) in pairs:
                        total += self.edge(t, u, ('edge-loose' if loose and lockstep else 'edge', a['section'][:60], p),
                                           loose=loose and lockstep)
                else:
                    _, fa = self.O.dfields(a); _, fb = self.N.dfields(b)
                    if [q for q, _ in fa] == [q for q, _ in fb]:
                        for (p, t), (q, u) in zip(fa, fb): total += self.edge(t, u, ('ptr', a['section'][:60], p))
    def colors(self, img, rounds=6):
        col = {a['idx']: img.ident(a) for a in img.atoms if a['size']}
        for _ in range(rounds):
            new = {}
            for a in img.atoms:
                if not a['size']: continue
                if a['kind'] == 'f':
                    b = img.body(a); es = []
                    for _, t in b['calls'] + b['refs']:
                        x, off = img.atom_at(t); es.append((col.get(x['idx']) if x else None, off))
                    # incoming edges matter too for leaves: include sorted caller colors
                    new[a['idx']] = H(col[a['idx']], es)
                else:
                    _, fs = img.dfields(a); es = []
                    for q, t in fs:
                        x, off = img.atom_at(t); es.append((q, col.get(x['idx']) if x else None, off))
                    new[a['idx']] = H(col[a['idx']], es)
            # callers' colors (reverse edges) disambiguate identical leaves
            rev = collections.defaultdict(list)
            for a in img.atoms:
                if not a['size']: continue
                edges = img.body(a)['calls'] + img.body(a)['refs'] if a['kind'] == 'f' else img.dfields(a)[1]
                for e in edges:
                    t = e[1]; x, off = img.atom_at(t)
                    if x: rev[x['idx']].append((col[a['idx']], e[0], off))
            col = {i: H(c, sorted(rev.get(i, []))) for i, c in new.items()}
        return col

def run(a):
    oimg = Path(a.old_symbols).read_bytes(); nimg = Path(a.new_symbols).read_bytes()
    O = Image(oimg, parse_map(Path(a.old_map).read_text())); N = Image(nimg, parse_map(Path(a.new_map).read_text()))
    lines, sel = parse_ld(Path(a.old_ld).read_text())
    B = Binder(O, N); passes = collections.OrderedDict()
    # P0: exact selector, stable (non-ordinal) names
    nidx = collections.defaultdict(list)
    for b in N.atoms: nidx[(b['owner'], b['section'])].append(b)
    n0 = 0
    for x in O.atoms:
        if not x['size'] or ORDINAL.search(x['section']) or x['owner'] == '*': continue
        ys = nidx.get((x['owner'], x['section']), [])
        if len(ys) == 1: n0 += B.bind(x, ys[0], 'exact-selector')
    passes['exact-selector'] = n0
    # P0b: merged pools by section name (selected as *("name"))
    for x in O.atoms:
        if x['owner'] == '*':
            ys = [y for y in N.atoms if y['owner'] == '*' and y['section'] == x['section']]
            if len(ys) == 1: B.bind(x, ys[0], 'merged-pool')
    # P1: alias-name sets without hashes (text), owner-qualified
    def aliaskey(img, x):
        if x['kind'] != 'f': return None
        return (re.sub(r'-[0-9a-f]{16}', '-H', x['owner']) if '.rlib:' in x['owner'] else 'ROOT', tuple(sorted(set(dehash(n) for n in img.names(x)))))
    passes['dehashed-aliases'] = B.unique(aliaskey, 'dehashed-aliases')
    # P1b: same for named (non-ordinal) data sections
    def dnamekey(img, x):
        if x['kind'] != 'd' or ORDINAL.search(x['section']) or x['owner'] == '*': return None
        return (re.sub(r'-[0-9a-f]{16}', '-H', x['owner']) if '.rlib:' in x['owner'] else 'ROOT', dehash(x['section']))
    passes['dehashed-data-name'] = B.unique(dnamekey, 'dehashed-data-name')
    # P2: unique content identity
    passes['unique-identity'] = B.unique(lambda img, x: img.ident(x), 'unique-identity')
    passes['propagation-1'] = B.propagate()
    passes['unique-identity-2'] = B.unique(lambda img, x: img.ident(x), 'unique-identity')
    # P3: identity + dehashed names (text) for still-ambiguous groups
    passes['identity+names'] = B.unique(lambda img, x: (img.ident(x), aliaskey(img, x)) if x['kind'] == 'f' else None, 'identity+names')
    passes['propagation-2'] = B.propagate()
    # P4: recursive colors
    co, cn = B.colors(O), B.colors(N)
    passes['colors'] = B.unique(lambda img, x: (co if img is O else cn).get(x['idx']), 'colors')
    passes['propagation-3'] = B.propagate()
    # P5: changed bodies: unique dehashed alias names regardless of content
    passes['names-only'] = B.unique(aliaskey, 'names-only')
    passes['propagation-4'] = B.propagate()
    # P6: stable order inside equal identity groups
    go = collections.defaultdict(list); gn = collections.defaultdict(list)
    for x in B.free_old(): go[(O.ident(x), aliaskey(O, x))].append(x)
    for y in B.free_new(): gn[(N.ident(y), aliaskey(N, y))].append(y)
    n6 = 0; ambiguous = []
    for k, xs in go.items():
        ys = gn.get(k, [])
        if len(xs) == len(ys) and xs:
            for x, y in zip(xs, ys): n6 += B.bind(x, y, 'stable-order-in-equal-group')
            ambiguous.append([x['section'][:80] for x in xs])
    passes['stable-order'] = n6
    passes['propagation-5'] = B.propagate()
    # P7: same call site of an unchanged caller (semantic successor, e.g. handler body moved to another fn)
    passes['callsite-successor'] = B.propagate(loose=True) if not a.no_successor else 0
    passes['propagation-6'] = B.propagate()
    # ---------------------------------------------------------------- layout
    orig = Path(a.original).read_bytes() if a.original else ORIG_PATH.read_bytes()
    ow = w.windows(orig)
    report = dict(passes=passes, ambiguous_groups=ambiguous)
    sel_atom = {}
    for x in O.atoms: sel_atom.setdefault((x['owner'], x['section']), x)
    new_lines = list(lines); outsel = {}
    placed = set()
    def fmt(y): return '    ' + (y['owner'] if y['owner'] != '*' else '*') + '(' + json.dumps(y['section']) + ')\n'
    for out in OUTS:
        entries = sel.get(out, [])
        olds = []
        for (li, ow_, sec) in entries:
            x = sel_atom.get((ow_, sec))
            olds.append((li, x))
        slots = []
        for li, x in olds:
            y = N.atoms[B.fw[x['idx']]] if (x is not None and x['idx'] in B.fw) else None
            slots.append(dict(old=x, new=y, line=li))
        if out == '.text':
            # original window of each OLD slot: align the OLD layout's slot signatures with the original
            # window signatures (equal blocks anchor; replaced blocks pair positionally, e.g. the unmatched
            # bodies' semantic slots); unaligned OLD slots are extras (e.g. the outlined event-data body)
            wsig = [r['signature'] for r in ow]
            osig = [O.body(sl['old'])['sig'] if sl['old'] is not None else None for sl in slots]
            win_of = [None] * len(slots)
            for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, wsig, osig, autojunk=False).get_opcodes():
                if tag in ('equal', 'replace'):
                    for d in range(min(i2 - i1, j2 - j1)): win_of[j1 + d] = i1 + d
            sig_of = lambda y: N.body(y)['sig']
            occ = {}; extras_old = []
            for k, sl in enumerate(slots):
                if sl['new'] is None: continue
                if win_of[k] is None or win_of[k] in occ: extras_old.append(sl['new'])
                else: occ[win_of[k]] = sl['new']
            want = collections.defaultdict(list)
            for k, sg in enumerate(wsig): want[sg].append(k)
            moves = []; extras_new = []
            for y in [b for b in N.atoms if b['kind'] == 'f' and b['size']]:
                ks = want.get(sig_of(y), [])
                if len(ks) != 1: continue
                k = ks[0]; cur = occ.get(k)
                if cur is not None and (cur['idx'] == y['idx'] or sig_of(cur) == wsig[k]): continue
                for j, z in list(occ.items()):
                    if z['idx'] == y['idx']: del occ[j]; moves.append(dict(emptied_window=ow[j]['address'], function=y['section']))
                extras_old = [z for z in extras_old if z['idx'] != y['idx']]
                if cur is not None: extras_new.append(cur)
                occ[k] = y
                moves.append(dict(window=ow[k]['address'], function=y['section'], displaced=cur['section'] if cur else None))
            placed_f = {z['idx'] for z in occ.values()} | {z['idx'] for z in extras_old + extras_new}
            extras_new += [b for b in N.atoms if b['kind'] == 'f' and b['size'] and b['idx'] not in placed_f and b['idx'] not in B.bw]
            # empty windows: place the most similar unplaced function (masked-instruction ratio >= 0.5, clear best)
            empty = [k for k in range(len(ow)) if k not in occ]
            if empty and extras_new:
                OI = Image(orig, [])
                for k in empty:
                    om = OI.body(dict(idx=('orig', k), address=ow[k]['address'], size=ow[k]['bytes'], kind='f'))['shape']
                    sc = sorted(((difflib.SequenceMatcher(None, om, N.body(z)['shape'], autojunk=False).ratio(), z['idx']) for z in extras_new),
                                reverse=True)
                    if sc and sc[0][0] >= 0.35 and (len(sc) == 1 or sc[0][0] - sc[1][0] >= 0.15):
                        z = N.atoms[sc[0][1]]; occ[k] = z; extras_new = [e for e in extras_new if e['idx'] != z['idx']]
                        moves.append(dict(window=ow[k]['address'], function=z['section'], similarity=round(sc[0][0], 4), kind='similarity'))
            report['window_moves'] = moves
            final = [occ[k] for k in sorted(occ)] + extras_old + extras_new
            report['text'] = dict(windows=len(ow), occupied=len(occ),
                                  empty_windows=[ow[k]['address'] for k in range(len(ow)) if k not in occ],
                                  mismatched_windows=[dict(window=ow[k]['address'], function=occ[k]['section'])
                                                      for k in sorted(occ) if sig_of(occ[k]) != wsig[k]],
                                  extras_old=[z['section'] for z in extras_old], extras_new=[z['section'] for z in extras_new])
            for sl in slots: new_lines[sl['line']] = ''
            if slots:
                new_lines[slots[0]['line']] = ''.join(fmt(y) for y in final)
            placed.update(y['idx'] for y in final)
            outsel[out] = len(final)
            continue
        else:
            # new data atoms: take the slot of a dropped old atom with the same size, else append
            newd = [b for b in N.atoms if b['out'] == out and b['size'] and b['idx'] not in B.bw]
            tail = []
            for y in newd:
                yr = N.dfields(y)[0]
                holes = [(difflib.SequenceMatcher(None, O.dfields(s['old'])[0], yr, autojunk=False).ratio(), i) for i, s in enumerate(slots)
                         if s['new'] is None and s['old'] is not None and s['old']['size'] == y['size']]
                hole = slots[max(holes)[1]] if holes and max(holes)[0] >= 0.5 else None
                if hole: hole['new'] = y; report.setdefault('data_hole_fills', []).append(dict(old=hole['old']['section'], new=y['section']))
                else: tail.append(y)
            report.setdefault('data', {})[out] = dict(slots=len(slots), dropped=[s['old']['section'] for s in slots if s['new'] is None and s['old']],
                                                    appended=[y['section'] for y in tail])
        # write: replace selector lines in place, append tail after the last selector
        for s in slots:
            new_lines[s['line']] = fmt(s['new']) if s['new'] is not None else ''
            if s['new'] is not None: placed.add(s['new']['idx'])
        if tail and entries:
            new_lines[entries[-1][0]] = new_lines[entries[-1][0]] + ''.join(fmt(y) for y in tail if y['idx'] not in placed)
            placed.update(y['idx'] for y in tail)
        outsel[out] = len(slots)
    # merged constant pools: the linker cannot reorder entries inside them (first-emission order is fixed
    # by the compiler, i.e. by source declaration order); report any content change
    pools = []
    for i, j in B.fw.items():
        x, y = O.atoms[i], N.atoms[j]
        if x['owner'] == '*' and x['size']:
            bx = m.at_address(O.img, x['address'], x['size']); by = m.at_address(N.img, y['address'], y['size'])
            if bx != by:
                pools.append(dict(section=x['section'], old_size=x['size'], new_size=y['size'],
                                  note='merged pool content/order changed: fixable only in source (declaration order)'))
    report['merged_pool_changes'] = pools
    dup = collections.Counter((y['owner'], y['section']) for y in N.atoms if y['idx'] in placed)
    report['duplicate_selectors'] = [k for k, v in dup.items() if v > 1]
    unbound_old = [dict(out=x['out'], section=x['section'], owner=x['owner']) for x in O.atoms if x['size'] and x['idx'] not in B.fw]
    unplaced_new = [dict(out=y['out'], section=y['section'], owner=y['owner']) for y in N.atoms if y['size'] and y['idx'] not in placed]
    report['dropped_old'] = unbound_old; report['unplaced_new'] = unplaced_new
    renamed = [dict(old=O.atoms[i]['section'], new=N.atoms[j]['section'], why=str(B.why[i])) for i, j in B.fw.items()
               if O.atoms[i]['section'] != N.atoms[j]['section'] or O.atoms[i]['owner'] != N.atoms[j]['owner']]
    report['renamed'] = renamed
    report['counts'] = dict(old_atoms=sum(1 for x in O.atoms if x['size']), new_atoms=sum(1 for y in N.atoms if y['size']),
                            bound=len(B.fw), renamed=len(renamed), dropped=len(unbound_old), unplaced_new=len(unplaced_new))
    text = ''.join(new_lines)
    Path(a.out).write_text(text)
    if a.report: Path(a.report).write_text(json.dumps(report, indent=1, default=str) + '\n')
    print(json.dumps(dict(counts=report['counts'], passes=passes,
                          text={k: (v if not isinstance(v, list) else len(v)) for k, v in report.get('text', {}).items()},
                          window_moves=report.get('window_moves', []), dropped=unbound_old[:12],
                          unplaced_new=unplaced_new[:12], renamed=len(renamed), merged_pool_changes=pools), indent=1, default=str))
    return 0

def check(a):
    lines, sel = parse_ld(Path(a.old_ld).read_text())
    rows = parse_map(Path(a.new_map).read_text())
    res = {}; ok = True
    for out in OUTS:
        want = [(o, s) for _, o, s in sel.get(out, [])]
        got = [(r['owner'], r['section']) for r in rows if r['out'] == out and r['size']]
        # merged pools appear once as <internal>
        gotset = collections.Counter(got)
        missing = [x for x in want if gotset[x] == 0]
        extra = [x for x in got if x not in set(want)]
        order_ok = [x for x in got if x in set(want)] == [x for x in want if gotset[x]]
        res[out] = dict(selectors=len(want), matched=len(want) - len(missing), missing=missing[:20], n_missing=len(missing),
                        fell_through=[x for x in extra][:20], n_fell_through=len(extra), order_ok=order_ok)
        ok &= not missing and order_ok
    print(json.dumps(res, indent=1)); return 0 if ok else 1

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--old-ld', required=True); ap.add_argument('--old-map'); ap.add_argument('--old-symbols')
    ap.add_argument('--new-map', required=True); ap.add_argument('--new-symbols'); ap.add_argument('--out')
    ap.add_argument('--report'); ap.add_argument('--original'); ap.add_argument('--check', action='store_true')
    ap.add_argument('--no-successor', action='store_true', help='(testing) disable the call-site successor pass')
    a = ap.parse_args()
    sys.exit(check(a) if a.check else run(a))
