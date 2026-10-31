import json,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a54-cto-feetag/e/')
SIG='fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'
CALL='let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'
HA='let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{'
NA='if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};'
END=' Ok(target)}pub fn'
arms=[(HA,HA.replace('}*holder_key}else{','}*out=*holder_key;*holder_key}else{')),(NA,NA.replace('}t};','}*out=t;t};'))]
sig=lambda r:(SIG,SIG.replace('sharing:&Pubkey)->Result<Pubkey>{','sharing:&Pubkey,out:&mut Pubkey)->'+r+'{'))
V={
'w1a':[sig('Result<()>')]+arms+[(END,' Ok(())}pub fn'),(CALL,'let mut target=Pubkey::default();validate(&st,hopt,fee,new,&holder_key,&sk,&mut target)?;')],
'w1d':[sig('Result<Pubkey>')]+arms+[(CALL,'let mut target=Pubkey::default();let _=validate(&st,hopt,fee,new,&holder_key,&sk,&mut target)?;')],
'w1e':[sig('Result<()>'),(END,' *out=target;Ok(())}pub fn'),(CALL,'let mut target=Pubkey::default();validate(&st,hopt,fee,new,&holder_key,&sk,&mut target)?;')],
'w1g':[sig('Result<()>')]+arms+[(END,' Ok(())}pub fn'),(CALL,'let mut target=st.creator;validate(&st,hopt,fee,new,&holder_key,&sk,&mut target)?;')],
}
for k,v in V.items(): open(O+k+'.py','w').write('EDITS='+json.dumps(v)+'\n')
print(' '.join(V))
