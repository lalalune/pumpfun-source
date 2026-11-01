# w16a18-cto-devoltie: placeholder-free tie screen for admin_cto validate (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 599891304 (A6 + ev6 from #3859, then #3870), admin_cto 0.67436, M 2,251, 3,141 slots (oracle count 3,140),
two `read_volatile(holder_key)` placeholders in `validate` (lines 334 and 338). Ledger approach `devoltie`, keys
`0x22a10-w16-5998913-devoltie-<form>-v1` (28 capture rows plus the summary rows `vbinsmap`, `vbsplice-single8`,
`vbsplice-pairs`, `vbinsmatch`, `fh-inlinecliff`).

**Result: notes only, no landing. No placeholder-free form ties main.** The kill test holds: 168 splice-screened
composites and 25 captured spellings, none at M >= 2,251 at 27,400 B. Main stays the best zero-loss measurement
(0.67436 / 3,141 slots / 27,400 B), with both placeholders.

The owner's 2026-11-01 decision (BRIEF wave-16 notes) narrows the angle: only a spelling whose instructions follow the
original's data flow may replace a placeholder, never a dead store or other filler. Section 5 prices the one such
form, the fee-tag phi, as ordinary source.

M is the masked difflib match count against the original window, and ratio = 2M / (6676 + (bytes - 27400)/8).
Everything comes from the raw-IR oracle: `tools/scr.py`, w16a02's scr pointed at this lane, captures pre-opt IR with
`--emit=llvm-ir` only (w14a73 capraw2), then SDK `opt -O3` and `llc`. Composites come from w16a02's splice oracle
(`tools/vbscreen.py`).

## 1. vol334_back on the new main is still one token short

| form | bytes | M | dM | note |
| --- | ---: | ---: | ---: | --- |
| main 599891304 | 27,400 | 2,251 | 0 | `eq` the baseline `unstripped.so` (masked) |
| `vb` (line-334 `read_volatile` removed), splice of w15a03 `N_vol334_back` onto main1f | 27,392 | 2,250 | -1 | |
| `d_vb` (built capture) | 27,392 | 2,250 | -1 | byte-identical (masked) to the splice, so the splice oracle holds on 5998913 |
| `d_vb338` (both placeholders removed) | 27,384 | 2,228 | -23 | the 338 anchor is still worth 22 M (w15a29) |

`insmapn.py` on vb (`data/insmap_vb599.json`): one junk 8 B slot gives back M 2,251 at 518 positions, in cand
0x180-0x1a0, 0x6d8-0x8b8, 0x978-0xac0, 0xad8-0xeb8, 0xf10-0x14a8, 0x1588-0x17a0, 0x17b8-0x18d0, 0x19c0-0x1a90 and
0x1c78. No position gives 2,252. These are the same bands as w14a138 found on ebe5387/90300f9. A6 and ev6 did not move
validate.

## 2. Splice screens of the cached library (step 1-2 of the angle)

`tools/vbscreen.py` splices vb with w16a02's 623-capture catalog (`catalog4.json`; 9bd38c7-source captures as
`splice(main9bd, [main1f, vb, X...])`).

| screen | composites | best at 27,400 B |
| --- | ---: | --- |
| vb + every +8 B capture (`data/vbs_single8.jsonl`) | 46 | `N_I6ssn` M 2,248 / 3,141 slots (-3); then `L2_rr7O`, `cu_unwrapcur`, `m_T2`, `p_colnat` 2,247 |
| vb + every zero-sum-to-+8 pair, M >= 2,238, abs(dB) <= 160 (`data/vbs_pairs.jsonl`) | 350 (122 apply) | `N_I6n + c2_L_share_none_first` 2,246 (-5) |

The existing composites with a placeholder removed are no better. w16a02's `pairs*.jsonl` and `triples*.jsonl` that
contain `vol334_back` or `vol334b_I6n` reach 2,244-2,246 on 9bd38c7. `vol334b_I6n` (27,408, M 2,249 on 9bd38c7) has no
-8 B partner above 2,245. The library holds no +8 B knob that is M-neutral at +8 B. The only positive size leads
(crl3 +72 B +1, g1 +120 B +2) need -64 B or -112 B M-neutral partners, and the library has none.

