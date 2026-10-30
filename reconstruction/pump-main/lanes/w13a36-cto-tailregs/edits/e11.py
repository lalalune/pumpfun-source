SX='_ZN14pump_recovered9admin_cto7execute5sweep17h9943ff4781c7e018E.exit'
def edit(f):
    a='  br i1 %_500.sroa.0.0.off0, label %bb77, label %bb82\n'; assert f.count(a)==1
    f=f.replace(a,'  br i1 %_500.sroa.0.0.off0, label %bb77, label %swj\n')
    b='''  %557 = icmp eq i64 %_382.sroa.0.3, 2
  br i1 %557, label %bb82, label %bb81
'''
    assert f.count(b)==1
    f=f.replace(b,'''  br label %swj

swj:
  %swt = phi i64 [ 2, %bb32 ], [ %_382.sroa.0.3, %'''+SX+''' ]
  %swv = phi i64 [ 0, %bb32 ], [ %_382.sroa.19.3, %'''+SX+''' ]
  %557 = icmp eq i64 %swt, 2
  br i1 %557, label %bb82, label %bb81
''')
    c='  %_90.sroa.0.0 = phi i64 [ 0, %bb32 ], [ %_382.sroa.19.3, %'+SX+' ]\n'; assert f.count(c)==1
    f=f.replace(c,'  %_90.sroa.0.0 = phi i64 [ %swv, %swj ]\n')
    d='  %566 = inttoptr i64 %_382.sroa.19.3 to ptr\n'; assert f.count(d)==1
    f=f.replace(d,'  %566 = inttoptr i64 %swv to ptr\n')
    g='[ %_382.sroa.0.3, %bb81 ]'; assert f.count(g)==1
    f=f.replace(g,'[ %swt, %bb81 ]')
    return f
