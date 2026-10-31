import runpy,os
exec(open(__import__('os').path.join(__import__('os').path.dirname(__file__) or '.','c.py')).read())
HYP="do_coin as mut seeded from coin_present: let mut do_coin=coin_present;if do_coin{do_coin=!frozen?}"
EDITS=[(DC,"let mut do_coin=coin_present;if do_coin{do_coin=!token_frozen(a.coin_creator_vault_ata.as_ref())?;}")]
