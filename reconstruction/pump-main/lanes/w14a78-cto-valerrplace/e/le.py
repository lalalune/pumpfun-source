EDITS=[('let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};','let Some(t)=new else{return Err(error!(PumpError::CtoNewCreatorRequired));};')]
