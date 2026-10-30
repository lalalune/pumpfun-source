from pathlib import Path
import sys,json,gzip,hashlib,subprocess,difflib,struct,collections
P=Path(r'C:/Users/ahi20/Documents/ChatGPT/pumpfun-contribution-review');R=Path(r'C:/Users/ahi20/Documents/ChatGPT/pumpfun-source');B=Path(__file__).parent;role=sys.argv[1];label={'parent':'multihop-tokens-quote','candidate':'multihop-sell-sub3'}[role];L='/home/ahi200/pumpfun-work/20261029-pump-legacy-exact-sol/'
sys.path[:0]=[str(R/'scripts'),str(P/'pump-legacy-exact-sol-20261029/tools')];import census;census.ROOT=R
blob=subprocess.check_output(['wsl','-d','Ubuntu','-u','root','--','cat',L+label+'/symbols.so']);path=B/(role+'-symbols.so');path.write_bytes(blob)
for n in ['result.json','launch.json','build.log']:(B/(role+'-'+n)).write_bytes(subprocess.check_output(['wsl','-d','Ubuntu','-u','root','--','cat',L+label+'/'+n]))
report=census.census(path);(B/(role+'-census.json.gz')).write_bytes(gzip.compress(json.dumps(report,sort_keys=True).encode(),mtime=0));old=json.loads(gzip.decompress((P/'pump-multihop-clock-20261029/candidate-census.json.gz').read_bytes()));se=lambda r,raw=False:{w['start'] for w in r['windows'] if w['raw_match'] if raw} if raw else {w['start'] for w in r['windows'] if w['normalized_matches']}
original=(R/'evidence/original/pump/deployed.so').read_bytes();os=census.sections(original);cs=census.sections(blob);ob=census.body(original,os,0x5b3b0,18584);on,orr=census.normalize(ob,0x5b3b0,os);symbol='_ZN14pump_recovered15multi_hop_curve8swap_hop17ha6abe54e52afef15E';target=next(x for x in census.functions(blob) if x[2]==symbol);a,size,_=target;body=census.body(blob,cs,a,size);norm,refs=census.normalize(body,a,cs);changes=[x for x in difflib.SequenceMatcher(None,[on[i:i+8] for i in range(0,len(on),8)],[norm[i:i+8] for i in range(0,len(norm),8)],autojunk=False).get_opcodes() if x[0]!='equal'];fns={x[0]:x for x in census.functions(blob)};calls=[]
for i in range(0,size,8):
 op,reg,off,imm=struct.unpack_from('<BBhi',body,i)
 if op!=0x85:continue
 ta=a+i+8+8*imm;f=fns.get(ta);row={'offset':hex(i),'target':hex(ta)}
 if f:
  bb=census.body(blob,cs,ta,f[1]);nn,rr=census.normalize(bb,ta,cs);row.update(symbol=f[2],size=f[1],raw_sha256=hashlib.sha256(bb).hexdigest(),normalized_sha256=hashlib.sha256(nn).hexdigest())
 calls.append(row)
r={'image_sha256':hashlib.sha256(blob).hexdigest(),'target_symbol':symbol,'start':hex(a),'size':size,'raw_sha256':hashlib.sha256(body).hexdigest(),'normalized_sha256':hashlib.sha256(norm).hexdigest(),'aligned_differing_slots_diagnostic':sum(max(j-i,l-k) for _,i,j,k,l in changes),'alignment_changes':changes,'calls':calls,'counts':report['counts'],'lost_normalized_vs_1164_parent':sorted(se(old)-se(report)),'gained_normalized_vs_1164_parent':sorted(se(report)-se(old)),'lost_raw_vs_1164_parent':sorted(se(old,True)-se(report,True)),'gained_raw_vs_1164_parent':sorted(se(report,True)-se(old,True))};(B/(role+'-measurement.json')).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['alignment_changes','calls']},indent=2));print('CALLS',len(calls),'CLOCK',[(x['offset'],x['symbol']) for x in calls if 'clock' in x.get('symbol','')])
