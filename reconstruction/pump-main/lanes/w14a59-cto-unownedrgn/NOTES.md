# w14a59-cto-unownedrgn: per-region miss tables and spelling screen for the unowned admin_cto regions

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 6330811 (0.65698, 3,193 slots), then **2e1379d (0.65728, 3,192 slots, 1034/1035)**.
Ledger approach `unownedrgn`, keys `0x22a10-w14-<sha7>-unownedrgn-<name>-v1` (67 rows).

**Result: no gain.** The unowned regions' statement shapes and error constructors are already the original's.
Their misses come from four mechanisms that other lanes have already mapped: the accounts+0x108 live range, swept/Err
payload register coalescing, the J2 tail-dup join, and block placement of the `?` pads. 55 source spellings in five
regions either fold to main's tokens or lose. The one statement-level divergence left is the token arm's call order:
the original calls `token_raw_amount` before `token_frozen`. Restoring that order costs 24 B and 5 M on main.

## Region map correction

w14a38's `regions.py` labels orig 0x2498-0x26e8 as "sweep 719 frozen/raw_amount". It is the **AMM arm**:
`token_frozen(coin_creator_vault_ata)`, then `token_raw_amount`, then the **660** `CtoSharedVaultFrozen` block
(`stw [r10-0x2b8],0x294`). The **719** token-arm head (the `token_raw_amount` and `token_frozen` calls on
`creator_vault_quote_token_account`, then the 719 require block with `stw 0x2cf`) is at orig **0x20b0-0x2238**, inside
the "sweep head" region 0x1d30-0x2300. The original lays out the token arm before the AMM arm, because the native
test `jeq native,0` (0x20a8) branches over both.

## Per-region miss tables (main 2e1379d)

`tools/sbs.py <so> 0 0x6b08` aligns the whole function with frame, registers and jumps masked. `tools/misstab.py`
then classifies each aligned original instruction:
- `frame`: only the r10 displacement differs.
- `reg`: only the registers differ.
- `jump`: only the jump offset differs.
- `mixed`: more than one of these differs.
- `extra`: the instruction is only in ours.
- `missing`: the instruction is only in the original.

| orig region | what | eq | frame | reg | jump | mixed | extra | missing |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0x1d30-0x2300 | sweep head + 719 token-arm head | 139 | 3 | 8 | 6 | 4 | 12 | 16 |
| 0x2300-0x2498 | 648 ConstraintSeeds with_pubkeys | 47 | 0 | 2 | 0 | 0 | 0 | 1 |
| 0x2498-0x26e8 | AMM arm + 660 | 54 | 0 | 2 | 8 | 2 | 2 | 4 |
| 0x3968-0x3c38 | TCF return, token `?` pad, Rent::get | 69 | 8 | 6 | 3 | 0 | 3 | 4 |
| 0x5570-0x5a80 | tail error blocks (Rc drops, 284, 556, unwrap_failed, From) | 122 | 7 | 14 | 3 | 1 | 4 | 4 |
| 0x5a80-0x5c38 | native ensure_rent_exempt / transfer_native join | 35 | 7 | 6 | 3 | 2 | 5 | 1 |

What each miss is (orig offset: original vs ours), by mechanism:

