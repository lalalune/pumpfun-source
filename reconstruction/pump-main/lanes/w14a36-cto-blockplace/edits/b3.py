EDITS=[('  if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}', '  if st.fee_configurable==false{return Err(error!(PumpError::CreatorFeeNotConfigurable));}')]
