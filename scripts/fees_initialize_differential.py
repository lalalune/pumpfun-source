#!/usr/bin/env python3
"""Compare FeeProgramGlobal initialization, including System CPI and rollback."""
import base64
from fees_admin_differential import *
from pump_differential_output import PumpReport
PUMP=Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
PUMP_GLOBAL=Pubkey.find_program_address([b'global'],PUMP)[0]
CAPTURE=next(x for x in json.loads((ROOT/'research/imported-lab/analysis/pump_fun/config-snapshot.json').read_text())['accounts'] if x['program_name']=='pump')
PUMP_DATA=bytearray(base64.b64decode(CAPTURE['data_base64']));PUMP_DATA[9:41]=bytes(AUTH.pubkey())
class InitFixture(Fixture):
 def run(self,c):
  mutation=c.get('mutation','none');pump_data=bytearray(PUMP_DATA);pump_owner=PUMP;pump_key=PUMP_GLOBAL;key=GLOBAL;event=EVENT;system=Pubkey.default();program=PROGRAM;authority=AUTH
  if mutation=='authority':authority=OTHER
  if mutation=='pump_owner':pump_owner=PROGRAM
  if mutation=='pump_key':pump_key=OTHER.pubkey()
  if mutation=='pump_discriminator':pump_data[0]^=1
  if mutation=='pump_bool':pump_data[8]=2
  if mutation.startswith('pump_length:'):pump_data=pump_data[:int(mutation.split(':')[1])]
  if mutation=='key':key=Pubkey.from_bytes(bytes([46])*32)
  if mutation=='event':event=Pubkey.from_bytes(bytes([47])*32)
  if mutation=='system':system=OTHER.pubkey()
  if mutation=='program':program=Pubkey.default()
  self.vm.set_account(pump_key,Account(10**9,bytes(pump_data),pump_owner))
  initial=Account(c.get('prefund',0),b'',Pubkey.default())
  if mutation=='existing':initial=Account(10**9,BASE,PROGRAM)
  if mutation=='wrong_owner':initial=Account(10**9,bytes(338),PUMP)
  self.vm.set_account(key,initial)
  accounts=[AccountMeta(authority.pubkey(),mutation!='unsigned',mutation!='authority_readonly'),AccountMeta(pump_key,False,False),AccountMeta(key,False,mutation!='readonly'),AccountMeta(system,False,False),AccountMeta(event,False,False),AccountMeta(program,False,False)]
  if mutation.startswith('accounts:'):accounts=accounts[:int(mutation.split(':')[1])]
  disc=bytes(next(x['discriminator'] for x in IDL['instructions'] if x['name']=='initialize_fee_program_global'))
  payload=disc+bytes.fromhex(c['arg'])
  before=[self.vm.get_account(k).lamports for k in [AUTH.pubkey(),OTHER.pubkey(),PAYER.pubkey()]]
  signers=[PAYER,authority] if mutation!='unsigned' and accounts else [PAYER]
  tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,payload,accounts)],PAYER.pubkey(),signers,self.vm.latest_blockhash())
  result=self.vm.send_transaction(tx);failed=isinstance(result,FailedTransactionMetadata);meta=result.meta() if failed else result;after=self.vm.get_account(key)
  balances=[self.vm.get_account(k).lamports for k in [AUTH.pubkey(),OTHER.pubkey(),PAYER.pubkey()]]
  return {'error':str(result.err()) if failed else None,'data_hex':after.data.hex() if after else None,'lamports':after.lamports if after else None,'owner':str(after.owner) if after else None,'balance_deltas':[a-b for a,b in zip(balances,before)],'pump_data':self.vm.get_account(pump_key).data.hex(),'events':[l for l in meta.logs() if l.startswith('Program data:')],'inner_instructions':json.loads(meta.to_json())['inner_instructions'],'logs':meta.logs()}
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();publisher=PumpReport(a.output,ROOT,a.candidate,__file__);o=InitFixture(ROOT/'evidence/original/pump_fees/deployed.so');b=InitFixture(a.candidate) if a.candidate else None
 valid=bytes([44])*32+bytes([17])+(123).to_bytes(8,'little');cases=[]
 for social in [bytes(32),bytes([44])*32,bytes(OTHER.pubkey())]:
  for flags in [0,1,255]:
   for limit in [0,123,2**64-1]:
    for prefund in [0,1,10**6,10**9]:cases.append({'name':f'init-{social.hex()}-{flags}-{limit}-{prefund}','arg':(social+bytes([flags])+limit.to_bytes(8,'little')).hex(),'prefund':prefund})
 for mutation in ['authority','pump_owner','pump_key','pump_discriminator','pump_bool','key','event','system','program','unsigned','authority_readonly','readonly','existing','wrong_owner']+['accounts:'+str(n) for n in range(6)]+['pump_length:'+str(n) for n in [0,7,8,9,41,739,740,741,1087,1088]]:cases.append({'name':mutation,'arg':valid.hex(),'mutation':mutation})
 for n in range(len(valid)):cases.append({'name':'arg-length-'+str(n),'arg':valid[:n].hex()})
 cases.append({'name':'extra-arguments','arg':(valid+b'ignored').hex()});rows=[];failures=[]
 for c in cases:
  x=o.run(c);y=b.run(c) if b else None;match=all(x[k]==y[k] for k in ['error','data_hex','lamports','owner','balance_deltas','pump_data','events','inner_instructions']) if b else None
  rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:failures.append(c['name'])
 report={'scope':'initialize_fee_program_global only. Local original/candidate SBF execution incl System CPI/state/errors/balances/events/inner instructions; not complete program identity.','original_sha256':o.program_sha256,'candidate_sha256':b.program_sha256 if b else None,'case_count':len(rows),'mismatches':failures,'cases':rows}
 publisher.write((json.dumps(report,separators=(',',':'))+'\n').encode('utf-8'));print(json.dumps({'case_count':len(rows),'mismatches':failures}))
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
