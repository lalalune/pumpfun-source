"""Diff of our L-block order against the original (difflib opcodes). ldiff.py <cand.so> <refined.json>"""
import sys,re,difflib; sys.path.insert(0,__file__.rsplit('/',1)[0])
import fastmodel as F
M=F.Model(sys.argv[1],sys.argv[2])
nm=lambda a: re.sub(r'17h[0-9a-f]{16}E$','',M.names[a])[:110]
ours=[a for a in M.cst if a in M.inv and M.region(a)=='L']
orig=sorted(ours,key=lambda a:M.inv[a])
for op,i1,i2,j1,j2 in difflib.SequenceMatcher(a=ours,b=orig,autojunk=False).get_opcodes():
    if op=='equal': print(f'= {i2-i1} ({nm(ours[i1])[:60]} .. {nm(ours[i2-1])[:60]})'); continue
    for a in ours[i1:i2]: print(f'- {M.inv[a]:#x} {M.units[a][0]} {nm(a)}')
    for a in orig[j1:j2]: print(f'+ {M.inv[a]:#x} {M.units[a][0]} {nm(a)}')
