EDITS=[('  if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}', '  require!(st.fee_configurable,PumpError::CreatorFeeNotConfigurable);')]
