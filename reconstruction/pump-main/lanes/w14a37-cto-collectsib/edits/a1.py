EDITS=[('let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,creator:a.current_creator.key(),','let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,creator:creator_key,'),
 ('  let collection_native=a.quote_mint.key()','  let creator_key=a.current_creator.key();let collection_native=a.quote_mint.key()')]
