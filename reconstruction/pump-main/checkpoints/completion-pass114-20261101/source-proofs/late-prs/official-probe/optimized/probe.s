	.text
	.file	"pass114_late_probe.c42a7eae2abfd033-cgu.0"
	.section	".text._ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE","ax",@progbits
	.p2align	3
	.type	_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE,@function
_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE:
	mov64 r3, r2
	mov64 r6, r1
	stdw [r10 - 80], 0
	stdw [r10 - 88], 1
	stdw [r10 - 96], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -96
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	mov64 r1, r3
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jne r0, 0, LBB0_2
	ldxdw r1, [r10 - 80]
	stxdw [r6 + 16], r1
	ldxdw r1, [r10 - 88]
	stxdw [r6 + 8], r1
	ldxdw r1, [r10 - 96]
	stxdw [r6 + 0], r1
	exit
LBB0_2:
	mov64 r3, r10
	add64 r3, -1
	lddw r1, .Lalloc_cc656815297f75969399c3f4b1ad3de4
	mov64 r2, 55
	lddw r4, .Lvtable.1
	lddw r5, .Lalloc_d5d9fccaf545b6e0545ef73245a3c43f
	call _ZN4core6result13unwrap_failed17h2dbd2ef42161686dE
.Lfunc_end0:
	.size	_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE, .Lfunc_end0-_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE

	.section	.text._ZN4core3fmt5Write9write_fmt17hf607f0d92912dfd2E,"ax",@progbits
	.p2align	3
	.type	_ZN4core3fmt5Write9write_fmt17hf607f0d92912dfd2E,@function
_ZN4core3fmt5Write9write_fmt17hf607f0d92912dfd2E:
	mov64 r3, r2
	lddw r2, .Lvtable.0
	call _ZN4core3fmt5write17h7d5c5d972f6bf082E
	exit
.Lfunc_end1:
	.size	_ZN4core3fmt5Write9write_fmt17hf607f0d92912dfd2E, .Lfunc_end1-_ZN4core3fmt5Write9write_fmt17hf607f0d92912dfd2E

	.section	".text._ZN4core3ptr37drop_in_place$LT$core..fmt..Error$GT$17hc55e87063dbb1cfcE","ax",@progbits
	.p2align	3
	.type	_ZN4core3ptr37drop_in_place$LT$core..fmt..Error$GT$17hc55e87063dbb1cfcE,@function
_ZN4core3ptr37drop_in_place$LT$core..fmt..Error$GT$17hc55e87063dbb1cfcE:
	exit
.Lfunc_end2:
	.size	_ZN4core3ptr37drop_in_place$LT$core..fmt..Error$GT$17hc55e87063dbb1cfcE, .Lfunc_end2-_ZN4core3ptr37drop_in_place$LT$core..fmt..Error$GT$17hc55e87063dbb1cfcE

	.section	".text._ZN4core3ptr42drop_in_place$LT$alloc..string..String$GT$17hd1d278fe2cba7629E","ax",@progbits
	.p2align	3
	.type	_ZN4core3ptr42drop_in_place$LT$alloc..string..String$GT$17hd1d278fe2cba7629E,@function
_ZN4core3ptr42drop_in_place$LT$alloc..string..String$GT$17hd1d278fe2cba7629E:
	ldxdw r2, [r1 + 0]
	jeq r2, 0, LBB3_2
	ldxdw r1, [r1 + 8]
	mov64 r3, 1
	call __rust_dealloc
LBB3_2:
	exit
.Lfunc_end3:
	.size	_ZN4core3ptr42drop_in_place$LT$alloc..string..String$GT$17hd1d278fe2cba7629E, .Lfunc_end3-_ZN4core3ptr42drop_in_place$LT$alloc..string..String$GT$17hd1d278fe2cba7629E

	.section	".text._ZN53_$LT$core..fmt..Error$u20$as$u20$core..fmt..Debug$GT$3fmt17h85666afa16c4890eE","ax",@progbits
	.p2align	3
	.type	_ZN53_$LT$core..fmt..Error$u20$as$u20$core..fmt..Debug$GT$3fmt17h85666afa16c4890eE,@function
_ZN53_$LT$core..fmt..Error$u20$as$u20$core..fmt..Debug$GT$3fmt17h85666afa16c4890eE:
	mov64 r1, r2
	lddw r2, .Lalloc_99ac8a81a24cac863217ce4a5cbfabea
	mov64 r3, 5
	call _ZN4core3fmt9Formatter9write_str17h97ca3d8b34e3baaaE
	exit
.Lfunc_end4:
	.size	_ZN53_$LT$core..fmt..Error$u20$as$u20$core..fmt..Debug$GT$3fmt17h85666afa16c4890eE, .Lfunc_end4-_ZN53_$LT$core..fmt..Error$u20$as$u20$core..fmt..Debug$GT$3fmt17h85666afa16c4890eE

	.section	".text._ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$10write_char17hfde5b685689164ccE","ax",@progbits
	.p2align	3
	.type	_ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$10write_char17hfde5b685689164ccE,@function
_ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$10write_char17hfde5b685689164ccE:
	mov64 r6, r1
	mov64 r1, r2
	lsh64 r1, 32
	rsh64 r1, 32
	jlt r1, 128, LBB5_9
	stw [r10 - 4], 0
	jlt r1, 2048, LBB5_3
	mov64 r1, r2
	lsh64 r1, 32
	rsh64 r1, 32
	jlt r1, 65536, LBB5_4
	ja LBB5_5
LBB5_4:
	mov64 r1, r2
	and64 r1, 63
	or64 r1, 128
	stxb [r10 - 2], r1
	mov64 r1, r2
	rsh64 r1, 12
	or64 r1, 224
	stxb [r10 - 4], r1
	rsh64 r2, 6
	and64 r2, 63
	or64 r2, 128
	stxb [r10 - 3], r2
	mov64 r7, 3
	ja LBB5_6
LBB5_9:
	ldxdw r7, [r6 + 16]
	ldxdw r1, [r6 + 0]
	jne r7, r1, LBB5_11
	mov64 r1, r6
	mov64 r8, r2
	call _ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$8grow_one17h4b15183664487c30E
	mov64 r2, r8
LBB5_11:
	ldxdw r1, [r6 + 8]
	add64 r1, r7
	stxb [r1 + 0], r2
	add64 r7, 1
	stxdw [r6 + 16], r7
	ja LBB5_12
LBB5_3:
	mov64 r1, r2
	and64 r1, 63
	or64 r1, 128
	stxb [r10 - 3], r1
	rsh64 r2, 6
	or64 r2, 192
	stxb [r10 - 4], r2
	mov64 r7, 2
	ja LBB5_6
LBB5_5:
	mov64 r1, r2
	and64 r1, 63
	or64 r1, 128
	stxb [r10 - 1], r1
	mov64 r1, r2
	rsh64 r1, 6
	and64 r1, 63
	or64 r1, 128
	stxb [r10 - 2], r1
	mov64 r1, r2
	rsh64 r1, 12
	and64 r1, 63
	or64 r1, 128
	stxb [r10 - 3], r1
	rsh64 r2, 18
	and64 r2, 7
	or64 r2, 240
	stxb [r10 - 4], r2
	mov64 r7, 4
LBB5_6:
	ldxdw r8, [r6 + 16]
	ldxdw r1, [r6 + 0]
	sub64 r1, r8
	jge r1, r7, LBB5_8
	mov64 r1, r6
	mov64 r2, r8
	mov64 r3, r7
	call _ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$7reserve21do_reserve_and_handle17h841f8186853dc167E
	ldxdw r8, [r6 + 16]
LBB5_8:
	ldxdw r1, [r6 + 8]
	add64 r1, r8
	mov64 r2, r10
	add64 r2, -4
	mov64 r3, r7
	call memcpy
	add64 r8, r7
	stxdw [r6 + 16], r8
LBB5_12:
	mov64 r0, 0
	exit
.Lfunc_end5:
	.size	_ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$10write_char17hfde5b685689164ccE, .Lfunc_end5-_ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$10write_char17hfde5b685689164ccE

	.section	".text._ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$9write_str17h4b62f46a222bd5b2E","ax",@progbits
	.p2align	3
	.type	_ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$9write_str17h4b62f46a222bd5b2E,@function
_ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$9write_str17h4b62f46a222bd5b2E:
	mov64 r6, r3
	mov64 r7, r1
	ldxdw r8, [r7 + 16]
	ldxdw r1, [r7 + 0]
	sub64 r1, r8
	jge r1, r6, LBB6_2
	mov64 r1, r7
	mov64 r9, r2
	mov64 r2, r8
	mov64 r3, r6
	call _ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$7reserve21do_reserve_and_handle17h841f8186853dc167E
	mov64 r2, r9
	ldxdw r8, [r7 + 16]
LBB6_2:
	ldxdw r1, [r7 + 8]
	add64 r1, r8
	mov64 r3, r6
	call memcpy
	add64 r8, r6
	stxdw [r7 + 16], r8
	mov64 r0, 0
	exit
.Lfunc_end6:
	.size	_ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$9write_str17h4b62f46a222bd5b2E, .Lfunc_end6-_ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$9write_str17h4b62f46a222bd5b2E

	.section	.text._ZN5alloc7raw_vec11finish_grow17h87f821cc75349c87E,"ax",@progbits
	.p2align	3
	.type	_ZN5alloc7raw_vec11finish_grow17h87f821cc75349c87E,@function
_ZN5alloc7raw_vec11finish_grow17h87f821cc75349c87E:
	mov64 r7, r3
	mov64 r8, r2
	mov64 r6, r1
	jeq r8, 0, LBB7_2
	ldxdw r1, [r4 + 8]
	jeq r1, 0, LBB7_7
	ldxdw r2, [r4 + 16]
	jne r2, 0, LBB7_6
	jeq r7, 0, LBB7_10
	mov64 r1, r7
	mov64 r2, r8
	call __rust_alloc
	jeq r0, 0, LBB7_9
	ja LBB7_11
LBB7_2:
	stdw [r6 + 8], 0
	mov64 r1, 1
	ja LBB7_12
LBB7_6:
	ldxdw r1, [r4 + 0]
	mov64 r3, r8
	mov64 r4, r7
	call __rust_realloc
	jeq r0, 0, LBB7_9
	ja LBB7_11
LBB7_7:
	jeq r7, 0, LBB7_10
	mov64 r1, r7
	mov64 r2, r8
	call __rust_alloc
	jne r0, 0, LBB7_11
LBB7_9:
	stxdw [r6 + 16], r7
	stxdw [r6 + 8], r8
	mov64 r1, 1
	ja LBB7_12
LBB7_10:
	mov64 r7, 0
	mov64 r0, r8
LBB7_11:
	stxdw [r6 + 16], r7
	stxdw [r6 + 8], r0
	mov64 r1, 0
LBB7_12:
	stxdw [r6 + 0], r1
	exit
.Lfunc_end7:
	.size	_ZN5alloc7raw_vec11finish_grow17h87f821cc75349c87E, .Lfunc_end7-_ZN5alloc7raw_vec11finish_grow17h87f821cc75349c87E

	.section	".text.unlikely._ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$7reserve21do_reserve_and_handle17h841f8186853dc167E","ax",@progbits
	.p2align	3
	.type	_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$7reserve21do_reserve_and_handle17h841f8186853dc167E,@function
_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$7reserve21do_reserve_and_handle17h841f8186853dc167E:
	mov64 r6, r1
	mov64 r4, r2
	add64 r4, r3
	mov64 r1, 0
	mov64 r3, 1
	jlt r4, r2, LBB8_2
	mov64 r3, 0
LBB8_2:
	and64 r3, 1
	jne r3, 0, LBB8_11
	ldxdw r1, [r6 + 0]
	mov64 r7, r1
	lsh64 r7, 1
	jgt r7, r4, LBB8_5
	mov64 r7, r4
LBB8_5:
	jgt r7, 8, LBB8_7
	mov64 r7, 8
