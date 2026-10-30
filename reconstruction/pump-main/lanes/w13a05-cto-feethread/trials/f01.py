EDITS=[
("fn validate(st:&CtoState,holder:bool,fee:","fn validate(st:&CtoState,holder:bool,shared:bool,fee:"),
("{return Err(error!(PumpError::InvalidCreator));}t};","{return Err(error!(PumpError::InvalidCreator));}if shared{st.creator}else{t}};"),
("let mut target=validate(&st,holder,fee,","let target=validate(&st,holder,shared,fee,"),
("else{target=st.creator;(Some(new),false)}","else{(Some(new),false)}"),
]
