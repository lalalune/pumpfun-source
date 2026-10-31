# sbs.py fn.bin lo hi: L2-aligned side-by-side listing of orig [lo,hi) vs cand (asm text)
import sys,difflib,re
exec(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a85-cto-s1reload/reconstruction/pump-main/lanes/w14a85-cto-s1reload/tools/fmr.py').read().split('def toks')[0].replace('sys.argv','[0]'))
def toks(raw,l): return [C.mask(t,l) for _,t in C.insns(raw)]
f,dis,lo,hi=sys.argv[1],sys.argv[2],int(sys.argv[3],0),int(sys.argv[4],0)
OT={}
for l in open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a85-cto-s1reload/orig.txt'):
    m=re.match(r'0x([0-9a-f]+)\s+(.*)',l)
    if m: OT[int(m.group(1),16)-0x22a10]=m.group(2).strip()
CT={}
for l in open(dis):
    m=re.match(r'([0-9a-f]{4})\s+(?:[0-9a-f]{2} )+\s*(.*)',l)
    if m: CT[int(m.group(1),16)]=re.sub(r'\s*<.*>','',m.group(2).split('\t')[-1]).strip()
c=open(f,'rb').read(); oi=C.insns(O); ci=C.insns(c)
sm=difflib.SequenceMatcher(None,toks(O,2),toks(c,2),autojunk=False)
for tag,a1,a2,b1,b2 in sm.get_opcodes():
    for k in range(max(a2-a1,b2-b1)):
        oo=oi[a1+k][0] if a1+k<a2 else None; co=ci[b1+k][0] if b1+k<b2 else None
        ref=oo if oo is not None else (oi[a1][0] if a1<len(oi) else 0)
        if not(lo<=ref<hi): continue
        ot=OT.get(oo,'') if oo is not None else ''; ct=CT.get(co,'') if co is not None else ''
        mark=' ' if (tag=='equal' and ot==ct) else ('~' if tag=='equal' else '*')
        print('%s %5s %-36s | %5s %s'%(mark,'%04x'%oo if oo is not None else '',ot,'%04x'%co if co is not None else '',ct))
