EDITS=[
("fn validate(st:&CtoState,holder:bool,fee:Option<u64>,","fn validate(st:&CtoState,holder:bool,hopt:Option<bool>,fee:Option<u64>,"),
(" if holder&&!st.holder_reward&&!st.holder_enabled{"," if matches!(hopt,Some(true))&&!st.holder_reward&&!st.holder_enabled{"),
(" let target=if holder{if new.is_some()"," let target=if matches!(hopt,Some(true)){if new.is_some()"),
(" let cashback=if holder{false}else{st.cashback};"," let cashback=if matches!(hopt,Some(true)){false}else{st.cashback};"),
("let holder=holder==Some(true);","let hopt=holder;let holder=hopt==Some(true);"),
("validate(&st,holder,fee,","validate(&st,holder,hopt,fee,"),
]
