# Sharing-CPI AccountInfo clone order

The source explicitly constructs the sharing CPI's event-authority and program
`AccountInfo` values. It preserves their fields and the lamports/data `Rc` clone
order, while loading the plain key reference after those clones.

Reviewed against main `6ac6f9b6789b0dddcbf03989f5b8511e732bdb3e`:

| Source | Admin bytes | Instruction-token ratio | Differing 8-byte slots |
| --- | ---: | ---: | ---: |
| Main | 27,400 | 0.56291 | 3,315 |
| Explicit sharing-CPI clones | 27,400 | 0.56741 | 3,312 |
| With event-info and sweep-signer setup from #3020 | 27,400 | 0.57100 | 3,312 |

All three candidates retain 1,034/1,035 raw and normalized exact windows with no
missing, resized or lost windows. This is partial alignment within the unmatched
admin handler, not a new exact window or whole-program identity.

The combined source was built with the normal identity recipe. Runtime evidence
compares 363 signed synthetic admin cases and 408 one-hop swap/boundary cases;
the latter disable AMM PDA signature verification. These are bounded comparisons,
not an all-input semantic proof. Scratch IR scans and unretained worker inputs
are outside this source change.
