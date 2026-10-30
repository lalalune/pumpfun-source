#!/usr/bin/env python3
"""Read-only ordered whole-log audit of an actual Pump report; only compute-meter lines excluded."""
from pathlib import Path
import argparse,gzip,hashlib,json,os,re,tempfile
ORIGINAL='7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
# A compute-meter line names a pubkey. One character also matches the old
# class, so a real log could be dropped as if it were a meter line.
UNITS=re.compile(r'^Program [1-9A-HJ-NP-Za-km-z]{32,44} consumed [0-9]+ of [0-9]+ compute units$')
def require(ok,message):
 if not ok:raise ValueError(message)
def audit(report,candidate_sha256,expected_pairs=None):
 require(report['original_sha256']==ORIGINAL and report['candidate_sha256']==candidate_sha256,'Actual report/image binding differs');expected=report['case_count']if expected_pairs is None else expected_pairs;require(type(expected)is int and expected>0 and type(report['case_count'])is int and report['case_count']==expected,'Expected actual case count differs');pairs=0;mismatches=[]
 def getlogs(outcome):
  value=outcome.get('logs')
  if value is None and isinstance(outcome.get('metadata'),dict):value=outcome['metadata'].get('logs')
  require(isinstance(value,list)and all(isinstance(s,str)for s in value),'Paired execution lacks actual ordered logs');return value
 def walk(value,path):
  nonlocal pairs
  if isinstance(value,dict):
   if 'original' in value or 'candidate' in value:
    require(isinstance(value.get('original'),dict)and isinstance(value.get('candidate'),dict),'Execution pair is incomplete or malformed')
    left,right=getlogs(value['original']),getlogs(value['candidate']);pairs+=1;a=[s for s in left if not UNITS.fullmatch(s)];b=[s for s in right if not UNITS.fullmatch(s)]
    if a!=b:mismatches.append({'path':path,'original_ordered_logs':a,'candidate_ordered_logs':b})
   for name,item in value.items():
    if name not in ['original','candidate']:walk(item,path+[str(name)])
  elif isinstance(value,list):
   for index,item in enumerate(value):walk(item,path+[str(index)])
 walk(report['suites'],[]);require(pairs==expected,'Report pair/log coverage differs')
 return {'scope':__doc__,'candidate_sha256':candidate_sha256,'original_sha256':ORIGINAL,'case_pairs':pairs,'strict_ordered_log_mismatch_cases':len(mismatches),'source_normalization':None,'excluded_log_category':'Only complete runtime compute-meter lines matching UNITS; all other log text/order preserved.','mismatches':mismatches,'new_execution_or_signature_coverage_claimed':False}
def main():
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--expected-pairs',type=int);a=p.parse_args()
 raw=a.report.read_bytes();report=json.loads(gzip.decompress(raw)if raw.startswith(b'\x1f\x8b')else raw);candidate=a.candidate.read_bytes();result=audit(report,hashlib.sha256(candidate).hexdigest(),a.expected_pairs);result['source_report_sha256']=hashlib.sha256(raw).hexdigest();result['checker_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();require(not a.output.exists(),'Output already exists')
 staged=None;published=False
 try:
  with tempfile.NamedTemporaryFile('w',dir=a.output.parent,prefix='.'+a.output.name+'.',delete=False,encoding='utf-8',newline='\n')as stream:
   staged=Path(stream.name);stream.write(json.dumps(result,indent=2)+'\n');stream.flush();os.fsync(stream.fileno())
  require(a.report.read_bytes()==raw and a.candidate.read_bytes()==candidate,'Input changed during audit');os.link(staged,a.output);published=True;require(a.report.read_bytes()==raw and a.candidate.read_bytes()==candidate,'Input changed during audit')
 except BaseException:
  if published:a.output.unlink(missing_ok=True)
  raise
 finally:
  if staged is not None:staged.unlink(missing_ok=True)
 print(json.dumps({k:v for k,v in result.items()if k!='mismatches'},indent=2));require(not result['mismatches'],'Strict ordered logs differ')
if __name__=='__main__':main()
