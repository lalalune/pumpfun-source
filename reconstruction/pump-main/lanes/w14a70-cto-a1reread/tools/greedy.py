import sys,os,multiprocessing as mp,struct,bisect
# greedy.py <fn.bin> <steps>: repeatedly add the best pure +8 pad (shift.py model), print M per step
D=os.path.dirname(os.path.abspath(__file__)); src=sys.argv[1]; steps=int(sys.argv[2]); G={}
def mmw(a): return G['mm'](a)
for s in range(steps):
    sys.argv=['shift.py',src]; G.clear(); G.update({'__name__':'lib','__file__':D+'/shift.py'})
    exec(open(D+'/shift.py').read(),G)
    ins=G['ins']; slot=G['slot']; isj=G['isj']; starts=set()
    for k,b in enumerate(ins):
        if isj(b):
            off=struct.unpack('<h',bytes(b[2:4]))[0]; t=slot[k]+len(b)//8+off
            starts.add(bisect.bisect_left(slot,t)); starts.add(k+1)
    starts=sorted(x for x in starts if 0<x<len(ins))
    base=G['M'](G['build']())
    with mp.get_context('fork').Pool(4) as P: R=P.map(mmw,[(a,None) for a in starts])
    R.sort(key=lambda z:-z[2]); a,_,m=R[0]
    print('step',s,'base',base,'best +8 at %05x'%(slot[a]*8),'M',m,'top',[('%05x'%(slot[x]*8),y) for x,_,y in R[:6]],flush=True)
    out=src[:-4]+'.p%d.bin'%s; open(out,'wb').write(G['build'](a,None)); src=out
