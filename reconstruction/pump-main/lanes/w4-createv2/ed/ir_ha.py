import sys; sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w4-createv2/scripts'); import ren
def edit(t):
    t=ren.ren(t)
    a='  %v307 = zext i1 %is_holder_reward to i8\n'
    assert t.count(a)==1; t=t.replace(a,'')
    b='  br i1 %is_holder_reward, label %bb14, label %bb15\n'
    assert t.count(b)==1
    return t.replace(b,a+b)
