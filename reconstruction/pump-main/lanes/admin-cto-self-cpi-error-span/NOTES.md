# admin_cto self-CPI error jump spans

Target: Pump Main `admin_cto::execute`, original `0x22a10`, 27,400 bytes.
Baseline: `bc659cc449d05e880294a62640a712b21c7f80c6` (program input fingerprint equals landed FCC).

The branches at original window offsets `0x5470` and `0x54e8` were each one
instruction short. Move one existing initialized holder-key byte read from the
sweep gate to the self-CPI `invoke_signed` error conversion. The Clock error
read and the sweep-gate account-pointer store remain intact. This preserves
the existing `Error::from` conversion and the source's 772 physical lines.
The holder-key allocation remains initialized and live at the later read.
Only source lines 647 and 767 change; there is no embedded machine code.

| Measurement | Fresh main | Candidate |
| --- | ---: | ---: |
| Normalized aligned instructions | 2389 | 2391 |
| Normalized instruction similarity | 0.715483678 | 0.716082659 |
| Raw aligned instructions | 2256 | 2258 |
| Raw instruction similarity | 0.675651393 | 0.676250374 |
| Same-offset raw bytes | 13324 / 27400 | 13831 / 27400 |
| Same-offset raw 8-byte slots | 133 / 3425 | 135 / 3425 |
| Same-offset normalized bytes | 14373 / 27400 | 14872 / 27400 |
| Same-offset normalized slots | 136 / 3425 | 140 / 3425 |
| Exact normalized / raw windows | 1034 / 1034 | 1034 / 1034 |

Both aligned instruction streams gain exactly `0x5470` and `0x54e8` and lose
no original indices. The existing `0x53d8` jump match is retained. Alignment
membership is a diagnostic, not semantic proof. Relocating the read changes
6,983 positional bytes across 1,787 slots. Function size and 154 internal /
3 external call counts remain unchanged. `losses=[]`, `raw_losses=[]`.
The function is not byte-for-byte complete.

The standard identity build has no stack warnings. All 388 signed synthetic
original/candidate differential pairs pass with the exact runtime image below.
These tests do not establish whole-program byte identity or exercise every
error path; the moved initialized read and unchanged error conversion were
also independently reviewed at source level.

## Reproduce

Build baseline `bc659cc449d05e880294a62640a712b21c7f80c6` and this commit with separate work/output directories:

```sh
python3 reconstruction/harness/fastbuild.py --src programs/pump --work <work> --out <out>
python3 reconstruction/harness/score.py <out>/unstripped.so --baseline <main-score.json> --json <out>/score.json
python3 reconstruction/harness/target_metric.py <out>/unstripped.so 0x22a10 --sym 'admin_cto::execute$'
python3 scripts/pump_admin_cto_differential.py --candidate <out>/candidate.so --output <out>/diff.json
```

Baseline source SHA-256: `75dff1fae41b6c2c714424deda198546f7543628937b635bfe4dc25292223629`.
Baseline unstripped SHA-256: `176a8f64d84f45288818326bba4bd3cfd6941d4a83a050038ed7535fb7b74dd4`.
Candidate source SHA-256: `40efe7b97f01587aed404b113d12e26ebd253107e5c63b660043365c200f45ec`.
Candidate unstripped SHA-256: `9bded91f3367afdf9b4c49876d524bdc586e6c80812cd1ffae2a1de3c3fed78c`.
Candidate runtime SHA-256: `8dda8719d35d9f705f4321dc10695a90001563fc48e142030f0b204f49991945`.
Runtime receipt SHA-256: `547628f9c82f5250b66be54978dd21e33ca63a962838e8b1ebc817bdfc5b6818`.
Original window SHA-256: `6a7659fd34097683cbfdae56187f5f73a3ecae20e52ac06a3fd25837e4137a96`.
