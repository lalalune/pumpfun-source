import sys,difflib,re
def ab(l):
    l=re.sub(r'r\d+','r',l); l=re.sub(r'[-+]?0x[0-9a-f]+','N',l); l=re.sub(r'\b\d+\b','N',l); return l
o=open(sys.argv[1]).read().splitlines(); c=open(sys.argv[2]).read().splitlines()
A=[ab(x) for x in o]; B=[ab(x) for x in c]
sm=difflib.SequenceMatcher(None,A,B,autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    print('@@ %s orig %d-%d cand %d-%d'%(tag,i1,i2,j1,j2))
    ctx=2
    for x in o[max(0,i1-ctx):i1]: print('  ',x)
    for x in o[i1:i2]: print(' -',x)
    for x in c[j1:j2]: print(' +',x)
