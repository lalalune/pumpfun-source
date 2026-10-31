def T(s):
    L=s.split('\n'); i=[j for j,l in enumerate(L) if 'transfer_creator_fees_to_pump_v2(CpiContext' in l]; assert len(i)==1; i=i[0]; l=L[i]
    for a,b in [('AccountInfo{key:x.key,lamports:x.lamports.clone(),owner:x.owner,data:a.creator_vault_quote_token_account.data.clone(),', 'AccountInfo{key:x.key,data:a.creator_vault_quote_token_account.data.clone(),owner:x.owner,lamports:x.lamports.clone(),'), ('coin_creator_vault_authority:a.coin_creator_vault_authority.to_account_info(),', 'coin_creator_vault_authority:{let x:&AccountInfo=a.coin_creator_vault_authority.as_ref();AccountInfo{key:x.key,lamports:x.lamports.clone(),data:a.coin_creator_vault_authority.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}},')]:
        assert l.count(a)==1,a; l=l.replace(a,b)
    L[i]=l; return '\n'.join(L)
