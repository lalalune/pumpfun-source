#!/usr/bin/env python3
"""Two ordinary Tokenkeg curves through actual captured AMM, normally signed.

Offline synthetic local state. No RPC, privileged signer substitution,
initializer instruction, historical-payload modification or extension fixtures.
Each side has a fresh VM and loads exactly one selected Pump executable.
"""
from pathlib import Path
import argparse,base64,gzip,hashlib,json,struct,sys
sys.dont_write_bytecode=True
from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta,Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction,VersionedTransaction
from solders.transaction_metadata import FailedTransactionMetadata
W=Path(__file__).resolve().parent
R=next(p for p in W.parents if(p/'evidence/original/pump/deployed.so').is_file())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
TEMPLATE=json.loads((W/'base-fixture.json').read_text())
PUMP=Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
AMM=Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22=Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
FEES=Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
WSOL=Pubkey.from_string('So11111111111111111111111111111111111111112')
# Public deterministic local test signer, matching the saved fixture user.
USER=Keypair.from_seed(bytes([201])*32)
KEYS=[Pubkey.from_string(k)for k in TEMPLATE['selected_outer_account_keys']]
assert USER.pubkey()==KEYS[0]
assert KEYS[3]==Pubkey.find_program_address([b'global_config'],AMM)[0]
A=KEYS[16];C_A=KEYS[18];B=Pubkey.from_bytes(bytes([84])*32)
C_B=Pubkey.find_program_address([b'bonding-curve',bytes(B)],PUMP)[0]
ata=lambda authority,mint:Pubkey.find_program_address([bytes(authority),bytes(TOKEN),bytes(mint)],ATA)[0]
VA=ata(C_A,A);VQA=ata(C_A,WSOL);VB=ata(C_B,B);VQB=ata(C_B,A)
UW=ata(USER.pubkey(),WSOL);UB=ata(USER.pubkey(),B)
assert VA==KEYS[19]and VQA==KEYS[20]
IDL=json.loads((R/'evidence/upstream/pump_amm.json').read_text())
IX=next(x for x in IDL['instructions']if x['name']=='multi_hop_swap')
PUMP_DISC=bytes([225,154,117,22,215,86,246,103])
PROGRAMS=[(AMM,'evidence/original/pump_amm/deployed.so'),(TOKEN,'evidence/dependencies/spl_token/deployed.so'),(TOKEN22,'evidence/dependencies/spl_token_2022/deployed.so'),(ATA,'evidence/dependencies/associated_token/deployed.so'),(FEES,'evidence/original/pump_fees/deployed.so')]

def token(mint,owner,amount):
 data=bytearray(165);data[:32]=bytes(mint);data[32:64]=bytes(owner);struct.pack_into('<Q',data,64,amount);data[108]=1
 return bytes(data)

def config(mode):
 original=bytes.fromhex(TEMPLATE['accounts'][str(KEYS[14])]['data_hex'])
 if mode=='captured':return original
 flat=(0,70,25);native=(0,60,30);exotic=(0,80,40)if mode=='exotic'else(0,0,0)
 data=original[:41]+struct.pack('<QQQ',*flat)+struct.pack('<I',1)+bytes(16)+struct.pack('<QQQ',*native)
 if mode!='legacy-flat':data+=struct.pack('<I',0)+struct.pack('<QQQ',*exotic)
 return data.ljust(2512 if mode=='legacy-flat'else 4097,b'\0')

