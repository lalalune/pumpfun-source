#!/usr/bin/env python3
"""Offline malformed-input smoke tests; not a functional or authorization audit."""
import hashlib,json,pathlib,random
ROOT=pathlib.Path(__file__).resolve().parents[1]
# .gitignore lists repro/, and this checkout has no repro/programs.json.
_CAPTURE_ORDER=('pump','pump_amm','pump_fees','mayhem')
def program_addresses(root=None):
    """Map each smoke-test program to the address of its captured binary.

    Use repro/programs.json when that archived selector is present. Otherwise
    read evidence/original/<name>/capture.json. Its program field is the
    account the deployed.so bytes were captured from. Where an IDL exists,
    its address is the same id; scripts/test_tooling.py checks that.
    """
    root=ROOT if root is None else pathlib.Path(root)
    archived=root/'repro/programs.json'
    if archived.is_file():
        selected=json.loads(archived.read_text())
        if not isinstance(selected,dict):
            raise ValueError('repro/programs.json must map program names to addresses')
        return selected
    selected={}
    for name in _CAPTURE_ORDER:
        binary=root/'evidence/original'/name/'deployed.so'
        if not binary.is_file():
            continue
        receipt_path=root/'evidence/original'/name/'capture.json'
        program=json.loads(receipt_path.read_text()).get('program')
        if not isinstance(program,str) or not program:
            raise ValueError(f'{receipt_path} has no program address')
        selected[name]=program
    if not selected:
        raise FileNotFoundError('no archived program selector and no captured originals')
    return selected
def main():
    # Metadata consumers (including test_tooling) do not execute a VM.
    # Keep the real runtime mandatory when the smoke-test entry point runs.
    from solders.litesvm import LiteSVM
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    from solders.instruction import Instruction
    from solders.transaction import Transaction
    from solders.transaction_metadata import FailedTransactionMetadata
    results={}; payer=Keypair.from_seed(bytes(range(32))); rng=random.Random(10424)
    for name,address in program_addresses().items():
        svm=LiteSVM().with_transaction_history(0); svm.airdrop(payer.pubkey(),10**10)
        program=Pubkey.from_string(address); svm.add_program_from_file(program,ROOT/f'evidence/original/{name}/deployed.so')
        tests=[('empty',b''),('short',b'\x01'*7),('unknown',b'\xff'*8)]
        idl=ROOT/f'evidence/upstream/{name}.json'
        if idl.exists():
            for ix in json.loads(idl.read_text())['instructions']: tests.append((ix['name']+'-missing-accounts',bytes(ix['discriminator'])))
        for i in range(64): tests.append((f'random-{i}',rng.randbytes(8+i)))
        rows=[]
        for label,data in tests:
            tx=Transaction.new_signed_with_payer([Instruction(program,data,[])],payer.pubkey(),[payer],svm.latest_blockhash())
            result=svm.send_transaction(tx); failed=isinstance(result,FailedTransactionMetadata)
            rows.append({'case':label,'input_hex':data.hex(),'rejected':failed,'error':str(result.err()) if failed else None,'logs':result.meta().logs() if failed else result.logs()})
        results[name]={'binary_sha256':hashlib.sha256((ROOT/f'evidence/original/{name}/deployed.so').read_bytes()).hexdigest(),'cases':rows,'all_rejected':all(x['rejected'] for x in rows)}
        print(name,len(rows),results[name]['all_rejected'],flush=True)
    report=ROOT/'audit/local-validation.json'
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps({'runtime':'solders 0.27.1 / LiteSVM','scope':'Malformed instruction data and missing accounts only; no network or broadcast. No valid-state authorization/economic/CPI coverage.','programs':results},indent=2)+'\n')
    assert all(x['all_rejected'] for x in results.values())
if __name__=='__main__': main()
