EDITS=[('let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,', 'let e=CollectCreatorFeeEvent{timestamp:Clock::get().map(|c|c.unix_timestamp)?,')]
