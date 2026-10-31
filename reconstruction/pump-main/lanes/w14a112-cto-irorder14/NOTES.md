# w14a112-cto-irorder14: the bb14.i@bb2.i IR-order lead, verified and priced (notes only)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 13fe4536b (0.67256, 3,123 slots, M 2,245, jM 2,271 @ 27,400) for most of the work. The lead was
re-verified on main ebe5387e1 (0.67316): the main capture is eq_main, h289 alone gives 0.66896, and the lead gives
0.67596 @ 27,392 (the same +0.0028 at -8 B). Continuation of w14a101-cto-mirorder296
(its uncommitted SUMMARY is kept here as `w14a101-SUMMARY.json`). Ledger: approach `irorder14`,
keys `0x22a10-w14-13fe453-irorder14-*`.

**Result: no landable change. The best zero-loss measurement is main (0.67256 @ 27,400).** The lead is real as an
IR-order oracle (+0.0028 at -8 B) but it needs two IR moves that no ordinary spelling produces, it is anti-original
in structure, and it does not survive repaying the 8 B.

## 1. What the w14a101 lead actually is

w14a101's greedy (`io/g1.jsonl`) did not start from main: it was seeded with `bb10.i@bb16.i` (Err289 head moved
right after `bb7.i`, the hr=1 holder test). Its SUMMARY leaves the seed out. On main 13fe453 (capture eq_main):

| post-opt IR order (main capture, real llc RA) | ratio @ bytes | M | jM | fM |
| --- | --- | ---: | ---: | ---: |
| main | 0.67256 @ 27,400 | 2,245 | 2,271 | 2,376 |
| bb14.i@bb2.i alone | 0.66417 @ 27,400 | | | |
| seed bb10.i@bb16.i alone | 0.67056 @ 27,392 | | | |
| seed + bb14.i@bb2.i (the lead) | **0.67536 @ 27,392** | 2,254 | 2,362 | 2,423 |
| seed + bb16.i@bb3.i51.i (second lead) | 0.67426 @ 27,384 | | | |
| seed + both | 0.66737 @ 27,384 | | | |

The whole gain is in orig chunk 0x800 (+9 M, +91 jM); every other chunk is unchanged. errseq becomes
289 298 296 326 306 (289/298 in original order). 330 338 334 410 is unchanged.

From the h289 capture (w14a104's `if st.holder_reward&&!holder`, 0.66836 @ 27,400) the same layout is **one** move:
put the Err284 group (`bb2.i bb3.i.i63 exit.i`) right after `bb8.i` (the Err289 head, before its inlined
to_string panic and exit). That gives 0.67536 @ 27,392, the same tokens as the lead.

| Err284 group placed (h289 capture) | ratio @ bytes |
| --- | --- |
| where rustc puts it (after bb6.i) | 0.66836 @ 27,400 |
| before bb6.i | 0.65129 @ 27,400 |
| after bb12.i (hr=0 holder test) | 0.66866 @ 27,400 |
| after bb7.i | 0.66417 @ 27,400 |
| **after bb8.i (Err289 head)** | **0.67536 @ 27,392** |
| after exit24.i / bb15.i / exit31.i / bb21.i | 0.606-0.612 (errseq 289 326 ..) |
| after bb13.i | 0.66267 @ 27,400 |

**Mechanism.** On BPF a block that ends in a conditional branch is glued to its IR successor when that successor
is one of its targets (w14a78 sec. 2). Moving Err284 does two things at once: `bb6.i` (hr test) gets `bb12.i`
(hr=0 holder test) as its IR successor and falls into it, and `bb8.i` loses `bb3.i23.i` (its to_string panic) as
IR successor, so MBP lets the Err289 head fall into its own tail `exit24.i`.

## 2. It is not the original layout

Original 0x5e0-0x910: the mayhem test jumps far, the hr test **falls into the hr=1 arm**, that holder test falls
into the Err289 head, and the Err289 head ends `jeq r0,0,tail; ja panic` (head glued to the panic `ja`, as in
main and h289). The hr=0 arm at 0x710 tests holder and then new's tag with `jeq +1; ja` pairs (true target laid
out next). The Err306 head is at 0x750 and the Err289 tail at 0x818. The lead lays the hr=0 arm out first and glues
the Err289 head to its tail. Both are the opposite of the original. The +9 M is token alignment in chunk 0x800,
not structure. The structural head is w14a104's bb21>bb12 / bb25>bb21 route.

## 3. Composition (oracle, h289 capture)

