# mv.py: move a basic block within execute in post-opt m.ll
import re
FN='define internal fastcc' 
def span(t,label):
    k='\n'+label+':'
    i=t.index(k)+1; j=t.index('\n\n',i)
    return i,j
def fnspan(t):
    i=t.index('@_ZN14pump_recovered9admin_cto7execute17h3bd6d7f34f2e30d7E(')
    i=t.rindex('\ndefine',0,i)+1; j=t.index('\n}\n',i)
    return i,j
def mvend(t,label):
    i,j=span(t,label); blk=t[i:j]; t=t[:i]+t[j+2:]
    a,b=fnspan(t); return t[:b]+'\n\n'+blk+t[b:]
def mvafter(t,label,after):
    i,j=span(t,label); blk=t[i:j]; t=t[:i]+t[j+2:]
    a,b=span(t,after); return t[:b]+'\n\n'+blk+t[b:]
