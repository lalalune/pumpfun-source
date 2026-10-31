EDITS=[('if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};','if t!=*sharing&&t!=*holder_key{t}else{return Err(error!(PumpError::InvalidCreator));}};')]
