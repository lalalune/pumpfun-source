# Lane w6r2-execute-sem (wave 6, round 2)

Target: `0x1e7c0` `pump_recovered::create_v2::execute` (original 15,576 B, 1,859 insns, 125 calls).
Approach: assembly-first semantic reconstruction, with the llc IR oracle (`w6r1-execute-ir` scripts) to
confirm which IR shape a source spelling needs.

Base: origin/main 3bbbe91 (#2215, sibling lane w6r2-execute-ir), 1027/1035 normalized, 276 raw,
target 0.95184 at 15,568 B. (Lane started on a7135a6, 0.851; #2215 merged mid-lane.)

## Results

| Build | Base | Bytes | Ratio | Official | sha256 (unstripped) |
| --- | --- | ---: | ---: | --- | --- |
| main a7135a6 | | 15,576 | 0.85100 | 1027 / 276 | |
| b1 | a7135a6 | 15,584 | 0.85346 | 1027 / 276, 0 losses | bd871813 |
| main 3bbbe91 | | 15,568 | 0.95184 | 1027 / 276 | |
| **b2** | 3bbbe91 | 15,584 | **0.96854** | 1027 / 276, 0 losses, 0 raw losses | a890a7f3 |

## Mechanism (b1/b2): `init_curve(bonding_curve:&mut BondingCurve, global:&Global, ..)`

In the original the curve-store block writes `creator` through a separate pointer computed right
after the `quote_mint == Pubkey::default()` memcmp (`mov r4,r7; add r4,8` ... `stxdw [r4+0x18..0]`),
while every other field is stored relative to the `Account` pointer r7. `creator` is at offset 0 of
`BondingCurve` (rustc puts the two `Pubkey`s first) and `BondingCurve` sits at `Account+8`, so r4 is
simply the `&mut BondingCurve` value. When `init_curve` is a `&mut self` method that derefs
`self.bonding_curve` inside, MIR place projections fold the deref into each field store and LLVM
emits `gep Account,8` next to the creator memcpy (stored first, through r7). Passing the deref'd
`&mut BondingCurve` as a parameter of a plain helper makes it a real SSA value computed at the call
site; LLVM merges the other field GEPs into Account-relative offsets and only the creator memcpy
(offset 0) uses the pointer itself, exactly as in the original. The IR-oracle edit `lategep0`
(creator GEP moved into the memcmp block, memcpy left in place) predicted b1's ratio exactly
(0.85346).

## IR oracle findings (on a7135a6 base)

- `spec` (Controlled payload load hoisted into the Option-test block): 0.85361.
- walk-edge branch weight >= 50%: 0.85346; control_account Err edge cold: 0.85368.
- `spec + bw + lategep0`: 0.86790. #2215 found the source spelling for spec+bw (bind the Option
  and override it on the walk path); b1/b2 is the spelling for lategep0.

## Ledger

Keys `0x1e7c0-main-a7135a6-*` and `0x1e7c0-main-3bbbe91-*` (lane `w6r2-execute-sem`).
