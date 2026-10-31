import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from common import *
EDITS=[(DC_OLD,DC_IF)]
HYP='wallet do_coin as if coin_present{!frozen?}else{false} (gate kept coin_present&do_coin)'
