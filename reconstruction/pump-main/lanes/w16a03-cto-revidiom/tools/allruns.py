import sys,os,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import revidiom,runs,shape
O=runs.cto_insns('orig'); d=json.load(open(shape.OUT+'/runs_main.json'))
for i,j in d['runs']:
    if j-i>=2: revidiom.lookup(O[i][0],O[j-1][0]+8,4,3); sys.stdout.flush()
