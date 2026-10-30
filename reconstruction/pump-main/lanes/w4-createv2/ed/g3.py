EDITS=[(" let fee=if creator_fee_bps.0>0 && matches!(source,QuoteSource::Controlled|QuoteSource::Nested(_)) {\n",
" let fee=if creator_fee_bps.0==0 || !matches!(source,QuoteSource::Controlled|QuoteSource::Nested(_)) {0} else {\n"),
("  creator_fee_bps.0\n } else {\n  0\n };\n","  creator_fee_bps.0\n };\n\n\n")]
