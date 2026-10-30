# pump_amm GlobalConfig setters: fee bounds, recipient checks and legacy account lengths

## Question

The `amm-multi-hop-*` packets change GlobalConfig only as setup inside trade chains.
The admin-setters chain packet covers `update_fee_config` only with lp 1001 and
descending recipients, and no packet runs `create_config` past its signer check.
This packet measures the eleven GlobalConfig setters on their own:

- `create_config` with the fixed admin `8LWu7QM2dGR1G8nKDHthckea57bkCzXyBTAKPJUBDHo8`.
  The source comment at `programs/pump-amm/src/instructions/admin/create_config.rs:8`
  says this success path is "unvalidated". It is run here with signature checks off.
- `update_fee_config`: each bps bound at 1000 and 1001, plus zero, duplicate and
  unsorted fee recipients, and the order in which the checks run.
- `update_creator_fee_config` and `set_boost_authority`. Both call
  `extend_global_config` (`instructions/admin/mod.rs:16`): if the account is shorter
  than 949 bytes, the admin tops up the rent and the account is reallocated to 949.
- `update_fee_config`, `disable` and `update_admin` on the legacy GlobalConfig lengths
  that the program still deserializes (`state.rs:46-56`). A 907-byte account has an
  899-byte body. A 940-byte account has a 932-byte body. The packet also uses 948,
  the neighbours 906 and 950, and the current length 949.
- `toggle_boost`, `toggle_mayhem_mode`, `toggle_cashback_enabled`,
  `update_buyback_config` and `set_reserved_fee_recipients` on legacy and current
  lengths.
- The `disable` bit layout, and `update_admin` hand-over sequences.

Every step runs on the original image and on the rebuild. For each step the packet
records the error, the compute units, the full logs and the post-state: GlobalConfig
bytes, length and lamports, and the lamports of the admin, the outsider and the fixed
admin.

Images:

| role | sha256 | provenance |
|---|---|---|
| original | `6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7` | `evidence/original/pump_amm/deployed.so` |
| candidate | `384737bdc6c54cca4330fd5ce15f8c556a40a78afa6a93a69fe47d2b18527ab5` | `scripts/build_partial_candidate.py`, platform-tools v1.44 / cargo-build-sbf 2.1.21, source tree `755200a0d9fffe6f82a43fb65cc452d164f6e90b` (repo commit `1e04f5b34aa33c53f2b20b4200ba4ba266b4203e`) |
| control | `f470afd6b3fd0c9091a5814e1ed6c281f38b548770d735adfdaa1eb4e3af1e24` | derived in memory from the original by `strip_prefix()` (245 sites patched), not stored |

## Setup

- There are no captured fixtures and no RPC. `producer.py` writes a synthetic
  GlobalConfig at its `["global_config"]` PDA. Every field has a recognisable value:
  lp 20, protocol 5, creator 5, buyback 5000, boost authority `0x70`×32,
  `creator_fee_configurable` 1, max 300. The account is cut or padded to the case
  length, and its lamports equal the rent minimum for that length unless the case
  says otherwise.
- The admin and outsider keypairs come from fixed seeds. The clock is fixed at unix
  time 1234567890. Each case uses a fresh `LiteSVM` (solders 0.27.1) that holds only
  the pump_amm image.
- The fixed admin cannot sign, so `create_config` cases use `with_sigverify(False)`,
  with the fixed admin as an unsigned fee payer. The `*-admin-readonly-nonpayer` cases
  also turn signature checks off. In those cases the outsider pays and the admin is a
  read-only signer, as in the IDL's `set_boost_authority` account list.
- The control image is the original with every `programs/pump-amm/src/*.rs` reference
  moved past the 18-byte `programs/pump-amm/` prefix, with the length immediate
  lowered by 18. This is the same control as in `pump-amm-liquidity-rounding-boundaries-20261030`.

## Result

60 cases, 65 steps.

| measure | value |
|---|---|
| steps with the same error + config bytes + lamports + tx bytes (original vs rebuild) | 65 / 65 |
| steps with byte-identical logs | 51 / 65 |
| steps with identical logs after `programs/pump-amm/src/` → `src/` | 65 / 65 |
| steps with equal CU | 51 / 65 |
| CU delta histogram (rebuild − original) | 0: 51, −18: 13, −122: 1 |
| control steps equal to the rebuild (behaviour, logs, CU) | 65 / 65 |

**The original and the rebuild behave identically on every step.** The only
differences are in CU and in the AnchorError file name:

