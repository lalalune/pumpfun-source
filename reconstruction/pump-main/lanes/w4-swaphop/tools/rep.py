# rep.py FILE : apply REPL env pairs: python list of (old,new)
import sys,os,ast
f=sys.argv[1]; t=open(f).read(); n0=t.count('\n')
for a,b in ast.literal_eval(open(os.environ['REPL']).read()):
    assert t.count(a)==1,(a,t.count(a)); t=t.replace(a,b)
assert t.count('\n')==n0,'line count changed'
open(f,'w').write(t)
