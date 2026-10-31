import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from common import *
EDITS=[RW7,(DC,'let do_coin=coin_present&&!{token_frozen(a.coin_creator_vault_ata.as_ref())?};')]
HYP='rw7 + do_coin frozen in a block'
