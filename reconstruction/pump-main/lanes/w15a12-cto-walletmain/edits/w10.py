import runpy,os
exec(open(__import__('os').path.join(__import__('os').path.dirname(__file__) or '.','c.py')).read())
HYP="coin_empty binding: let coin_empty=..data_is_empty(); gates on !coin_empty"
EDITS=[(CP,"let coin_empty=a.coin_creator_vault_ata.data_is_empty();"),(DC,"let do_coin=!coin_empty&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;"),(ATA,"if !collection_native||!coin_empty{"),(GATE,"  if !coin_empty&do_coin{\n")]
