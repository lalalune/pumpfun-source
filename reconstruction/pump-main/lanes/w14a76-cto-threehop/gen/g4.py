import sys,os;sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a76-cto-threehop/tools');import th
M=os.environ.get('TH','val,arms').split(',')
EDITS=([th.val] if 'val' in M else [])+[ (lambda t,m=m: th.ex(t,m)) for m in M if m in ('arms','all3','keeplt')]
