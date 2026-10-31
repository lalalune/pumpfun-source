#!/usr/bin/env python3
"""roles.py <ra.log>: name the wallet vregs in the pre-RA MIR and print each role's greedy timeline (wtl) and final regs."""
import sys,re,subprocess,os
T=os.path.dirname(os.path.abspath(__file__))
L=sys.argv[1]; log=open(L).read()
gi=log.index('********** GREEDY'); mi=log[:gi]; mi=mi[mi.rindex('********** MACHINEINSTRS'):]
R={}
m=re.search(r'JAL @memcmp[^\n]*\n[^\n]*\n\d+B\t  (%\d+):gpr = COPY killed \$r0\n(?:[^\n]*\n){1,6}?[^\n]*data_is_empty[^\n]*\n[^\n]*\n\d+B\t  (%\d+):gpr = COPY killed \$r0',mi)
R['coll_native'],R['coin_present']=m.group(1),m.group(2)
m=re.search(r'(%\d+):gpr = COPY killed \$r0\n\d+B\t  (%\d+):gpr = MOV_ri 0\n\d+B\t  (%\d+):gpr = MOV_ri 0\n\d+B\t  JNE_ri \1:gpr, 0',mi)
R['do_coin'],R['do_collect']=m.group(2),m.group(3)
lo=int(re.search(r'(\d+)B\t  %s:gpr = MOV_ri 0'%R['do_coin'],mi).group(1))
m=re.search(r'(%\d+):gpr = MOV_rr %stack.\d+._130.i',mi); R['clonebuf']=m.group(1) if m else None
print(R)
roots=[v for v in R.values() if v]+['%0']
out=subprocess.run(['python3',T+'/wtl.py',L,str(lo-500),str(lo+7000)]+roots,capture_output=True,text=True).stdout
inv={v:k for k,v in R.items()}; inv['%0']='accounts'
for l in out.split('\n'):
    m=re.search(r'root=(%\d+)',l)
    if m: print('%-12s'%inv.get(m.group(1),'?'),l)
