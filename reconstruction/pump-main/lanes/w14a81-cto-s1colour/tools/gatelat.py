import sys,os,re,json,subprocess
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__))
sys.argv=['wscan','x','y']
src=open(T+'/wscan.py').read().split("if __name__=='__main__':")[0]
def one(name):
    g={'__name__':'w','__file__':T+'/wscan.py'}; 
    t=open('rx/%s/m.ll'%name).read(); s=t.index('define hidden { i64, ptr } @_ZN14pump_recovered9admin_cto7execute'); e=t.index('\n}\n',s)
    body=t[s:e]; ms=list(re.finditer(r'\n  br i1 (%[\w.]+), label %([\w.$"]+), label %([\w.$"]+)\n',body))
    gi=[i for i,m in enumerate(ms) if re.search(r'\n  '+re.escape(m.group(1))+r' = icmp ne i8 %_\d+\.sroa\.0\.0, 2\n',body)]
    sys.argv=['wscan','rx/%s/m.ll'%name,'/dev/null']; exec(src,g)
    out=[]
    for w in [None,(8,1),(2,1),(20,12),(1,8)]:
        r=g['run']([] if w is None else [(gi[0],w[0],w[1])]); r['name']=name; r['gi']=gi; out.append(r)
    return out
if __name__=='__main__':
    names=sys.argv_names=[l.strip() for l in open(sys.argv_save) ] if False else None
    names=[d for d in os.listdir('rx') if (d.startswith('lat_') or d.startswith('r1_') or d in ('m0','s1'))]
    with Pool(4) as P, open('gatelat.jsonl','w') as f:
        for res in P.imap_unordered(one,names):
            for r in res: f.write(json.dumps(r)+'\n')
