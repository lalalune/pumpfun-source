# w13a37-cto-skelregress: sharing-CPI AccountInfo clone forms, plain ratio vs skeleton

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: win back the code shape (skeleton) the hand-written AccountInfo literals lost, while keeping their plain-ratio gain.
Wave 13 lane, continued in wave 14 after the network loss. Ledger approach `cpi-clone-form`, keys
`0x22a10-w13-fb83222-skelregress-*` (wave 13, 115 rows) and `0x22a10-w13-53abf28-skelregress-*` (wave 14).

## Result

**No landable gain on current main.** Main moved five times during wave 14:
53abf28 0.62672 -> 23322b0 0.62882 -> 308b545 0.63062 -> 769f331 0.63241 (w13a47-cto-stitch9) -> cef0574 0.63421 / 3,179 slots
(w14a03-cto-liverange). The last re-check (r14 table) is on cef0574.

- On 53abf28 the sharing CPI `authority` as the struct-update clone
  `{let x:&AccountInfo=a.admin_set_creator_authority.as_ref();AccountInfo{key:x.key,owner:x.owner,..x.clone()}}`
  gave 0.62672 -> 0.62702 at 27,400 B, 3,305 slots, 0 losses, differential 363/0. It was committed as 6a844efec.
- Main moved to 23322b0 before the PR, and the same edit then measured 0.62852 against main's 0.62882. On 769f331 it
  measures 0.63212 against 0.63241. It was reverted (6dab09ec5), so this branch is notes only.
- On 769f331 (0.63241), none of 16 single moves or 27 pairs beats main. Single moves: struct-update forms, the K-position
  moves that tie, and field orders. Pairs: combinations of the ties and near-misses.

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
6. **Every clone-form knob is local and additive on current main.** Single deltas on 769f331: `aKO` -0.00029,
   `tKO_tok` -0.00089, `tKO_sys` -0.00149, `pK` -0.00179, `glob_kD` -0.00029. Every pair sums its singles to within one token
   step of about 0.0003 (`aKO+tKO_tok` 0.63122 = -0.00029 - 0.00089; `tKO_tok+pK` 0.62972). With no single knob
   positive, no combination of this class can gain. Ratios are quantized in steps of about 0.0003, a few tokens each.
7. **Ratio-neutral moves on three mains** (same ratio and slots, different sha): event_authority `DLKORSWE` (skeleton +0.0012),
   global `WSRLDOEK` / `SWRLDOKE`, program `OLRSEDWK`. `uK`-form TCF fields and `uK` on authority / sharing_config are
   byte-identical to main, because a key read first is the derive order.
8. **Size knobs from the struct-update form**, each measured as a single edit:
   - program (sharing) `uK`: **-16 B**, -0.00011 on both 23322b0 and 769f331. This is a cheap -16 B companion.
   - program `uKO` / `uO`: -8 B, -0.0044.
   - mint `uK`: -24 B, -0.018, with skeleton +0.011.
   - event_authority `uK`: -40 B, -0.012.
   - sharing_config `uO`: +8 B, -0.021.
   - Any `..x.clone()` form in the pool CPI (`AdminCtoPool`): +232..+312 B, -0.07. The original pool CPI uses plain
     `to_account_info()` clones.
9. **The skeleton/plain trade-off persists on 769f331.** See the `q11_*` rows: key-after-lamports on
   mint / sharing_config / event_authority restores the clone-run skeleton and loses 0.015-0.02 plain ratio to spill-slot offsets.
10. **Inside the skeleton-faithful basin the knobs are not additive.** `S_E` (sharing_config and event_authority key after
    lamports) alone is -0.0147 at 27,400 B, and program `uK` alone is -0.0001 at -16 B. Together (`SE_prK`) they are only
    -0.0054 at 27,376 B. The best point is `SE_prK_evDK` (event_authority back to `LDKORSWE`): 0.63040 at 27,368 B on
    cef0574. That is -0.0038 against main, with skeleton 0.8543 against 0.8526. Even a perfect +32 B companion would leave it
    below main. `S_E` also has one fewer slot than main at 27,400 B (3,178 vs 3,179), but ratio ranks first.
