#!/usr/bin/env python3
"""jfix2.py <m.ll|x.s> <tag>: post-RA relayout oracle for the validate-exit join %bb56.i (w14a93 jfix generalised to any
%bb9.iNNN name): when J is laid out before validate's second arm chain, move the chain (%bb9.iN .. block before %bb5.i)
in front of J, as main and the original lay it out. Writes <tag>.s/<tag>_re.s/_re.bin; prints relay ratio, regceil, fbound."""
import sys,re,importlib.util,subprocess,json,os
F=os.path.dirname(os.path.abspath(__file__)); m,tag=sys.argv[1:3]; tag=os.path.abspath(tag); os.chdir(F)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
if m.endswith('.ll'): subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',m,'-filetype=asm','-o',tag+'.s'],check=True)
else: subprocess.run(['cp',m,tag+'.s'],check=True)
sv=sys.argv; sys.argv=['x']
sp=importlib.util.spec_from_file_location('relay','relay.py'); R=importlib.util.module_from_spec(sp); sp.loader.exec_module(R); sys.argv=sv
pre,bl,post=R.parse(tag+'.s'); names=[n for n,b in bl]
ir=[(re.search(r'#\s*(%\S+)',b[0]).group(1) if re.search(r'#\s*(%\S+)',b[0]) else '') for n,b in bl]
j=ir.index('%bb56.i'); bs=[k for k in range(j,len(ir)) if re.fullmatch(r'%bb9\.i\d+',ir[k])]
if not bs: print(json.dumps({'tag':tag,'note':'J already after second arm'})); sys.exit()
b0=bs[0]; be=[k for k in range(b0,len(ir)) if re.fullmatch(r'%bb5\.i\d*',ir[k])][0]-1
spec=','.join(names[b0:be+1]+[names[j],'*'])
r=subprocess.run(['python3','relay.py',tag+'.s',tag+'_re.s',spec],capture_output=True,text=True)
subprocess.run(['bash','asm2bin.sh',tag+'_re.s'],check=True)
rc=subprocess.run(['python3','regceil.py',tag+'_re.bin'],capture_output=True,text=True).stdout.split('L2')[-1].strip()
fb=subprocess.run(['python3','fbound.py',tag+'_re.bin'],capture_output=True,text=True).stdout.strip()
print(json.dumps({'tag':os.path.basename(tag),'moved':be+1-b0,'relay':r.stdout.strip()[-300:],'err':r.stderr[-500:],'regceil':rc,'fbound':fb[-300:]}))
