EDITS=[
("let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{","if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}}else{"),
("if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};","if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}}"),
("return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};}None=>{}}\n Ok(target)}","return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}}None=>{}}\n Ok(if let Some(t)=new{t}else{*holder_key})}"),
]