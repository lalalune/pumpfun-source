EDITS=[('  if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}', '  if st.fee_configurable{}else{return Err(error!(PumpError::CreatorFeeNotConfigurable));}')]
