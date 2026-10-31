import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from common import *
EDITS=[(COINCPI_HEAD,'  match do_coin{true=>{\n  crate::pump_amm::cpi::collect_coin_creator_fee('),(COINCPI_TAIL,'program:a.pump_amm.to_account_info()}))?;}false=>{}}\n }}Ok(())}')]
HYP='rw7 as match do_coin{true=>cpi,false=>{}}'
