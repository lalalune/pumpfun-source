# w19a09-shim-nat-rcweights: Rc overflow-trap weights on the natural clones

Target `0x22a10` `admin_cto::execute`. Base s10 (w19a04: the natural sweep tail lever on w19a08 x1, plus a holder_key byte read). This adds the mint lamports trap weight 1:9 (`aicl::<10>`) and two holder_key byte reads in the `Clock::get` error path.

Weights on the natural `Rc::clone` traps steer C1's first-round evictions. Edge numbering: 0..25 are T1 (13 clones x lamports,data), 26..41 are C1 (8 clones x lamports,data).

| base | spec | M | bytes | T1 | C1 | all3 |
|---|---|---:|---:|---:|---:|---:|
| n2 | - | 2,272 | 27,448 | 382 | 148 | 3,158 |
| n2 | 34=7 | 2,350 | 27,416 | 382 | 228 | 3,197 |
| n2 | 0=40,4=40,15=200,16=40,26=10,32=40,34=7,39=40 | 2,436 | 27,384 | 443 | 244 | 3,200 |
| s7 | - | 2,881 | 27,336 | 672 | 231 | 3,199 |
| s7 | 34=10 | 2,931 | 27,344 | 674 | 278 | 3,228 |
| s10 | 34=10 | 2,955 | 27,384 | 675 | 279 | 3,232 |
| s10 | 34=10 + 2 reads | 2,956 | 27,400 | | | |

The IR edit on the post-opt module and the source form `rcw::<D,_>` give the same bytes.
