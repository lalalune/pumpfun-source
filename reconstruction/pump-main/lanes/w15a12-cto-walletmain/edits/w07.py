import runpy,os
exec(open(__import__('os').path.join(__import__('os').path.dirname(__file__) or '.','c.py')).read())
HYP="do_coin from a match on coin_present: match coin_present{false=>false,true=>!frozen?}"
EDITS=[(DC,"let do_coin=match coin_present{false=>false,true=>!token_frozen(a.coin_creator_vault_ata.as_ref())?};")]