11. **Single-knob deltas against main hold to within one token step on 769f331 and cef0574.** `eDL` and `gW` are 0, `aKO`
    is -0.0003 and `prK` is -0.0001 / -0.0007. They can be reused as a catalog without re-measuring.

## Next ideas

- The skeleton-faithful clone forms (`S_E`, `M_S_E`, `mint_kL`) only pay once spill-slot order matches the original. Pair them
  with whatever frame or spill-order lever moves the 0x42e5 chunk's r10 offsets (`fpairs.py` gives the delta histogram).
  w13a40 #3164 shows the clone run's accounts-pointer reload is set by the swept / Err-payload coalescing.
- Use program `uK` (-16 B, -0.0001) as a size companion for -16 B..+16 B gene stacks.
- The per-account literal / clone-form space of the sharing and TCF CPIs is exhausted on this main: 115 wave-13 rows and
  about 190 wave-14 rows.

## Tables

Plain ratio, bytes, whole skeleton and the two sharing-CPI chunk skeletons. Builds off 27,400 B carry the expected 687 raw
shift losses. Specs are in  and in the ledger hypothesis text.

### r14 (main cef0574 0.63421)

| variant | ratio | bytes | skeleton | 0x3c34 | 0x42e5 | sha |
|---|---:|---:|---:|---:|---:|---|
| r14_eDL | 0.63421 | 27400 | 0.8535 | 0.87 | 0.64 | 00165addf067 |
| r14_gW | 0.63421 | 27400 | 0.8523 | 0.78 | 0.71 | c3af79df87e8 |
| r14_aKO | 0.63391 | 27400 | 0.8526 | 0.74 | 0.76 | 073b4c745215 |
| r14_prK | 0.63350 | 27384 | 0.8457 | 0.84 | 0.55 | e76436ebce7c |
| r14_SE_prK_evDK | 0.63040 | 27368 | 0.8543 | 0.78 | 0.73 | 931d11c8eed1 |
| r14_SE_prK_aKO | 0.63000 | 27376 | 0.8536 | 0.74 | 0.77 | f1a32c38d04b |
| r14_SE_prK_pK | 0.62970 | 27376 | 0.8563 | 0.85 | 0.70 | 2902d675d46d |
| r14_SE_prK_aKO_pK | 0.62940 | 27376 | 0.8560 | 0.85 | 0.70 | c8b03ec9993b |
| r14_SE_prK | 0.62880 | 27376 | 0.8554 | 0.84 | 0.70 | d666716b7d71 |
| r14_SE | 0.61953 | 27400 | 0.8628 | 0.88 | 0.78 | 80448f02391d |

### q13 (main 769f331 0.63241)