LBB8_7:
	mov64 r3, 0
	mov64 r2, r7
	xor64 r2, -1
	rsh64 r2, 63
	jeq r1, 0, LBB8_9
	ldxdw r3, [r6 + 8]
	stxdw [r10 - 8], r1
	stxdw [r10 - 24], r3
	mov64 r3, 1
LBB8_9:
	stxdw [r10 - 16], r3
	mov64 r1, r10
	add64 r1, -48
	mov64 r4, r10
	add64 r4, -24
	mov64 r3, r7
	call _ZN5alloc7raw_vec11finish_grow17h87f821cc75349c87E
	ldxdw r1, [r10 - 48]
	jeq r1, 0, LBB8_12
	ldxdw r2, [r10 - 32]
	ldxdw r1, [r10 - 40]
LBB8_11:
	call _ZN5alloc7raw_vec12handle_error17h22fdf317f3a37641E
LBB8_12:
	ldxdw r1, [r10 - 40]
	stxdw [r6 + 0], r7
	stxdw [r6 + 8], r1
	exit
.Lfunc_end8:
	.size	_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$7reserve21do_reserve_and_handle17h841f8186853dc167E, .Lfunc_end8-_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$7reserve21do_reserve_and_handle17h841f8186853dc167E

	.section	".text._ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$8grow_one17h4b15183664487c30E","ax",@progbits
	.p2align	3
	.type	_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$8grow_one17h4b15183664487c30E,@function
_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$8grow_one17h4b15183664487c30E:
	mov64 r6, r1
	ldxdw r3, [r6 + 0]
	mov64 r4, r3
	add64 r4, 1
	mov64 r1, 0
	mov64 r5, 1
	jeq r4, 0, LBB9_2
	mov64 r5, 0
LBB9_2:
	and64 r5, 1
	jne r5, 0, LBB9_11
	mov64 r7, r3
	lsh64 r7, 1
	jgt r7, r4, LBB9_5
	mov64 r7, r4
LBB9_5:
	jgt r7, 8, LBB9_7
	mov64 r7, 8
LBB9_7:
	mov64 r2, r7
	xor64 r2, -1
	rsh64 r2, 63
	jeq r3, 0, LBB9_9
	ldxdw r1, [r6 + 8]
	stxdw [r10 - 8], r3
	stxdw [r10 - 24], r1
	mov64 r1, 1
LBB9_9:
	stxdw [r10 - 16], r1
	mov64 r1, r10
	add64 r1, -48
	mov64 r4, r10
	add64 r4, -24
	mov64 r3, r7
	call _ZN5alloc7raw_vec11finish_grow17h87f821cc75349c87E
	ldxdw r1, [r10 - 48]
	jeq r1, 0, LBB9_12
	ldxdw r2, [r10 - 32]
	ldxdw r1, [r10 - 40]
LBB9_11:
	call _ZN5alloc7raw_vec12handle_error17h22fdf317f3a37641E
LBB9_12:
	ldxdw r1, [r10 - 40]
	stxdw [r6 + 0], r7
	stxdw [r6 + 8], r1
	exit
.Lfunc_end9:
	.size	_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$8grow_one17h4b15183664487c30E, .Lfunc_end9-_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$8grow_one17h4b15183664487c30E

	.section	.text.main34_validate,"ax",@progbits
	.globl	main34_validate
	.p2align	3
	.type	main34_validate,@function
main34_validate:
	mov64 r6, r1
	ldxb r1, [r2 + 40]
	jne r1, 0, LBB10_29
	and64 r3, -3
	ldxdw r7, [r5 - 4080]
	ldxdw r8, [r5 - 4088]
	ldxdw r9, [r5 - 4096]
	ldxb r1, [r2 + 41]
	jeq r1, 0, LBB10_5
	and64 r3, 255
	jeq r3, 0, LBB10_3
	ja LBB10_11
LBB10_3:
	mov64 r1, r10
	add64 r1, -96
	lddw r2, .Lalloc_8f95cb73e89711d65e95d13598508b19
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 83
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r8, r0
	stdw [r10 - 328], 0
	stdw [r10 - 336], 1
	stdw [r10 - 344], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -344
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_8f95cb73e89711d65e95d13598508b19
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB10_9
	ja LBB10_30
LBB10_5:
	and64 r3, 255
	jeq r3, 0, LBB10_6
	ja LBB10_10
LBB10_6:
	ldxb r1, [r8 + 0]
	jeq r1, 0, LBB10_7
	ja LBB10_20
LBB10_7:
	mov64 r1, r10
	add64 r1, -312
	lddw r2, .Lalloc_1ba5e1e397ae92b788c97e688ac0b362
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 89
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 80], 0
	stdw [r10 - 88], 1
	stdw [r10 - 96], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -96
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_1ba5e1e397ae92b788c97e688ac0b362
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB10_15
	ja LBB10_30
LBB10_9:
	ldxdw r1, [r10 - 328]
	stxdw [r10 - 216], r1
	ldxdw r1, [r10 - 336]
	stxdw [r10 - 224], r1
	ldxdw r1, [r10 - 344]
	stxdw [r10 - 232], r1
	ldxdw r1, [r10 - 96]
	stxdw [r10 - 256], r1
	ldxdw r1, [r10 - 88]
	stxdw [r10 - 248], r1
	ldxdw r1, [r10 - 80]
	stxdw [r10 - 240], r1
	stxw [r10 - 136], r8
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stb [r10 - 208], 2
	stw [r10 - 264], 24
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -408
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 408]
	ldxdw r2, [r10 - 400]
	ldxb r3, [r7 + 0]
	ja LBB10_32
LBB10_10:
	ldxb r1, [r2 + 44]
	jeq r1, 0, LBB10_17
LBB10_11:
	ldxb r1, [r8 + 0]
	jeq r1, 0, LBB10_35
	mov64 r1, r10
	add64 r1, -96
	lddw r2, .Lalloc_b5f839a6bda937f2cae73e49fc88071f
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 90
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 328], 0
	stdw [r10 - 336], 1
	stdw [r10 - 344], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -344
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_b5f839a6bda937f2cae73e49fc88071f
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB10_14
	ja LBB10_30
LBB10_14:
	ldxdw r1, [r10 - 328]
	stxdw [r10 - 216], r1
	ldxdw r1, [r10 - 336]
	stxdw [r10 - 224], r1
	ldxdw r1, [r10 - 344]
	stxdw [r10 - 232], r1
	ldxdw r1, [r10 - 96]
	stxdw [r10 - 256], r1
	ldxdw r1, [r10 - 88]
	stxdw [r10 - 248], r1
	ldxdw r1, [r10 - 80]
	stxdw [r10 - 240], r1
	stxw [r10 - 136], r7
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stb [r10 - 208], 2
	stw [r10 - 264], 33
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -424
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 424]
	ldxdw r2, [r10 - 416]
	ja LBB10_32
LBB10_15:
	ldxdw r1, [r10 - 80]
	stxdw [r10 - 216], r1
	ldxdw r1, [r10 - 88]
	stxdw [r10 - 224], r1
	ldxdw r1, [r10 - 96]
	stxdw [r10 - 232], r1
	ldxdw r1, [r10 - 312]
	stxdw [r10 - 256], r1
	ldxdw r1, [r10 - 304]
	stxdw [r10 - 248], r1
	ldxdw r1, [r10 - 296]
	stxdw [r10 - 240], r1
	stxw [r10 - 136], r7
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stb [r10 - 208], 2
	stw [r10 - 264], 41
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -568
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 560]
	ldxdw r2, [r10 - 568]
LBB10_16:
	stxdw [r6 + 8], r2
	stxdw [r6 + 16], r1
	ja LBB10_33
LBB10_17:
	mov64 r1, r10
	add64 r1, -96
	lddw r2, .Lalloc_f94f166953c814e4161e699857179a1e
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 84
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 328], 0
	stdw [r10 - 336], 1
	stdw [r10 - 344], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -344
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_f94f166953c814e4161e699857179a1e
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB10_19
	ja LBB10_30
LBB10_19:
	ldxdw r1, [r10 - 328]
	stxdw [r10 - 216], r1
	ldxdw r1, [r10 - 336]
	stxdw [r10 - 224], r1
	ldxdw r1, [r10 - 344]
	stxdw [r10 - 232], r1
	ldxdw r1, [r10 - 96]
	stxdw [r10 - 256], r1
	ldxdw r1, [r10 - 88]
	stxdw [r10 - 248], r1
	ldxdw r1, [r10 - 80]
	stxdw [r10 - 240], r1
	stxw [r10 - 136], r7
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stb [r10 - 208], 2
	stw [r10 - 264], 31
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -440
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 440]
	ldxdw r2, [r10 - 432]
	ja LBB10_32
LBB10_20:
	stxdw [r10 - 584], r4
	stxdw [r10 - 592], r2
	ldxdw r1, [r5 - 4072]
	stxdw [r10 - 576], r1
	ldxdw r1, [r8 + 25]
	stxdw [r10 - 320], r1
	ldxdw r1, [r8 + 17]
	stxdw [r10 - 328], r1
	ldxdw r1, [r8 + 9]
	stxdw [r10 - 336], r1
	ldxdw r1, [r8 + 1]
	stxdw [r10 - 344], r1
	stdw [r10 - 264], 0
	stdw [r10 - 272], 0
	stdw [r10 - 280], 0
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -344
	mov64 r2, r10
	add64 r2, -288
	mov64 r3, 32
	call memcmp
	add64 r8, 1
	lsh64 r0, 32
	rsh64 r0, 32
	jeq r0, 0, LBB10_24
	mov64 r1, r10
	add64 r1, -344
	ldxdw r2, [r10 - 576]
	mov64 r3, 32
	call memcmp
	lsh64 r0, 32
	rsh64 r0, 32
	jne r0, 0, LBB10_22
	ja LBB10_23
LBB10_22:
	mov64 r1, r10
	add64 r1, -344
	mov64 r2, r7
	mov64 r3, 32
	call memcmp
	lsh64 r0, 32
	rsh64 r0, 32
	jne r0, 0, LBB10_25
LBB10_23:
	ldxb r1, [r7 + 0]
	ldxb r1, [r7 + 0]
	ldxb r1, [r7 + 0]
	ldxb r1, [r7 + 0]
	ldxb r1, [r7 + 0]
	ldxb r1, [r7 + 0]
	ldxb r1, [r7 + 0]
	ldxb r1, [r7 + 0]
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_861c8964bbad6d9cede9df277e628fe9
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 19
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -232
	lddw r2, .Lalloc_861c8964bbad6d9cede9df277e628fe9
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stxw [r10 - 136], r7
	stb [r10 - 208], 2
	stw [r10 - 264], 47
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -520
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 512]
	ldxdw r2, [r10 - 520]
	ja LBB10_16
LBB10_24:
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_0e3505805f4905816c1bd644811a7869
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 30
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -232
	lddw r2, .Lalloc_0e3505805f4905816c1bd644811a7869
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stxw [r10 - 136], r7
	stb [r10 - 208], 2
	stw [r10 - 264], 42
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -536
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r3, [r10 - 528]
	ldxdw r2, [r10 - 536]
	ldxdw r1, [r8 + 24]
	stxdw [r10 - 264], r1
	ldxdw r1, [r8 + 16]
	stxdw [r10 - 272], r1
	ldxdw r1, [r8 + 8]
	stxdw [r10 - 280], r1
	ldxdw r1, [r8 + 0]
	stxdw [r10 - 288], r1
	stdw [r10 - 256], 0
	stdw [r10 - 248], 0
	stdw [r10 - 240], 0
	stdw [r10 - 232], 0
	mov64 r1, r10
	add64 r1, -552
	mov64 r4, r10
	add64 r4, -288
	call _ZN11anchor_lang5error5Error12with_pubkeys17hca6dbbbe6a9a5da7E
	ldxdw r1, [r10 - 544]
	ldxdw r2, [r10 - 552]
	ja LBB10_16
