def T(s):
    L=s.split('\n'); i=[j for j,l in enumerate(L) if 'admin_cto_sharing_config(CpiContext' in l]; assert len(i)==1; i=i[0]; l=L[i]
    for a,b in [('mint:{let x:&AccountInfo= a.mint.as_ref();AccountInfo{rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable,lamports:x.lamports.clone(),owner:x.owner,data:x.data.clone(),key:x.key}}', 'mint:{let x:&AccountInfo= a.mint.as_ref();AccountInfo{rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable,data:x.data.clone(),owner:x.owner,lamports:x.lamports.clone(),key:x.key}}')]:
        assert l.count(a)==1,a; l=l.replace(a,b)
    L[i]=l; return '\n'.join(L)
