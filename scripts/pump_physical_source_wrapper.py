#!/usr/bin/env python3
"""Canonicalize actual registry source symlinks, without remapping source text or coordinates."""
import os,sys,json,hashlib
from pathlib import Path
compiler=sys.argv[1];args=sys.argv[2:];registry=os.environ.get('PUMP_LOGICAL_REGISTRY_SRC','')
response=next((arg for arg in args if arg.startswith('@')),None)
if response is not None: raise SystemExit('response-file compiler input unsupported: '+response)
for i,arg in enumerate(args):
 if registry and arg.startswith(registry+'/') and arg.endswith('.rs'):
  p=Path(arg)
  if p.is_file():
   physical=p.resolve()
   assert p.read_bytes()==physical.read_bytes()
   args[i]=str(physical)
   if os.environ.get('PUMP_SOURCE_WRAPPER_LOG'):
    record={'original_source':arg,'physical_source':str(physical),'sha256':hashlib.sha256(physical.read_bytes()).hexdigest(),'cwd':os.getcwd()}
    fd=os.open(os.environ['PUMP_SOURCE_WRAPPER_LOG'],os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
    os.write(fd,(json.dumps(record)+'\n').encode());os.close(fd)
os.execv(compiler,[compiler,*args])
