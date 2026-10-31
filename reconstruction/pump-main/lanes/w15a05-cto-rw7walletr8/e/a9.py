import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from common import *
EDITS=[(COINCPI_HEAD,'  if !do_coin{}else{\n  crate::pump_amm::cpi::collect_coin_creator_fee(')]
HYP='rw7 polarity: if !do_coin{}else{coin cpi}'
