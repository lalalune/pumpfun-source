| # | branch | condition (post-opt IR) | BPI now (P true) | heuristic | reachable states | best reachable: weight, ratio delta, bytes | best any weight: weight, ratio delta, bytes, jm/fm delta |
| ---: | --- | --- | ---: | --- | --- | --- | --- |
| 1 | `start` | `icmp eq i32 %6, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 1:2000 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 2 | `bb1` | `icmp eq i32 %9, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 3 | `bb6` | `icmp eq i32 %16, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 1:2000 +0.00010 @27392, jm -0.0002 fm +0.0001 |
| 4 | `bb9` | `icmp eq i32 %18, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 5 | `bb12` | `icmp eq i8 %27, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.04028 @27360 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 6 | `bb6.i` | `icmp eq i8 %29, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.00819 @27408 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 7 | `bb14.i` | `icmp eq i8 %44, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.00879 @27408 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 8 | `bb7.i` | `icmp eq i8 %44, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.01028 @27408 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 9 | `bb16.i` | `icmp eq i8 %33, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 10 | `bb23.i` | `icmp eq i8 %_45.sroa.0.0.copyload, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.00879 @27408 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 11 | `bb22.i` | `icmp eq i8 %_45.sroa.0.0.copyload, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.03556 @27392 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 12 | `bb28.i` | `icmp eq i32 %81, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.00549 @27408 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 13 | `bb37.i` | `icmp eq i32 %95, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 14 | `bb38.i` | `icmp eq i32 %111, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 15 | `bb45.i` | `icmp eq i64 %0, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.00140 @27392 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 16 | `bb44.i` | `icmp eq i64 %0, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.05591 @27416 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 17 | `bb47.i` | `phi i1 [ true, %bb6 ], [ true, %bb9 ], [ %22, %bb11 ]` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 12:20 +0.00000 @27400 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 18 | `bb52.i` | `icmp eq i8 %31, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.00729 @27408 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 19 | `bb54.i` | `icmp eq i8 %35, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.00809 @27400 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 20 | `bb94.i` | `phi i1 [ true, %bb6 ], [ true, %bb9 ], [ %22, %bb11 ]` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 -0.00030 @27400 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 21 | `bb58.i` | `icmp ult i64 %159, %_33` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 12:20 -0.00030 @27400 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 22 | `bb76` | `phi i1 [ %11, %bb2 ], [ false, %start ], [ false, %bb1 ]` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 23 | `bb22` | `icmp eq i8 %29, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 24 | `bb19` | `icmp ne i8 %44, 0` | 0.625 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 25 | `bb26` | `icmp eq i64 %170, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 -0.00190 @27384 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 26 | `bb80` | `icmp eq i64 %_80, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.00509 @27400 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 27 | `bb28` | `phi i1 [ false, %bb21 ], [ false, %bb22 ], [ %167, %bb23 ]` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 1:2 -0.00539 @27400 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 28 | `bb35` | `phi i1 [ false, %bb21 ], [ false, %bb22 ], [ false, %bb23 ` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 -0.00260 @27392 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 29 | `bb33` | `icmp eq i8 %189, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.03526 @27392 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 30 | `bb2.i67` | `icmp eq i32 %191, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.03715 @27400 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 31 | `bb4.i` | `icmp eq i8 %193, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.03535 @27400 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 32 | `bb9.i` | `icmp eq i64 %195, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 -0.00130 @27384 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 33 | `bb66.i71` | `icmp eq i8 %210, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.02547 @27400 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 34 | `bb60.i` | `icmp eq i32 %213, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.01648 @27400 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 35 | `bb14.i73` | `call noundef zeroext i1 @_ZN19solana_account_info11Account` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 +0.00000 @27400 | 20:12 +0.00000 @27400, jm -0.0003 fm +0.0000 |
| 36 | `bb13.i` | `call noundef zeroext i1 @_ZN19solana_account_info11Account` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 37 | `bb17.i74` | `icmp eq i64 %217, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 1:2 +0.00000 @27400 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 38 | `bb19.i` | `call noundef zeroext i1 @_ZN19solana_account_info11Account` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 39 | `bb20.i` | `icmp eq i64 %221, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 2:1 +0.00000 @27400 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 40 | `bb24.i` | `icmp eq i64 %237, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 2:1 +0.00030 @27400 | 16:1 +0.00030 @27400, jm -0.0003 fm +0.0003 |
| 41 | `bb26.i` | `phi i1 [ %do_collect.sroa.0.1.off0.i, %bb71.i ], [ %do_col` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 2:1 +0.00000 @27400 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 42 | `bb43.i` | `and i1 %do_coin.sroa.0.1.off061.i, %coin_present.i` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 12:20 +0.00000 @27400 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 43 | `bb27.i79` | `icmp eq i64 %245, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 12:20 +0.00000 @27400 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 44 | `bb82.i` | `icmp eq i64 %245, 1` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 2:1 +0.00000 @27400 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 45 | `bb29.i` | `icmp eq i64 %_200.i, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.00729 @27408 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 46 | `bb84.i` | `icmp eq i64 %266, -9223372036854775782` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 -0.00140 @27392 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 47 | `bb90.i` | `icmp eq i64 %val.i.i.i.i.i, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 48 | `_ZN4core3ptr84drop_in_place$LT$all` | `icmp eq i64 %val.i.i3.i.i.i, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 49 | `_ZN4core3ptr74drop_in_place$LT$$u5` | `icmp eq i64 %_1.val.i.i, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 50 | `_ZN4core3ptr89drop_in_place$LT$all` | `icmp eq i64 %.val.i.i, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 51 | `bb89.i` | `icmp eq i64 %val.i.i.i.i38.i, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 52 | `_ZN4core3ptr84drop_in_place$LT$all` | `icmp eq i64 %val.i.i3.i.i41.i, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 53 | `_ZN4core3ptr74drop_in_place$LT$$u5` | `icmp eq i64 %_1.val.i49.i, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 54 | `_ZN4core3ptr89drop_in_place$LT$all` | `icmp eq i64 %.val.i53.i, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 55 | `bb44.i78` | `icmp eq i64 %316, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 56 | `_ZN14pump_recovered9admin_cto7exec` | `icmp eq i64 %_0.sroa.0.4.i, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 12:20 +0.00000 @27400 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 57 | `bb84` | `icmp eq i32 %329, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.06103 @27392 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 58 | `bb7.i105` | `call noundef zeroext i1 @_ZN19solana_account_info11Account` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 -0.06848 @27416 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 59 | `bb9.i107` | `icmp eq i64 %346, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 -0.00120 @27400 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 60 | `bb20.i133` | `call noundef zeroext i1 @_ZN19solana_account_info11Account` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 12:20 -0.08380 @27392 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 61 | `bb61.i` | `icmp eq i8 %349, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.06471 @27400 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 62 | `bb13.i110` | `icmp eq i64 %351, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 63 | `_ZN5alloc2rc10RcInnerPtr10inc_stro` | `icmp eq i64 %496, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 12:20 -0.00040 @27408 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 64 | `bb25.i` | `icmp eq i32 %323, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.01538 @27408 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 65 | `bb63.i` | `icmp eq i64 %_218.i, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 66 | `bb34.i` | `icmp eq i64 %516, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 -0.00180 @27400 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 67 | `bb26.i128` | `icmp eq i64 %_269.i, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.04593 @27408 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 68 | `bb94.i119` | `icmp eq i64 %521, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 69 | `bb96.i` | `icmp eq i8 %520, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.02167 @27408 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 70 | `bb43.i125` | `icmp eq i64 %_288.i, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 -0.01877 @27416 | 1:2000 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 71 | `bb37.i121` | `icmp eq i64 %_288.i, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 72 | `bb44.i126` | `icmp eq i64 %541, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 12:20 +0.00000 @27400 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 73 | `bb106.i` | `icmp eq i64 %546, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 12:20 +0.00000 @27400 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 74 | `bb85.i` | `icmp ugt i64 %_122.i, %min.i` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 -0.00120 @27400 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 75 | `bb30.i` | `icmp eq i64 %559, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 -0.00030 @27400 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 76 | `bb89.i132` | `icmp eq i64 %562, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 77 | `_ZN14pump_recovered9admin_cto7exec` | `icmp eq i64 %_424.sroa.0.3, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 78 | `bb89` | `icmp ne i8 %_548.sroa.0.0, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 12:20 -0.00170 @27392 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 79 | `bb38` | `icmp eq i64 %0, 1` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 80 | `_ZN5alloc2rc10RcInnerPtr10inc_stro` | `icmp eq i64 %671, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 81 | `bb40` | `call noundef zeroext i1 @_ZN19solana_account_info11Account` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 82 | `bb43` | `icmp eq i32 %677, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 83 | `bb44` | `icmp eq i64 %698, 2` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 +0.00000 @27400 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 84 | `bb47` | `icmp eq i64 %_512, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 85 | `bb122` | `icmp eq i64 %732, -9223372036854775782` | 0.5 | none 50:50 | 20:12, 12:20 (zero/ptr spelling), 2:1, 1:2 (3-way switch) | 20:12 -0.00140 @27392 | 1:1 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 86 | `bb131` | `icmp eq i64 %val.i.i.i.i, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 87 | `_ZN4core3ptr84drop_in_place$LT$all` | `icmp eq i64 %val.i.i3.i.i, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 88 | `_ZN4core3ptr74drop_in_place$LT$$u5` | `icmp eq i64 %_1.val.i, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 89 | `_ZN4core3ptr89drop_in_place$LT$all` | `icmp eq i64 %.val.i, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 90 | `bb130` | `icmp eq i64 %val.i.i.i.i254, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 91 | `_ZN4core3ptr84drop_in_place$LT$all` | `icmp eq i64 %val.i.i3.i.i257, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 92 | `_ZN4core3ptr74drop_in_place$LT$$u5` | `icmp eq i64 %_1.val.i265, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 20:12 +0.00000 @27400, jm +0.0000 fm +0.0000 |
| 93 | `_ZN4core3ptr89drop_in_place$LT$all` | `icmp eq i64 %.val.i269, 0` | 0.375 | zero/libcall 20:12 | 1:1 (and-1 / i1 test) | 1:1 +0.00000 @27400 | 12:20 +0.00000 @27400, jm +0.0000 fm +0.0000 |
