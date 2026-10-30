# Pump Main `create_v2`: Token-2022 quote-mint extension allowlist, original vs rebuild

## Question

When `create_v2` gets a non-SOL quote mint owned by Token-2022, it checks the
mint's raw account data against a TLV allowlist before it creates the curve's
quote ATA. The check is `quote_extensions_supported(data, true)`
(`programs/pump/pump-token-ext/src/lib.rs`, called from `check_quote_mint_extensions`
in `programs/pump/src/create_v2.rs`). The check is skipped for the
`pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn` quote mint. A rejected mint stops the
instruction with `UnsupportedQuoteMint` (6063).

This packet asks whether the deployed program and the rebuild accept and reject
the same quote-mint byte layouts, and what happens next for accepted mints. It
covers every Token-2022 extension type from 1 to 27, the payload rules the parser
inspects, duplicates, mixed lists, and TLV framing.

## Setup

- Instruction: `create_v2` with the default (valid) argument set. The Global
  account is synthetic: 1,088 bytes laid out from the IDL, with `create_v2_enabled=1`
  and the quote mint in the whitelisted-quote slot. Remaining accounts are
  `[quote mint, curve quote ATA, quote token program]`.
- Only the quote mint's data varies. Its base is an initialized 82-byte mint
  (decimals 6). For TLV cases it is padded to 165 bytes, followed by
  account-type byte 1 and the TLV entries listed per case. Payload sizes follow
  the Token-2022 layouts. Payload bytes are zero unless the case says otherwise.
- Pump is loaded under the upgradeable loader, which is the mainnet program
  layout. The ATA and system programs are LiteSVM built-ins.
- Two Token-2022 configurations:
  - `builtin-token-2022`: LiteSVM's bundled Token-2022. With it, every accepted
    mint stops later at the base mint's TokenMetadata initialize CPI with
    `InvalidRealloc`. This is a LiteSVM built-in limitation, also seen in the
    earlier synthetic-Global create_v2 measurements. This configuration needs
    nothing outside the packet.
  - `mainnet-token-2022`: `evidence/dependencies/spl_token_2022/deployed.so`
    (sha256 `15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d`),
    loaded over the built-in. Accepted mints run to `success`. This also measures
    the quote-ATA creation by Token-2022 (GetAccountDataSize and
    InitializeAccount3 on the same mint bytes).
- Keys come from fixed seeds and the clock is fixed. Each case runs in a fresh
  VM, with no network. Each step uses 1,400,000 CU (SetComputeUnitLimit).
- Images:
  - original: `evidence/original/pump/deployed.so`, sha256
    `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`, 10,485,715 bytes.
  - rebuild: `candidate.so`, sha256
    `e04e3e5652e0cfbf55c6ef30533aea6084ea60432aac8a468056b0a6f19dd633`, 1,934,648 bytes.
    It was built with `scripts/build_partial_candidate.py` (platform-tools v1.44 /
    cargo-build-sbf 2.1.21) from source tree `97a2a2a383ba1bc5c5af08429de150e6124f0fc1`
    at repository commit `aba9e07e8872a53ebfdeffc7cc5bfa20714fc053`.
- Behavior fields compared per case: transaction bytes, error, return data,
  events, inner instructions, and every non-executable account after the
  transaction. Compute units and log lines are recorded and classified separately.

## Result

**60 cases × 2 Token-2022 configurations: 0 behavior mismatches.** The original
and the rebuild accept and reject exactly the same quote-mint layouts. Accepted
mints then produce the same accounts, the same Token-2022 / ATA inner
instructions and the same CreateEvent.

| | builtin-token-2022 | mainnet-token-2022 |
|---|---|---|
| `UnsupportedQuoteMint` (6063) | 38 | 38 |
| accepted → `InvalidRealloc` at the base-mint metadata CPI | 21 | - |
| accepted → `success` | - | 21 |
| SPL Token error 2 (InvalidMint) in the ATA CPI | 1 | 1 |
| behavior mismatches | 0 | 0 |
| compute units equal | 21 | 0 |
| log lines identical | 0 | 0 |

Compute units (original minus rebuild):