| mechanism | sites | owner / evidence |
| --- | --- | --- |
| sweep gate reads a spilled `skip` flag: `ldxdw r1,[-0x8e0]; jne r1,0,far`; ours keeps `!skip` in r9: `jne r9,0,+1; ja far` | 0x1d38-0x1d40 | w14a11 (skip gate dead), w14a46 (r9 occupant is the gate flag) |
| sharing tag reloaded into r6 at the gate (`ldxdw r6,[-0x8f8]`); ours keeps it in its slot | 0x1d30, 0x3c58 | w14a45 table |
| `&a.holder_creator_vault` (+0x108) spilled at its def to [-0x8e0]; ours keeps it in r6 and spills it mid-arm to [-0x9b8] | 0x1f38-0x1f48, 0x2130, 0x23d8-0x23e0 (648 key reload), 0x20b8, 0x5938, 0x5a78, 0x5ae8 | w14a45 (acc108): every forced spill or remat loses |
| bump spilled to [-0x910] after the dest compare, reloaded for `&[bump]`; ours keeps it in r9 | 0x1f70, 0x2060 | w14a45 b1/sb |
| swept/Err payload in r9 (one phi = return payload); ours uses r3 at the join and r8 at the return | 0x2148, 0x2220, 0x25f8, 0x3b98, 0x3c40, 0x5858/0x5870, 0x5950, 0x54d0-0x54e0 (`mov r9,r1`), 0x55a8, 0x5b18 | w14a06 swept coalescing, w14a33 section 5 |
| join test tail-duplicated into the 660 block (`ldxdw r1,[-0x950]; jne r7,2`); ours has J2 (`jne r7,2,+1; ja`) after transfer_native | 0x2608-0x2610, 0x5b10-0x5b28 | w14a33 / w14a51 (J2) |
| token-arm `?` Err pad (`ldxdw r9,[-0x2c8]; ja join`) placed after the TCF Err edge; ours places it after the 660 block | 0x3ba8-0x3bb0 | placement only; w14a36 chain scan: every such move is <= 0 |
| token arm: `token_raw_amount` first (amount in r6, `add64 r8,0x48` in place); main calls `token_frozen` first | 0x20c8-0x2160 | this lane, below |
| error-name String buffer [-0x488] vs ours [-0x470] | 0x5688, 0x57c0-0x57e0 | w14a57 frameremap |

None of the error constructors differ. The 648 `error!(ConstraintSeeds).with_pubkeys(..)`, the 660/719
`require!(..==0, CtoSharedVaultFrozen)`, the 284/556 `Err(error!(..))`, the `ProgramError` `From` for `Rent::get()?`,
and the `unwrap_failed` inside the inlined `to_string` all match the original except for the payload register and
frame slots listed above.

## Spelling screen (raw-IR capture + opt + llc oracle, `tools/capvar.sh` + `rx.py`; `m0` = main exactly)

M = matched masked tokens and jM = M with jump offsets also masked (`tools/mm.py`). Main 2e1379d: M 2194, jM 2227,
0.65728. Main 6330811: M 2193, jM 2225, 0.65698.

