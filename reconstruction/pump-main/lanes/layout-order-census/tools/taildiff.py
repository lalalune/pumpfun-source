import sys; sys.path.insert(0,sys.argv[1])
import fastmodel as F, difflib, re
OUT=sys.argv[2]
M=F.Model(OUT+'/out/main2/unstripped.so',OUT+'/analysis/m2-refined.json')
ra=[a for a in M.cst if M.names[a]=='__rust_alloc'][0]
ours=[a for a in M.cst if a>=ra and M.region(a)=='L']
orig=sorted([a for a in M.inv if M.region(a)=='L' and M.inv[a]>=M.inv[ra]],key=lambda a:M.inv[a])
nm=lambda a: re.sub(r'17h[0-9a-f]{16}E$','',M.names[a])[:110]
print(len(ours),len(orig))
sm=difflib.SequenceMatcher(a=ours,b=orig,autojunk=False)
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op=='equal': print(f'= {i2-i1} units ({nm(ours[i1])[:50]} .. {nm(ours[i2-1])[:50]})'); continue
    for a in ours[i1:i2]: print(f'- ours {a:#x} orig {M.inv.get(a,0):#x} {M.units[a][0]} {nm(a)}')
    for a in orig[j1:j2]: print(f'+ orig {M.inv[a]:#x} ours {a:#x} {M.units[a][0]} {nm(a)}')
