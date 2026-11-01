#!/usr/bin/env python3
"""Signed offline Surfpool holder-distribution comparisons with captured CPI programs."""
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")
import argparse,base64,hashlib,json,socket,struct,subprocess,sys,time,urllib.request
from pathlib import Path
from solders.hash import Hash
from solders.instruction import AccountMeta,Instruction
from solders.transaction import Transaction
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from surfpool_recording_vm import require_aligned_runs
import pump_holder_distribution_probe as fixture
import pump_holder_distribution_differential as suite
from types import SimpleNamespace
from solders.compute_budget import set_compute_unit_limit
f=SimpleNamespace(Pubkey=fixture.Pubkey,PAYER=fixture.PAYER,AUTH=fixture.AUTH,OTHER=fixture.OTHER,set_compute_unit_limit=set_compute_unit_limit)
for attr,name,folder in [('PUMP','pump','original'),('PROGRAM','pump_fees','original'),('AMM','pump_amm','original'),('TOKEN','spl_token','dependencies'),('TOKEN22','spl_token_2022','dependencies'),('ATA','associated_token','dependencies')]:setattr(f,attr,f.Pubkey.from_string(json.loads((ROOT/f'evidence/{folder}/{name}/capture.json').read_text())['program']))
COMPUTE=f.Pubkey.from_string('ComputeBudget111111111111111111111111111111')
PORT=20251
sha=lambda data:hashlib.sha256(data).hexdigest()
class RecordingVM:
 def __init__(self,vm):self.vm=vm;self.keys=set();self.accounts={};self.transaction=None
 def __getattr__(self,name):return getattr(self.vm,name)
 def set_account(self,key,account):self.keys.add(key);return self.vm.set_account(key,account)
 def send_transaction(self,tx):
  self.transaction=tx;self.accounts={}
  self.keys.update(tx.message.account_keys)
  for key in self.keys:
   a=self.vm.get_account(key)
   if a is None:self.accounts[str(key)]={'lamports':0,'data':'','owner':str(f.Pubkey.default()),'executable':False}
   elif not a.executable:self.accounts[str(key)]={'lamports':a.lamports,'data':a.data.hex(),'owner':str(a.owner),'executable':False}
  return self.vm.send_transaction(tx)
def prepare(c):
 original=fixture.LiteSVM;recorded=[]
 class VM(RecordingVM):
  def with_transaction_history(self,n):self.vm=self.vm.with_transaction_history(n);return self
  def with_sigverify(self,n):self.vm=self.vm.with_sigverify(n);return self
  def with_log_bytes_limit(self,n):self.vm=self.vm.with_log_bytes_limit(n);return self
 def factory():
  vm=VM(original());recorded.append(vm);return vm
 fixture.LiteSVM=factory
 try:receipt=fixture.run(c)
 finally:fixture.LiteSVM=original
 vm=recorded[0]
 return {'case':c,'accounts':vm.accounts,'transaction_base64':base64.b64encode(bytes(vm.transaction)).decode(),'litesvm_error':receipt['error']}