- **+118** on all 38 `UnsupportedQuoteMint` stops, under both configurations. The
  only differing log lines are the AnchorError site
  (`programs/pump/src/create_v2.rs:528` in the original, `src/create_v2.rs:528`
  in the rebuild) and the `consumed` lines.
- **+8** on all 21 successes under mainnet Token-2022. In the inner logs of
  `type-01`, the original's remaining budget is 1 CU lower at the first
  Token-2022 CPI and 7 CU lower at the Token-2022 CPI after the quote-ATA
  creation. Each inner program consumes the same amount on both images.
- **0** on the 21 built-in `InvalidRealloc` stops.
- **+1** on the SPL-owned case.

The CU gaps come from the program and source-path differences already recorded
for Pump Main. They do not change any behavior field.

What the parser does, as measured identically on both images:

- **Accepted single extensions:** 1 TransferFeeConfig, 4 ConfidentialTransferMint,
  6 DefaultAccountState (value 1 only), 12 PermanentDelegate, 14 TransferHook (hook
  program id all zero only), 16 ConfidentialTransferFeeConfig, 18 MetadataPointer,
  19 TokenMetadata, 25 ScaledUiAmount and 26 Pausable.
- **Rejected single extensions:** all other types from 2 to 27, including the
  account-side types 2, 5, 7, 13, 15, 17 and 27.
- **Payload rules:**
  - TransferFeeConfig with 107 bytes is rejected; 109 bytes is accepted.
  - DefaultAccountState 0, 2 or an empty payload is rejected; `01 00` is accepted.
  - TransferHook is rejected if any of the 32 program-id bytes is non-zero, even
    only the last one. It is also rejected at 63 bytes. A non-zero hook
    authority is accepted.
- **Duplicates and mixed lists:**
  - A duplicate entry is rejected.
  - A list of five allowed types is accepted.
  - A rejected type after an allowed one is rejected.
- **Framing:**
  - A plain 82-byte mint is accepted.
  - Data lengths of 83, 165 and 166 bytes are rejected. 166 bytes is a mint with
    account-type byte 1 and an empty TLV area.
  - 167 bytes is accepted, whether the last byte is 00 or ff.
  - Account-type byte 0 or 2 is rejected.
  - A non-zero padding byte at offset 82 or 164 is rejected.
  - A type-0 entry ends the scan, so a MintCloseAuthority entry placed after it
    is accepted.
  - One trailing byte after the last entry is accepted; three trailing bytes are
    rejected.
  - A length field one byte past the data is rejected, and so is type 64.
- **Mints the check does not read:**
  - The `pumpCm…` quote mint is accepted with a MintCloseAuthority entry, and
    also with a non-zero TransferHook program id.
  - An SPL-Token-owned 202-byte mint is not checked by Pump. It fails in SPL
    Token `GetAccountDataSize` ("Invalid Mint", error 2) during the ATA CPI.
- **Mainnet Token-2022 accepted every mint that Pump accepted.** The created
  quote ATA is 170 bytes in most cases, 182 with TransferFeeConfig, 175 with
  TransferHook, 174 with Pausable and 186 for the five-extension list.

## Relation to existing work

- `scripts/pump_create_quote_differential.py` (and `pump_create_control_differential.py`)
  contain a single-extension matrix of create_v2 quote mints: types 1–28 with
  payloads of 0/1/32/64 bytes, plus a few payload boundaries. Those scripts read
  `research/imported-lab/analysis/pump_fun/config-snapshot.json`, which is not
  in the git tree, so they do not run from a checkout. This packet is
  self-contained. It adds duplicates, mixed lists, account-type and padding
  bytes, TLV framing (type-0 terminator, trailing bytes, length overrun, type 64),
  the `pumpCm…` exemption, the SPL-owned path, and the follow-on Token-2022
  quote-ATA creation under the mainnet Token-2022 build.
- The synthetic-Global `create_v2` measurements used three Token-2022 quote
  cases (transfer-fee, non-transferable, permanent-delegate). The same three
  layouts appear here as `type-01`, `type-09` and `type-12`, with the same outcomes.
- The rest of the research/ packets for Pump Main cover trades, migrate,
  Global admin and instruction decoding. None of them varies the quote-mint TLV.

## Cases

