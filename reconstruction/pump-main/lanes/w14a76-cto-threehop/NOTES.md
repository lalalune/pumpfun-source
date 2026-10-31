# w14a76-cto-threehop: the three-hop target flow threads as the original does, but costs 0.1 to 0.4 (notes only)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
This lane continues w14a67-cto-h7src (#3384, next idea 1) and w14a66-cto-feeedge (#3386, NOTES section 2).

- Bases: main 39eb377 (0.66477 / 3,230), then 0d04cf4 (0.66507 / 3,228) after #3393.
- Ledger: approach `threehop`, keys `0x22a10-w14-{39eb377,0d04cf4}-threehop-*` (about 90 rows).
- **Result: no landable change.** The best zero-loss measurement is still main.

The angle was to rebuild validate → execute as the original's three hops, without the volatile `holder_key` load:
1. an entry copy of `new`;
2. a per-exit write of the target in each validate arm;
3. a late copy into execute's target after the tree.

The aim was to bring bb76's JumpThreading duplication cost to 6 or less, so that both fee-None exits get threaded and the
fee-Some exit keeps its own block, as at orig 0x24210.

## 1. JT cost of the validate join, and what removes it (`tools/jtc.py`, `tools/th.py`)

`jtc.py raw.ll` runs `opt -O3 -print-after=jump-threading` on execute. For every join that ends in `br i1 %shared`, it
prints the `getJumpThreadDuplicationCost` estimate: an intrinsic counts 2, any other instruction counts 1, and phis are free.

| IR state | join cost (JT2) | what JT threads | ratio @ bytes | fm / sk |
| --- | ---: | --- | --- | --- |
| main 39eb377 | 42 | nothing | 0.66477 @27,400 | 0.71031 / 0.79569 |
| `ir3b`: validate arms write straight into the sret (`th.val`), nothing else | 34 | nothing | 0.66477 @27,400 (token-equal) | = |
| `ir4_arms_0`: execute `?` chain (`_49`→`_410`→`_48`→`val`→`target`) collapsed, copy from `_49` in the tree arms | 10 | nothing | 0.55153 @27,400 | 0.65309 / 0.77951 |
| `ir4_arms_1` = `th.val` + collapse | 2 | non-holder fee-None exit only | 0.26937 @27,568 | 0.43333 / 0.56981 |
| `t1_a`: t1 source (section 2) + collapse | 8 | holder fee-None exit only | 0.56207 @27,480 | 0.67454 / 0.77505 |
| **`t1_va`: t1 + `th.val` + collapse** | **0 (threaded away)** | **both fee-None exits; fee-Some keeps the join** | 0.26995 @27,632 | 0.43758 / 0.57062 |
| same on 0d04cf4 (`n_va`) | 0 | both | 0.26309 @27,632 | 0.43371 / 0.57062 |

To get the cost to 6 or less, two things must happen together:
- validate's own `target` alloca has to go, with the arms writing into the sret. That form alone is token-neutral.
- execute's `?`/tuple hop chain has to be collapsed into one copy, placed in the tree arms.

Those two account for all of the cost; the lifetime markers in the join are minor.

The holder exit also needs a second change. JT reaches it only when LVI knows the tree's test on that edge, and validate's holder
fee-None arm is guarded by `new.tag == 0`, not by `holder`. So the tree must test `new`, as in t1.

`t1_va` is the original's validate-exit CFG: both fee-None exits have their own shared test and per-exit target copy, the
fee-Some exit keeps the join, and there is no volatile load. **Its price is -0.40.**

## 2. Why the faithful CFG loses: JT also duplicates the non-shared arm, and block placement swaps two regions

Once the join is free to duplicate, JT also threads the non-holder exit through the non-shared tree arm (`bb21.thread`).
After that, MachineBlockPlacement stops placing the wallet error block (InvalidCreator `with_pubkeys`) before
`bb9.i` (the wallet/`token_frozen` region). It falls through into the sweep error join `bb56.i` instead, and pulls in the
whole post-sweep chain. `tools/mv.py` and `tools/bord.py` show the result: orig slots 1,878-2,608 (0x26740-0x27e90, from the
sharing-update copy of `target` onward) are placed before orig 1,043-1,878 (0x24ca8-0x26740). That swap is about 730
slots each way, and difflib loses all of it (`amap.py` chunks 18-24 drop to 0).

- `n_vpin`: the same IR, with 8 volatile loads in the non-shared arm head so that JT cannot duplicate it. The swap is gone
  (chunks 18-24 return to 84/22/24/98/84/88/92), but the non-holder exit is no longer threaded. Score: 0.35548 @27,464,
  sk 0.71125.
- Branch weights on the wallet `executable` branch (`bb7.i108`), at 1:2000, 2000:1 and 1:1, do not undo the swap
  (0.240-0.272).
- **Even before the swap**, t1_va's chunks 0-17 add up to 1,301 skeleton points against main's 1,380. Chunk 2 (validate)
  gains +24, but chunk 3 (the tree just after it) loses 24 and chunks 8-11 lose about 8 each. So a swap-free three-hop
  would still be below main on today's skeleton.

## 3. Source forms (raw-IR capture + oracle; `gen/`)

| form | base | ratio @ bytes | fm / sk | errseq |
| --- | --- | --- | --- | --- |
| main | 0d04cf4 | 0.66507 @27,400 | 0.71061 / 0.79509 | 330 338 334 410 |
| **t1**: execute tree `if shared{if new.is_none(){..}else{..}}` (holder ⇔ `new` None once validate succeeds) | 0d04cf4 | 0.66427 @27,440 | 0.70947 / **0.79599** | 330 338 334 410 |
| t1 | 39eb377 | 0.66397 @27,440 | 0.70918 / 0.79659 | = |
| t2 `args.0.is_none()` / t3 `let None=new` | 39eb377 | 0.66387 / 0.66397 @27,440-27,448 | | = |
| t1n/t2n/t3n (t1-t3 without the volatile) | 39eb377 | 0.65739-0.65749 @27,432-27,440 | | 330 338 410 334 |
| nv: the volatile removed, nothing else | 39eb377 | 0.65828 @27,392 | 0.70382 / 0.78861 | 330 338 410 334 |
| s1-s4: target chosen after the fee checks inside validate (`if let Some(t)=new{t}else{*holder_key}` etc.) | 39eb377 | 0.287-0.517 | | 284 moves |
| e1-e6: `validate -> Result<()>`, target chosen in execute (`if holder{holder_key}else{..}`, `new.unwrap_or(holder_key)`, ..) | 39eb377 | 0.319-0.325 @26,944-27,128 | ~0.52 / 0.70 | 330 338 334 284 |

- s1 makes SimplifyCFG sink both arm copies into one memcpy from a phi of source pointers (`holder_key.sink.i`), which is
  the opposite of the original's per-exit copies.
- In e1-e6, JT does thread (`bb77.thread`), but the whole frame moves and so does error 284.
- **t1 plus each of the 44 size knobs** that still apply (`sizeknobs-cto.json`, on 0d04cf4) gives at best 0.66427 @27,440.
  - No single knob lands on 27,400 with a gain. `cu_typed` reaches 27,400 at 0.65279.
  - `sh_accs_let` raises sk to 0.80563 but scores 0.62773 @27,416.
  - Knob pairs and triples that land t1 on 27,400 (0d04cf4):
    - `sh_prog_let+ev_hr_curve`: 0.65998, 3,195 slots, which is fewer slots than main's 3,228 but a lower ratio.
    - `s_dest_borrow+ev_mint_key+ev_newfee_unwrap`: 0.65159.
    - `s_dest_borrow+wl_ts_clockvar+ev_newfee_unwrap`: 0.65339.
    - `s_old_borrow+…`: 0.6417.
    - `g_s7_dborrow+…`: 0.65159.
- Other spellings of the t1 test all score 0.66417-0.66427 @27,440-27,448: t4 (Some-first `if new.is_some()`), t5 (`match new{None=>..,Some(_)=>..}`),
  t6 (`args.0.is_none()`) and t7 (`if let Some(_)=args.0`).
- An instruction diff shows that t1 changes no structure. Its +40 B are 5 register moves (`mov r3,r8`, `mov r7,r9`,
  `mov r4,r7`, ...) from a reshuffled register assignment around the tree test, and the sk gain is a side effect of that.

## 4. Mechanisms for other lanes

- The validate join's JT cost is set by execute's hop chain and validate's `target` alloca, not by lifetimes. Removing
  either one alone leaves 10 or more; removing both gives 0-2.
- LVI threads the holder fee-None exit only when the tree tests `new`'s tag, because validate's holder arm is guarded by
  `new.tag == 0`. Testing `holder` threads only the non-holder exit.
- The tree's test spelling (`new.is_none()` against `holder`) raises the skeleton score on its own (+0.0009 sk on 0d04cf4).
  It costs 40 B, and no knob in the catalog repays that.
- Threading the non-holder exit through the non-shared arm sets off a placement swap of the wallet and post-sweep
  regions. Any lane that makes the validate join cheap has to keep the non-shared arm from being duplicated, as `n_vpin`
  does, or price this swap in.

## Tools (experiment only; never source proposals)

- `tools/jtc.py`: JT cost of the shared-test joins after each JT pass.
- `tools/th.py`: generic three-hop IR edits. `val` makes validate arms write into the sret. `ex(mode)` collapses the
  `?` chain and adds arm copies; modes are `arms`, `all3`, `keeplt` and `pin`. Driven by `gen/g4.py` with `TH=val,arms`.
- `tools/amap.py`: per-1/32 skeleton match map against the original.
- `tools/mv.py`: where an orig slot range landed in a candidate.
- `tools/bord.py`: asm block order with slot positions (from `llc -filetype=asm`).
- `tools/rec.py`: ledger recorder.
- `rx.py`, `px.py`, `capvar.sh`, `capraw.py`, `batch.sh`, `fx.py`, `bw.py`, `eseq.py`: from w14a66/w14a54, repointed here.
