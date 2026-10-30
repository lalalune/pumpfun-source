#!/usr/bin/env python3
"""Offline, normally signed prerequisite probe for Pump initialize only."""
import base64,json,hashlib
from pathlib import Path
from solders.account import Account
from solders.instruction import AccountMeta,Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from probe_report import write_json_report
R=Path(__file__).resolve().parents[1]
IDL=json.loads((R/'evidence/upstream/pump.json').read_text());P=Pubkey.from_string(IDL['address']);G=Pubkey.find_program_address([b'global'],P)[0]
IX=next(i for i in IDL['instructions'] if i['name']=='initialize')
def run(seed):
 vm=LiteSVM().with_sigverify(True);vm.add_program_from_file(P,R/'evidence/original/pump/deployed.so')
 user=Keypair.from_seed(bytes([seed])*32);vm.set_account(user.pubkey(),Account(10**12,b'',Pubkey.default()))
 tx=Transaction.new_signed_with_payer([Instruction(P,bytes(IX['discriminator']),[AccountMeta(G,False,True),AccountMeta(user.pubkey(),True,True),AccountMeta(Pubkey.default(),False,False)])],user.pubkey(),[user],vm.latest_blockhash());tx.verify()
 res=vm.send_transaction(tx);fail=isinstance(res,FailedTransactionMetadata);meta=res.meta() if fail else res;a=vm.get_account(G)
 return {'seed':seed,'error':str(res.err()) if fail else None,'logs':meta.logs(),'metadata':json.loads(meta.to_json()),'transaction_base64':base64.b64encode(bytes(tx)).decode(),'signatures_verified':True,'global':None if a is None else {'owner':str(a.owner),'lamports':a.lamports,'data_base64':base64.b64encode(a.data).decode()}}
if __name__=='__main__':
 d={'scope':'Offline ordinary test-owned initialize signers only. No Mayhem instruction execution.','original_sha256':hashlib.sha256((R/'evidence/original/pump/deployed.so').read_bytes()).hexdigest(),'cases':[run(x) for x in [201,202]]};write_json_report(R/'work/pump-global-init-recovery/prerequisite.json',d);print([(c['seed'],c['error']) for c in d['cases']])
