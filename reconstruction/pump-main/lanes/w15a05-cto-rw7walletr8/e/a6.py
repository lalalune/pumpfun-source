import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from common import *
EDITS=[RW7,(DCOL,'let mut do_collect=true;if !collection_native{do_collect=!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?;}')]
HYP='rw7 + do_collect as let mut true; if !native{do_collect=..}'