- −18 CU on 13 steps that fail in a `require!` / `require_gte!`. These are
  `state/global_config.rs` lines 220, 230 and 243 (`FeeBasisPointsExceedsMaximum`,
  6000), 256 (`AllProtocolFeeRecipientsShouldBeNonZero`, 6011), 263
  (`UnsortedNotUniqueProtocolFeeRecipients`, 6012) and 306
  (`BuybackBasisPointsOutOfRange`, 6056), plus
  `instructions/admin/set_reserved_fee_recipients.rs:40` (6044).
- −122 CU on 1 step: `tb-len907`, `require_keys_neq!` at
  `instructions/admin/toggle_boost.rs:14` (6005, CU 4439 → 4317). This macro also
  logs `Left:` / `Right:` and both pubkeys. Those log lines are identical in the two
  images.

The original logs `programs/pump-amm/src/<file>:<line>` and the rebuild logs
`src/<file>:<line>`. The line numbers are the same.

18 = `len("programs/pump-amm/")`. `programs/pump-amm/Cargo.toml` has its own
`[workspace]`, so in the `build_partial_candidate` rebuild `file!()` is
crate-relative. The control image only shortens those strings, and it reproduces the
rebuild's CU and logs on 65 / 65 steps. That includes the −122 step, where the control
also costs 4317 CU. So the 104 CU beyond the 18-byte length on the
`require_keys_neq!` path also comes only from the longer file-name string. It is not a
code difference. No other code difference shows up on these paths. Failures that log
no file name show no CU difference: Anchor account constraints (2000, 3010, and 6005
on `has_one` / `address`), `InvalidAccountData`, `BorshIoError`,
`PrivilegeEscalation` and the system-program "already in use" error.

### Per-step table (original image; the rebuild differs only where Δ ≠ 0)