## 3. Faithful-token ceiling: where one original instruction would pay

`tools/insmatch2.py` (w15a01 insmatch, whole window) inserts one ORIGINAL token from the facing LCS gap at each
candidate position of each gap of vb. Summaries are in `data/insmatch_vb599_*_top.json`.

| cand range | (pos, token) pairs | 2,250 | 2,251 (tie) | 2,252 (gain) |
| --- | ---: | ---: | ---: | ---: |
| 0x0-0x1a90 (entry + validate) | 2,226 | 26 | 1,246 | **933** |
| 0x1a90-0x6b00 (rest) | 2,913 | 78 | 7 | 0 |

The 2,252 cells sit in 37 runs (`cand_runs_with_2252`). Examples:
- entry 0x180-0x1a0: orig 0x258 `ldxdw r1,[r10-0x8e0]` (the sharing_config pointer reloaded for `data_is_empty`) or
  orig 0x268 `ldxdw r9,[r8+0x38]` (the bonding-curve pointer loaded right after `data_is_empty`, as in the
  original's PDA-first entry);
- validate 0x6d8: orig 0x710/0x718/0x730/0x738 (`ldxdw r2,[r10-0x910]`, `mov64 r9,r4`, the `and64 r1,1` holder-flag
  test);
- 0x1738-0x17a0: the range-check OK-block spills and `mov64 r7,1`.

Every one of them is a register-allocation fact of the original (r9 carries max_fee from the entry through validate, then
the error-return payload; the holder flag is a spilled i1; the fee tag is a phi), or the PDA-first entry order
(w15a35: `m_pdaf` 27,400 / 1,939). None is a source construct that adds exactly that instruction. Outside validate the
ceiling is a tie at two points (0x1c58 error payload `ldxdw r9`, 0x1d20 sweep gate), also RA facts.

## 4. Captured validate spellings on vb (step 3; all with the line-338 placeholder kept)

| key | form (on vb) | bytes | M | vs vb |
| --- | --- | ---: | ---: | --- |
| d_nf | `match fee{None=>{}Some(f)=>..}` (arm order) | 27,392 | 2,250 | byte-identical |
| d_rq4 | create_v2 `require!` on 326/330/334/338 | 27,392 | 2,250 | byte-identical |
| d_rqhead | `require!` on 284/289/298 | 27,392 | 2,250 | byte-identical |
| d_rkn307 | create_v2 `require_keys_neq!(t,Pubkey::default(),..)` | 27,392 | 2,250 | byte-identical |
| d_req284 / d_req289 / d_req298 | single `require!` forms (289/298 were neutral, not identical, on 9bd38c7) | 27,392 | 2,250 | byte-identical |
| d_rq338b / d_rq338c | `require!(f!=0&&f<=max)` / `require!((1..=max).contains(&f))` | 27,392 | 2,250 | byte-identical |
| d_reff | `match &fee{Some(f)=>{let f=*f;..}}` | 27,392 | 2,250 | byte-identical |
| d_rqall | rq4 + rqhead + rkn307 | 27,392 | 2,250 | byte-identical |
| d_ifl | `if let Some(f)=fee{..}` | 27,400 | 2,163 | -87 |
| d_wc | `_=>{}` arm | 27,400 | 2,163 | -87 (= d_ifl) |
| d_iflrq4 | if-let + rq4 | 27,400 | 2,163 | -87 (= d_ifl) |

The sibling forms that w16a02 found byte-identical on main stay byte-identical without the placeholder. They lower to the
same IR before register allocation, so the different RA context cannot reach them. The `if let` / wildcard forms are the
only fee-arm spellings that change code: +8 B, but they rebuild the fee-arm switch and lose 87.

## 5. The faithful form: fee-tag phi as source hits an inliner cliff (step 4)

The original's range-check OK block is `stxdw [r10-0x918],r4; stxdw [r10-0x948],r3; mov64 r7,1`. The last instruction
is the fee-tag phi constant that feeds the line-757 `Some(f)` test (`mov64 r7,0` on the None paths). This is the only
data flow that legitimately fills the block the 338 placeholder anchors (w15a29). Its IR-level price on main is -186 M at
-176 B (phi feeds 757 + pool tag) or -276 M (757 only). w16a12's `ft` and `ftc` source forms lose 1,138 and 201.

This lane's ordinary-source form `fh` keeps validate's `Result<Pubkey>` and moves the fee arm to a helper at the same
lines. `fn fee_checked(st,cashback,fee)->Result<Option<u64>>` returns `Ok(Some(f))` or `Ok(None)`, and execute uses the
re-made fee for the curve store and/or the pool tag. No placeholder is left and every error line is kept.

| key | form | result |
| --- | --- | --- |
| f_fh / f_fh757 / f_fhcpi | re-made fee feeds both uses / line 757 only / pool tag only | collapse |
| f_fhmt | helper returns the input fee (`Ok(fee)`, no re-make, no phi) | collapse |
| f_fhi, f_fh757i, f_fhcpii, f_fhmti | the same with `#[inline] fn fee_checked` | collapse |
| f_fhand | one combined `?`: `validate(..).and_then(\|t\|Ok((t,fee_checked(..)?)))?` | collapse |

Every helper form un-inlines the nested `sweep` fn: execute is 18,448 B plus `sweep` 9,088 B. The res rows' 9,088 B /
M 208 are the `sweep` symbol. `opt -pass-remarks-missed=inline` on f_fhi reports: `sweep` not inlined into execute,
"too costly (cost=4220, threshold=45)". On main the same site inlines at cost -10,780 / threshold 250. Moving the fee
arm behind a helper boundary turns the sweep call site cold (threshold 45) and drops the last-call bonus. Even the
no-phi control `fh_mt` does this, so the helper boundary alone causes it, not the phi. A faithful fee-tag phi therefore
needs, in one joint move:
- the fee re-made inside the inlined validate body, keeping validate's Result layout (ft's tuple return shifts the frame);
- sweep kept inlined;
- the 176 B the dead `%1` argument frees, repaid with faithful code (the 307/312 `to_string` outline direction,
  #3632 / w16a13).

## Conclusion

Within this angle neither placeholder can be replaced faithfully at a tie:
- 334 is pure fill. It needs exactly one extra instruction in validate or the entry. The only faithful candidates are
  RA facts or the PDA-first order, and no source spelling adds one.
- 338 is the anchor of the fee-tag phi's block. The phi's source forms are whole-region moves that cost 186-1,138 M,
  or collapse through the sweep inliner cliff found here.

Per the owner's decision the placeholders stay.

## Next ideas

1. A joint fee-tag-phi move: re-make the fee inside validate's own body so no new helper boundary or `?` appears, for
   example by returning the fee through the existing `(holder,cashback,target,..)` block tuple from an inline `match`
   at lines 326-338 (that needs execute's body to start before line 326, a large line-layout change). Then repay the
   -176 B with the to_string outline. Price it with w16a12's restored-joint pipeline before building.
2. The sweep cold-site cliff (cost 4,220 against threshold 45 once anything adds a branch before the sweep site) is a
   general hazard for any lane that adds a `?` between validate and the sweep. Check `-pass-remarks-missed=inline` first
   when a capture shrinks to about 18.4 KB.
3. insmatch's 933 +1 cells say that one instruction of the original's entry or validate RA would gain over main. A lane
   that moves max_fee into a callee-saved register across validate (the original's r9) is the source-level route, and
   it is an RA lever, not a spelling.

## Tools (experiment only; paths point at this lane's `$OUT`)

- `tools/scr.py` (w16a02 scr: ledger approach `devoltie`, `KEEPNAMES`), `tools/capraw.py` (`--emit=llvm-ir` only).
- `tools/genes_dt.py`: `vb`, `v338`, fee-arm forms, `require!` bundles, and the `fh*` fee-helper family
  (imports w16a02's `genes_fk`).
- `tools/vbscreen.py`: vb x catalog splice screen (singles / zero-sum pairs).
- `tools/insmatch2.py`: whole-window faithful-token insertion map. `tools/gaps2.py`: LCS gaps over a candidate range.
