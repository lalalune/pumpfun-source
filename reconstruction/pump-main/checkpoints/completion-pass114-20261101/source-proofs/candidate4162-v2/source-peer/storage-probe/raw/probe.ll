; ModuleID = 'pass114_slot_probe.836c91c48f54db30-cgu.0'
source_filename = "pass114_slot_probe.836c91c48f54db30-cgu.0"
target datalayout = "e-m:e-p:64:64-i64:64-n32:64-S128"
target triple = "sbf"

@0 = private unnamed_addr constant <{ [4 x i8], [4 x i8] }> <{ [4 x i8] zeroinitializer, [4 x i8] undef }>, align 4
@alloc_1eb6f53a157dccb32488e066ad957e6d = private unnamed_addr constant <{ [82 x i8] }> <{ [82 x i8] c"unsafe precondition(s) violated: hint::unreachable_unchecked must never be reached" }>, align 1
@alloc_7a7952b5e0d15f2b72d0341cef6d4739 = private unnamed_addr constant <{ [17 x i8] }> <{ [17 x i8] c"__event_authority" }>, align 1

; <i32 as core::iter::range::Step>::forward_unchecked
; Function Attrs: inlinehint nounwind
define internal noundef i32 @"_ZN47_$LT$i32$u20$as$u20$core..iter..range..Step$GT$17forward_unchecked17h8d7efb28a3d3ad12E"(i32 noundef %start1, i64 noundef %n) unnamed_addr #0 {
start:
  %0 = alloca [1 x i8], align 1
  %self = alloca [8 x i8], align 4
  call void @llvm.lifetime.start.p0(i64 8, ptr %self)
  %rhs = trunc i64 %n to i32
  %1 = call { i32, i1 } @llvm.sadd.with.overflow.i32(i32 %start1, i32 %rhs)
  %_11.0 = extractvalue { i32, i1 } %1, 0
  %_11.1 = extractvalue { i32, i1 } %1, 1
  %_8 = icmp slt i32 %rhs, 0
  %b = xor i1 %_11.1, %_8
  call void @llvm.lifetime.start.p0(i64 1, ptr %0)
  %2 = call i1 @llvm.expect.i1(i1 %b, i1 false)
  %3 = zext i1 %2 to i8
  store i8 %3, ptr %0, align 1
  %4 = load i8, ptr %0, align 1, !range !2, !noundef !3
  %_5 = trunc i8 %4 to i1
  call void @llvm.lifetime.end.p0(i64 1, ptr %0)
  br i1 %_5, label %bb2, label %bb3

bb3:                                              ; preds = %start
  %5 = getelementptr inbounds i8, ptr %self, i64 4
  store i32 %_11.0, ptr %5, align 4
  store i32 1, ptr %self, align 4
  %6 = getelementptr inbounds i8, ptr %self, i64 4
  %val = load i32, ptr %6, align 4, !noundef !3
  call void @llvm.lifetime.end.p0(i64 8, ptr %self)
  ret i32 %val

bb2:                                              ; preds = %start
  %7 = load i32, ptr @0, align 4, !range !4, !noundef !3
  %8 = load i32, ptr getelementptr inbounds (i8, ptr @0, i64 4), align 4
  store i32 %7, ptr %self, align 4
  %9 = getelementptr inbounds i8, ptr %self, i64 4
  store i32 %8, ptr %9, align 4
  call void @llvm.assume(i1 false)
; call core::hint::unreachable_unchecked::precondition_check
  call void @_ZN4core4hint21unreachable_unchecked18precondition_check17h07e713a874469782E() #8
  unreachable
}

; core::intrinsics::unlikely
; Function Attrs: nounwind
define internal noundef zeroext i1 @_ZN4core10intrinsics8unlikely17h91c20b0f228684e2E(i1 noundef zeroext %b) unnamed_addr #1 {
start:
  ret i1 %b
}

; core::hint::unreachable_unchecked::precondition_check
; Function Attrs: inlinehint nounwind
define internal void @_ZN4core4hint21unreachable_unchecked18precondition_check17h07e713a874469782E() unnamed_addr #0 {
start:
; call core::panicking::panic_nounwind
  call void @_ZN4core9panicking14panic_nounwind17h59c09f9524fc568aE(ptr noalias noundef nonnull readonly align 1 @alloc_1eb6f53a157dccb32488e066ad957e6d, i64 noundef 82) #9
  unreachable
}

