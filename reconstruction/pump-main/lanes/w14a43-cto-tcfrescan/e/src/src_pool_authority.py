def T(s):
    L=s.split('\n'); i=[j for j,l in enumerate(L) if 'admin_cto_sharing_config(CpiContext' in l]; assert len(i)==1; i=i[0]; l=L[i]
    for a,b in [('pool_authority:{let x:&AccountInfo= a.pool_authority.as_ref();AccountInfo{owner:x.owner,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:a.pool_authority.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,key:x.key,executable:x.executable}}', 'pool_authority:{let x:&AccountInfo= a.pool_authority.as_ref();AccountInfo{owner:x.owner,data:x.data.clone(),lamports:x.lamports.clone(),rent_epoch:a.pool_authority.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,key:x.key,executable:x.executable}}')]:
        assert l.count(a)==1,a; l=l.replace(a,b)
    L[i]=l; return '\n'.join(L)
