import re,difflib,sys
o=open(sys.argv[1]).read().splitlines(); c=open(sys.argv[2]).read().splitlines()
def mask(s):
    s=re.sub(r'\br\d\b','r',s); s=re.sub(r'r10 - 0x[0-9a-f]+','S',s)
    if s.startswith('j'): s=re.sub(r'[+-]0x[0-9a-f]+$','OFF',s)
    return s
M=len(sys.argv)>3
mo=[mask(x) if M else x for x in o]; mc=[mask(x) if M else x for x in c]
sm=difflib.SequenceMatcher(None,mo,mc,autojunk=False)
B=[0]*20
for tg,i1,i2,j1,j2 in sm.get_opcodes():
    if tg=='equal': continue
    n=max(i2-i1,j2-j1)
    B[min(i1//50,19)]+=n
print(' '.join(f'{i*50}:{b}' for i,b in enumerate(B)))