LBB10_25:
	ldxw r1, [r8 + 0]
	stxw [r10 - 312], r1
	ldxw r1, [r8 + 3]
	stxw [r10 - 309], r1
	ldxdw r1, [r8 + 8]
	stxdw [r10 - 280], r1
	ldxdw r1, [r8 + 0]
	stxdw [r10 - 288], r1
	ldxdw r1, [r8 + 16]
	stxdw [r10 - 272], r1
	ldxdw r1, [r8 + 24]
	stxdw [r10 - 264], r1
	ldxdw r1, [r10 - 281]
	stxdw [r10 - 376], r1
	ldxdw r1, [r10 - 273]
	stxdw [r10 - 368], r1
	ldxdw r1, [r10 - 265]
	stxdw [r10 - 360], r1
	ldxb r1, [r10 - 257]
	stxb [r10 - 352], r1
	ldxdw r2, [r10 - 592]
	ldxdw r1, [r10 - 584]
	jeq r1, 0, LBB10_36
	ldxb r1, [r2 + 43]
	jne r1, 0, LBB10_38
	ldxb r1, [r2 + 42]
	jeq r1, 0, LBB10_41
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_835bb996f1795bf0338da0490417da62
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 80
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -232
	lddw r2, .Lalloc_835bb996f1795bf0338da0490417da62
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stxw [r10 - 136], r7
	stb [r10 - 208], 2
	stw [r10 - 264], 65
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -472
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 472]
	ldxdw r2, [r10 - 464]
	ja LBB10_32
LBB10_29:
	mov64 r1, r10
	add64 r1, -376
	lddw r2, .Lalloc_eb4f91695bc6f999067c65f428fcc4d8
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 88
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 328], 0
	stdw [r10 - 336], 1
	stdw [r10 - 344], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -344
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_eb4f91695bc6f999067c65f428fcc4d8
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB10_31
LBB10_30:
	mov64 r3, r10
	add64 r3, -1
	lddw r1, .Lalloc_cc656815297f75969399c3f4b1ad3de4
	mov64 r2, 55
	lddw r4, .Lvtable.1
	lddw r5, .Lalloc_d5d9fccaf545b6e0545ef73245a3c43f
	call _ZN4core6result13unwrap_failed17h2dbd2ef42161686dE
LBB10_31:
	ldxdw r1, [r10 - 328]
	stxdw [r10 - 216], r1
	ldxdw r1, [r10 - 336]
	stxdw [r10 - 224], r1
	ldxdw r1, [r10 - 344]
	stxdw [r10 - 232], r1
	ldxdw r1, [r10 - 376]
	stxdw [r10 - 256], r1
	ldxdw r1, [r10 - 368]
	stxdw [r10 - 248], r1
	ldxdw r1, [r10 - 360]
	stxdw [r10 - 240], r1
	stxw [r10 - 136], r7
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stb [r10 - 208], 2
	stw [r10 - 264], 19
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -392
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 392]
	ldxdw r2, [r10 - 384]
LBB10_32:
	stxdw [r6 + 16], r2
	stxdw [r6 + 8], r1
LBB10_33:
	stb [r6 + 0], 1
LBB10_34:
	exit
LBB10_35:
	ldxw r1, [r7 + 3]
	stxw [r10 - 309], r1
	ldxw r1, [r7 + 0]
	stxw [r10 - 312], r1
	ldxdw r1, [r7 + 7]
	stxdw [r10 - 376], r1
	ldxdw r1, [r7 + 15]
	stxdw [r10 - 368], r1
	ldxdw r1, [r7 + 23]
	stxdw [r10 - 360], r1
	ldxb r1, [r7 + 31]
	stxb [r10 - 352], r1
	jne r4, 0, LBB10_37
LBB10_36:
	ldxdw r1, [r10 - 368]
	stxdw [r10 - 113], r1
	ldxdw r1, [r10 - 376]
	stxdw [r10 - 121], r1
	ldxb r1, [r10 - 352]
	stxb [r10 - 97], r1
	ldxdw r1, [r10 - 360]
	stxdw [r10 - 105], r1
	ldxw r1, [r10 - 309]
	stxw [r10 - 125], r1
	ldxw r1, [r10 - 312]
	stxw [r10 - 128], r1
	ldxdw r1, [r10 - 120]
	stxdw [r6 + 9], r1
	ldxdw r1, [r10 - 112]
	stxdw [r6 + 17], r1
	ldxdw r1, [r10 - 104]
	stxdw [r6 + 25], r1
	ldxdw r1, [r10 - 128]
	stxdw [r6 + 1], r1
	stb [r6 + 0], 0
	ja LBB10_34
LBB10_37:
	ldxb r1, [r2 + 43]
	jeq r1, 0, LBB10_41
LBB10_38:
	mov64 r1, r10
	add64 r1, -96
	lddw r2, .Lalloc_e75cefee4bb91125af0ea8444b842ed0
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 91
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 328], 0
	stdw [r10 - 336], 1
	stdw [r10 - 344], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -344
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_e75cefee4bb91125af0ea8444b842ed0
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB10_40
	ja LBB10_30
LBB10_40:
	ldxdw r1, [r10 - 328]
	stxdw [r10 - 216], r1
	ldxdw r1, [r10 - 336]
	stxdw [r10 - 224], r1
	ldxdw r1, [r10 - 344]
	stxdw [r10 - 232], r1
	ldxdw r1, [r10 - 96]
	stxdw [r10 - 256], r1
	ldxdw r1, [r10 - 88]
	stxdw [r10 - 248], r1
	ldxdw r1, [r10 - 80]
	stxdw [r10 - 240], r1
	stxw [r10 - 136], r7
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stb [r10 - 208], 2
	stw [r10 - 264], 61
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -456
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 456]
	ldxdw r2, [r10 - 448]
	ja LBB10_32
LBB10_41:
	ldxb r1, [r7 + 0]
	ldxb r1, [r2 + 45]
	jeq r1, 0, LBB10_44
	add64 r9, -1
	ldxdw r1, [r2 + 32]
	jlt r9, r1, LBB10_45
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_973adb9e8664e25d4750ddb14e0de56a
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 78
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -232
	lddw r2, .Lalloc_973adb9e8664e25d4750ddb14e0de56a
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stxw [r10 - 136], r7
	stb [r10 - 208], 2
	stw [r10 - 264], 73
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -488
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 488]
	ldxdw r2, [r10 - 480]
	ja LBB10_32
LBB10_44:
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_01eaaa187d2be542d4425f23ab284310
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 77
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -232
	lddw r2, .Lalloc_01eaaa187d2be542d4425f23ab284310
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stxw [r10 - 136], r7
	stb [r10 - 208], 2
	stw [r10 - 264], 69
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -504
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 504]
	ldxdw r2, [r10 - 496]
	ja LBB10_32
LBB10_45:
	ldxb r1, [r7 + 0]
	ja LBB10_36
.Lfunc_end10:
	.size	main34_validate, .Lfunc_end10-main34_validate

	.section	.text.custom_mir_validate,"ax",@progbits
	.globl	custom_mir_validate
	.p2align	3
	.type	custom_mir_validate,@function
custom_mir_validate:
	mov64 r6, r1
	ldxb r1, [r2 + 40]
	jne r1, 0, LBB11_32
	and64 r3, -3
	ldxdw r7, [r5 - 4080]
	ldxdw r9, [r5 - 4088]
	ldxdw r8, [r5 - 4096]
	ldxb r1, [r2 + 41]
	jeq r1, 0, LBB11_5
	and64 r3, 255
	jeq r3, 0, LBB11_3
	ja LBB11_11
LBB11_3:
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_8f95cb73e89711d65e95d13598508b19
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 83
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r8, r0
	stdw [r10 - 272], 0
	stdw [r10 - 280], 1
	stdw [r10 - 288], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -288
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_8f95cb73e89711d65e95d13598508b19
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB11_9
	ja LBB11_33
LBB11_5:
	and64 r3, 255
	jeq r3, 0, LBB11_6
	ja LBB11_10
LBB11_6:
	ldxb r1, [r9 + 0]
	jeq r1, 0, LBB11_7
	ja LBB11_15
LBB11_7:
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_1ba5e1e397ae92b788c97e688ac0b362
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 89
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 304], 0
	stdw [r10 - 312], 1
	stdw [r10 - 320], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -320
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_1ba5e1e397ae92b788c97e688ac0b362
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB11_21
	ja LBB11_33
LBB11_9:
	ldxdw r1, [r10 - 272]
	stxdw [r10 - 160], r1
	ldxdw r1, [r10 - 280]
	stxdw [r10 - 168], r1
	ldxdw r1, [r10 - 288]
	stxdw [r10 - 176], r1
	ldxdw r1, [r10 - 256]
	stxdw [r10 - 200], r1
	ldxdw r1, [r10 - 248]
	stxdw [r10 - 192], r1
	ldxdw r1, [r10 - 240]
	stxdw [r10 - 184], r1
	stxw [r10 - 80], r8
	lddw r1, .Lalloc_ebe040a358b3132776a16f34a7b7aa5b
	stxdw [r10 - 224], r1
	stb [r10 - 152], 2
	stw [r10 - 208], 289
	stdw [r10 - 216], 38
	stdw [r10 - 232], 0
	mov64 r1, r10
	add64 r1, -352
	mov64 r2, r10
	add64 r2, -232
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 352]
	ldxdw r2, [r10 - 344]
	ldxb r3, [r7 + 0]
	ja LBB11_35
LBB11_10:
	ldxb r1, [r2 + 44]
	jeq r1, 0, LBB11_23
LBB11_11:
	ldxb r1, [r9 + 0]
	jeq r1, 0, LBB11_38
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_b5f839a6bda937f2cae73e49fc88071f
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 90
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 272], 0
	stdw [r10 - 280], 1
	stdw [r10 - 288], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -288
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_b5f839a6bda937f2cae73e49fc88071f
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB11_14
	ja LBB11_33
LBB11_14:
	ldxdw r1, [r10 - 272]
	stxdw [r10 - 160], r1
	ldxdw r1, [r10 - 280]
	stxdw [r10 - 168], r1
	ldxdw r1, [r10 - 288]
	stxdw [r10 - 176], r1
	ldxdw r1, [r10 - 256]
	stxdw [r10 - 200], r1
	ldxdw r1, [r10 - 248]
	stxdw [r10 - 192], r1
	ldxdw r1, [r10 - 240]
	stxdw [r10 - 184], r1
	stxw [r10 - 80], r7
	lddw r1, .Lalloc_ebe040a358b3132776a16f34a7b7aa5b
	stxdw [r10 - 224], r1
	stb [r10 - 152], 2
	stw [r10 - 208], 298
	stdw [r10 - 216], 38
	stdw [r10 - 232], 0
	mov64 r1, r10
	add64 r1, -368
	mov64 r2, r10
	add64 r2, -232
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 368]
	ldxdw r2, [r10 - 360]
	ja LBB11_35
LBB11_15:
	ldxdw r5, [r5 - 4072]
	ldxb r1, [r7 + 0]
	ldxb r3, [r7 + 0]
	jeq r1, r3, LBB11_16
	ja LBB11_20
LBB11_16:
	stxdw [r10 - 520], r5
	stxdw [r10 - 528], r4
	stxdw [r10 - 536], r2
	ldxdw r1, [r9 + 25]
	stxdw [r10 - 264], r1
	ldxdw r1, [r9 + 17]
	stxdw [r10 - 272], r1
	ldxdw r1, [r9 + 9]
	stxdw [r10 - 280], r1
	ldxdw r1, [r9 + 1]
	stxdw [r10 - 288], r1
	stdw [r10 - 208], 0
	stdw [r10 - 216], 0
	stdw [r10 - 224], 0
	stdw [r10 - 232], 0
	mov64 r1, r10
	add64 r1, -288
	mov64 r2, r10
	add64 r2, -232
	mov64 r3, 32
	call memcmp
	add64 r9, 1
	lsh64 r0, 32
	rsh64 r0, 32
	jeq r0, 0, LBB11_27
	mov64 r1, r10
	add64 r1, -288
	mov64 r2, r7
	mov64 r3, 32
	call memcmp
	lsh64 r0, 32
	rsh64 r0, 32
	jne r0, 0, LBB11_18
	ja LBB11_19
