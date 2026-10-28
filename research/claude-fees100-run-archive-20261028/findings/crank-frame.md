# crank-frame findings (frame/allocation lane, window 147944 crank_donation_fee_pda) — round 3

STATUS 21:10: window ALREADY CLOSED by crank-brute-g01 (DIRECTIVES 21:08). This lane reached the SAME fix
independently: my w01 native build is BYTE-IDENTICAL to crank-brute-g01 and crank-transfer-g01
(native-symbols sha e77815918e6e022dac1df0105084643458222cc2d4aa9204ce08ee1c8f1f6d0c; measure vs native w584:
gained_normalized [147944], lost_normalized []). Not harvested separately (duplicate). Stopped per directive.

Lane dir: RR/lanes/crank-frame. Tools (all in lanes/crank-frame/tools):
- mkvar.py NAME SPEC.py (variant tree from w584: HANDLER line 248 / HELPER on donation.rs blank lines 12.. / EVENT=anchor),
  run.sh NAME SLOT [rustc args] (nbuild + score), cx.py (masked/raw ratio, depth, call order), fmask.py (frame-masked).
- extract_fn.py MODULE.ll SUBSTR OUT.ll + `llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext` (v1.44 llc):
  reproduces the rustc crank body EXACTLY in ~0.1 s; `-stop-after=prologepilog` gives the MIR stack table (alloca names
  + final offsets). ocmp.py FILE.(o|so) [--so REF]: instruction-exact compare vs original window (call/lddw imm masked).

## Results
- v08 (crank-b, round 2) reconstructed on w584 = specs/v08r.py: 1950i/15976B, masked 0.9641 span 74, depth 2168.
  Requires the DIRECT mint condition (`if ctx.accounts.quote_mint.key()==native_mint::ID`) and the DIRECT receiver
  temporary (`(DonatePubkeyConfigIdWithPayerV1{..}).invoke_signed(..)`): with PR #304's named `let mint` + named
  `relay_accounts` (specs/v08.py) the frame is 2392 deep — MIR stack table shows an extra `mint` 32-B slot and
  `event.sroa.0` 192 B no longer merged into the 624-B receiver slot (named locals live to scope end).
- v08r MIR stack table == original survivor layout (-120/-160/-184/-208/-232/-280/-304/-928 receiver/-992 seeds/
  -1096 relay_args/-1128/-1160/-1192, 12x16-B sret slots, spill -1408 = rent AccountInfo ptr).
- ROOT CAUSE (llc loop, an/e1.ll): the ONLY IR difference from the original is that the rent AccountInfo clone in the
  SyncNative infos must RE-LOAD the key pointer (`load ptr, ptr %rent_info`) instead of reusing the AccountMeta key-ptr
  load (GVN-merged in v08r because `rent: &AccountInfo` is a noalias-readonly param of the inlined helper). That single
  IR edit makes llc emit the original body EXACTLY (ocmp EXACT=True, raw 1.0000). Donation's key load IS merged in the
  original too (spill -1400), i.e. donation stays a `&AccountInfo` param while rent is not noalias-scoped.
- Source forms (builds):
  w01 `rent: &UncheckedAccount<'info>` param, call `&ctx.accounts.rent`, `rent.key()` / `rent.to_account_info()`:
      EXACT (ocmp vs original), measure gained 147944, no loss.  == crank-brute-g01 binary.
  w02 = w01 + `let rent: &AccountInfo<'info> = rent.as_ref();` at helper top: same sha as w01.
  w03 `rent: UncheckedAccount<'info>` BY VALUE (call `ctx.accounts.rent.clone()`): NO fix (masked 0.9641, = v08r) —
      the by-value newtype still gets noalias readonly (rustc pointee info looks through the newtype).
- fndiff on NATIVE builds is never identical=True for these windows: the lddw string previews include the bytes after
  the string, which depend on the (non-ordered.ld) native rodata order — same 3-line delta appears for the already
  matched create window 163920 on native w584. measure.py normalized gain is the authority natively; Linux/ordered.ld
  build needed for whole-ELF (elfinv).
