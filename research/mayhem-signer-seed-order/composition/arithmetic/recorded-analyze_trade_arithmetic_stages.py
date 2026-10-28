from pathlib import Path
import hashlib,importlib.util,json,re
W=Path(__file__).resolve().parent;P=W/'mayhem-trade-arithmetic-lowering';D=P/'baseline-stages';V=W/'mayhem-current-cpi-order-control/publication'
def module(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
v=module('arith_v',V/'verify.py');reader=module('arith_reader',V/'reader.py')
e=reader.Elf(D/'symbols.so');fs=v.functions(e);syms={s['name']:s['value'] for s in e.symbols};original=reader.Elf(W/'mayhem-current-trade-control/original.so');originals={r['id']:original.window(r['start'],r['end']) for r in v.read(V/'reference/original-windows.json')};ids={v.shape(w):k for k,w in originals.items()}
log=(D/'stderr.log').read_text(encoding='utf-8');headers=json.loads((D/'diagnostic-headers.json').read_bytes());result=[]
for index,header in enumerate(headers):
    a=log.index(header);z=log.index('# End machine code',a);z=log.index('\n',z);text=log[a:z+1];calls=[];block=None
    for line in text.splitlines():
        line=re.sub(r'^\d+[Berd]\s+','',line)
        if line.startswith('bb.'):block=line.split()[0].rstrip(':')
        m=re.match(r'\s*JAL\s+[@&]("[^"]+"|[^,]+),',line)
        if m:
            name=m[1].strip('"');address=syms[name];tag=ids.get(v.shape(fs[address]),'?') if address in fs else name;calls.append(dict(block=block,name=name,tag=tag))
        elif re.search(r'\bJAL\w*\b',line):raise ValueError('unparsed machine call')
    name=str(index)+'-'+header.split('(')[-1].split(')')[0]+'.mir';(P/name).write_text(text,encoding='utf-8',newline='\n');row=dict(header=header,path=name,sha256=hashlib.sha256(text.encode()).hexdigest(),calls=calls);result.append(row)
    print(index,header,'calls',len(calls),'first18',[(x['block'],x['tag']) for x in calls[:18]])
assert all(r['calls'] for r in result)
out=P/'stage-observations.json';backup=P/'stage-observations-before-slot-index-fix.json'
if out.exists() and not backup.exists():backup.write_bytes(out.read_bytes())
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
for p in json.loads((D/'pass-arguments.json').read_bytes()):print('pipeline passes',len(p.split()),'sinking',p.count('-machine-sink'),'scheduler',p.count('-machine-scheduler'),'regallocgreedy',p.count('-greedy'))