; Function Attrs: nounwind
define noundef i8 @low_byte_false() unnamed_addr #1 {
start:
  %0 = alloca [1 x i8], align 1
  %_1 = alloca [8 x i8], align 8
  call void @llvm.lifetime.start.p0(i64 8, ptr %_1)
  store i64 0, ptr %_1, align 8
  call void @llvm.lifetime.start.p0(i64 1, ptr %0)
  %1 = load volatile i8, ptr %_1, align 1
  store i8 %1, ptr %0, align 1
  %_0 = load i8, ptr %0, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %0)
  call void @llvm.lifetime.end.p0(i64 8, ptr %_1)
  ret i8 %_0
}

; Function Attrs: nounwind
define noundef i8 @low_byte_true() unnamed_addr #1 {
start:
  %0 = alloca [1 x i8], align 1
  %_1 = alloca [8 x i8], align 8
  call void @llvm.lifetime.start.p0(i64 8, ptr %_1)
  store i64 1, ptr %_1, align 8
  call void @llvm.lifetime.start.p0(i64 1, ptr %0)
  %1 = load volatile i8, ptr %_1, align 1
  store i8 %1, ptr %0, align 1
  %_0 = load i8, ptr %0, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %0)
  call void @llvm.lifetime.end.p0(i64 8, ptr %_1)
  ret i8 %_0
}

; Function Attrs: nounwind
define void @scratch_slots(ptr dead_on_unwind noalias nocapture noundef writable sret([33 x i8]) align 1 dereferenceable(33) %_0, ptr noalias nocapture noundef readonly align 1 dereferenceable(32) %key, ptr noalias noundef readonly align 8 dereferenceable(48) %accounts, i1 noundef zeroext %cashback, i1 noundef zeroext %coin_empty, i8 noundef %bump) unnamed_addr #1 {
start:
  %0 = alloca [1 x i8], align 1
  %1 = alloca [8 x i8], align 8
  %iter = alloca [4 x i8], align 4
  %_42 = alloca [32 x i8], align 1
  %curve_cashback = alloca [1 x i8], align 1
  %_21 = alloca [16 x i8], align 8
  %_18 = alloca [1 x i8], align 1
  %_14 = alloca [32 x i8], align 8
  %hkx = alloca [72 x i8], align 8
  call void @llvm.lifetime.start.p0(i64 72, ptr %hkx)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %hkx, ptr align 1 %key, i64 32, i1 false)
  %_10 = getelementptr inbounds i64, ptr %hkx, i64 8
  call void @llvm.lifetime.start.p0(i64 4, ptr %iter)
  store i32 0, ptr %iter, align 4
  br label %bb1

bb1:                                              ; preds = %bb5, %start
  %_48 = load i32, ptr %iter, align 4, !noundef !3
  %_45 = icmp slt i32 %_48, 6
  br i1 %_45, label %bb5, label %bb7

bb7:                                              ; preds = %bb1
  call void @llvm.lifetime.end.p0(i64 4, ptr %iter)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_14)
  call void @llvm.lifetime.start.p0(i64 1, ptr %_18)
  %2 = getelementptr inbounds [1 x i8], ptr %_18, i64 0, i64 0
  store i8 %bump, ptr %2, align 1
  %3 = getelementptr inbounds [2 x { ptr, i64 }], ptr %_14, i64 0, i64 0
  store ptr @alloc_7a7952b5e0d15f2b72d0341cef6d4739, ptr %3, align 8
  %4 = getelementptr inbounds i8, ptr %3, i64 8
  store i64 17, ptr %4, align 8
  %5 = getelementptr inbounds [2 x { ptr, i64 }], ptr %_14, i64 0, i64 1
  store ptr %_18, ptr %5, align 8
  %6 = getelementptr inbounds i8, ptr %5, i64 8
  store i64 1, ptr %6, align 8
  %_20 = getelementptr inbounds i64, ptr %hkx, i64 4
  %7 = getelementptr inbounds [1 x { ptr, i64 }], ptr %_21, i64 0, i64 0
  store ptr %_14, ptr %7, align 8
  %8 = getelementptr inbounds i8, ptr %7, i64 8
  store i64 2, ptr %8, align 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_20, ptr align 8 %_21, i64 16, i1 false)
  call void @observe_signers(ptr noundef %_20, i64 noundef 1) #8
  call void @llvm.lifetime.end.p0(i64 1, ptr %_18)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_14)
  %_26 = getelementptr inbounds i64, ptr %hkx, i64 6
  store volatile ptr %accounts, ptr %_26, align 8
  call void @observe_accounts(ptr noundef %accounts) #8
  %_30 = getelementptr inbounds i64, ptr %hkx, i64 7
  %_31 = zext i1 %cashback to i64
  store volatile i64 %_31, ptr %_30, align 8
  call void @llvm.lifetime.start.p0(i64 8, ptr %1)
  %9 = load volatile ptr, ptr %_26, align 8
  store ptr %9, ptr %1, align 8
  %a1 = load ptr, ptr %1, align 8, !noundef !3
  call void @llvm.lifetime.end.p0(i64 8, ptr %1)
  call void @observe_accounts(ptr noundef %a1) #8
  call void @llvm.lifetime.start.p0(i64 1, ptr %curve_cashback)
  store i8 0, ptr %curve_cashback, align 1
  call void @llvm.lifetime.start.p0(i64 1, ptr %0)
  %10 = load volatile i8, ptr %_30, align 1
  store i8 %10, ptr %0, align 1
  %_39 = load i8, ptr %0, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %0)
  store i8 %_39, ptr %curve_cashback, align 1
  store volatile i8 %bump, ptr %_10, align 1
  store volatile i8 %bump, ptr %_10, align 1
  call void @llvm.lifetime.start.p0(i64 32, ptr %_42)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_42, ptr align 1 %hkx, i64 32, i1 false)
  %11 = load i8, ptr %curve_cashback, align 1, !range !2, !noundef !3
  %_43 = trunc i8 %11 to i1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_0, ptr align 1 %_42, i64 32, i1 false)
  %12 = getelementptr inbounds i8, ptr %_0, i64 32
  %13 = zext i1 %_43 to i8
  store i8 %13, ptr %12, align 1
  call void @llvm.lifetime.end.p0(i64 32, ptr %_42)
  call void @llvm.lifetime.end.p0(i64 1, ptr %curve_cashback)
  call void @llvm.lifetime.end.p0(i64 72, ptr %hkx)
  ret void

