import runpy,os
exec(open(__import__('os').path.join(__import__('os').path.dirname(__file__) or '.','c.py')).read())
HYP="coin flags in a let-else block: let (coin_present,do_coin)={let p=..;(p,p&&!frozen?)} after do_collect"
EDITS=[(CP+"\n  "+DCOL+"\n  "+DC, DCOL+"\n  "+"let (coin_present,do_coin)={let p=!a.coin_creator_vault_ata.data_is_empty();(p,p&&!token_frozen(a.coin_creator_vault_ata.as_ref())?)};\n  ")]
