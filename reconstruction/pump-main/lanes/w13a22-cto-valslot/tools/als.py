import re,sys
def als(p):
    t=open(p).read(); m=re.search(r'define [^\n]*admin_cto7execute[^\n]*\n',t); s=m.end(); e=t.index('\n}\n',s)
    return [re.match(r'\s*%(\S+) = alloca (.*?), align',l).groups() for l in t[s:e].split('\n') if ' = alloca ' in l]
a=als(sys.argv[1]); b=als(sys.argv[2])
import difflib
for op,i1,i2,j1,j2 in difflib.SequenceMatcher(None,[x[0] for x in a],[x[0] for x in b],autojunk=False).get_opcodes():
    if op!='equal': print(op,a[i1:i2],'->',b[j1:j2])
print(len(a),len(b))
