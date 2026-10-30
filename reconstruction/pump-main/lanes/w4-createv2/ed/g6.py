EDITS=[(" let mut fee=0;if creator_fee_bps.0>0 && matches!(source,QuoteSource::Controlled|QuoteSource::Nested(_)) {\n",
" let mut fee=0;if creator_fee_bps.0>0 {if let QuoteSource::Controlled|QuoteSource::Nested(_)=source {\n"),
("  fee=creator_fee_bps.0;\n }\n","  fee=creator_fee_bps.0;\n }}\n")]