| family | spellings | result |
| --- | --- | --- |
| token arm, original call order: `let amount=token_raw_amount(..)?;let frozen=token_frozen(..)?;` (a1), with frozen inline in the `if` (a2), as a tuple (a3), `let frozen;` deferred (a4), `!=0 {return err!}` (a6), `&..` args (c1), `0==amount` (c3), `if !frozen{..}else{require}` (c4), `match frozen` (c5), `frozen&&amount!=0` (c6), `amount!=0` (c7), `if !frozen&&` (c10), `amount==0{}else{}` (c12), `frozen==true` (c13), rebinding (c14) | 15 | **all one token stream**: 0.65608 @ 27,376 (M 2189, jM 2224) on 2e1379d. At level 3 (frame+regs+jumps masked) it is +1 over main. The original's structure is there, but the amount gets r8 (`mov r6,r8; add64 r6,0x48`) where the original uses r6 and `add64 r8,0x48`. The tail segments 0x6000-0x6a28 lose 1-2 each from that naming and the -24 B shift. |
| token arm, other | a5 `let t=..as_ref()` 0.63779; a7 `require_eq!` 0.51947; a8/c11 `return Ok(..)` in the frozen arm 0.65518 @ 27,400 | lose |
| token arm, frozen-first control-flow (c4f, c5f, c6f, c12f) | 4 | token-identical to main; c11f (frozen-arm return) 0.62148 @ 27,464 |
| a1 + size repay (+8..+32 B knobs from w14a50 k1 that grow the function: ev_cb_local, clock_local, wl_ts_clockvar, cu_replace, ev_newfee_unwrap, ev_creator_first, t7_puswap, t4_nopargs, ev_mint_key) | 9 (+ 15 zero-size knobs) | best single 0.65478 @ 27,384 (6330811). Every size-adding knob loses 0.0007-0.006 against a1. The +24 B pairs at 27,400 on 2e1379d: ev_cb_local + clock_local or wl_ts_clockvar 0.65368 (q1/q2), cu_replace + either 0.65189 (q3/q4), ev_cb_local + ev_mint_key 0.64709 (q5). |
| 648 ConstraintSeeds: `require_keys_eq!` (h1), `.with_pubkeys((*key,..))` (h8), `Err(..)?` (h9), `let e=error!` (h10), `.into()` (h12), `.ne(&dest)` (h13) | 6 | token-identical to main |
| 648 other: `let hcv=key()` (h3) 0.37708; `!key().eq(&dest)` (h5) / `==dest{}else{}` (h14) 0.44468 @ 27,496; `Error::from(..).with_source` (h11) 0.5347 @ 27,112; local `keys_eq` (h16, sweep_fees sibling) 0.46552 @ 27,720 | 5 | lose |
| AMM arm 660: `if ..!=0{return err!}` (m3), `let r=..;require!` (m4), `<1` (m5), `&..` args (m6, m8), `if !empty{..}else{false}` (m9), `match empty` (m10) | 7 | token-identical to main |
| native test: `native_mint::id()` (n1), `.eq(&ID)` (n3) identical; `check_id` (n2) 0.64139 @ 27,368; `*to_account_info().key` (n4) 0.56768 | 4 | fold or lose |
| creator-vault PDA seeds: `.as_ref()` (p1) identical; `&holder_key.to_bytes()` (p2, p3) 0.6547 @ 27,464 | 3 | fold or lose |
| tail errors: `require!(!st.mayhem,..)` (t1), `err!` (t3) identical; 556 `require!(is_writable)` (t2) / `!is_writable` + `err!` (t4) 0.65678 @ 27,392 on 6330811 (main 2e1379d already has `!is_writable`, #3372); 719 `<1` (f1), `!=0 {return err!}` (f2) identical | 6 | fold |

Readings:
- The `require!`/`err!`/`error!` and comparison spellings fold before codegen, so error-construction idioms are no lever
  in these regions. Only call order (a1) and argument binding (a5, h3, p2, n2) change tokens, and those changes lose.
- a1 is the original's token-arm skeleton. It is worth +1 jump-masked token if its registers matched, but it is 24 B short.
  The gain #3358 got from frozen-first is register naming (the amount lands in r6) plus size, not structure. A
  landable a1 needs a +24 B repay that does not lose. No catalog knob does that. The best +24 B pair (q1) is 0.65368, 0.0036 below main.

## Tools (tools/)

- `sbs.py <so> lo hi`: side-by-side orig vs build listing, calls named, frame/regs/jumps-masked alignment.
- `osbs.py <so> <rx m.o|-> lo hi`: the same for a raw-IR oracle object (relocation-named calls), aligned over the whole function.
- `misstab.py <sbs listing> lo:hi:label ...`: the per-region eq/frame/reg/jump/mixed/extra/missing table above.
- `mm.py name...`: M and jM for `rx/<name>/fn.bin`.
- `runlist.sh <res> names...`: 2-worker capvar queue.
- `capvar.sh`, `rx.py`, `capraw.py`, `rec.py`: w14a38's oracle, re-pointed at this lane.
- `regions.py` / `splice.py` / `segdiff.py` (w14a38). `REGIONS-2e1379d.json` is the regenerated map.
- `e/*.py`: every spelling (EDITS lists for capvar). `results.jsonl`: every oracle row.
