# thread transfer_vault_tokens Ok straight to the post-test block bb82 (orig 0x60f0 -> 0x3c68)
SX='_ZN14pump_recovered9admin_cto7execute5sweep17h9943ff4781c7e018E.exit'
def edit(f):
    a='  br i1 %538, label %bb51.i, label %bb107.i\n'; assert f.count(a)==1
    f=f.replace(a,'  br i1 %538, label %bb82, label %bb107.i\n')
    b=', [ 2, %bb106.i ]'; assert f.count(b)==1; f=f.replace(b,'')
    c=', [ %_251.i, %bb106.i ]'; assert f.count(c)==1; f=f.replace(c,'')
    d='  %_90.sroa.0.0 = phi i64 [ 0, %bb32 ], [ %_386.sroa.19.3, %'+SX+' ]\n'; assert f.count(d)==1
    f=f.replace(d,'  %_90.sroa.0.0 = phi i64 [ 0, %bb32 ], [ %_386.sroa.19.3, %'+SX+' ], [ %_251.i, %bb106.i ]\n')
    f=f.replace('bb51.i:                                           ; preds = %bb89.i108, %bb85.i, %bb45.i102, %bb39.i101, %bb106.i, %bb91.i','bb51.i:                                           ; preds = %bb89.i108, %bb85.i, %bb45.i102, %bb39.i101, %bb91.i')
    return f
