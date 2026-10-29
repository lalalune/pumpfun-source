import sys,difflib,re
def ab(l):
    l=re.sub(r'r\d+','r',l); l=re.sub(r'[-+]?0x[0-9a-f]+','N',l); l=re.sub(r'\b\d+\b','N',l); return l
o=open(sys.argv[1]).read().splitlines(); c=open(sys.argv[2]).read().splitlines()
ao=[ab(x) for x in o]; ac=[ab(x) for x in c]
sm=difflib.SequenceMatcher(None,ao,ac,autojunk=False)
print('abstract ratio',round(sm.ratio(),5))
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    print(f'== {tag} orig[{i1}:{i2}] cand[{j1}:{j2}]')
    if len(sys.argv)>3:
        for x in o[i1:i2]: print('  -',x)
        for x in c[j1:j2]: print('  +',x)
