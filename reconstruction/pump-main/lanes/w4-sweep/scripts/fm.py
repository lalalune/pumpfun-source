import re,sys,difflib
# fm.py name... : full-mask (regs, stack offsets, add64 imm on r10 copies, jump offsets) diff line count vs orig
B='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w4-sweep/'
def M(L):
    out=[]
    for x in L:
        x=re.sub(r'([+-]0x[0-9a-f]+)$','J',x) if re.match(r'(ja|j[a-z]+ )',x) else x
        x=re.sub(r'add64 (r\d), -0x[0-9a-f]+',r'add64 \1, -S',x)
        x=re.sub(r'r10 - 0x[0-9a-f]+','r10-S',re.sub(r'\br[0-9]\b','r',x)); out.append(x)
    return out
o=M([l.strip() for l in open(B+'orig-norm.txt') if l.strip()])
for n in sys.argv[1:]:
    c=M([l.strip() for l in open(B+f'irexp/{n}/fn.txt') if l.strip()])
    sm=difflib.SequenceMatcher(None,o,c,autojunk=False)
    nd=sum(max(i2-i1,j2-j1) for t,i1,i2,j1,j2 in sm.get_opcodes() if t!='equal')
    print(n,'fullmask diff',nd,'ratio',round(sm.ratio(),4))
