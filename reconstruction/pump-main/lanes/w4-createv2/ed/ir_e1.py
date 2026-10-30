import os
def edit(t):
    a='  %_237 = load ptr, ptr %284, align 8, !nonnull !2, !align !3, !noundef !2\n'
    assert t.count(a)==1
    t=t.replace(a,'')
    i=t.index('define internal fastcc void @_ZN14pump_recovered9create_v27execute') if 'define internal fastcc void @_ZN14pump_recovered9create_v27execute' in t else t.index('create_v27execute')
    head,body=t[:i],t[i:]
    body=body.replace('%_237)', '%%%s)'%os.environ.get('E1','_233.val')).replace('%_237,','%%%s,'%os.environ.get('E1','_233.val'))
    return head+body
