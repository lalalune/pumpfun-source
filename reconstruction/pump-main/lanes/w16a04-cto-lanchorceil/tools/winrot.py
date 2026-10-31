#!/usr/bin/env python3
"""winrot.py <fn.bin|rxname>...: window-rotation check for the 13 spill offsets -2264..-2360 (experiment only).
For each window offset, align the frame-masked tokens of the original and the candidate (relab.votes) and take the
original offset that the candidate offset's aligned mem insns vote for most. A slot is 'rotated' when its majority vote
differs from main's (baseline unstripped.so) majority vote for the same offset. Prints rot count and per-slot votes."""
import sys,os,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import relab as R
W=list(range(-2264,-2361,-8))
def maj(b):
    V=R.votes(b,set(W)); out={}
    for y in W:
        d=V.get(y,{})
        out[y]=max(d,key=d.get) if d else None
    return out,V
BS=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
_main=None
def main_maj():
    global _main
    if _main is None: _main=maj(R.g['elf_fn'](BS,R.g['KEEP']))[0]
    return _main
def rot(b):
    mm=main_maj(); cm,V=maj(b)
    diff=[y for y in W if cm[y]!=mm[y]]
    return len(diff),diff,cm
if __name__=='__main__':
    O=os.path.dirname(T)
    for a in sys.argv[1:]:
        p=a if a.endswith('.bin') else f'{O}/rx/{a}/fn.bin'
        n,diff,cm=rot(open(p,'rb').read())
        print(json.dumps({'n':a,'rot':n,'slots':diff,'maj':{str(k):v for k,v in cm.items()},'main':{str(k):v for k,v in main_maj().items()}}))
