import re
SW='define internal void @_ZN14pump_recovered9admin_cto7execute5sweep17h9943ff4781c7e018E('
def in_sweep(f):
    def g(t):
        i=t.index(SW); j=t.index('\n}\n',i)
        return t[:i]+f(t[i:j])+t[j:]
    return g
def drop_lt_in_blocks(blocks, which=None):
    """remove lifetime.end calls inside the named blocks (optionally only for allocas in which)"""
    def f(s):
        out=[];cur=None
        for l in s.split('\n'):
            m=re.match(r'^([\w.]+):',l)
            if m: cur=m.group(1)
            if cur in blocks and 'llvm.lifetime.end' in l:
                if which is None or re.search(r'ptr %('+'|'.join(which)+r')\)',l): continue
            out.append(l)
        return '\n'.join(out)
    return in_sweep(f)
