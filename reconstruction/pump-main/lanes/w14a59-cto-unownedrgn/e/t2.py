EDITS=[('if a.current_creator.is_writable==false{return Err(error!(PumpError::CtoCreatorAccountNotWritable));}', 'require!(a.current_creator.is_writable,PumpError::CtoCreatorAccountNotWritable);')]
