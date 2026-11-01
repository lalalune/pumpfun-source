import re
def f(t):
    m=re.search(r'  switch i8 (%_4\d\.sroa\.0\.0\.copyload), label %bb29\.i \[\n    i8 2, label %bb27\.i\n    i8 0, label %bb27\.i\n  \]',t)
    assert m
    return t[:m.start()]+f'  %sw306a = and i8 {m.group(1)}, 1\n  %sw306 = icmp eq i8 %sw306a, 0\n  br i1 %sw306, label %bb27.i, label %bb29.i'+t[m.end():]
EDITS=[f]
