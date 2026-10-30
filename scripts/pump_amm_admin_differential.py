#!/usr/bin/env python3
"""Local original/rebuilt PumpSwap administration differential tests; no RPC."""
import argparse, base64, hashlib, itertools, json, pathlib
from solders.account import Account
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from pump_differential_output import PumpReport

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROGRAM = Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
EVENT = Pubkey.find_program_address([b'__event_authority'], PROGRAM)[0]
PAYER = Keypair.from_seed(bytes([201])*32)
OUTSIDER = Keypair.from_seed(bytes([202])*32)
IDL = json.loads((ROOT/'evidence/upstream/pump_amm.json').read_text())
CONFIG = next(x for x in json.loads((ROOT/'research/imported-lab/analysis/pump_fun/config-snapshot.json').read_text())['accounts'] if x['program_name']=='pump_amm')
CONFIG_KEY = Pubkey.from_string(CONFIG['address'])
RAW = bytearray(base64.b64decode(CONFIG['data_base64']))
RAW[8:40] = bytes(PAYER.pubkey())
DISABLE = bytes(next(x for x in IDL['instructions'] if x['name']=='disable')['discriminator'])

class Harness:
    def __init__(self, program):
        self.vm = LiteSVM().with_transaction_history(0)
        # Hash and load one byte snapshot, so the receipt names the executed image.
        image = pathlib.Path(program).read_bytes(); self.sha256 = hashlib.sha256(image).hexdigest()
        self.vm.add_program(PROGRAM, image)
        for who in [PAYER, OUTSIDER]: self.vm.airdrop(who.pubkey(), 10**12)
        self.vm.set_account(EVENT, Account(10**9,b'',Pubkey.default()))
    def query(self, arguments, prior_flags=0, mutation=None, instruction="disable", new_admin=None):
        data=bytearray(RAW); data[56]=prior_flags
        config_key=CONFIG_KEY; admin=PAYER; signer=True; writable=True; owner=PROGRAM; event=EVENT; program=PROGRAM
        if mutation=='outsider': admin=OUTSIDER
        if mutation=='unsigned': signer=False
        if mutation=='readonly': writable=False
        if mutation=='owner': owner=Pubkey.default()
        if mutation=='program': program=OUTSIDER.pubkey()
        if mutation=='discriminator': data[0]^=1
        if mutation=='truncated': data=data[:56]
        if mutation=='zero-boost-authority': data[907:939]=bytes(32)
        if mutation and mutation.startswith('set-'): _,offset,value=mutation.split('-'); data[int(offset)]=int(value)
        if mutation and mutation.startswith('length-'): data=(data+bytes(2000))[:int(mutation.split('-')[1])]
        if mutation and mutation.startswith('bad-bool-'): data[int(mutation.split('-')[2])]=2
        if mutation=='event': event=Pubkey.from_bytes(hashlib.sha256(b'pump-amm-differential-invalid-event').digest()); self.vm.set_account(event,Account(10**9,b'',Pubkey.default()))
        if mutation=='noncanonical_config': config_key=Pubkey.from_bytes(hashlib.sha256(b'pump-amm-differential-invalid-config').digest())
        self.vm.set_account(config_key,Account(CONFIG['lamports'],bytes(data),owner))
        accounts=[AccountMeta(admin.pubkey(),signer,False),AccountMeta(config_key,False,writable),AccountMeta(event,False,False),AccountMeta(program,False,False)]
        if instruction=='toggle_boost': accounts=accounts[:2]
        if instruction=='update_admin':
            key=Pubkey.from_bytes(new_admin)
            if key not in [PROGRAM,EVENT,CONFIG_KEY,Pubkey.default(),PAYER.pubkey(),OUTSIDER.pubkey()]: self.vm.set_account(key,Account(10**9,b'',Pubkey.default()))
            accounts.insert(2,AccountMeta(key,False,False))
        discriminator=bytes(next(x for x in IDL['instructions'] if x['name']==instruction)['discriminator']) if instruction else b''
        # Separate transaction payer allows testing a genuinely unsigned admin.
        payer=OUTSIDER if mutation=='unsigned' else admin
        tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,discriminator+arguments,accounts)],payer.pubkey(),[payer],self.vm.latest_blockhash())
        r=self.vm.send_transaction(tx)
        failed=isinstance(r,FailedTransactionMetadata)
        meta=r.meta() if failed else r
        after=bytes(self.vm.get_account(config_key).data)
        logs=meta.logs()
        return {'error':str(r.err()) if failed else None,'state_hex':after.hex(),
                'event_logs':[x for x in logs if x.startswith('Program data: ')],
                'rollback':after==bytes(data) if failed else None,
                'logs':logs}

