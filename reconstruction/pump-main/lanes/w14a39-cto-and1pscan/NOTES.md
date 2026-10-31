# w14a39-cto-and1pscan: and-1 outline basin re-port + clone scan (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a10-cto-and1outline (#3224) and w14a07-cto-cold306 (#3223).
Ledger keys: `0x22a10-w14-faf9962-and1pscan-*-v1`, `0x22a10-w14-28ab23a-and1pscan-*-v1`.

## Landing 1: TCF pump_creator_vault_ata literal, data clone before lamports clone

Found while screening the Rc-order swap (data.clone() before lamports.clone()) per AccountInfo literal in the and-1
basin. On main itself, swapping the two Rc clones in the `pump_creator_vault_ata` literal of the
`transfer_creator_fees_to_pump_v2` CPI (`K,L,O,D,..` -> `K,D,O,L,..`) gains 2 matched instructions:

| | main 28ab23a | this branch |
| --- | ---: | ---: |
| admin_cto ratio | 0.65488 | **0.65548** |
| M (matched orig insns) | 2,186 | 2,188 |
| slots_diff | 3,280 | 3,280 |
| bytes | 27,400 | 27,400 |
| normalized / raw | 1034 / 1034 | 1034 / 1034, 0 losses |
| differential | | 363 cases, 0 mismatches |
| unstripped sha256 | | `294794674d664b84312c6abc1251c11a9a8fb5ad25574e32f997975a4feee1ed` |

(On main faf9962 the same edit was +2 M as well: 0.65129 -> 0.65189.)
