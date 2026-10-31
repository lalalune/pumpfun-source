# whole event literal reads ctx.accounts directly (a.  -> ctx.accounts.) inside the literal
import re
def f(s):
    i=s.index('let e=AdminCtoEvent{'); j=s.index('};emit!(e)',i)
    return s[:i]+s[i:j].replace('a.','ctx.accounts.')+s[j:]
EDITS=[f]
