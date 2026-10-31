# Faithful-anchor price on main 9120883 post-opt IR: volatiles removed, fee-tag phi [0,bb45],[1,bb65],[0,bb44] at bb75
# feeds the line-757 test (and optionally the pool CPI tag). Experiment only.
import subprocess,sys
from concurrent.futures import ThreadPoolExecutor
T='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a29-cto-devolrepay'
B=T+'/rx/main/m.ll'
V334='  %138 = load volatile i8, ptr %holder_key, align 1, !alias.scope !8547, !noalias !8582\n'
V338='  %167 = load volatile i8, ptr %holder_key, align 1, !alias.scope !8547, !noalias !8582\n'
BB75='bb75:                                             ; preds = %bb65.i, %bb44.i, %bb45.i\n'
PHI=BB75+'  %feetag = phi i64 [ 0, %bb45.i ], [ 1, %bb65.i ], [ 0, %bb44.i ]\n'
SW='  %switch53 = icmp eq i64 %1, 1'
SWP='  %switch53 = icmp eq i64 %feetag, 1'
CPI_OLD='i1 noundef zeroext %685, i64 noundef %1, i64 %2) #27'
CPI_NEW='i1 noundef zeroext %685, i64 noundef %feetag, i64 %2) #27'
P={
 'phi_main_novol':[(V334,''),(V338,''),(BB75,PHI),(SW,SWP)],
 'phi_main_novol_cpi':[(V334,''),(V338,''),(BB75,PHI),(SW,SWP),(CPI_OLD,CPI_NEW)],
 'phi_main_keep334':[(V338,''),(BB75,PHI),(SW,SWP)],
 'novol_nophi':[(V334,''),(V338,'')],
}
def run(n):
    args=['python3',T+'/tools/pv.py',B,'phi_'+n]
    for o,w in P[n]: args+=[o,w]
    r=subprocess.run(args,capture_output=True,text=True)
    return n,(r.stdout.strip() or r.stderr.strip()[-400:])
with ThreadPoolExecutor(4) as ex:
    for n,o in ex.map(run,sys.argv[1:] or list(P)): print(n,o,flush=True)
