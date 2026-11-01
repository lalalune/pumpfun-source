import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import subprocess
for n in sys.argv[1:]:
    b=open(f'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a16-shim-outlinerepay/fx/{n}/fn.bin','rb').read()
    i=0;l=0
    while i<len(b):
        if b[i]==0x18: l+=1; i+=16
        else: i+=8
    r=subprocess.run(['python3',os.path.dirname(os.path.abspath(__file__))+'/errseq.py',f'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a16-shim-outlinerepay/fx/{n}/fn.bin'],capture_output=True,text=True).stdout.strip().split('\n')[-2:]
    print(f'{n:14s} lddw {l} bytes {len(b)} | '+' | '.join(r))
