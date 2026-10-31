# w14a144-cto-vinarm: per-arm sharing_update local, and the vin/payload-local family priced on main, O and O312

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Base main ebe5387
(0.67316, 3,123 slots). Continues w14a123-cto-origfill (#3593) next ideas 3 and 4. Ledger approach `vinarm`, keys
`0x22a10-w14-ebe5387-vinarm-*`.

## Landable change (pl2)

The execute-level sharing tree assigns `sharing_update` per arm instead of returning it in the tuple:

```rust
let mut sharing_update:Option<Option<Pubkey>>=None;
let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}
  else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}
  else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};
```

Same semantics (holder arm `Some(None)`, shared non-holder `Some(new)`, not shared `None`). Line count unchanged.

| build | admin_cto ratio | slots | bytes | normalized / raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| main ebe5387 | 0.67316 | 3,123 | 27,400 | 1034 / 1034 | |
| pl2 (measure.sh, unstripped sha e9df54086dcfc8ca) | **0.67346** | 3,124 | 27,400 | 1034 / 1034 | none |

Runtime differential: 363 cases, 0 mismatches. The change is local: the fee/flag init block at 0x17d0 is rescheduled
(the `[r10-2272]` store moves up) and the 0x19c0 sharing-payload copy runs in the other piece order.

**Landed as #3621 (merge e88f9d559).** Everything below is from the follow-up branch `swarm/w14a144-cto-vinarm-2`.

## Angle result: the vin / payload-local family, priced on main, O and O312

Oracle: w14a108/w14a123 raw-IR capture + opt + llc (`rx.py`; the main capture is `eq_main` true and reproduces
O = 26,992 / M 1,953 and O312 = 27,184 / M 2,194). `tools/vr.sh` scores each capture plain, on base O (call-site noinline
on the 307 and 312 `to_string`) and on O312 (312 only). Cells are bytes / M / rfjM (w14a108 `fr.py`, difflib). "LCS" is
w14a128 `lcschunk.py` true-LCS rfj matched tokens (main 3,007), which does not have difflib's alignment artifacts.

| gene | form | main: B / M / rfjM | O | O312 | LCS rfj |
| --- | --- | --- | --- | --- | ---: |
| main ebe5387 | | 27400 / 2247 / 2810 | 26992 / 1953 / 2790 | 27184 / 2194 / 2779 | 3,007 |
| `vin` | whole tree inside validate before `match fee`, validate returns the tuple | 27168 / 1555 / 2791 | 26736 / 1550 / 2793 | 26952 / 1570 / 2778 | 2,947 |
| `vinh` | vin + holder arm `Some(new)` (= vin + ha) | 27328 / 1234 / 2127 | 26896 / 1231 / 2126 | 27112 / 1249 / 2110 | 2,467 |
| `vinr` | vin, tree as `match (shared,holder)` | identical to vin | | | 2,947 |
| `vins` | control: tuple-returning validate, tree after the fee checks | 27928 / 1307 / 2188 | 27496 / 1271 / 2158 | 27712 / 1268 / 2147 | 2,490 |
| `vpl1` | vin + per-arm `Option<Option<Pubkey>>` local set inside each validate target arm | 27312 / 1465 / 2720 | 26880 / 1460 / 2718 | 27096 / 1522 / 2698 | 2,937 |
| `vpl2` | vpl1 + shared override in the non-holder arm | 27424 / 1230 / 2131 | 26992 / 1223 / 2133 | 27208 / 1243 / 2111 | 2,465 |
| `vpl3` | vpl1 with `su=if shared{Some(new)}else{None}` per arm | 27424 / 1458 / 2671 | 26984 / 1455 / 2634 | 27208 / 1458 / 2624 | 2,928 |
| `ha` (w14a123) | holder arm `Some(args.0)` | 27168 / 2061 / 2846 | 26696 / 2003 / 2825 | | 2,986 |
| `pl1` | execute-level payload local, holder arm `Some(args.0)` (= ha) | 27168 / 2062 / 2844 | 26696 / 2004 / 2823 | 26952 / 2010 / 2812 | 2,985 |
| **`pl2`** | execute-level payload local, holder arm `Some(None)` (**landed**) | **27400 / 2248 / 2810** | 26992 / 1954 / 2794 | 27184 / 2195 / 2779 | 3,007 |
| `pl5` | pl2, `target=` before `sharing_update=` | 27416 / 2247 / 2810 | 26984 / **2028** / 2777 | 27200 / 2195 / 2779 | 3,008 |
| `pl7` | pl2 + collect_old/skip as mut locals | 27448 / 1710 / 2197 | 26976 / **2014** / 2776 | 27232 / 1658 | 2,483 |

- **True LCS removes the skeleton lead.** ha's "+36 rfjM" (difflib) is -21 in true LCS, vin is -60, vpl1 -70; on O and O312
  the vin family is -51 to -62 against its own base. No form in the family gains skeleton on any base.
- **The vin collapse is frame, not registers.** w14a84 `regceil.py`: vin plain 0.468, register-masked 0.443, frame-masked
  (L1) 0.619, L2 0.772 (main 0.673 / 0.768 / 0.703 / 0.786). The w14a84 private RAPRIO llc climb (`cclimb.sh`, 170 colour
  singles, 12 forces) takes vin only to **0.49872** (27,184 B). It is not RA-recoverable.
- On base O, two per-arm local forms are clearly positive: `pl5_O` +75 M and `pl7_O` +61 M over O. On main and O312 they are
  neutral or collapse. They would matter only to a lane that lands the 307+312 outline (O needs +408 B of repay).

## Other mechanisms screened on e88f9d5 (after pl2 landed)

| gene | form | result |
| --- | --- | --- |
| w2a / w2g | collect_old (and skip) as mut locals | 0.51182 @27,448 (collapse) |
| w2b, w3a, w3b, pl3, pl10, pl11, pl13-15, pl18, pl19 | skip mut local; `let old_creator;let old_fee;` deferred; `let cashback;` deferred; spelling variants of pl2 | byte-identical or 0.67346 tie |
| w2c | `let mut sharing_update` before `let args`/validate | 0.55164 @27,360. The arg spill moves to the original's `[r10-0x928]`, but RA changes |
| w2d, w2e, w3c | sharing_update declared outside the outer block; drop it from the `Ok(..)?` passthrough; `let mut target;` outside | **frame-only permutations** (fM, rfjM and L1 equal to main): 0.5725 / 0.55123 / 0.37927 @27,400. `tools/fmap.py` gives the slot remap (block moves of +32/-8/-248) |
| w2h, pl6, pl12 | shared non-holder arm `Some(new)` instead of `Some(args.0)`; `Some(if holder{None}else{..})` | 0.48 (collapse, ~-640 M) |
| pl17 | holder arm `Some(new)` | = ha (27,168) |
| v1-v4 | per-arm deferred-init `cashback` / `target` inside validate's target arms | byte-identical to main |
| v5, v6 | cashback set before the holder error / `let mut cashback=false` | 0.62819 @27,352 |
| vsp0-2, vsp*i/a | validate split into validate + validate_fee, with the tree before the fee checks (plain, `#[inline]`, `#[inline(always)]`) | the sweep stops being inlined (execute 9,096 B); dead even for the control vsp0 |
| vo1 / vo1n / vo6 | validate fills an `&mut Option<Option<Pubkey>>` out-param per arm (keeps `Result<Pubkey>`) | 0.52086 @27,288. L2 0.785 = main and LCS rfj 2,989 (+5/+6 in validate chunk 0x1000), but frame-masked L1 0.656 vs 0.703 |
| vo1b/c/d | vo1 with the declaration moved | 0.52-0.55 |
| vo3 / vo5 | out-param set after the arms / at validate's end | 0.40 / 0.36 |
| d338pl2 | pl2 on w14a115-cto-devol338st (#3510; line-338 read_volatile replaced by an ordinary store) | 0.67346 @27,400. A tie with main, but it removes one placeholder. Needs `--allow-neutral` |

## Conclusion

The original's per-arm sharing tree, computed inside validate before the fee checks, cannot be expressed with LLVM's
current assignment. Every form that moves the payload or the tree into validate (tuple return, out-param, split fn)
keeps or nearly keeps the skeleton, but shifts the frame and loses 500-1,000 M. Neither RA forcing nor any of the
declaration-position frame permutations tried here recovers it. The one lever that worked is execute-level:
`sharing_update` as a mut local assigned per arm (+0.0003, landed).

## Tools (`tools/`)

- `og.py`: every gene above (old/new exact replacements; line count kept). `vr.sh <name> <genes> <slot>`: capture, then
  score plain, O and O312 (`SRCB` = crate to start from, `RES` = results file).
- `fmap.py a.bin b.bin`: r10 offset remap between two frame-only variants. `tab.py`: builds `screen_table.md`.
- Needs w14a123's `tools/` (cv.sh, rx.py, fr.py, ni.py, capraw.py) and, for RA ceilings, the w14a84 `llc-patch/build.sh`
  private llc (rebuilt here in about a minute from `~/.cache/pumpfun-reconstruction/llvm-dbg/build`).
