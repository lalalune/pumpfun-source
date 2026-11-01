# vw.py edits (for rx.py): V-time (pre-opt) branch weights on validate's 306 test (`switch` on new's tag in bb23).
# env VW="some:none" (e.g. 1:2 = None/error twice as likely). Experiment only: no source form.
import re,os
def f(t):
    i=t.index(re.search(r'define [^\n]*admin_cto8validate',t).group(0)); j=t.index('\n}\n',i); v=t[i:j]
    m=re.search(r'\n  %\w+ = load i8, ptr %new, align 1[^\n]*\n  %\w+ = trunc i8 %\w+ to i1\n  %(\w+) = zext i1 %\w+ to i64\n  switch i64 %(\w+), label %(\w+) \[\n    i64 1, label %(\w+)\n    i64 0, label %(\w+)\n  \]',v)
    assert m and m.group(1)==m.group(2), 'switch306'
    s,n=os.environ.get('VW','1:2').split(':')
    v=v[:m.end()]+', !prof !9100'+v[m.end():]
    return t[:i]+v+t[j:]+f'\n!9100 = !{{!"branch_weights", i32 0, i32 {s}, i32 {n}}}\n'
EDITS=[f]