| variant | ratio | bytes | skeleton | 0x3c34 | 0x42e5 | sha |
|---|---:|---:|---:|---:|---:|---|
| q13_aKO | 0.62850 | 27376 | 0.8539 | 0.74 | 0.77 | 34adffc1eb36 |
| q13_evDK | 0.62830 | 27368 | 0.8546 | 0.78 | 0.73 | 87cde7c7645f |
| q13_pK | 0.62820 | 27376 | 0.8566 | 0.85 | 0.70 | 6f8830a1fcd3 |
| q13_authkL | 0.62751 | 27384 | 0.8460 | 0.66 | 0.73 | a7fcd703469a |
| q13_gW | 0.62730 | 27376 | 0.8557 | 0.84 | 0.70 | 2623971e064e |
| q13_prKLDORSWE | 0.62730 | 27376 | 0.8557 | 0.84 | 0.70 | a0e52857e617 |
| q13_prLKDORSWE | 0.62730 | 27376 | 0.8536 | 0.88 | 0.63 | 620b639d80d9 |
| q13_prKO | 0.62670 | 27376 | 0.8551 | 0.84 | 0.69 | 5d4ff8cbd333 |
| q13_prKE | 0.62670 | 27376 | 0.8551 | 0.84 | 0.69 | ab5f0f1b1915 |
| q13_prKOLDRSWE | 0.62670 | 27376 | 0.8551 | 0.84 | 0.69 | 5d4ff8cbd333 |
| q13_prKR | 0.62640 | 27376 | 0.8551 | 0.84 | 0.69 | dfa509f643fb |
| q13_shKL | 0.62491 | 27376 | 0.8563 | 0.80 | 0.75 | 15c8cc96592f |
| q13_globkL | 0.62440 | 27368 | 0.8540 | 0.88 | 0.63 | 697efe810995 |
| q13_evLK2 | 0.62300 | 27360 | 0.8541 | 0.88 | 0.63 | 1193b45225db |
| q13_gK | 0.62148 | 27336 | 0.8632 | 0.74 | 0.90 | f2a2fcd376a2 |
| q13_authkL_globkL | 0.61993 | 27392 | 0.8443 | 0.82 | 0.54 | 09fd74c58f53 |
| q13_poolkL | 0.61806 | 27320 | 0.8563 | 0.63 | 0.90 | 634839d40862 |
| q13_mK | 0.61432 | 27384 | 0.8460 | 0.62 | 0.77 | 88400566aacd |
| q13_shDK | 0.61253 | 27384 | 0.8520 | 0.70 | 0.78 | d53ce48efa6d |
| q13_shLK2 | 0.61193 | 27384 | 0.8451 | 0.70 | 0.67 | 840eef944803 |
| q13_mintkL | 0.61184 | 27392 | 0.8449 | 0.65 | 0.72 | 3081d65c07a3 |
| q13_authkL_mintkL | 0.60764 | 27392 | 0.8165 | 0.39 | 0.53 | 43f971d2bc14 |

### q12 (main 769f331 0.63241)

| variant | ratio | bytes | skeleton | 0x3c34 | 0x42e5 | sha |
|---|---:|---:|---:|---:|---:|---|
| q12_SE_prK | 0.62730 | 27376 | 0.8557 | 0.84 | 0.70 | a0e52857e617 |
| q12_SE_authkL | 0.62631 | 27384 | 0.8436 | 0.81 | 0.54 | f5c61d78d50b |
| q12_SE_globkL | 0.62431 | 27376 | 0.8536 | 0.88 | 0.63 | fa45ce3d8ec3 |
| q12_SE_aKO | 0.61833 | 27400 | 0.8445 | 0.83 | 0.54 | 7275a26c8f73 |
| q12_SE_prO | 0.61774 | 27400 | 0.8631 | 0.88 | 0.78 | 3404def536fd |
| q12_SE_gW | 0.61774 | 27400 | 0.8631 | 0.88 | 0.78 | 13181f4b508f |
| q12_SE_poolkL | 0.61608 | 27336 | 0.8536 | 0.63 | 0.86 | ec5e77eb1165 |
| q12_SE_pK | 0.61534 | 27400 | 0.8640 | 0.90 | 0.78 | 2e66b219da4d |

### q11 (main 769f331 0.63241)

| variant | ratio | bytes | skeleton | 0x3c34 | 0x42e5 | sha |
|---|---:|---:|---:|---:|---:|---|
| q11_uKO_prog | 0.62801 | 27392 | 0.8545 | 0.78 | 0.74 | f47300d6e9cd |
| q11_uK_even | 0.62030 | 27360 | 0.8449 | 0.83 | 0.54 | 681d46a392c2 |
| q11_S_E | 0.61774 | 27400 | 0.8631 | 0.88 | 0.78 | 3404def536fd |
| q11_uK_mint | 0.61472 | 27376 | 0.8638 | 0.75 | 0.92 | 3930c48f65ff |
| q11_mint_kL | 0.61327 | 27424 | 0.8630 | 0.90 | 0.76 | 809d305df17f |
| q11_uO_shar | 0.61135 | 27408 | 0.8522 | 0.78 | 0.71 | 84f77d9baeb6 |
| q11_M_S_E | 0.61114 | 27400 | 0.8637 | 0.89 | 0.78 | 152361dd125e |

