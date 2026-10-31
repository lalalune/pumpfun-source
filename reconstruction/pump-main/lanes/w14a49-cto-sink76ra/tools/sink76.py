import sys
# sink76.py in.ll out.ll : move bb76's target-piece memcpys/lifetime.ends into bb22 (non-shared) and a new bb19h block on
# the bb19->bb26 (shared+holder) edge; the bb21 (shared non-holder) path overwrites target, so it gets none (original-like).
t=open(sys.argv[1]).read()
i=t.index('\nbb76:'); j=t.index('br i1 %shared.sroa.0.0.off0, label %bb19, label %bb22',i)
lines=t[i:j].split('\n')
keep=[l for l in lines if not ('memcpy' in l or 'lifetime.end' in l)]
moved=[l for l in lines if ('memcpy' in l or 'lifetime.end' in l)]
t=t[:i]+'\n'.join(keep)+t[j:]
k=t.index('\nbb22:'); e=t.index('\n',k+1); t=t[:e+1]+'\n'.join(moved)+'\n'+t[e+1:]
t=t.replace('br i1 %_0.sroa.0.0.off0.i, label %bb26, label %bb21','br i1 %_0.sroa.0.0.off0.i, label %bb19h, label %bb21',1)
k=t.index('\nbb19:'); e=t.index('\n\n',k+1)
t=t[:e+1]+'\nbb19h:                                             ; preds = %bb19\n'+'\n'.join(moved)+'\n  br label %bb26\n'+t[e+1:]
k=t.index('\nbb26:'); e=t.index('\n\n',k+1); b=t[k:e]
b=b.replace(', %bb19 ]',', %bb19h ]').replace('preds = %bb19,','preds = %bb19h,')
# bb21 still needs lifetime.end of the validate pieces and _48.sroa.11; add them (no copies)
t=t[:k]+b+t[e:]
k=t.index('\nbb21:'); e=t.index('\n',k+1)
ends=[l for l in moved if 'lifetime.end' in l]
t=t[:e+1]+'\n'.join(ends)+'\n'+t[e+1:]
open(sys.argv[2],'w').write(t)
