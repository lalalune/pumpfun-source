import itertools,os
P0='CpiContext::new({let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{key:x.key,owner:x.owner,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}},crate::pump_amm::cpi::accounts::TransferCreatorFeesToPumpV2{'
P={'p0':P0,
 'p1':'CpiContext::new({let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}},crate::pump_amm::cpi::accounts::TransferCreatorFeesToPumpV2{',
 'p2':'CpiContext::new(a.pump_amm.to_account_info(),crate::pump_amm::cpi::accounts::TransferCreatorFeesToPumpV2{'}
A0='associated_token_program:{let x:&AccountInfo=a.associated_token_program.as_ref();AccountInfo{key:x.key,owner:x.owner,..x.clone()}},coin_creator:'
A={'a0':A0,'a1':'associated_token_program:a.associated_token_program.to_account_info(),coin_creator:',
 'a2':'associated_token_program:{let x:&AccountInfo=a.associated_token_program.as_ref();AccountInfo{key:x.key,..x.clone()}},coin_creator:'}
L0='program:{let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{key:x.key,owner:x.owner,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}}))?;}'
Lv={'l0':L0,
 'l1':'program:{let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable,owner:x.owner}}}))?;}',
 'l2':'program:{let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}}))?;}'}
for p,a,l in itertools.product(P,A,Lv):
    if (p,a,l)==('p0','a0','l0'): continue
    n=p+a+l; ed=[]
    if p!='p0': ed.append((P0,P[p]))
    if a!='a0': ed.append((A0,A[a]))
    if l!='l0': ed.append((L0,Lv[l]))
    open(f'{n}.py','w').write('EDITS='+repr(ed)+'\n')
    print(n)