### q10 (main 769f331 0.63241)

| variant | ratio | bytes | skeleton | 0x3c34 | 0x42e5 | sha |
|---|---:|---:|---:|---:|---:|---|
| q10_eDL+gW | 0.63241 | 27400 | 0.8538 | 0.87 | 0.64 | 4f4c7aadd9b6 |
| q10_eDL+prOLRSEDWK | 0.63241 | 27400 | 0.8538 | 0.87 | 0.64 | 533372cd3df7 |
| q10_gW+prOLRSEDWK | 0.63241 | 27400 | 0.8526 | 0.78 | 0.71 | 0437b529a0b2 |
| q10_aKO+pK | 0.63241 | 27400 | 0.8541 | 0.76 | 0.76 | 3246d5452017 |
| q10_eDL+glob_kD | 0.63212 | 27400 | 0.8538 | 0.87 | 0.64 | 3da76bf4ed56 |
| q10_eDL+aKO | 0.63212 | 27400 | 0.8523 | 0.74 | 0.75 | 3956f4c19ec8 |
| q10_gW+aKO | 0.63212 | 27400 | 0.8529 | 0.74 | 0.76 | ba04a12783eb |
| q10_prOLRSEDWK+aKO | 0.63212 | 27400 | 0.8529 | 0.74 | 0.76 | 8cf674975d01 |
| q10_prOLRSEDWK+glob_kD | 0.63212 | 27400 | 0.8526 | 0.78 | 0.71 | 8880d2e106c8 |
| q10_aKO+glob_kD | 0.63182 | 27400 | 0.8529 | 0.74 | 0.76 | d89c351e96ba |
| q10_eDL+tKO_tok | 0.63152 | 27400 | 0.8532 | 0.87 | 0.64 | 76ee36af29ef |
| q10_gW+tKO_tok | 0.63152 | 27400 | 0.8520 | 0.78 | 0.71 | 8f264e6791f4 |
| q10_prOLRSEDWK+tKO_tok | 0.63152 | 27400 | 0.8520 | 0.78 | 0.71 | d5b40e99ce21 |
| q10_aKO+tKO_tok | 0.63122 | 27400 | 0.8523 | 0.74 | 0.76 | b93907ced89e |
| q10_glob_kD+tKO_tok | 0.63122 | 27400 | 0.8520 | 0.78 | 0.71 | 4fb761b3375d |
| q10_eDL+tKO_sys | 0.63092 | 27400 | 0.8538 | 0.87 | 0.64 | e44629a16c43 |
| q10_gW+tKO_sys | 0.63092 | 27400 | 0.8526 | 0.78 | 0.71 | ee9d59574b9b |
| q10_prOLRSEDWK+tKO_sys | 0.63092 | 27400 | 0.8526 | 0.78 | 0.71 | 786006f59f1e |
| q10_eDL+pK | 0.63062 | 27400 | 0.8532 | 0.75 | 0.75 | 85fa320f55f9 |
| q10_gW+pK | 0.63062 | 27400 | 0.8538 | 0.76 | 0.76 | 6a99b85df3b3 |
| q10_prOLRSEDWK+pK | 0.63062 | 27400 | 0.8538 | 0.76 | 0.76 | 90e8d1628e89 |
| q10_aKO+tKO_sys | 0.63062 | 27400 | 0.8529 | 0.74 | 0.76 | 2dae143db16e |
| q10_glob_kD+tKO_sys | 0.63062 | 27400 | 0.8526 | 0.78 | 0.71 | e0c831be57ac |
| q10_glob_kD+pK | 0.63032 | 27400 | 0.8538 | 0.76 | 0.76 | af30a11ab2b0 |
| q10_tKO_tok+tKO_sys | 0.63002 | 27400 | 0.8526 | 0.78 | 0.71 | 6c2c75cb0233 |
| q10_tKO_tok+pK | 0.62972 | 27400 | 0.8532 | 0.76 | 0.76 | 40393ba8dae1 |
| q10_tKO_sys+pK | 0.62912 | 27400 | 0.8538 | 0.76 | 0.76 | 5490e8ea201d |