LBB11_18:
	mov64 r1, r10
	add64 r1, -288
	ldxdw r2, [r10 - 520]
	mov64 r3, 32
	call memcmp
	lsh64 r0, 32
	rsh64 r0, 32
	jne r0, 0, LBB11_28
LBB11_19:
	ldxb r1, [r7 + 0]
	ldxb r2, [r7 + 0]
	jeq r1, r2, LBB11_26
LBB11_20:
	ldxb r1, [r7 + 0]
	call abort
LBB11_21:
	ldxdw r1, [r10 - 304]
	stxdw [r10 - 160], r1
	ldxdw r1, [r10 - 312]
	stxdw [r10 - 168], r1
	ldxdw r1, [r10 - 320]
	stxdw [r10 - 176], r1
	ldxdw r1, [r10 - 256]
	stxdw [r10 - 200], r1
	ldxdw r1, [r10 - 248]
	stxdw [r10 - 192], r1
	ldxdw r1, [r10 - 240]
	stxdw [r10 - 184], r1
	stxw [r10 - 80], r7
	lddw r1, .Lalloc_ebe040a358b3132776a16f34a7b7aa5b
	stxdw [r10 - 224], r1
	stb [r10 - 152], 2
	stw [r10 - 208], 306
	stdw [r10 - 216], 38
	stdw [r10 - 232], 0
	mov64 r1, r10
	add64 r1, -512
	mov64 r2, r10
	add64 r2, -232
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 504]
	ldxdw r2, [r10 - 512]
LBB11_22:
	stxdw [r6 + 8], r2
	stxdw [r6 + 16], r1
	ja LBB11_36
LBB11_23:
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_f94f166953c814e4161e699857179a1e
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 84
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 272], 0
	stdw [r10 - 280], 1
	stdw [r10 - 288], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -288
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_f94f166953c814e4161e699857179a1e
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB11_25
	ja LBB11_33
LBB11_25:
	ldxdw r1, [r10 - 272]
	stxdw [r10 - 160], r1
	ldxdw r1, [r10 - 280]
	stxdw [r10 - 168], r1
	ldxdw r1, [r10 - 288]
	stxdw [r10 - 176], r1
	ldxdw r1, [r10 - 256]
	stxdw [r10 - 200], r1
	ldxdw r1, [r10 - 248]
	stxdw [r10 - 192], r1
	ldxdw r1, [r10 - 240]
	stxdw [r10 - 184], r1
	stxw [r10 - 80], r7
	lddw r1, .Lalloc_ebe040a358b3132776a16f34a7b7aa5b
	stxdw [r10 - 224], r1
	stb [r10 - 152], 2
	stw [r10 - 208], 296
	stdw [r10 - 216], 38
	stdw [r10 - 232], 0
	mov64 r1, r10
	add64 r1, -384
	mov64 r2, r10
	add64 r2, -232
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 384]
	ldxdw r2, [r10 - 376]
	ja LBB11_35
LBB11_26:
	mov64 r1, r10
	add64 r1, -200
	lddw r2, .Lalloc_861c8964bbad6d9cede9df277e628fe9
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 19
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -176
	lddw r2, .Lalloc_861c8964bbad6d9cede9df277e628fe9
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_ebe040a358b3132776a16f34a7b7aa5b
	stxdw [r10 - 224], r1
	stxw [r10 - 80], r7
	stb [r10 - 152], 2
	stw [r10 - 208], 312
	stdw [r10 - 216], 38
	stdw [r10 - 232], 0
	mov64 r1, r10
	add64 r1, -464
	mov64 r2, r10
	add64 r2, -232
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 456]
	ldxdw r2, [r10 - 464]
	ja LBB11_22
LBB11_27:
	mov64 r1, r10
	add64 r1, -200
	lddw r2, .Lalloc_0e3505805f4905816c1bd644811a7869
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 30
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -176
	lddw r2, .Lalloc_0e3505805f4905816c1bd644811a7869
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_ebe040a358b3132776a16f34a7b7aa5b
	stxdw [r10 - 224], r1
	stxw [r10 - 80], r7
	stb [r10 - 152], 2
	stw [r10 - 208], 307
	stdw [r10 - 216], 38
	stdw [r10 - 232], 0
	mov64 r1, r10
	add64 r1, -480
	mov64 r2, r10
	add64 r2, -232
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r3, [r10 - 472]
	ldxdw r2, [r10 - 480]
	ldxdw r1, [r9 + 24]
	stxdw [r10 - 208], r1
	ldxdw r1, [r9 + 16]
	stxdw [r10 - 216], r1
	ldxdw r1, [r9 + 8]
	stxdw [r10 - 224], r1
	ldxdw r1, [r9 + 0]
	stxdw [r10 - 232], r1
	stdw [r10 - 200], 0
	stdw [r10 - 192], 0
	stdw [r10 - 184], 0
	stdw [r10 - 176], 0
	mov64 r1, r10
	add64 r1, -496
	mov64 r4, r10
	add64 r4, -232
	call _ZN11anchor_lang5error5Error12with_pubkeys17hca6dbbbe6a9a5da7E
	ldxdw r1, [r10 - 488]
	ldxdw r2, [r10 - 496]
	ja LBB11_22
LBB11_28:
	ldxdw r1, [r9 + 24]
	stxdw [r10 - 296], r1
	ldxdw r1, [r9 + 16]
	stxdw [r10 - 304], r1
	ldxdw r1, [r9 + 8]
	stxdw [r10 - 312], r1
	ldxdw r1, [r9 + 0]
	stxdw [r10 - 320], r1
	ldxdw r2, [r10 - 536]
	ldxdw r1, [r10 - 528]
	jeq r1, 0, LBB11_39
	ldxb r1, [r2 + 43]
	jne r1, 0, LBB11_41
	ldxb r1, [r2 + 42]
	jeq r1, 0, LBB11_44
	mov64 r1, r10
	add64 r1, -200
	lddw r2, .Lalloc_835bb996f1795bf0338da0490417da62
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 80
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -176
	lddw r2, .Lalloc_835bb996f1795bf0338da0490417da62
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_ebe040a358b3132776a16f34a7b7aa5b
	stxdw [r10 - 224], r1
	stxw [r10 - 80], r7
	stb [r10 - 152], 2
	stw [r10 - 208], 330
	stdw [r10 - 216], 38
	stdw [r10 - 232], 0
	mov64 r1, r10
	add64 r1, -416
	mov64 r2, r10
	add64 r2, -232
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 416]
	ldxdw r2, [r10 - 408]
	ja LBB11_35
LBB11_32:
	mov64 r1, r10
	add64 r1, -320
	lddw r2, .Lalloc_eb4f91695bc6f999067c65f428fcc4d8
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 88
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 272], 0
	stdw [r10 - 280], 1
	stdw [r10 - 288], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -288
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_eb4f91695bc6f999067c65f428fcc4d8
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB11_34
LBB11_33:
	mov64 r3, r10
	add64 r3, -1
	lddw r1, .Lalloc_cc656815297f75969399c3f4b1ad3de4
	mov64 r2, 55
	lddw r4, .Lvtable.1
	lddw r5, .Lalloc_d5d9fccaf545b6e0545ef73245a3c43f
	call _ZN4core6result13unwrap_failed17h2dbd2ef42161686dE
LBB11_34:
	ldxdw r1, [r10 - 272]
	stxdw [r10 - 160], r1
	ldxdw r1, [r10 - 280]
	stxdw [r10 - 168], r1
	ldxdw r1, [r10 - 288]
	stxdw [r10 - 176], r1
	ldxdw r1, [r10 - 320]
	stxdw [r10 - 200], r1
	ldxdw r1, [r10 - 312]
	stxdw [r10 - 192], r1
	ldxdw r1, [r10 - 304]
	stxdw [r10 - 184], r1
	stxw [r10 - 80], r7
	lddw r1, .Lalloc_ebe040a358b3132776a16f34a7b7aa5b
	stxdw [r10 - 224], r1
	stb [r10 - 152], 2
	stw [r10 - 208], 284
	stdw [r10 - 216], 38
	stdw [r10 - 232], 0
	mov64 r1, r10
	add64 r1, -336
	mov64 r2, r10
	add64 r2, -232
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 336]
	ldxdw r2, [r10 - 328]
LBB11_35:
	stxdw [r6 + 16], r2
	stxdw [r6 + 8], r1
LBB11_36:
	stb [r6 + 0], 1
LBB11_37:
	exit
LBB11_38:
	ldxdw r1, [r7 + 24]
	stxdw [r10 - 296], r1
	ldxdw r1, [r7 + 16]
	stxdw [r10 - 304], r1
	ldxdw r1, [r7 + 8]
	stxdw [r10 - 312], r1
	ldxdw r1, [r7 + 0]
	stxdw [r10 - 320], r1
	jne r4, 0, LBB11_40
LBB11_39:
	ldxdw r1, [r10 - 296]
	stxdw [r6 + 25], r1
	ldxdw r1, [r10 - 304]
	stxdw [r6 + 17], r1
	ldxdw r1, [r10 - 312]
	stxdw [r6 + 9], r1
	ldxdw r1, [r10 - 320]
	stxdw [r6 + 1], r1
	stb [r6 + 0], 0
	ja LBB11_37
LBB11_40:
	ldxb r1, [r2 + 43]
	jeq r1, 0, LBB11_44
LBB11_41:
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_e75cefee4bb91125af0ea8444b842ed0
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 91
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 272], 0
	stdw [r10 - 280], 1
	stdw [r10 - 288], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -288
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_e75cefee4bb91125af0ea8444b842ed0
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB11_43
	ja LBB11_33
LBB11_43:
	ldxdw r1, [r10 - 272]
	stxdw [r10 - 160], r1
	ldxdw r1, [r10 - 280]
	stxdw [r10 - 168], r1
	ldxdw r1, [r10 - 288]
	stxdw [r10 - 176], r1
	ldxdw r1, [r10 - 256]
	stxdw [r10 - 200], r1
	ldxdw r1, [r10 - 248]
	stxdw [r10 - 192], r1
	ldxdw r1, [r10 - 240]
	stxdw [r10 - 184], r1
	stxw [r10 - 80], r7
	lddw r1, .Lalloc_ebe040a358b3132776a16f34a7b7aa5b
	stxdw [r10 - 224], r1
	stb [r10 - 152], 2
	stw [r10 - 208], 326
	stdw [r10 - 216], 38
	stdw [r10 - 232], 0
	mov64 r1, r10
	add64 r1, -400
	mov64 r2, r10
	add64 r2, -232
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 400]
	ldxdw r2, [r10 - 392]
	ja LBB11_35
LBB11_44:
	ldxb r1, [r2 + 45]
	jeq r1, 0, LBB11_47
	add64 r8, -1
	ldxdw r1, [r2 + 32]
	jlt r8, r1, LBB11_48
	mov64 r1, r10
	add64 r1, -200
	lddw r2, .Lalloc_973adb9e8664e25d4750ddb14e0de56a
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 78
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -176
	lddw r2, .Lalloc_973adb9e8664e25d4750ddb14e0de56a
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_ebe040a358b3132776a16f34a7b7aa5b
	stxdw [r10 - 224], r1
	stxw [r10 - 80], r7
	stb [r10 - 152], 2
	stw [r10 - 208], 338
	stdw [r10 - 216], 38
	stdw [r10 - 232], 0
	mov64 r1, r10
	add64 r1, -432
	mov64 r2, r10
	add64 r2, -232
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 432]
	ldxdw r2, [r10 - 424]
	ja LBB11_35
