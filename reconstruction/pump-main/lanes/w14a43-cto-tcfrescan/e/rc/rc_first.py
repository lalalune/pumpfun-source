def T(s):
    L=s.split('\n'); i=[j for j,l in enumerate(L) if 'transfer_creator_fees_to_pump_v2(CpiContext' in l]; assert len(i)==1; i=i[0]; l=L[i]
    for a,b in [('CpiContext::new({let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{owner:x.owner,key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),', 'CpiContext::new({let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{owner:x.owner,key:x.key,data:x.data.clone(),lamports:x.lamports.clone(),')]:
        assert l.count(a)==1,a; l=l.replace(a,b)
    L[i]=l; return '\n'.join(L)
