# w14a86-cto-t1vaultname: t1 token-arm naming probes + gene screen (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a70-cto-a1reread (#3402) and w14a79-cto-splitartifact (#3403). Ledger approach `t1vaultname`, keys
`0x22a10-w14-<main7>-t1vaultname-*`. Main moved twice during the lane: 0d04cf4 (0.66507) -> 95a64ba (#3409, 0.66986)
-> ecea702 (#3430, 0.67076). Oracle numbers come from the raw-IR capture + opt + llc oracle (`capvar.sh` / `rx.py`, w14a70/w14a79 tools);
`m0` reproduced main exactly (`eq_main`) on each base. M = matched masked tokens (`mm.py`).

## Result: landable gain, admin_cto 0.67076 / 3,123 -> 0.67226 / 3,123 at 27,400 B (M 2,239 -> 2,244)

measure.sh on ecea702: 1034/1034 normalized and raw, zero losses, swap_hop 1.0, differential 363 cases / 0 mismatches,
unstripped sha256 `c3ea5d9310d855ee`.

Change (three genes, line count unchanged). **None of them is t1.** They came out of the t1 gene screen, and they score
higher without t1:
- `nf`: the event's `new_creator_fee_bps` reads a local `nf=a.bonding_curve.creator_fee_bps` taken before `pool_updated`
  (w14a64 gene `g_ev_nf_let`, +16 B, M +1 on main ecea702, +3 on t1).
- `rP`: pool_authority clone `rent_epoch:x.rent_epoch` (drops the re-read, -8 B).
- `sm`: `if let Some(val)=sharing_update{..}` for the sharing CPI instead of `match ..{Some(val)=>{..}None=>{}}` (-8 B).

| base ecea702 (M 2,239) | bytes | M | ratio |
| --- | ---: | ---: | ---: |
| **nf + rP + sm** | 27,400 | **2,244** | **0.67226** |
| nf + aP (drop `amm_present` let) | 27,400 | 2,243 | 0.67196 |
| nf alone | 27,416 | 2,240 | 0.67086 |
| t1 + nf + aP + rP / + sm | 27,400 | 2,240 | 0.67106 |
| t1 + nf + rP + sm + rL / cm, t1 + nf + aP + rL / cm | 27,400 | 2,239 | 0.67076 |
| t1 alone (a1 + separate `?`) | 27,408 | 2,233 | 0.66886 |

On 95a64ba (main M 2,236) t1+nB+nf+aP measured 0.67106 at 27,400 with zero losses, but ecea702 landed nB, and on ecea702 the same
genes without t1 are 4 M better.

## 1. t1 on 0d04cf4: the angle's IR probes (`spillprobe.py`, `llcx.py`, `fmr.py` L0/L1/L2)

| probe on t1+nB | bytes | L1 | L2 | token-arm naming |
| --- | ---: | ---: | ---: | --- |
| t1+nB | 27,400 | 0.70072 | 0.78520 | field ptr r6, amount r8 (main L1 0.70132 / L2 0.78310) |
| sp328 (`&holder_creator_vault` spilled at def) | 27,384 | 0.68265 | 0.78184 | unchanged |
| spb (bump `%ctx.val57`) | 27,424 | 0.67884 | 0.77886 | unchanged |
| sp2 (both) | 27,432 | 0.66647 | 0.77784 | unchanged |
| sp3 (+ native `%324`) | 27,448 | 0.66327 | 0.76025 | arm reshaped (wrong value: ours already spills the i32 memcmp result at -2328) |
| P1 / P1b / P1c / P1d: accounts `%_269` re-loaded from ctx in the token arm (create, frozen, raw_amount and transfer blocks) | 27,408-27,472 | 0.52-0.697 | | unchanged |
| H1: separate `accounts+72` GEP for the transfer arg | 27,360 | 0.68416 | 0.7678 | amount r9, field load folds |

Freeing r6 does not hand it to the amount. The field pointer `%245` (`COPY %0; ADD_ri 72`) still takes r6.

## 2. Why the field pointer takes r6: greedy queue order (debug llc `-debug-only=regalloc` on t1+nB)

- `%245` has hints `$r3` (the transfer arg COPY, a physreg hint, which gives priority bit 30) and `$r8` (the COPY from `%0`).
  It is dequeued while accounts `%0` still holds r8 over the whole arm. Both hints interfere, so it takes the first free
  CSR, r6.
- Later the entry-region value `%387` ([640r,12816r)) evicts `%0` from r8 (cascade 34), and `%0` is region-split. The amount
  `%247` (no hint, weight 1.3e-07) is dequeued last and inherits the freed r8.
- The original's naming (pointer r8 in place, amount r6) needs `%245` to be dequeued after `%0`'s split, or the amount to be
  dequeued first. Neither depends on `%121` occupying r6. This is the same queue-order mechanism as w14a82 (#3409).
- Register-only misses (`regmiss.py`, ecea702-era t1 vs main): orig [0x2000,0x2200) 3 -> 5 and [0x5e00,0x6400) 10 -> 14, while
  L2-matched rises 51 -> 53 and 163 -> 169. t1's skeleton gain is spent on naming.

## 3. Screens

| screen | base | runs | best at 27,400 |
| --- | --- | ---: | --- |
| t1 + C0 (wlB + smB + rP) | 0d04cf4 | 2 | M 2,218 @27,384 (C0 alone 2,224): t1 costs 6 M on C0 |
| t1+nB x w14a70 gene/knob library (g_/k_/c_) | 95a64ba | 130 | none above t1+nB (2,235). nf +3 M @+16 B |
| t1+nB+nf x {aP, rP, rL, cm, sm} pairs | 95a64ba | 7 | nf+aP / nf+rP+sm 2,240 (0.67106) |
| holder-vault path spellings on t1 (648 binding `hv`, `&a.holder_creator_vault`, `*key` deref, `.clone()` / `ctx.accounts` authority, `amount!=0`) | 95a64ba | 6 | byte-identical to t1+nB or worse (`hv` binding 0.39623, deref 0.66697) |
| ecea702 recombination (t1 and non-t1) | ecea702 | 11 | **nf+rP+sm 0.67226** |

## Next ideas
- t1 stays a skeleton lead (+8 L2-aligned tokens in the token arm) whose gain is lost to naming. Only a change in greedy queue
  order fixes that: the amount needs a physreg hint, or `%0` must be split before `%245` is dequeued. No source form found.
- nf + aP is 1 M behind nf + rP + sm at the same size. Try aP on top of the landed state with an 8-16 B faithful fill.
