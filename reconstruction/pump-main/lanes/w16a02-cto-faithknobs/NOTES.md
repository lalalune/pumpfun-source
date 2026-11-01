# w16a02-cto-faithknobs: faithful size knobs for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 9bd38c7 (admin_cto source unchanged since 86e2a6b/9120883): 0.67376, M 2,249, 3,124 slots. Main moved to
1f4e396 during the lane (#3859, w16a07's A6 + ev6: 0.67436, M 2,251, 3,141 slots); the branch is merged up to it.
Ledger approach `faithknob`, keys `0x22a10-w16-<main7>-faithknob-<name>-v1` (main7 = 9bd38c7, then 1f4e396).

**Result: notes and tools, no landing of my own.** The exhaustive splice screen of every cached source capture
(section 5) ranks **w15a30 `ev:6012345789abc` + w16a07 `m_A6`** first. I built it as `H_ev6_A6` (27,400 B, M 2,251,
0.67436). It is exactly w16a07's PR #3859, found independently, so I left the landing to that lane (it landed as
7e5ba44a7). Nothing in the library improves on that composite, and the one remaining -8 B polarity fix (sh_iflet) has
a +8 B pay band on the new main only in the event's error paths (section 6), where no ordinary spelling adds code.

Every number comes from the raw-IR capture + opt + llc oracle (`tools/scr.py` = w15a03's capraw + rx with this lane's
paths; `main` reproduces `$BASE`, `eq_main`). M is the masked difflib match count: ratio = 2M / (6676 + (bytes -
27400)/8), so +1 M = +0.0003.

## 1. The original's call order differs from main's at exactly four places

`data/orig_calls.txt` / `data/main_calls.txt` list all 157 calls of both windows with the callee symbol (the original's
targets resolve through main's symbol table, since every other window is byte-identical at the same address). The callee
sequences are identical except at:

| call # | original | main | already priced by |
| --- | --- | --- | --- |
| 0-3 (entry) | `find_program_address` (holder PDA), memcmp, memcmp, data_is_empty | memcmp, memcmp, data_is_empty, `find_program_address` | PDA-first (w15a03 m_pdaf, w15a35) |
| 20-29 (validate errors) | error blocks in another order | | 307/312 `to_string` outlining |
| **53/54 (sweep token arm)** | **`token_raw_amount`, then `token_frozen`** (orig 0x20c8 -> 0x296f0, 0x2110 -> 0x29518) | `token_frozen`, then `token_raw_amount` | a1 (w14a70) |
| 73/74 (pool gate) | memcmp (`owner==AMM`), then `data_is_empty` | `data_is_empty`, then memcmp | owner-first gate (w14a73 opswap-L761, w15a04 n1po) |

So a1 (`let amount=token_raw_amount(..)?;let frozen=token_frozen(..)?;`) is the original's order, not a guess.

`tools/polmap.py <fn.bin>`: of main's 15 `jeq rX,K,+1; ja` pairs, exactly two are a single `jne` in the original:
line 660's `token_raw_amount(..)?` (orig 0x2528, fixed by w16a07's A6 tuple match, now on main) and the sharing-CPI `?`
(orig 0x4aa0, fixed by sh_iflet). The others match the original's two-instruction form, or are the inlined `to_string`
`fmt::Error` test at 0x1288 that the original outlines (the 307/312 residual). There is no third -8 B polarity site.

## 2. sh_iflet (= mil) needs +8 B only for jump displacements

