def T(s):
    L=s.split('\n'); i=[j for j,l in enumerate(L) if 'admin_cto_sharing_config(CpiContext' in l]; assert len(i)==1; i=i[0]; l=L[i]
    for a,b in [('authority:{let x:&AccountInfo=a.admin_set_creator_authority.as_ref();AccountInfo{is_writable:x.is_writable,executable:x.executable,is_signer:x.is_signer,rent_epoch:x.rent_epoch,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,key:x.key}}', 'authority:{let x:&AccountInfo=a.admin_set_creator_authority.as_ref();AccountInfo{is_writable:x.is_writable,executable:x.executable,is_signer:x.is_signer,rent_epoch:x.rent_epoch,data:x.data.clone(),lamports:x.lamports.clone(),owner:x.owner,key:x.key}}')]:
        assert l.count(a)==1,a; l=l.replace(a,b)
    L[i]=l; return '\n'.join(L)
