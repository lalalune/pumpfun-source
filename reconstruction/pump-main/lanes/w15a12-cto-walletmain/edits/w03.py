import runpy,os
exec(open(__import__('os').path.join(__import__('os').path.dirname(__file__) or '.','c.py')).read())
HYP="do_coin as non-short-circuit coin_present&!frozen? (frozen evaluated unconditionally; its inner data_is_empty is the gate)"
EDITS=[(DC,"let do_coin=coin_present&!token_frozen(a.coin_creator_vault_ata.as_ref())?;")]
