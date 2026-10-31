import difflib,re,sys
def ld(f): return [l.split(' ',1)[1].strip() for l in open(f)]
a=ld(sys.argv[1]); b=ld(sys.argv[2])
J=lambda x: re.sub(r'[+-]0x[0-9a-f]+$','J',x) if x.startswith('j') else x
sm=difflib.SequenceMatcher(None,[J(x) for x in a],[J(x) for x in b],autojunk=False)
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op!='equal': print(op,hex(i1*8),i2-i1,hex(j1*8),j2-j1, a[i1:i2][:5], b[j1:j2][:5])
