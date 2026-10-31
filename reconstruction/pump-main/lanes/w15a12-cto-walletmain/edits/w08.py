import runpy,os
exec(open(__import__('os').path.join(__import__('os').path.dirname(__file__) or '.','c.py')).read())
HYP="coin_present as data_is_empty()==false"
EDITS=[(CP,"let coin_present=a.coin_creator_vault_ata.data_is_empty()==false;")]
