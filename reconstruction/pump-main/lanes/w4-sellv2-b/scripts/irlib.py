import re
FN='define hidden { i64, ptr } @_ZN14pump_recovered14pump_recovered7sell_v2'
def split(t):
    i=t.index(FN); j=t.index('\n}\n',i)
    body=t[i:j+1]
    # blocks: header line then lines until blank line
    parts=re.split(r'\n\n',body)
    return t[:i],parts,t[j+1:]
def label(p):
    m=re.match(r'^("?[^\s:]+"?):',p)
    return m.group(1) if m else None
def join(pre,parts,post): return pre+'\n\n'.join(parts)+post
def move_before(t,blk,before):
    pre,parts,post=split(t)
    L=[label(p) for p in parts]
    a=L.index(blk); p=parts.pop(a); L.pop(a)
    b=L.index(before); parts.insert(b,p)
    return join(pre,parts,post)
def move_after(t,blk,after):
    pre,parts,post=split(t)
    L=[label(p) for p in parts]
    a=L.index(blk); p=parts.pop(a); L.pop(a)
    b=L.index(after); parts.insert(b+1,p)
    return join(pre,parts,post)
def zero_rent(t):
    a='@_ZN14pump_recovered6buy_v215native_payments18ensure_rent_exempt17h8d931a266c748eedE(i64 poison,'
    i=t.index(FN); j=t.index(a,i)
    return t[:j]+a.replace('poison','0')+t[j+len(a):]
def named(t):
    i=t.index(FN); j=t.index('\n}\n',i)
    b=t[i:j+1]
    b=re.sub(r'%(\d+)\b',r'%v\1',b); b=re.sub(r'(?m)^(\d+):',r'v\1:',b)
    return t[:i]+b+t[j+1:]
_s=split
def split(t): return _s(named(t) if '%v0' not in t[t.index(FN):t.index(FN)+400000] else t)
