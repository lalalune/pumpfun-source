import sys,json
sys.path.insert(0,sys.argv[1])
import fastmodel as F
M=F.Model(sys.argv[2],sys.argv[3])
sc=json.load(open(sys.argv[4]))['windows']
tot=0
for st in sorted(M.UN):
    a=M.pair.get(st)
    if a is None: print(hex(st),'unpaired');continue
    ob=M.wins[st]['bytes']; cb=M.units[a][0]; tot+=cb-ob
    print(hex(st), 'norm' if sc[str(st)]['normalized'] else '----', ob, cb, cb-ob, M.region(a), M.names[a][:80])
ex=[a for a in M.cst if a not in M.inv]
for a in ex: print('extra',hex(a),M.units[a][0],M.names[a][:90]); tot+=M.units[a][0]
print('total delta',tot, 'text delta', M.csec['.text']['size']-M.osec['.text']['size'])
