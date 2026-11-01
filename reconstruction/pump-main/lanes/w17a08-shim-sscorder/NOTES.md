# w17a08-shim-sscorder: spill-colour order on main with weight shims (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Wave 17 SHIM track.
Base: main bf01b5fd9 (programs/ = d20fb326e): 0.68005, 3,170 slots, M 2,270, Pump Main 1034/1034.
Ledger: approach `sscorder`, keys `0x22a10-w17-bf01b5f-sscorder-<item>-v1`.

## Result

| build | admin_cto ratio | M | slots | bytes | normalized / raw | losses | differential |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| main bf01b5fd9 | 0.68005 | 2,270 | 3,170 | 27,400 | 1034 / 1034 | - | - |
| **sco1** (#4011, landed d5751b26e) | **0.68065** | **2,272** | 3,170 | 27,400 | 1034 / 1034 | none | 388 cases, 0 mismatches |

measure.sh unstripped sha `748fbfba8140c508`; calls stay 154 / 3. Landed with `land.py 4011 --allow-forcing`
(forcing delta 2, merge commit d5751b26e). The source capture is byte-identical to the IR oracle
cell (w17a03's L5713 lead, re-measured here on the current main).

### The shim (line 749, no line added)

The sharing CPI's `sharing_config: a.sharing_config.to_account_info()` becomes a manual `AccountInfo` literal whose
`owner` field is written LAST and does the next field's work first:

```
sharing_config:{let x:&AccountInfo=a.sharing_config.as_ref();AccountInfo{key:..,lamports:x.lamports.clone(),data:x.data.clone(),
  rent_epoch:..,is_signer:..,is_writable:..,executable:..,
  owner:unsafe{let r=ptr::read(&a.pump_fees_event_authority.data);if Rc::strong_count(&r)==0{unreachable_unchecked()}
               let o=read_volatile(&x.owner);let raw=Rc::into_raw(r);Rc::increment_strong_count(raw);ead=Rc::from_raw(raw);o}}}
event_authority:AccountInfo{data:ead, ..}        // `let ead;` deferred next to `let pf`
```

So the event_authority `data` Rc increment (count load, +1, store, trap) runs inside the sharing_config literal, and the
volatile `owner` read sits between its count load and its store: w17a03's L5713 window (Rc-window recipe). Plain removal
of the window (natural field order, `sco2`) collapses (M 2,201 @27,424): the owner must follow rent_epoch and the flags.

**Why it pays (SSC view):** the move changes no code outside the window; it re-spills the sharing_config clone's
`executable` byte one block later (weight 5.080780e-3 → 5.080777e-3), so it leaves the {owner, rent_epoch, is_signer,
is_writable} tie group and is coloured after 233/242/280 (k53 → k56; three intervals move up one colour). That is the
original's order for that group (votes below).

Peel target: an ordinary spelling that puts the sharing_config owner read inside the event_authority data clone.

## Tools (all under `tools/`; no build slot except `cap.sh`)

- `llcp.sh`: the private llc (w15a24 RAPRIO + w15a32 `SSC_WSET` + w16a20 `SSC_SEGB` hooks, Release+Asserts) with the
  fastbuild flags. **zsh trap:** `$PL $A file` with `A="-O3 -relocation-model=pic ..."` does NOT word-split in zsh, so llc
  gets one bogus option and silently drops `-mattr=+store-imm,+jmp-ext`; logs then come from the wrong configuration.
- `sscsim.py`: exact StackSlotColoring simulator. It parses the `-debug-only=stack-slot-coloring` intervals (segments,
  weights, processing order), re-colours any processing order (first-fit over colours in opening order, colour k at
  `-2264-8k`), and relabels the `-no-stack-slot-sharing` object (one offset per interval). BPF has no
  `isLoadFromStackSlot`, so RemoveDeadStores is a no-op and colouring changes only spill offsets. On main it reproduces the
  real bytes exactly (`eq_main: true`) and matches the private llc on random order moves; 0.02-0.03 s per evaluation.
- `ordor.py`: the same through the real llc, with every interval's weight set (`SSC_WSET` full spec).
- `votes.py`: aligns the no-share code with the original (spill offsets blanked) and lists, per interval, the original's
  colour at aligned accesses (`data/votes-bf01b5f.txt`; 293 aligned spill accesses, 171 already on the original colour).
- `movemap.py`: every single "move interval s to rank j" scored with sscsim; `sa.py`: annealing over orders.
- `dvec.py` / `combo.py`: branch-weight edits on execute's post-opt IR (every conditional br; trap-like edges p in
  {2e-6..5e-4}, others x(1±eps)) scored with the real llc, with RA-identity check and weight deltas; singles, pairs, triples.
- `mvload.py`: move one load (plus its GEP) to each later position, plain or volatile (needs an instnamer'd module).
- `cap.sh` + `apply.py`: crate copy + exact edits → capraw → preslim → fx (w17a06's exact slim oracle).

## Findings on main bf01b5f (M 2,270)

1. **Colour-order ceiling on fixed code is small.** Mperm 2,305 / Mhc 2,308, but the best single order move gives 2,274
   (+4) and annealing over orders (4 chains) also stops at 2,274. Most of Mperm is not a legal first-fit colouring.
2. **The +4 single moves** (`movemap`): 341 (sharing_config owner) below its tie group {342-345} (+4); 250 between 244 and
   245 (+4, impossible: 244/245 are an exact tie in one block); 315/316/258/281/187 raised above the head (+4, needs
   +0.05 weight); 186/187 swap (+4, the S3 flag slot, owned elsewhere); 319, 278, 282, 303 (+3).
3. **Traps cannot reorder clone-run spills.** In both clone runs every spill is stored in the clone's block and reloaded in
   the CPI argument block, and block frequency only falls along the chain of Rc traps. So a later-stored interval is always
   lighter, ties within one block stay tied (FI order = RA spill order), and no trap probability inverts them.
4. **Branch-weight combos are exhausted on this main** (`combo.py`, ledger `brcombo`): 928 singles (92 change the
   colouring at 27,400, none gains), 1,770 pairs of the 60 best, 900 triples: best 2,270 / 2,270 / 2,269.
5. **Load moves:** of 2,604 sharing-run moves only the L5713 window gains (+2, volatile only); every other position of the
   sharing_config field loads re-allocates registers (2,168-2,253 off-size).

## Round 2 on the landed main d5751b26e (M 2,272, 0.68065)

All screens re-run on a fresh capture of d5751b2 (`fx/m3`, simulator `eq_main: true`):

| screen | cells | best at 27,400 | note |
| --- | ---: | --- | --- |
| branch weights (`combo.py`) | 928 singles, 1,770 pairs | 2,272 (= main) | 92 singles re-colour, none gains |
| Rc-window volatile moves (`winmove.py`, L5713 generalised) | 1,420 | 2,272 | 58 count windows, every earlier load of the function |
| sharing_config field loads moved again (`mvload.py`) | 266 | 2,272 | rent_epoch / flags around the landed window |
| post-opt volatile re-read at a later use (`rr.py`, lever b) | 272 | 2,273 @27,392 (rr197@232) | with rr157@169 (+8 B): **2,273 @27,400 (+1)** |
| pre-opt single shim edits (w17a06 `gen.py`/`screen.py`: vload fld, reread, bw, swbw, fence) | 801 | **2,273** (`bf:wallet:31259`) | the do_coin=false fence on the native path (w17a06's bf:wallet:30918) |
| single colour-order moves (`movemap.py`) | 13.5k+ | 2,276 (+4) | same families as before: flag 186 (S3 slot, excluded), head raises, the 244/245 exact tie |

Source attempts for the +1 cells:
- rr197@232 + rr157@169 as `read_volatile` of the curve Box pointer (mayhem byte) and of the sharing_config
  AccountInfo pointer (owner test): 2,074 @27,280 (pair) and 2,052 @27,424 (mayhem only). A pre-opt volatile load of an
  accounts pointer stops GVN from merging the later reloads (MemorySSA treats it as a def), so the post-opt cell is not a
  source cell. Only the pre-opt screen predicts source behaviour.
- `bf:wallet:31259`: `do_coin` as `if coin_present{..}else{false}` is byte-identical to main (f0). A fence under
  `if collection_native` in the else arm (f1) lands in both threaded copies plus a dead test: 2,258 @27,408.

## Round 3 on main 8330455eb (w17a15 passthrough landed; M 2,278, 0.68244): two marked fences, +4 M

Screens on a fresh capture (`m5`): branch weights (928 singles + pairs + triples) and Rc-window moves (1,396) give
nothing; the post-opt re-read screen gives rr1316@1353 + rr197@232 = 2,281 @27,400 (the wallet's `collected` re-read
from the collect result buffer; a `ManuallyDrop` + `ptr::read` source form collapses to 1,881). The pre-opt single-edit
beam (w17a06 `gen.py`/`screen.py`, 807 cells) has one big fence cell, `bf:sweep:33476` (+4 M at -16 B), and a repay
screen (88 combos) pairs it with `bf:wallet:31884` (+0 M, +16 B) for **2,282 @27,400**.

| build | admin_cto ratio | M | slots | bytes | normalized / raw | losses | differential |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| main 8330455eb | 0.68244 | 2,278 | 3,293 | 27,400 | 1034 / 1034 | - | - |
| **swl1** (this branch) | **0.68364** | **2,282** | 3,348 | 27,400 | 1034 / 1034 | none | 388 cases, 0 mismatches |

measure.sh unstripped sha `d9ae67ece207fe2c`; calls 154 / 3. The source captures equal the oracle cells
(sw1 alone: 2,282 @27,384; both: 2,282 @27,400).

The two shims (no line added, both `core::hint::black_box(())`, a zero-size compiler memory barrier that emits no
instruction):
- line 664, sweep native arm: the tail `(..transfer_native(..)}else{Ok(())}).map(|()|amount)` becomes
  `{let r=(..).map(|()|amount);black_box(());r}`: a fence at the merge where the sweep's Result is written (`bb95`);
- line 579, wallet: `collect_coin_creator_fee(..)?;black_box(());`: a fence on the AMM collect CPI's Ok continuation
  (`bb103`), the +16 B repay.

Peel targets: an ordinary spelling that keeps the sweep's native result merge as its own block (the fence stops the
memory ops of the two arms from being merged/scheduled across it), and one that gives the wallet's +16 B back.

**Update: not landed.** `land.py 4021 --allow-forcing` merged main ac37d7415 (w17a18-cto-stitch17-2, 0.68424) into the
branch and measured 0.68214 (worse), so it rejected the PR. On ac37d74 neither fence cell gains any more: the pre-opt
beam (807 single cells: fence, bw, swbw, reread, vload fld) and 297 pairs of its 25 code-changing cells top out at main's
M 2,284. The fences are removed from this branch again (programs/ = origin/main); the cells are recorded in the ledger
(`0x22a10-w17-8330455-sscorder-swl1-v1`, `0x22a10-w17-ac37d74-sscorder-beam6-v1`).

Lesson for shim lanes: on this fast-moving main a fence or weight cell is worth re-screening after every landing, and a
lane should land within minutes of measuring; the same two fences went from +4 M to -21 M in one landing.
