import sys,json,re,bisect
sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
M=model(sys.argv[1],sys.argv[2])
seq=[a for a in M.cst]
# full-sequence diff ours vs orig (paired only), print runs
import difflib
ours=[a for a in seq if a in M.inv]; orig=sorted(ours,key=lambda a:M.inv[a])
nm=lambda a: re.sub(r'17h[0-9a-f]{16}E$','',M.names[a])[:100]
tot={}
for op,i1,i2,j1,j2 in difflib.SequenceMatcher(a=ours,b=orig,autojunk=False).get_opcodes():
    if op=='equal': continue
    sz1=sum(M.units[a][0] for a in ours[i1:i2]); sz2=sum(M.units[a][0] for a in orig[j1:j2])
    print(op, f'ours[{i1}:{i2}] {sz1}B', f'orig[{j1}:{j2}] {sz2}B')
    for a in ours[i1:i2][:6]: print('   -',hex(a),hex(M.inv[a]),M.region(a),M.units[a][0],nm(a))
    for a in orig[j1:j2][:6]: print('   +',hex(a),hex(M.inv[a]),M.region(a),M.units[a][0],nm(a))
