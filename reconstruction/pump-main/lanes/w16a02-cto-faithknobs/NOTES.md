# w16a02-cto-faithknobs: faithful size knobs for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 9bd38c7 (admin_cto source unchanged since 86e2a6b/9120883): 0.67376, M 2,249, 3,124 slots. Main was not
rebuilt (`$BASE`). Ledger approach `faithknob`, keys `0x22a10-w16-9bd38c7-faithknob-<name>-v1`.

**Status: notes (in progress).** No composite above main yet. Every number below comes from the raw-IR capture + opt +
llc oracle (`tools/scr.py` = w15a03's capraw + rx with this lane's paths). `main` reproduces `$BASE` exactly (`eq_main`).
M is the masked difflib match count, so ratio = 2M / (6676 + (bytes - 27400)/8).

## 1. The original's call order differs from main's at exactly four places

`orig_calls.txt` / `main_calls.txt` (this lane's `$OUT`) list all 157 calls of both windows with the callee symbol
(original targets resolved through main's unstripped symbol table: every other window is byte-identical at the same
address). The callee sequence is identical except at:

| call # | original | main | lead that already prices it |
| --- | --- | --- | --- |
| 0-3 (entry) | `find_program_address` (holder PDA), memcmp, memcmp, data_is_empty | memcmp, memcmp, data_is_empty, `find_program_address` | PDA-first (w15a03 m_pdaf, w15a35 pdafceiling) |
| 20-29 (validate errors) | error blocks in another order | | the 307/312 `to_string` outline residual |
| **53/54 (sweep token arm)** | **`token_raw_amount` then `token_frozen`** (orig 0x20c8 -> 0x296f0, 0x2110 -> 0x29518) | `token_frozen` then `token_raw_amount` | a1 (w14a70) |
| 73/74 (pool gate) | memcmp (`owner==AMM`) then `data_is_empty` | `data_is_empty` then memcmp | owner-first gate (w14a73 opswap-L761, w15a04 n1po) |

So `a1` (`let amount=token_raw_amount(..)?;let frozen=token_frozen(..)?;`) is the original's order, not a guess. It is
0x20c8 `ldxdw r2,[r8+0x48]; call token_raw_amount`, then `add64 r8,0x48; ldxdw r6,[r10-0x2c8]` (amount in r6).

## 2. sh_iflet (= mil) needs +8 B only for jump displacements

`tools/whyins.py <fn.bin> <off>` lists the original tokens gained and lost by one junk slot. On sh_iflet (27,392 B,
M 2,244) a junk slot anywhere in candidate 0x2130-0x2508 restores **seven jump displacements that cross the sharing CPI**
(orig 0x708 `ja +0xa06`, 0x1fb0 `ja +0xdb`, 0x2140 `jeq r1,0,+0x7a5`, 0x2538 `jeq r1,0,-0xb1`, 0x62d8, 0x6870, 0x6a30)
and breaks one (0x1f60 `jne r0,0,+0x5a`, or 0x2230 `ja +0x344` further in), so M 2,250 = main + 1. At 0x54b8 it also fixes
0x53d8/0x54e8 and loses nothing (M 2,251), which is the original's `mov64 r9,r1` after the Rent `Error::from`.

The extra original instructions in that band are register-allocation artefacts (w15a23 5.1). New sweep-head spellings
on sh_iflet (this lane, `data/spec_s1.txt`):

| variant (on sh_iflet) | bytes | M | note |
| --- | ---: | ---: | --- |
| d_ctxkey `with_pubkeys((ctx.accounts.holder_creator_vault.key(),dest))` | 27,392 | 2,244 | byte-identical to sh_iflet |
| d_errinto `Error::from(error!(..)).with_pubkeys(..)` | 27,392 | 2,244 | identical |
| d_infokey `(*a.holder_creator_vault.as_ref().key,dest)` | 27,392 | 2,244 | identical |
| ap_info `token_frozen(&a.coin_creator_vault_ata)` | 27,392 | 2,244 | identical |
| v_direct `let vsigner:[..;1]=[vaultseeds];` | 27,392 | 2,240 | reorders the seed-array stores |
| d_full `let dest=find_program_address(..);` + `dest.0` | 27,384 | 1,923 | collapses |
| d_progid `&crate::id()` (PDA program id by value) | 27,488 | 2,240 | +96 B in SH: the id is materialised on the stack; the original passes `lddw r4,&ID` |
| a1 | 27,368 | 2,243 | a1 alone on main: 27,376, M 2,242 |

None adds one surviving instruction in the band; with w15a03's 13 and w15a23's rows the local spellings there are exhausted.

## 3. t1 (a1 + separate `?`) is the original's token-arm skeleton; with sh_iflet it lands at exactly 27,400 B

| variant | genes | bytes | M | rfj true LCS | jumps bad / aligned |
| --- | --- | ---: | ---: | ---: | --- |
| main | | 27,400 | 2,249 | 3,002 | 113 / 261 |
| a1 | a1 | 27,376 | 2,242 | | |
| T1 | a1 + tsplit | 27,408 | 2,243 | 3,006 | 119 / 263 |
| **ST1** | **sh_iflet + a1 + tsplit** | **27,400** | **2,245** | **3,006** | 118 / 264 |
| tsplit / S_tsplit | split `?` on frozen-first main | 27,456 / 27,448 | 2,135 | | collapses (as w14a70 f1) |

tsplit = `create_idempotent(..)?;crate::collect_v2::transfer_vault_tokens(..)?;return Ok(amount);` instead of
`.and_then(|()|transfer_vault_tokens(..))?`. ST1 combines three changes toward the original (call order, the
create/transfer `jne r7,2` Err tests, the post-sharing-CPI `jne r7,2`), is +4 rfj over main, and sits at the pinned size,
but it is M -4. `tools/jdiff.py main ST1`: ST1 fixes 4 jump displacements main has wrong (orig 0x810, 0x8f0, 0x6238,
0x6260) and breaks 6 (0x708, 0x1f60, 0x2140, 0x62d8, 0x6ae0, 0x6b00); the rest is the token-arm r6/r8 naming that w14a70
bounded at +5 (`rename2.py`).

## 4. Splice oracle: composites without builds

`tools/splice.py base var...` applies each variant's instruction-level diff (difflib on jump-normalised tokens) to main
and re-resolves every jump displacement. It reproduces sh_iflet, a1 and the S_a1 build byte for byte. On the 54
conflict-free pairs of w15a03's cached singles that were also built as pairs, **43 splices are byte-identical to the
built pair and 52 have the same M** (the other two: +1 and -6). So it predicts composites of local changes exactly and
costs about 0.5 s per composite with no build slot.

Main's own capture is byte-identical to w15a03 `n0`, w15a13 `M0`, w15a16 `n0` and others, so every cached source capture
on 86e2a6b/9120883/1cc4879/9bd38c7 is valid for the current source.

Exhaustive splice screens (`tools/pairsearch.py`, `tools/leadsearch.py`, 196 catalogued captures with M >= 2,200):

| screen | composites | best M | best |
| --- | ---: | ---: | --- |
| every zero-sum pair | 584 | 2,248 | p_colnat / cu_unwrapcur / e0u + sh_iflet (w15a03's -1) |
| every zero-sum triple of items with dM >= -8, 8 <= abs(dB) <= 128 | 417 | 2,246 | p_colnat + cu_unwrapcur + amp_inline |
| T1 + every -8 B item | 26 | 2,246 | T1 + c2_L_share_none_first; T1 + sh_iflet = 2,245 = the ST1 build |
| ST1 + every 0 B item and zero-sum pair | 557 | 2,245 | ST1 + hk_copy |

No composite of the cached library beats main.

## Tools (`tools/`, experiment only)

- `scr.py`, `genes_fk.py`, `capraw.py`, `rx.py`, `oracle.py`, `bdis.py`, `insmapn.py` (w15a03, re-pointed).
- `whyins.py`: which original tokens one junk slot gains or loses.
- `region.py`: where a variant's byte delta lands (call-anchor alignment against main; regions E/V/SH/TC/SC/PC/ER/NA/WA/TL).
- `drift.py`: the w16-strategy `decomp.py --drift` metrics on a fn.bin (rfj true LCS, jump-displacement mismatches,
  region drift).
- `jdiff.py`: jumps whose displacement matches in A but not in B.
- `splice.py`, `pairsearch.py`, `leadsearch.py`: the splice oracle and its exhaustive screens.
- `catalog.py`: the size-knob catalog builder (section 5).
- `lq.py`: a fast in-memory ledger grep (the ledger has 6,000+ rows and `log_attempt.py search` takes minutes).
