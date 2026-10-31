def T(s):
    L=s.split('\n'); i=[j for j,l in enumerate(L) if 'transfer_creator_fees_to_pump_v2(CpiContext' in l]; assert len(i)==1; i=i[0]; l=L[i]
    for a,b in [('event_authority:a.pump_amm_event_authority.to_account_info(),', 'event_authority:{let x:&AccountInfo=a.pump_amm_event_authority.as_ref();AccountInfo{key:x.key,data:x.data.clone(),lamports:x.lamports.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}},'), ('associated_token_program:a.associated_token_program.to_account_info(),', 'associated_token_program:{let x:&AccountInfo=a.associated_token_program.as_ref();AccountInfo{key:x.key,data:x.data.clone(),lamports:x.lamports.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}},')]:
        assert l.count(a)==1,a; l=l.replace(a,b)
    L[i]=l; return '\n'.join(L)