### q9 (main 769f331 0.63241)

| variant | ratio | bytes | skeleton | 0x3c34 | 0x42e5 | sha |
|---|---:|---:|---:|---:|---:|---|
| q9_eDL | 0.63241 | 27400 | 0.8538 | 0.87 | 0.64 | 533372cd3df7 |
| q9_gW | 0.63241 | 27400 | 0.8526 | 0.78 | 0.71 | 0437b529a0b2 |
| q9_gSWRLDOKE | 0.63241 | 27400 | 0.8526 | 0.78 | 0.71 | 2c4226876b33 |
| q9_prOLRSEDWK | 0.63241 | 27400 | 0.8526 | 0.78 | 0.71 | 83f55c383a65 |
| q9_prK | 0.63230 | 27384 | 0.8460 | 0.84 | 0.55 | 3289817488fc |
| q9_aKO | 0.63212 | 27400 | 0.8529 | 0.74 | 0.76 | 8cf674975d01 |
| q9_aO | 0.63212 | 27400 | 0.8523 | 0.78 | 0.71 | d47cb8a36c8f |
| q9_glob_kD | 0.63212 | 27400 | 0.8526 | 0.78 | 0.71 | 8880d2e106c8 |
| q9_tKO_tok | 0.63152 | 27400 | 0.8520 | 0.78 | 0.71 | d5b40e99ce21 |
| q9_tKO_sys | 0.63092 | 27400 | 0.8526 | 0.78 | 0.71 | 786006f59f1e |
| q9_pK | 0.63062 | 27400 | 0.8538 | 0.76 | 0.76 | 90e8d1628e89 |
| q9_auth_kZ | 0.63032 | 27400 | 0.8442 | 0.65 | 0.71 | 30f9a43d472b |
| q9_pool_kD | 0.63002 | 27400 | 0.8523 | 0.78 | 0.71 | 07aad66d6a7e |
| q9_auth_kD | 0.63002 | 27400 | 0.8526 | 0.78 | 0.71 | 611919216358 |
| q9_gK | 0.62942 | 27400 | 0.8538 | 0.76 | 0.76 | 2c6d1e130fca |
| q9_tKO_pcv | 0.61204 | 27400 | 0.8520 | 0.78 | 0.71 | 60ec3a682e73 |

### p7 (main 23322b0 0.62882)

