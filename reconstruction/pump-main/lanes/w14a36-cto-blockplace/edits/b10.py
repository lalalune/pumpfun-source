EDITS=[('  if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}', '  if st.fee_configurable!=true{return Err(error!(PumpError::CreatorFeeNotConfigurable));}')]
