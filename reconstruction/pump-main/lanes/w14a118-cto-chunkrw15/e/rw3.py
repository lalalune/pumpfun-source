import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from common import *
EDITS=[(NAT_OLD,NAT_SIB),(NT_OLD,NT_PLAIN)]
HYP='sweep native arm collect_creator_fee sibling style: let rent=Rent::get()?;let min=..;if amount>0{ensure?;transfer_native?;}Ok(amount)'
