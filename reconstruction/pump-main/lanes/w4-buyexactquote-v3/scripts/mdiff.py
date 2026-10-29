import sys,re,difflib
o=[l.strip() for l in open(sys.argv[1]) if l.strip()]; c=[l.strip() for l in open(sys.argv[2]) if l.strip()]
def M(s):
    s=re.sub(r'\br\d\b','r',s); s=re.sub(r'r10 - 0x[0-9a-f]+','S',s)
    return re.sub(r'[+-]0x[0-9a-f]+$','OFF',s) if s.startswith('j') else s
mo=[M(x) for x in o]; mc=[M(x) for x in c]
sm=difflib.SequenceMatcher(None,mo,mc,autojunk=False)
for tg,i1,i2,j1,j2 in sm.get_opcodes():
    if tg=='equal': continue
    print(f'--- {tg} orig[{i1}:{i2}] cand[{j1}:{j2}]')
    for k in range(i1,min(i2,i1+12)): print('  < ',o[k])
    for k in range(j1,min(j2,j1+12)): print('  > ',c[k])
