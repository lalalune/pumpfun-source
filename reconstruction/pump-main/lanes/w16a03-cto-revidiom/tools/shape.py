"""Shape normalisation + n-gram index over the original Pump Main .text.
Shapes keep opcode, base class (fp / reg) and non-fp memory offsets; registers are alpha-renamed
inside each n-gram (so dataflow is kept), fp offsets and immediates are masked."""
import re,sys,json,bisect,os
sys.path.insert(0,os.path.dirname(__file__))
from odis import load
OUT='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a03-cto-revidiom'
BASE='/Users/shawwalters/.cache/pumpfun-reconstruction/w11/current-baseline'
CTO=0x22a10; CTO_END=0x22a10+27400
RX=re.compile(r'r(\d+)')
def parse(t):
    """-> (mn, ops list) ops: ('r',n) ('m',basereg,off) ('i',val) ('j',off)"""
    parts=t.split(None,1); mn=parts[0]; ops=[]
    if len(parts)>1:
        s=parts[1]
        # split on commas not inside []
        toks=re.findall(r'\[[^\]]*\]|[^,\s][^,]*',s)
        for x in toks:
            x=x.strip()
            m=re.match(r'\[r(\d+)\s*([+-])\s*(0x[0-9a-f]+|\d+)\]',x)
            if m:
                off=int(m.group(3),0)*(1 if m.group(2)=='+' else -1); ops.append(('m',int(m.group(1)),off)); continue
            m=re.match(r'^r(\d+)$',x)
            if m: ops.append(('r',int(m.group(1)))); continue
            m=re.match(r'^([+-]?)(0x[0-9a-f]+|\d+)$',x)
            if m:
                v=int(m.group(2),0)*(-1 if m.group(1)=='-' else 1)
                if mn in('ja',) or (mn.startswith('j') and len(ops)>=1 and x.startswith(('+','-')) and False):
                    ops.append(('j',v))
                else: ops.append(('i',v))
                continue
            ops.append(('?',x))
    # jumps: last operand is offset
    if mn.startswith('j') and ops and ops[-1][0]=='i': ops[-1]=('j',ops[-1][1])
    return mn,ops
def shape_seq(insns, keep_fp=False, keep_imm=False, keep_off=True):
    """alpha-rename registers over a sequence; return tuple of shape strings"""
    ren={}; out=[]
    def R(n):
        if n==10: return 'fp'
        if n not in ren: ren[n]='abcdefghijk'[len(ren)] if len(ren)<11 else 'z'
        return ren[n]
    for mn,ops in insns:
        s=[]
        for o in ops:
            if o[0]=='r': s.append(R(o[1]))
            elif o[0]=='m':
                if o[1]==10: s.append(f'[fp{o[2]:+#x}]' if keep_fp else '[fp]')
                else: s.append(f'[{R(o[1])}{o[2]:+#x}]' if keep_off else f'[{R(o[1])}]')
            elif o[0]=='i':
                if mn=='call': s.append('fn')
                elif keep_imm or mn.startswith(('and','lsh','rsh','arsh')): s.append(f'{o[1]:#x}')
                elif mn.startswith('j') : s.append(f'{o[1]:#x}' if abs(o[1])<4 else 'k')
                else: s.append('k' if o[1] not in (0,1) else str(o[1]))
            elif o[0]=='j': s.append('@')
            else: s.append('?')
        out.append(mn+' '+','.join(s))
    return tuple(out)
_cache={}
def orig():
    if 'o' not in _cache:
        rows,_=load(f'{OUT}/dis/orig.dis'); _cache['o']=[(a,t,parse(t)) for a,t in rows]
    return _cache['o']
def main():
    if 'm' not in _cache:
        rows,syms=load(f'{OUT}/dis/main.dis'); _cache['m']=([(a,t,parse(t)) for a,t in rows],syms)
    return _cache['m']
def windows():
    if 'w' not in _cache:
        d=json.load(open(f'{BASE}/score.json'))['windows']
        ws=sorted((int(k),v['bytes'],v['symbols'],v['normalized'],v['raw']) for k,v in d.items())
        _cache['w']=ws
    return _cache['w']
def win_of(addr):
    ws=windows(); starts=[w[0] for w in ws]
    i=bisect.bisect_right(starts,addr)-1
    if i<0: return None
    w=ws[i]
    return w if addr<w[0]+w[1] else None
