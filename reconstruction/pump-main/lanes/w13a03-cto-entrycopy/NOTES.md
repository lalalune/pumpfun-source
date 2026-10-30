# w13a03-cto-entrycopy: entry copy of `new` in admin_cto::execute (0x22a10)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 3912c47ac (0.48772), 085e5dffb (0.48922), 43946852e (0.49071 / 3,313 slots).
Ledger: approach `entrycopy`, keys `0x22a10-w13-<main7>-entrycopy-*-v1`.
Trial sources are the edit lists in `~/.cache/pumpfun-reconstruction/lanes/w13a03-cto-entrycopy/e/*.py`
(exact `(old,new)` substitutions on main's admin_cto.rs; `g8.py`, `r1.py`, `s1.py` are the useful ones).

## What the original does (orig 0x22ee8..0x22fe0, after the CtoState stores)

`new` (Option<Pubkey>, passed by pointer in `[r5-0xff8]`) is copied in SROA pieces: tag -> spill, `[1,8)` -> 7 B
at T 0x658, `[8,16)` -> spill, `[16,24)` -> r9, `[24,33)` -> 9 B at T 0x668; then the sharing key temp (T 0x470)
and a holder_key copy (T 0x518) are made, then the mayhem test. The 7/9 B pieces are read once, in the shared
non-holder arm (orig 0x24268..0x242a0), into the sharing_update payload (P1 at T 0x538/0x548); the sharing tag
lives in the spill slot that held new's tag (`[r10-0x8f8]`, set to 2 for None).

So the sharing_update payload is read from a copy of `new`, not from the `new` argument.

## Mechanism found (source)

A **referenced copy of `new` at function scope, next to a function-scope `CtoState`**, read only by the
shared non-holder arm's sharing_update:

```rust
let st=CtoState{..};            // moved out of the (holder,cashback,..)={..} block
let args=&(new,);               // or &(fee,new) / &Some(new) / &(holder,new): same bytes
let (holder,..,skip)={ ..; validate(&st,holder,fee,new,..)?; .. else{target=st.creator;(Some(args.0),false,true)} ..};
```

- The reference keeps the copy out of MIR CopyProp/SROA (the same tuple inside the block, or a plain
  `let new2=new`, is forwarded: w12 a1c/a1h, y1 shadow-let). The copy is placed where the original makes it.
- First arg spills move to the original's: r4 `[r10-0x928]` and r2 `[r10-0x938]` (main: 0x8f8 / 0x908).
- Hoisting `CtoState` alone (g0) is byte-different but worse (0.47274 at 27,400 on 085e5df); the copy is what helps.
- If validate also reads `new` from the copy (g1/j2), +232 B: 0.50529 at 27,664 (085e5df).
- Still missing: the original loads the pieces at entry; ours loads them lazily in the arm (the `new` argument
  is `noalias readonly`, so the loads sink). Writing `new` (`mut new` + `take()`) keeps the tag/[8]/[16] loads
  at entry but forwards the 7/9 B pieces and costs ratio (n1k2: 0.47394 at the pinned size).

| trial (main) | form | bytes | ratio |
| --- | --- | ---: | ---: |
| main 43946852e | | 27,400 | 0.49071 |
| m8 = g8 (4394685) | hoisted st, then `let args=&(new,)`, sharing `Some(args.0)` | 27,416 | 0.49296 |
| r1 (4394685) | hoisted st, `let args=&(new,)` **before** the CtoState literal | 27,424 | **0.50397** |
| p2 (4394685) | m8 + event fields from curve/local (`m_ev_hrc_cbl`) | 27,432 | 0.50180 |
| p3 (4394685) | m8 + `m_ev_hr_curve` | 27,408 | 0.49334 |
| g1 (085e5df) | hoisted st, `&(fee,new)` read by validate and sharing | 27,664 | 0.50529 |

All need size compensation to 27,400; catalog size knobs are chaotic on these frames (v_ik_split, val_sh_borrow
collapse the ratio). w13a10-cto-pfclimb pairs `x_g8` with its gene library.

## Rejected (this lane)

`mut new`+`take()` in the sharing arm (e1/n1) or at the validate call (t2/n2); shadow `let mut new=new`+take
(t3); validate by-value holder_key with those (e2/t5); args aggregate before the block on current main (a1:
forwarded, a2: exact 0x655/0x658 pieces but 0.39345/+312); outlining (296 in holder arm, keys by value, o0:
26,960 B, pf 0.631) plus the copy read by validate (o1/o2: ratio 0.364/0.228).
