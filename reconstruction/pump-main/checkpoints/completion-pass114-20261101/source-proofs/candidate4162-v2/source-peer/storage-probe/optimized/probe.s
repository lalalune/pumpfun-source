	.text
	.file	"pass114_slot_probe.836c91c48f54db30-cgu.0"
	.section	.text.low_byte_false,"ax",@progbits
	.globl	low_byte_false
	.p2align	3
	.type	low_byte_false,@function
low_byte_false:
	stb [r10 - 8], 0
	ldxb r0, [r10 - 8]
	exit
.Lfunc_end0:
	.size	low_byte_false, .Lfunc_end0-low_byte_false

	.section	.text.low_byte_true,"ax",@progbits
	.globl	low_byte_true
	.p2align	3
	.type	low_byte_true,@function
low_byte_true:
	stb [r10 - 8], 1
	ldxb r0, [r10 - 8]
	exit
.Lfunc_end1:
	.size	low_byte_true, .Lfunc_end1-low_byte_true

	.section	.text.scratch_slots,"ax",@progbits
	.globl	scratch_slots
	.p2align	3
	.type	scratch_slots,@function
scratch_slots:
	mov64 r7, r4
	mov64 r8, r3
	mov64 r6, r1
	ldxdw r1, [r2 + 24]
	stxdw [r10 - 88], r1
	ldxdw r1, [r2 + 16]
	stxdw [r10 - 96], r1
	ldxdw r1, [r2 + 8]
	stxdw [r10 - 104], r1
	ldxdw r1, [r2 + 0]
	stxdw [r10 - 112], r1
	ldxdw r1, [r5 - 4096]
	stxb [r10 - 48], r1
	stxb [r10 - 48], r1
	stxb [r10 - 48], r1
	stxb [r10 - 48], r1
	stxb [r10 - 48], r1
	stxb [r10 - 48], r1
	mov64 r1, r10
	add64 r1, -40
	stxdw [r10 - 80], r1
	mov64 r1, r10
	add64 r1, -1
	stxdw [r10 - 24], r1
	lddw r1, .Lalloc_7a7952b5e0d15f2b72d0341cef6d4739
	stxdw [r10 - 40], r1
	stdw [r10 - 72], 2
	ldxdw r9, [r5 - 4088]
	stxb [r10 - 1], r9
	stdw [r10 - 16], 1
	stdw [r10 - 32], 17
	mov64 r1, r10
	add64 r1, -80
	mov64 r2, 1
	call observe_signers
	stxdw [r10 - 64], r8
	mov64 r1, r8
	call observe_accounts
	stxdw [r10 - 56], r7
	ldxdw r1, [r10 - 64]
	call observe_accounts
	ldxb r1, [r10 - 56]
	stxb [r10 - 48], r9
	stxb [r10 - 48], r9
	ldxdw r2, [r10 - 88]
	stxdw [r6 + 24], r2
	ldxdw r2, [r10 - 96]
	stxdw [r6 + 16], r2
	ldxdw r2, [r10 - 104]
	stxdw [r6 + 8], r2
	ldxdw r2, [r10 - 112]
	stxdw [r6 + 0], r2
	and64 r1, 1
	stxb [r6 + 32], r1
	exit
.Lfunc_end2:
	.size	scratch_slots, .Lfunc_end2-scratch_slots

	.type	.Lalloc_7a7952b5e0d15f2b72d0341cef6d4739,@object
	.section	.rodata..Lalloc_7a7952b5e0d15f2b72d0341cef6d4739,"a",@progbits
.Lalloc_7a7952b5e0d15f2b72d0341cef6d4739:
	.ascii	"__event_authority"
	.size	.Lalloc_7a7952b5e0d15f2b72d0341cef6d4739, 17

