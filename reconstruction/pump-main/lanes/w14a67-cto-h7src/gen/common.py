A='let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{'
B='  if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};'
C=' Ok(target)}pub fn execute'
T='  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};'
