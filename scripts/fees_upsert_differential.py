#!/usr/bin/env python3
"""Synthetic local fee-tier splice tests with actual admin signatures."""
from fees_config_differential import *
def cases():
 out=[];rng=random.Random(774)
 for name in ['upsert_fee_tiers','upsert_stable_fee_tiers']:
  def add(label,offset,new,**kw):out.append({'name':name+'-'+label,'instruction':name,'arg':(tiers(new)+bytes([offset])).hex(),'allocation':4097,**kw})
  for offset in [0,1,2,3,49,50,51,255]:
   for count in [0,1,2,49,50,51]:add(f'offset-{offset}-count-{count}',offset,[(offset+i,(1,2,3)) for i in range(count)])
  for allocation in [2512,4072,4073,4096,4097,5000]:
   for offset in [0,1,2]:add(f'allocation-{allocation}-offset-{offset}',offset,[(100+offset,(4,5,6))],allocation=allocation)
  for ts in [[(0,(0,0,0))],[(0,(10001,0,0))],[(0,(2**64-1,1,0))],[(0,(1,2,3)),(0,(4,5,6))],[(1,(1,2,3)),(0,(1,2,3))],[(2**128-1,(1,2,3))]]:
   for offset in [0,1,2,255]:add('input-'+str(ts)+'-'+str(offset),offset,ts)
  for mutation in ['owner','key','bump','discriminator','admin','config_program','event','program','unsigned','readonly']+['accounts:'+str(n) for n in range(5)]+['length:'+str(n) for n in [0,8,69,2511,2512,4073]]+['normal_count:'+str(n) for n in [0,1,60,2**32-1]]:add(mutation,0,[(0,(1,2,3))],mutation=mutation)
  for count in [0,1,2,30,50,60]:
   add('old-count-'+str(count),0,[(0,(1,2,3))],old_normal=[(i,(4,5,6)) for i in range(count)],old_stable=[(i,(7,8,9)) for i in range(count)],allocation=8192)
  for offset in [0,1]:
   for oldfees in [(10001,0,0),(2**64-1,1,0)]:
    add('old-invalid-'+str(offset)+'-'+str(oldfees),offset,[(offset+1,(1,2,3))],old_normal=[(0,oldfees),(100,(1,2,3))],old_stable=[(0,oldfees),(100,(1,2,3))])
  for length in [0,1,2,3,4,19,20,27,28,43,44,45,46,47]:
   add('arg-length-'+str(length),0,[(0,(1,2,3))]);out[-1]['arg']=out[-1]['arg'][:length*2]
  for i in range(150):
   old_count=rng.randrange(0,51);offset=rng.randrange(0,old_count+2);new_count=rng.randrange(0,52);new=[(rng.randrange(1000),tuple(rng.randrange(4000) for _ in range(3))) for _ in range(new_count)];new.sort()
   add('random-'+str(i),offset,new,old_normal=[(j*20,(1,2,3)) for j in range(old_count)],old_stable=[(j*20,(4,5,6)) for j in range(old_count)],allocation=8192)
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();o=ConfigFixture(ROOT/'evidence/original/pump_fees/deployed.so');b=ConfigFixture(a.candidate) if a.candidate else None;rows=[];bad=[]
 for c in cases():
  x=o.run(c);y=b.run(c) if b else None;match=all(x[k]==y[k] for k in ['error','data_hex','lamports','owner','balance_deltas','events','inner_instructions']) if b else None;rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:bad.append(c['name'])
 report={'scope':'Two fee-tier upsert handlers, normally signed local synthetic state, state/errors/events/inner instructions. Not complete byte identity or security assessment.','original_sha256':o.program_sha256,'candidate_sha256':b.program_sha256 if b else None,'case_count':len(rows),'mismatches':bad,'cases':rows};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8',newline='\n');print(json.dumps({'case_count':len(rows),'mismatches':bad[:20]}))
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
