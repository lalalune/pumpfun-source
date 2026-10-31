# q.py: n_va (t1 + th.val + th.ex arms) + EXTRA inserts from env QX (python dict literal)
import sys,os;sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a89-cto-jtnodup/tools');import th
th.EXTRA=eval(os.environ.get('QX','{}')); th.EXTRA['names']={}
M=os.environ.get('TH','val,arms').split(',')
def show(t):
    print('NAMES',th.EXTRA['names'],file=sys.stderr); return t
EDITS=([th.val] if 'val' in M else [])+[ (lambda t,m=m: th.ex(t,m)) for m in M if m in ('arms','all3','keeplt','pin')]+[show]
