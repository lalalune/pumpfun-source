#!/usr/bin/env python3
"""Authenticated Mayhem dispatcher inventory and deterministic case planning.

The selectors are the 25 captured comparisons in ``evidence/dispatch-map.json``.
Argument layouts and account order come from the maintained Rust source.  This is
deliberately an inventory fixture, not an invented IDL.
"""

import hashlib
import struct


PROGRAM_ID = "MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e"
EVENT_CPI_TAG = bytes.fromhex("e445a52e51cb9a1d")
IDL_TAG = bytes.fromhex("40f4bc78a7e9690a")

TRADE = "trade(u128,u16,u16)"
OPTIONS = "options(u32,u32,u64,u64,u64,u64,u8,u64,u64,u64,u64,u64,u64,u64,u64,u64)"


def _row(name, discriminator, args, accounts, signer=(), writable=()):
    return {
        "name": name,
        "discriminator": discriminator,
        "args": args,
        "accounts": tuple(accounts.split(",")) if accounts else (),
        "signer": tuple(signer),
        "writable": tuple(writable),
    }


# Keep this literal table reviewable against lib.rs and the Accounts structs.
INSTRUCTIONS = (
    _row("burn_tokens", "4c0f33fee5d77942", "none", "mayhem_state,mint,mayhem_token_vault,sol_vault,bonding_curve,global,pump_program,pump_event_authority,system_program,token_program,event_authority,program", writable=(0, 1, 2, 3, 4)),
    _row("buy", "66063d1201daebea", TRADE, "trader,global_params,mayhem_state,mint,mayhem_token_vault,sol_vault,system_program,token_program,global,bonding_curve,fee_recipient,associated_bonding_curve,creator_vault,pump_event_authority,pump_program,global_volume_accumulator,user_volume_accumulator,fee_config,fee_program,event_authority,program,bonding_curve_v2,buyback_recipient", signer=(0,), writable=(0, 1, 2, 4, 5, 9, 10, 11, 12, 15, 16, 22)),
    _row("buy_pump_swap", "de939d076c089151", TRADE, "trader,global_params,mayhem_state,mint,mayhem_token_vault,mayhem_quote_vault,sol_vault,system_program,quote_token_program,base_token_program,associated_token_program,pool,global_config,quote_mint,pool_base_token_account,pool_quote_token_account,protocol_fee_recipient,protocol_fee_recipient_token_account,pump_swap_event_authority,pump_swap_program,coin_creator_vault_ata,coin_creator_vault_authority,global_volume_accumulator,user_volume_accumulator,fee_config,fee_program,event_authority,program,pool_v2,buyback_recipient,buyback_recipient_ata", signer=(0,), writable=(0, 1, 2, 4, 5, 6, 11, 14, 15, 16, 17, 20, 22, 23, 29, 30)),
    _row("buy_v2", "b817ee6167c5d33d", TRADE, "trader,global_params,mayhem_state,mint,quote_mint,associated_token_program,mayhem_base_token_vault,mayhem_quote_token_vault,sol_vault,system_program,token_program,quote_token_program,global,bonding_curve,associated_quote_bonding_curve,fee_recipient,fee_recipient_ata,associated_base_bonding_curve,creator_vault,associated_creator_vault,sharing_config,pump_event_authority,pump_program,global_volume_accumulator,user_volume_accumulator,associated_user_volume_accumulator,fee_config,fee_program,event_authority,program,buyback_recipient,buyback_recipient_ata", signer=(0,), writable=(0, 1, 2, 6, 7, 8, 13, 14, 15, 16, 17, 18, 19, 23, 24, 25, 30, 31)),
    _row("extend_account", "ea66c2cb96483ee5", "none", "account,user,system_program,event_authority,program", signer=(1,), writable=(0,)),
    _row("initialize_fee_recipient", "da578ec8cec516c8", "u8", "admin,wsol_mint,fee_recipient,fee_recipient_ata,global_params,system_program,token_program,associated_token_program", signer=(0,), writable=(0, 2, 3, 4)),
    _row("initialize_global_params", "0d127fea3b28ccda", "none", "admin,global_params,system_program", signer=(0,), writable=(0, 1)),
    _row("initialize_mayhem_state", "9dbd5e485545cc2d", "none", "payer,global_params,mint_authority,sol_vault,mint,mayhem_token_vault,mayhem_state,system_program,token_program,associated_token_program", signer=(0, 2), writable=(0, 3, 5, 6)),
    _row("reset_sol_deployed", "b0ad9da2f0bcc439", "none", "admin,global_params,system_program,event_authority,program", signer=(0,), writable=(0, 1)),
    _row("reset_stable_deployed", "bf2530b70f5489cb", "none", "admin,global_params,system_program,event_authority,program", signer=(0,), writable=(0, 1)),
    _row("reset_state", "9176742a28db948b", "none", "admin,global_params,system_program,event_authority,program", signer=(0,), writable=(0, 1)),
    _row("resume_trading", "922ed456459f1e41", "none", "admin,global_params,system_program,event_authority,program", signer=(0,), writable=(0, 1)),
    _row("sell", "33e685a4017f83ad", TRADE, "trader,global_params,mayhem_state,sol_vault,mint,mayhem_token_vault,token_program,system_program,global,bonding_curve,fee_recipient,associated_bonding_curve,creator_vault,pump_event_authority,pump_program,fee_config,fee_program,event_authority,program,bonding_curve_v2,buyback_recipient", signer=(0,), writable=(0, 1, 2, 3, 5, 9, 10, 11, 12, 20)),
    _row("sell_pump_swap", "10c691f0ee6589cb", TRADE, "trader,global_params,mayhem_state,mint,mayhem_token_vault,mayhem_quote_vault,sol_vault,system_program,quote_token_program,base_token_program,associated_token_program,pool,global_config,quote_mint,pool_base_token_account,pool_quote_token_account,protocol_fee_recipient,protocol_fee_recipient_token_account,pump_swap_event_authority,pump_swap_program,coin_creator_vault_ata,coin_creator_vault_authority,fee_config,fee_program,event_authority,program,pool_v2,buyback_recipient,buyback_recipient_ata", signer=(0,), writable=(0, 1, 2, 4, 5, 6, 11, 14, 15, 16, 17, 20, 28)),
    _row("sell_v2", "5df6823ce7e940b2", TRADE, "trader,global_params,mayhem_state,mint,quote_mint,associated_token_program,mayhem_base_token_vault,mayhem_quote_token_vault,sol_vault,system_program,token_program,quote_token_program,global,bonding_curve,associated_quote_bonding_curve,fee_recipient,fee_recipient_ata,associated_base_bonding_curve,creator_vault,associated_creator_vault,sharing_config,pump_event_authority,pump_program,user_volume_accumulator,associated_user_volume_accumulator,fee_config,fee_program,event_authority,program,buyback_recipient,buyback_recipient_ata", signer=(0,), writable=(0, 1, 2, 6, 7, 8, 13, 14, 15, 16, 17, 18, 19, 23, 24, 29, 30)),
    _row("stop_trading", "7fb06a3bf27a726f", "none", "admin,global_params,system_program,event_authority,program", signer=(0,), writable=(0, 1)),
    _row("sweep_fees", "afe1624776422294", "none", "trader,global_params,quote_mint,trader_quote_ata,system_program,token_program,associated_token_program,event_authority,program", signer=(0,), writable=(0, 1, 3)),
    _row("sweep_fees_admin", "4c93c5e16f9c75e7", "none", "admin,global_params,quote_mint,admin_quote_ata,system_program,token_program,associated_token_program,event_authority,program", signer=(0,), writable=(0, 1, 3)),
    _row("update_admin", "a1b028d53cb8b3e4", "pubkey", "admin,global_params,system_program,event_authority,program", signer=(0,), writable=(0, 1)),
    _row("update_global_params", "9224de6c59e2f97e", OPTIONS, "admin,global_params,system_program,event_authority,program", signer=(0,), writable=(0, 1)),
    _row("update_max_sol_per_sweep", "22ada705c885e192", "u64", "admin,global_params,system_program,event_authority,program", signer=(0,), writable=(0, 1)),
    _row("update_max_stable_per_sweep", "804b4c8b7dc46f67", "u64", "admin,global_params,system_program,event_authority,program", signer=(0,), writable=(0, 1)),
    _row("update_trader", "c9cf63406556af60", "pubkey", "admin,global_params,system_program,event_authority,program", signer=(0,), writable=(0, 1)),
    _row("withdraw_admin", "1e1b87bc899eda6b", "u64", "admin,global_params,sol_vault,system_program", signer=(0,), writable=(0, 1, 2)),
    _row("withdraw_quote_admin", "cc712a30723af859", "u64", "admin,global_params,sol_vault,quote_mint,sol_vault_quote_ata,admin_quote_ata,token_program,associated_token_program,system_program", signer=(0,), writable=(0, 1, 2, 4, 5)),
)


