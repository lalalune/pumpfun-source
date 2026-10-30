# IR probe: sweep Err edge goes straight from sweep.exit to the payload phi (no inttoptr-only bb81 block),
# as in 7fb9a5e3e7a2 where the sweep result payload phi is ptr-typed.
SW='_ZN14pump_recovered9admin_cto7execute5sweep17h9943ff4781c7e018E.exit'
def edit(fn):
    a='  %557 = icmp eq i64 %_386.sroa.0.3, 2\n  br i1 %557, label %bb82, label %bb81\n'
    assert fn.count(a)==1
    fn=fn.replace(a,'  %557 = icmp eq i64 %_386.sroa.0.3, 2\n  %swerr = inttoptr i64 %_386.sroa.19.3 to ptr\n  br i1 %557, label %bb82, label %bb64\n')
    b='bb81:                                             ; preds = %'+SW+'\n  %566 = inttoptr i64 %_386.sroa.19.3 to ptr\n  br label %bb64\n\n'
    assert fn.count(b)==1; fn=fn.replace(b,'')
    fn=fn.replace('[ %566, %bb81 ]','[ %swerr, %'+SW+' ]').replace('[ %_386.sroa.0.3, %bb81 ]','[ %_386.sroa.0.3, %'+SW+' ]')
    assert not any(('%bb81 ' in l or '%bb81,' in l) for l in fn.split('\n') if not l.lstrip().startswith(';') and 'preds =' not in l)
    import re
    def ren(m):
        n=int(m.group(1)); return '%'+str(n-1 if n>566 else n)
    fn=re.sub(r'%(\d+)(?![\w.$])',ren,fn)
    return fn
