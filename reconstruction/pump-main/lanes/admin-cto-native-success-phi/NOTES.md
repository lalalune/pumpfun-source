The positive native sweep now maps a successful transfer to its amount inside the positive branch, while the zero branch returns `Ok(0)` directly. This separates the zero result from the positive amount's live range. The compiler restores the target's `r6` amount, holder-vault pointer reloads and final result copy. The two native holder-byte shim reads are removed because the recovered instructions supply their 16-byte size budget.

Target: Pump Main `admin_cto::execute`, original `0x22a10`, 27,400 bytes. Fresh main `525085ff4274c23fa299ed74bdbd1c2e83face36` → candidate:

| Measurement | Main | Candidate |
| --- | ---: | ---: |
| Normalized aligned instructions | 2975 | 2986 |
| Normalized instruction similarity | 89.09853% | 89.42797% |
| Raw aligned instructions | 2916 | 2928 |
| Same-offset raw matching bytes | 21782 / 27400 | 21877 / 27400 |
| Same-offset raw matching 8-byte slots | 1896 / 3425 | 1922 / 3425 |
| Exact normalized / raw windows | 1034 / 1034 | 1034 / 1034 |

All 95 changed bytes now equal the original at the same offsets. There are 26 newly exact slots and zero positional byte or slot losses. Raw alignment gains 12 instructions with zero losses; normalized alignment gains 11 with zero losses. `losses=[]`, `raw_losses=[]`. The target size and 154 internal / 3 external calls are unchanged. These partial diagnostics do not establish full byte-for-byte completion.

Only physical source line 664 changes; all 772 lines and error locations remain intact. This uses ordinary Rust result control flow and removes unsafe reads. Independent review checked that the zero amount remains zero, positive native transfers retain rent/CPI/error order, and token behavior is unchanged. All 388 signed synthetic differential cases pass against the captured original using the exact candidate runtime. They are bounded runtime evidence, not exhaustive path coverage.

Source fingerprint: `1c89d9ff6faa421dc3ef2fdff8e3c9f2af5c6d4996c9ddbba1e2f5dbcfd741da`.
Unstripped image: `c663d263ce8272568b779614e0e88914004f3cc31d2c066a0eef88af7412f50e`.
Runtime image: `3984ea8e4d8516afffb891932ed7564b5899840469618588aedd9934b41778b5`.
Fresh-main image: `6c2a006a084364dc95f226a567c8547911a87a82c8ca24d6a03d477ca204f053`.
Runtime receipt SHA-256: `6dfa12c25090fc987b6046c7543dd4b8356c66ff02616e48b0846b3281b0eb8e`.

Reproduce with the pinned identity recipe in `reconstruction/harness/fastbuild.py`, then `reconstruction/harness/score.py <candidate> --baseline <fresh-main-score.json>`, `reconstruction/harness/target_metric.py <candidate> 0x22a10 --sym 'admin_cto::execute$'`, and `scripts/pump_admin_cto_differential.py --candidate <candidate.so> --output <diff.json>`.
