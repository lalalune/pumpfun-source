import sys
# irmv.py in.ll out.ll BLOCK AFTER : move IR basic block BLOCK to just after block AFTER (text order only)
t=open(sys.argv[1]).read(); b,a=sys.argv[3],sys.argv[4]
def span(t,name):
    i=t.index('\n'+name+':'); j=t.find('\n\n',i+1)
    return i+1,j+1
i,j=span(t,b); blk=t[i:j]; t=t[:i]+t[j:]
i,j=span(t,a); t=t[:j]+blk+t[j:]
open(sys.argv[2],'w').write(t)
