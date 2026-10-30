import itertools,re
lits={
'pa':('pool_authority:{let x:&AccountInfo= a.pool_authority.as_ref();AccountInfo{executable:x.executable,lamports:x.lamports.clone(),data:x.data.clone(),is_writable:x.is_writable,owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,key:x.key}}','pool_authority:a.pool_authority.to_account_info()'),
'gl':('global:{let x:&AccountInfo= a.global.as_ref().as_ref();AccountInfo{is_signer:x.is_signer,is_writable:x.is_writable,rent_epoch:x.rent_epoch,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,executable:x.executable,key:x.key}}','global:a.global.to_account_info()'),
'mi':('mint:{let x:&AccountInfo= a.mint.as_ref();AccountInfo{rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable,lamports:x.lamports.clone(),owner:x.owner,data:x.data.clone(),key:x.key}}','mint:a.mint.to_account_info()'),
'ea':('event_authority:{let x=&*a.pump_fees_event_authority;AccountInfo{lamports:x.lamports.clone(),data:x.data.clone(),key:x.key,owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}','event_authority:a.pump_fees_event_authority.to_account_info()'),
'pr':('program:{let x:&AccountInfo= a.pump_fees.as_ref();AccountInfo{owner:x.owner,lamports:x.lamports.clone(),rent_epoch:x.rent_epoch,is_signer:x.is_signer,executable:x.executable,data:x.data.clone(),key:x.key,is_writable:x.is_writable}}','program:a.pump_fees.to_account_info()'),
}
ks=list(lits)
for r in range(1,5):
    for c in itertools.combinations(ks,r):
        n='u_'+'_'.join(c)
        open(f'edits/{n}.py','w').write('EDITS='+repr([lits[k] for k in c])+'\n')
        print(n)
