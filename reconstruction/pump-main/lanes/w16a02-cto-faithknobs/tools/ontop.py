#!/usr/bin/env python3
"""ontop.py <base-lead fn.bin> <name>...: splice each of this lane's captures rx/<name> on top of a lead capture (e.g. the
ev6+A6 composite) and print bytes and predicted M. Experiment only."""
import sys,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import splice
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a02-cto-faithknobs')
main=open(O+'/rx/main/fn.bin','rb').read(); lead=open(sys.argv[1],'rb').read()
for n in sys.argv[2:]:
    p=f'{O}/rx/{n}/fn.bin'
    if not os.path.exists(p): print(n,'missing'); continue
    s=splice.splice(main,[lead,open(p,'rb').read()])
    print(f'{n:16s}', 'conflict' if s is None else (len(s),splice.M(s)))
