EDITS=[["let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,", "let e=AdminCtoEvent{timestamp:Clock::get().map(|c|c.unix_timestamp)?,"]]
