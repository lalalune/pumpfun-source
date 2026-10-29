# Legacy capture metadata

`scripts/verify_evidence.py` checks the legacy loader branch's payload hashes,
owner and genesis hash, but never reads `last_deploy_slot`, `upgrade_authority`
or the `programdata*` keys. A legacy capture can therefore claim a deployment
slot, an upgrade authority and ProgramData bytes and still pass the archived
gate. The retained legacy capture is
`evidence/dependencies/associated_token` (the other eight captures are
upgradeable).

The legacy loader has no ProgramData account, deployment slot or upgrade
authority. This packet binds every known capture folder to its expected loader,
then checks the record:

- the legacy capture must declare `legacy-v2`; all other known captures must
  omit `loader`, so unknown values and capture-folder swaps fail;
- legacy: null slot and authority, no `programdata`, `programdata_sha256` or
  `programdata_bytes`, and the legacy loader owner;
- upgradeable: integer slot, optional 32-byte base58 authority, all three
  programdata keys, and the upgradeable loader owner.

```sh
python3 -B research/tooling-legacy-capture-metadata-20261029/test_verify.py
python3 -B research/tooling-legacy-capture-metadata-20261029/verify.py --repo .
python3 -B scripts/verify_evidence.py
python3 -B scripts/test_tooling.py
```

`test_verify.py` copies the one legacy capture and upstream evidence to a
detached temporary tree, injects a deploy slot and authority, and runs the
archived `verify_evidence.main()`: it exits successfully. The new validator
rejects the same record. The other controls cover the three legacy keys, a
malformed upgradeable authority, the nine-capture split and stale observations.

## Limits

This reads only `capture.json`; it does not re-fetch accounts, re-hash the
archived binaries, or authenticate `captured_at_utc`. The archived verifier and
all capture bytes remain unchanged. A matching declaration does not prove the
account was read at that address, and no runtime, source or security claim is
added.
