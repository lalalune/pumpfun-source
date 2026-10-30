# w13a37-cto-skelregress: sharing-CPI AccountInfo clone forms, plain ratio vs skeleton

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: win back the code shape (skeleton) the hand-written AccountInfo literals lost, while keeping their plain-ratio gain.
Wave 13 lane, continued in wave 14 after the network loss. Ledger approach `cpi-clone-form`, keys
`0x22a10-w13-fb83222-skelregress-*` (wave 13, 115 rows) and `0x22a10-w13-53abf28-skelregress-*` (wave 14).

## Result (wave 14, main 53abf28b1, 0.62672 / 3,305 slots)

**0.62672 -> 0.62702, 3,305 slots, 27,400 B, 1034/1034 normalized and raw, 0 losses, differential 363/0,
skeleton 0.8562 -> 0.8565.** The sharing CPI's `authority` changed from `a.admin_set_creator_authority.to_account_info()` to the
struct-update clone form
`{let x:&AccountInfo=a.admin_set_creator_authority.as_ref();AccountInfo{key:x.key,owner:x.owner,..x.clone()}}`.
This is the same form main already uses for the TCF `associated_token_program`. Unstripped sha `6fa6f9a2706d2659`.

## Metric

`tools/reg.py <unstripped.so>` (in `$OUT/tools`, needs the w13a23 `ctoracle.py`): difflib ratio over the whole function and per
1/16 of the original window, for plain tokens, frame-masked tokens (`ctoracle.abstract`) and the skeleton (frame-masked
with the register byte zeroed). The "0x3c34" and "0x42e5" columns are the two sharing-CPI clone chunks.
`tools/skdiff.py <so> lo hi` prints the skeleton opcodes for an original offset range. `tools/fpairs.py <so> lo hi`
gives a histogram of the (orig - cand) r10 offset deltas over frame-masked matched instructions.
`tools/var.py` rewrites one CPI account initializer per spec (`tai`, a field-order string `KLDORSWE`, or `raw:`).
`tools/run.sh` / `tools/batch.py` build specs through `measure.sh` and append to `$OUT/results.jsonl`.

## Findings

1. **A literal in derive order is byte-identical to `to_account_info()`** (wave 13, `s_kl` == `s_drv`). A literal changes code
   only through where each field read sits relative to the two `Rc` increments (L = lamports, D = data). Moving a scalar
   within one position class usually changes only registers and spill slots, but not always: mint `RSWELKOD` and
   `SRWELKOD` differ in skeleton.
