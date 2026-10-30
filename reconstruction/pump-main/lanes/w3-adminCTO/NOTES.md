# Lane w3-adminCTO: 0x22a10 `admin_cto::execute` (stack-slot / frame-layout reconstruction)

Base: origin/main 6654999 (1022 normalized / 276 raw). Target on base: 27,160 B, ratio 0.19314, calls 154/3 (= orig).

## Method

- `scripts/irtrial.sh <n>`: capture rustc IR of the current source (scratch copy), run the SDK `llc` with
  `-print-after=prologepilog -filter-print-funcs=<execute>` and print every live frame object with its IR alloca
  name, size, r10 offset and whether rustc/inliner gave it lifetime markers (`frame.py`, `allocas.py`).
- `scripts/offmap.py orig.txt cand.txt pei.txt allocas.txt`: aligns the two instruction streams with r10 offsets
  abstracted and maps each candidate frame object to the original offset it lines up with.
- Frame objects are laid out in alloca (fi#) order: inlined callees' allocas first (last inlined first), then the
  outer function's. StackColoring merges only allocas that have lifetime markers and disjoint live ranges.

## Findings

1. The abstracted-offset ratio (all r10 offsets masked) is 0.4228 for t19/e1/e2: the frame-offset mismatch is
   about half of the remaining difflib gap.
2. `let cpi_accounts = Struct{..}; CpiContext::new(prog, cpi_accounts)` loses StorageLive/StorageDead in MIR
   (CopyProp merges the move temporary into the let local), so the outer function's 336-byte AdminCtoPool
   alloca has no lifetime markers and is never merged. In the original it shares the 384-byte slot at r10-0x450.
   Writing the accounts struct as a call-argument temporary restores the markers (e1, -336 B of frame).
3. Same mechanism inside the wallet closure: the let-bound CollectCoinCreatorFee accounts/program get
   inliner-added markers spanning the whole closure, which blocked the 288-byte `Create` accounts of
   create_idempotent from sharing the 384 slot (e2). After e2 the top frame object is the vault-seeds
   `[&[u8];3]` class, as in the original (orig at r10-0x38, ours r10-0x30: orig's top class is 8 B larger).
4. Original layout after e2 (orig -> ours): top 0x38/0x30, CpiContext 664 0x2d0/0x2c8, 384 slot 0x450/0x448,
   wallet emit_cpi seeds 0x470/0x470, invoke result 0x488/0x498, ... val 0x651/0x611, holder_key 0x6a0/0x690,
   mint 0x6c0/0x6b0, ISel temporaries 32x16 B from 0x6d0 (ours 33), first spill 0x8d8/0x8c8.
   Remaining differences: the original has Pubkey SROA pieces split at offsets 7/15/23 (Pubkey at offset 1 of
   an Option-like aggregate: 7-byte + 9-byte allocas at 0x658/0x668 and 0x538/0x548) where ours splits `target`
   at 5/13/21 (Result<(bool,bool,Pubkey)>) and keeps `sharing_update.sroa.8` (32) and `old` (32); ours keeps the
   wallet emit_cpi bump (1 B) and signer slice (16 B) unmerged, the original merges them into those pieces.

## Trials

| trial | mechanism | bytes | ratio | first spill | normalized/raw |
|---|---|---:|---:|---:|---|
| main | origin/main 6654999 | 27,160 | 0.1931 | | 1022/276 |
| t19 | prior lane t19: both events emitted by reference | 26,616 | 0.2009 | 0xb38 | 1022/276 |
| e1 | AdminCtoPool accounts as call-argument temporary | 26,616 | 0.1951 | 0x9e8 | 1022/276 |
| e2 | + CollectCoinCreatorFee program/accounts as call-argument temporaries | 26,616 | **0.2286** | 0x8c8 (orig 0x8d8) | 1022/276 |

Ledger: t19 b482bc3a, e1 9647310e, e2 1d8fd823.

## Round 2 trials (CtoState line; judged by exact ratio plus the offset-abstracted ratio `segab.py`)

| trial | mechanism | bytes | ratio | note |
|---|---|---:|---:|---|
| e5 | prior t18 CtoState + nested `fn validate` | 26,936 | 0.153 | abstracted 0.537 (code much closer; frame off) |
| e6 | CtoState scoped in a block ending before prepare | 27,000 | 0.157 | st merges into top slot; 109 spills = orig |
| e9 | no entry `old` copy; vault seeds/event use `a.current_creator.key()` | 27,024 | 0.154 | |
| e11 | holder/non-holder split with `holder==Some(true)` | 27,312 | 0.334 | frame r10-0x0..0x4ff now equal to orig |
| e13 | validate takes `(holder,fee,new)` tuple | 27,488 | 0.347 | |
| **e17** | validate returns `Result<Pubkey>` (target); holder/cashback outside | **27,416** | **0.3633** | 7 B/9 B Pubkey pieces like orig (Pubkey at offset 1 of Result<Pubkey>) |
| e8/e10 | split with `unwrap_or(false)` | 27,024 | 0.142 | extra None branch; 326 cold |
| e12,e14,e16,e18,e19 | target from current_creator after block; global_quote in literal; validate returns sharing_update; block as closure; deferred init | | 0.25-0.34 | not kept |
| e15 | sweep flag `matches!(sharing_update,Some(None))` | 27,552 | 0.255 | rejected |
| e20/e21 | sweep `?` as `match` (both arm orders) | | 0.3633 | byte-identical |

The prior lane rejected the CtoState and holder-split mechanisms on the difflib ratio, which is dominated by r10 offsets. `segab.py` (offsets and jumps masked) showed that both are closer to the original.

Inline hot/cold: in the original, to_string is inlined at 284, 289, 298, 306, 296 and 326, and not at 307, 312, 330, 334 or 338 (`rem.sh` gives the remark sets).

IR oracle (`irexp.py`; llc reproduces e17 exactly): giving the sweep's 648 dest-memcmp branch a mild continue-favoring weight (3:2 or 5:3) moves 719/648/660 to the original's offsets (0x21d8/0x2388/0x2588) and places the 5 KB transfer_creator_fees clone block before the pool CPI, as in the original. The ratio goes to 0.3765. The source mechanism that produces this probability is still open. 1:1 and 4:3 do not reproduce the layout.

Remaining frame residuals: the wallet emit_cpi signer slice `_109.i` (16 B) is unmerged; the original merges it into a 24 B outer object at 0x680. The original has validate-region Result<Pubkey> pieces at 0x538-0x580, and its outer pieces sit at 0x658/0x668. Ours has the block-tuple copies `sharing_update2.sroa.3`/`target1` (no lifetime markers). There are 33 ISel 16 B temporaries against the original's 32.
