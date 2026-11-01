# w17a08-shim-sscorder: spill-colour order on main with weight shims (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Wave 17 SHIM track.
Base: main bf01b5fd9 (programs/ = d20fb326e): 0.68005, 3,170 slots, M 2,270, Pump Main 1034/1034.
Ledger: approach `sscorder`, keys `0x22a10-w17-bf01b5f-sscorder-<item>-v1`.

## Result

| build | admin_cto ratio | M | slots | bytes | normalized / raw | losses | differential |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| main bf01b5fd9 | 0.68005 | 2,270 | 3,170 | 27,400 | 1034 / 1034 | - | - |
| **sco1** (this PR) | **0.68065** | **2,272** | 3,170 | 27,400 | 1034 / 1034 | none | 388 cases, 0 mismatches |

measure.sh unstripped sha `748fbfba8140c508`; calls stay 154 / 3. The source capture is byte-identical to the IR oracle
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
