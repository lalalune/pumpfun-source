import sys,re,difflib
o=[l.strip() for l in open(sys.argv[1]) if l.strip()]; c=[l.strip() for l in open(sys.argv[2]) if l.strip()]
def R(s): return re.sub(r'\br\d\b','r',s)
def S(s): return re.sub(r'r10 - 0x[0-9a-f]+','S',s)
def J(s): return re.sub(r'[+-]0x[0-9a-f]+$','OFF',s) if s.startswith('j') else s
for nm,f in [('raw',lambda s:s),('reg',R),('stack',S),('jmp',J),('reg+jmp',lambda s:J(R(s))),('stack+jmp',lambda s:J(S(s))),('all',lambda s:J(S(R(s))))]:
    print(nm, round(difflib.SequenceMatcher(None,[f(x) for x in o],[f(x) for x in c],autojunk=False).ratio(),4))
