EDITS=[("pub enum QuoteSource { Sol, Whitelisted, Controlled, Nested }","pub enum QuoteSource { Sol, Whitelisted, Controlled, Nested(u8) }"),
 ("->Result<(Pubkey,Option<(u64,u8)>,QuoteSource)>{","->Result<(Pubkey,Option<u64>,QuoteSource)>{"),
 ("   Some(reserves)=>(QuoteSource::Controlled,Some((reserves,0))),","   Some(reserves)=>(QuoteSource::Controlled,Some(reserves)),"),
 ("    (QuoteSource::Nested,Some((reserves,depth)))","    (QuoteSource::Nested(depth),Some(reserves))"),
 ("matches!(source,QuoteSource::Controlled|QuoteSource::Nested)","matches!(source,QuoteSource::Controlled|QuoteSource::Nested(_))"),
 (" let depth=if let Some((_,depth))=reserves {depth} else {0};"," let depth=if let QuoteSource::Nested(depth)=source {depth} else {0};"),
 ("{let (m,r)=(quote_mint,reserves);if m==Pubkey::default() {global.initial_virtual_sol_reserves} else {r.map_or(global.initial_virtual_quote_reserves,|(r,_)|r)}};","if quote_mint==Pubkey::default() {global.initial_virtual_sol_reserves} else {reserves.unwrap_or(global.initial_virtual_quote_reserves)};")]