| variant | ratio | bytes | skeleton | 0x3c34 | 0x42e5 | sha |
|---|---:|---:|---:|---:|---:|---|
| p7_t_uK_payer | 0.62882 | 27400 | 0.8535 | 0.78 | 0.71 | 74617479b768 |
| p7_t_uK_quote_mint | 0.62882 | 27400 | 0.8535 | 0.78 | 0.71 | 74617479b768 |
| p7_t_uK_token_progra | 0.62882 | 27400 | 0.8535 | 0.78 | 0.71 | 74617479b768 |
| p7_t_uK_system_progr | 0.62882 | 27400 | 0.8535 | 0.78 | 0.71 | 74617479b768 |
| p7_t_uK_coin_creator | 0.62882 | 27400 | 0.8535 | 0.78 | 0.71 | 74617479b768 |
| p7_t_uK_coin_creator | 0.62882 | 27400 | 0.8535 | 0.78 | 0.71 | 74617479b768 |
| p7_t_uK_coin_creator | 0.62882 | 27400 | 0.8535 | 0.78 | 0.71 | 74617479b768 |
| p7_t_uK_pump_creator | 0.62882 | 27400 | 0.8535 | 0.78 | 0.71 | 74617479b768 |
| p7_t_uK_pump_creator | 0.62882 | 27400 | 0.8535 | 0.78 | 0.71 | 74617479b768 |
| p7_t_uK_event_author | 0.62882 | 27400 | 0.8535 | 0.78 | 0.71 | 74617479b768 |
| p7_t_uKO_token_progra | 0.62792 | 27400 | 0.8529 | 0.78 | 0.71 | 7803365a1c12 |
| p7_t_uKO_pump_creator | 0.62762 | 27400 | 0.8529 | 0.78 | 0.71 | 21cc29a44afe |
| p7_t_uKO_system_progr | 0.62732 | 27400 | 0.8535 | 0.78 | 0.71 | 9826f58a431c |
| p7_t_uKO_coin_creator | 0.62672 | 27400 | 0.8529 | 0.78 | 0.71 | 443cc8fa9768 |
| p7_t_uKO_coin_creator | 0.62672 | 27400 | 0.8529 | 0.78 | 0.71 | 1c6c59292c51 |
| p7_t_uKO_event_author | 0.61923 | 27400 | 0.8532 | 0.78 | 0.71 | 9c95f67b5986 |
| p7_p_uK_payer | 0.61548 | 27648 | 0.8475 | 0.78 | 0.71 | dd29b37398ec |
| p7_p_uKO_payer | 0.61548 | 27648 | 0.8475 | 0.78 | 0.71 | 8afb9cecefb5 |
| p7_t_uKO_coin_creator | 0.60905 | 27400 | 0.8529 | 0.78 | 0.71 | 2c92de42628c |
| p7_t_uKO_pump_creator | 0.60845 | 27400 | 0.8529 | 0.78 | 0.71 | e0d22f5ea773 |
| p7_t_uKO_quote_mint | 0.59107 | 27400 | 0.8517 | 0.78 | 0.71 | 53f2bcda590c |
| p7_t_uKO_payer | 0.58149 | 27400 | 0.8484 | 0.78 | 0.71 | e38b5dafd31a |
| p7_p_uK_program | 0.55690 | 27632 | 0.8424 | 0.75 | 0.63 | 42e47f0eb5be |
| p7_p_uKO_program | 0.55690 | 27632 | 0.8424 | 0.75 | 0.63 | c952017da1f6 |
| p7_p_uK_pool_authori | 0.55147 | 27696 | 0.8405 | 0.75 | 0.62 | 82644e04e275 |
| p7_p_uK_event_author | 0.55133 | 27680 | 0.8410 | 0.75 | 0.63 | 044c6fa4471b |
| p7_p_uKO_event_author | 0.55133 | 27680 | 0.8410 | 0.75 | 0.63 | ec53ef68745d |
| p7_p_uKO_pool | 0.55117 | 27696 | 0.8405 | 0.75 | 0.62 | 89b4b0582c42 |
| p7_p_uK_system_progr | 0.55104 | 27680 | 0.8407 | 0.75 | 0.63 | a4a7a494c974 |
| p7_p_uKO_system_progr | 0.55104 | 27680 | 0.8407 | 0.75 | 0.63 | c590c26b0e34 |
| p7_p_uK_pool | 0.55101 | 27712 | 0.8402 | 0.75 | 0.62 | ca0a804a95f6 |
| p7_p_uK_global_confi | 0.55047 | 27648 | 0.8406 | 0.75 | 0.62 | 180928e5d102 |
| p7_p_uKO_global_confi | 0.55047 | 27648 | 0.8406 | 0.75 | 0.62 | 0867f4bb82dd |
| p7_p_uKO_pool_authori | 0.55041 | 27712 | 0.8405 | 0.75 | 0.63 | 66eda318c4c5 |

### p6 (main 23322b0 0.62882)

