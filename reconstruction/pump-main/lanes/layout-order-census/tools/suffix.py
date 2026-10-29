import sys; sys.path.insert(0,sys.argv[1])
import fastmodel as F
OUT=sys.argv[2]
M=F.Model(OUT+'/out/main2/unstripped.so',OUT+'/analysis/m2-refined.json')
base=M.eval(M.cst)
Lc=[a for a in M.cst if M.region(a)=='L']   # includes extras in L
Lo=sorted([a for a in Lc if a in M.inv],key=lambda a:M.inv[a])
pre=[a for a in M.cst if M.region(a)=='U']; post=[a for a in M.cst if M.region(a)=='D']
for k in list(range(455,424,-1)):
    tail=Lo[k:]; ts=set(tail)
    order=pre+[a for a in Lc if a not in ts]+tail+post
    r=M.eval(order)
    print(k, hex(M.inv[Lo[k]]) if k<len(Lo) else '-', len(r), len(r-base), len(base-r), M.names[Lo[k]][:60] if k<len(Lo) else '')
