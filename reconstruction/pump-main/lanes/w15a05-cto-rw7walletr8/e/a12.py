import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from common import *
EDITS=[RW7,(DC,'let do_coin=if coin_present{let f=token_frozen(a.coin_creator_vault_ata.as_ref())?;!f}else{false};')]
HYP='rw7 + do_coin if-expr with frozen bound to local'
