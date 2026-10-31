def T(s):
    L=s.split('\n'); i=[j for j,l in enumerate(L) if 'transfer_creator_fees_to_pump_v2(CpiContext' in l]; assert len(i)==1; i=i[0]; l=L[i]
    for a,b in [('quote_mint:a.quote_mint.to_account_info(),', 'quote_mint:{let x:&AccountInfo=(*a.quote_mint).as_ref();AccountInfo{key:x.key,data:x.data.clone(),lamports:x.lamports.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}},')]:
        assert l.count(a)==1,a; l=l.replace(a,b)
    L[i]=l; return '\n'.join(L)