LBB11_47:
	mov64 r1, r10
	add64 r1, -200
	lddw r2, .Lalloc_01eaaa187d2be542d4425f23ab284310
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 77
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -176
	lddw r2, .Lalloc_01eaaa187d2be542d4425f23ab284310
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_ebe040a358b3132776a16f34a7b7aa5b
	stxdw [r10 - 224], r1
	stxw [r10 - 80], r7
	stb [r10 - 152], 2
	stw [r10 - 208], 334
	stdw [r10 - 216], 38
	stdw [r10 - 232], 0
	mov64 r1, r10
	add64 r1, -448
	mov64 r2, r10
	add64 r2, -232
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 448]
	ldxdw r2, [r10 - 440]
	ja LBB11_35
LBB11_48:
	ldxb r1, [r7 + 0]
	ja LBB11_39
.Lfunc_end11:
	.size	custom_mir_validate, .Lfunc_end11-custom_mir_validate

	.section	.text.actual_curve_size,"ax",@progbits
	.globl	actual_curve_size
	.p2align	3
	.type	actual_curve_size,@function
actual_curve_size:
	mov64 r0, 160
	exit
.Lfunc_end12:
	.size	actual_curve_size, .Lfunc_end12-actual_curve_size

	.section	.text.actual_account_size,"ax",@progbits
	.globl	actual_account_size
	.p2align	3
	.type	actual_account_size,@function
actual_account_size:
	mov64 r0, 168
	exit
.Lfunc_end13:
	.size	actual_account_size, .Lfunc_end13-actual_account_size

	.section	.text.actual_box_size,"ax",@progbits
	.globl	actual_box_size
	.p2align	3
	.type	actual_box_size,@function
actual_box_size:
	mov64 r0, 8
	exit
.Lfunc_end14:
	.size	actual_box_size, .Lfunc_end14-actual_box_size

	.section	.text.actual_curve_holder_offset,"ax",@progbits
	.globl	actual_curve_holder_offset
	.p2align	3
	.type	actual_curve_holder_offset,@function
actual_curve_holder_offset:
	mov64 r0, 157
	exit
.Lfunc_end15:
	.size	actual_curve_holder_offset, .Lfunc_end15-actual_curve_holder_offset

	.section	.text.actual_account_holder_offset,"ax",@progbits
	.globl	actual_account_holder_offset
	.p2align	3
	.type	actual_account_holder_offset,@function
actual_account_holder_offset:
	mov64 r0, 165
	exit
.Lfunc_end16:
	.size	actual_account_holder_offset, .Lfunc_end16-actual_account_holder_offset

	.section	.text.actual_account_raw_hold,"ax",@progbits
	.globl	actual_account_raw_hold
	.p2align	3
	.type	actual_account_raw_hold,@function
actual_account_raw_hold:
	ldxdw r1, [r1 + 0]
	ldxb r0, [r1 + 165]
	exit
.Lfunc_end17:
	.size	actual_account_raw_hold, .Lfunc_end17-actual_account_raw_hold

	.section	.text.actual_account_holder,"ax",@progbits
	.globl	actual_account_holder
	.p2align	3
	.type	actual_account_holder,@function
actual_account_holder:
	ldxdw r1, [r1 + 0]
	ldxb r0, [r1 + 165]
	exit
.Lfunc_end18:
	.size	actual_account_holder, .Lfunc_end18-actual_account_holder

	.section	.text.actual_clone,"ax",@progbits
	.globl	actual_clone
	.p2align	3
	.type	actual_clone,@function
actual_clone:
	ldxdw r3, [r2 + 8]
	ldxdw r5, [r3 + 0]
	add64 r5, 1
	mov64 r0, 1
	jeq r5, 0, LBB19_2
	mov64 r0, 0
LBB19_2:
	ldxdw r4, [r2 + 0]
	stxdw [r3 + 0], r5
	jne r0, 1, LBB19_4
LBB19_3:
	call abort
LBB19_4:
	ldxdw r5, [r2 + 16]
	ldxdw r0, [r5 + 0]
	add64 r0, 1
	mov64 r6, 1
	jeq r0, 0, LBB19_6
	mov64 r6, 0
LBB19_6:
	stxdw [r5 + 0], r0
	jne r6, 1, LBB19_8
	ja LBB19_3
LBB19_8:
	ldxdw r0, [r2 + 24]
	ldxdw r6, [r2 + 32]
	ldxb r7, [r2 + 40]
	ldxb r8, [r2 + 41]
	ldxb r2, [r2 + 42]
	stxb [r10 - 6], r2
	stxb [r10 - 7], r8
	stxb [r10 - 8], r7
	stxdw [r10 - 16], r6
	stxdw [r10 - 24], r0
	stxdw [r10 - 32], r5
	stxdw [r10 - 40], r3
	stxdw [r10 - 48], r4
	mov64 r2, r10
	add64 r2, -48
	mov64 r3, 48
	call memcpy
	exit
.Lfunc_end19:
	.size	actual_clone, .Lfunc_end19-actual_clone

	.section	.text.nested_outer_none,"ax",@progbits
	.globl	nested_outer_none
	.p2align	3
	.type	nested_outer_none,@function
nested_outer_none:
	mov64 r0, 2
	exit
.Lfunc_end20:
	.size	nested_outer_none, .Lfunc_end20-nested_outer_none

	.section	.text.nested_inner_none,"ax",@progbits
	.globl	nested_inner_none
	.p2align	3
	.type	nested_inner_none,@function
nested_inner_none:
	mov64 r0, 0
	exit
.Lfunc_end21:
	.size	nested_inner_none, .Lfunc_end21-nested_inner_none

	.section	.text.nested_some,"ax",@progbits
	.globl	nested_some
	.p2align	3
	.type	nested_some,@function
nested_some:
	mov64 r0, 1
	exit
.Lfunc_end22:
	.size	nested_some, .Lfunc_end22-nested_some

	.section	.text.nested_raw,"ax",@progbits
	.globl	nested_raw
	.p2align	3
	.type	nested_raw,@function
nested_raw:
	ldxb r3, [r2 + 0]
	ldxdw r4, [r2 + 25]
	stxdw [r1 + 25], r4
	ldxdw r4, [r2 + 17]
	stxdw [r1 + 17], r4
	ldxdw r4, [r2 + 9]
	stxdw [r1 + 9], r4
	ldxdw r2, [r2 + 1]
	stxdw [r1 + 1], r2
	stxb [r1 + 0], r3
	exit
.Lfunc_end23:
	.size	nested_raw, .Lfunc_end23-nested_raw

	.section	.text.nested_control,"ax",@progbits
	.globl	nested_control
	.p2align	3
	.type	nested_control,@function
nested_control:
	ldxb r3, [r2 + 32]
	stxb [r1 + 32], r3
	ldxdw r3, [r2 + 24]
	stxdw [r1 + 24], r3
	ldxdw r3, [r2 + 16]
	stxdw [r1 + 16], r3
	ldxdw r3, [r2 + 8]
	stxdw [r1 + 8], r3
	ldxdw r2, [r2 + 0]
	stxdw [r1 + 0], r2
	exit
.Lfunc_end24:
	.size	nested_control, .Lfunc_end24-nested_control

	.section	.text.annotation_bool,"ax",@progbits
	.globl	annotation_bool
	.p2align	3
	.type	annotation_bool,@function
annotation_bool:
	mov64 r0, r1
	exit
.Lfunc_end25:
	.size	annotation_bool, .Lfunc_end25-annotation_bool

	.section	.text.annotation_control,"ax",@progbits
	.globl	annotation_control
	.p2align	3
	.type	annotation_control,@function
annotation_control:
	mov64 r0, r1
	exit
.Lfunc_end26:
	.size	annotation_control, .Lfunc_end26-annotation_control

	.section	.text.ordinary4158_validate,"ax",@progbits
	.globl	ordinary4158_validate
	.p2align	3
	.type	ordinary4158_validate,@function
ordinary4158_validate:
	mov64 r6, r1
	ldxb r1, [r2 + 40]
	jne r1, 0, LBB27_29
	and64 r3, -3
	ldxdw r7, [r5 - 4080]
	ldxdw r8, [r5 - 4088]
	ldxdw r9, [r5 - 4096]
	ldxb r1, [r2 + 41]
	jeq r1, 0, LBB27_5
	and64 r3, 255
	jeq r3, 0, LBB27_3
	ja LBB27_11
LBB27_3:
	mov64 r1, r10
	add64 r1, -96
	lddw r2, .Lalloc_8f95cb73e89711d65e95d13598508b19
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 83
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 328], 0
	stdw [r10 - 336], 1
	stdw [r10 - 344], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -344
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_8f95cb73e89711d65e95d13598508b19
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB27_9
	ja LBB27_30
LBB27_5:
	and64 r3, 255
	jeq r3, 0, LBB27_6
	ja LBB27_10
LBB27_6:
	ldxb r1, [r8 + 0]
	jeq r1, 0, LBB27_7
	ja LBB27_15
LBB27_7:
	mov64 r1, r10
	add64 r1, -312
	lddw r2, .Lalloc_1ba5e1e397ae92b788c97e688ac0b362
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 89
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 80], 0
	stdw [r10 - 88], 1
	stdw [r10 - 96], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -96
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_1ba5e1e397ae92b788c97e688ac0b362
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB27_22
	ja LBB27_30
LBB27_9:
	ldxdw r1, [r10 - 328]
	stxdw [r10 - 216], r1
	ldxdw r1, [r10 - 336]
	stxdw [r10 - 224], r1
	ldxdw r1, [r10 - 344]
	stxdw [r10 - 232], r1
	ldxdw r1, [r10 - 96]
	stxdw [r10 - 256], r1
	ldxdw r1, [r10 - 88]
	stxdw [r10 - 248], r1
	ldxdw r1, [r10 - 80]
	stxdw [r10 - 240], r1
	stxw [r10 - 136], r7
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stb [r10 - 208], 2
	stw [r10 - 264], 159
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -408
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 408]
	ldxdw r2, [r10 - 400]
	ja LBB27_32
LBB27_10:
	ldxb r1, [r2 + 44]
	jeq r1, 0, LBB27_23
LBB27_11:
	ldxb r1, [r8 + 0]
	jeq r1, 0, LBB27_35
	mov64 r1, r10
	add64 r1, -96
	lddw r2, .Lalloc_b5f839a6bda937f2cae73e49fc88071f
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 90
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 328], 0
	stdw [r10 - 336], 1
	stdw [r10 - 344], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -344
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_b5f839a6bda937f2cae73e49fc88071f
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB27_14
	ja LBB27_30
LBB27_14:
	ldxdw r1, [r10 - 328]
	stxdw [r10 - 216], r1
	ldxdw r1, [r10 - 336]
	stxdw [r10 - 224], r1
	ldxdw r1, [r10 - 344]
	stxdw [r10 - 232], r1
	ldxdw r1, [r10 - 96]
	stxdw [r10 - 256], r1
	ldxdw r1, [r10 - 88]
	stxdw [r10 - 248], r1
	ldxdw r1, [r10 - 80]
	stxdw [r10 - 240], r1
	stxw [r10 - 136], r7
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stb [r10 - 208], 2
	stw [r10 - 264], 168
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -424
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 424]
	ldxdw r2, [r10 - 416]
	ja LBB27_32
LBB27_15:
	stxdw [r10 - 584], r4
	stxdw [r10 - 592], r2
	ldxdw r1, [r5 - 4072]
	stxdw [r10 - 576], r1
	ldxdw r1, [r8 + 25]
	stxdw [r10 - 320], r1
	ldxdw r1, [r8 + 17]
	stxdw [r10 - 328], r1
	ldxdw r1, [r8 + 9]
	stxdw [r10 - 336], r1
	ldxdw r1, [r8 + 1]
	stxdw [r10 - 344], r1
	stdw [r10 - 264], 0
	stdw [r10 - 272], 0
	stdw [r10 - 280], 0
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -344
	mov64 r2, r10
	add64 r2, -288
	mov64 r3, 32
	call memcmp
	add64 r8, 1
	lsh64 r0, 32
	rsh64 r0, 32
	jeq r0, 0, LBB27_27
	mov64 r1, r10
	add64 r1, -344
	mov64 r2, r7
	mov64 r3, 32
	call memcmp
	lsh64 r0, 32
	rsh64 r0, 32
	jne r0, 0, LBB27_17
	ja LBB27_26
