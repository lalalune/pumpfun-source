# mv.py: move a basic block within execute in post-opt m.ll
import re
FN='define internal fastcc' 
def span(t,label):
    a,b=fnspan(t)
    k='\n'+label+':'
    i=t.index(k,a,b)+1; j=t.find('\n\n',i,b)
    if j<0: j=b
    return i,j
def fnspan(t):
    """Span of admin_cto::execute's `define` through its closing `}`. The first
    `@...execute...(` in a module can sit in an earlier caller's body, so a call
    site must never pick the span: the scans then enumerate and move the
    caller's blocks and score them as execute's."""
    m=re.search(r'(?m)^define [^\n]*@_ZN14pump_recovered9admin_cto7execute17h3bd6d7f34f2e30d7E\(',t)
    if m is None: raise ValueError('no definition of admin_cto::execute')
    i=m.start(); j=t.index('\n}\n',i)
    return i,j
def mvend(t,label):
    i,j=span(t,label); a,b=fnspan(t)
    if j==b: return t
    blk=t[i:j]; t=t[:i]+t[j+2:]
    a,b=fnspan(t); return t[:b]+'\n\n'+blk+t[b:]
def mvafter(t,label,after):
    if label==after: return t
    i,j=span(t,label); blk=t[i:j]
    t=t[:i]+t[j+(2 if t[j:j+2]=='\n\n' else 0):]
    a,b=span(t,after); return t[:b]+'\n\n'+blk+t[b:]