bb5:                                              ; preds = %bb1
  %_46 = load i32, ptr %iter, align 4, !noundef !3
; call <i32 as core::iter::range::Step>::forward_unchecked
  %_47 = call noundef i32 @"_ZN47_$LT$i32$u20$as$u20$core..iter..range..Step$GT$17forward_unchecked17h8d7efb28a3d3ad12E"(i32 noundef %_46, i64 noundef 1) #8
  store i32 %_47, ptr %iter, align 4
  %14 = zext i1 %coin_empty to i8
  store volatile i8 %14, ptr %_10, align 1
  br label %bb1
}

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare hidden { i32, i1 } @llvm.sadd.with.overflow.i32(i32, i32) #2

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(none)
declare hidden i1 @llvm.expect.i1(i1, i1) #3

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(inaccessiblemem: write)
declare hidden void @llvm.assume(i1 noundef) #4

; core::panicking::panic_nounwind
; Function Attrs: cold noinline noreturn nounwind
declare void @_ZN4core9panicking14panic_nounwind17h59c09f9524fc568aE(ptr noalias noundef nonnull readonly align 1, i64 noundef) unnamed_addr #5

; Function Attrs: nocallback nofree nounwind willreturn memory(argmem: readwrite)
declare void @llvm.memcpy.p0.p0.i64(ptr noalias nocapture writeonly, ptr noalias nocapture readonly, i64, i1 immarg) #6

; Function Attrs: nounwind
declare void @observe_signers(ptr noundef, i64 noundef) unnamed_addr #1

; Function Attrs: nounwind
declare void @observe_accounts(ptr noundef) unnamed_addr #1

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(argmem: readwrite)
declare void @llvm.lifetime.start.p0(i64 immarg, ptr nocapture) #7

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(argmem: readwrite)
declare void @llvm.lifetime.end.p0(i64 immarg, ptr nocapture) #7

attributes #0 = { inlinehint nounwind "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #1 = { nounwind "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #2 = { nocallback nofree nosync nounwind speculatable willreturn memory(none) }
attributes #3 = { nocallback nofree nosync nounwind willreturn memory(none) }
attributes #4 = { nocallback nofree nosync nounwind willreturn memory(inaccessiblemem: write) }
attributes #5 = { cold noinline noreturn nounwind "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #6 = { nocallback nofree nounwind willreturn memory(argmem: readwrite) }
attributes #7 = { nocallback nofree nosync nounwind willreturn memory(argmem: readwrite) }
attributes #8 = { nounwind }
attributes #9 = { noreturn nounwind }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 8, !"PIC Level", i32 2}
!1 = !{!"rustc version 1.79.0-dev"}
!2 = !{i8 0, i8 2}
!3 = !{}
!4 = !{i32 0, i32 2}
