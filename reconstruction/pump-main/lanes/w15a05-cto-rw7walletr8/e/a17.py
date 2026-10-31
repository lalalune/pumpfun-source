import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from common import *
EDITS=[RW7,(DC,'let do_coin=coin_present&&!token_frozen(&a.coin_creator_vault_ata)?;')]
HYP='rw7 + token_frozen(&ata) deref instead of as_ref'
