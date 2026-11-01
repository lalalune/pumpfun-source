# Calibration: how Rust/Anchor idioms look in this Ghidra pseudo-C

These are byte-matched siblings whose Rust is known. They are decompiled with the same SBF fix-ups as admin_cto, from
main 599891304; every one of them is byte-identical to the original. The pseudo-C is under `calibration/`:

| function | address | source | file |
|---|---|---|---|
| `set_creator::set` | 0x38fc0 (6,136 B) | `programs/pump/src/creator/set_creator.rs` | `set_creator_set.addr.c` |
| `__global::migrate_bonding_curve_creator` | 0x1308c0 | handler entry, migrate_bonding_curve_creator.rs | `global_migrate_bonding_curve_creator.addr.c` |
| `pump_amm::cpi::admin_cto_pool` | 0x10a0e0 | anchor-generated CPI builder that admin_cto calls | `pump_amm_cpi_admin_cto_pool.addr.c` |
| `pump_fees::cpi::admin_cto_sharing_config` | 0x116718 | anchor-generated CPI builder | `pump_fees_cpi_admin_cto_sharing_config.addr.c` |
| `admin_cto::token_frozen` | 0x29518 | admin_cto.rs line 770 | `admin_cto_token_frozen.addr.c` |

Each line is prefixed with `/*lo-hi*/`, the function-relative offsets of the instructions that produced it. Use that
to go from a C statement to the exact instructions in the `.lst`.

## Reading conventions

- **Stack.** `uStack_4b8`, `ppppppplStack_2d0` and the like are `[r10-0x4b8]`, `[r10-0x2d0]`. The `p…p` chains and
  `undefined8` are Ghidra's failed type propagation ("Type propagation algorithm not settling"); ignore the stars. A
  name like `uStack_4b8._4_1_` is a 1-byte piece at -0x4b4: the slot holds a value written with mixed widths, usually
  because stack coloring shares it with a differently shaped value.
- **Odd offsets** (-0x651, -0x649, -0x679) are packed `Option<Pubkey>` or `(Pubkey,u8)` objects, which have align 1.
  The `CONCAT71`/`SUB87` noise around them is the decompiler gluing 7+1-byte pieces.
- **Parameters.** `param_1` is the sret pointer of the function's `Result`. `param_2` is `&Context` (`*(param_2 + 8)`
  is `ctx.accounts`). `param_3`/`param_4` are the first scalar args. `param_5` is the SBF stack-argument pointer:
  arguments 5 and up are read as `*(param_5 - 0x1000)`, `*(param_5 - 0xff8)`, ..., and callers write them at
  `[r10-0x1000..]` in their own frame.
- **Constants.**
  - `k_u32_<n>` is a pooled u32 constant passed by reference, almost always `&PumpError::<variant n>`.
  - `obj_1bd838` is the `fmt::Write` vtable for `String` (used by inline to_string).
  - `PUMP_PROGRAM_ID_…`, `PUMP_FEES_PROGRAM_ID_…`, `PUMP_AMM_PROGRAM_ID_…`, `NATIVE_MINT_…` are 32-byte rodata
    pubkeys.
  - `k_u32_0_1b5ba8` points at 32 zero bytes: the System Program id / `Pubkey::default()`.

## Idioms

**Account access.** `ctx.accounts.x` is a pointer load `plVar115[i]` from the accounts struct, with i the field index
in the `#[derive(Accounts)]` order.

- `Account<T>` fields resolve to `AccountInfo*`. `x.key` is `*(info + 0)`. `x.owner` is `*(info + 0x18)`.
  `lamports`/`data` are `Rc<RefCell<..>>` pointers at +8 and +0x10.
- Flags `is_signer`/`is_writable`/`executable` are bytes at +0x28..+0x2a.
- Deserialized `Account` data (BondingCurve, Global) is read at fixed offsets, for example `curve + 0x10..0x30` for the
  creator and bytes `+0xa2..+0xa5` for the bools.
- In set_creator, `ctx.accounts` holds the deserialized structs inline (`lVar18 + 0x1e8` is `bonding_curve.creator`).

**Pubkey comparisons.** `a == b` on Pubkeys is `memcmp(a, b, 0x20) == 0`, always a call (`memcmp` is the
`sol_memcmp_` wrapper).

- `x == Pubkey::default()` first writes four zero qwords to a scratch slot, then calls memcmp against it
  (set_creator +0x20..+0x58; admin_cto -0x2d0).
- `Pubkey::key()` copies are four `ldxdw`/`stxdw` pairs.

**Error returns, `require!`, `error!`.** Anchor's `error!(PumpError::X)` becomes this sequence:

```c
PumpError::name(&String_out, &k_u32_X);                    // error_name
uStack_4b0 = 1; uStack_4b8 = 0; ...                        // empty String for error_msg
<PumpError as Display>::fmt(&k_u32_X, &Formatter)          // inline to_string: Formatter on stack, vtable obj_1bd838
if (ret != 0) core::result::unwrap_failed(...)            // "a Display implementation returned an error unexpectedly"
<From<AnchorError>>::from(&Error_out, &AnchorError)        // boxed into anchor_lang::error::Error
goto shared_err_exit;                                      // copy Error into param_1, return
```

