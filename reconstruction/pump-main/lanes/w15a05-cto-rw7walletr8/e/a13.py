import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from common import *
EDITS=[(COINCPI_HEAD,'  if !do_coin{return Ok(());}\n  crate::pump_amm::cpi::collect_coin_creator_fee('),(COINCPI_TAIL,'program:a.pump_amm.to_account_info()}))?;\n }}Ok(())}')]
HYP='rw7 early return: if !do_coin{return Ok(())} before coin cpi'