| variant | ratio | bytes | skeleton | 0x3c34 | 0x42e5 | sha |
|---|---:|---:|---:|---:|---:|---|
| p6_uK_auth | 0.62882 | 27400 | 0.8535 | 0.78 | 0.71 | 74617479b768 |
| p6_uK_shar | 0.62882 | 27400 | 0.8535 | 0.78 | 0.71 | 74617479b768 |
| p6_auKO_puK | 0.62882 | 27400 | 0.8550 | 0.76 | 0.76 | 90f4f71cc7ad |
| p6_even_DL | 0.62882 | 27400 | 0.8547 | 0.87 | 0.64 | 1d05eba97227 |
| p6_glob_WSRLDOEK | 0.62882 | 27400 | 0.8535 | 0.78 | 0.71 | 8e00216e3cf0 |
| p6_glob_SWRLDOKE | 0.62882 | 27400 | 0.8535 | 0.78 | 0.71 | 7e13dfb7c466 |
| p6_prog_OLRSEDWK | 0.62882 | 27400 | 0.8535 | 0.78 | 0.71 | 74617479b768 |
| p6_uK_prog | 0.62871 | 27384 | 0.8469 | 0.84 | 0.55 | c26fbc461ab9 |
| p6_uKO_auth | 0.62852 | 27400 | 0.8538 | 0.74 | 0.76 | ce99722d04f1 |
| p6_uO_auth | 0.62852 | 27400 | 0.8532 | 0.78 | 0.71 | a2c81345496c |
| p6_uOK_auth | 0.62852 | 27400 | 0.8532 | 0.78 | 0.71 | a2c81345496c |
| p6_uK_pool | 0.62702 | 27400 | 0.8547 | 0.76 | 0.76 | db55890bb04d |
| p6_uK_glob | 0.62582 | 27400 | 0.8547 | 0.76 | 0.76 | d78eb676e578 |
| p6_uKO_prog | 0.62442 | 27392 | 0.8554 | 0.78 | 0.74 | c9decd074091 |
| p6_uO_prog | 0.62442 | 27392 | 0.8554 | 0.78 | 0.74 | 42b78c1ce8c7 |
| p6_uOK_prog | 0.62442 | 27392 | 0.8554 | 0.78 | 0.74 | 42b78c1ce8c7 |
| p6_uK_even | 0.61670 | 27360 | 0.8458 | 0.83 | 0.54 | 5e6449d8868e |
| p6_uKO_even | 0.61442 | 27376 | 0.8539 | 0.69 | 0.80 | 2e83f2fd1ae4 |
| p6_uO_even | 0.61442 | 27376 | 0.8539 | 0.69 | 0.80 | 3cc0c28e22df |
| p6_uOK_even | 0.61442 | 27376 | 0.8539 | 0.69 | 0.80 | 3cc0c28e22df |
| p6_uK_mint | 0.61112 | 27376 | 0.8647 | 0.75 | 0.92 | 02baa204330c |
| p6_uKO_mint | 0.61112 | 27376 | 0.8641 | 0.75 | 0.91 | f7776e3ce839 |
| p6_uO_mint | 0.61112 | 27376 | 0.8641 | 0.75 | 0.91 | e48456b88787 |
| p6_uOK_mint | 0.61112 | 27376 | 0.8641 | 0.75 | 0.91 | e48456b88787 |
| p6_uKO_pool | 0.60858 | 27336 | 0.8464 | 0.75 | 0.62 | 32522ff8a070 |
| p6_uO_pool | 0.60858 | 27336 | 0.8464 | 0.75 | 0.62 | efeba02e74dd |
| p6_uOK_pool | 0.60858 | 27336 | 0.8464 | 0.75 | 0.62 | efeba02e74dd |
| p6_uKO_shar | 0.60776 | 27408 | 0.8531 | 0.78 | 0.71 | 2494bc7034a1 |
| p6_uO_shar | 0.60776 | 27408 | 0.8531 | 0.78 | 0.71 | 84e61254e040 |
| p6_uOK_shar | 0.60776 | 27408 | 0.8531 | 0.78 | 0.71 | 84e61254e040 |
| p6_uKO_glob | 0.60212 | 27456 | 0.8433 | 0.81 | 0.54 | 9969adacf5dd |
| p6_uO_glob | 0.60212 | 27456 | 0.8433 | 0.81 | 0.54 | f46a8bc9855b |
| p6_uOK_glob | 0.60212 | 27456 | 0.8433 | 0.81 | 0.54 | f46a8bc9855b |


### n1-n3 (main 53abf28 0.62672)


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