def invoke(sell,amount,mode,limit=1,candidate=None):
 vm=LiteSVM().with_transaction_history(0)
 vm.set_clock(Clock(100,1234567890,0,0,1234567890))
 selected=[(pid,R/p)for pid,p in PROGRAMS]+[(PUMP,candidate or R/'evidence/original/pump/deployed.so')]
 for pid,path in selected:vm.add_program_from_file(pid,path)
 for key,row in TEMPLATE['accounts'].items():
  if row is not None:vm.set_account(Pubkey.from_string(key),Account(row['lamports'],bytes.fromhex(row['data_hex']),Pubkey.from_string(row['owner'])))
 # Every curve/vault/volume account exists before invocation. These are labeled
 # synthetic values; no initializer instruction or administration signer is used.
 vol=bytes(next(x for x in IDL['accounts']if x['name']=='UserVolumeAccumulator')['discriminator'])+bytes(USER.pubkey())+bytes(97)
 vm.set_account(KEYS[5],Account(10**9,vol,AMM))
 raw=bytearray(vm.get_account(C_A).data)
 assert len(raw)==166 and raw[48]==0 and raw[81:83]==b'\0\0'and raw[83:115]==bytes(32)and raw[124]==0
 for offset in [8,16,24,32,40,142]:struct.pack_into('<Q',raw,offset,10**15)
 raw[83:115]=bytes(A);raw[125:141]=bytes(16);raw[141]=1
 vm.set_account(C_B,Account(10**9,bytes(raw),PUMP))
 mint=vm.get_account(A);assert mint.owner==TOKEN and len(mint.data)==82
 vm.set_account(B,Account(mint.lamports,bytes(mint.data),TOKEN))
 vm.set_account(VB,Account(10**9,token(B,C_B,10**15),TOKEN))
 vm.set_account(VQB,Account(10**9,token(A,C_B,10**15),TOKEN))
 vm.set_account(UB,Account(10**9,token(B,USER.pubkey(),10**15),TOKEN))
 old=vm.get_account(KEYS[1]);vm.set_account(UW,Account(old.lamports,bytes(old.data),TOKEN))
 fee=vm.get_account(KEYS[14]);vm.set_account(KEYS[14],Account(fee.lamports,config(mode),fee.owner))
 fixed=KEYS[:16];fixed[1]=UB if sell else UW;fixed[2]=UW if sell else UB
 metas=[AccountMeta(k,bool(spec.get('signer')),bool(spec.get('writable')))for k,spec in zip(fixed,IX['accounts'])]
 group_a=[A,WSOL,C_A,VA,VQA];group_b=[B,A,C_B,VB,VQB]
 for group in [group_b,group_a]if sell else[group_a,group_b]:
  metas.extend(AccountMeta(key,False,i>=2)for i,key in enumerate(group))
 assert all(not m.is_signer for m in metas if m.pubkey==KEYS[3])
 def snapshot():
  rows={}
  for key in sorted({m.pubkey for m in metas},key=str):
   acc=vm.get_account(key)
   if not acc or not acc.executable:rows[str(key)]=None if not acc else{'lamports':acc.lamports,'owner':str(acc.owner),'data_hex':bytes(acc.data).hex()}
  return rows
 before=snapshot();data=bytes(IX['discriminator'])+struct.pack('<QQ',amount,limit)
 tx=Transaction.new_signed_with_payer([Instruction(AMM,data,metas)],USER.pubkey(),[USER],vm.latest_blockhash())
 assert all(tx.verify_with_results())and len(tx.signatures)==1
 result=vm.send_transaction(tx);failed=isinstance(result,FailedTransactionMetadata);meta=result.meta()if failed else result;encoded=json.loads(meta.to_json())
 inner=encoded['inner_instructions'];keys=tx.message.account_keys;pump_calls=[];token_calls=[]
 for group in inner:
  for entry in group:
   ix=entry['instruction'];payload=bytes(ix['data'][1:]);accounts=[str(keys[i])for i in ix['accounts'][1:]];pid=keys[ix['programIdIndex']]
   if pid==PUMP and payload.startswith(PUMP_DISC):
    flags=list(payload[20:]);assert flags==([2,1]if sell else[1,2]);assert len(accounts)==23 and accounts[2]==str(KEYS[3])
    pump_calls.append({'amount':struct.unpack_from('<Q',payload,8)[0],'flags':flags,'accounts':accounts})
   if pid==TOKEN:token_calls.append({'data_hex':payload.hex(),'accounts':accounts})
 return {'error':str(result.err())if failed else None,'logs':meta.logs(),'events':[x for x in meta.logs()if x.startswith('Program data: ')],'inner':inner,'return_data':encoded.get('return_data'),'before':before,'after':snapshot(),'transaction_base64':base64.b64encode(bytes(tx)).decode(),'transaction_sha256':hashlib.sha256(bytes(tx)).hexdigest(),'verified_signature_count':len(tx.signatures),'fresh_vm':True,'pump_calls':pump_calls,'token_calls':token_calls,'program_sha256':{str(pid):sha(path)for pid,path in selected}}

