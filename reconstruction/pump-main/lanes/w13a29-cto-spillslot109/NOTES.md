# Admin CTO: transfer-CPI copies and InvalidCreator comparison order

Target: `0x22a10`, `admin_cto::execute`, at the original 27,400-byte size.
The accepted source combines #3028's transfer-CPI copy layout with #3095's
sharing-first `InvalidCreator` comparison. Fresh ordinary identity builds
against the same verified main source produced:

| Source | Sequence similarity | Differing 8-byte slots | Handler bytes |
| --- | ---: | ---: | ---: |
| Main before these changes | 0.59916 | 3,313 | 27,400 |
| #3095 alone | 0.60126 | 3,313 | 27,400 |
| #3028 alone | 0.61833 | 3,306 | 27,400 |
| Combined | 0.62043 | 3,306 | 27,400 |

All three candidates retain 1,034/1,035 raw and normalized exact windows, with
no missing, resized, gained or lost exact windows. This is partial sequence
similarity progress, not a new complete-window match or whole-Pump identity.

The transfer-CPI account literal evaluates `payer` first and uses equivalent
`AccountInfo` copies for both `pump_amm` program values. The eight field values
and shared lamports/data cells remain the same. Literal evaluation order does
not change the generated CPI account order. The event reads the holder flag
from the curve field assigned earlier in the handler. #3095 swaps two pure
Pubkey equality checks that produce the same `InvalidCreator` error. All 27
lexical macro positions remain unchanged.

The exploratory IR analysis that motivated these changes used private,
unretained inputs and is not a reproducible validation artifact. Its scratch
scripts are omitted. The measurements above come from ordinary source builds
and the maintained `score.py` and `target_metric.py` tools; runtime validation
is recorded separately in the completion checkpoint.

Reproduction with the documented identity toolchain:

```sh
python3 reconstruction/harness/fastbuild.py --src programs/pump --work <work> --out <candidate> --recipe identity
python3 reconstruction/harness/score.py <candidate>/unstripped.so --baseline <baseline-score.json> --json <candidate>/score.json
python3 reconstruction/harness/target_metric.py <candidate>/unstripped.so 0x22a10 --sym 'admin_cto::execute'
python3 scripts/pump_admin_cto_differential.py --candidate <candidate>/candidate.so --output <runtime-report.json>
```
