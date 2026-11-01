# w16a02-cto-faithknobs: faithful size knobs for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 9bd38c7 (admin_cto source unchanged since 86e2a6b/9120883): 0.67376, M 2,249, 3,124 slots. Main was not
rebuilt (`$BASE`). Ledger approach `faithknob`, keys `0x22a10-w16-9bd38c7-faithknob-<name>-v1`.

**Result: notes and tools, no landing of my own.** The exhaustive splice screen of every cached source capture
(section 5) ranks **w15a30 `ev:6012345789abc` + w16a07 `m_A6`** first. I built it here as `H_ev6_A6` (27,400 B,
**M 2,251, 0.67436**), which is exactly w16a07's PR #3859 (found independently, measured there with measure.sh and the
differential), so I left the landing to that lane. Nothing in the library improves on that composite (section 5.3).

Every number comes from the raw-IR capture + opt + llc oracle (`tools/scr.py` = w15a03's capraw + rx with this lane's
paths; `main` reproduces `$BASE` exactly, `eq_main`). M is the masked difflib match count: ratio = 2M / (6676 + (bytes -
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
line 660's `token_raw_amount(..)?` (orig 0x2528, fixed by w16a07's A6 tuple match) and the sharing-CPI `?` (orig
0x4aa0, fixed by sh_iflet). The others match the original's two-instruction form, or are the inlined `to_string`
`fmt::Error` test at 0x1288 that the original outlines (the 307/312 residual). There is no third -8 B polarity site; on
ev6+A6 only the sharing-CPI one is left.

## 2. sh_iflet (= mil) needs +8 B only for jump displacements

`tools/whyins.py <fn.bin> <off>` lists the original tokens that one junk slot gains or loses. On sh_iflet (27,392 B,
M 2,244) a junk slot anywhere in candidate 0x2130-0x2508 restores seven jump displacements that cross the sharing CPI
(orig 0x708 `ja +0xa06`, 0x1fb0 `ja +0xdb`, 0x2140 `jeq r1,0,+0x7a5`, 0x2538 `jeq r1,0,-0xb1`, 0x62d8, 0x6870,
0x6a30) and breaks one (0x1f60 `jne r0,0,+0x5a`, or 0x2230 `ja +0x344` for later slots): M 2,250. At 0x54b8 it also
fixes 0x53d8/0x54e8 and breaks nothing (M 2,251); that is the original's `mov64 r9,r1` after the Rent `Error::from`.

The original's extra instructions in that band are register-allocation artefacts (w15a23 5.1). New sweep-head spellings
on sh_iflet (`data/spec_s1.txt`), none of which adds a surviving instruction in the band:

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
| main | | 27,400 | 2,249 | 3,002 | 113 / 261 |
| a1 | a1 | 27,376 | 2,242 | | |
| T1 | a1 + tsplit | 27,408 | 2,243 | 3,006 | 119 / 263 |
| **ST1** | **sh_iflet + a1 + tsplit** | **27,400** | **2,245** | **3,006** | 118 / 264 |
| tsplit / S_tsplit | split `?` on frozen-first main | 27,456 / 27,448 | 2,135 | | collapses (as w14a70 f1) |

tsplit = `create_idempotent(..)?;crate::collect_v2::transfer_vault_tokens(..)?;return Ok(amount);` instead of
`.and_then(|()|transfer_vault_tokens(..))?`. ST1 carries three changes toward the original (call order, the
create/transfer `jne r7,2` Err tests, the post-sharing-CPI `jne r7,2`) and is +4 rfj over main, but M -4.
`tools/jdiff.py main ST1`: ST1 fixes 4 displacements main has wrong (orig 0x810, 0x8f0, 0x6238, 0x6260) and breaks 6
(0x708, 0x1f60, 0x2140, 0x62d8, 0x6ae0, 0x6b00); the rest is the token-arm r6/r8 naming that w14a70 bounded at +5.
w16a07's `m_t1A6` (T1 + A6) is the same family at 27,400 B, M 2,246.

## 4. Splice oracle: exact composites of local changes without builds

`tools/splice.py base var...` applies each variant's instruction-level diff (difflib on jump-normalised tokens) to main
and re-resolves every jump: base jumps keep their target unless a variant retargets that same jump (for example into
code it inserted at a block head), in which case the variant's target wins. Validation:
- every single capture reproduces itself byte for byte (200/200 w15a03 captures and all of this lane's);
- **88 of 89** w15a03 multi-gene builds are byte-identical to the splice of their single-gene captures; the other has
  the same M;
- the ev6 + A6 build (`H_ev6_A6`) is byte-identical to the splice of w15a30's and w16a07's single captures;
- ST1 = splice(T1, sh_iflet) byte for byte.

It costs about 0.5 s per composite and no build slot. Main's raw-IR capture is byte-identical to w15a03 `n0`, w15a13
`M0`, w15a16 `n0`, w15a17 `main` and others, so every cached source capture on 86e2a6b/9120883/1cc4879/9bd38c7 can be
combined. (The first version, v1, missed retargeted jumps and could read 1 M low; every screen below was rerun with v2.)

## 5. Exhaustive splice screens of the cached library

`tools/catalog.py` collects 615 unique source captures on the current admin_cto source (w15a01, a03, a13, a16, a30,
a32, a35; w16a02, a04, a05, a07), re-derives bytes and M from each fn.bin (rows whose rx dir was overwritten are
dropped) and tags them (section 6). Screens exclude devol and O/tf_g3 bases as the brief asks.

### 5.1 Zero-sum pairs and triples on main

| screen | composites | best |
| --- | ---: | --- |
| every zero-sum pair of the 187 captures with M >= 2,236 (`tools/pairsearch.py`) | 542 | **2,251: ev_6012345789abc + m_A6** (= PR #3859); 2,250: ev6 + sh_iflet, ev6 + m_A1; 2,249: ev6 + cu_match, ev6 + b6xl |
| zero-sum triples, items with dM >= -8 and 8 <= abs(dB) <= 128 | 1,251 | 2,249 |

ev6 (`AdminCtoEvent{is_holder_reward:..` first, w15a30) is the only +8 B repay that pairs above main: it loads the
curve's holder flag before the Clock call (+8 B in the post-CPI region), which shifts the code between a -8 B change
in the sweep head and the event back by 8 B and fixes three jump displacements (orig 0x24b0, 0x2628, 0x4e70).

### 5.2 Built confirmations

| capture | genes | bytes | M | ratio |
| --- | --- | ---: | ---: | ---: |
| H_ev6_A6 | ev6 + A6 | 27,400 | **2,251** | **0.67436** (oracle; w16a07 measured 0.67436 / 3,141 slots / 0 losses / differential ok) |
| H_A6 | A6 | 27,392 | 2,244 | 0.67236 |

### 5.3 On top of ev6 + A6 (the next main)

| screen | composites | best |
| --- | ---: | --- |
| H_ev6_A6 + every 0 B capture and every zero-sum pair (`tools/leadsearch.py`) | see SUMMARY | 2,251 (0 B knobs that keep it, e.g. hk_copy, q5, k_req289, k_req298) |
| + sh_iflet + one +8 B capture | | 2,250 (cu_unwrapcur, wl_writ_eq) |
| + T1 + sh_iflet | | 2,247 |
| + t1n + crl3 | 27,448 | 2,251 (needs a neutral -48 B) |

So ev6 + A6 is a local maximum of the cached library; a gain on top of it needs a new knob.

## 6. The size-knob catalog (`data/sizeknobs-w16.json`)

Same shape as `$SWARM/w11/sizeknobs-cto.json` (`knobs[].results.main9bd38c7`), one row per unique capture, with:
- bytes, delta_bytes, M, dM, ratio, identical_to_base;
- `by_region` / `changes`: where the byte delta lands, by call-anchor alignment against main (`tools/region.py`;
  regions E entry < 0x3a8, V validate+tree < 0x1a88, SH sweep head < 0x26b8, TC TCF clones/call/Rent < 0x3c40, SC
  sharing-CPI build < 0x4a28, PC post-CPI pool/event < 0x5490, ER error blocks < 0x5990, NA sweep native arm < 0x5bc0,
  WA wallet and the sweep token-arm CPI < 0x6a68, TL tail);
- the w16-strategy `decomp.py --drift` metrics (`tools/drift.py`): jumps_bad / jumps_aligned (main 113 / 261),
  rfj true LCS (main 3,002) and the region drift medians (main entry -22, validate tail -21, sharing CPI -12, event -6);
- `composites[]`: the splice-priced zero-sum sets with predicted M >= 2,246.

Single-region knobs with M >= 2,236, by region (bytes, M):
- E: crl3 (+72, 2,250).
- V: g1 (+120, 2,251), vol334b_I6n / dv_I6n (+8, 2,249), t1n (-24, 2,248), vol334_back (-8, 2,248).
- SH: wl_writ_eq (+8, 2,245), m_A6 (-8, 2,244), c2_L_share_none_first (-8, 2,244).
- SC: cu_unwrapcur / e0u (+8, 2,245), sh_iflet (-8, 2,244), cu_match (-8, 2,243).
- PC: **ev_6012345789abc (+8, 2,247)**, ev_7012345689abc (+8, 2,245).
- WA: p_colnat / m_T2 (+8, 2,246). TL: K_g_w_clock_local (+16, 2,246). TC: b6xl (-8, 2,243).

Sibling-idiom knobs built here (`tools/genes_fk.py` k_*, `data/spec_k.txt`): see the table in SUMMARY.json. So far:
`require!(!st.mayhem,..)` (k_req284) is byte-identical to main; `if st.holder_reward{require!(..)}` (k_req289) and
`require!(new.is_none(),..)` (k_req298) are 0 B and M-neutral but not identical (free partners); `let holder_key=
find_program_address(..).0` (k_hkproj, also the `let (x,_)=` form) collapses to M 1,869 at 0 B, so the deferred-init
`let holder_key; .. holder_key=hk.0;` is load-bearing; `&crate::id()` for the holder PDA is +112 B, M 2,171;
`if holder&&!st.holder_reward{require!(st.holder_enabled,..)}` collapses (+32 B, M 1,423).

## Tools (`tools/`, experiment only)

- `scr.py`, `genes_fk.py`, `capraw.py`, `rx.py`, `oracle.py`, `bdis.py`, `insmapn.py` (w15a03's, re-pointed).
- `splice.py` (the oracle), `pairsearch.py`, `leadsearch.py`, `newscan.py`, `ontop.py`: splice screens.
- `catalog.py`, `mkcatalog.py`: the catalog builder and its sizeknobs-format export.
- `region.py`, `drift.py`, `jdiff.py`, `whyins.py`: where bytes land, drift metrics, jump displacement diffs, junk-slot
  gain/loss lists.
- `lq.py`: an in-memory ledger grep (the shared ledger is 32 MB; `log_attempt.py search` takes minutes).
