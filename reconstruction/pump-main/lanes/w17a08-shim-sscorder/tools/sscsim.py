#!/usr/bin/env python3
"""sscsim.py: exact StackSlotColoring simulator and relabel oracle for admin_cto (experiment only).

Inputs from ONE post-opt module (llc flags as fastbuild; private llc with assertions):
  <d>/ssc.log : -debug-only=stack-slot-coloring (sharing on)   -> intervals, weights, processing order
  <d>/ns.log  : same with -no-stack-slot-sharing                -> SS# -> own FI
  <d>/ns.o    : object built with -no-stack-slot-sharing        -> code with one offset per interval
Colour k (k-th opened colour) sits at -2264-8k (checked on PEI MIR for main and no-share).
BPF has no isLoadFromStackSlot, so RemoveDeadStores is a no-op: colouring changes only spill offsets.

API: S=Sim(d); S.order (base processing order), S.W (weights); S.colour(order)->{ss:k};
     S.relabel({ss:k})->bytes; S.M(bytes)->(M,ratio); S.eval_order(order)->(M,ratio,ncol,bytes)
"""
import re, sys, os, difflib
T6 = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w17a08-shim-sscorder/t6')
sys.path.insert(0, T6)
import oracle

SEG = re.compile(r'\[(\d+)([Berd]),(\d+)([Berd]):\d+\)')

def slot(i, l): return int(i) + 'Berd'.index(l)

def parse(path):
    t = open(path).read()
    i = t.index('Spill slot intervals:'); j = t.index('Color spill slot intervals:', i)
    iv = {}
    for line in t[i:j].splitlines():
        m = re.match(r'SS#(\d+) (.*)weight:(\S+)$', line)
        if not m: continue
        segs = [(slot(a, b), slot(c, d)) for a, b, c, d in SEG.findall(m.group(2))]
        iv[int(m.group(1))] = (segs, float(m.group(3)))
    asg = [(int(a), int(b)) for a, b in re.findall(r'Assigning fi#(\d+) to fi#(\d+)', t[j:])]
    return iv, asg

def overlaps(a, b):
    i = j = 0
    while i < len(a) and j < len(b):
        s1, e1 = a[i]; s2, e2 = b[j]
        if s1 < e2 and s2 < e1: return True
        if e1 <= e2: i += 1
        else: j += 1
    return False

class Sim:
    def __init__(self, d, fnpat=oracle.KEEP):
        self.iv, asg = parse(d + '/ssc.log')
        self.order = [a for a, b in asg]                     # processing order (weight desc, FI asc)
        self.base_colour_fi = dict(asg)
        self.W = {s: self.iv[s][1] for s in self.iv}
        self.fis = sorted(self.iv)                           # spill FIs = colour FIs in opening order
        ss = sorted(self.iv)
        self.OV = {s: set() for s in ss}
        for x in range(len(ss)):
            for y in range(x + 1, len(ss)):
                if overlaps(self.iv[ss[x]][0], self.iv[ss[y]][0]):
                    self.OV[ss[x]].add(ss[y]); self.OV[ss[y]].add(ss[x])
        _, nsasg = parse(d + '/ns.log')
        self.ns_off = {}                                      # ns offset -> SS#
        for a, b in nsasg: self.ns_off[-2264 - 8 * (b - 178)] = a
        self.ns = oracle.elf_fn(d + '/ns.o', fnpat)
        self.O = oracle.mask(oracle.orig_window())
        self.rank = {s: i for i, s in enumerate(self.order)}
        # spill-access instruction positions in ns
        self.acc = []
        b = self.ns; i = 0
        while i < len(b):
            op = b[i]; n = 16 if op == 0x18 else 8
            if op in (0x79, 0x7b, 0x7a, 0x71, 0x69, 0x61, 0x73, 0x6b, 0x63):
                regs = b[i + 1]; dst, src = regs & 15, regs >> 4
                base = src if op in (0x79, 0x71, 0x69, 0x61) else dst
                off = int.from_bytes(b[i + 2:i + 4], 'little', signed=True)
                if base == 10 and off in self.ns_off: self.acc.append((i, self.ns_off[off]))
            i += n

    def sort(self, W):
        return sorted(self.order, key=lambda s: (-W[s], self.rank[s]))

    def colour(self, order):
        cols = []; k = {}
        for s in order:
            ov = self.OV[s]
            for c, mem in enumerate(cols):
                if not (ov & mem): mem.add(s); k[s] = c; break
            else:
                cols.append({s}); k[s] = len(cols) - 1
        return k

    def relabel(self, k):
        b = bytearray(self.ns)
        for i, s in self.acc:
            b[i + 2:i + 4] = (-2264 - 8 * k[s]).to_bytes(2, 'little', signed=True)
        return bytes(b)

    def M(self, raw):
        c = oracle.mask(raw)
        sm = difflib.SequenceMatcher(None, self.O, c, autojunk=False)
        m = sum(x.size for x in sm.get_matching_blocks())
        return m, round(2 * m / (len(self.O) + len(c)), 5)

    def eval_order(self, order):
        k = self.colour(order); b = self.relabel(k); m, r = self.M(b)
        return m, r, max(k.values()) + 1, b

    def wset(self, spec):
        """spec 'ss:=w,ss:+d' like the private llc's SSC_WSET; returns the new processing order."""
        W = dict(self.W)
        for tok in filter(None, spec.split(',')):
            a, v = tok.split(':'); s = int(a)
            W[s] = W[s] + float(v[1:]) if v[0] == '+' else float(v[1:])
        return self.sort(W)

if __name__ == '__main__':
    d = sys.argv[1]
    S = Sim(d)
    m, r, nc, b = S.eval_order(S.order)
    main = oracle.elf_fn(d + '/main.o', oracle.KEEP) if os.path.exists(d + '/main.o') else None
    print({'M': m, 'ratio': r, 'ncol': nc, 'bytes': len(b), 'eq_main': (b == main) if main else None,
           'n_iv': len(S.iv), 'n_acc': len(S.acc)})
