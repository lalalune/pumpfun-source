import re
def f(t):
    old_bb34=re.search(r'\nbb34\.i:.*?\n  br label %bb50\.i\n',t,re.S).group(0)
    t=t.replace(old_bb34,'\n')
    t=t.replace("""  %_406.sroa.0.0 = phi i64 [ %_406.sroa.0.2, %bb34.i ], [ 2, %bb109.i ], [ 2, %bb38.i118 ], [ 2, %bb44.i119 ]
  %_406.sroa.18.0 = phi i64 [ %_406.sroa.18.2, %bb34.i ], [ %_280.i, %bb109.i ], [ 0, %bb38.i118 ], [ 0, %bb44.i119 ]""",
"""  %_406.sroa.0.0 = phi i64 [ %552, %bb94.i ], [ 2, %bb88.i ], [ 2, %bb92.i ], [ 2, %bb109.i ], [ 2, %bb38.i118 ], [ 2, %bb44.i119 ]
  %_406.sroa.18.0 = phi i64 [ %555, %bb94.i ], [ 0, %bb88.i ], [ %546, %bb92.i ], [ %_280.i, %bb109.i ], [ 0, %bb38.i118 ], [ 0, %bb44.i119 ]""")
    t=t.replace("br i1 %_121.not.not.i, label %bb30.i, label %bb34.i","br i1 %_121.not.not.i, label %bb30.i, label %bb50.i")
    t=t.replace("br i1 %553, label %bb34.i, label %bb94.i","br i1 %553, label %bb50.i, label %bb94.i")
    a=t.index('\nbb94.i:'); b=t.index('br label %bb34.i',a); t=t[:b]+'br label %bb50.i'+t[b+len('br label %bb34.i'):]
    return t
EDITS=[f]
