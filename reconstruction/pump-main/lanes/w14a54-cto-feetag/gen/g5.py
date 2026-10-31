import json,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a54-cto-feetag/e/')
SIG='fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'
CALL='let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'
Z='if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));}'
S='if t==*sharing||t==*holder_key{'
base=[(Z,'if *t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((*t,Pubkey::default())));}'),(S,'if *t==*sharing||*t==*holder_key{'),
 ('}*holder_key}else{','}holder_key}else{')]
V={
'r1':[(SIG,"fn validate<'a>(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:&'a Option<Pubkey>,holder_key:&'a Pubkey,sharing:&Pubkey)->Result<&'a Pubkey>{")]+base+[(CALL,'let mut target=*validate(&st,hopt,fee,&new,&holder_key,&sk)?;')],
'r1b':[(SIG,"fn validate<'a>(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:&'a Option<Pubkey>,holder_key:&'a Pubkey,sharing:&Pubkey)->Result<&'a Pubkey>{")]+base+[(CALL,'let tr=validate(&st,hopt,fee,&new,&holder_key,&sk)?;let mut target=*tr;')],
'r2':[(SIG,"fn validate<'a>(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&'a Pubkey,sharing:&Pubkey)->Result<Pubkey>{")],
}
for k,v in V.items(): open(O+k+'.py','w').write('EDITS='+json.dumps(v)+'\n')
print(' '.join(V))