OPTION_WIDTHS = (4, 4, 8, 8, 8, 8, 1, 8, 8, 8, 8, 8, 8, 8, 8, 8)


def selector(name):
    return hashlib.sha256(("global:" + name).encode()).digest()[:8]


def default_args(kind):
    if kind == "none":
        return b""
    if kind == TRADE:
        return (5).to_bytes(16, "little") + struct.pack("<HH", 25, 50)
    if kind == "u64":
        return struct.pack("<Q", 7)
    if kind == "u8":
        return b"\x01"
    if kind == "pubkey":
        return bytes([7]) * 32
    if kind == OPTIONS:
        return b"\x00" * 16
    raise ValueError(kind)


def argument_variants(kind):
    """Return focused (label, bytes) variants, including bounded malformed forms."""
    valid = default_args(kind)
    out = [("valid-args", valid), ("trailing-byte", valid + b"\xa5")]
    if kind == "none":
        return out
    out.append(("last-byte-removed", valid[:-1]))
    if kind == TRADE:
        out.extend((
            ("numeric-all-zero", bytes(20)),
            ("numeric-all-max", bytes([255]) * 20),
            ("reference-max", bytes([255]) * 16 + struct.pack("<HH", 25, 50)),
            ("tolerance-max", (5).to_bytes(16, "little") + struct.pack("<HH", 65535, 50)),
            ("retained-reserve-max", (5).to_bytes(16, "little") + struct.pack("<HH", 25, 65535)),
            ("reference-truncated-15", bytes(15)),
            ("tolerance-truncated-1", bytes(16) + b"\x00"),
        ))
    elif kind == "u64":
        out.extend((("numeric-zero", bytes(8)), ("numeric-max", bytes([255]) * 8),
                    ("integer-one-byte", b"\x00"), ("integer-four-bytes", bytes(4))))
    elif kind == "u8":
        out.extend((("numeric-zero", b"\x00"), ("numeric-max", b"\xff")))
    elif kind == "pubkey":
        out.extend((("pubkey-zero", bytes(32)), ("pubkey-ff", bytes([255]) * 32),
                    ("pubkey-truncated-31", bytes(31))))
    elif kind == OPTIONS:
        all_zero = b"".join(b"\x01" + bytes(w) for w in OPTION_WIDTHS)
        all_max = b"".join(b"\x01" + bytes([255]) * w for w in OPTION_WIDTHS)
        out.extend((("options-all-some-zero", all_zero), ("options-all-some-max", all_max)))
        prefix = bytearray()
        for index, width in enumerate(OPTION_WIDTHS):
            rest = b"\x00" * (len(OPTION_WIDTHS) - index - 1)
            out.append((f"option-{index}-invalid-tag-2", bytes(prefix) + b"\x02" + rest))
            out.append((f"option-{index}-truncated-body", bytes(prefix) + b"\x01" + bytes(max(width - 1, 0))))
            prefix += b"\x00"
    return out


def validate_inventory():
    names = [row["name"] for row in INSTRUCTIONS]
    assert len(INSTRUCTIONS) == len(set(names)) == 25
    for row in INSTRUCTIONS:
        assert selector(row["name"]).hex() == row["discriminator"]
        assert all(0 <= i < len(row["accounts"]) for i in row["signer"] + row["writable"])


validate_inventory()
