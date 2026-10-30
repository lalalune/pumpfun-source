"""Synthetic equal-artifact benchmark; does not load or execute a captured ELF."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import time
from compare import compare

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--bytes',type=int,default=4*1024*1024)
 parser.add_argument('--repetitions',type=int,default=5)
 args=parser.parse_args()
 if args.bytes<1 or args.repetitions<1:parser.error('positive bounds are required')
 original=b'x'*args.bytes
 candidate=bytes(bytearray(original))
 times=[]
 for _ in range(args.repetitions):
  start=time.perf_counter();result=compare(original,candidate);times.append(time.perf_counter()-start)
  if result['full_byte_equality'] is not True or result['first_difference'] is not None or result['different_positions_in_shared_length']!=0:raise ValueError('comparison semantics changed')
 print(json.dumps({'bytes':args.bytes,'repetitions':args.repetitions,'median_seconds':statistics.median(times),'source_sha256':hashlib.sha256(Path(__file__).with_name('compare.py').read_bytes()).hexdigest(),'comparison':result},indent=2))
if __name__=='__main__':main()