def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--quick',action='store_true');a=p.parse_args()
    sources=[p for p in (ROOT/'programs/pump-amm').rglob('*.rs') if 'target' not in p.parts]
    output=PumpReport(a.output,ROOT,a.candidate,__file__,extra_inputs=[ROOT/'programs/pump-amm',*sources])
    original=ROOT/'evidence/original/pump_amm/deployed.so'
    left,right=Harness(original),Harness(a.candidate)
    cases=[];mismatches=[]
    def test(label,args,flags=0,mutation=None,instruction="disable",new_admin=None):
        x,y=left.query(args,flags,mutation,instruction,new_admin),right.query(args,flags,mutation,instruction,new_admin)
        same=all(x[k]==y[k] for k in ['error','state_hex','event_logs','rollback'])
        cases.append({'label':label,'args_hex':args.hex(),'prior_flags':flags,'mutation':mutation,'instruction':instruction,'new_admin_hex':new_admin.hex() if new_admin else None,'original':x,'candidate':y,'match':same})
        if not same:mismatches.append(label)
    priors=[0,31,224,255] if a.quick else range(256)
    for prior in priors:
        for bits in itertools.product([0,1],repeat=5):test(f'flags-{prior}-{bits}',bytes(bits),prior)
    for mutation in ['outsider','unsigned','readonly','owner','discriminator','truncated','event','noncanonical_config','program']:
        test(mutation,bytes([0,0,0,1,0]),255,mutation)
    for n in range(5):test(f'short-{n}',bytes(n))
    for n in range(5):
        data=bytearray(5);data[n]=2;test(f'invalid-bool-{n}',data)
    test('trailing-data',bytes(5)+b'ignored')
    for length in [0,7,8,56,417,642,899,907,939,940,941,948,949,950,1024]:test(f'length-{length}',bytes(5),mutation=f'length-{length}')
    for offset in [417,642,939,940]:test(f'bad-bool-{offset}',bytes(5),mutation=f'bad-bool-{offset}')
    for b in range(32):test(f'new-admin-{b}',b'',instruction='update_admin',new_admin=bytes([b])*32)
    for key in [PAYER.pubkey(),OUTSIDER.pubkey(),PROGRAM,CONFIG_KEY,EVENT]:test(f'new-admin-{key}',b'',instruction='update_admin',new_admin=bytes(key))
    for mutation in ['outsider','unsigned','readonly','owner','discriminator','truncated','event','noncanonical_config','program']:
        test(f'update-admin-{mutation}',b'',mutation=mutation,instruction='update_admin',new_admin=bytes([55])*32)
    test('update-admin-trailing',b'ignored',instruction='update_admin',new_admin=bytes([55])*32)
    for instruction,offset in [('toggle_mayhem_mode',417),('toggle_cashback_enabled',642),('toggle_boost',939)]:
        for old,new in itertools.product([0,1],repeat=2):test(f'{instruction}-{old}-{new}',bytes([new]),mutation=f'set-{offset}-{old}',instruction=instruction)
        for mutation in ['outsider','unsigned','readonly','owner','discriminator','truncated','noncanonical_config','zero-boost-authority']:
            test(f'{instruction}-{mutation}',b'\0',mutation=mutation,instruction=instruction)
        for payload in [b'',b'\2',b'\0extra']:test(f'{instruction}-payload-{payload.hex()}',payload,instruction=instruction)
    for length in range(8):test(f'short-dispatch-{length}',bytes(length),instruction=None)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    report={'scope':'Partial independently built disable/update_admin/toggle handlers vs captured original. Full state and log events compared; other instruction paths are not covered by this suite; no byte identity claimed.','original_sha256':left.sha256,'candidate_sha256':right.sha256,'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sources},'cases':cases,'case_count':len(cases),'mismatches':mismatches}
    output.write((json.dumps(report,separators=(',',':'))+'\n').encode('utf-8'))
    print(json.dumps({'cases':len(cases),'mismatches':mismatches[:30],'mismatch_count':len(mismatches)}))
    if mismatches:raise SystemExit(1)
if __name__=='__main__':main()
