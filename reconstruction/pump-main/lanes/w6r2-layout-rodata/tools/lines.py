# lines.py so symregex : list (offset,line) for path lddw followed by line immediates in the function
import sys,re,struct
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r2-layout-rodata/reconstruction/harness')
from score import candidate_functions, sections
b=open(sys.argv[1],'rb').read(); S=sections(b); t=S['.text']
for st,l,n in candidate_functions(sys.argv[1]):
    if re.search(sys.argv[2],n):
        o=st-t['addr']+t['offset']; code=b[o:o+l]; out=[]
        for i in range(0,l,8):
            op=code[i]; imm=struct.unpack_from('<i',code,i+4)[0]
            if op in (0x62,0x7a,0xb7,0xb4) and 280<=imm<=770 : out.append((hex(i),imm))
        print(n[:60],l,out); break
