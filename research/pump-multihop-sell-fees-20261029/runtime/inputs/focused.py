"""Local signed multi-hop parser-order comparisons through the captured AMM."""
from pathlib import Path
import argparse,base64,gzip,hashlib,importlib.util,json,struct,sys,re
ROOT=Path('/mnt/c/Users/ahi20/Documents/ChatGPT/pumpfun-source')
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'scripts'))
import pump_captured_loader as loader
loader.install()
H=Path(__file__).resolve().parent/'pump_tokenkeg_two_curve_differential.py'
spec=importlib.util.spec_from_file_location('two_curve_fixture',H);f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
Base=f.LiteSVM
CASE={};SENDS=[]
def signatures_verified(tx):
 """True only for every signature required by the message header."""
 required = tx.message.header.num_required_signatures
 if required <= 0 or len(tx.signatures) != required:return False
 results = tx.verify_with_results()
 return bool(results) and len(results) == required and all(results)
NATIVE_ALIAS=f.Pubkey.from_bytes(bytes([146])*32)
OLD_VA,OLD_VQA,OLD_VQB=f.VA,f.VQA,f.VQB
class ObservedVM(Base):
 def add_program_from_file(self,pid,path):
  before=hashlib.sha256(Path(path).read_bytes()).hexdigest()
  answer=super().add_program_from_file(pid,path)
  assert before==hashlib.sha256(Path(path).read_bytes()).hexdigest()
  if not hasattr(self,'observed_loads'):self.observed_loads=[]
  self.observed_loads.append(dict(program=str(pid),sha256=before))
  return answer
 def set_account(self,key,account):
  answer=super().set_account(key,account)
  if key==f.KEYS[19] and CASE.get('token2022_flow'):super().set_account(f.VA,f.Account(account.lamports,account.data[:165]+b'\x02'+struct.pack('<HHQ',2,8,0),f.TOKEN22))
  if key==f.KEYS[20] and CASE.get('native_wrong_address'):super().set_account(NATIVE_ALIAS,account)
  if key==f.VQB and CASE.get('extension'):
   if CASE.get('token2022_flow'):super().set_account(key,f.Account(account.lamports,account.data[:165]+b'\x02'+struct.pack('<HHQ',2,8,0),f.TOKEN22))
   mint=self.get_account(f.A)
   payload=bytes(72)+struct.pack('<QQH',0,100,CASE.get('bps',0))*2
   extension=CASE['extension']
   tlv=struct.pack('<HH',1,108)+(payload if extension=='valid'else b'') if extension!='none'else b''
   if extension=='short_header':tlv=b'\x01'
   data=mint.data[:82]+bytes(83)+b'\x01'+tlv
   super().set_account(f.A,f.Account(mint.lamports,data,f.TOKEN22))
  return answer
 def send_transaction(self,tx):
  before=[]
  for key in tx.message.account_keys:
   a=self.get_account(key)
   before.append(dict(key=str(key),owner=str(a.owner),lamports=a.lamports,data_sha256=hashlib.sha256(a.data).hexdigest(),executable=a.executable)if a else dict(key=str(key),missing=True))
  result=super().send_transaction(tx);failed=isinstance(result,f.FailedTransactionMetadata);meta=result.meta()if failed else result
  SENDS.append(dict(transaction_base64=base64.b64encode(bytes(tx)).decode(),signatures_verified=signatures_verified(tx),before=before,metadata=json.loads(meta.to_json()),loads=list(loader.LOADS),program_loads=self.observed_loads))
  return result
f.LiteSVM=ObservedVM

def main():
 p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--proposal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 images={'original':ROOT/'evidence/original/pump/deployed.so','parent':a.parent.resolve(),'proposal':a.proposal.resolve()}
 cases=[dict(name='tokenkeg_sell_control',sell=True),dict(name='tokenkeg_buy_control',sell=False),dict(name='truncated_fee_config',sell=True,extension='truncated'),dict(name='short_tlv_header',sell=True,extension='short_header'),dict(name='no_extension_wrong_address',sell=True,extension='none'),dict(name='valid_zero_fee_wrong_address',sell=True,extension='valid'),dict(name='valid_fee_wrong_address',sell=True,extension='valid',bps=25),dict(name='native_quote_address_control',sell=False,native_wrong_address=True),dict(name='valid_fee_quote_owner_control',sell=True,extension='valid',correct_quote_address=True),dict(name='truncated_fee_before_quote_owner',sell=True,extension='truncated',correct_quote_address=True),dict(name='token2022_zero_fee_sell',sell=True,extension='valid',correct_quote_address=True,token2022_flow=True),dict(name='token2022_capped_fee_sell',sell=True,extension='valid',bps=25,correct_quote_address=True,token2022_flow=True),dict(name='token2022_capped_fee_buy',sell=False,extension='valid',bps=25,correct_quote_address=True,token2022_flow=True)]
 rows=[];units=re.compile(r'^Program [1-9A-HJ-NP-Za-km-z]+ consumed [0-9]+ of [0-9]+ compute units$')
 for c in cases:
  CASE.clear();CASE.update(c);runs={};raw={}
  f.VA=f.Pubkey.find_program_address([bytes(f.C_A),bytes(f.TOKEN22),bytes(f.A)],f.ATA)[0] if c.get('token2022_flow')else OLD_VA
  f.VQA=NATIVE_ALIAS if c.get('native_wrong_address')else OLD_VQA
  f.VQB=f.Pubkey.find_program_address([bytes(f.C_B),bytes(f.TOKEN22),bytes(f.A)],f.ATA)[0] if c.get('correct_quote_address')else OLD_VQB
  for name,path in images.items():
   SENDS.clear();loader.LOADS.clear();runs[name]=f.invoke(c['sell'],10**6,'exotic',1,path);assert len(SENDS)==1;raw[name]=SENDS[0]
  fields=['error','events','inner','return_data','before','after','transaction_base64','pump_calls','token_calls']
  compare=lambda name:[k for k in fields if runs['original'][k]!=runs[name][k]]
  logs=lambda name:[l for l in runs[name]['logs']if not units.fullmatch(l)]
  row=dict(case=c,runs=runs,observations=raw,proposal_differences=compare('proposal'),parent_differences=compare('parent'),proposal_log_equal=logs('original')==logs('proposal'))
  rows.append(row);print(json.dumps(dict(case=c['name'],errors={k:v['error']for k,v in runs.items()},proposal_differences=row['proposal_differences'],parent_differences=row['parent_differences'],log_equal=row['proposal_log_equal'],original_diagnostics=[l for l in runs['original']['logs']if 'Error'in l or 'failed'in l])),flush=True)
 a.output.write_bytes(gzip.compress(json.dumps(dict(scope=__doc__,images_sha256={k:hashlib.sha256(v.read_bytes()).hexdigest()for k,v in images.items()},producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),fixture_sha256=hashlib.sha256(H.read_bytes()).hexdigest(),cases=rows),separators=(',',':')).encode(),mtime=0))
 assert all(not r['proposal_differences'] and r['proposal_log_equal'] for r in rows), 'Original/proposal observation mismatch; raw report retained'
if __name__=='__main__':main()
