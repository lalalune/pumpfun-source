import runpy
g=runpy.run_path('common.py'); globals().update({k:v for k,v in g.items() if k.isupper()})
V={}
EC="#[derive(Clone,Copy)]enum Creator{Holder,New(Pubkey)}"
VH=" let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"
VT="if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};"
VB=[(STRUCT,STRUCT+EC),(VSIG,VSIG.replace("->Result<Pubkey>{","->Result<Creator>{")),(VH,VH.replace("*holder_key}else{","Creator::Holder}else{")),(VT,VT.replace("}t};","}Creator::New(t)};"))]
OLDH="let hopt=holder;let holder=hopt==Some(true);let cashback=!holder&&st.cashback;let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"
def ex(newh): return (T0,T0.replace(OLDH,newh))
H1="let hopt=holder;let args=&(new,);let sk=a.sharing_config.key();let c=validate(&st,hopt,fee,new,&holder_key,&sk)?;let holder=matches!(c,Creator::Holder);let cashback=!holder&&st.cashback;let mut target=match c{Creator::Holder=>holder_key,Creator::New(t)=>t};"
HRT=(HR,"  curve.is_holder_reward=_holder;")
V['h1']=VB+[ex(H1),HRT]
V['h2']=VB+[ex(H1)]
H4="let hopt=holder;let args=&(new,);let sk=a.sharing_config.key();let c=validate(&st,hopt,fee,new,&holder_key,&sk)?;let (holder,cashback,mut target)=match c{Creator::Holder=>(true,false,holder_key),Creator::New(t)=>(false,st.cashback,t)};"
V['h4']=VB+[ex(H4),HRT]
V['h4b']=VB+[ex(H4)]
# h3: Option<Pubkey> return, None = holder
VB3=[(VSIG,VSIG.replace("->Result<Pubkey>{","->Result<Option<Pubkey>>{")),(VH,VH.replace("*holder_key}else{","None}else{")),(VT,VT.replace("}t};","}Some(t)};"))]
H3="let hopt=holder;let args=&(new,);let sk=a.sharing_config.key();let c=validate(&st,hopt,fee,new,&holder_key,&sk)?;let holder=c.is_none();let cashback=!holder&&st.cashback;let mut target=c.unwrap_or(holder_key);"
V['h3']=VB3+[ex(H3),HRT]
for k,v in V.items():
    open(k+'.py','w').write('EDITS='+repr(v)+'\n')
print(list(V))