| case | step | outcome | site | CU orig | CU rebuild | Δ | config len after | config lamports after |
|---|---|---|---|---|---|---|---|---|
| cc-ok | 0 | ok | | 21598 | 21598 | 0 | 949 | 7495920 |
| cc-lp-1001 | 0 | 6000 | global_config.rs:220 | 13439 | 13421 | −18 | – | – |
| cc-proto-1001 | 0 | 6000 | global_config.rs:230 | 13461 | 13443 | −18 | – | – |
| cc-creator-1001 | 0 | 6000 | global_config.rs:243 | 13943 | 13925 | −18 | – | – |
| cc-recipient0-zero | 0 | 6011 | global_config.rs:256 | 12329 | 12311 | −18 | – | – |
| cc-recipients-dup | 0 | 6012 | global_config.rs:263 | 12652 | 12634 | −18 | – | – |
| cc-creator1001-and-zero-recip | 0 | 6011 | global_config.rs:256 | 12329 | 12311 | −18 | – | – |
| cc-twice | 0 / 1 | ok / system Custom(0) "already in use" | | 21598 / 5907 | same | 0 | 949 | 7495920 |
| cc-then-update | 0 / 1 | ok / ok | | 21598 / 16071 | same | 0 | 949 | 7495920 |
| cc-non-fixed-admin | 0 | 6005 | account: admin | 10820 | 10820 | 0 | – | – |
| cc-over-existing | 0 | system Custom(0) | | 5907 | 5907 | 0 | 949 | 7495920 |
| ufc-ok | 0 | ok | | 16075 | 16075 | 0 | 949 | 7495920 |
| ufc-all-bps-1000 | 0 | ok | | 16075 | 16075 | 0 | 949 | 7495920 |
| ufc-lp-1001 | 0 | 6000 | global_config.rs:220 | 7913 | 7895 | −18 | 949 | 7495920 |
| ufc-proto-1001 | 0 | 6000 | global_config.rs:230 | 7936 | 7918 | −18 | 949 | 7495920 |
| ufc-creator-1001 | 0 | 6000 | global_config.rs:243 | 8420 | 8402 | −18 | 949 | 7495920 |
| ufc-recipient-zero-mid | 0 | 6011 | global_config.rs:256 | 6899 | 6881 | −18 | 949 | 7495920 |
| ufc-recipients-dup-last | 0 | 6012 | global_config.rs:263 | 7209 | 7191 | −18 | 949 | 7495920 |
| ufc-non-admin | 0 | 6005 | account: global_config | 5353 | 5353 | 0 | 949 | 7495920 |
| ucfc-ok | 0 | ok | | 11872 | 11872 | 0 | 949 | 7495920 |
| ucfc-non-admin | 0 | 6005 | account: global_config | 5265 | 5265 | 0 | 949 | 7495920 |
| ucfc-len907 | 0 | ok | | 14270 | 14270 | 0 | 949 | 7495920 |
| ucfc-len907-prefunded | 0 | ok | | 12277 | 12277 | 0 | 949 | 7495920 |
| ucfc-len940 | 0 | ok | | 14355 | 14355 | 0 | 949 | 7495920 |
| ucfc-len948 | 0 | ok | | 14355 | 14355 | 0 | 949 | 7495920 |
| ucfc-len906 | 0 | InvalidAccountData | account: global_config | 2991 | 2991 | 0 | 906 | 7196640 |
| ucfc-len950 | 0 | ok | | 11872 | 11872 | 0 | 950 | 7502880 |
| ucfc-len907-admin-readonly-nonpayer | 0 | 2000 (ConstraintMut) | account: admin | 4632 | 4632 | 0 | 907 | 7203600 |
| ucfc-len907-then-ufc | 0 / 1 | ok / ok | | 14270 / 16074 | same | 0 | 949 | 7495920 |
| sba-len907 | 0 | ok | | 15172 | 15172 | 0 | 949 | 7495920 |
| sba-len948 | 0 | ok | | 15257 | 15257 | 0 | 949 | 7495920 |
| sba-len949 | 0 | ok | | 12774 | 12774 | 0 | 949 | 7495920 |
| sba-len907-admin-readonly-nonpayer | 0 | PrivilegeEscalation | | 7404 | 7404 | 0 | 907 | 7203600 |
| sba-len949-admin-readonly-nonpayer | 0 | ok | | 12776 | 12776 | 0 | 949 | 7495920 |
| ufc-len907 / dis-len907 / ua-len907 | 0 | BorshIoError | account: global_config | 19379 / 14820 / 15342 | same | 0 | 907 | 7203600 |
| ufc-len940 / dis-len940 / ua-len940 | 0 | BorshIoError | account: global_config | 19566 / 15007 / 15529 | same | 0 | 940 | 7433280 |
| ufc-len948 / dis-len948 / ua-len948 | 0 | BorshIoError | account: global_config | 19650 / 15091 / 15613 | same | 0 | 948 | 7488960 |
| ufc-len950 / dis-len950 / ua-len950 | 0 | ok | | 16075 / 11516 / 12038 | same | 0 | 950 | 7502880 |
| dis-all-true-from-e0 | 0 | ok, flags 0xE0 → 0xFF | | 11512 | 11512 | 0 | 949 | 7495920 |
| dis-all-false-from-ff | 0 | ok, flags 0xFF → 0xE0 | | 11521 | 11521 | 0 | 949 | 7495920 |
| tb-len907 | 0 | 6005 | toggle_boost.rs:14 | 4439 | 4317 | −122 | 907 | 7203600 |
| tb-len940 | 0 | BorshIoError | account: global_config | 8157 | 8157 | 0 | 940 | 7433280 |
| tb-len949 | 0 | ok | | 4668 | 4668 | 0 | 949 | 7495920 |
| tm-len907 | 0 | BorshIoError | account: global_config | 10212 | 10212 | 0 | 907 | 7203600 |
| tc-len907 | 0 | BorshIoError | account: global_config | 10227 | 10227 | 0 | 907 | 7203600 |
| bb-len907 | 0 | BorshIoError | account: global_config | 10245 | 10245 | 0 | 907 | 7203600 |
| bb-none-len949 | 0 | ok | | 6920 | 6920 | 0 | 949 | 7495920 |
| bb-10001-len949 | 0 | 6056 | global_config.rs:306 | 6424 | 6406 | −18 | 949 | 7495920 |
| srf-no-remaining-len949 | 0 | 6044 | set_reserved_fee_recipients.rs:40 | 9085 | 9067 | −18 | 949 | 7495920 |
| ua-then-old-admin | 0 / 1 | ok / 6005 | account: global_config | 12038 / 5351 | same | 0 | 949 | 7495920 |
| ua-to-default-then-old | 0 / 1 | ok / 6005 | account: global_config | 12037 / 4956 | same | 0 | 949 | 7495920 |
| ua-not-signer | 0 | 3010 | account: admin | 3014 | 3014 | 0 | 949 | 7495920 |

### Behaviour pinned (identical on both images)

