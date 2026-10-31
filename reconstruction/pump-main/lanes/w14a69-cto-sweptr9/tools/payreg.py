#!/usr/bin/env python3
"""payreg.py <unstripped.so|fn.dis>...: Err-payload register of admin_cto::execute's return block
(stxdw [rX+0x8], rP right before exit) and the registers that store swept into the event ([r10-0x218]).
In every 6/2 clone-run build, swept is stored straight from the payload register (swept coalesced into the
Err-payload class); main stores it from a reload."""
import sys,subprocess,os,re
T=os.path.dirname(os.path.abspath(__file__))
for p in sys.argv[1:]:
    L=(open(p).read() if p.endswith('.dis') else subprocess.run([sys.executable,T+'/sodis.py',p],capture_output=True,text=True).stdout).split('\n')
    pay=None
    for i,l in enumerate(L):
        if l.endswith('exit'):
            for k in range(i-1,i-4,-1):
                m=re.search(r'stxdw \[r\d \+ 0x8\], (r\d)',L[k])
                if m: pay=m.group(1)
            break
    ev=[l.split()[-1] for l in L if 'stxdw [r10 - 0x218], r' in l]
    print(f'{p}: payload={pay} event_swept={ev} merged={pay in ev}')
