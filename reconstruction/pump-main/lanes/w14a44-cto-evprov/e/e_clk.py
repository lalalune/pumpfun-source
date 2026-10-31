EDITS=[["let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,", "let clock=Clock::get()?;let e=AdminCtoEvent{timestamp:clock.unix_timestamp,"]]
