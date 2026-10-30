EDITS=[(" let fee=if creator_fee_bps.0>0 && matches!(source,QuoteSource::Controlled|QuoteSource::Nested(_)) {\n",
" let mut fee=0;if creator_fee_bps.0>0 && matches!(source,QuoteSource::Controlled|QuoteSource::Nested(_)) {\n"),
("  creator_fee_bps.0\n } else {\n  0\n };\n","  fee=creator_fee_bps.0;\n }\n\n\n")]