The quote ATA bytes and CU columns come from the `mainnet-token-2022`
configuration. The `parser` column is derived from the stop. A case with any
stop other than `UnsupportedQuoteMint` got past the allowlist.

| # | case | quote-mint bytes | parser | built-in Token-2022 | mainnet Token-2022 | CU orig / rebuild (mainnet) | Δ | quote ATA bytes | behavior |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `type-01-transfer-fee-config` | single extension type 1 (transfer-fee-config), 108-byte payload | accept | InvalidRealloc (Token-2022 CPI) | success | 145062 / 145054 | +8 | 182 | match |
| 2 | `type-02-transfer-fee-amount` | single extension type 2 (transfer-fee-amount), 8-byte payload | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76147 / 76029 | +118 | - | match |
| 3 | `type-03-mint-close-authority` | single extension type 3 (mint-close-authority), 32-byte payload | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76147 / 76029 | +118 | - | match |
| 4 | `type-04-confidential-transfer-mint` | single extension type 4 (confidential-transfer-mint), 65-byte payload | accept | InvalidRealloc (Token-2022 CPI) | success | 144757 / 144749 | +8 | 170 | match |
| 5 | `type-05-confidential-transfer-account` | single extension type 5 (confidential-transfer-account), 295-byte payload | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76147 / 76029 | +118 | - | match |
| 6 | `type-06-default-account-state-initialized` | single extension type 6 (default-account-state-initialized), 1-byte payload | accept | InvalidRealloc (Token-2022 CPI) | success | 144773 / 144765 | +8 | 170 | match |
| 7 | `type-07-immutable-owner` | single extension type 7 (immutable-owner), 0-byte payload | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76147 / 76029 | +118 | - | match |
| 8 | `type-08-memo-transfer` | single extension type 8 (memo-transfer), 1-byte payload | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76147 / 76029 | +118 | - | match |
| 9 | `type-09-non-transferable` | single extension type 9 (non-transferable), 0-byte payload | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76147 / 76029 | +118 | - | match |
| 10 | `type-10-interest-bearing-config` | single extension type 10 (interest-bearing-config), 52-byte payload | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76147 / 76029 | +118 | - | match |
| 11 | `type-11-cpi-guard` | single extension type 11 (cpi-guard), 1-byte payload | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76147 / 76029 | +118 | - | match |
| 12 | `type-12-permanent-delegate` | single extension type 12 (permanent-delegate), 32-byte payload | accept | InvalidRealloc (Token-2022 CPI) | success | 144874 / 144866 | +8 | 170 | match |
| 13 | `type-13-non-transferable-account` | single extension type 13 (non-transferable-account), 0-byte payload | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76147 / 76029 | +118 | - | match |
| 14 | `type-14-transfer-hook-zero-program` | single extension type 14 (transfer-hook-zero-program), 64-byte payload | accept | InvalidRealloc (Token-2022 CPI) | success | 145130 / 145122 | +8 | 175 | match |
| 15 | `type-15-transfer-hook-account` | single extension type 15 (transfer-hook-account), 1-byte payload | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76147 / 76029 | +118 | - | match |
| 16 | `type-16-confidential-transfer-fee-config` | single extension type 16 (confidential-transfer-fee-config), 129-byte payload | accept | InvalidRealloc (Token-2022 CPI) | success | 144760 / 144752 | +8 | 170 | match |
| 17 | `type-17-confidential-transfer-fee-amount` | single extension type 17 (confidential-transfer-fee-amount), 64-byte payload | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76147 / 76029 | +118 | - | match |
| 18 | `type-18-metadata-pointer` | single extension type 18 (metadata-pointer), 64-byte payload | accept | InvalidRealloc (Token-2022 CPI) | success | 144757 / 144749 | +8 | 170 | match |
| 19 | `type-19-token-metadata` | single extension type 19 (token-metadata), 82-byte payload | accept | InvalidRealloc (Token-2022 CPI) | success | 144760 / 144752 | +8 | 170 | match |
| 20 | `type-20-group-pointer` | single extension type 20 (group-pointer), 64-byte payload | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76147 / 76029 | +118 | - | match |
| 21 | `type-21-token-group` | single extension type 21 (token-group), 80-byte payload | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76147 / 76029 | +118 | - | match |
| 22 | `type-22-group-member-pointer` | single extension type 22 (group-member-pointer), 64-byte payload | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76147 / 76029 | +118 | - | match |
| 23 | `type-23-token-group-member` | single extension type 23 (token-group-member), 72-byte payload | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76147 / 76029 | +118 | - | match |
| 24 | `type-24-confidential-mint-burn` | single extension type 24 (confidential-mint-burn), 196-byte payload | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76147 / 76029 | +118 | - | match |
| 25 | `type-25-scaled-ui-amount` | single extension type 25 (scaled-ui-amount), 56-byte payload | accept | InvalidRealloc (Token-2022 CPI) | success | 144757 / 144749 | +8 | 170 | match |
| 26 | `type-26-pausable` | single extension type 26 (pausable), 33-byte payload | accept | InvalidRealloc (Token-2022 CPI) | success | 145057 / 145049 | +8 | 174 | match |
| 27 | `type-27-pausable-account` | single extension type 27 (pausable-account), 0-byte payload | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76139 / 76021 | +118 | - | match |
| 28 | `transfer-fee-107` | TransferFeeConfig payload 107 bytes (one short) | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76155 / 76037 | +118 | - | match |
| 29 | `transfer-fee-109` | TransferFeeConfig payload 109 bytes (one extra) | accept | InvalidRealloc (Token-2022 CPI) | success | 145062 / 145054 | +8 | 182 | match |
| 30 | `default-state-0` | DefaultAccountState payload byte = 0 | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76157 / 76039 | +118 | - | match |
| 31 | `default-state-2` | DefaultAccountState payload byte = 2 | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76157 / 76039 | +118 | - | match |
| 32 | `default-state-empty` | DefaultAccountState with a 0-byte payload | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76155 / 76037 | +118 | - | match |
| 33 | `default-state-1-extra` | DefaultAccountState payload 01 00 (2 bytes) | accept | InvalidRealloc (Token-2022 CPI) | success | 144769 / 144761 | +8 | 170 | match |
| 34 | `hook-program-set` | TransferHook with a non-zero hook program id | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76159 / 76041 | +118 | - | match |
| 35 | `hook-authority-set` | TransferHook with authority set, program id zero | accept | InvalidRealloc (Token-2022 CPI) | success | 145130 / 145122 | +8 | 175 | match |
| 36 | `hook-program-last-byte` | TransferHook program id = 31 zero bytes then 01 | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76221 / 76103 | +118 | - | match |
| 37 | `hook-63` | TransferHook payload 63 bytes | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76156 / 76038 | +118 | - | match |
| 38 | `dup-metadata-pointer` | MetadataPointer twice | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76197 / 76079 | +118 | - | match |
| 39 | `dup-permanent-delegate` | PermanentDelegate twice | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76197 / 76079 | +118 | - | match |
| 40 | `combo-allowed-5` | TransferFeeConfig + PermanentDelegate + MetadataPointer + TokenMetadata + Pausable | accept | InvalidRealloc (Token-2022 CPI) | success | 146838 / 146830 | +8 | 186 | match |
| 41 | `combo-allowed-then-rejected` | MetadataPointer then MintCloseAuthority | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76192 / 76074 | +118 | - | match |
| 42 | `combo-allowed-then-bad-hook` | MetadataPointer then TransferHook with program id set | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76204 / 76086 | +118 | - | match |
| 43 | `len-82` | plain 82-byte mint (no account type, no TLV) | accept | InvalidRealloc (Token-2022 CPI) | success | 142327 / 142319 | +8 | 170 | match |
| 44 | `len-165` | 165 bytes: base + zero padding, no account-type byte | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 75614 / 75496 | +118 | - | match |
| 45 | `len-166` | 166 bytes: base + padding + account type 1, empty TLV | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 75614 / 75496 | +118 | - | match |
| 46 | `len-167` | 167 bytes: account type 1 + one zero TLV byte | accept | InvalidRealloc (Token-2022 CPI) | success | 144505 / 144497 | +8 | 170 | match |
| 47 | `len-167-nonzero` | 167 bytes: account type 1 + one 0xff byte (TLV shorter than a type field) | accept | InvalidRealloc (Token-2022 CPI) | success | 144505 / 144497 | +8 | 170 | match |
| 48 | `len-83` | 83 bytes: base + one zero byte | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 75614 / 75496 | +118 | - | match |
| 49 | `account-type-0` | account-type byte 0 + MetadataPointer | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76119 / 76001 | +118 | - | match |
| 50 | `account-type-2` | account-type byte 2 (Account) + MetadataPointer | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76119 / 76001 | +118 | - | match |
| 51 | `padding-82-set` | padding byte 82 = 1 + MetadataPointer | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 75624 / 75506 | +118 | - | match |
| 52 | `padding-164-set` | padding byte 164 = 1 + MetadataPointer | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76116 / 75998 | +118 | - | match |
| 53 | `tlv-zero-then-rejected` | type 0 entry, then MintCloseAuthority after it | accept | InvalidRealloc (Token-2022 CPI) | success | 144594 / 144586 | +8 | 170 | match |
| 54 | `tlv-trailing-3` | MetadataPointer then 3 trailing bytes 12 00 00 | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76179 / 76061 | +118 | - | match |
| 55 | `tlv-trailing-1` | MetadataPointer then 1 trailing byte 0xff | accept | InvalidRealloc (Token-2022 CPI) | success | 144874 / 144866 | +8 | 170 | match |
| 56 | `tlv-length-overrun` | MetadataPointer whose length field is 65 with 64 bytes present | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76138 / 76020 | +118 | - | match |
| 57 | `tlv-type-64` | extension type 64 (outside the u64 seen-mask) | reject | UnsupportedQuoteMint (6063) | UnsupportedQuoteMint (6063) | 76139 / 76021 | +118 | - | match |
| 58 | `pump-quote-mint-close-authority` | pumpCm... quote mint (exempt) with MintCloseAuthority | n/a (not read) | InvalidRealloc (Token-2022 CPI) | success | 148646 / 148638 | +8 | 170 | match |
| 59 | `pump-quote-hook-program` | pumpCm... quote mint (exempt) with a TransferHook program id set | n/a (not read) | InvalidRealloc (Token-2022 CPI) | success | 148954 / 148946 | +8 | 175 | match |
| 60 | `spl-owned-close-authority` | SPL-Token-owned quote mint carrying a MintCloseAuthority TLV | n/a (not read) | SPL Token 2 InvalidMint (ATA CPI) | SPL Token 2 InvalidMint (ATA CPI) | 86643 / 86642 | +1 | - | match |

