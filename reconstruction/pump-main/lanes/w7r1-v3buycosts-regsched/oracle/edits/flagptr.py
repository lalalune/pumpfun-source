def edit(f):
    a='  br i1 %5, label %bb11, label %bb8'
    assert a in f
    return f.replace(a,'  %ptrt = icmp eq ptr %0, null\n  br i1 %ptrt, label %bb11, label %bb8')
