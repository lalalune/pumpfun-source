# w19b09-shim-frame-c1t1: frame-slot naming outside validate (admin_cto 0x22a10, shim track)

Target `0x22a10` `admin_cto::execute`, `programs/pump/src/creator/admin_cto.rs`, pinned at 27,400 B. Ledger approach `framec1t1`.

## Wallet event signer array at the original's -0x680

Measured on main `4024f2632` after #4125. Instruction similarity is a diagnostic,
not byte-for-byte completion; the exact window count stays 1,034/1,035.

| | instruction similarity | normalized aligned tokens | differing normalized slots | bytes | exact normalized / raw windows | losses / raw_losses |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| before | 0.69811 | 2,331 | 3,173 | 27,400 | 1034 / 1034 | — |
| after | 0.69901 | 2,334 | 3,173 | 27,400 | 1034 / 1034 | 0 / 0 |

Raw instruction matches after sequence alignment rise from 2,210 to 2,213.
Positional raw equality stays 14,696/27,400 bytes and 246/3,425 eight-byte slots.

Window W2 (original 0x66f8, 0x6740, 0x6760): `event_signers.i` sits at -0x540 in FI53, the original has it at -0x680.
The original's -0x680 lies in the 40 B tail of main's `hkx` slot. The array is now written there through the `hkx` base
pointer, passed to `wallet`, which inlines. A 16 B `MaybeUninit` with `llvm.var.annotation` stays in `event_signers`'
place, so FI53 still hosts validate's 7 B target piece and no other offset moves. Calls stay 154 / 3. The source capture
changes only six bytes across those three instructions. Candidate offsets are
0x66e0, 0x6728 and 0x6748; this is not positional equality with the whole target.

The raw allocation base is retained before creating `holder_key`. Tail writes
start 32 bytes later and never create a new mutable borrow of the whole `hkx`
allocation while the shared key is live. A minimal host-side probe passes both
Miri Stacked Borrows and Tree Borrows; this does not establish whole-program
soundness. The pinned SBF build passes 388 signed synthetic differential cases
with zero mismatches and no stack diagnostics.

Reproduce using the identity recipe and a fresh main score:

```sh
python3 reconstruction/harness/fastbuild.py --src programs/pump --work <work> --out <out>
python3 reconstruction/harness/score.py <out>/unstripped.so --baseline <main-score.json> --json <out>/score.json
python3 reconstruction/harness/target_metric.py <out>/unstripped.so 0x22a10 --sym 'admin_cto::execute$'
python3 scripts/pump_admin_cto_differential.py --candidate <out>/candidate.so --output <out>/diff.json
```

Source input fingerprint: `9f28d6cfbe5089ca1f7f33919e6b55211675ab71648781ff54555dbbda060dcb`.
Unstripped SHA-256: `730dfd47229fd7aed04fc47a70b5262b1d620908fe236bd28a9d1d2644e8fd68`.

## J1 target pieces at the original's offsets

Measured on main `0325ac1d5`.

| | admin_cto | slots | bytes | normalized / raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| before | 0.70051 | 3,193 | 27,400 | 1034 / 1034 | |
| after | 0.70261 | 3,197 | 27,400 | 1034 / 1034 | none |

Window J1 (original 0x1858-0x1890): the join copy now reads `-0x655`, `-0x658`, `-0x668`, `-0x660` and writes `-0x535`, `-0x538`, as the original does.
`validate` writes the 7 B and 9 B pieces through `place` into `n7` (-0x658) and `n9` (-0x668) and rebuilds its result from them. Two 8 B stand-ins take
`event_signers`' 16 B place, so the 7 B join piece merges into the one at -0x538. `tg9`, `target` (6 B) and `s68` are lifetime-only stand-ins that keep
the DAG chain nodes and the host assignment. The shared arm takes the curve creator piecewise, because the stand-ins' markers would stop MemCpyOpt
forwarding a local creator copy. This drops 72 B of spill code, repaid by 9 more `holder_key` fill reads in the 312 block.
