import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from common import *
EDITS=[RW7,(DC,'let mut do_coin=false;if coin_present{do_coin=!token_frozen(a.coin_creator_vault_ata.as_ref())?;}')]
HYP='rw7 + do_coin as let mut false; if coin_present{do_coin=!frozen?}'
