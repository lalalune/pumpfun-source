import re
def edit(t):
    s = t.index('\nbb117:'); hdr_end = t.index('\n', s + 1)
    t = t[:hdr_end] + '\n  %hv.m = phi ptr [ %h.val, %bb88 ], [ %h.val, %bb116 ]' + t[hdr_end:]
    b = t.index('\nbb147:'); be = t.index('\n\n', b + 2)
    blk = re.sub(r'%h\.val\b(?!\.)', '%hv.m', t[b:be])
    return t[:b] + blk + t[be:]
