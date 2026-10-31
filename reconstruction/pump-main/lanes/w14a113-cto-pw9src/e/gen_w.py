import json,os
D=os.path.dirname(os.path.abspath(__file__))
ARGS="let args=&(new,);"
CB="let cashback=!holder&&st.cashback;let args=&(new,);"
SH="let r=(false,Some(args.0),true);"
MINT="let a=&ctx.accounts;let mint=a.mint.key();"
SHE="&&!a.sharing_config.data_is_empty();"
HK="holder_key=hk.0;"
QL="a.global.whitelisted_quote_mints.contains(&q)};"
BLK="={ let st=CtoState{"
HO="let hopt=holder;"
NA="if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}"
def mv(anchor,after=True): return [(CB,"let cashback=!holder&&st.cashback;"),(anchor,anchor+ARGS if after else ARGS+anchor)]
V={
 'w01':mv(MINT),
 'w02':mv(SHE),
 'w03':mv(HK),
 'w04':mv(QL),
 'w05':[(CB,"let cashback=!holder&&st.cashback;"),(BLK,"={ "+ARGS+"let st=CtoState{")],
 'w06':mv(HO),
 'w07':[(CB,"let cashback=!holder&&st.cashback;"),(SH,"let r=(false,Some(Some(target)),true);")],
 'w08':[(CB,"let cashback=!holder&&st.cashback;"),(SH,"let r=(false,Some(new),true);")],
 'w10':[(NA,"if let Some(_)=new{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}")],
 'w11':[(ARGS,"let args=(&new,);"),(SH,"let r=(false,Some(*args.0),true);")],
 'w12':[(ARGS,"let args=&new;"),(SH,"let r=(false,Some(*args),true);")],
}
for k,e in V.items(): open(f'{D}/{k}.py','w').write('EDITS='+json.dumps(e)+'\n')
print(' '.join(V))
