#!/usr/bin/env python3
"""Check external-account decoder errors with normal offline test-owned signatures."""
import argparse,base64,hashlib,json,pathlib,re
from solders.transaction import Transaction
import fees_sharing_create_differential as sharing
ROOT=pathlib.Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/'evidence/original/pump_fees/deployed.so'
FIELDS=['error','sharing','curve','payer_lamports','authority_lamports','sharing_lamports','pool','pool_lamports','curve_lamports','events','inner']
def errors(result):
 return [re.sub(r'AnchorError thrown in [^ ]+:\d+\.', 'AnchorError thrown in <source>.', line) for line in result['logs'] if 'AnchorError' in line]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--baseline',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();rows=[]
 for name,length,bad_bool in [('global',740,8),('curve',82,48),('pool',261,243)]:
  for kind in ['short','discriminator','boolean']:
   c={'name':name+'-'+kind}
   if name=='pool':c.update(tokens=0,pool=True)
   if kind=='short':c[name+'_length']=7
   elif kind=='discriminator':c[name+'_patches']=[(0,'0000000000000000')]
   else:c[name+'_patches']=[(bad_bool,'02')]
   x,y=sharing.run(c,ORIGINAL),sharing.run(c,a.candidate)
   for result in [x,y]:assert all(Transaction.from_bytes(base64.b64decode(result['transaction_base64'])).verify_with_results())
   assert x['error'] is not None and errors(x),c
   diff=[k for k in FIELDS if x[k]!=y[k]]
   if errors(x)!=errors(y):diff.append('anchor_error_logs_without_source_location')
   row={'case':c,'original':x,'candidate':y,'original_errors':errors(x),'candidate_errors':errors(y),'signature_verification':True,'mismatches':diff}
   if a.baseline:row['baseline']=sharing.run(c,a.baseline);row['baseline_errors']=errors(row['baseline'])
   rows.append(row)
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 d={'scope':'Nine normal-signature synthetic external-account decoder rejections. Compare error logs excluding only source file/line, selected state/balances/events/inner calls; raw logs retained. Not whole-program/security/byte identity.','original_sha256':sha(ORIGINAL),'candidate_sha256':sha(a.candidate),'case_count':len(rows),'cases':rows,'mismatches':[r['case']['name'] for r in rows if r['mismatches']]}
 if a.baseline:d['baseline_sha256']=sha(a.baseline)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'cases':len(rows),'mismatches':d['mismatches']}));assert not d['mismatches']
if __name__=='__main__':main()
