#!/usr/bin/env python3
"""SBF fee configuration differential with boundary values and recipient constraints."""
import argparse,hashlib,itertools,json,pathlib,struct
from pump_amm_admin_differential import Harness,ROOT,RAW

def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
 original=ROOT/'evidence/original/pump_amm/deployed.so';left,right=Harness(original),Harness(a.candidate)
 recipients=bytes(RAW[57:313]);authority=bytes(RAW[321:353]);rows=[]
 def test(lp,protocol,creator,rs=recipients,auth=authority,mutation=None,raw=None):
  payload=struct.pack('<QQ',lp,protocol)+rs+struct.pack('<Q',creator)+auth if raw is None else raw
  x,y=left.query(payload,mutation=mutation,instruction='update_fee_config'),right.query(payload,mutation=mutation,instruction='update_fee_config')
  same=all(x[k]==y[k] for k in ['error','state_hex','event_logs','rollback'])
  rows.append({'payload_hex':payload.hex(),'mutation':mutation,'original':x,'candidate':y,'match':same})
 for values in itertools.product([0,1,999,1000,1001,2**64-1],repeat=3):test(*values)
 chunks=[recipients[i:i+32] for i in range(0,256,32)]
 sets=[bytes(256),bytes([1])*256,b''.join(reversed(chunks))]
 for i in range(8):
  changed=chunks.copy();changed[i]=bytes(32);sets.append(b''.join(changed))
  for j in range(i):changed=chunks.copy();changed[i]=changed[j];sets.append(b''.join(changed))
 for rs in sets:
  for values in [(0,0,0),(1000,1000,1000),(1001,0,0)]:test(*values,rs=rs)
 for b in [0,1,255]:test(1,2,3,auth=bytes([b])*32)
 for mutation in ['outsider','unsigned','readonly','owner','discriminator','truncated','event','program','noncanonical_config']:
  test(1,2,3,mutation=mutation)
 data=struct.pack('<QQ',1,2)+recipients+struct.pack('<Q',3)+authority
 for n in [0,7,8,15,16,271,272,279,280,311]:test(0,0,0,raw=data[:n])
 test(0,0,0,raw=data+b'ignored')
 failures=[i for i,x in enumerate(rows) if not x['match']];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 report={'scope':'SBF update_fee_config handler only, not whole-program equality.','original_sha256':left.sha256,'candidate_sha256':right.sha256,'script_sha256':sha(pathlib.Path(__file__)),'case_count':len(rows),'mismatches':failures,'cases':rows}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,separators=(',',':'))+'\n')
 print(json.dumps({'case_count':len(rows),'mismatches':failures[:20],'mismatch_count':len(failures)}))
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
