# w17a35-shim-trycarrier-2: repay pad moves at the sweep (0x22a10)

Target `admin_cto::execute`, 27,400 B. Base main e60774c17 (0.70021, M 2,338, 3,189 slots).

Three of the 312-block placeholder reads move to a generic `pad()` (one volatile stack store, no register use): two at the sweep `ConstraintSeeds` error head and
one before the sweep gate. Result 0.70051, M 2,339: S1 +5, W1 +1, J2 -3, V1 -1, TL -1. Zero losses, differential 388/0. The wallet non-native arm pad moves a wallet block (W2 -52): do not use it.

Lane analysis (Err payload register, coalescer order, `?` carrier spellings): `origin/swarm/w17a35-shim-trycarrier`.
