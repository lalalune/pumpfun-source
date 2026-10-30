#!/usr/bin/env python3
"""Verify saved evidence locally. This is NOT a rebuilt-source verification."""
import hashlib,json,pathlib,struct
from capture import b58
from analyze import elf_layout
from solders.pubkey import Pubkey
ROOT=pathlib.Path(__file__).resolve().parents[1]
# Canonical address of every capture this repository publishes. The gate used to hash the
# payload and the ProgramData link but never compare `capture.json["program"]` with the
# folder it sits in, so swapping pump and pump_amm still printed "9 captures verified".
# The originals come from the archived IDL/inventory addresses (`evidence/interface-inventory.json`
# and `declare_id!`); the dependencies carry the fixed mainnet program ids.
PROGRAM_ADDRESS={
 'evidence/dependencies/associated_token':'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL',
 'evidence/dependencies/donation_relay':'RLAYHr9TRFcKB2ubYQhspcnXiaGpaVzNQvHytt47RZu',
 'evidence/dependencies/spl_token':'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
 'evidence/dependencies/spl_token_2022':'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb',
 'evidence/dependencies/token_metadata':'metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s',
 'evidence/original/mayhem':'MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e',
 'evidence/original/pump':'6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P',
 'evidence/original/pump_amm':'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA',
 'evidence/original/pump_fees':'pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ'}
# Every capture this repository publishes. The gate used to assert a count floor (`count>=4`),
# which hid the loss of up to five captures: deleting four of the nine still passed
# (verified on a sealed copy). Pin the exact set so a removal is a hard failure.
EXPECTED_CAPTURES=frozenset(PROGRAM_ADDRESS)
# The upstream IDLs hashed in evidence/upstream/provenance.json. That file also says which
# files to hash, so deleting an IDL together with its entry passed. Pin the set here too.
EXPECTED_UPSTREAM=frozenset({'pump.json','pump_amm.json','pump_fees.json'})
def sha(b): return hashlib.sha256(b).hexdigest()
UPGRADEABLE_LOADER=Pubkey.from_string('BPFLoaderUpgradeab1e11111111111111111111111')
# The program account only stores its ProgramData address, and every hash is checked against the
# capture's own record, so another program's account, ProgramData and payload could be filed under
# this program id. ProgramData must be the loader PDA of `program`, which ties the bytes to the id.
def check_programdata_pda(m):
    derived,_=Pubkey.find_program_address([bytes(Pubkey.from_string(m['program']))],UPGRADEABLE_LOADER)
    if str(derived)!=m['programdata']:
        raise AssertionError(f"programdata {m['programdata']} is not the loader PDA of {m['program']} ({derived})")


class EvidenceError(Exception): pass
def check(ok,msg='evidence check failed'):
    # Explicit check instead of `assert`: `python -O` / PYTHONOPTIMIZE strips asserts,
    # which made a corrupted capture report "9 captures verified".
    if not ok: raise EvidenceError(msg)
def main():
    count=0
    upstream=json.loads((ROOT/'evidence/upstream/provenance.json').read_text())
    listed=frozenset(upstream['file_sha256'])
    missing=sorted(EXPECTED_UPSTREAM-listed); unexpected=sorted(listed-EXPECTED_UPSTREAM)
    check(not missing, f'upstream IDL missing from evidence/upstream/provenance.json: {missing}')
    check(not unexpected, f'unexpected upstream file in provenance.json (not in EXPECTED_UPSTREAM): {unexpected}')
    for name,expected in upstream['file_sha256'].items():
        check(sha((ROOT/'evidence/upstream'/name).read_bytes())==expected)
    for f in sorted((ROOT/'evidence').glob('**/capture.json')):
        m=json.loads(f.read_text()); folder=f.parent; key=folder.relative_to(ROOT).as_posix()
        # The gate exists to publish finalized snapshots, but the declared commitment
        # was never read: a capture taken at `processed`/`confirmed` still passed.
        check(m.get('commitment')=='finalized', f'{key}: commitment {m.get("commitment")!r}')
        check(m['program']==PROGRAM_ADDRESS[key], f'{key}: capture program {m["program"]}, expected {PROGRAM_ADDRESS[key]}')
        if m.get('loader')=='legacy-v2':
            p=(folder/'program-account.bin').read_bytes(); b=(folder/'deployed.so').read_bytes()
            check(p==b and sha(b)==m['payload_sha256']==m['program_sha256'] and len(b)==m['payload_bytes'])
            check(m['owner']=='BPFLoader2111111111111111111111111111111111')
            check(m['genesis_hash']=='5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d')
            check(m.get('last_deploy_slot') is None and m.get('upgrade_authority') is None and not any(k in m for k in ('programdata','programdata_sha256','programdata_bytes')))
            check(elf_layout(b)['trailing_all_zero']); print(key,'OK (legacy loader)'); count+=1; continue
        p=(folder/'program-account.bin').read_bytes(); d=(folder/'programdata-account.bin').read_bytes(); b=(folder/'deployed.so').read_bytes()
        check(sha(p)==m['program_sha256']); check(sha(d)==m['programdata_sha256']); check(sha(b)==m['payload_sha256'])
        check(len(p)==36 and struct.unpack_from('<I',p)[0]==2)
        check(b58(p[4:])==m['programdata'])
        check_programdata_pda(m)
        check(struct.unpack_from('<I',d)[0]==3)
        check(struct.unpack_from('<Q',d,4)[0]==m['last_deploy_slot'])
        if d[12] not in (0,1):
            raise ValueError(f'{key}: invalid ProgramData upgrade authority option tag {d[12]}')
        check((b58(d[13:45]) if d[12] else None)==m['upgrade_authority'])
        check(d[45:]==b and len(b)==m['payload_bytes'] and len(d)==m['programdata_bytes'])
        check(m['owner']=='BPFLoaderUpgradeab1e11111111111111111111111')
        check(m['genesis_hash']=='5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d')
        slots=m['context_slots']; check(slots and slots==sorted(slots) and m['last_deploy_slot']<=slots[0])
        layout=elf_layout(b); check(layout['trailing_all_zero'])
        print(key,'OK'); count+=1
    seen=frozenset(f.parent.relative_to(ROOT).as_posix() for f in (ROOT/'evidence').glob('**/capture.json'))
    missing=sorted(EXPECTED_CAPTURES-seen); unexpected=sorted(seen-EXPECTED_CAPTURES)
    check(not missing, f'capture manifest missing from evidence/: {missing}')
    check(not unexpected, f'unexpected capture in evidence/ (not in EXPECTED_CAPTURES): {unexpected}')
    check(count==len(EXPECTED_CAPTURES), f'verified {count}, expected {len(EXPECTED_CAPTURES)}')
    print(f'{count} captures verified; no source rebuild claimed.')
if __name__=='__main__': main()
