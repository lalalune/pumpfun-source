import runpy
g=runpy.run_path('common.py'); globals().update({k:v for k,v in g.items() if k.isupper()})
V={}
VH=" let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"
VT="if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};"
OLDH="let hopt=holder;let holder=hopt==Some(true);let cashback=!holder&&st.cashback;let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"
HRT=(HR,"  curve.is_holder_reward=_holder;")
E5="#[derive(Clone,Copy)]enum Creator{Holder(Pubkey),New(Pubkey)}"
B5=[(STRUCT,STRUCT+E5),(VSIG,VSIG.replace("->Result<Pubkey>{","->Result<Creator>{")),(VH,VH.replace("*holder_key}else{","Creator::Holder(*holder_key)}else{")),(VT,VT.replace("}t};","}Creator::New(t)};"))]
H5="let hopt=holder;let args=&(new,);let sk=a.sharing_config.key();let c=validate(&st,hopt,fee,new,&holder_key,&sk)?;let holder=matches!(c,Creator::Holder(_));let cashback=!holder&&st.cashback;let mut target=match c{Creator::Holder(k)|Creator::New(k)=>k};"
V['h5']=B5+[(T0,T0.replace(OLDH,H5)),HRT]
H5b="let hopt=holder;let args=&(new,);let sk=a.sharing_config.key();let (holder,mut target)=match validate(&st,hopt,fee,new,&holder_key,&sk)?{Creator::Holder(k)=>(true,k),Creator::New(k)=>(false,k)};let cashback=!holder&&st.cashback;"
V['h5b']=B5+[(T0,T0.replace(OLDH,H5b)),HRT]
V['h5c']=B5+[(T0,T0.replace(OLDH,H5b))]
# h6: Result<(Pubkey,bool)>
B6=[(VSIG,VSIG.replace("->Result<Pubkey>{","->Result<(Pubkey,bool)>{")),(VH,VH.replace("*holder_key}else{","(*holder_key,true)}else{")),(VT,VT.replace("}t};","}(t,false)};"))]
H6="let hopt=holder;let args=&(new,);let sk=a.sharing_config.key();let (mut target,holder)=validate(&st,hopt,fee,new,&holder_key,&sk)?;let cashback=!holder&&st.cashback;"
V['h6']=B6+[(T0,T0.replace(OLDH,H6)),HRT]
# h1 variant with holder before cashback in st order kept: cashback computed before matches (same), but target via if
EC="#[derive(Clone,Copy)]enum Creator{Holder,New(Pubkey)}"
B1=[(STRUCT,STRUCT+EC),(VSIG,VSIG.replace("->Result<Pubkey>{","->Result<Creator>{")),(VH,VH.replace("*holder_key}else{","Creator::Holder}else{")),(VT,VT.replace("}t};","}Creator::New(t)};"))]
H1b="let hopt=holder;let args=&(new,);let sk=a.sharing_config.key();let (holder,mut target)=match validate(&st,hopt,fee,new,&holder_key,&sk)?{Creator::Holder=>(true,holder_key),Creator::New(t)=>(false,t)};let cashback=!holder&&st.cashback;"
V['h1b']=B1+[(T0,T0.replace(OLDH,H1b)),HRT]
# h1 with New first variant order
EC2="#[derive(Clone,Copy)]enum Creator{New(Pubkey),Holder}"
V['h1n']=[(STRUCT,STRUCT+EC2)]+B1[1:]+[(T0,T0.replace(OLDH,"let hopt=holder;let args=&(new,);let sk=a.sharing_config.key();let c=validate(&st,hopt,fee,new,&holder_key,&sk)?;let holder=matches!(c,Creator::Holder);let cashback=!holder&&st.cashback;let mut target=match c{Creator::Holder=>holder_key,Creator::New(t)=>t};")),HRT]
for k,v in V.items():
    open(k+'.py','w').write('EDITS='+repr(v)+'\n')
print(list(V))
