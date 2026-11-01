# w18a03-shim-rescreen-ann: annotation and volatile-pin cells re-screened on the outline main

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Slim pre-opt oracle; ledger approach `rescreen-ann`; tables and tools on
`origin/swarm/w18a03-shim-rescreen-ann`.

On main with its 10 `read_volatile(holder_key)` fill reads removed (M 2,334 at 27,320 B, so the fill costs 0 M at that block), the
best single cell at +8 B is +1 M: one fill read moved out of the validate error block into the wallet or sweep range fixes the
displacement of `ja -360` (orig 0x63a0). The landed spelling swaps one fill read for `pt8` on the wallet quote==native byte, one
instruction more at the wallet head and one fewer in validate.
