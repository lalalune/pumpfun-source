import sys,re,difflib; sys.path.insert(0,sys.argv[1]+'/scripts')
from m13 import *
M=model(sys.argv[2],sys.argv[3])
nm=lambda a: re.sub(r'17h[0-9a-f]{16}E$','',M.names[a])[:120]
ours=[a for a in M.cst if a in M.inv and M.region(a)=='L']
orig=sorted(ours,key=lambda a:M.inv[a])
for op,i1,i2,j1,j2 in difflib.SequenceMatcher(a=ours,b=orig,autojunk=False).get_opcodes():
    if op=='equal': print(f'= {i2-i1} [{M.inv[ours[i1]]:#x}] ({nm(ours[i1])[:70]} .. {nm(ours[i2-1])[:70]})'); continue
    for a in ours[i1:i2]: print(f'- {M.inv[a]:#x} {M.units[a][0]} {nm(a)}')
    for a in orig[j1:j2]: print(f'+ {M.inv[a]:#x} {M.units[a][0]} {nm(a)}')
