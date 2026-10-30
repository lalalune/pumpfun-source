"""Normally signed root creation followed by depth-one SOL-root nested creation."""
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")
from pathlib import Path
import importlib.util,json,gzip,struct,hashlib,argparse
from pump_amm_reusable_harness import pin_program
ROOT=Path(__file__).resolve().parents[1]
def load():
 s=importlib.util.spec_from_file_location('nested_fixture',ROOT/'scripts/pump_create_nested_fixture.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def prepare(c):
 boot=load();boot.MINT=boot.OTHER;boot.CURVE=boot.Pubkey.find_program_address([b'bonding-curve',bytes(boot.MINT.pubkey())],boot.PROGRAM)[0]
 b=boot.run({'instruction':'create_v2','name':'Synthetic Quote','symbol':'QUOTE',**c.get('root',{})});assert b['error'] is None,b['error']
 accounts={k:v for k,v in b['after'].items() if v is not None and v!=b['before'][k]}
 return b,{'instruction':'create_v2','quote':True,'quote_token22':True,'quote_whitelisted':False,'quote_control':True,'control_entries':[],'nested':True,'bootstrap_accounts':accounts,**c.get('child',{})}
def cases():
 rows=[{'name':'fresh'}]
 for off,values in [(73,[10**12,1073000000000000,2*10**15]),(81,[1,1000,30000000000,10**12]),(89,[1,10**9,793100000000000]),(1087,[0,1,5,6,255])]:
  for n in values:rows.append({'name':f'child-global-{off}-{n}','child':{'global_patches':[(off,n.to_bytes(1 if off==1087 else 8,'little').hex())]}})
 for vq in [1,1000,10**7,10**8,10**9,10**10,29999999999,30000000000,30000000001,10**12,2**64-1]:rows.append({'name':f'root-quote-{vq}','root':{'global_patches':[(81,struct.pack('<Q',vq).hex())]}})
 for off,n in [(97,2*10**15),(89,500000000000000),(73,2*10**15)]:rows.append({'name':f'root-reserve-{off}','root':{'global_patches':[(81,struct.pack('<Q',10**9).hex()),(off,struct.pack('<Q',n).hex())]}})
 for extra in [{'wrong':'quote_bonding_curve'},{'nested':False},{'quote_whitelisted':True},{'quote_control':False},{'wrong':'quote_control'},{'readonly':'associated_quote_bonding_curve'},{'readonly':'user'},{'name':'x'*33},{'creator':str(load().Pubkey.default())},{'control_entries':[(str(load().OTHER.pubkey()),777)]}]:rows.append({'name':'context-'+str(extra),'child':extra})
 for bps in [0,1,123,300,301,10000,2**64-1]:rows.append({'name':f'creator-fee-{bps}','child':{'optional_args':(b'\0'+struct.pack('<Q',bps)).hex()}})
 rows.append({'name':'legacy-root','root':{'instruction':'create'},'child':{'quote_token22':False}})
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.candidate=pin_program(a.candidate) if a.candidate else None;rows=[];bad=[]
 h=load()
 for c in cases():
  boot,child=prepare(c);x=h.run(child);y=h.run(child,a.candidate) if a.candidate else None;diff=[k for k in ['before','after','error','events','inner','return'] if y is not None and x[k]!=y[k]];rows.append({'case':c,'bootstrap':boot,'child_fixture':child,'original':x,'candidate':y,'diff':diff})
  if diff:bad.append(c['name'])
 report={'scope':'Depth-one nested create_v2 from genuinely created normal SOL-root quote coins, ordinary signatures. No Mayhem, migrated pools or deeper chains recovered.','original_sha256':hashlib.sha256(pin_program(h.ORIGINAL).read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest() if a.candidate else None,'case_count':len(rows),'cases':rows,'mismatches':bad};a.output.write_bytes(gzip.compress(json.dumps(report,separators=(',',':')).encode(),mtime=0));print({'cases':len(rows),'mismatches':bad});assert not bad
if __name__=='__main__':main()
