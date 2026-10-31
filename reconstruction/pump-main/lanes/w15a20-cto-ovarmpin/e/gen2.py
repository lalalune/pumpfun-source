import json,runpy
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a20-cto-ovarmpin'
SIG='fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);'
def sig(ret): return 'fn validate(st:&CtoState,hopt:Option<bool>,hb:bool,shared:bool,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey,out:&mut Pubkey)->'+ret+'{let holder=hopt==Some(true);'
ARM=(' let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{',' *out=if hb{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{')
OVR=('if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};','if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}if shared{st.creator}else{t}};')
TREE=('sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)','sharing_update=Some(args.0);(false,true)')
CALL='let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'
rs=runpy.run_path(O+'/e/m_rs.py')['EDITS']
V={}
V['lv3']=[(SIG,sig('Result<Pubkey>')),ARM,OVR,(' Ok(target)}pub fn execute(',' Ok(*holder_key)}pub fn execute('),(CALL,'let mut target=holder_key;validate(&st,hopt,holder,shared,fee,new,&holder_key,&sk,&mut target)?;'),TREE]
V['vb']=[(SIG,sig('Result<()>')),ARM,OVR,(' Ok(target)}pub fn execute(',' Ok(())}pub fn execute('),(CALL,'let mut target=Pubkey::default();validate(&st,hopt,holder,shared,fee,new,&holder_key,&sk,&mut target)?;'),TREE]
V['lv3_rs']=V['lv3']+rs
V['vb_rs']=V['vb']+rs
for k,v in V.items(): open(f'{O}/e/{k}.py','w').write('EDITS='+json.dumps(v)+'\n')
