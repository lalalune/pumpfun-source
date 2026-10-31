EDITS=[('  if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};','  if [*sharing,*holder_key].contains(&t){return Err(error!(PumpError::InvalidCreator));}t};')]
