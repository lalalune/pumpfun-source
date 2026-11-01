# w17a34-shim-outlineland: cheaper 72 B repay of the outline base

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Main 0881307b0 (0.69542, M 2,322, 3,224 slots).

The outline base without #4117's repay knobs (`cnat` +40 B, `wown` +32 B) is M 2,330 at 27,328 B, so the repay costs 8 M.
Swapping `wown` (+32 B, -5) for a hand-written `?` at the wallet's creator-ata `token_frozen` test with its Err residual kept in
memory (`qrwtf`, +32 B, -1) gives M 2,326 at 27,400 B: 0.69662, 3,221 slots, 1034/1034, zero losses, differential 388/0.

Re-measured repay table on 0881307b0 (singles on the unrepaid base, M 2,330 at 27,328 B; bytes, M): ph338/ph339 +8, 0 (only one
of them: both -13, nine reads collapse validate); qrwtf +32, -1; qrpbc +16, -3; qr560 +32, -3; cnat +40, -3; wexe +8, -4;
wown +32, -5; wwr +8, -6; pow +32, -6; qr559 +32, -8; f719 +40, -9; cpr +8, -10. Collapse (more than -100): f410, f660, qnat,
snat, qr649, qrsfz, qrsam, ph326, ph330. A real hk2 copy in the stand-in slot (ptr copy or volatile u64 stores) collapses to
about 1,870-1,900.
