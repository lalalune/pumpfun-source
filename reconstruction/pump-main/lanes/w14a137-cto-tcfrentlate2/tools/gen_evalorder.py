import sys
s=open(''+__import__("os").environ.get("WT","..")+'/programs/pump/src/creator/admin_cto.rs').read()
L=s.split('\n')[660]
head='crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(CpiContext::new('
i=L.index(head)+len(head)
XB='let x:&AccountInfo=a.pump_amm.as_ref();'
LIT='AccountInfo{owner:x.owner,key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,executable:x.executable,is_writable:x.is_writable,is_signer:x.is_signer}'
PROG='{'+XB+LIT+'}'
assert L[i:].startswith(PROG+',')
rest=L[i+len(PROG)+1:]; tail='))?;}'
assert rest.endswith(tail); ACCTS=rest[:-len(tail)]
OLD=head+PROG+','+ACCTS+'))?;'
assert s.count(OLD)==1
fn='crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2('
LIT_RL='AccountInfo{owner:x.owner,key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),executable:x.executable,is_writable:x.is_writable,is_signer:x.is_signer,rent_epoch:x.rent_epoch}'
V={}
V['pf1']=fn+'CpiContext{program:'+PROG+',accounts:'+ACCTS+',remaining_accounts:Vec::new(),signer_seeds:&[]})?;'
V['pf2']=fn+'CpiContext{program:'+PROG+',accounts:'+ACCTS+',signer_seeds:&[],remaining_accounts:vec![]})?;'
V['af2']=fn+'CpiContext{accounts:'+ACCTS+',program:'+PROG+',signer_seeds:&[],remaining_accounts:vec![]})?;'
V['def4']=fn+'{let accs;CpiContext::new('+PROG+',{accs='+ACCTS+';accs})})?;'
V['def1']=fn+'{let accs;let p='+PROG+';accs='+ACCTS+';CpiContext::new(p,accs)})?;'
V['defrl']=fn+'{'+XB+'let accs;CpiContext::new('+LIT_RL+',{accs='+ACCTS+';accs})})?;'
V['defx']=fn+'{'+XB+'let accs;CpiContext::new('+LIT+',{accs='+ACCTS+';accs})})?;'
for k,v in V.items():
    if len(sys.argv)>1 and k not in sys.argv[1:]: continue
    open(f'{k}.py','w').write('EDITS='+repr([(OLD,v)])+'\n')
print(len(ACCTS), list(V))
LAM='lamports:x.lamports.clone()'; DAT='data:x.data.clone()'; R='rent_epoch:x.rent_epoch'; B3='executable:x.executable,is_writable:x.is_writable,is_signer:x.is_signer'
def P(body): return '{'+XB+'AccountInfo{'+body+'}}'
W={}
W['fru3']='owner:x.owner,key:x.key,'+LAM+','+DAT+','+B3+',..*x'
W['fru4']='owner:x.owner,key:x.key,'+LAM+','+DAT+','+R+',..*x'
W['rfirst']=None
W['rkey']='owner:x.owner,key:x.key,'+R+','+LAM+','+DAT+','+B3
W['rmid']='owner:x.owner,key:x.key,'+LAM+','+R+','+DAT+','+B3
W['rown']=R+',owner:x.owner,key:x.key,'+LAM+','+DAT+','+B3
for k,b in W.items():
    if b is None:
        prog='{'+XB+'let rent_epoch=x.rent_epoch;AccountInfo{owner:x.owner,key:x.key,'+LAM+','+DAT+',rent_epoch,'+B3+'}}'
    else: prog=P(b)
    if len(sys.argv)>1 and k not in sys.argv[1:]: continue
    open(f'{k}.py','w').write('EDITS='+repr([(OLD,head+prog+','+ACCTS+'))?;')])+'\n')
V['cl1']=fn+'CpiContext{program:'+PROG+',remaining_accounts:Vec::new(),accounts:'+ACCTS+',signer_seeds:&[]})?;'
open('cl1.py','w').write('EDITS='+repr([(OLD,V['cl1'])])+'\n')
V2={'tup':fn+'{let (p,acc)=('+PROG+','+ACCTS+');CpiContext::new(p,acc)})?;','tup2':fn+'{let t=('+PROG+','+ACCTS+');CpiContext::new(t.0,t.1)})?;','ctxb':fn+'{let ctx=CpiContext::new('+PROG+','+ACCTS+');ctx})?;'}
for k,v in V2.items(): open(f'{k}.py','w').write('EDITS='+repr([(OLD,v)])+'\n')
