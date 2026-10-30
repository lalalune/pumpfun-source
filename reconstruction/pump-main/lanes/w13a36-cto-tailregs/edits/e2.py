A='''  %569 = getelementptr inbounds i8, ptr %_300, i64 163
  store i8 %167, ptr %569, align 1
  %_301 = load ptr, ptr %4, align 8, !nonnull !2, !align !3, !noundef !2
  %570 = getelementptr inbounds i8, ptr %_301, i64 165
  %571 = zext i1 %_0.sroa.0.0.off0.i45 to i8
  store i8 %571, ptr %570, align 1
'''
B='''  %570 = getelementptr inbounds i8, ptr %_300, i64 165
  %571 = zext i1 %_0.sroa.0.0.off0.i45 to i8
  store i8 %571, ptr %570, align 1
  %_301 = load ptr, ptr %4, align 8, !nonnull !2, !align !3, !noundef !2
  %cb569 = getelementptr inbounds i8, ptr %_301, i64 163
  store i8 %167, ptr %cb569, align 1
'''
def edit(f):
    assert f.count(A)==1; return f.replace(A,B)