def run(binary,cases,surfpool,output):
 def rpc(method,params=None):
  req=urllib.request.Request(f'http://127.0.0.1:{PORT}',data=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params or []}).encode(),headers={'Content-Type':'application/json'})
  with urllib.request.urlopen(req,timeout=60) as response:result=json.load(response)
  if 'error' in result:raise RuntimeError((method,result['error']))
  return result['result']
 def get(key):
  a=rpc('getAccountInfo',[key,{'encoding':'base64'}])['value']
  return None if a is None else {'lamports':a['lamports'],'owner':a['owner'],'data':base64.b64decode(a['data'][0]).hex()}
 with (output/(binary.stem+'.log')).open('w') as log:
  proc=subprocess.Popen([str(surfpool),'start','--offline','--no-deploy','--no-tui','--no-studio','--host','127.0.0.1','--port',str(PORT),'--ws-port',str(PORT+1),'--airdrop-amount','0','--db',':memory:'],cwd=output,stdout=log,stderr=subprocess.STDOUT)
  try:
   for _ in range(100):
    if proc.poll() is not None:raise RuntimeError('Surfpool terminated')
    try:
     if rpc('getHealth')=='ok':break
    except OSError:pass
    time.sleep(.1)
   else:raise TimeoutError('Surfpool startup')
   programs=[(f.PROGRAM,ROOT/'evidence/original/pump_fees/deployed.so'),(f.PUMP,binary),(f.AMM,ROOT/'evidence/original/pump_amm/deployed.so')]+[(key,ROOT/f'evidence/dependencies/{name}/deployed.so') for name,key in [('spl_token',f.TOKEN),('spl_token_2022',f.TOKEN22),('associated_token',f.ATA)]]
   for key,path in programs:
    blob=path.read_bytes();extent=struct.unpack_from('<Q',blob,40)[0]+struct.unpack_from('<H',blob,58)[0]*struct.unpack_from('<H',blob,60)[0];assert not any(blob[extent:])
    rpc('surfnet_setAccount',[str(key),{'lamports':10**10,'data':blob[:extent].hex(),'owner':'BPFLoader2111111111111111111111111111111111','executable':True}])
   rows=[];previous=set()
   for row in cases:
    for key in previous-set(row['accounts']):rpc('surfnet_setAccount',[key,{'lamports':0,'data':'','owner':str(f.Pubkey.default()),'executable':False}])
    for key,account in row['accounts'].items():rpc('surfnet_setAccount',[key,account])
    previous=set(row['accounts']);before={key:get(key) for key in row['accounts']}
    old=Transaction.from_bytes(base64.b64decode(row['transaction_base64']));msg=old.message;h=msg.header;keys=msg.account_keys
    def writable(i):return i<h.num_required_signatures-h.num_readonly_signed_accounts if i<h.num_required_signatures else i<len(keys)-h.num_readonly_unsigned_accounts
    instructions=[Instruction(keys[ix.program_id_index],bytes(ix.data),[AccountMeta(keys[n],n<h.num_required_signatures,writable(n)) for n in ix.accounts]) for ix in msg.instructions]
    # Distinct compute budgets avoid transaction deduplication for repeated payloads.
    # The recorded fixture leads with a compute-budget instruction; replacing a
    # different first instruction would silently drop a real program call.
    if not instructions or instructions[0].program_id!=COMPUTE:
     raise ValueError(('first recorded instruction is not compute-budget',row['name']))
    instructions[0]=f.set_compute_unit_limit(1400000-len(rows))
    signers=[k for k in [f.PAYER,f.AUTH] if k.pubkey() in keys[:h.num_required_signatures]]
    tx=Transaction.new_signed_with_payer(instructions,f.PAYER.pubkey(),signers,Hash.from_string(rpc('getLatestBlockhash')['value']['blockhash']));assert (tx.signatures and all(tx.verify_with_results()));encoded=base64.b64encode(bytes(tx)).decode()
    sim=rpc('simulateTransaction',[encoded,{'encoding':'base64','sigVerify':True,'innerInstructions':True}])['value'];sig=rpc('sendTransaction',[encoded,{'encoding':'base64','skipPreflight':True}])
    for _ in range(100):
     status=rpc('getSignatureStatuses',[[sig]])['value'][0]
     if status is not None:break
     time.sleep(.05)
    else:raise TimeoutError('Confirmation')
    assert status['err']==sim['err'];after={key:get(key) for key in row['accounts']}
    if status['err']:assert all(before[k]==after[k] for k in before if k!=str(f.PAYER.pubkey())),'Failed transaction changed nonpayer state'
    rows.append({'case':row['case'],'signature':sig,'transaction_base64':encoded,'error':status['err'],'before':before,'after':after,'logs':sim.get('logs',[]),'return_data':sim.get('returnData'),'inner_instructions':sim.get('innerInstructions')})
   return rows
  finally:
   proc.terminate()
   try:proc.wait(timeout=5)
   except subprocess.TimeoutExpired:proc.kill();proc.wait()
def layouts():
 out={}
 for name in ['pump','pump_amm','pump_fees']:
  idl=json.loads((ROOT/f'evidence/upstream/{name}.json').read_text(encoding='utf-8'));types={t['name']:t for t in idl['types']}
  for e in idl['events']:
   offset=8
   for field in types[e['name']]['type']['fields']:
    if field['name']=='timestamp':out[bytes(e['discriminator'])]=offset;break
    t=field['type']
    if not isinstance(t,str) or t not in ['pubkey','u64','i64','bool','u8','u16','u32']:break
    offset+={'pubkey':32,'u64':8,'i64':8,'bool':1,'u8':1,'u16':2,'u32':4}[t]
 return out
def normalize_event(data,offsets):
 data=bytearray(data);key=bytes(data[:8])
 if key not in offsets:raise ValueError(('unknown event',key.hex()))
 off=offsets[key]
 if len(data)<off+8:raise ValueError(('truncated event',key.hex(),len(data)))
 data[off:off+8]=bytes(8)
 return bytes(data)
