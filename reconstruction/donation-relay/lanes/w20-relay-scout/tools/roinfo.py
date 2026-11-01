import sys,os,re,difflib
sys.path.insert(0,os.path.expanduser('~/.cache/pumpfun-reconstruction/relay/rea'))
from relayfn import Elf
a=Elf(sys.argv[1]);b=Elf(sys.argv[2])
sa=a.sec['.rodata'];sb=b.sec['.rodata']
ra=a.b[sa['off']:sa['off']+sa['size']];rb=b.b[sb['off']:sb['off']+sb['size']]
print(len(ra),len(rb))
for m in difflib.SequenceMatcher(None,ra,rb,autojunk=False).get_opcodes() if len(ra)<40000 else []:
    if m[0]!='equal':
        print(m[0],hex(m[1]),hex(m[2]),hex(m[3]),hex(m[4]),ra[max(0,m[1]-30):m[2]+10],rb[max(0,m[3]-30):m[4]+10])