When the error site is cold enough, LLVM keeps the generic call instead of inlining it:
`<T as ToString>::to_string(&String, &k_u32_X)`. The original does this at 312/307 (main inlines those two).
`.with_pubkeys((a,b))` adds a call to `anchor_lang::error::Error::with_pubkeys(&out, …)` after `From`. Every Err exit
in a function funnels into one block that stores the 2-word Error into `param_1` (`LAB_…39220` in set_creator).

**`?` on Result.** The callee writes a tagged union into a stack slot. The caller tests the tag against the niche
value and branches to the shared Err exit:

```c
Clock::get(&out); if (out.tag != 0) { From<ProgramError>::from(&err, &out); goto exit; }
```

Two more niche values to recognise:

- In token_frozen, `*param_1 = 2` is `Ok` for `Result<bool,Error>`: `Error` uses tags 0 and 1, so `Ok` takes 2. The
  bool sits in `param_1[1]`.
- `try_borrow_data` succeeds when its tag equals `-0x7fffffffffffffe6`.

**`Option`.**

- `Option<bool>` arrives as one byte: 0/1 for `Some(false)`/`Some(true)`, 2 for `None`. `hopt == Some(true)` compiles
  to `param & 1` in the original (and-1) or to `== 1`.
- `Option<u64>` is a (tag, value) pair in two registers or slots.
- `Option<Pubkey>` is 33 bytes with the tag byte first. `Option<Option<Pubkey>>` reuses the same bytes, with tag 2 for
  the outer `None`. So `Some(new)` is bit-identical to `new`, and the original tests `new.tag != 2` directly.

**`msg!("…")`** compiles to `sol_log_("literal", len)` with the literal named in the C. A shared `msg!` site (the
wallet's three messages) appears as one `sol_log_(msg, len)` with `msg`/`len` phi'd.

**`emit!(e)`.** The bump allocator is inlined: `puRam0000000300000000` is the heap cursor at 0x300000000 and
0x300007f00 is the heap end. The block below allocates a buffer, writes the 8-byte discriminator constant (set_creator:
`0xd248fbf5257b34ed`) and the fields, then calls `sol_log_data(&slice, 1)`.

```c
p = cursor - 0x20 (aligned) ...; if (p < 0x300000008) goto alloc_fail;
```

`emit_cpi!` / the manual self-CPI does this:

1. `Event::data` → `Vec::from_iter` (prefix with the EVENT_IX_TAG) → `exchange_malloc(0x22, 1)` (AccountMeta);
2. `Instruction::new_with_bytes(&ix, PUMP_PROGRAM_ID, …)`;
3. `memcpy` of the AccountInfo (0x30);
4. `invoke_signed(&ix, infos, seeds, 1)`.

**`to_account_info()` / `AccountInfo{..}` literals / `.clone()`.** Each clone is two inline `Rc` increments, as below.
The abort block is shared by the whole function: in admin_cto it is the single `abort()` at +0x26e0, which explains
the original's long call-free T1/C1 runs.

```c
n = *rc; *rc = n + 1; if (n + 1 == 0) goto abort_block;
```

- Calling the out-of-line `<AccountInfo as Clone>::clone(&dst, src)` instead gives a real call. That is the P1 pool
  CPI's 8 calls and W2's create_idempotent/collect runs.
- Field order inside a literal shows up as the order of the loads and increments.

**CPI builders** (`admin_cto_pool`, `admin_cto_sharing_config`):

1. `ToAccountMetas::to_account_metas` → Vec;
2. the instruction data: `RawVec::reserve`, `memcpy` of the discriminator plus the borsh-serialized args;
3. `grow_one` per AccountInfo;
4. `invoke_signed(&ix, infos, n, signer_seeds)`.

admin_cto passes the CpiContext by reference (`&ppppppplStack_860`) plus the args. An `Option<Pubkey>` arg travels as
the 33-byte packed object described above.

## Translating pseudo-C back into shim Rust

| pseudo-C shape in the original | Rust that compiles to it |
|---|---|
| `memcmp(x, &zero_slot, 32)` with zero qwords stored first | `x == Pubkey::default()`. To pin the zero store, read the key through `read_volatile(&key as *const _ as *const [u64;4])` |
| `param & 1` holder test | `hopt == Some(true)` written as `matches!(hopt, Some(true))`, or `(*(&hopt as *const _ as *const u8) & 1) != 0` as a shim |
| separate `to_string` call at an error site | a cold error path, so LLVM does not inline it (branch weight via the `llvm.expect.i1` extern, see the w17a02 notes) |
| values loaded at entry and spilled, used much later | `let v = unsafe{core::ptr::read_volatile(p)} /*shim: entry load*/` at the original's position (volatile loads are neither sunk nor merged) |
| a 32-byte scratch slot reused by several temporaries (-0x2d0) | one `MaybeUninit<[u64;4]>` scratch written through `as_mut_ptr()` by each producer (out-param pinning) |
| packed `Option<Pubkey>` at an odd slot with an aligned payload | build it in a `#[repr(C)]` buffer `[u8;40]` with the tag at offset 7, or write its pieces with `write_volatile` at explicit offsets |