## Reproduce

```
# produce (writes runtime/ deterministically; a second run gives identical bytes)
python3 producer.py --root <repo> \
  --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}' \
  --out <packet dir>

# verify from this folder: image sha256 vs report, receipt sha256, replay of every
# builtin-token-2022 case on both images, recomputed summaries
python3 verify.py --images '{"original": "<deployed.so>", "candidate": "<candidate.so>"}'

# also replay the mainnet-token-2022 receipts (sha256 of the dependency is checked)
python3 verify.py --images '{"original": "<deployed.so>", "candidate": "<candidate.so>"}' \
  --token-2022 <repo>/evidence/dependencies/spl_token_2022/deployed.so
```

Without `--token-2022`, verify.py replays all 120 built-in receipts. The 120
mainnet-configuration receipts are then only checked against their sha256 and
re-summarized. With the flag, all 240 receipts are replayed.

Requirements: Python 3 with `solders` 0.27.1 (in-process LiteSVM), no network.

## Files

- `producer.py` — case plan, execution and summary. verify.py imports the
  execution part, which does not read the repository.
- `verify.py` — the independent re-check, exit 0/1.
- `runtime/plan.json.gz` — for every case: instruction data, account metas,
  signer seeds and the full initial account set.
- `runtime/receipts-builtin-token-2022.jsonl.gz`,
  `runtime/receipts-mainnet-token-2022.jsonl.gz` — one receipt per case and
  image: transaction, error, logs, compute units, events, inner instructions
  and after-state.
- `runtime/report.json.gz` — image hashes, the Token-2022 dependency hash,
  receipt hashes and per-case summaries.
