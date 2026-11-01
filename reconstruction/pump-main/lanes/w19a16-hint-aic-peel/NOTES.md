# w19a16-hint-aic-peel

Byte-identical peel. Target window 0x22a10 (`admin_cto::execute`).

Plain `aic(x)` on lines 659 and 749 becomes `x.to_account_info()`, and the helper leaves line 8. Line numbers are unchanged.

Measured on main 1f7ca411c: unstripped sha 963ea0fe51f8ed97 before and after, admin_cto 0.92243, 2,746 slots, 27,400 B, Pump Main 1034/1034, no losses. The weighted forms (`aicl`, `aicd`, `aicb`) stay: they carry real branch weights.
