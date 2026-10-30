#!/usr/bin/env python3
"""Reject reported backend errors even when Cargo returned zero; no runtime acceptance."""
import argparse,gzip,hashlib,json,re
from pathlib import Path
ANSI=re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
STACK=re.compile(r'^Error: Function (.*?) Stack offset of (-?\d+) exceeded max offset of (\d+) by (\d+) bytes.*?Estimated function frame size: (\d+) bytes\.')
def inspect(path):
 path=Path(path);raw=path.read_bytes();decoded=gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw
 errors=[]
 for number,line in enumerate(decoded.decode('utf-8').splitlines(),1):
  plain=ANSI.sub('',line).lstrip()
  if not plain.startswith('Error:'):continue
  row={'line_number':number,'text':line,'kind':'backend_error'};m=STACK.match(plain)
  if m:row.update(kind='stack_offset_exceeded',function=m[1],reported_offset=int(m[2]),maximum_offset=int(m[3]),excess_bytes=int(m[4]),estimated_frame_bytes=int(m[5]))
  errors.append(row)
 return {'input':str(path),'input_sha256':hashlib.sha256(raw).hexdigest(),'decoded_sha256':hashlib.sha256(decoded).hexdigest(),'backend_errors':errors}
def check(paths):
 rows=[inspect(p) for p in paths];count=sum(len(r['backend_errors']) for r in rows)
 return {'checked':True,'logs':rows,'backend_error_count':count,'diagnostic_gate_passed':count==0,'program_readiness_proven':False,'compiler_or_strip_exit_codes_rewritten':False,'runtime_executions':0,'limit':'No reported backend errors is only a diagnostic gate; it does not establish stack safety, verifier acceptance, runtime or SDK equivalence.'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--log',type=Path,action='append',required=True);a=p.parse_args()
 report=check(a.log);print(json.dumps(report,indent=2));return 0 if report['diagnostic_gate_passed'] else 1
if __name__=='__main__':raise SystemExit(main())