| probe | ratio @ bytes |
| --- | --- |
| w14a104 head moves bb21>bb12, bb25>bb21, bb20>bb13 | 0.67386 @ 27,392 |
| lead + those three | 0.67126 @ 27,384 |
| lead + bb21>bb12, bb25>bb21 | 0.66976 @ 27,384 |
| w14a104 moves + Err289 tail after the Err306 head (original tail spot) | 0.67386 (no change) |
| lead + enabled test before bb3.i51.i (second lead, h289 naming bb13.i) | 0.66737 @ 27,384 |
| second lead alone on h289 | 0.66757 @ 27,392 |

The leads do not compose.

## 4. Spelling table (validate lines 283-296, raw-IR capture + opt + llc, main 13fe453)

pre-opt rule: rustc creates an LLVM block when it is first referenced, and a bool `switchInt` creates its 0-target
(the `else` / condition-false side) first. MIR folds `Not` into the switch, so `!`/`==false`/`match` arms do not
change the order. validate's first terminator is the mayhem test, so Err284 is always created second, between the
hr test and the hr=0 arm. No ordinary spelling makes it a later-created block: that would need a second predecessor
or a forwarding block.

| spelling | result |
| --- | --- |
| 284 `if !st.mayhem{}else{Err}` / `match st.mayhem{false=>{},true=>Err}` / `match{true=>Err,false=>{}}` / `==true` | token-identical to main |
| same four + h289 | identical to h289 |
| 284 `if st.mayhem{Err::<(),_>(error!(..))?;}` | same ratio as main, Err284 still second |
| same + h289; 289 Err via `Err(..)?` + h289 | identical to h289 |
| else-if chain 284/289/296 | identical to h289 |
| `let hr=st.holder_reward` or `let (mayhem,hr)=(..)` bound before 284 | identical to h289 |
| 289 `hr&&hopt!=Some(true)` | same ratio as main, order unchanged |
| 289 `match st.holder_reward{true=>if !holder{Err},false=>{}}` | 0.66497 @ 27,408 |
| 289/296 nested `if hr{if !holder{..}}else if/else{..}` (A5, A9, F11), tuple match (A6) | outline basin 26,976 |
| eager flags `let disabled=..`/`let immut=..` at 283 (F1-F4, F2h) | basins 26,712-27,360 |

## 5. Repaying the 8 B (task step c)

23 size knobs that still apply to the source ($SWARM/w11/sizeknobs-cto.json plus w14a82's kn/kn2 catalogs) were each
captured on top of h289 (13fe453). The Err284>bb8.i move was then applied to each capture:

| knob (on h289) | knob alone | + lead move |
| --- | --- | --- |
| cu_fee_oldunwrap = L_fee_unwrap_again = g_fee_unwrap (`fee.unwrap_or(old_fee)`) | 0.66317 @ 27,408 | **0.67046 @ 27,400** (< main) |
| g_w_clock_local = wl_ts_clockvar | 0.66727 @ 27,416 | 0.67425 @ 27,408 |
| ev_mint_key | 0.65918 @ 27,416 | 0.66617 @ 27,408 |
| ev_cb_local | 0.66127 @ 27,392 | 0.66797 @ 27,384 |
| cu_typed / sh_prog_let | 0.6655 @ 27,368 | 0.6722 @ 27,360 |
| 12 zero-byte knobs | 0.66537-0.66836 @ 27,400 | 0.67236-0.67536 @ 27,392 |
| pair g_w_clock_local + ev_cb_local (ebe5387) | 0.66078 @ 27,408 | 0.66747 @ 27,400 (main 0.67316) |

No combination at the pinned size beats main. A block-order greedy from the lead state (62 units x 25 positions,
689 of 1,500 jobs) found at best 0.67556 @ 27,376, and no 27,400 B move above 0.66387. The lead is a local optimum.

## Tools (`tools/`)

`mv2.py` moves post-opt IR blocks by name (`U1+U2@X` = before X, `U>X` = after X; to_string exits are named by
their short `exitNN.i`, first match wins). `mv.sh` runs that and scores with `px.py`. `bord.py` prints the execute
block order from the validate head and tags error blocks by their PumpError alloc. `asq.sh` prints the llc block
sequence via w14a97's `seq.py`. `capvar.sh`, `capraw.py`, `rx.py` and `batch.sh` are w14a101's capture pipeline,
repointed. `spell_b1.py` and `spell_b2.py` generate the spellings in section 4.
