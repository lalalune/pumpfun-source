"""Whole-ELF non-.text identity modulo placement: maps candidate addresses to original ones
(.text via the refined window pairing, data sections by section base) and compares .rel.dyn,
.dynsym, .dynamic, .data.rel.ro. Usage: elfmap.py <unstripped.so> <refined.json>"""
import sys,json,struct,bisect,collections
H='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r3-layout-rodata/reconstruction'
sys.path.insert(0,H+'/harness'); from score import sections
ob=open(H+'/base/original.so','rb').read(); cb=open(sys.argv[1],'rb').read()
OS=sections(ob); CS=sections(cb)
R=json.load(open(sys.argv[2])); P={int(v,16):int(k,16) for k,v in R['pair'].items()}  # cand window start -> orig
cst=sorted(P)
# candidate function extents from score.candidate_functions
from score import candidate_functions
ext={st:l for st,l,n in candidate_functions(sys.argv[1])}
def c2o(a):
    for n,s in CS.items():
        if s['addr'] and s['addr']<=a<s['addr']+s['size']:
            if n=='.text':
                j=bisect.bisect_right(cst,a)-1
                if j<0: return ('text?',a)
                ws=cst[j]
                if ws in ext and a>=ws+ext[ws]: return ('text-unpaired',hex(a))
                return P[ws]+(a-ws)
            return OS[n]['addr']+(a-s['addr'])
    return ('nosec',a)
def sec(b,S,n): s=S[n]; return b[s['offset']:s['offset']+s['size']]
def rels(b,S): r=sec(b,S,'.rel.dyn'); return [struct.unpack_from('<QQ',r,i) for i in range(0,len(r),16)]
o=rels(ob,OS); c=rels(cb,CS)
om=collections.Counter(o); cm=collections.Counter((c2o(off),info) for off,info in c)
print('.rel.dyn entries',len(o),len(c),'orig-only',sum((om-cm).values()),'cand-only',sum((cm-om).values()))
for k,v in list((cm-om).items())[:6]: print('  cand-only',hex(k[0]) if isinstance(k[0],int) else k[0],hex(k[1]),v)
for k,v in list((om-cm).items())[:6]: print('  orig-only',hex(k[0]),hex(k[1]),v)
print('.rel.dyn order equal after mapping:', [ (c2o(a),i) for a,i in c]==o)
def syms(b,S):
    r=sec(b,S,'.dynsym'); return [struct.unpack_from('<IBBHQQ',r,i) for i in range(0,len(r),24)]
os_=syms(ob,OS); cs=syms(cb,CS)
bad=[(x,y) for x,y in zip(os_,cs) if x[:4]!=y[:4] or x[5]!=y[5] or (y[4] and c2o(y[4])!=x[4])]
print('.dynsym',len(os_),len(cs),'mismatch',len(bad)); [print('  ',x,y) for x,y in bad[:5]]
def dyn(b,S):
    r=sec(b,S,'.dynamic'); return [struct.unpack_from('<qQ',r,i) for i in range(0,len(r),16)]
od=dyn(ob,OS); cd=dyn(cb,CS)
for x,y in zip(od,cd):
    if x!=y:
        m=c2o(y[1]) if y[1]>0x1000 else y[1]
        print('  .dynamic tag',x[0],hex(x[1]),hex(y[1]),'mapped-equal' if m==x[1] else 'DIFF')
# per-window relocation counts (orig window of each entry)
ows=sorted(P.values())
def win(a):
    if not isinstance(a,int): return a
    j=bisect.bisect_right(ows,a)-1; return ows[j] if j>=0 else None
oc=collections.Counter(win(a) for a,i in o if OS['.text']['addr']<=a<OS['.text']['addr']+OS['.text']['size'])
cc=collections.Counter(win(c2o(a)) for a,i in c if CS['.text']['addr']<=a<CS['.text']['addr']+CS['.text']['size'])
print('text reloc windows differing:',{hex(k) if isinstance(k,int) else k:(oc[k],cc[k]) for k in set(oc)|set(cc) if oc[k]!=cc[k]})
nt=lambda L,S: collections.Counter(x for x in L if not (S['.text']['addr']<=x[0]<S['.text']['addr']+S['.text']['size']))
print('non-text reloc orig',sum(nt(o,OS).values()),'cand',sum(nt([(c2o(a),i) for a,i in c],OS).values()),'diff',sum((nt(o,OS)-nt([(c2o(a),i) for a,i in c],OS)).values()))
