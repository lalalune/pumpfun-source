#!/usr/bin/env python3
"""Diff one ORIGINAL Fees window against a CANDIDATE function (masked call/lddw/frame operands).

usage: python3 -I fndiff.py ORIG_ADDR CANDIDATE_SYMBOLS.so [--symbol SUBSTR] [--context N] [--full] [--raw]

The candidate function is chosen by --symbol substring (mangled-name match) or by the target table below.
Prints sizes, a SequenceMatcher ratio over masked instruction text, the differing-instruction span and a
unified diff. --raw keeps stack offsets and branch targets. Exit 0 iff the masked streams are identical.
"""
import argparse, difflib, importlib.util, sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
def module(n, p):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
dis = module('fees_dis', HERE / 'dis.py')
w = dis.w
ORIG = (Path('/Users/shawwalters/fees100-run/base') / 'evidence/original/pump_fees/deployed.so').read_bytes()
TARGETS = {
    147944: '19pump_fees_candidate22crank_donation_fee_pda',
    163920: 'create_donation_fee_pda6create',
    120816: 'buyback13sweep_buyback',
    76384: 'extend_fee_config7execute',
    243184: 'admit_associated_token_account',
    249264: 'withdraw7execute',
    137280: 'claim_v2',
}
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('addr', type=lambda x: int(x, 0)); ap.add_argument('candidate')
    ap.add_argument('--symbol'); ap.add_argument('--context', type=int, default=3)
    ap.add_argument('--full', action='store_true'); ap.add_argument('--raw', action='store_true')
    a = ap.parse_args()
    cand = Path(a.candidate).read_bytes()
    key = a.symbol or TARGETS.get(a.addr)
    funcs = [f for f in w.m.functions(cand) if key and key in (f['name'] or '')]
    if not funcs:
        sys.exit(f'no candidate function matching {key!r}')
    f = funcs[0]
    cnames = dis.names_for(cand)
    onames = dis.names_for(ORIG, cand)
    mask = not a.raw
    o = [t for _, t in dis.listing(ORIG, a.addr, onames, mask)]
    c = [t for _, t in dis.listing(cand, f['address'], cnames, mask)]
    sm = difflib.SequenceMatcher(None, o, c, autojunk=False)
    diff_ins = sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != 'equal')
    owin = {r['address']: r for r in dis._meas.windows(ORIG)}[a.addr]
    print(f'original {a.addr} {owin["bytes"]}B {len(o)} insns | candidate {f["name"][:90]} @{f["address"]} {len(c)} insns')
    print(f'ratio {sm.ratio():.4f}  differing-insn-span {diff_ins}  identical={o == c}')
    for line in difflib.unified_diff(o, c, 'original', 'candidate', n=10**6 if a.full else a.context, lineterm=''):
        print(line)
    return 0 if o == c else 1
if __name__ == '__main__':
    sys.exit(main())