`tools/whyins.py <fn.bin> <off>` lists the original tokens that one junk slot gains or loses. On sh_iflet (27,392 B,
M 2,244) a junk slot anywhere in candidate 0x2130-0x2508 restores seven jump displacements that cross the sharing CPI
(orig 0x708 `ja +0xa06`, 0x1fb0 `ja +0xdb`, 0x2140 `jeq r1,0,+0x7a5`, 0x2538 `jeq r1,0,-0xb1`, 0x62d8, 0x6870,
0x6a30) and breaks one (0x1f60 `jne r0,0,+0x5a`, or 0x2230 `ja +0x344` for later slots): M 2,250. At 0x54b8 it also
fixes 0x53d8/0x54e8 and breaks nothing (M 2,251); that is the original's `mov64 r9,r1` after the `Clock::get()?`
`Error::from` (the Err payload goes through r1 into r9, the original's error-return register; ours loads into r8).

The original's extra instructions in the sweep-head band are register-allocation artefacts (w15a23 5.1). New
sweep-head spellings on sh_iflet (`data/spec_s1.txt`), none of which adds a surviving instruction there:

| variant (on sh_iflet) | bytes | M | note |
| --- | ---: | ---: | --- |
| d_ctxkey `with_pubkeys((ctx.accounts.holder_creator_vault.key(),dest))` | 27,392 | 2,244 | byte-identical to sh_iflet |
| d_errinto `Error::from(error!(..)).with_pubkeys(..)` | 27,392 | 2,244 | identical |
| d_infokey `(*a.holder_creator_vault.as_ref().key,dest)` | 27,392 | 2,244 | identical |
| ap_info `token_frozen(&a.coin_creator_vault_ata)` | 27,392 | 2,244 | identical |
| v_direct `let vsigner:[..;1]=[vaultseeds];` | 27,392 | 2,240 | reorders the seed-array stores |
| d_full `let dest=find_program_address(..);` + `dest.0` | 27,384 | 1,923 | collapses |
| d_progid `&crate::id()` | 27,488 | 2,240 | +96 B in SH: the id is built on the stack; the original passes `lddw r4,&ID` |
| d_defer (on main) `let dest;let d=..;dest=d.0;` (the holder_key idiom) | 27,400 | 1,356 | collapses |
| v_olddefer (on main) `let old;old=a.current_creator.key();` | 27,400 | 2,241 | |

## 3. t1 (a1 + separate `?`) is the original's token-arm skeleton; with sh_iflet it lands at exactly 27,400 B

| variant | genes | bytes | M | rfj true LCS | jumps bad / aligned |
| --- | --- | ---: | ---: | ---: | --- |
| main 9bd38c7 | | 27,400 | 2,249 | 3,002 | 113 / 261 |
| a1 | a1 | 27,376 | 2,242 | | |
| T1 | a1 + tsplit | 27,408 | 2,243 | 3,006 | 119 / 263 |
| **ST1** | **sh_iflet + a1 + tsplit** | **27,400** | **2,245** | **3,006** | 118 / 264 |
| tsplit / S_tsplit | split `?` on frozen-first main | 27,456 / 27,448 | 2,135 | | collapses (as w14a70 f1) |
| ev6+A6+T1+sh_iflet (splice) | | 27,400 | 2,247 | | on the new main |

tsplit = `create_idempotent(..)?;crate::collect_v2::transfer_vault_tokens(..)?;return Ok(amount);` instead of
`.and_then(|()|transfer_vault_tokens(..))?`. ST1 carries three changes toward the original (call order, the
create/transfer `jne r7,2` Err tests, the post-sharing-CPI `jne r7,2`) and is +4 rfj over main, but M -4.
`tools/jdiff.py main ST1`: ST1 fixes 4 displacements main has wrong (orig 0x810, 0x8f0, 0x6238, 0x6260) and breaks 6
(0x708, 0x1f60, 0x2140, 0x62d8, 0x6ae0, 0x6b00); the rest is the token-arm r6/r8 naming that w14a70 bounded at +5.

## 4. Splice oracle v2: exact composites of local changes without builds

`tools/splice.py base var...` applies each variant's instruction-level diff (difflib on jump-normalised tokens) to main
and re-resolves every jump: base jumps keep their target unless a variant retargets that same jump (for example into
code it inserted at a block head), in which case the variant's target wins. Validation:
- every single capture reproduces itself byte for byte (200/200 w15a03 captures and all of this lane's);
- **88 of 89** w15a03 multi-gene builds are byte-identical to the splice of their single-gene captures; the other has
  the same M;
- the ev6 + A6 build (`H_ev6_A6`, = main 1f4e396) is byte-identical to the splice of w15a30's and w16a07's singles;
- ST1 = splice(T1, sh_iflet) byte for byte.

It costs about 0.5 s per composite and no build slot. Main's raw-IR capture is byte-identical to w15a03 `n0`, w15a13
`M0`, w15a16 `n0`, w15a17 `main` and others, so every cached source capture on 86e2a6b/9120883/1cc4879/9bd38c7 can be
combined; captures built on 1f4e396 combine too (their diff simply includes A6 and ev6). v1 missed retargeted jumps
and could read 1 M low; the pair screens below are v2 (`pairs4`, `lead_HevA6b`); `triples3`, `lead_T1`, `lead_ST1` are
v1 and may be 1 M low.

## 5. Exhaustive splice screens of the cached library

`tools/catalog.py` collects the unique source captures on the current admin_cto source (w15a01, a03, a13, a16, a30,
a32, a35; w16a02, a04, a05, a07), re-derives bytes and M from each fn.bin (rows whose rx dir was overwritten are
dropped) and tags them (section 7). Screens exclude devol and O/tf_g3 bases as the brief asks.
`data/splice_screens.json` has the top rows of each screen.

| screen | composites | best |
| --- | ---: | --- |
| every zero-sum pair of the 187 captures with M >= 2,236, on main 9bd38c7 (v2) | 542 | **2,251: ev_6012345789abc + m_A6** (= #3859); 2,250: ev6 + sh_iflet, ev6 + m_A1; 2,249: ev6 + cu_match, ev6 + b6xl |
| zero-sum triples, items with dM >= -8 and 8 <= abs(dB) <= 128 (v1) | 1,251 | 2,249 |
| ev6+A6 (H_ev6_A6) + every 0 B capture and every zero-sum pair (v2) | 2,170 | 2,251 (neutral 0 B knobs: hk_copy, hkl3, q5, the CtoState df_/dl_ orders, lfb5) |
| ev6+A6 + sh_iflet + each +8 B capture | | 2,250 (cu_unwrapcur, wl_writ_eq); p_colnat 2,249; m_T2 2,247 |
| T1 + every -8 B capture (v1) | 26 | 2,246 |
| ST1 + every 0 B capture and zero-sum pair (v1) | 557 | 2,245 |

ev6 (`AdminCtoEvent{is_holder_reward:..` first) is the only +8 B repay that pairs above main: it loads the curve's
holder flag before the Clock call (+8 B in the post-CPI region, cand 0x4e10), which moves the code between a -8 B
change in the sweep head and the event back by 8 B and fixes three jump displacements (orig 0x24b0, 0x2628, 0x4e70).
Double moves (`ev:6701234589abc`, `ev:7601234589abc`) collapse with A6 (+48 B, M 1,983) and with A6 + sh_iflet
(+40 B, M 1,987).

## 6. sh_iflet on the new main: the pay band is the event's error paths

`insmapn.py` on the splice ev6+A6+sh_iflet (27,392 B, M 2,245), maximum M after one junk 8 B slot, by region:

| cand region (ev6+A6+sh_iflet) | max M | what is there |
| --- | ---: | --- |
| 0x0-0x1a88 entry + validate | 2,246 | |
| 0x1a88-0x26b8 sweep head | 2,251 | (the old main's band; A6 removed 8 B inside it) |
| 0x3c40-0x5448 sharing CPI, pool, event | 2,251 | |
| **0x5448-0x5578** | **2,252 (36 slots), 2,253 at 0x54b8** | `Clock::get()?` `Error::from`, the `emit_cpi!` `invoke_signed` `Error::from`, the event-authority `AccountInfo` drop glue on that Err path |
| 0x5578-end | 2,249 | |

So on 1f4e396 the remaining polarity fix pays only with +8 B of real code in those error paths, ideally the original's
`mov64 r9,r1` at 0x54b8 (+2). Tried: execute's `emit_cpi!(e)` hand-expanded in the wallet's form (`event_infos`
binding with and without the deferred `event_signers`, E1/E3/E4) is byte-identical to the macro (+ sh_iflet: 27,392,
M 2,245). `let clock=Clock::get()?` locals were priced on older mains at about -10 M (w14a73 ev_ts_clockvar).

## 7. The size-knob catalog (`data/sizeknobs-w16.json`)

Same shape as `$SWARM/w11/sizeknobs-cto.json` (`knobs[].results.main9bd38c7`), one row per unique capture with M >=
2,150, with:
- bytes, delta_bytes, M, dM, ratio, identical_to_base;
- `by_region` / `changes`: where the byte delta lands, by call-anchor alignment against main (`tools/region.py`;
  regions E entry < 0x3a8, V validate+tree < 0x1a88, SH sweep head < 0x26b8, TC TCF clones/call/Rent < 0x3c40, SC
  sharing-CPI build < 0x4a28, PC post-CPI pool/event < 0x5490, ER error blocks < 0x5990, NA sweep native arm < 0x5bc0,
  WA wallet and the sweep token-arm CPI < 0x6a68, TL tail);
- the w16-strategy `decomp.py --drift` metrics (`tools/drift.py`): jumps_bad / jumps_aligned (main 113 / 261),
  rfj true LCS (main 3,002) and region drift medians (main entry -22, validate tail -21, sharing CPI -12, event -6);
- `composites[]`: the splice-priced sets with predicted M >= 2,246.

Single-region knobs with M >= 2,236 on main 9bd38c7, by region (bytes, M):
- E: crl3 (+72, 2,250).
- V: g1 (+120, 2,251), vol334b_I6n / dv_I6n (+8, 2,249), t1n (-24, 2,248), vol334_back (-8, 2,248).
- SH: wl_writ_eq (+8, 2,245), m_A6 (-8, 2,244), c2_L_share_none_first (-8, 2,244).
- SC: cu_unwrapcur / e0u (+8, 2,245), sh_iflet (-8, 2,244), cu_match (-8, 2,243).
- PC: **ev_6012345789abc (+8, 2,247)**, ev_7012345689abc (+8, 2,245).
- WA: p_colnat / m_T2 (+8, 2,246). TL: K_g_w_clock_local (+16, 2,246). TC: b6xl (-8, 2,243).

Sibling-idiom knobs built here (`tools/genes_fk.py` k_*; on 9bd38c7 unless marked):

| knob | sibling idiom | bytes | M | note |
| --- | --- | ---: | ---: | --- |
| k_req284 `require!(!st.mayhem,..)` | create_v2 / admin_cto_pool `require!` | 27,400 | 2,249 | byte-identical |
| k_req289 `if st.holder_reward{require!(hopt==Some(true),..)}` | admin_cto_pool `if flag{require!}` | 27,400 | 2,249 | neutral, not identical |
| k_req298 `require!(new.is_none(),..)` | `require!` | 27,400 | 2,249 | neutral, not identical |
| k_req296 `if holder&&!st.holder_reward{require!(st.holder_enabled,..)}` | create_v2 nesting | 27,432 | 1,423 | collapses |
| k_hkproj `let holder_key=find_program_address(..).0` (and `let (holder_key,_)=`) | create_v2 `.0`, admin_cto_pool `let (x,_)=` | 27,400 | 1,869 | the deferred-init `holder_key` is load-bearing |
| k_hkpid `&crate::id()` for the holder PDA | | 27,512 | 2,171 | |
| k_rkn307 `require_keys_neq!(t,Pubkey::default(),..)` (on 1f4e396) | create_v2 | 27,400 | 2,251 | byte-identical to main |

## Tools (`tools/`, experiment only)

- `scr.py`, `genes_fk.py`, `capraw.py`, `rx.py`, `oracle.py`, `bdis.py`, `insmapn.py` (w15a03's, re-pointed).
- `splice.py` (the oracle), `pairsearch.py`, `leadsearch.py`, `newscan.py`, `ontop.py`, `kscan.py`: splice screens.
- `catalog.py`, `mkcatalog.py`: the catalog builder and its sizeknobs-format export.
- `region.py`, `drift.py`, `jdiff.py`, `whyins.py`, `polmap.py`: where bytes land, drift metrics, jump displacement
  diffs, junk-slot gain/loss lists, `?` polarity sites.
- `lq.py`: an in-memory ledger grep (the shared ledger is 32 MB; `log_attempt.py search` takes minutes).

## Next ideas

1. sh_iflet on 1f4e396 pays with +8 B of real code in cand 0x5448-0x5578 (the event's `Clock::get()?` / `emit_cpi`
   Err paths and the event-authority drop glue). The original's code there differs only by `mov64 r9,r1` (Err payload
   via r1 into r9, the original's error-return register). A lane that moves the function's error-return payload
   register from r8 to r9 would likely make that instruction appear.
2. Use `tools/splice.py` before building: every cached capture on the current source composes exactly with every other
   (88/89 built composites byte-identical). Rebuild `catalog.py` over new lanes' res files to extend the library.
3. ST1 (sh_iflet + a1 + tsplit) is the most faithful token-arm skeleton at 27,400 B (+4 rfj, M -4 on 9bd38c7); its
   residual is the token-arm r6/r8 naming (w14a70 bound +5).
