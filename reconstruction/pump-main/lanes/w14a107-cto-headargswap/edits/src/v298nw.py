EDITS=[('if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}', 'if holder{if let Some(_)=new{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}')]
