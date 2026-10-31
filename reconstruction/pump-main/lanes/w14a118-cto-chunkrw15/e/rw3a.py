import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from common import *
EDITS=[(NAT_OLD,NAT_SIB)]
HYP='sweep native arm: let rent=Rent::get()?;let min=rent.minimum_balance(0) (no block)'
