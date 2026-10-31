import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from common import *
EDITS=[(COIN_OLD,COIN_DO),(DC_OLD,DC_IF)]
HYP='wallet coin region: do_coin as if coin_present{!frozen?}else{false} + gate if do_coin'
