## Contributions

| lane | windows | source change |
|---|---|---|
| pump-hi | `0xea68`, `0xf130`, `0xca628`, `0xcf510`, `0x10a0e0`, `0x10b0b8`, `0x10c0b8`, `0x10d638`, `0x10e938`, `0x10fb38`, `0x1100f8`, `0x110d40`, `0x1113c8`, `0x112220`, `0x1133c8`, `0x113f00`, `0x114d48`, `0x116718`, `0x118360`, `0x119c50`, `0x1255a8`, `0x12a4e0`, `0x12abc8`, `0x137fc0`, `0x163ea8`, `0x17c0f0` | Round37-aware tools/apply_lane_changes.py --with-cpi-7 --with-fee-8 (items already in Round37 are skipped; Round37's own idls/pump_fees.json and pump_fees client are kept): const-generic legacy buy, SetMayhemVirtualParams layout and handler, declare_program!(pump_amm) generated CPI clients (migrate_v2 keeps its hand-built CPIs to stay within the 4 KiB SBF frame), collect_coin_creator_fee client built inside `if !frozen`. That lane reports the 44-suite corpus passing for the equivalent Round36 H7 candidate. Plus migrate_v2::required_quote_account_len rewritten as an #[inline(never)] TLV walk with a u64 seen-bitset (+0x17c0f0); duplicate TLV entries are skipped exactly as the original does, and the lane reports the migrate_v2 suite at 827/827. |
| pump-mid | `0xdd700` | CurveHop constraint compares quote_mint.key()==bonding_curve.quote_mint. |
| pump-lo | `0x2a8e8` | CollectCreatorFeeV2: exported creator-fee collector taking system_program as &AccountInfo (no argument promotion) and emitting the event by reference. That lane independently reproduced the nearmiss changes below (its p02-p04). |
| nearmiss | `0x340`, `0x3b598`, `0x3b738`, `0x8cc58` | require_gt! operand bound before the macro; exported native-payment helpers (external linkage blocks ArgumentPromotion); v2 rent helper keeps an unused leading argument and uses the shared transfer. |
| nearmiss2 | `0xa23f0` | u128 numerator via checked_add(..).ok_or(Overflow)? before checked_mul. |
| libinst | `0x95610`, `0x184e38`, `0x18fc98`, `0x1905a8` | MigrateV2 harvests withheld Token-2022 fees through a pub wrapper around anchor_spl::token_2022_extensions::harvest_withheld_tokens_to_mint. |
| hostid | (raw/order only) | Removes two constructs the original does not contain: runtime pubkey! base58 decoding in create_v2::execute (now consts on the existing MAYHEM_ID line) and u128 Display formatting from a require_gt! on a u128 operand in trade_v3.rs (narrowed with the file's narrow()). The library region then has exactly the original's function set and order: +29 raw windows, no normalized change. |
| libnear3 | `0x524f0`, `0x109488` | migrate's boost_enabled helper reads pump_amm's GlobalConfig through the declare_program! generated try_deserialize + map_or, with the IDL GlobalConfig field set of the older official pump_amm IDL (ending at boost_enabled), which is what the original's deserializer reads. |
| layout-integrator (genuine steps only) | `0x95f38`, `0x96280`, `0x96d48`, `0x970f8`, `0x97580` | Genuine (no-padding) source-structure steps recovered from the coordinate lanes: native transfers moved to their original helper (move_native, x2) and signer seeds built inline (x3). |
| bodyloB | `0x56658` | migrate_v2::refund_pool_authority builds its signer seeds as one nested temporary passed to an inlined transfer closure, giving the original frame order and loading system_program after the seeds. |
| pump-hi (feature) | `0xc5650` | anchor-lang built with its `allow-missing-optionals` feature: the original DistributeFeeToHolders::try_accounts constructs AccountNotEnoughKeys twice (not three times), i.e. missing trailing optional accounts deserialize to None. Crate-wide behaviour equals the original; that lane reports 43 public suites passing. |
| bodyloB (transfer helpers) | `0x8c2d8`, `0x8e908`, `0x90e60`, `0x91690`, `0x92820`, `0x93898` | transfer_checked / native-transfer helpers with the original parameter shapes (e.g. authority &&Signer, zero guard inside), each wired to its original caller's counterpart; ported by the integrator onto the legacy buy/sell bodies that the coordinate lanes moved into lib.rs. |
| coordinate lanes (genuine steps) | (see integ-genuine README) | Genuine source-structure steps (no padding): original item order in lib.rs, legacy buy/sell bodies inline in the #[program] handlers with per-site closures, buy_v2 split into the original's two handlers, inline Overflow/Truncation closures at the original sites, validate_trade allow-first argument order, native transfers through their original helper, inline signer seeds. |

Lanes `pump-hi`, `pump-mid` and `pump-lo` are the parallel Claude session's. The others are this session's workflow lanes; the coordinate lanes' work was recovered from their transcripts after a machine restart wiped their scratch directories, then re-applied to Round37 by the integrator (its notes are below). Every change keeps the original's observable behaviour.

## Toolchain note

With the official Linux x86_64 v1.44 target libraries for `sbpf-solana-solana` (PR #307), this same source reaches **880 / 1,035 normalized**. The packaged ELFs use the repository builder's `linux-v1.44-sbf` profile.

## SYNTHETIC LINE POSITIONING (read this first)

Most of this packet's gains over the genuine composite rely on a **layout device**: blank or `// layout-pad...` comment lines, and token-preserving line joins, placed so that each `error!`/`require!` Source site lands on the line the original binary records. The original's per-site `Source {file, line}` immediates are the evidence. **The padding is not recovered source text.** Every code change underneath it is a genuine source-form change, and the genuine-only subset is published separately. `tools/` holds the re-runnable pipeline that rebuilds this tree from the Round37 genuine base (`tools/pipeline_r37.sh`), which places each site on its original line.

## Integrator notes

# integ-layout-r37-03: layout composite on the Round37 genuine base r37g5

Base: W/integ/r37g5/src (788 / 165 vs W/base/round37/inventory.json). Result (fastbuild identity recipe):
**880 normalized / 165 raw = +92 vs r37g5 (+131 vs Round37 749), no losses and no
raw losses vs r37g5 and vs integ-layout-r37-02, runtime_valid = true.** Supersedes integ-layout-r37-02.

| source of the gain | windows vs r37g5 |
|---|---|
| bodyloB-04 | 7 |
| coordfiles | 43 |
| coordlib | 18 |
| coordlib/changes4 | 13 |
| coordlib/nearmiss2 | 1 |
| nearmiss2 | 9 |
| pump-hi | 1 |

Genuine (gained by the unpadded build): 0x56658, 0x8c2d8, 0x8e908, 0x90e60, 0x91690, 0x92820, 0x93898, 0x95f38, 0x96280, 0x96d48, 0x970f8, 0x97580, 0xc5650.
Synthetic-layout-dependent (79): all other gains (their code changes are genuine; matching also needs the pads/joins).

## Pipeline (re-runnable: `tools/pipeline_r37.sh W/integ/r37g5/src <out> <unpadded build dir>`)
1. coordfiles genuine steps: `tools/cf/structural37.py` = coordfiles' final structural.py with S7 skipped (Round37 already
   split the distribution handlers its own way; S7 only pre-positioned sites), then closures.py, split_buy_v2.py,
   closures2..8.py unchanged.
2. coordlib genuine steps: restructure.py; `tools/changes2_r37.py` = changes2.py section B only (validate_buyback_fee_recipient;
   A is obsolete on Round37, C/D are in r37g5); changes3.py; changes4.py (legacy `buy` non-exact path and `sell` body inline
   in the #[program] handlers with per-site closures; coordlib's last, undelivered step, recovered from its transcript).
3. nearmiss2 genuine steps (`tools/nm2_r37.py`): validate_trade(u8,u64,u64) allow-first, add3/sub3, move_native (the legacy
   sell payouts in the lib.rs sell handler), inline signer seeds in transfer_to_user/owned/recipient.
4. Round-3 lanes and pump-hi (`tools/round3.py`, all r37g4-based, ported by hand):
   - pump-hi: Cargo.toml anchor-lang features += `allow-missing-optionals` (missing trailing optional accounts become None,
     so DistributeFeeToHolders::try_accounts builds AccountNotEnoughKeys only twice: 0xc5650).
   - bodyloB-04 (cumulative): refund_pool_authority seeds (0x56658); transfer helpers with the original parameter shapes
     (user_quote_payments::transfer_native_unchecked / transfer_native_curve_unchecked in lib.rs, collect_v2::
     transfer_vault_tokens / transfer_user_tokens_ref / transfer_user_quote_tokens, token_transfers::
     transfer_curve_tokens_ref) wired to their call sites. Its legacy buy hunks are applied to BOTH copies of the legacy
     buy body (buy.rs `execute`, still used by buy_exact_sol_in, and the lib.rs `buy` handler that coordlib's changes4
     inlined); its sell hunk to the lib.rs `sell` handler; trade_v3 buyback transfers and admin_cto pay_token as in bodyloB.
5. Unpadded build = integ-genuine-r37-03: 801 (+13 vs r37g5).
6. SYNTHETIC line positioning, applied once to the unpadded tree: coordlib `tools/cl/layout.py apply --cand <unpadded
   build>` (lib.rs only; marker `// layout-pad: aligns the next Source site with the original lib.rs line`); coordfiles:
   site map re-derived from the fresh unpadded build (`tools/cf/mksitemap.py`, saved under tools/), `tools/merge_sitemap.py`
   (hand-written anchors win for their windows: an unpadded build pairs same-shape Overflow closures with the wrong
   instance), `tools/cf/layout.py apply --sitemap merged --sitemap extra_anchors.json --sitemap integ_anchors.json` (all other
   files; marker `// layout-pad(N): ...`, token-preserving joins in trade_v3.rs). integ_anchors.json: add3 :285, sub3 :294,
   0x4bf50 migrate_v2.rs:326. The coordfiles pass must be applied to the unpadded tree (re-applying it on its own output
   joins more trade_v3.rs lines); the coordlib pass is idempotent.
7. Padded build = integ-layout-r37-03: 880.

## Not carried over / unresolved
- 0x1159d8 (FeeConfig::try_deserialize_unchecked): on Round37 FeeConfig::deserialize_reader has three callers (FeeConfig
  try_deserialize_unchecked, RouteFeeConfig, trade::buy_exact_quote), so it stays out of line; needs genuine work on
  Round37's other FeeConfig readers.
- coordfiles S7 not re-applied on Round37; libinst2-01 not integrated (nested crate needs a harness change); no bodyloA
  delivery yet.

## Recovery note
Lane tools were re-created from the lane transcripts (recover/tx_sandbox.py, recover/tx_segments.py), see PROGRESS.md.
