import re
s=open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a133-cto-tcfrentlate/programs/pump/src/creator/admin_cto.rs').read()
L=s.split('\n')[660]
head='crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(CpiContext::new('
i=L.index(head)+len(head)
PROG='{let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{owner:x.owner,key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,executable:x.executable,is_writable:x.is_writable,is_signer:x.is_signer}}'
assert L[i:].startswith(PROG+',')
rest=L[i+len(PROG)+1:]
tail='))?;}'
assert rest.endswith(tail)
ACCTS=rest[:-len(tail)]
OLD=head+PROG+','+ACCTS+'))?;'
assert s.count(OLD)==1
fn='crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2('
V={}
P_FRU1='{let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{owner:x.owner,key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),..*x}}'
P_FRU2='{let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{lamports:x.lamports.clone(),data:x.data.clone(),..*x}}'
V['fru1']=fn+'CpiContext::new('+P_FRU1+','+ACCTS+'))?;'
V['fru2']=fn+'CpiContext::new('+P_FRU2+','+ACCTS+'))?;'
V['acc1']=fn+'{let accounts='+ACCTS+';CpiContext::new('+PROG+',accounts)})?;'
V['acc2']=fn+'{let x:&AccountInfo=a.pump_amm.as_ref();let accounts='+ACCTS+';CpiContext::new(AccountInfo{owner:x.owner,key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,executable:x.executable,is_writable:x.is_writable,is_signer:x.is_signer},accounts)})?;'
V['bindp']=fn+'{let program='+PROG+';CpiContext::new(program,'+ACCTS+')})?;'
V['lit1']=fn+'CpiContext{accounts:'+ACCTS+',remaining_accounts:Vec::new(),program:'+PROG+',signer_seeds:&[]})?;'
V['acc_fru1']=fn+'{let accounts='+ACCTS+';CpiContext::new('+P_FRU1+',accounts)})?;'
for k,v in V.items():
    open(f'{k}.py','w').write('EDITS='+repr([(OLD,v)])+'\n')
print(len(ACCTS), list(V))
X='{let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{'
W={}
W['fru3']=X+'owner:x.owner,key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),executable:x.executable,is_writable:x.is_writable,is_signer:x.is_signer,..*x}}'
W['fru5']=X+'owner:x.owner,lamports:x.lamports.clone(),data:x.data.clone(),..*x}}'
W['fru6']=X+'key:x.key,owner:x.owner,lamports:x.lamports.clone(),data:x.data.clone(),..*x}}'
W['fru7']=X+'owner:x.owner,key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),executable:x.executable,..*x}}'
for k,p in W.items():
    open(f'{k}.py','w').write('EDITS='+repr([(OLD,fn+'CpiContext::new('+p+','+ACCTS+'))?;')])+'\n')
open('bindfru.py','w').write('EDITS='+repr([(OLD,fn+'{let program='+P_FRU1+';CpiContext::new(program,'+ACCTS+')})?;')])+'\n')
PB='AccountInfo{owner:x.owner,key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,executable:x.executable,is_writable:x.is_writable,is_signer:x.is_signer}'
PROGF='program:{let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{key:x.key,'
assert ACCTS.count(PROGF)==1
open('pre1.py','w').write('EDITS='+repr([(OLD,'{let x:&AccountInfo=a.pump_amm.as_ref();'+fn+'CpiContext::new('+PB+','+ACCTS+'))?;}')])+'\n')
open('pre2.py','w').write('EDITS='+repr([(OLD,'{let x:&AccountInfo=a.pump_amm.as_ref();'+fn+'CpiContext::new('+PB+','+ACCTS.replace(PROGF,'program:{AccountInfo{key:x.key,')+'))?;}')])+'\n')
