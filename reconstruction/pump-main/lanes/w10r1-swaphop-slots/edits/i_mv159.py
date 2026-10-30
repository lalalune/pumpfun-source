import re
def edit(t):
    s = t.index('\nbb159:'); e = t.index('\nbb172:', s)
    blk = t[s:e]
    t = t[:s] + t[e:]
    a = "  br i1 %switch232, label %bb159, label %bb172\n"
    i = t.index(a) + len(a)
    return t[:i] + blk.lstrip('\n') + '\n' + t[i:]
