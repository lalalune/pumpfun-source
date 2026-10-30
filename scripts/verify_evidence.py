#!/usr/bin/env python3
"""Verify saved evidence locally. This is NOT a rebuilt-source verification."""
import hashlib,json,pathlib,struct
from capture import b58
from analyze import elf_layout
ROOT=pathlib.Path(__file__).resolve().parents[1]
# Every capture this repository publishes. The gate used to assert a count floor (`count>=4`),
# which hid the loss of up to five captures: deleting four of the nine still passed
# (verified on a sealed copy). Pin the exact set so a removal is a hard failure.
EXPECTED_CAPTURES=frozenset({
 'evidence/dependencies/associated_token','evidence/dependencies/donation_relay',
 'evidence/dependencies/spl_token','evidence/dependencies/spl_token_2022',
 'evidence/dependencies/token_metadata','evidence/original/mayhem','evidence/original/pump',
 'evidence/original/pump_amm','evidence/original/pump_fees'})
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    count=0
    upstream=json.loads((ROOT/'evidence/upstream/provenance.json').read_text())
    for name,expected in upstream['file_sha256'].items():
        assert sha((ROOT/'evidence/upstream'/name).read_bytes())==expected
    for f in sorted((ROOT/'evidence').glob('**/capture.json')):
        m=json.loads(f.read_text()); folder=f.parent
        if m.get('loader')=='legacy-v2':
            p=(folder/'program-account.bin').read_bytes(); b=(folder/'deployed.so').read_bytes()
            assert p==b and sha(b)==m['payload_sha256']==m['program_sha256'] and len(b)==m['payload_bytes']
            assert m['owner']=='BPFLoader2111111111111111111111111111111111'
            assert m['genesis_hash']=='5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d'
            assert m.get('last_deploy_slot') is None and m.get('upgrade_authority') is None and not any(k in m for k in ('programdata','programdata_sha256','programdata_bytes'))
            elf_layout(b); print(folder.relative_to(ROOT),'OK (legacy loader)'); count+=1; continue
        p=(folder/'program-account.bin').read_bytes(); d=(folder/'programdata-account.bin').read_bytes(); b=(folder/'deployed.so').read_bytes()
        assert sha(p)==m['program_sha256']; assert sha(d)==m['programdata_sha256']; assert sha(b)==m['payload_sha256']
        assert len(p)==36 and struct.unpack_from('<I',p)[0]==2
        assert b58(p[4:])==m['programdata']
        assert struct.unpack_from('<I',d)[0]==3
        assert struct.unpack_from('<Q',d,4)[0]==m['last_deploy_slot']
        if d[12] not in (0,1):
            raise ValueError(f'{folder.relative_to(ROOT)}: invalid ProgramData upgrade authority option tag {d[12]}')
        assert (b58(d[13:45]) if d[12] else None)==m['upgrade_authority']
        assert d[45:]==b and len(b)==m['payload_bytes'] and len(d)==m['programdata_bytes']
        assert m['owner']=='BPFLoaderUpgradeab1e11111111111111111111111'
        assert m['genesis_hash']=='5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d'
        slots=m['context_slots']; assert slots and slots==sorted(slots) and m['last_deploy_slot']<=slots[0]
        layout=elf_layout(b); assert layout['trailing_all_zero']
        print(folder.relative_to(ROOT),'OK'); count+=1
    seen=frozenset(f.parent.relative_to(ROOT).as_posix() for f in (ROOT/'evidence').glob('**/capture.json'))
    missing=sorted(EXPECTED_CAPTURES-seen); unexpected=sorted(seen-EXPECTED_CAPTURES)
    assert not missing, f'capture manifest missing from evidence/: {missing}'
    assert not unexpected, f'unexpected capture in evidence/ (not in EXPECTED_CAPTURES): {unexpected}'
    assert count==len(EXPECTED_CAPTURES), f'verified {count}, expected {len(EXPECTED_CAPTURES)}'
    print(f'{count} captures verified; no source rebuild claimed.')
if __name__=='__main__': main()
