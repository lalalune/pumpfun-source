#!/usr/bin/env python3
"""Read original crank behavior using test-owned payer and synthetic offline state."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse,struct
from fees_donation_create_differential import *
import sys
sys.path.insert(0,str(ROOT/'scripts'))
from pump_amm_reusable_harness import pin_program
from pump_differential_output import PumpReport
from solders.compute_budget import set_compute_unit_limit
from solders.clock import Clock
RELAY=Pubkey.from_string('RLAYHr9TRFcKB2ubYQhspcnXiaGpaVzNQvHytt47RZu')
TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
RELAY_EVENT=Pubkey.find_program_address([b'__event_authority'],RELAY)[0]
WHITELIST,WB=Pubkey.find_program_address([b'mint_whitelist_v1'],RELAY)
EPOCH=Pubkey.find_program_address([b'epoch_tracker_v1',bytes(CONFIG),bytes(QUOTE)],RELAY)[0]
DEBOUNCER=Pubkey.find_program_address([b'debouncer_v1',bytes(CONFIG),bytes(QUOTE)],RELAY)[0]
D_ATA=Pubkey.find_program_address([bytes(DONATION),bytes(TOKEN),bytes(QUOTE)],ATA)[0]
B_ATA=Pubkey.find_program_address([bytes(DEBOUNCER),bytes(TOKEN),bytes(QUOTE)],ATA)[0]
IX=next(x for x in IDL['instructions'] if x['name']=='crank_donation_fee_pda')
class CrankFixture:
 def __init__(self,binary):
  self.vm=LiteSVM().with_transaction_history(0);self.vm.add_program_from_file(PROGRAM,binary)
  for name,key in [('donation_relay',RELAY),('spl_token',TOKEN),('associated_token',ATA)]:self.vm.add_program_from_file(key,ROOT/f'evidence/dependencies/{name}/deployed.so')
 def run(self,c):
  quote=Pubkey.from_string(c.get('quote',str(QUOTE)))
  epoch=Pubkey.find_program_address([b'epoch_tracker_v1',bytes(CONFIG),bytes(quote)],RELAY)[0]
  debouncer=Pubkey.find_program_address([b'debouncer_v1',bytes(CONFIG),bytes(quote)],RELAY)[0]
  d_ata=Pubkey.find_program_address([bytes(DONATION),bytes(TOKEN),bytes(quote)],ATA)[0]
  b_ata=Pubkey.find_program_address([bytes(debouncer),bytes(TOKEN),bytes(quote)],ATA)[0]
  self.vm.set_clock(Clock(1000,0,0,0,1700000000))
  for kp in [PAYER,AUTH,OTHER]:self.vm.set_account(kp.pubkey(),Account(c.get('payer_lamports',10**12) if kp==AUTH else 10**12,b'',Pubkey.default()))
  for k in [EVENT,RELAY_EVENT,epoch,debouncer,d_ata,b_ata,WHITELIST]:self.vm.set_account(k,Account(0,b'',Pubkey.default()))
  gd=bytearray(BASE);gd[41]=c.get('flags',0)
  for offset,value in c.get('global_patches',[]):gd[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
  self.vm.set_account(GLOBAL,Account(10**9,bytes(gd),PROGRAM))
  state=hashlib.sha256(b'account:DonationFeePda').digest()[:8]+bytes([DONATION_BUMP,c.get('version',1)])+bytes(CONFIG)+bytes(MINT)+bytes(quote)+bytes(AUTH.pubkey())+c.get('total',0).to_bytes(8,'little')+c.get('last',0).to_bytes(8,'little',signed=True)+bytes(64)
  state=bytearray(state)
  for offset,value in c.get('state_patches',[]):state[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
  length=c.get('state_length',len(state));state=(state+bytearray(max(0,length-len(state))))[:length]
  self.vm.set_account(DONATION,Account(self.vm.minimum_balance_for_rent_exemption(218)+c.get('amount',1000000),bytes(state),Pubkey.from_string(c.get('state_owner',str(PROGRAM)))))
  fixture=json.loads((ROOT/'research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json').read_text())
  mint=fixture['accounts']['quote_mint'];self.vm.set_account(quote,Account(mint['lamports'],base64.b64decode(mint['data_base64']),TOKEN))
  if quote!=QUOTE:
   md=bytearray(82);md[44]=6;md[45]=1;self.vm.set_account(quote,Account(10**9,bytes(md),TOKEN))
  if 'token_amount' in c:
   reserve=self.vm.minimum_balance_for_rent_exemption(165);td=bytearray(165);td[:32]=bytes(quote);td[32:64]=bytes(DONATION);td[64:72]=c['token_amount'].to_bytes(8,'little');td[108]=1;td[109:113]=(1).to_bytes(4,'little');td[113:121]=reserve.to_bytes(8,'little')
   if quote!=QUOTE:td[109:121]=bytes(12)
   for offset,value in c.get('token_patches',[]):td[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
   self.vm.set_account(d_ata,Account(reserve+(c['token_amount'] if quote==QUOTE else 0)+c.get('unsynced',0),bytes(td),Pubkey.from_string(c.get('token_owner',str(TOKEN)))))
  if c.get('whitelist',True):
   wd=hashlib.sha256(b'account:MintWhitelistV1').digest()[:8]+bytes([WB])+bytes(4)
   if c.get('listed'):wd=wd[:-4]+(1).to_bytes(4,'little')+bytes(quote)
   self.vm.set_account(WHITELIST,Account(10**9,wd,RELAY))
  addresses={'transaction_payer':PAYER.pubkey(),'global':GLOBAL,'whitelist':WHITELIST,'donation':DONATION,'donation_ata':d_ata,'debouncer':debouncer,'debouncer_ata':b_ata,'epoch':epoch,'payer':AUTH.pubkey(),'quote':quote}
  def snapshot():
   out={}
   for n,k in addresses.items():
    a=self.vm.get_account(k);out[n]=None if not a else {'lamports':a.lamports,'owner':str(a.owner),'data':a.data.hex()}
   return out
  names={'event_authority':EVENT,'program':PROGRAM,'payer':AUTH.pubkey(),'system_program':Pubkey.default(),'token_program':TOKEN,'associated_token_program':ATA,'rent':Pubkey.from_string('SysvarRent111111111111111111111111111111111'),'fee_program_global':GLOBAL,'donation_fee_pda':DONATION,'quote_mint':quote,'donation_fee_pda_ata':d_ata,'donation_relay_program':RELAY,'donation_relay_event_authority':RELAY_EVENT,'mint_whitelist':WHITELIST,'epoch_tracker':epoch,'debouncer':debouncer,'debouncer_ata':b_ata}
  if c.get('wrong_account'):names[c['wrong_account']]=OTHER.pubkey()
  metas=[AccountMeta(names[a['name']],a.get('signer',False) and not c.get('unsigned'),a.get('writable',False) and a['name']!=c.get('readonly')) for a in IX['accounts']]
  metas=metas[:c.get('account_count',len(metas))]
  tx=Transaction.new_signed_with_payer([set_compute_unit_limit(1400000),Instruction(PROGRAM,bytes(IX['discriminator']),metas)],PAYER.pubkey(),[PAYER]+([AUTH] if any(m.is_signer and m.pubkey==AUTH.pubkey() for m in metas) else []),self.vm.latest_blockhash());assert all(tx.verify_with_results())
  before=snapshot();r=self.vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r
  return {'case':c,'error':str(r.err()) if failed else None,'before':before,'after':snapshot(),'logs':meta.logs(),'inner':json.loads(meta.to_json())['inner_instructions'],'transaction_base64':base64.b64encode(bytes(tx)).decode()}
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--candidate',type=pathlib.Path);a=p.parse_args();publisher=PumpReport(a.output,ROOT,a.candidate,__file__,extra_inputs=[ROOT/'evidence/dependencies/donation_relay/deployed.so',ROOT/'research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json']);f=CrankFixture(pin_program(ROOT/'evidence/original/pump_fees/deployed.so'))
 cases=[{'name':'base'},{'name':'zero','amount':0},{'name':'one','amount':1},{'name':'large','amount':10**9},{'name':'no-whitelist','whitelist':False}]
 cases += [{'name':'flags-'+str(n),'flags':n} for n in range(256)]
 cases += [{'name':'wrong-'+a['name'],'wrong_account':a['name']} for a in IX['accounts'] if a['name']!='payer']
 cases += [{'name':'version-'+str(n),'version':n} for n in [0,2,255]]
 cases += [{'name':'recent','last':1700000000},{'name':'recent-1','last':1699999999},{'name':'total-overflow','total':2**64-1}]
 cases += [{'name':'token-existing-'+str(n),'token_amount':n,'amount':0} for n in [0,1,1000000]]
 cases += [{'name':'token-and-native','token_amount':11,'amount':100}]
 cases += [{'name':'unsigned','unsigned':True}]
 cases += [{'name':'readonly-'+x['name'],'readonly':x['name']} for x in IX['accounts'] if x.get('writable')]
 cases += [{'name':'account-count-'+str(n),'account_count':n} for n in range(len(IX['accounts']))]
 cases += [{'name':'state-length-'+str(n),'state_length':n} for n in [0,7,8,9,10,42,74,106,138,146,154,217]]
 for offset,label in [(0,'disc'),(8,'bump'),(10,'config'),(42,'base'),(74,'quote'),(106,'creator')]:cases.append({'name':'state-'+label,'state_patches':[(offset,'00')]})
 cases += [{'name':'global-'+str(n),'global_patches':[(n,'00')]} for n in [0,8]]
 for amount in [0,1,1000000]:
  for listed in [False,True]:cases.append({'name':'non-native-'+str(amount)+'-'+str(listed),'quote':str(MINT),'token_amount':amount,'listed':listed})
 cases += [{'name':'larger-allocation-'+str(n),'state_length':n} for n in [219,300,500]]
 cases += [{'name':'below-rent-'+str(n),'amount':n} for n in [-1,-1000000]]
 cases += [{'name':'poor-payer-'+str(n),'payer_lamports':n} for n in [0,1,2039280,2039281,4000000,8000000]]
 for offset,label,value in [(0,'mint',bytes(32)),(32,'authority',bytes(32)),(108,'uninitialized',bytes([0])),(108,'frozen',bytes([2]))]:cases.append({'name':'ata-'+label,'token_amount':1,'token_patches':[(offset,value.hex())]})
 cases += [{'name':'ata-owner','token_amount':1,'token_owner':str(PROGRAM)},{'name':'ata-unsynced','token_amount':0,'amount':0,'unsynced':12345},{'name':'quote-and-disable','flags':8,'state_patches':[(74,'00')]},{'name':'zero-no-whitelist','amount':0,'whitelist':False}]
 rows=[];failures=[];candidate=CrankFixture(pin_program(a.candidate)) if a.candidate else None
 for c in cases:
  x=f.run(c);y=candidate.run(c) if candidate else None
  keys=['error','before','after','inner']
  match=all(x[k]==y[k] for k in keys) and [l for l in x['logs'] if l.startswith('Program data:')]==[l for l in y['logs'] if l.startswith('Program data:')] if y else None
  rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:failures.append(c['name'])
 report={'scope':'Signed synthetic offline crank fixtures; no full-program byte identity claim.','original_sha256':hashlib.sha256(pin_program(ROOT/'evidence/original/pump_fees/deployed.so').read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(pin_program(a.candidate).read_bytes()).hexdigest() if a.candidate else None,'cases':rows,'mismatches':failures}
 publisher.write((json.dumps(report,indent=2)+'\n').encode('utf-8'))
 print('Cases',len(rows),'mismatches',failures)
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
