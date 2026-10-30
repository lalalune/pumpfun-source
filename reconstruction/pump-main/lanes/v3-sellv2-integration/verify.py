"""Verify retained receipts; optionally rescore actual compiler outputs."""
import argparse,base64,gzip,hashlib,json,re,sys,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[3]
def need(ok,message):
 if not ok:raise ValueError(message)
def sha(data):return hashlib.sha256(data).hexdigest()
def load(name):return json.loads((HERE/name).read_text())
def logs(r):return [x for x in r['logs'] if not re.fullmatch(r'Program [1-9A-HJ-NP-Za-km-z]+ consumed \d+ of \d+ compute units',x)]
def membership_gate(base,candidate):
 need(set(base)==set(candidate) and len(base)==1035,'window census differs')
 for k,b in base.items():
  for field in ['normalized','raw']:need(not b[field] or candidate[k][field],f'lost {field} {hex(int(k))}')
 gains={hex(int(k)) for k,b in base.items() if candidate[k]['normalized'] and not b['normalized']}
 need(gains=={'0x83c00','0x144508'},f'unexpected gains {gains}')
def main():
 p=argparse.ArgumentParser();p.add_argument('--signatures',action='store_true');p.add_argument('--binary',type=Path);p.add_argument('--objdump');a=p.parse_args()
 s=load('SUMMARY.json')
 for name,h in s['artifacts'].items():need(sha((HERE/name).read_bytes())==h,'artifact hash '+name)
 inputs=load('source-inputs.json')
 for f,h in inputs['candidate'].items():need(sha((ROOT/f).read_bytes())==h,'candidate source '+f)
 for f,h in s['tooling'].items():need(sha((ROOT/f).read_bytes())==h,'tooling '+f)
 with tarfile.open(HERE/'control-source.tar.gz') as t:
  need(set(t.getnames())==set(inputs['control']),'archive census')
  for f,h in inputs['control'].items():need(sha(t.extractfile(f).read())==h,'control source '+f)
 base=load('main-memberships.json')['windows'];combined=load('combined-memberships.json')['windows'];membership_gate(base,combined)
 for cohort in ['execute-only','sell-only']:
  rows=load(cohort+'-memberships.json')['windows']
  losses=[hex(int(k)) for k,b in base.items() if b['raw'] and not rows[k]['raw']]
  need(losses==['0xa868'],cohort+' raw loss control')
 for target in ['0x83c00','0x144508']:
  d=load('call-audit-'+target+'.json');need(d['original']==d['candidate'],'callee order '+target)
 for key in ['candidate_sha256','unstripped_sha256']:need(s['builds']['combined'][key]==s['builds']['repeat'][key],'repeat '+key)
 total=0
 for suite,fields in [('buy',['error','accounts','inner_instructions','event_payloads','return_data']),('sell',['error','accounts','inner','events','return_data'])]:
  d=json.loads(gzip.decompress((HERE/f'runtime-{suite}.json.gz').read_bytes()))
  need(len(d['rows'])==d['case_count']==s['runtime'][suite]['cases'],'runtime census')
  need(d['images']['candidate']==s['builds']['combined']['candidate_sha256'],'runtime candidate binding')
  need(d['images']['control']==s['builds']['main']['candidate_sha256'],'runtime control binding')
  need(d['images']['original']==sha((ROOT/'evidence/original/pump/deployed.so').read_bytes()),'original binding')
  for row in d['rows']:
   rs=row['receipts'];need(set(rs)=={'original','control','candidate'},'receipt census')
   for image in ['control','candidate']:
    need(all(rs['original'][f]==rs[image][f] for f in fields),'runtime fields')
    need(logs(rs['original'])==logs(rs[image]),'runtime logs')
   if a.signatures:
    from solders.transaction import Transaction
    for receipt in rs.values():
     tx=Transaction.from_bytes(base64.b64decode(receipt['transaction_base64']));v=tx.verify_with_results();need(bool(v) and all(v),'transaction signature')
   total+=3
 if a.binary:
  sys.path.insert(0,str(ROOT/'reconstruction/harness'));import score
  if a.objdump:score.OBJDUMP=a.objdump
  measured={str(k):v for k,v in score.score(a.binary).items()};membership_gate(base,measured)
  need(sha(a.binary.read_bytes())==s['builds']['combined']['unstripped_sha256'],'binary binding')
 print(json.dumps({'verified':True,'windows':1035,'normalized':1026,'raw':277,'executions':total,'signatures_checked':a.signatures,'binary_rescored':bool(a.binary)}))
if __name__=='__main__':main()