LBB27_17:
	mov64 r1, r10
	add64 r1, -344
	ldxdw r2, [r10 - 576]
	mov64 r3, 32
	call memcmp
	lsh64 r0, 32
	rsh64 r0, 32
	jeq r0, 0, LBB27_26
	ldxw r1, [r8 + 0]
	stxw [r10 - 312], r1
	ldxw r1, [r8 + 3]
	stxw [r10 - 309], r1
	ldxdw r1, [r8 + 8]
	stxdw [r10 - 280], r1
	ldxdw r1, [r8 + 0]
	stxdw [r10 - 288], r1
	ldxdw r1, [r8 + 16]
	stxdw [r10 - 272], r1
	ldxdw r1, [r8 + 24]
	stxdw [r10 - 264], r1
	ldxdw r1, [r10 - 281]
	stxdw [r10 - 376], r1
	ldxdw r1, [r10 - 273]
	stxdw [r10 - 368], r1
	ldxdw r1, [r10 - 265]
	stxdw [r10 - 360], r1
	ldxb r1, [r10 - 257]
	stxb [r10 - 352], r1
	ldxdw r1, [r10 - 584]
	jeq r1, 0, LBB27_36
	ldxdw r2, [r10 - 592]
	ldxb r1, [r2 + 43]
	jne r1, 0, LBB27_38
	ldxb r1, [r2 + 42]
	jeq r1, 0, LBB27_41
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_835bb996f1795bf0338da0490417da62
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 80
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -232
	lddw r2, .Lalloc_835bb996f1795bf0338da0490417da62
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stxw [r10 - 136], r7
	stb [r10 - 208], 2
	stw [r10 - 264], 200
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -472
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 472]
	ldxdw r2, [r10 - 464]
	ja LBB27_32
LBB27_22:
	ldxdw r1, [r10 - 80]
	stxdw [r10 - 216], r1
	ldxdw r1, [r10 - 88]
	stxdw [r10 - 224], r1
	ldxdw r1, [r10 - 96]
	stxdw [r10 - 232], r1
	ldxdw r1, [r10 - 312]
	stxdw [r10 - 256], r1
	ldxdw r1, [r10 - 304]
	stxdw [r10 - 248], r1
	ldxdw r1, [r10 - 296]
	stxdw [r10 - 240], r1
	stxw [r10 - 136], r7
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stb [r10 - 208], 2
	stw [r10 - 264], 176
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -568
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 560]
	ldxdw r2, [r10 - 568]
	ja LBB27_28
LBB27_23:
	mov64 r1, r10
	add64 r1, -96
	lddw r2, .Lalloc_f94f166953c814e4161e699857179a1e
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 84
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 328], 0
	stdw [r10 - 336], 1
	stdw [r10 - 344], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -344
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_f94f166953c814e4161e699857179a1e
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB27_25
	ja LBB27_30
LBB27_25:
	ldxdw r1, [r10 - 328]
	stxdw [r10 - 216], r1
	ldxdw r1, [r10 - 336]
	stxdw [r10 - 224], r1
	ldxdw r1, [r10 - 344]
	stxdw [r10 - 232], r1
	ldxdw r1, [r10 - 96]
	stxdw [r10 - 256], r1
	ldxdw r1, [r10 - 88]
	stxdw [r10 - 248], r1
	ldxdw r1, [r10 - 80]
	stxdw [r10 - 240], r1
	stxw [r10 - 136], r7
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stb [r10 - 208], 2
	stw [r10 - 264], 166
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -440
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 440]
	ldxdw r2, [r10 - 432]
	ja LBB27_32
LBB27_26:
	ldxb r1, [r7 + 0]
	ldxb r1, [r7 + 0]
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_861c8964bbad6d9cede9df277e628fe9
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 19
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -232
	lddw r2, .Lalloc_861c8964bbad6d9cede9df277e628fe9
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stxw [r10 - 136], r7
	stb [r10 - 208], 2
	stw [r10 - 264], 182
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -520
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 512]
	ldxdw r2, [r10 - 520]
	ja LBB27_28
LBB27_27:
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_0e3505805f4905816c1bd644811a7869
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 30
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -232
	lddw r2, .Lalloc_0e3505805f4905816c1bd644811a7869
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stxw [r10 - 136], r7
	stb [r10 - 208], 2
	stw [r10 - 264], 177
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -536
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r3, [r10 - 528]
	ldxdw r2, [r10 - 536]
	ldxdw r1, [r8 + 24]
	stxdw [r10 - 264], r1
	ldxdw r1, [r8 + 16]
	stxdw [r10 - 272], r1
	ldxdw r1, [r8 + 8]
	stxdw [r10 - 280], r1
	ldxdw r1, [r8 + 0]
	stxdw [r10 - 288], r1
	stdw [r10 - 256], 0
	stdw [r10 - 248], 0
	stdw [r10 - 240], 0
	stdw [r10 - 232], 0
	mov64 r1, r10
	add64 r1, -552
	mov64 r4, r10
	add64 r4, -288
	call _ZN11anchor_lang5error5Error12with_pubkeys17hca6dbbbe6a9a5da7E
	ldxdw r1, [r10 - 544]
	ldxdw r2, [r10 - 552]
LBB27_28:
	stxdw [r6 + 8], r2
	stxdw [r6 + 16], r1
	ja LBB27_33
LBB27_29:
	mov64 r1, r10
	add64 r1, -376
	lddw r2, .Lalloc_eb4f91695bc6f999067c65f428fcc4d8
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 88
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 328], 0
	stdw [r10 - 336], 1
	stdw [r10 - 344], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -344
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_eb4f91695bc6f999067c65f428fcc4d8
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB27_31
LBB27_30:
	mov64 r3, r10
	add64 r3, -1
	lddw r1, .Lalloc_cc656815297f75969399c3f4b1ad3de4
	mov64 r2, 55
	lddw r4, .Lvtable.1
	lddw r5, .Lalloc_d5d9fccaf545b6e0545ef73245a3c43f
	call _ZN4core6result13unwrap_failed17h2dbd2ef42161686dE
LBB27_31:
	ldxdw r1, [r10 - 328]
	stxdw [r10 - 216], r1
	ldxdw r1, [r10 - 336]
	stxdw [r10 - 224], r1
	ldxdw r1, [r10 - 344]
	stxdw [r10 - 232], r1
	ldxdw r1, [r10 - 376]
	stxdw [r10 - 256], r1
	ldxdw r1, [r10 - 368]
	stxdw [r10 - 248], r1
	ldxdw r1, [r10 - 360]
	stxdw [r10 - 240], r1
	stxw [r10 - 136], r7
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stb [r10 - 208], 2
	stw [r10 - 264], 154
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -392
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 392]
	ldxdw r2, [r10 - 384]
LBB27_32:
	stxdw [r6 + 16], r2
	stxdw [r6 + 8], r1
LBB27_33:
	stb [r6 + 0], 1
LBB27_34:
	exit
LBB27_35:
	ldxw r1, [r7 + 3]
	stxw [r10 - 309], r1
	ldxw r1, [r7 + 0]
	stxw [r10 - 312], r1
	ldxdw r1, [r7 + 7]
	stxdw [r10 - 376], r1
	ldxdw r1, [r7 + 15]
	stxdw [r10 - 368], r1
	ldxdw r1, [r7 + 23]
	stxdw [r10 - 360], r1
	ldxb r1, [r7 + 31]
	stxb [r10 - 352], r1
	jne r4, 0, LBB27_37
LBB27_36:
	ldxdw r1, [r10 - 368]
	stxdw [r10 - 113], r1
	ldxdw r1, [r10 - 376]
	stxdw [r10 - 121], r1
	ldxb r1, [r10 - 352]
	stxb [r10 - 97], r1
	ldxdw r1, [r10 - 360]
	stxdw [r10 - 105], r1
	ldxw r1, [r10 - 309]
	stxw [r10 - 125], r1
	ldxw r1, [r10 - 312]
	stxw [r10 - 128], r1
	ldxdw r1, [r10 - 120]
	stxdw [r6 + 9], r1
	ldxdw r1, [r10 - 112]
	stxdw [r6 + 17], r1
	ldxdw r1, [r10 - 104]
	stxdw [r6 + 25], r1
	ldxdw r1, [r10 - 128]
	stxdw [r6 + 1], r1
	stb [r6 + 0], 0
	ja LBB27_34
LBB27_37:
	ldxb r1, [r2 + 43]
	jeq r1, 0, LBB27_41
LBB27_38:
	mov64 r1, r10
	add64 r1, -96
	lddw r2, .Lalloc_e75cefee4bb91125af0ea8444b842ed0
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 91
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 328], 0
	stdw [r10 - 336], 1
	stdw [r10 - 344], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -344
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_e75cefee4bb91125af0ea8444b842ed0
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB27_40
	ja LBB27_30
LBB27_40:
	ldxdw r1, [r10 - 328]
	stxdw [r10 - 216], r1
	ldxdw r1, [r10 - 336]
	stxdw [r10 - 224], r1
	ldxdw r1, [r10 - 344]
	stxdw [r10 - 232], r1
	ldxdw r1, [r10 - 96]
	stxdw [r10 - 256], r1
	ldxdw r1, [r10 - 88]
	stxdw [r10 - 248], r1
	ldxdw r1, [r10 - 80]
	stxdw [r10 - 240], r1
	stxw [r10 - 136], r7
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stb [r10 - 208], 2
	stw [r10 - 264], 196
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -456
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 456]
	ldxdw r2, [r10 - 448]
	ja LBB27_32
LBB27_41:
	ldxb r1, [r7 + 0]
	ldxb r1, [r2 + 45]
	jeq r1, 0, LBB27_44
	add64 r9, -1
	ldxdw r1, [r2 + 32]
	jlt r9, r1, LBB27_45
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_973adb9e8664e25d4750ddb14e0de56a
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 78
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -232
	lddw r2, .Lalloc_973adb9e8664e25d4750ddb14e0de56a
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stxw [r10 - 136], r7
	stb [r10 - 208], 2
	stw [r10 - 264], 208
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -488
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 488]
	ldxdw r2, [r10 - 480]
	ja LBB27_32
LBB27_44:
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_01eaaa187d2be542d4425f23ab284310
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 77
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -232
	lddw r2, .Lalloc_01eaaa187d2be542d4425f23ab284310
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stxw [r10 - 136], r7
	stb [r10 - 208], 2
	stw [r10 - 264], 204
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -504
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 504]
	ldxdw r2, [r10 - 496]
	ja LBB27_32
LBB27_45:
	ldxb r1, [r7 + 0]
	ja LBB27_36
.Lfunc_end27:
	.size	ordinary4158_validate, .Lfunc_end27-ordinary4158_validate

	.section	.text.updated4149_validate,"ax",@progbits
	.globl	updated4149_validate
	.p2align	3
	.type	updated4149_validate,@function
updated4149_validate:
	mov64 r6, r1
	ldxb r1, [r2 + 40]
	jne r1, 0, LBB28_29
	ldxdw r7, [r5 - 4080]
	ldxdw r8, [r5 - 4088]
	ldxdw r9, [r5 - 4096]
	and64 r3, 1
	ldxb r1, [r2 + 41]
	jeq r1, 0, LBB28_5
	jeq r3, 0, LBB28_3
	ja LBB28_11
LBB28_3:
	mov64 r1, r10
	add64 r1, -96
	lddw r2, .Lalloc_8f95cb73e89711d65e95d13598508b19
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 83
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r8, r0
	stdw [r10 - 328], 0
	stdw [r10 - 336], 1
	stdw [r10 - 344], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -344
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_8f95cb73e89711d65e95d13598508b19
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB28_9
	ja LBB28_30
LBB28_5:
	jeq r3, 0, LBB28_6
	ja LBB28_10
