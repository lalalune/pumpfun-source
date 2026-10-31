EDITS=[["let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;", "let r=validate(&st,hopt,fee,new,&holder_key,&sk);let mut target=if let Ok(t)=r{t}else{return r.map(|_|());};"]]