2. **On main 53abf28 every skeleton-faithful move costs plain ratio.** Key read right after the lamports clone (`kL`, the
   original's order at orig 0x4210) on mint / sharing_config / event_authority restores the 0x3c34 chunk skeleton
   0.78 -> 0.87-0.90 (whole skeleton 0.8562 -> 0.866-0.867) but loses 0.014-0.021 plain ratio (`n2_S_E` 0.61234 at 27,400 B,
   skeleton 0.8667). The loss is frame offsets only: in 0x42e5 the plain match drops 0.27 -> 0.09 while the frame-masked
   match rises 0.49 -> 0.53, and whole frame-masked is 0.7283 vs main 0.7259. The offset deltas are spread over 8-56 B
   (`fpairs.py`), so it is spill-slot order, not a single frame shift.
3. **The wave-13 lever `c_ko_rev` (0.62191 at 27,376 B on fb83222) did not carry over.** On 53abf28 it gives 0.61882 at 27,384 B,
   and the old `s_rev` basin gives 0.60827 at 27,416 B.
4. **Main's literals are a local maximum under adjacent swaps.** 35 adjacent field swaps over the 5 sharing literals: none
   beats 0.62672. Several tie at 0.62672 (glob `WSRLDOEK`, `SWRLDOKE`, prog `OLRSEDWK`). Event_authority `DLKORSWE` ties
   ratio with skeleton 0.8574.
5. **The struct-update form `AccountInfo{key,owner,..x.clone()}` is a new knob class.** It reads key/owner before the
   clone, and the remaining scalars come from the clone. On the authority account `uKO` and `uO` both give 0.62702.
   `uK` on authority / sharing_config is identical to main (same sha). On pool / global it is 0.62522 / 0.62433 at
   27,400 B with skeleton 0.8574, and on program 0.62292-0.62631 at 27,384-27,392 B.

## Tables (main 53abf28)

| variant | ratio | bytes | skeleton | 0x3c34 | 0x42e5 |
|---|---:|---:|---:|---:|---:|
| n3_uO_auth | 0.62702 | 27400 | 0.8559 | 0.78 | 0.71 |
| n3_uKO_auth | 0.62702 | 27400 | 0.8565 | 0.74 | 0.76 |
| n1_prog_kZ_OLRSEDWK | 0.62672 | 27400 | 0.8562 | 0.78 | 0.71 |
| n1_ctx_KLDORSWE | 0.62672 | 27400 | 0.8562 | 0.78 | 0.71 |
| n3_sw_glob_WSRLDOEK | 0.62672 | 27400 | 0.8562 | 0.78 | 0.71 |
| n3_sw_glob_SWRLDOKE | 0.62672 | 27400 | 0.8562 | 0.78 | 0.71 |
| n3_sw_even_DLKORSWE | 0.62672 | 27400 | 0.8574 | 0.87 | 0.64 |
| n3_sw_prog_OLRSEDWK | 0.62672 | 27400 | 0.8562 | 0.78 | 0.71 |
| n3_uK_auth | 0.62672 | 27400 | 0.8562 | 0.78 | 0.71 |
| n3_uK_shar | 0.62672 | 27400 | 0.8562 | 0.78 | 0.71 |
| n1_glob_kD_SWRLDKOE | 0.62642 | 27400 | 0.8562 | 0.78 | 0.71 |
| n3_uK_prog | 0.62631 | 27384 | 0.8496 | 0.84 | 0.55 |
| n3_sw_glob_SWRDLOEK | 0.62612 | 27400 | 0.8565 | 0.74 | 0.76 |
| n3_sw_glob_SWRLDEOK | 0.62612 | 27400 | 0.8562 | 0.78 | 0.71 |
| n3_sw_prog_OLSREDKW | 0.62612 | 27400 | 0.8562 | 0.78 | 0.71 |
| n3_sw_prog_OLRESDKW | 0.62582 | 27400 | 0.8562 | 0.78 | 0.71 |
| n3_sw_glob_SRWLDOEK | 0.62552 | 27400 | 0.8562 | 0.78 | 0.71 |
| n3_uK_pool | 0.62522 | 27400 | 0.8574 | 0.76 | 0.76 |
| n1_pool_kD_ELDKWORS | 0.62463 | 27400 | 0.8559 | 0.78 | 0.71 |
| n1_auth_kZ_LDORSWEK | 0.62463 | 27400 | 0.8478 | 0.65 | 0.71 |
| n1_auth_kD_LDKORSWE | 0.62433 | 27400 | 0.8562 | 0.78 | 0.71 |
| n3_sw_pool_ELDWORKS | 0.62433 | 27400 | 0.8559 | 0.78 | 0.71 |
| n3_uK_glob | 0.62433 | 27400 | 0.8574 | 0.76 | 0.76 |
| n3_uKO_prog | 0.62292 | 27392 | 0.8581 | 0.78 | 0.74 |
| n3_uO_prog | 0.62292 | 27392 | 0.8581 | 0.78 | 0.74 |
| n3_sw_prog_ORLSEDKW | 0.62283 | 27400 | 0.8565 | 0.78 | 0.71 |
| n3_sw_prog_OLRSDEKW | 0.62101 | 27376 | 0.8482 | 0.78 | 0.58 |
| n3_sw_prog_LORSEDKW | 0.62052 | 27392 | 0.8578 | 0.87 | 0.64 |
| n3_sw_even_LDKORSEW | 0.62013 | 27400 | 0.8565 | 0.84 | 0.66 |
| n1_even_kZ_LDORSWEK | 0.61993 | 27392 | 0.8572 | 0.84 | 0.67 |
| n3_sw_even_LDOKRSWE | 0.61993 | 27392 | 0.8566 | 0.88 | 0.62 |
| n1_glob_kL_SWRLKDOE | 0.61914 | 27408 | 0.8480 | 0.83 | 0.54 |
| n3_sw_even_LDKROSWE | 0.61873 | 27392 | 0.8563 | 0.88 | 0.62 |
| n3_sw_even_LDKOSRWE | 0.61873 | 27392 | 0.8515 | 0.88 | 0.54 |
| n3_sw_even_LDKORWSE | 0.61873 | 27392 | 0.8515 | 0.88 | 0.54 |
| n3_sw_glob_SWLRDOEK | 0.61824 | 27408 | 0.8486 | 0.84 | 0.54 |
| n2_Mk_RSWELKDO | 0.61792 | 27384 | 0.8538 | 0.74 | 0.71 |
| n1_shar_kZ_LDORSWEK | 0.61732 | 27384 | 0.8487 | 0.84 | 0.54 |
| n3_sw_pool_ELWDORSK | 0.61695 | 27416 | 0.8467 | 0.64 | 0.71 |
| n3_sw_pool_ELDOWRSK | 0.61663 | 27392 | 0.8482 | 0.83 | 0.54 |
| n1_pool_kL_ELKDWORS | 0.61649 | 27352 | 0.8483 | 0.57 | 0.79 |
| n1_even_kF_KLDORSWE | 0.61640 | 27360 | 0.8484 | 0.83 | 0.54 |
| n3_uK_even | 0.61640 | 27360 | 0.8484 | 0.83 | 0.54 |
| n3_sw_pool_ELDWOSRK | 0.61633 | 27392 | 0.8476 | 0.82 | 0.54 |
| n3_sw_pool_ELDWROSK | 0.61603 | 27392 | 0.8476 | 0.82 | 0.54 |
| n1_shar_kD_LDKORSWE | 0.61552 | 27384 | 0.8487 | 0.84 | 0.54 |
| n3_sw_mint_RSEWLODK | 0.61499 | 27352 | 0.8486 | 0.74 | 0.62 |
| n3_sw_mint_SRWELODK | 0.61469 | 27352 | 0.8486 | 0.74 | 0.62 |
| n3_sw_mint_RWSELODK | 0.61469 | 27352 | 0.8486 | 0.74 | 0.62 |
| n1_prog_kF_KOLRSEDW | 0.61456 | 27416 | 0.8562 | 0.87 | 0.63 |
| n2_Mk_SRWELKOD | 0.61402 | 27384 | 0.8535 | 0.74 | 0.71 |
| n2_Mk_SWELKROD | 0.61372 | 27384 | 0.8535 | 0.74 | 0.71 |
| n2_Mk_RWELKSOD | 0.61343 | 27384 | 0.8535 | 0.74 | 0.71 |
| n3_sw_glob_SWRLODEK | 0.61315 | 27408 | 0.8486 | 0.84 | 0.54 |
| n2_Mk_WSRELKOD | 0.61313 | 27384 | 0.8535 | 0.74 | 0.71 |
| n2_Mk_RSELKWOD | 0.61313 | 27384 | 0.8535 | 0.74 | 0.71 |
| n1_prog_kL_OLKRSEDW | 0.61306 | 27416 | 0.8571 | 0.87 | 0.64 |
| n3_sw_prog_OLRSEKDW | 0.61306 | 27416 | 0.8562 | 0.87 | 0.63 |
| n2_S_E | 0.61234 | 27400 | 0.8667 | 0.88 | 0.78 |
| n2_Mk_RSWEOLKD | 0.61193 | 27384 | 0.8571 | 0.88 | 0.63 |
| n2_Mk_ROSWELKD | 0.61193 | 27384 | 0.8571 | 0.88 | 0.63 |
| n1_auth_kL_LKDORSWE | 0.61184 | 27392 | 0.8393 | 0.69 | 0.54 |
| n3_uKO_even | 0.61172 | 27376 | 0.8566 | 0.69 | 0.80 |
| n3_uO_even | 0.61172 | 27376 | 0.8566 | 0.69 | 0.80 |
| n3_sw_mint_RSWELDOK | 0.61112 | 27376 | 0.8485 | 0.83 | 0.54 |
| n2_Mk_OLKDRSWE | 0.61013 | 27384 | 0.8538 | 0.74 | 0.71 |
| n2_Mk_ELKDORSW | 0.61013 | 27384 | 0.8538 | 0.74 | 0.71 |
| n3_sw_mint_RSWEOLDK | 0.60948 | 27336 | 0.8494 | 0.84 | 0.54 |
| n3_sw_mint_RSWELOKD | 0.60893 | 27384 | 0.8535 | 0.74 | 0.71 |
| n3_uK_mint | 0.60872 | 27376 | 0.8674 | 0.75 | 0.92 |
| n3_uKO_mint | 0.60872 | 27376 | 0.8668 | 0.75 | 0.91 |
| n3_uO_mint | 0.60872 | 27376 | 0.8668 | 0.75 | 0.91 |
| n2_Mk_LKDORSWE | 0.60863 | 27384 | 0.8535 | 0.74 | 0.71 |
| n2_M_P | 0.60857 | 27416 | 0.8580 | 0.90 | 0.63 |
| n1_even_kL_LKDORSWE | 0.60836 | 27408 | 0.8660 | 0.87 | 0.78 |
| n3_sw_even_LKDORSWE | 0.60836 | 27408 | 0.8660 | 0.87 | 0.78 |
| n1_mint_kF_KRSWELOD | 0.60833 | 27384 | 0.8571 | 0.88 | 0.63 |
| n1_mint_kL_RSWELKOD | 0.60817 | 27424 | 0.8666 | 0.90 | 0.76 |
| n2_M_S_E_P | 0.60799 | 27440 | 0.8672 | 0.90 | 0.78 |
| n3_uKO_shar | 0.60716 | 27408 | 0.8558 | 0.78 | 0.71 |
| n3_uO_shar | 0.60716 | 27408 | 0.8558 | 0.78 | 0.71 |
| n1_ctx_KODLRSWE | 0.60711 | 27360 | 0.8475 | 0.56 | 0.79 |
| n3_uKO_pool | 0.60708 | 27336 | 0.8491 | 0.75 | 0.62 |
| n3_uO_pool | 0.60708 | 27336 | 0.8491 | 0.75 | 0.62 |
| n2_M_S | 0.60683 | 27384 | 0.8628 | 0.88 | 0.71 |
| n3_sw_pool_LEDWORSK | 0.60662 | 27376 | 0.8488 | 0.84 | 0.54 |
| n3_sw_pool_EDLWORSK | 0.60662 | 27376 | 0.8401 | 0.70 | 0.54 |
| n1_ctx_LKDORSWE | 0.60660 | 27352 | 0.8468 | 0.80 | 0.54 |
| n2_M_E | 0.60656 | 27408 | 0.8666 | 0.87 | 0.79 |
| n2_Mk_RSWLKOED | 0.60593 | 27384 | 0.8535 | 0.74 | 0.71 |
| n2_Mk_ERSWLKOD | 0.60593 | 27384 | 0.8535 | 0.74 | 0.71 |
| n1_shar_kL_LKDORSWE | 0.60584 | 27392 | 0.8659 | 0.88 | 0.76 |
| n2_M_S_E | 0.60575 | 27400 | 0.8673 | 0.89 | 0.78 |
| n2_Mk_LKODRSWE | 0.60563 | 27384 | 0.8535 | 0.74 | 0.71 |
| n3_sw_mint_RSWLEODK | 0.60563 | 27384 | 0.8538 | 0.74 | 0.71 |
| n1_pool_kF_KELDWORS | 0.60381 | 27360 | 0.8568 | 0.71 | 0.79 |
| n1_ctx_OLRSEDKW | 0.60225 | 27392 | 0.8479 | 0.75 | 0.62 |
| n1_glob_kF_KSWRLDOE | 0.60123 | 27456 | 0.8460 | 0.81 | 0.54 |
| n3_uKO_glob | 0.60123 | 27456 | 0.8460 | 0.81 | 0.54 |
| n3_uO_glob | 0.60123 | 27456 | 0.8460 | 0.81 | 0.54 |
