def T(s):
    L=s.split('\n'); i=[j for j,l in enumerate(L) if 'admin_cto_sharing_config(CpiContext' in l]; assert len(i)==1; i=i[0]; l=L[i]
    for a,b in [('program:{let x:&AccountInfo=a.pump_fees.as_ref();AccountInfo{lamports:x.lamports.clone(),key:x.key,data:a.pump_fees.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}', 'program:{let x:&AccountInfo=a.pump_fees.as_ref();AccountInfo{data:a.pump_fees.data.clone(),key:x.key,lamports:a.pump_fees.lamports.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}')]:
        assert l.count(a)==1,a; l=l.replace(a,b)
    L[i]=l; return '\n'.join(L)
