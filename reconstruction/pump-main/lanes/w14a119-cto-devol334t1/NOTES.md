# w14a119-cto-devol334t1: remove the line-334 `read_volatile(holder_key)` placeholder (admin_cto::execute, 0x22a10)

Continuation of w14a95-cto-devol334 (#3498). Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Base main ebe5387
(M 2,247, 0.67316, 3,123 slots). Ledger approach `devol334t1`, keys `0x22a10-w14-ebe5387-devol334t1-<variant>-v1`.
All numbers come from the raw-IR oracle (capraw identity capture, then opt -O3 and llc; stitch13 `scr.py` as `tools/scr2.py`).
`m0` reproduces main exactly (`eq_main` true). M is the count of matched masked tokens, and
ratio = 2M/(6676+(bytes-27400)/8). To tie main without the placeholder, a variant needs 27,400 B and M >= 2,247.

## Result: negative. No zero-loss replacement was found at 27,400 B.

- `vol334_back + I6` (inline-L339-6: `target=a.bonding_curve.creator;(false,Some(args.0),true)`) gives **27,408 B and M 2,247**,
  so it ties main's M with no placeholder but is +8 B. It replaces the placeholder's `ldxb` with a register copy at the
  0x600 test (`ldxdw r2,[r10-0x940]; mov64 r1,r2`) plus a reload `ldxdw r2,[r10-0x940]` in the shared arm.
- The planned t1 mechanism fails: on top of I6 + vol334_back, t1 is **-40 B** (X: 27,368, M 2,244), not -24, because
  I6 becomes a no-op under t1 (I6+t1 = t1 = 27,376, M 2,246). Reaching 27,400 from X needs +32 B.
- `vol334_back + I6s` (`target=st.creator;(false,Some(args.0),true)`) lands **exactly at 27,400 B with no placeholder,
  M 2,244 (0.67226, 3,124 slots)**: -3 M against main. This is the closest faithful candidate. It needs a 0-byte change
  worth +3 M. The 0-byte k_*/cb* key-local family from #3495, applied on I6s, was queued (`S_*` rows in `s5.txt`), but the
  machine load (load average about 120, captures taking 75-95 min) stopped it before any of them finished.
- Every -8 B partner for VI6 that I tried costs 5-27 M (table). As w14a95 found on B1, -8 knobs outside validate cost M.

## Deletion map (tools/delmap.py, new oracle)

`delmap.py fn.bin out.json` deletes each single 8-byte non-jump instruction in turn, re-fixes the jumps, and reports M. On VI6, 112
deletions keep M 2,247, and all of them except 0x15b0 and 0x1678 lie in 0x0-0x620 (entry and validate head). The VI6 `mov64 r1,r2` at
0x608 is one of them. A source change that removes that copy, for example by making the 0x940 value not live into the shared arm,
would tie main at 27,400 with no placeholder. A -8 B change anywhere after 0x620 costs at least 1 M, because jump encodings
shift. That explains why the late knobs (cu_*, nf_*, n_*, sh_*) all lose.

## Screen (ebe5387)

| variant | genes | bytes | dB | M | dM |
| --- | --- | ---: | ---: | ---: | ---: |
| VI6 | `vol334_back+I6` | 27408 | +8 | 2247 | +0 |
| X | `vol334_back+I6+t1` | 27368 | -32 | 2244 | -3 |
| XP | `vol334_back+I6p+t1` | 27368 | -32 | 2244 | -3 |
| I6t1 | `I6+t1` | 27376 | -24 | 2246 | -1 |
| m0 | `-` | 27400 | +0 | 2247 | +0 |
| A_cu_match | `vol334_back+I6+cu_match` | 27400 | +0 | 2241 | -6 |
| A_ev_reset_early | `vol334_back+I6+ev_reset_early` | 27400 | +0 | 2242 | -5 |
| A_ur5r | `vol334_back+I6+ur5r` | error | | | |
| A_wl_writ_not2 | `vol334_back+I6+wl_writ_not2` | error | | | |
| A_sm_iflet | `vol334_back+I6+sm_iflet` | 27400 | +0 | 2242 | -5 |
| A_lf_pr | `vol334_back+I6+lf_pr` | 27400 | +0 | 2236 | -11 |
| A_t3 | `vol334_back+I6+t3` | 27368 | -32 | 2244 | -3 |
| A_I6s | `vol334_back+I6s` | 27400 | +0 | 2244 | -3 |
| A_ur9l | `vol334_back+I6+ur9l` | 27400 | +0 | 2241 | -6 |
| A_ur3o | `vol334_back+I6+ur3o` | 27400 | +0 | 2237 | -10 |
| A_ur9d | `vol334_back+I6+ur9d` | 27408 | +8 | 2247 | +0 |
| A_ur3d | `vol334_back+I6+ur3d` | 27408 | +8 | 2247 | +0 |
| A_cu_iflet_old | `vol334_back+I6+cu_iflet_old` | 27416 | +16 | 2229 | -18 |
| A_amp_inline | `vol334_back+I6+amp_inline` | 27392 | -8 | 2240 | -7 |
| A_r_inl | `vol334_back+I6+r_inl` | 27392 | -8 | 2220 | -27 |
| A_K_cu_fee_replace | `vol334_back+I6+K_cu_fee_replace` | 27400 | +0 | 2232 | -15 |
| A_nf_back | `vol334_back+I6+nf_back` | 27384 | -16 | 2239 | -8 |
| A_ev_nf_inline | `vol334_back+I6+ev_nf_inline` | 27384 | -16 | 2239 | -8 |
| A_n_andthen | `vol334_back+I6+n_andthen` | 27384 | -16 | 2237 | -10 |
| A_n_ensmatch | `vol334_back+I6+n_ensmatch` | 27384 | -16 | 2237 | -10 |
| A_K_cu_typed | `vol334_back+I6+K_cu_typed` | 27376 | -24 | 2234 | -13 |
| A_K_sh_prog_let | `vol334_back+I6+K_sh_prog_let` | 27376 | -24 | 2235 | -12 |
| A_K_g_s7_dborrow | `vol334_back+I6+K_g_s7_dborrow` | 27328 | -72 | 2233 | -14 |
| A_K_ev_reset_shared | `vol334_back+I6+K_ev_reset_shared` | 27280 | -120 | 1969 | -278 |
| A_ev_reset_m | `vol334_back+I6+ev_reset_m` | 27408 | +8 | 2247 | +0 |
| A_sh_iflet | `vol334_back+I6+sh_iflet` | 27400 | +0 | 2242 | -5 |
| A_sk_inl | `vol334_back+I6+sk_inl` | 27352 | -48 | 2077 | -170 |
| A_sk_inl2 | `vol334_back+I6+sk_inl2` | 27072 | -328 | 1797 | -450 |
| A_sk_ref | `vol334_back+I6+sk_ref` | 27072 | -328 | 1797 | -450 |
| A_sk_ref2 | `vol334_back+I6+sk_ref2` | 27408 | +8 | 2247 | +0 |
| A_hk_copy | `vol334_back+I6+hk_copy` | 27408 | +8 | 2247 | +0 |
| A_su_hold | `vol334_back+I6+su_hold` | 27408 | +8 | 2247 | +0 |
| A_su_ns | `vol334_back+I6+su_ns` | 27408 | +8 | 2247 | +0 |
| A_v_hkclone | `vol334_back+I6+v_hkclone` | 27408 | +8 | 2247 | +0 |
| A_x_cr_curve | `vol334_back+I6+x_cr_curve` | 27240 | -160 | 1725 | -522 |
| A_x_hr_curve | `vol334_back+I6+x_hr_curve` | 27408 | +8 | 2247 | +0 |
| A_pargs_hr_local | `vol334_back+I6+pargs_hr_local` | error | | | |
| A_x_cb_curve | `vol334_back+I6+x_cb_curve` | 27408 | +8 | 2247 | +0 |
| A_pargs_tgt_curve | `vol334_back+I6+pargs_tgt_curve` | 27560 | +160 | 1829 | -418 |
| A_tl_nf_late | `vol334_back+I6+tl_nf_late` | 27392 | -8 | 2233 | -14 |
| A_tl_a_before_block | `vol334_back+I6+tl_a_before_block` | 27408 | +8 | 2247 | +0 |
| A_w_bump_a | `vol334_back+I6+w_bump_a` | 27408 | +8 | 2247 | +0 |
| C_I6b | `vol334_back+I6b` | 27408 | +8 | 2247 | +0 |
| C_I6sn | `vol334_back+I6sn` | 27360 | -40 | 1603 | -644 |

## Next

1. On `vol334_back+I6s` (27,400, M 2,244), run the 0-byte families: `S_*` in `s5.txt` (k_*/cb*/crl*/v_uo* from #3495's
   mine.py), plus validate spellings from w14a73 autospell. The target is +3 M.
2. On VI6 (27,408), look for a validate- or entry-region spelling that kills the 0x608 register copy (-8 B, free per delmap).
3. Hsw/Hsw6 (shared arm `if !holder` first), I6sb, and I6s+T1s/T3s are defined in `tools/genes_x.py` but were not measured.

Tools need stitch13's `tools/` (rx.py, capraw.py, genes*.py from `$C/lanes/w14a109-cto-stitch13/tools`) next to them.
