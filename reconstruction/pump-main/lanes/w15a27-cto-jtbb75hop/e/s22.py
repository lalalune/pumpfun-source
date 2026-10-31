A='let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'
EDITS=[("let cashback=!holder&&st.cashback;let args=&(new,);let sk=a.sharing_config.key();"+A,
        "let args=&(new,);let sk=a.sharing_config.key();"+A+"let cashback=!holder&&st.cashback;")]