def fixtures():
 for sell in [False,True]:
  for mode in ['captured','exotic','flat-fallback','legacy-flat']:
   for amount in [10**6,10**9]:yield f'{"sell"if sell else"buy"}-{mode}-{amount}',sell,amount,mode,1
  yield f'{"sell"if sell else"buy"}-final-slippage',sell,10**9,'exotic',2**64-1
  yield f'{"sell"if sell else"buy"}-zero-input',sell,0,'exotic',1

def compiled_binding(candidate,build_report):
 assert build_report is not None,'Candidate execution requires its actual clean-build report'
 report=json.loads(build_report.read_text());attempt_path=build_report.with_name('build-attempt.json');attempt=json.loads(attempt_path.read_text())
 assert attempt['returncode']==0 and attempt['source_unchanged']
 assert attempt['source_sha256']==attempt['source_after_sha256']==report['source_sha256']
 assert len(report['source_sha256'])==36
 assert report['comparison']['candidate_sha256']==sha(candidate)
 for path,digest in report['source_sha256'].items():assert sha(R/path)==digest,path
 return {'report':str(build_report.relative_to(R)),'report_sha256':sha(build_report),'attempt_sha256':sha(attempt_path),'candidate_sha256':sha(candidate),'actual_source_sha256':report['source_sha256']}

def bindings(candidate=None,build_report=None):
 paths={str(Path(__file__).relative_to(R)),str((W/'base-fixture.json').relative_to(R)),'evidence/upstream/pump_amm.json','evidence/original/pump/deployed.so'}|{p for _,p in PROGRAMS}
 runtime={}
 for name,module in sorted(sys.modules.items()):
  p=getattr(module,'__file__',None)
  if name.startswith('solders')and p and Path(p).is_file():runtime[str(Path(p).resolve())]=sha(p)
 runtime[str(Path(sys.executable).resolve())]=sha(Path(sys.executable).resolve())
 return {'repository_inputs':{p:sha(R/p)for p in sorted(paths)},'runtime_files':runtime,'python_version':sys.version,'compiled_candidate_binding':compiled_binding(candidate,build_report)if candidate else None}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path);p.add_argument('--build-report',type=Path);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 assert not args.output.exists(),'Retain prior attempts; output path must be fresh'
 args.candidate=args.candidate.resolve()if args.candidate else None
 if args.candidate and args.build_report is None:
  choices=[args.candidate.parent/'build-comparison.json',args.candidate.parent.parent/'build-comparison.json']
  args.build_report=next((p for p in choices if p.is_file()),None)
 args.build_report=args.build_report.resolve()if args.build_report else None
 before=bindings(args.candidate,args.build_report);rows=[]
 for name,sell,amount,mode,limit in fixtures():
  original=invoke(sell,amount,mode,limit)
  candidate=invoke(sell,amount,mode,limit,args.candidate.resolve())if args.candidate else None
  fields=['error','events','inner','return_data','before','after','pump_calls','token_calls']
  mismatches=[k for k in fields if original[k]!=candidate[k]]if candidate else None
  rows.append({'case':name,'parameters':{'sell':sell,'amount':amount,'fee_mode':mode,'limit':limit},'original':original,'candidate':candidate,'mismatches':mismatches})
  print(json.dumps({'case':name,'original_error':original['error'],'pump_calls':len(original['pump_calls']),'mismatches':mismatches}),flush=True)
 after=bindings(args.candidate,args.build_report);assert before==after
 out={'scope':__doc__,'mode':'original-versus-candidate'if args.candidate else'original-only fixture acceptance; no candidate claim','provenance':before,'inputs_unchanged':True,'case_count':len(rows),'original_successes':sum(r['original']['error']is None for r in rows),'original_pump_cpi_cases':sum(bool(r['original']['pump_calls'])for r in rows),'verified_outer_signatures':sum(r['original']['verified_signature_count']+(r['candidate']['verified_signature_count']if r['candidate']else 0)for r in rows),'candidate_sha256':sha(args.candidate)if args.candidate else None,'cases':rows}
 payload=(json.dumps(out,separators=(',',':'))+'\n').encode();args.output.write_bytes(gzip.compress(payload,mtime=0)if args.output.suffix=='.gz'else payload)
 print(json.dumps({k:v for k,v in out.items()if k not in['scope','cases','provenance']},indent=2))
 if args.candidate:raise SystemExit(any(r['mismatches']for r in rows))