def decode58(s):
 alphabet='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';n=0
 for c in s:n=n*58+alphabet.index(c)
 return bytes(len(s)-len(s.lstrip('1')))+n.to_bytes((n.bit_length()+7)//8,'big')
def normalized(row,offsets):
 events=[normalize_event(base64.b64decode(l.split(': ',1)[1]),offsets).hex() for l in row['logs'] if l.startswith('Program data: ')]
 inner=[]
 assert row['inner_instructions'] is not None,'RPC omitted inner instructions'
 for group in row['inner_instructions']:
  instructions=[]
  for ix in group['instructions']:
   if 'parsed' in ix:
    instructions.append(ix);continue
   data=decode58(ix['data'])
   if data[:8].hex()=='e445a52e51cb9a1d':data=data[:8]+normalize_event(data[8:],offsets)
   instructions.append({**ix,'data':data.hex()})
  inner.append({**group,'instructions':instructions})
 return {'error':row['error'],'before':row['before'],'after':row['after'],'events':events,'inner':inner,'return_data':row['return_data']}

def main():
 import re
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--surfpool',type=Path,default=ROOT/'work/localnet/surfpool');a=p.parse_args();a.output=a.output.resolve();a.surfpool=a.surfpool.resolve()
 assert subprocess.check_output([str(a.surfpool),'--version'],text=True).strip()=='surfpool 1.6.1'
 for port in [PORT,PORT+1]:
  with socket.socket() as so:so.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);so.bind(('127.0.0.1',port))
 a.output.mkdir(parents=True,exist_ok=False);original=a.output/'original.so';candidate=a.output/'candidate.so';original.write_bytes((ROOT/'evidence/original/pump/deployed.so').read_bytes());candidate.write_bytes(a.candidate.read_bytes())
 cases=[{}, {'source':True}, {'stable':True}, {'stable':True,'token22':True}]
 for mode in [{},{'source':True},{'stable':True},{'stable':True,'token22':True}]:
  cases += [{**mode,**c} for c in [{'amounts':[]},{'amounts':[0]},{'amounts':[1000,2000]},{'remaining_count':0},{'existing_dest':True},{'amounts':[10**9+1]},{'readonly_dest':True}]]
 cases += [{'holder_lamports':891879},{'holder_lamports':891880},{'holder_lamports':1000},{'stable':True,'alternate_dest':True},{'stable':True,'source':False},{'stable':True,'alternate_source':True},{'stable':True,'existing_dest':True,'mutations':{'dest':{'patches':[(108,'02')]}}},{'mutations':{'global':{'patches':[(1054,bytes(fixture.OTHER.pubkey()).hex())]}}}]
 paths=[Path(__file__),Path(fixture.__file__),Path(suite.__file__)]+[ROOT/f'evidence/upstream/{n}.json' for n in ['pump','pump_fees','pump_amm']]+[ROOT/f'evidence/original/{n}/deployed.so' for n in ['pump','pump_fees','pump_amm']]+[ROOT/f'evidence/dependencies/{n}/deployed.so' for n in ['spl_token','spl_token_2022','associated_token']]
 provenance={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in paths};fixtures=[prepare(c) for c in cases];(a.output/'fixtures.json').write_text(json.dumps(fixtures,indent=2),encoding='utf-8',newline='\n');x=run(original,fixtures,a.surfpool,a.output);y=run(candidate,fixtures,a.surfpool,a.output);require_aligned_runs(fixtures,x,y);bad=[];unexpected=[];offsets=layouts()
 def error(v):
  if v is None:return None
  m=re.fullmatch(r'TransactionErrorInstructionError\(\((\d+), Tagged\(InstructionErrorCustom\((\d+)\)\)\)\)',v)
  if m:return {'InstructionError':[int(m[1]),{'Custom':int(m[2])}]}
  m=re.fullmatch(r'TransactionErrorInstructionError\(\((\d+), Fieldless\((\w+)\)\)\)',v)
  assert m,v
  return {'InstructionError':[int(m[1]),m[2]]}
 for i,(f0,l,r) in enumerate(zip(fixtures,x,y)):
  if l['error']!=error(f0['litesvm_error']):unexpected.append(i)
  if normalized(l,offsets)!=normalized(r,offsets):bad.append(i)
 assert all(sha((ROOT/p).read_bytes())==h for p,h in provenance.items());assert sha(candidate.read_bytes())==sha(a.candidate.read_bytes())
 report={'scope':'Holder distributions using normally signed test-owned configured authority and synthetic native/classic/Token22 vaults, captured genuine Token/Token22/ATA CPIs. Exact errors/state/returns/inner/events except recognized event timestamps. Raw bytes retained. No whole-program identity claim.','original_sha256':sha(original.read_bytes()),'candidate_sha256':sha(candidate.read_bytes()),'runner_sha256':sha(Path(__file__).read_bytes()),'provenance':provenance,'cases':len(cases),'signed_transactions':len(x)+len(y),'mismatches':bad,'unexpected_original_errors':unexpected,'original':x,'candidate':y};(a.output/'pump-holder-distribution-transactions.json').write_text(json.dumps(report,indent=2),encoding='utf-8',newline='\n');(a.output/'raw-transactions.json').write_text(json.dumps({n:[r['transaction_base64'] for r in rows] for n,rows in [('original',x),('candidate',y)]}),encoding='utf-8',newline='\n');print(json.dumps({k:report[k] for k in ['cases','signed_transactions','mismatches','unexpected_original_errors']}));assert not bad and not unexpected
if __name__=='__main__':main()
