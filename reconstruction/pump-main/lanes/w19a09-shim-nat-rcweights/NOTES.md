# w19a09-shim-nat-rcweights: Rc overflow-trap weights on the natural clones

Target `0x22a10` `admin_cto::execute`. Base: the shim-free whole-file source n2 (w19a03, from w19a02 f17 and w19b08 cr28), M 2,272 at 27,448 B.

On n2, weights on the natural `Rc::clone` overflow traps act as they did on w19b01's plain clones:

| spec (edge = den, 1:(den-1)) | M | bytes | T1 exact | C1 exact | all3 |
|---|---:|---:|---:|---:|---:|
| n2 | 2,272 | 27,448 | 382 | 148 | 3,158 |
| 34=7 (mint lamports) | 2,350 | 27,416 | 382 | 228 | 3,197 |
| + 15=200 (vault authority data) | 2,396 | 27,416 | 422 | 228 | 3,197 |
| + 4=40, 16=40, 0=40 | 2,419 | 27,384 | 443 | 227 | 3,200 |
| + 26=10, 32=40, 39=40 | 2,436 | 27,384 | 443 | 244 | 3,200 |
| + two holder_key byte reads (Clock::get error, ConstraintSeeds error) | 2,442 | 27,400 | | | |

Edges: 0..25 are T1 (13 clones x lamports,data), 26..41 are C1 (8 clones x lamports,data). The IR edit on the post-opt module and the source form `rcw::<D,_>` give the same bytes (sig 001f4748ff9e).
