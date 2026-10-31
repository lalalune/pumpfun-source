def T(s):
    L=s.split('\n'); i=[j for j,l in enumerate(L) if 'transfer_creator_fees_to_pump_v2(CpiContext' in l]; assert len(i)==1; i=i[0]; l=L[i]
    for a,b in [('AccountInfo{key:x.key,data:a.creator_vault_quote_token_account.data.clone(),owner:a.creator_vault_quote_token_account.owner,lamports:x.lamports.clone(),', 'AccountInfo{owner:a.creator_vault_quote_token_account.owner,key:x.key,data:a.creator_vault_quote_token_account.data.clone(),lamports:x.lamports.clone(),')]:
        assert l.count(a)==1,a; l=l.replace(a,b)
    L[i]=l; return '\n'.join(L)
