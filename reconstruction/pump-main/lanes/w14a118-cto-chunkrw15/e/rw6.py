import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from common import *
EDITS=[(JOIN_OLD,JOIN_MATCH)]
HYP='post-validate tuple join as match (shared,holder){(true,true),(true,false),(false,_)}'
