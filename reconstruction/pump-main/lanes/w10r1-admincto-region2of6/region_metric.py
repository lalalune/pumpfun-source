import sys,re,difflib,json
sys.argv_save=sys.argv; sys.argv=[sys.argv[0]]
sys.path.insert(0,'./worktrees/w10r1-admincto-region2of6/reconstruction/harness')
import win
args=sys.argv_save[1:]
so=args[0]; K=int(args[1]) if len(args)>1 else 2; NR=6
st=0x22a10
w=next(x for x in win.original_windows() if x['start']==st)
cand=win.Cand(so)
cs=[(s,n,nm) for (s,n,nm) in cand.funcs if re.search(r'admin_cto::execute$',win.demangle(nm))]
s,n,nm=cs[0]
oi=win.insns(w['raw'],st,win.ORIG_SECS); ci=win.insns(cand.fn(s,n),s,cand.secs)
ot=[x[2] for x in oi]; ct=[x[2] for x in ci]
sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False)
lo=st+(K-1)*w['bytes']//NR; hi=st+K*w['bytes']//NR
idx=[i for i,x in enumerate(oi) if lo<=x[0]<hi]
i0,i1=idx[0],idx[-1]+1
eq=0; m={}
for b in sm.get_matching_blocks():
  for k in range(b.size): m[b.a+k]=b.b+k
eq=sum(1 for i in range(i0,i1) if i in m)
js=[m[i] for i in range(i0,i1) if i in m]
# local: candidate span = between mapped ends
j0=min(js) if js else 0; j1=max(js)+1 if js else 0
loc=difflib.SequenceMatcher(None,ot[i0:i1],ct[j0:j1],autojunk=False).ratio()
# opcode-only structural
def op(t): return bytes([t[0]])
oo=[x[1][0] for x in oi[i0:i1]]
# best structural local: opcode seq vs candidate opcode in same span
co=[x[1][0] for x in ci[j0:j1]]
sloc=difflib.SequenceMatcher(None,oo,co,autojunk=False).ratio()
print(json.dumps(dict(bytes=n,ratio=round(sm.ratio(),5),region=K,orig_range=[hex(lo),hex(hi)],slots=i1-i0,eq_in_region=eq,frac=round(eq/(i1-i0),4),cand_span=[hex(ci[j0][0]) if js else None,hex(ci[j1-1][0]) if js else None],local_ratio=round(loc,4),local_opcode_ratio=round(sloc,4))))
