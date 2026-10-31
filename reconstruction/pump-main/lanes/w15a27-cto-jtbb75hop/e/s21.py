A='let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'
M_='let mut target=match validate(&st,hopt,fee,new,&holder_key,&sk){Ok(t)=>t,Err(e)=>return Err(e)};'
EDITS=[("let cashback=!holder&&st.cashback;let args=&(new,);let sk=a.sharing_config.key();"+A,
        "let args=&(new,);let sk=a.sharing_config.key();"+M_+"let cashback=!holder&&st.cashback;")]