LBB28_6:
	ldxb r1, [r8 + 0]
	and64 r1, 1
	jeq r1, 0, LBB28_7
	ja LBB28_20
LBB28_7:
	ldxb r1, [r7 + 0]
	mov64 r1, r10
	add64 r1, -312
	lddw r2, .Lalloc_1ba5e1e397ae92b788c97e688ac0b362
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 89
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 80], 0
	stdw [r10 - 88], 1
	stdw [r10 - 96], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -96
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_1ba5e1e397ae92b788c97e688ac0b362
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB28_15
	ja LBB28_30
LBB28_9:
	ldxdw r1, [r10 - 328]
	stxdw [r10 - 216], r1
	ldxdw r1, [r10 - 336]
	stxdw [r10 - 224], r1
	ldxdw r1, [r10 - 344]
	stxdw [r10 - 232], r1
	ldxdw r1, [r10 - 96]
	stxdw [r10 - 256], r1
	ldxdw r1, [r10 - 88]
	stxdw [r10 - 248], r1
	ldxdw r1, [r10 - 80]
	stxdw [r10 - 240], r1
	stxw [r10 - 136], r8
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stb [r10 - 208], 2
	stw [r10 - 264], 217
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -408
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 408]
	ldxdw r2, [r10 - 400]
	ldxb r3, [r7 + 0]
	ja LBB28_32
LBB28_10:
	ldxb r1, [r2 + 44]
	jeq r1, 0, LBB28_17
LBB28_11:
	ldxb r1, [r8 + 0]
	jeq r1, 0, LBB28_35
	mov64 r1, r10
	add64 r1, -96
	lddw r2, .Lalloc_b5f839a6bda937f2cae73e49fc88071f
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 90
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 328], 0
	stdw [r10 - 336], 1
	stdw [r10 - 344], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -344
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_b5f839a6bda937f2cae73e49fc88071f
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB28_14
	ja LBB28_30
LBB28_14:
	ldxdw r1, [r10 - 328]
	stxdw [r10 - 216], r1
	ldxdw r1, [r10 - 336]
	stxdw [r10 - 224], r1
	ldxdw r1, [r10 - 344]
	stxdw [r10 - 232], r1
	ldxdw r1, [r10 - 96]
	stxdw [r10 - 256], r1
	ldxdw r1, [r10 - 88]
	stxdw [r10 - 248], r1
	ldxdw r1, [r10 - 80]
	stxdw [r10 - 240], r1
	stxw [r10 - 136], r7
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stb [r10 - 208], 2
	stw [r10 - 264], 226
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -424
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 424]
	ldxdw r2, [r10 - 416]
	ja LBB28_32
LBB28_15:
	ldxdw r1, [r10 - 80]
	stxdw [r10 - 216], r1
	ldxdw r1, [r10 - 88]
	stxdw [r10 - 224], r1
	ldxdw r1, [r10 - 96]
	stxdw [r10 - 232], r1
	ldxdw r1, [r10 - 312]
	stxdw [r10 - 256], r1
	ldxdw r1, [r10 - 304]
	stxdw [r10 - 248], r1
	ldxdw r1, [r10 - 296]
	stxdw [r10 - 240], r1
	stxw [r10 - 136], r7
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stb [r10 - 208], 2
	stw [r10 - 264], 234
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -568
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 560]
	ldxdw r2, [r10 - 568]
LBB28_16:
	stxdw [r6 + 8], r2
	stxdw [r6 + 16], r1
	ja LBB28_33
LBB28_17:
	mov64 r1, r10
	add64 r1, -96
	lddw r2, .Lalloc_f94f166953c814e4161e699857179a1e
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 84
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 328], 0
	stdw [r10 - 336], 1
	stdw [r10 - 344], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -344
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_f94f166953c814e4161e699857179a1e
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB28_19
	ja LBB28_30
LBB28_19:
	ldxdw r1, [r10 - 328]
	stxdw [r10 - 216], r1
	ldxdw r1, [r10 - 336]
	stxdw [r10 - 224], r1
	ldxdw r1, [r10 - 344]
	stxdw [r10 - 232], r1
	ldxdw r1, [r10 - 96]
	stxdw [r10 - 256], r1
	ldxdw r1, [r10 - 88]
	stxdw [r10 - 248], r1
	ldxdw r1, [r10 - 80]
	stxdw [r10 - 240], r1
	stxw [r10 - 136], r7
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stb [r10 - 208], 2
	stw [r10 - 264], 224
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -440
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 440]
	ldxdw r2, [r10 - 432]
	ja LBB28_32
LBB28_20:
	stxdw [r10 - 584], r4
	stxdw [r10 - 592], r2
	ldxdw r1, [r5 - 4072]
	stxdw [r10 - 576], r1
	ldxdw r1, [r8 + 25]
	stxdw [r10 - 320], r1
	ldxdw r1, [r8 + 17]
	stxdw [r10 - 328], r1
	ldxdw r1, [r8 + 9]
	stxdw [r10 - 336], r1
	ldxdw r1, [r8 + 1]
	stxdw [r10 - 344], r1
	stdw [r10 - 264], 0
	stdw [r10 - 272], 0
	stdw [r10 - 280], 0
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -344
	mov64 r2, r10
	add64 r2, -288
	mov64 r3, 32
	call memcmp
	add64 r8, 1
	lsh64 r0, 32
	rsh64 r0, 32
	jeq r0, 0, LBB28_24
	mov64 r1, r10
	add64 r1, -344
	ldxdw r2, [r10 - 576]
	mov64 r3, 32
	call memcmp
	lsh64 r0, 32
	rsh64 r0, 32
	jne r0, 0, LBB28_22
	ja LBB28_23
LBB28_22:
	mov64 r1, r10
	add64 r1, -344
	mov64 r2, r7
	mov64 r3, 32
	call memcmp
	lsh64 r0, 32
	rsh64 r0, 32
	jne r0, 0, LBB28_25
LBB28_23:
	ldxb r1, [r7 + 0]
	ldxb r1, [r7 + 0]
	ldxb r1, [r7 + 0]
	ldxb r1, [r7 + 0]
	ldxb r1, [r7 + 0]
	ldxb r1, [r7 + 0]
	ldxb r1, [r7 + 0]
	ldxb r1, [r7 + 0]
	ldxb r1, [r7 + 0]
	ldxb r1, [r7 + 0]
	ldxb r1, [r7 + 0]
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_861c8964bbad6d9cede9df277e628fe9
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 19
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -232
	lddw r2, .Lalloc_861c8964bbad6d9cede9df277e628fe9
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stxw [r10 - 136], r7
	stb [r10 - 208], 2
	stw [r10 - 264], 240
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -520
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 512]
	ldxdw r2, [r10 - 520]
	ja LBB28_16
LBB28_24:
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_0e3505805f4905816c1bd644811a7869
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 30
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -232
	lddw r2, .Lalloc_0e3505805f4905816c1bd644811a7869
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stxw [r10 - 136], r7
	stb [r10 - 208], 2
	stw [r10 - 264], 235
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -536
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r3, [r10 - 528]
	ldxdw r2, [r10 - 536]
	ldxdw r1, [r10 - 320]
	stxdw [r10 - 264], r1
	ldxdw r1, [r10 - 328]
	stxdw [r10 - 272], r1
	ldxdw r1, [r10 - 336]
	stxdw [r10 - 280], r1
	ldxdw r1, [r8 + 0]
	stxdw [r10 - 288], r1
	stdw [r10 - 256], 0
	stdw [r10 - 248], 0
	stdw [r10 - 240], 0
	stdw [r10 - 232], 0
	mov64 r1, r10
	add64 r1, -552
	mov64 r4, r10
	add64 r4, -288
	call _ZN11anchor_lang5error5Error12with_pubkeys17hca6dbbbe6a9a5da7E
	ldxdw r1, [r10 - 544]
	ldxdw r2, [r10 - 552]
	ja LBB28_16
LBB28_25:
	ldxw r1, [r8 + 0]
	stxw [r10 - 312], r1
	ldxw r1, [r8 + 3]
	stxw [r10 - 309], r1
	ldxdw r1, [r8 + 8]
	stxdw [r10 - 280], r1
	ldxdw r1, [r8 + 0]
	stxdw [r10 - 288], r1
	ldxdw r1, [r8 + 16]
	stxdw [r10 - 272], r1
	ldxdw r1, [r8 + 24]
	stxdw [r10 - 264], r1
	ldxdw r1, [r10 - 281]
	stxdw [r10 - 376], r1
	ldxdw r1, [r10 - 273]
	stxdw [r10 - 368], r1
	ldxdw r1, [r10 - 265]
	stxdw [r10 - 360], r1
	ldxb r1, [r10 - 257]
	stxb [r10 - 352], r1
	ldxdw r2, [r10 - 592]
	ldxdw r1, [r10 - 584]
	jeq r1, 0, LBB28_36
	ldxb r1, [r2 + 43]
	jne r1, 0, LBB28_38
	ldxb r1, [r2 + 42]
	jeq r1, 0, LBB28_41
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_835bb996f1795bf0338da0490417da62
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 80
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -232
	lddw r2, .Lalloc_835bb996f1795bf0338da0490417da62
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stxw [r10 - 136], r7
	stb [r10 - 208], 2
	stw [r10 - 264], 258
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -472
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 472]
	ldxdw r2, [r10 - 464]
	ja LBB28_32
LBB28_29:
	mov64 r1, r10
	add64 r1, -376
	lddw r2, .Lalloc_eb4f91695bc6f999067c65f428fcc4d8
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 88
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 328], 0
	stdw [r10 - 336], 1
	stdw [r10 - 344], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -344
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_eb4f91695bc6f999067c65f428fcc4d8
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB28_31
LBB28_30:
	mov64 r3, r10
	add64 r3, -1
	lddw r1, .Lalloc_cc656815297f75969399c3f4b1ad3de4
	mov64 r2, 55
	lddw r4, .Lvtable.1
	lddw r5, .Lalloc_d5d9fccaf545b6e0545ef73245a3c43f
	call _ZN4core6result13unwrap_failed17h2dbd2ef42161686dE
LBB28_31:
	ldxdw r1, [r10 - 328]
	stxdw [r10 - 216], r1
	ldxdw r1, [r10 - 336]
	stxdw [r10 - 224], r1
	ldxdw r1, [r10 - 344]
	stxdw [r10 - 232], r1
	ldxdw r1, [r10 - 376]
	stxdw [r10 - 256], r1
	ldxdw r1, [r10 - 368]
	stxdw [r10 - 248], r1
	ldxdw r1, [r10 - 360]
	stxdw [r10 - 240], r1
	stxw [r10 - 136], r7
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stb [r10 - 208], 2
	stw [r10 - 264], 212
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -392
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 392]
	ldxdw r2, [r10 - 384]
LBB28_32:
	stxdw [r6 + 16], r2
	stxdw [r6 + 8], r1
LBB28_33:
	stb [r6 + 0], 1
LBB28_34:
	exit
LBB28_35:
	ldxw r1, [r7 + 3]
	stxw [r10 - 309], r1
	ldxw r1, [r7 + 0]
	stxw [r10 - 312], r1
	ldxdw r1, [r7 + 7]
	stxdw [r10 - 376], r1
	ldxdw r1, [r7 + 15]
	stxdw [r10 - 368], r1
	ldxdw r1, [r7 + 23]
	stxdw [r10 - 360], r1
	ldxb r1, [r7 + 31]
	stxb [r10 - 352], r1
	jne r4, 0, LBB28_37
