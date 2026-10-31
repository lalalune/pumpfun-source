#!/usr/bin/env python3
"""jfix.py <m.ll> <tag>: asm relayout oracle for the sweep join (IR %bb56.i, 'J'): when J is laid out right after the
first arm, move the second arm chain (%bb9.i116 .. block before %bb5.i) in front of J, as main/the original lay it out.
Writes <tag>.s/<tag>_re.s/.bin and prints ratio, regceil, fbound. Experiment only (post-RA block move)."""
import sys,re,importlib.util,subprocess,json,os
F=os.path.dirname(os.path.abspath(__file__)); os.chdir(F)
m,tag=sys.argv[1:3]
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
LLC=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a93-cto-pdaheadra/llvmb/bin/llc') if os.environ.get('RAPRIO_FORCE') else SDK+'/llc'
subprocess.run([LLC,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',m,'-filetype=asm','-o',tag+'.s'],check=True)
sys.argv=['x']
sp=importlib.util.spec_from_file_location('relay','relay.py'); R=importlib.util.module_from_spec(sp); sp.loader.exec_module(R)
pre,bl,post=R.parse(tag+'.s'); names=[n for n,b in bl]
ir=[(re.search(r'#\s*(%\S+)',b[0]).group(1) if re.search(r'#\s*(%\S+)',b[0]) else '') for n,b in bl]
j=ir.index('%bb56.i'); bs=[k for k in range(j,len(ir)) if ir[k]=='%bb9.i116']
if not bs: print(json.dumps({'tag':tag,'note':'J already after second arm'})); sys.exit()
b0=bs[0]; be=[k for k in range(b0,len(ir)) if ir[k]=='%bb5.i'][0]-1
spec=','.join(names[b0:be+1]+[names[j],'*'])
r=subprocess.run(['python3','relay.py',tag+'.s',tag+'_re.s',spec],capture_output=True,text=True).stdout.strip()
subprocess.run(['bash','asm2bin.sh',tag+'_re.s'],check=True)
rc=subprocess.run(['python3','../tools/regceil.py',tag+'_re.bin'],capture_output=True,text=True).stdout.split('L2')[-1].strip()
fb=subprocess.run(['python3','fbound.py',tag+'_re.bin'],capture_output=True,text=True).stdout.split(' ',1)[-1].strip()
print(json.dumps({'tag':tag,'relay':json.loads(r),'regceil':rc,'fbound':json.loads(fb)}))
