import sys,os,difflib
T='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a80-cto-stitch12/reconstruction/pump-main/lanes/w14a80-cto-stitch12/tools'; exec(open(T+'/rx.py').read().split('OUT=os.environ')[0])
o=mask(orig_window()); c=mask(open(sys.argv[1],'rb').read())
def offs(t):
    r=[0]
    for x in t: r.append(r[-1]+len(x))
    return r
oo=offs(o); co=offs(c)
sm=difflib.SequenceMatcher(None,o,c,autojunk=False)
ex=[]
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    ex.append((j2-j1)-(i2-i1)); 
    if (j2-j1)-(i2-i1)>=int(sys.argv[2] if len(sys.argv)>2 else 3): print(f'{tag:8s} orig {oo[i1]:05x}-{oo[i2]:05x} ({i2-i1}) cand {co[j1]:05x}-{co[j2]:05x} ({j2-j1}) extra {(j2-j1)-(i2-i1)}')
print('orig',len(o),'cand',len(c))
