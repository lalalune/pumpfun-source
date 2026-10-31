import runpy,os
exec(open(__import__('os').path.join(__import__('os').path.dirname(__file__) or '.','c.py')).read())
HYP="do_collect as if-expr: if collection_native{true}else{!empty&&!frozen?}"
EDITS=[(DCOL,"let do_collect=if collection_native{true}else{!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?};")]