1. **Check order in `create_config` / `update_fee_config`.** The checks run in this
   order: lp bps, protocol bps, fee recipients (zero first, then strictly ascending),
   creator bps. With creator bps 1001 and a zero recipient, the call fails 6011 at
   line 256, not 6000 at line 243. 1000 is accepted for all three bps fields
   (`ufc-all-bps-1000`) and 1001 is rejected.
2. **`create_config` success path.** The fixed admin pays 7,495,920 lamports of rent
   for 949 bytes plus the 5,000 fee (fixed-admin balance 999,992,499,080). The config
   stores the arguments and `disable_flags` 0. `boost_authority`, `boost_enabled`,
   `creator_fee_configurable` and `max_configurable_creator_fee_bps` stay zero. A
   second call, or a call over an existing account, fails in the system program
   (`Allocate: ... already in use`, Custom(0)). Any other signer gets 6005 on
   `admin`.
3. **Legacy lengths break the plain setters.** On a 907-, 940- or 948-byte config,
   `update_fee_config`, `disable` and `update_admin` deserialize the shorter layout,
   run the handler and emit the event CPI. On 907 bytes, `toggle_mayhem_mode`,
   `toggle_cashback_enabled` and `update_buyback_config` do the same, and so does
   `toggle_boost` on 940 bytes. At Anchor exit they then fail with
   `ProgramError caused by account: global_config. Error Code: BorshIoError("failed
   to write whole buffer")`, because the full 949-byte struct no longer fits. These
   failures cost 8,157–19,650 CU, because the whole handler runs first, and nothing
   is written. `toggle_boost` on 907 bytes fails earlier: the 899-byte layout has no
   boost authority, so it reads the default key, and
   `require_keys_neq!(boost_authority, default)` returns 6005. 906 bytes is below the deserializer floor (`InvalidAccountData`). At
   950 bytes all three setters succeed. The 950th byte is 0 in the fixture and is
   still 0 afterwards.
4. **The extend path repairs them.** `update_creator_fee_config` and
   `set_boost_authority` realloc a 907/940/948-byte config to 949. The admin pays the
   rent difference: 292,320 / 62,640 / 6,960 lamports (admin balance
   999,999,702,680 / 999,999,932,360 / 999,999,988,040 after the 5,000 fee). The
   balance after a prefunded config shows that no transfer happens when the lamports
   already cover 949 bytes (rent 7,495,920). After the extend, `update_fee_config`
   succeeds (`ucfc-len907-then-ufc`). Fields that are missing from the legacy layout
   are serialized as defaults. On 907, `ucfc` writes a default `boost_authority`. On
   907 and 948, `set_boost_authority` leaves `creator_fee_configurable` = 0 and
   max = 0.
5. **Admin writability.** The IDL lists `set_boost_authority`'s admin as read-only.
   On a 949-byte config, a read-only, non-payer admin succeeds. On a 907-byte config,
   the top-up transfer from that admin fails with `PrivilegeEscalation` ("writable
   privilege escalated"). `update_creator_fee_config` declares `#[account(mut)]`, so
   a read-only admin fails earlier with 2000 (ConstraintMut).
6. **`disable`.** Each call rewrites bits 0–4 from the five bools and keeps bits 5–7:
   0xE0 → 0xFF with all true, and 0xFF → 0xE0 with all false.
7. **Other setters on 949 bytes.** `update_buyback_config(None)` succeeds.
   10001 bps fails 6056. `set_reserved_fee_recipients` without remaining accounts
   fails 6044. `toggle_boost` succeeds when the boost authority is set.
8. **`update_admin`.** The new admin can be any key, including the default pubkey. The
   old admin then gets 6005 on `global_config`. An admin that has not signed gets 3010.

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump_amm/deployed.so", "candidate": "<candidate.so>"}' --out <packet dir>
python3 verify.py --images '{"original": "<deployed.so>", "candidate": "<candidate.so>"}'
```

`producer.py` is deterministic: two runs produce byte-identical
`runtime/receipts.jsonl.gz` and `runtime/report.json.gz`. `verify.py` runs inside the
packet folder and checks four things. MANIFEST hashes. That both image sha256 values
equal those in `report.json.gz`. That re-running all 60 cases on the original, the
rebuild and the control reproduces the stored receipts and report byte for byte. It
exits 0 on success and 1 otherwise.

Files: `runtime/receipts.jsonl.gz` holds one line per case: the case spec, plus the
full per-step record for the original and the candidate (error, CU, logs, config
bytes, lamports, tx sha256) and for the control. `runtime/report.json.gz` holds the
summary, the per-step comparison rows and the decoded final configs.
