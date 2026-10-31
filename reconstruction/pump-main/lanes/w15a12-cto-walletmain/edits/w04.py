import runpy,os
exec(open(__import__('os').path.join(__import__('os').path.dirname(__file__) or '.','c.py')).read())
HYP="do_coin as !frozen?&&coin_present (frozen first)"
EDITS=[(DC,"let do_coin=!token_frozen(a.coin_creator_vault_ata.as_ref())?&&coin_present;")]