LBB28_36:
	ldxdw r1, [r10 - 368]
	stxdw [r10 - 113], r1
	ldxdw r1, [r10 - 376]
	stxdw [r10 - 121], r1
	ldxb r1, [r10 - 352]
	stxb [r10 - 97], r1
	ldxdw r1, [r10 - 360]
	stxdw [r10 - 105], r1
	ldxw r1, [r10 - 309]
	stxw [r10 - 125], r1
	ldxw r1, [r10 - 312]
	stxw [r10 - 128], r1
	ldxdw r1, [r10 - 120]
	stxdw [r6 + 9], r1
	ldxdw r1, [r10 - 112]
	stxdw [r6 + 17], r1
	ldxdw r1, [r10 - 104]
	stxdw [r6 + 25], r1
	ldxdw r1, [r10 - 128]
	stxdw [r6 + 1], r1
	stb [r6 + 0], 0
	ja LBB28_34
LBB28_37:
	ldxb r1, [r2 + 43]
	jeq r1, 0, LBB28_41
LBB28_38:
	mov64 r1, r10
	add64 r1, -96
	lddw r2, .Lalloc_e75cefee4bb91125af0ea8444b842ed0
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 91
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	stdw [r10 - 328], 0
	stdw [r10 - 336], 1
	stdw [r10 - 344], 0
	lddw r1, .Lvtable.0
	stxdw [r10 - 32], r1
	mov64 r1, r10
	add64 r1, -344
	stxdw [r10 - 40], r1
	stb [r10 - 16], 3
	stdw [r10 - 24], 32
	stdw [r10 - 56], 0
	stdw [r10 - 72], 0
	mov64 r2, r10
	add64 r2, -72
	lddw r1, .Lalloc_e75cefee4bb91125af0ea8444b842ed0
	call _ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE
	jeq r0, 0, LBB28_40
	ja LBB28_30
LBB28_40:
	ldxdw r1, [r10 - 328]
	stxdw [r10 - 216], r1
	ldxdw r1, [r10 - 336]
	stxdw [r10 - 224], r1
	ldxdw r1, [r10 - 344]
	stxdw [r10 - 232], r1
	ldxdw r1, [r10 - 96]
	stxdw [r10 - 256], r1
	ldxdw r1, [r10 - 88]
	stxdw [r10 - 248], r1
	ldxdw r1, [r10 - 80]
	stxdw [r10 - 240], r1
	stxw [r10 - 136], r7
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stb [r10 - 208], 2
	stw [r10 - 264], 254
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -456
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 456]
	ldxdw r2, [r10 - 448]
	ja LBB28_32
LBB28_41:
	ldxb r1, [r7 + 0]
	ldxb r1, [r2 + 45]
	jeq r1, 0, LBB28_44
	add64 r9, -1
	ldxdw r1, [r2 + 32]
	jlt r9, r1, LBB28_45
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_973adb9e8664e25d4750ddb14e0de56a
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 78
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -232
	lddw r2, .Lalloc_973adb9e8664e25d4750ddb14e0de56a
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stxw [r10 - 136], r7
	stb [r10 - 208], 2
	stw [r10 - 264], 266
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -488
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 488]
	ldxdw r2, [r10 - 480]
	ja LBB28_32
LBB28_44:
	mov64 r1, r10
	add64 r1, -256
	lddw r2, .Lalloc_01eaaa187d2be542d4425f23ab284310
	call _ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E
	mov64 r1, 77
	call _ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E
	mov64 r7, r0
	mov64 r1, r10
	add64 r1, -232
	lddw r2, .Lalloc_01eaaa187d2be542d4425f23ab284310
	call _ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE
	lddw r1, .Lalloc_a6d06679426228b5e58f8de7567c2075
	stxdw [r10 - 280], r1
	stxw [r10 - 136], r7
	stb [r10 - 208], 2
	stw [r10 - 264], 262
	stdw [r10 - 272], 103
	stdw [r10 - 288], 0
	mov64 r1, r10
	add64 r1, -504
	mov64 r2, r10
	add64 r2, -288
	call _ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E
	ldxdw r1, [r10 - 504]
	ldxdw r2, [r10 - 496]
	ja LBB28_32
LBB28_45:
	ldxb r1, [r7 + 0]
	ja LBB28_36
.Lfunc_end28:
	.size	updated4149_validate, .Lfunc_end28-updated4149_validate

	.type	.Lvtable.0,@object
	.section	.data.rel.ro..Lvtable.0,"aw",@progbits
	.p2align	3, 0x0
.Lvtable.0:
	.quad	_ZN4core3ptr42drop_in_place$LT$alloc..string..String$GT$17hd1d278fe2cba7629E
	.asciz	"\030\000\000\000\000\000\000\000\b\000\000\000\000\000\000"
	.quad	_ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$9write_str17h4b62f46a222bd5b2E
	.quad	_ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$10write_char17hfde5b685689164ccE
	.quad	_ZN4core3fmt5Write9write_fmt17hf607f0d92912dfd2E
	.size	.Lvtable.0, 48

	.type	.Lalloc_cc656815297f75969399c3f4b1ad3de4,@object
	.section	.rodata..Lalloc_cc656815297f75969399c3f4b1ad3de4,"a",@progbits
.Lalloc_cc656815297f75969399c3f4b1ad3de4:
	.ascii	"a Display implementation returned an error unexpectedly"
	.size	.Lalloc_cc656815297f75969399c3f4b1ad3de4, 55

	.type	.Lvtable.1,@object
	.section	.data.rel.ro..Lvtable.1,"aw",@progbits
	.p2align	3, 0x0
.Lvtable.1:
	.quad	_ZN4core3ptr37drop_in_place$LT$core..fmt..Error$GT$17hc55e87063dbb1cfcE
	.asciz	"\000\000\000\000\000\000\000\000\001\000\000\000\000\000\000"
	.quad	_ZN53_$LT$core..fmt..Error$u20$as$u20$core..fmt..Debug$GT$3fmt17h85666afa16c4890eE
	.size	.Lvtable.1, 32

	.type	.Lalloc_0c7342d701a2219de6bddb6c078f5127,@object
	.section	.rodata..Lalloc_0c7342d701a2219de6bddb6c078f5127,"a",@progbits
.Lalloc_0c7342d701a2219de6bddb6c078f5127:
	.ascii	"/home/runner/work/platform-tools/platform-tools/out/rust/library/alloc/src/string.rs"
	.size	.Lalloc_0c7342d701a2219de6bddb6c078f5127, 84

	.type	.Lalloc_d5d9fccaf545b6e0545ef73245a3c43f,@object
	.section	.data.rel.ro..Lalloc_d5d9fccaf545b6e0545ef73245a3c43f,"aw",@progbits
	.p2align	3, 0x0
.Lalloc_d5d9fccaf545b6e0545ef73245a3c43f:
	.quad	.Lalloc_0c7342d701a2219de6bddb6c078f5127
	.asciz	"T\000\000\000\000\000\000\000\377\t\000\000\016\000\000"
	.size	.Lalloc_d5d9fccaf545b6e0545ef73245a3c43f, 24

	.type	.Lalloc_99ac8a81a24cac863217ce4a5cbfabea,@object
	.section	.rodata..Lalloc_99ac8a81a24cac863217ce4a5cbfabea,"a",@progbits
.Lalloc_99ac8a81a24cac863217ce4a5cbfabea:
	.ascii	"Error"
	.size	.Lalloc_99ac8a81a24cac863217ce4a5cbfabea, 5

	.type	.Lalloc_8f95cb73e89711d65e95d13598508b19,@object
	.section	.rodata.cst4,"aM",@progbits,4
	.p2align	2, 0x0
.Lalloc_8f95cb73e89711d65e95d13598508b19:
	.asciz	"S\000\000"
	.size	.Lalloc_8f95cb73e89711d65e95d13598508b19, 4

	.type	.Lalloc_a6d06679426228b5e58f8de7567c2075,@object
	.section	.rodata..Lalloc_a6d06679426228b5e58f8de7567c2075,"a",@progbits
.Lalloc_a6d06679426228b5e58f8de7567c2075:
	.ascii	"/Users/shawwalters/.codex/artifacts/pumpfun-pr-branch-pass114-20261101/late-prs/official-probe/probe.rs"
	.size	.Lalloc_a6d06679426228b5e58f8de7567c2075, 103

	.type	.Lalloc_861c8964bbad6d9cede9df277e628fe9,@object
	.section	.rodata.cst4,"aM",@progbits,4
	.p2align	2, 0x0
.Lalloc_861c8964bbad6d9cede9df277e628fe9:
	.asciz	"\023\000\000"
	.size	.Lalloc_861c8964bbad6d9cede9df277e628fe9, 4

	.type	.Lalloc_0e3505805f4905816c1bd644811a7869,@object
	.p2align	2, 0x0
.Lalloc_0e3505805f4905816c1bd644811a7869:
	.asciz	"\036\000\000"
	.size	.Lalloc_0e3505805f4905816c1bd644811a7869, 4

	.type	.Lalloc_1ba5e1e397ae92b788c97e688ac0b362,@object
	.p2align	2, 0x0
.Lalloc_1ba5e1e397ae92b788c97e688ac0b362:
	.asciz	"Y\000\000"
	.size	.Lalloc_1ba5e1e397ae92b788c97e688ac0b362, 4

	.type	.Lalloc_f94f166953c814e4161e699857179a1e,@object
	.p2align	2, 0x0
.Lalloc_f94f166953c814e4161e699857179a1e:
	.asciz	"T\000\000"
	.size	.Lalloc_f94f166953c814e4161e699857179a1e, 4

	.type	.Lalloc_b5f839a6bda937f2cae73e49fc88071f,@object
	.p2align	2, 0x0
.Lalloc_b5f839a6bda937f2cae73e49fc88071f:
	.asciz	"Z\000\000"
	.size	.Lalloc_b5f839a6bda937f2cae73e49fc88071f, 4

	.type	.Lalloc_835bb996f1795bf0338da0490417da62,@object
	.p2align	2, 0x0
.Lalloc_835bb996f1795bf0338da0490417da62:
	.asciz	"P\000\000"
	.size	.Lalloc_835bb996f1795bf0338da0490417da62, 4

	.type	.Lalloc_01eaaa187d2be542d4425f23ab284310,@object
	.p2align	2, 0x0
.Lalloc_01eaaa187d2be542d4425f23ab284310:
	.asciz	"M\000\000"
	.size	.Lalloc_01eaaa187d2be542d4425f23ab284310, 4

	.type	.Lalloc_973adb9e8664e25d4750ddb14e0de56a,@object
	.p2align	2, 0x0
.Lalloc_973adb9e8664e25d4750ddb14e0de56a:
	.asciz	"N\000\000"
	.size	.Lalloc_973adb9e8664e25d4750ddb14e0de56a, 4

	.type	.Lalloc_e75cefee4bb91125af0ea8444b842ed0,@object
	.p2align	2, 0x0
.Lalloc_e75cefee4bb91125af0ea8444b842ed0:
	.asciz	"[\000\000"
	.size	.Lalloc_e75cefee4bb91125af0ea8444b842ed0, 4

	.type	.Lalloc_eb4f91695bc6f999067c65f428fcc4d8,@object
	.p2align	2, 0x0
.Lalloc_eb4f91695bc6f999067c65f428fcc4d8:
	.asciz	"X\000\000"
	.size	.Lalloc_eb4f91695bc6f999067c65f428fcc4d8, 4

	.type	.Lalloc_ebe040a358b3132776a16f34a7b7aa5b,@object
	.section	.rodata..Lalloc_ebe040a358b3132776a16f34a7b7aa5b,"a",@progbits
.Lalloc_ebe040a358b3132776a16f34a7b7aa5b:
	.ascii	"programs/pump/src/creator/admin_cto.rs"
	.size	.Lalloc_ebe040a358b3132776a16f34a7b7aa5b, 38

	.type	.Lalloc_914b2c69d7eca30497b9feaf15ac92f1,@object
	.section	.rodata..Lalloc_914b2c69d7eca30497b9feaf15ac92f1,"a",@progbits
.Lalloc_914b2c69d7eca30497b9feaf15ac92f1:
	.zero	1
	.size	.Lalloc_914b2c69d7eca30497b9feaf15ac92f1, 1

	.hidden	llvm.assume
	.hidden	llvm.trap
	.hidden	llvm.uadd.with.overflow.i64
	.hidden	memcmp
