; ModuleID = 'pass114_late_probe.c42a7eae2abfd033-cgu.0'
source_filename = "pass114_late_probe.c42a7eae2abfd033-cgu.0"
target datalayout = "e-m:e-p:64:64-i64:64-n32:64-S128"
target triple = "sbf"

%"core::fmt::rt::Argument<'_>" = type { %"core::fmt::rt::ArgumentType<'_>" }
%"core::fmt::rt::ArgumentType<'_>" = type { [1 x i64], ptr }

@vtable.0 = private unnamed_addr constant <{ ptr, [16 x i8], ptr, ptr, ptr }> <{ ptr @"_ZN4core3ptr42drop_in_place$LT$alloc..string..String$GT$17hd1d278fe2cba7629E", [16 x i8] c"\18\00\00\00\00\00\00\00\08\00\00\00\00\00\00\00", ptr @"_ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$9write_str17h4b62f46a222bd5b2E", ptr @"_ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$10write_char17hfde5b685689164ccE", ptr @_ZN4core3fmt5Write9write_fmt17hf607f0d92912dfd2E }>, align 8
@0 = private unnamed_addr constant <{ [8 x i8], [8 x i8] }> <{ [8 x i8] zeroinitializer, [8 x i8] undef }>, align 8
@alloc_cc656815297f75969399c3f4b1ad3de4 = private unnamed_addr constant <{ [55 x i8] }> <{ [55 x i8] c"a Display implementation returned an error unexpectedly" }>, align 1
@vtable.1 = private unnamed_addr constant <{ ptr, [16 x i8], ptr }> <{ ptr @"_ZN4core3ptr37drop_in_place$LT$core..fmt..Error$GT$17hc55e87063dbb1cfcE", [16 x i8] c"\00\00\00\00\00\00\00\00\01\00\00\00\00\00\00\00", ptr @"_ZN53_$LT$core..fmt..Error$u20$as$u20$core..fmt..Debug$GT$3fmt17h85666afa16c4890eE" }>, align 8
@alloc_0c7342d701a2219de6bddb6c078f5127 = private unnamed_addr constant <{ [84 x i8] }> <{ [84 x i8] c"/home/runner/work/platform-tools/platform-tools/out/rust/library/alloc/src/string.rs" }>, align 1
@alloc_d5d9fccaf545b6e0545ef73245a3c43f = private unnamed_addr constant <{ ptr, [16 x i8] }> <{ ptr @alloc_0c7342d701a2219de6bddb6c078f5127, [16 x i8] c"T\00\00\00\00\00\00\00\FF\09\00\00\0E\00\00\00" }>, align 8
@alloc_424341b75ece3fa20496f1c69b9fb0ac = private unnamed_addr constant <{ [111 x i8] }> <{ [111 x i8] c"unsafe precondition(s) violated: ptr::write_bytes requires that the destination pointer is aligned and non-null" }>, align 1
@alloc_20b3d155afd5c58c42e598b7e6d186ef = private unnamed_addr constant <{ [93 x i8] }> <{ [93 x i8] c"unsafe precondition(s) violated: NonNull::new_unchecked requires that the pointer is non-null" }>, align 1
@alloc_ec595fc0e82ef92fc59bd74f68296eae = private unnamed_addr constant <{ [73 x i8] }> <{ [73 x i8] c"assertion failed: 0 < pointee_size && pointee_size <= isize::MAX as usize" }>, align 1
@alloc_8394a2083f066ba3e976aa396c04d3a0 = private unnamed_addr constant <{ [90 x i8] }> <{ [90 x i8] c"/home/runner/work/platform-tools/platform-tools/out/rust/library/core/src/ptr/const_ptr.rs" }>, align 1
@alloc_afb1e04822894c5e702f11276eeca143 = private unnamed_addr constant <{ ptr, [16 x i8] }> <{ ptr @alloc_8394a2083f066ba3e976aa396c04d3a0, [16 x i8] c"Z\00\00\00\00\00\00\00?\03\00\00\09\00\00\00" }>, align 8
@alloc_5b79f2642a8cbf6a05af601701bb502f = private unnamed_addr constant <{ [89 x i8] }> <{ [89 x i8] c"/home/runner/work/platform-tools/platform-tools/out/rust/library/core/src/char/methods.rs" }>, align 1
@alloc_e29f835cd238567227661dc24e0368e1 = private unnamed_addr constant <{ ptr, [16 x i8] }> <{ ptr @alloc_5b79f2642a8cbf6a05af601701bb502f, [16 x i8] c"Y\00\00\00\00\00\00\00\05\07\00\00\0D\00\00\00" }>, align 8
@alloc_6b031f9bca8204235732c7c365d04a1d = private unnamed_addr constant <{ [18 x i8] }> <{ [18 x i8] c"encode_utf8: need " }>, align 1
@alloc_28d13efb0f9a95ccb5d02ec33dd195cf = private unnamed_addr constant <{ [19 x i8] }> <{ [19 x i8] c" bytes to encode U+" }>, align 1
@alloc_0d928972d2befd736e581c7fcc5a2f9a = private unnamed_addr constant <{ [21 x i8] }> <{ [21 x i8] c", but the buffer has " }>, align 1
@alloc_d51214f097f67314513b76e97e13aa6b = private unnamed_addr constant <{ ptr, [8 x i8], ptr, [8 x i8], ptr, [8 x i8] }> <{ ptr @alloc_6b031f9bca8204235732c7c365d04a1d, [8 x i8] c"\12\00\00\00\00\00\00\00", ptr @alloc_28d13efb0f9a95ccb5d02ec33dd195cf, [8 x i8] c"\13\00\00\00\00\00\00\00", ptr @alloc_0d928972d2befd736e581c7fcc5a2f9a, [8 x i8] c"\15\00\00\00\00\00\00\00" }>, align 8
@alloc_ead0a6452eb67e6b8ed625150350d4a0 = private unnamed_addr constant <{ ptr, [16 x i8] }> <{ ptr @alloc_5b79f2642a8cbf6a05af601701bb502f, [16 x i8] c"Y\00\00\00\00\00\00\00\FE\06\00\00\0E\00\00\00" }>, align 8
@alloc_91c7fa63c3cfeaa3c795652d5cf060e4 = private unnamed_addr constant <{ [12 x i8] }> <{ [12 x i8] c"invalid args" }>, align 1
@alloc_af99043bc04c419363a7f04d23183506 = private unnamed_addr constant <{ ptr, [8 x i8] }> <{ ptr @alloc_91c7fa63c3cfeaa3c795652d5cf060e4, [8 x i8] c"\0C\00\00\00\00\00\00\00" }>, align 8
@alloc_e823ea955ea2dd1bcfed65d87e219815 = private unnamed_addr constant <{ [84 x i8] }> <{ [84 x i8] c"/home/runner/work/platform-tools/platform-tools/out/rust/library/core/src/fmt/mod.rs" }>, align 1
@alloc_e4fccddea0c43959feb45d791879a000 = private unnamed_addr constant <{ ptr, [16 x i8] }> <{ ptr @alloc_e823ea955ea2dd1bcfed65d87e219815, [16 x i8] c"T\00\00\00\00\00\00\00U\01\00\00\0D\00\00\00" }>, align 8
@alloc_93ced4cd66973a4e8bca3e6a1e33f994 = private unnamed_addr constant <{ [89 x i8] }> <{ [89 x i8] c"/home/runner/work/platform-tools/platform-tools/out/rust/library/core/src/alloc/layout.rs" }>, align 1
@alloc_ef43001908d4e2140f0598778794310e = private unnamed_addr constant <{ ptr, [16 x i8] }> <{ ptr @alloc_93ced4cd66973a4e8bca3e6a1e33f994, [16 x i8] c"Y\00\00\00\00\00\00\00\C3\01\00\00)\00\00\00" }>, align 8
@alloc_fad0cd83b7d1858a846a172eb260e593 = private unnamed_addr constant <{ [42 x i8] }> <{ [42 x i8] c"is_aligned_to: align is not a power-of-two" }>, align 1
@alloc_041983ee8170efdaaf95ba67fd072d26 = private unnamed_addr constant <{ ptr, [8 x i8] }> <{ ptr @alloc_fad0cd83b7d1858a846a172eb260e593, [8 x i8] c"*\00\00\00\00\00\00\00" }>, align 8
@alloc_310ca4c1a780778a2fe8d929c908356a = private unnamed_addr constant <{ ptr, [16 x i8] }> <{ ptr @alloc_8394a2083f066ba3e976aa396c04d3a0, [16 x i8] c"Z\00\00\00\00\00\00\00R\06\00\00\0D\00\00\00" }>, align 8
@alloc_99ac8a81a24cac863217ce4a5cbfabea = private unnamed_addr constant <{ [5 x i8] }> <{ [5 x i8] c"Error" }>, align 1
@1 = private unnamed_addr constant <{ [8 x i8], [8 x i8] }> <{ [8 x i8] c"\01\00\00\00\00\00\00\80", [8 x i8] undef }>, align 8
@alloc_8821998f047ca62cad40e6bc4e4d87c4 = private unnamed_addr constant <{ [1 x i8] }> <{ [1 x i8] c"\01" }>, align 1
@alloc_8f95cb73e89711d65e95d13598508b19 = private unnamed_addr constant <{ [4 x i8] }> <{ [4 x i8] c"S\00\00\00" }>, align 4
@alloc_a6d06679426228b5e58f8de7567c2075 = private unnamed_addr constant <{ [103 x i8] }> <{ [103 x i8] c"/Users/shawwalters/.codex/artifacts/pumpfun-pr-branch-pass114-20261101/late-prs/official-probe/probe.rs" }>, align 1
@alloc_861c8964bbad6d9cede9df277e628fe9 = private unnamed_addr constant <{ [4 x i8] }> <{ [4 x i8] c"\13\00\00\00" }>, align 4
@alloc_0e3505805f4905816c1bd644811a7869 = private unnamed_addr constant <{ [4 x i8] }> <{ [4 x i8] c"\1E\00\00\00" }>, align 4
@alloc_1ba5e1e397ae92b788c97e688ac0b362 = private unnamed_addr constant <{ [4 x i8] }> <{ [4 x i8] c"Y\00\00\00" }>, align 4
@alloc_f94f166953c814e4161e699857179a1e = private unnamed_addr constant <{ [4 x i8] }> <{ [4 x i8] c"T\00\00\00" }>, align 4
@alloc_b5f839a6bda937f2cae73e49fc88071f = private unnamed_addr constant <{ [4 x i8] }> <{ [4 x i8] c"Z\00\00\00" }>, align 4
@alloc_835bb996f1795bf0338da0490417da62 = private unnamed_addr constant <{ [4 x i8] }> <{ [4 x i8] c"P\00\00\00" }>, align 4
@alloc_01eaaa187d2be542d4425f23ab284310 = private unnamed_addr constant <{ [4 x i8] }> <{ [4 x i8] c"M\00\00\00" }>, align 4
@alloc_973adb9e8664e25d4750ddb14e0de56a = private unnamed_addr constant <{ [4 x i8] }> <{ [4 x i8] c"N\00\00\00" }>, align 4
@alloc_e75cefee4bb91125af0ea8444b842ed0 = private unnamed_addr constant <{ [4 x i8] }> <{ [4 x i8] c"[\00\00\00" }>, align 4
@alloc_eb4f91695bc6f999067c65f428fcc4d8 = private unnamed_addr constant <{ [4 x i8] }> <{ [4 x i8] c"X\00\00\00" }>, align 4
@alloc_ebe040a358b3132776a16f34a7b7aa5b = private unnamed_addr constant <{ [38 x i8] }> <{ [38 x i8] c"programs/pump/src/creator/admin_cto.rs" }>, align 1
@alloc_e4468c65f8d1e2b77e8f88d0bdfc7833 = private unnamed_addr constant <{ ptr, [16 x i8] }> <{ ptr @alloc_a6d06679426228b5e58f8de7567c2075, [16 x i8] c"g\00\00\00\00\00\00\00\87\00\00\00G\00\00\00" }>, align 8
@alloc_a9c7f39c0aa194410e7398e0248fb345 = private unnamed_addr constant <{ ptr, [16 x i8] }> <{ ptr @alloc_a6d06679426228b5e58f8de7567c2075, [16 x i8] c"g\00\00\00\00\00\00\00\88\00\00\00R\00\00\00" }>, align 8
@alloc_914b2c69d7eca30497b9feaf15ac92f1 = private unnamed_addr constant <{ [1 x i8] }> zeroinitializer, align 1

; <core::ops::range::Range<usize> as core::slice::index::SliceIndex<[T]>>::get_unchecked_mut
; Function Attrs: inlinehint nounwind
define internal { ptr, i64 } @"_ZN106_$LT$core..ops..range..Range$LT$usize$GT$$u20$as$u20$core..slice..index..SliceIndex$LT$$u5b$T$u5d$$GT$$GT$17get_unchecked_mut17hd1d199a69ef3ebecE"(i64 noundef %self.0, i64 noundef %self.1, ptr noundef %slice.0, i64 noundef %slice.1) unnamed_addr #0 {
start:
  %_14 = alloca [16 x i8], align 8
  br label %bb3

bb3:                                              ; preds = %start
  %new_len = sub nuw i64 %self.1, %self.0
  %data = getelementptr inbounds i8, ptr %slice.0, i64 %self.0
  %0 = insertvalue { ptr, i64 } poison, ptr %data, 0
  %1 = insertvalue { ptr, i64 } %0, i64 %new_len, 1
  ret { ptr, i64 } %1

bb1:                                              ; No predecessors!
  unreachable

bb2:                                              ; No predecessors!
  unreachable
}

; <core::ops::range::Range<usize> as core::slice::index::SliceIndex<[T]>>::index_mut
; Function Attrs: inlinehint nounwind
define internal { ptr, i64 } @"_ZN106_$LT$core..ops..range..Range$LT$usize$GT$$u20$as$u20$core..slice..index..SliceIndex$LT$$u5b$T$u5d$$GT$$GT$9index_mut17h048b4ea69424aa51E"(i64 noundef %self.0, i64 noundef %self.1, ptr noalias noundef nonnull align 1 %slice.0, i64 noundef %slice.1, ptr noalias noundef readonly align 8 dereferenceable(24) %0) unnamed_addr #0 {
start:
  %_3 = icmp ugt i64 %self.0, %self.1
  br i1 %_3, label %bb1, label %bb2

bb2:                                              ; preds = %start
  %_7 = icmp ugt i64 %self.1, %slice.1
  br i1 %_7, label %bb3, label %bb4

bb1:                                              ; preds = %start
; call core::slice::index::slice_index_order_fail
  call void @_ZN4core5slice5index22slice_index_order_fail17hcc61bcee7ef2204dE(i64 noundef %self.0, i64 noundef %self.1, ptr noalias noundef readonly align 8 dereferenceable(24) %0) #21
  unreachable

bb4:                                              ; preds = %bb2
; call <core::ops::range::Range<usize> as core::slice::index::SliceIndex<[T]>>::get_unchecked_mut
  %1 = call { ptr, i64 } @"_ZN106_$LT$core..ops..range..Range$LT$usize$GT$$u20$as$u20$core..slice..index..SliceIndex$LT$$u5b$T$u5d$$GT$$GT$17get_unchecked_mut17hd1d199a69ef3ebecE"(i64 noundef %self.0, i64 noundef %self.1, ptr noundef %slice.0, i64 noundef %slice.1) #22
  %_11.0 = extractvalue { ptr, i64 } %1, 0
  %_11.1 = extractvalue { ptr, i64 } %1, 1
  %2 = insertvalue { ptr, i64 } poison, ptr %_11.0, 0
  %3 = insertvalue { ptr, i64 } %2, i64 %_11.1, 1
  ret { ptr, i64 } %3

bb3:                                              ; preds = %bb2
; call core::slice::index::slice_end_index_len_fail
  call void @_ZN4core5slice5index24slice_end_index_len_fail17h3f8438963677f5b8E(i64 noundef %self.1, i64 noundef %slice.1, ptr noalias noundef readonly align 8 dereferenceable(24) %0) #21
  unreachable
}

; <alloc::vec::Vec<T,A> as alloc::vec::spec_extend::SpecExtend<&T,core::slice::iter::Iter<T>>>::spec_extend
; Function Attrs: nounwind
define internal void @"_ZN132_$LT$alloc..vec..Vec$LT$T$C$A$GT$$u20$as$u20$alloc..vec..spec_extend..SpecExtend$LT$$RF$T$C$core..slice..iter..Iter$LT$T$GT$$GT$$GT$11spec_extend17h97a0acb7d1db89dfE"(ptr noalias noundef align 8 dereferenceable(24) %self, ptr noundef nonnull %0, ptr noundef %1) unnamed_addr #1 {
start:
  %iterator = alloca [16 x i8], align 8
  store ptr %0, ptr %iterator, align 8
  %2 = getelementptr inbounds i8, ptr %iterator, i64 8
  store ptr %1, ptr %2, align 8
; call core::slice::iter::Iter<T>::make_slice
  %3 = call { ptr, i64 } @"_ZN4core5slice4iter13Iter$LT$T$GT$10make_slice17h5ca6add12385cc71E"(ptr noalias noundef readonly align 8 dereferenceable(16) %iterator) #22
  %slice.0 = extractvalue { ptr, i64 } %3, 0
  %slice.1 = extractvalue { ptr, i64 } %3, 1
; call alloc::vec::Vec<T,A>::append_elements
  call void @"_ZN5alloc3vec16Vec$LT$T$C$A$GT$15append_elements17hcb02820fa3a5db71E"(ptr noalias noundef align 8 dereferenceable(24) %self, ptr noundef %slice.0, i64 noundef %slice.1) #22
  ret void
}

; <T as alloc::string::ToString>::to_string
; Function Attrs: inlinehint nounwind
define internal void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr dead_on_unwind noalias nocapture noundef writable sret([24 x i8]) align 8 dereferenceable(24) %_0, ptr noalias noundef readonly align 4 dereferenceable(4) %self) unnamed_addr #0 {
start:
  %_11 = alloca [0 x i8], align 1
  %_9 = alloca [24 x i8], align 8
  %self1 = alloca [1 x i8], align 1
  %formatter = alloca [64 x i8], align 8
  %buf = alloca [24 x i8], align 8
  call void @llvm.lifetime.start.p0(i64 24, ptr %buf)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_9)
  store i64 0, ptr %_9, align 8
  %0 = getelementptr inbounds i8, ptr %_9, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %0, align 8
  %1 = getelementptr inbounds i8, ptr %_9, i64 16
  store i64 0, ptr %1, align 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %buf, ptr align 8 %_9, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_9)
  call void @llvm.lifetime.start.p0(i64 64, ptr %formatter)
  %2 = getelementptr inbounds i8, ptr %formatter, i64 52
  store i32 0, ptr %2, align 4
  %3 = getelementptr inbounds i8, ptr %formatter, i64 48
  store i32 32, ptr %3, align 8
  %4 = getelementptr inbounds i8, ptr %formatter, i64 56
  store i8 3, ptr %4, align 8
  %5 = load i64, ptr @0, align 8, !range !2, !noundef !3
  %6 = load i64, ptr getelementptr inbounds (i8, ptr @0, i64 8), align 8
  store i64 %5, ptr %formatter, align 8
  %7 = getelementptr inbounds i8, ptr %formatter, i64 8
  store i64 %6, ptr %7, align 8
  %8 = load i64, ptr @0, align 8, !range !2, !noundef !3
  %9 = load i64, ptr getelementptr inbounds (i8, ptr @0, i64 8), align 8
  %10 = getelementptr inbounds i8, ptr %formatter, i64 16
  store i64 %8, ptr %10, align 8
  %11 = getelementptr inbounds i8, ptr %10, i64 8
  store i64 %9, ptr %11, align 8
  %12 = getelementptr inbounds i8, ptr %formatter, i64 32
  store ptr %buf, ptr %12, align 8
  %13 = getelementptr inbounds i8, ptr %12, i64 8
  store ptr @vtable.0, ptr %13, align 8
  call void @llvm.lifetime.start.p0(i64 1, ptr %self1)
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %14 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef readonly align 4 dereferenceable(4) %self, ptr noalias noundef align 8 dereferenceable(64) %formatter) #22
  %15 = zext i1 %14 to i8
  store i8 %15, ptr %self1, align 1
  %16 = load i8, ptr %self1, align 1, !range !4, !noundef !3
  %17 = trunc i8 %16 to i1
  %_10 = zext i1 %17 to i64
  switch i64 %_10, label %bb2 [
    i64 0, label %bb4
    i64 1, label %bb3
  ]

bb2:                                              ; preds = %start
  unreachable

bb4:                                              ; preds = %start
  call void @llvm.lifetime.end.p0(i64 1, ptr %self1)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_0, ptr align 8 %buf, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr %formatter)
  call void @llvm.lifetime.end.p0(i64 24, ptr %buf)
  ret void

bb3:                                              ; preds = %start
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11, ptr noalias noundef readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #21
  unreachable
}

; <u8 as core::default::Default>::default
; Function Attrs: alwaysinline nounwind
define internal noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() unnamed_addr #2 {
start:
  ret i8 0
}

; core::intrinsics::write_bytes::precondition_check
; Function Attrs: inlinehint nounwind
define internal void @_ZN4core10intrinsics11write_bytes18precondition_check17hd24e09892c9ab5e4E(ptr noundef %addr, i64 noundef %align) unnamed_addr #0 {
start:
; call core::ub_checks::is_aligned_and_not_null
  %_3 = call noundef zeroext i1 @_ZN4core9ub_checks23is_aligned_and_not_null17hcabcf8abc95e5d7fE(ptr noundef %addr, i64 noundef %align) #22
  br i1 %_3, label %bb2, label %bb3

bb3:                                              ; preds = %start
; call core::panicking::panic_nounwind
  call void @_ZN4core9panicking14panic_nounwind17h59c09f9524fc568aE(ptr noalias noundef nonnull readonly align 1 @alloc_424341b75ece3fa20496f1c69b9fb0ac, i64 noundef 111) #21
  unreachable

bb2:                                              ; preds = %start
  ret void
}

; core::intrinsics::is_val_statically_known
; Function Attrs: nounwind
define internal noundef zeroext i1 @_ZN4core10intrinsics23is_val_statically_known17hc11cc68d41c48f5eE(i1 noundef zeroext %_arg) unnamed_addr #1 {
start:
  ret i1 false
}

; core::intrinsics::unlikely
; Function Attrs: nounwind
define internal noundef zeroext i1 @_ZN4core10intrinsics8unlikely17h91c20b0f228684e2E(i1 noundef zeroext %b) unnamed_addr #1 {
start:
  ret i1 %b
}

; core::cmp::impls::<impl core::cmp::Ord for usize>::cmp
; Function Attrs: inlinehint nounwind
define internal noundef i8 @"_ZN4core3cmp5impls50_$LT$impl$u20$core..cmp..Ord$u20$for$u20$usize$GT$3cmp17h6115fb2632dca20aE"(ptr noalias noundef readonly align 8 dereferenceable(8) %self, ptr noalias noundef readonly align 8 dereferenceable(8) %other) unnamed_addr #0 {
start:
  %_3 = load i64, ptr %self, align 8, !noundef !3
  %_4 = load i64, ptr %other, align 8, !noundef !3
  %0 = icmp ult i64 %_3, %_4
  %1 = icmp ne i64 %_3, %_4
  %2 = select i1 %1, i8 1, i8 0
  %_0 = select i1 %0, i8 -1, i8 %2
  ret i8 %_0
}

; core::cmp::impls::<impl core::cmp::PartialEq for bool>::eq
; Function Attrs: inlinehint nounwind
define internal noundef zeroext i1 @"_ZN4core3cmp5impls55_$LT$impl$u20$core..cmp..PartialEq$u20$for$u20$bool$GT$2eq17hc3a2858fc4477333E"(ptr noalias noundef readonly align 1 dereferenceable(1) %self, ptr noalias noundef readonly align 1 dereferenceable(1) %other) unnamed_addr #0 {
start:
  %0 = load i8, ptr %self, align 1, !range !4, !noundef !3
  %_3 = trunc i8 %0 to i1
  %1 = load i8, ptr %other, align 1, !range !4, !noundef !3
  %_4 = trunc i8 %1 to i1
  %_0 = icmp eq i1 %_3, %_4
  ret i1 %_0
}

; core::fmt::Write::write_fmt
; Function Attrs: nounwind
define internal noundef zeroext i1 @_ZN4core3fmt5Write9write_fmt17hf607f0d92912dfd2E(ptr noalias noundef align 8 dereferenceable(24) %self, ptr noalias nocapture noundef align 8 dereferenceable(48) %args) unnamed_addr #1 {
start:
; call <&mut W as core::fmt::Write::write_fmt::SpecWriteFmt>::spec_write_fmt
  %_0 = call noundef zeroext i1 @"_ZN75_$LT$$RF$mut$u20$W$u20$as$u20$core..fmt..Write..write_fmt..SpecWriteFmt$GT$14spec_write_fmt17haafb67d99364a4b3E"(ptr noalias noundef align 8 dereferenceable(24) %self, ptr noalias nocapture noundef readonly align 8 dereferenceable(48) %args) #22
  ret i1 %_0
}

; core::fmt::Arguments::as_statically_known_str
; Function Attrs: inlinehint nounwind
define internal { ptr, i64 } @_ZN4core3fmt9Arguments23as_statically_known_str17h724859523fc262c5E(ptr noalias noundef readonly align 8 dereferenceable(48) %self) unnamed_addr #0 {
start:
  %0 = alloca [1 x i8], align 1
  %_4 = alloca [1 x i8], align 1
  %s = alloca [16 x i8], align 8
  %_0 = alloca [16 x i8], align 8
  call void @llvm.lifetime.start.p0(i64 16, ptr %s)
  %_6.0 = load ptr, ptr %self, align 8, !nonnull !3, !align !5, !noundef !3
  %1 = getelementptr inbounds i8, ptr %self, i64 8
  %_6.1 = load i64, ptr %1, align 8, !noundef !3
  %2 = getelementptr inbounds i8, ptr %self, i64 16
  %_7.0 = load ptr, ptr %2, align 8, !nonnull !3, !align !5, !noundef !3
  %3 = getelementptr inbounds i8, ptr %2, i64 8
  %_7.1 = load i64, ptr %3, align 8, !noundef !3
  %4 = icmp eq i64 %_6.1, 0
  br i1 %4, label %bb7, label %bb8

bb7:                                              ; preds = %start
  %5 = icmp eq i64 %_7.1, 0
  br i1 %5, label %bb10, label %bb6

bb8:                                              ; preds = %start
  %6 = icmp eq i64 %_6.1, 1
  br i1 %6, label %bb9, label %bb6

bb10:                                             ; preds = %bb7
  store ptr inttoptr (i64 1 to ptr), ptr %s, align 8
  %7 = getelementptr inbounds i8, ptr %s, i64 8
  store i64 0, ptr %7, align 8
  br label %bb5

bb6:                                              ; preds = %bb9, %bb8, %bb7
  %8 = load ptr, ptr @0, align 8, !align !6, !noundef !3
  %9 = load i64, ptr getelementptr inbounds (i8, ptr @0, i64 8), align 8
  store ptr %8, ptr %s, align 8
  %10 = getelementptr inbounds i8, ptr %s, i64 8
  store i64 %9, ptr %10, align 8
  br label %bb5

bb5:                                              ; preds = %bb6, %bb11, %bb10
  call void @llvm.lifetime.start.p0(i64 1, ptr %_4)
  %11 = load ptr, ptr %s, align 8, !noundef !3
  %12 = ptrtoint ptr %11 to i64
  %13 = icmp eq i64 %12, 0
  %_14 = select i1 %13, i64 0, i64 1
  switch i64 %_14, label %bb15 [
    i64 1, label %bb14
    i64 0, label %bb13
  ]

bb9:                                              ; preds = %bb8
  %14 = icmp eq i64 %_7.1, 0
  br i1 %14, label %bb11, label %bb6

bb11:                                             ; preds = %bb9
  %s1 = getelementptr inbounds [0 x { ptr, i64 }], ptr %_6.0, i64 0, i64 0
  %15 = getelementptr inbounds [0 x { ptr, i64 }], ptr %_6.0, i64 0, i64 0
  %_13.0 = load ptr, ptr %15, align 8, !nonnull !3, !align !6, !noundef !3
  %16 = getelementptr inbounds i8, ptr %15, i64 8
  %_13.1 = load i64, ptr %16, align 8, !noundef !3
  store ptr %_13.0, ptr %s, align 8
  %17 = getelementptr inbounds i8, ptr %s, i64 8
  store i64 %_13.1, ptr %17, align 8
  br label %bb5

bb15:                                             ; preds = %bb5
  unreachable

bb14:                                             ; preds = %bb5
  store i8 1, ptr %_4, align 1
  br label %bb12

bb13:                                             ; preds = %bb5
  store i8 0, ptr %_4, align 1
  br label %bb12

bb12:                                             ; preds = %bb13, %bb14
  call void @llvm.lifetime.start.p0(i64 1, ptr %0)
  %18 = load i8, ptr %_4, align 1, !range !4, !noundef !3
  %19 = trunc i8 %18 to i1
  %20 = call i1 @llvm.is.constant.i1(i1 %19)
  %21 = zext i1 %20 to i8
  store i8 %21, ptr %0, align 1
  %22 = load i8, ptr %0, align 1, !range !4, !noundef !3
  %_3 = trunc i8 %22 to i1
  call void @llvm.lifetime.end.p0(i64 1, ptr %0)
  br i1 %_3, label %bb2, label %bb3

bb3:                                              ; preds = %bb12
  call void @llvm.lifetime.end.p0(i64 1, ptr %_4)
  %23 = load ptr, ptr @0, align 8, !align !6, !noundef !3
  %24 = load i64, ptr getelementptr inbounds (i8, ptr @0, i64 8), align 8
  store ptr %23, ptr %_0, align 8
  %25 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %24, ptr %25, align 8
  br label %bb4

bb2:                                              ; preds = %bb12
  call void @llvm.lifetime.end.p0(i64 1, ptr %_4)
  %26 = load ptr, ptr %s, align 8, !align !6, !noundef !3
  %27 = getelementptr inbounds i8, ptr %s, i64 8
  %28 = load i64, ptr %27, align 8
  store ptr %26, ptr %_0, align 8
  %29 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %28, ptr %29, align 8
  br label %bb4

bb4:                                              ; preds = %bb2, %bb3
  call void @llvm.lifetime.end.p0(i64 16, ptr %s)
  %30 = load ptr, ptr %_0, align 8, !align !6, !noundef !3
  %31 = getelementptr inbounds i8, ptr %_0, i64 8
  %32 = load i64, ptr %31, align 8
  %33 = insertvalue { ptr, i64 } poison, ptr %30, 0
  %34 = insertvalue { ptr, i64 } %33, i64 %32, 1
  ret { ptr, i64 } %34
}

; core::ops::function::FnOnce::call_once
; Function Attrs: inlinehint nounwind
define internal noundef i8 @_ZN4core3ops8function6FnOnce9call_once17hb1bad2e3e1b02e6cE(ptr noalias noundef readonly align 8 dereferenceable(8) %0, ptr noalias noundef readonly align 8 dereferenceable(8) %1) unnamed_addr #0 {
start:
  %_2 = alloca [16 x i8], align 8
  store ptr %0, ptr %_2, align 8
  %2 = getelementptr inbounds i8, ptr %_2, i64 8
  store ptr %1, ptr %2, align 8
  %3 = load ptr, ptr %_2, align 8, !nonnull !3, !align !5, !noundef !3
  %4 = getelementptr inbounds i8, ptr %_2, i64 8
  %5 = load ptr, ptr %4, align 8, !nonnull !3, !align !5, !noundef !3
; call core::cmp::impls::<impl core::cmp::Ord for usize>::cmp
  %_0 = call noundef i8 @"_ZN4core3cmp5impls50_$LT$impl$u20$core..cmp..Ord$u20$for$u20$usize$GT$3cmp17h6115fb2632dca20aE"(ptr noalias noundef readonly align 8 dereferenceable(8) %3, ptr noalias noundef readonly align 8 dereferenceable(8) %5) #22, !range !7
  ret i8 %_0
}

; core::ptr::read_unaligned
; Function Attrs: inlinehint nounwind
define internal noundef i64 @_ZN4core3ptr14read_unaligned17h516ffa4b8b8a8286E(ptr noundef %src) unnamed_addr #0 {
start:
  %tmp = alloca [8 x i8], align 8
  call void @llvm.lifetime.start.p0(i64 8, ptr %tmp)
  br label %bb3

bb3:                                              ; preds = %start
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %tmp, ptr align 1 %src, i64 8, i1 false)
  %self = load i64, ptr %tmp, align 8
  call void @llvm.lifetime.end.p0(i64 8, ptr %tmp)
  ret i64 %self

bb1:                                              ; No predecessors!
  unreachable

bb2:                                              ; No predecessors!
  unreachable
}

; core::ptr::read_unaligned
; Function Attrs: inlinehint nounwind
define internal void @_ZN4core3ptr14read_unaligned17hfb0286d8a885119bE(ptr dead_on_unwind noalias nocapture noundef writable sret([32 x i8]) align 1 dereferenceable(32) %_0, ptr noundef %src) unnamed_addr #0 {
start:
  %slot = alloca [32 x i8], align 1
  %self = alloca [32 x i8], align 1
  %tmp = alloca [32 x i8], align 1
  call void @llvm.lifetime.start.p0(i64 32, ptr %tmp)
  br label %bb3

bb3:                                              ; preds = %start
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %tmp, ptr align 1 %src, i64 32, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr %self)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %self, ptr align 1 %tmp, i64 32, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr %slot)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %slot, ptr align 1 %self, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_0, ptr align 1 %slot, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %slot)
  call void @llvm.lifetime.end.p0(i64 32, ptr %self)
  call void @llvm.lifetime.end.p0(i64 32, ptr %tmp)
  ret void

bb1:                                              ; No predecessors!
  unreachable

bb2:                                              ; No predecessors!
  unreachable
}

; core::ptr::drop_in_place<core::fmt::Error>
; Function Attrs: inlinehint nounwind
define internal void @"_ZN4core3ptr37drop_in_place$LT$core..fmt..Error$GT$17hc55e87063dbb1cfcE"(ptr noalias noundef nonnull align 1 %_1) unnamed_addr #0 {
start:
  ret void
}

; core::ptr::drop_in_place<alloc::string::String>
; Function Attrs: nounwind
define internal void @"_ZN4core3ptr42drop_in_place$LT$alloc..string..String$GT$17hd1d278fe2cba7629E"(ptr noalias noundef align 8 dereferenceable(24) %_1) unnamed_addr #1 {
start:
; call core::ptr::drop_in_place<alloc::vec::Vec<u8>>
  call void @"_ZN4core3ptr46drop_in_place$LT$alloc..vec..Vec$LT$u8$GT$$GT$17hb09713401b9fe8c0E"(ptr noalias noundef align 8 dereferenceable(24) %_1) #22
  ret void
}

; core::ptr::drop_in_place<alloc::vec::Vec<u8>>
; Function Attrs: nounwind
define internal void @"_ZN4core3ptr46drop_in_place$LT$alloc..vec..Vec$LT$u8$GT$$GT$17hb09713401b9fe8c0E"(ptr noalias noundef align 8 dereferenceable(24) %_1) unnamed_addr #1 {
start:
; call <alloc::vec::Vec<T,A> as core::ops::drop::Drop>::drop
  call void @"_ZN70_$LT$alloc..vec..Vec$LT$T$C$A$GT$$u20$as$u20$core..ops..drop..Drop$GT$4drop17h2fce56f4d16a6d65E"(ptr noalias noundef align 8 dereferenceable(24) %_1) #22
; call core::ptr::drop_in_place<alloc::raw_vec::RawVec<u8>>
  call void @"_ZN4core3ptr53drop_in_place$LT$alloc..raw_vec..RawVec$LT$u8$GT$$GT$17h0e70d4db24ebe8e3E"(ptr noalias noundef align 8 dereferenceable(16) %_1) #22
  ret void
}

; core::ptr::drop_in_place<alloc::raw_vec::RawVec<u8>>
; Function Attrs: nounwind
define internal void @"_ZN4core3ptr53drop_in_place$LT$alloc..raw_vec..RawVec$LT$u8$GT$$GT$17h0e70d4db24ebe8e3E"(ptr noalias noundef align 8 dereferenceable(16) %_1) unnamed_addr #1 {
start:
; call <alloc::raw_vec::RawVec<T,A> as core::ops::drop::Drop>::drop
  call void @"_ZN77_$LT$alloc..raw_vec..RawVec$LT$T$C$A$GT$$u20$as$u20$core..ops..drop..Drop$GT$4drop17h3b9335e739eb6028E"(ptr noalias noundef align 8 dereferenceable(16) %_1) #22
  ret void
}

; core::ptr::non_null::NonNull<T>::new_unchecked::precondition_check
; Function Attrs: inlinehint nounwind
define internal void @"_ZN4core3ptr8non_null16NonNull$LT$T$GT$13new_unchecked18precondition_check17hdc271a756f76605cE"(ptr noundef %ptr) unnamed_addr #0 {
start:
  %_4 = ptrtoint ptr %ptr to i64
  %0 = icmp eq i64 %_4, 0
  br i1 %0, label %bb1, label %bb2

bb1:                                              ; preds = %start
; call core::panicking::panic_nounwind
  call void @_ZN4core9panicking14panic_nounwind17h59c09f9524fc568aE(ptr noalias noundef nonnull readonly align 1 @alloc_20b3d155afd5c58c42e598b7e6d186ef, i64 noundef 93) #21
  unreachable

bb2:                                              ; preds = %start
  ret void
}

; core::ptr::const_ptr::<impl *const T>::sub_ptr
; Function Attrs: inlinehint nounwind
define internal noundef i64 @"_ZN4core3ptr9const_ptr33_$LT$impl$u20$$BP$const$u20$T$GT$7sub_ptr17h26f56479ac07e811E"(ptr noundef %self, ptr noundef %origin) unnamed_addr #0 {
start:
  %0 = alloca [8 x i8], align 8
  br label %bb3

bb3:                                              ; preds = %start
  br label %bb4

bb1:                                              ; No predecessors!
  unreachable

bb2:                                              ; No predecessors!
  unreachable

bb4:                                              ; preds = %bb3
  br label %bb5

bb5:                                              ; preds = %bb4
  call void @llvm.lifetime.start.p0(i64 8, ptr %0)
  %1 = ptrtoint ptr %self to i64
  %2 = ptrtoint ptr %origin to i64
  %3 = sub nuw i64 %1, %2
  %4 = udiv exact i64 %3, 1
  store i64 %4, ptr %0, align 8
  %_0 = load i64, ptr %0, align 8, !noundef !3
  call void @llvm.lifetime.end.p0(i64 8, ptr %0)
  ret i64 %_0

bb6:                                              ; No predecessors!
; call core::panicking::panic
  call void @_ZN4core9panicking5panic17h0d41b9de9b340d2cE(ptr noalias noundef nonnull readonly align 1 @alloc_ec595fc0e82ef92fc59bd74f68296eae, i64 noundef 73, ptr noalias noundef readonly align 8 dereferenceable(24) @alloc_afb1e04822894c5e702f11276eeca143) #21
  unreachable
}

; core::char::methods::encode_utf8_raw
; Function Attrs: inlinehint nounwind
define internal { ptr, i64 } @_ZN4core4char7methods15encode_utf8_raw17h84badf475ef2bb54E(i32 noundef %0, ptr noalias noundef nonnull align 1 %dst.0, i64 noundef %dst.1) unnamed_addr #0 {
start:
  %_95 = alloca [16 x i8], align 8
  %_92 = alloca [48 x i8], align 8
  %_84 = alloca [16 x i8], align 8
  %_80 = alloca [16 x i8], align 8
  %_76 = alloca [16 x i8], align 8
  %_70 = alloca [8 x i8], align 8
  %_68 = alloca [16 x i8], align 8
  %_66 = alloca [16 x i8], align 8
  %_64 = alloca [16 x i8], align 8
  %_63 = alloca [48 x i8], align 8
  %_59 = alloca [48 x i8], align 8
  %len = alloca [8 x i8], align 8
  %code = alloca [4 x i8], align 4
  store i32 %0, ptr %code, align 4
  call void @llvm.lifetime.start.p0(i64 8, ptr %len)
  %code1 = load i32, ptr %code, align 4, !noundef !3
  %_72 = icmp ult i32 %code1, 128
  br i1 %_72, label %bb11, label %bb12

bb12:                                             ; preds = %start
  %_73 = icmp ult i32 %code1, 2048
  br i1 %_73, label %bb13, label %bb14

bb11:                                             ; preds = %start
  store i64 1, ptr %len, align 8
  br label %bb19

bb14:                                             ; preds = %bb12
  %_74 = icmp ult i32 %code1, 65536
  br i1 %_74, label %bb15, label %bb16

bb13:                                             ; preds = %bb12
  store i64 2, ptr %len, align 8
  br label %bb18

bb16:                                             ; preds = %bb14
  store i64 4, ptr %len, align 8
  br label %bb17

bb15:                                             ; preds = %bb14
  store i64 3, ptr %len, align 8
  br label %bb17

bb17:                                             ; preds = %bb15, %bb16
  br label %bb18

bb18:                                             ; preds = %bb13, %bb17
  br label %bb19

bb19:                                             ; preds = %bb11, %bb18
  %_5 = load i64, ptr %len, align 8, !noundef !3
  switch i64 %_5, label %bb1 [
    i64 1, label %bb2
    i64 2, label %bb3
    i64 3, label %bb4
    i64 4, label %bb5
  ]

bb1:                                              ; preds = %bb5, %bb4, %bb3, %bb2, %bb19
  call void @llvm.lifetime.start.p0(i64 48, ptr %_59)
  call void @llvm.lifetime.start.p0(i64 48, ptr %_63)
  call void @llvm.lifetime.start.p0(i64 16, ptr %_64)
  call void @llvm.lifetime.start.p0(i64 16, ptr %_76)
  store ptr %len, ptr %_76, align 8
  %1 = getelementptr inbounds i8, ptr %_76, i64 8
  store ptr @"_ZN4core3fmt3num3imp54_$LT$impl$u20$core..fmt..Display$u20$for$u20$usize$GT$3fmt17h1fc8323720f2b108E", ptr %1, align 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_64, ptr align 8 %_76, i64 16, i1 false)
  call void @llvm.lifetime.end.p0(i64 16, ptr %_76)
  call void @llvm.lifetime.start.p0(i64 16, ptr %_66)
  call void @llvm.lifetime.start.p0(i64 16, ptr %_80)
  store ptr %code, ptr %_80, align 8
  %2 = getelementptr inbounds i8, ptr %_80, i64 8
  store ptr @"_ZN4core3fmt3num53_$LT$impl$u20$core..fmt..UpperHex$u20$for$u20$u32$GT$3fmt17hf4c59f29dbc8ac3eE", ptr %2, align 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_66, ptr align 8 %_80, i64 16, i1 false)
  call void @llvm.lifetime.end.p0(i64 16, ptr %_80)
  call void @llvm.lifetime.start.p0(i64 16, ptr %_68)
  call void @llvm.lifetime.start.p0(i64 8, ptr %_70)
  store i64 %dst.1, ptr %_70, align 8
  call void @llvm.lifetime.start.p0(i64 16, ptr %_84)
  store ptr %_70, ptr %_84, align 8
  %3 = getelementptr inbounds i8, ptr %_84, i64 8
  store ptr @"_ZN4core3fmt3num3imp54_$LT$impl$u20$core..fmt..Display$u20$for$u20$usize$GT$3fmt17h1fc8323720f2b108E", ptr %3, align 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_68, ptr align 8 %_84, i64 16, i1 false)
  call void @llvm.lifetime.end.p0(i64 16, ptr %_84)
  %4 = getelementptr inbounds [3 x %"core::fmt::rt::Argument<'_>"], ptr %_63, i64 0, i64 0
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %4, ptr align 8 %_64, i64 16, i1 false)
  %5 = getelementptr inbounds [3 x %"core::fmt::rt::Argument<'_>"], ptr %_63, i64 0, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %5, ptr align 8 %_66, i64 16, i1 false)
  %6 = getelementptr inbounds [3 x %"core::fmt::rt::Argument<'_>"], ptr %_63, i64 0, i64 2
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %6, ptr align 8 %_68, i64 16, i1 false)
  call void @llvm.lifetime.end.p0(i64 16, ptr %_68)
  call void @llvm.lifetime.end.p0(i64 16, ptr %_66)
  call void @llvm.lifetime.end.p0(i64 16, ptr %_64)
  br label %bb20

bb2:                                              ; preds = %bb19
  %_7 = icmp uge i64 %dst.1, 1
  br i1 %_7, label %bb6, label %bb1

bb3:                                              ; preds = %bb19
  %_9 = icmp uge i64 %dst.1, 2
  br i1 %_9, label %bb7, label %bb1

bb4:                                              ; preds = %bb19
  %_11 = icmp uge i64 %dst.1, 3
  br i1 %_11, label %bb8, label %bb1

bb5:                                              ; preds = %bb19
  %_13 = icmp uge i64 %dst.1, 4
  br i1 %_13, label %bb9, label %bb1

bb6:                                              ; preds = %bb2
  %a = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 0
  %_15 = load i32, ptr %code, align 4, !noundef !3
  %7 = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 0
  %8 = trunc i32 %_15 to i8
  store i8 %8, ptr %7, align 1
  br label %bb10

bb10:                                             ; preds = %bb9, %bb8, %bb7, %bb6
  %index = load i64, ptr %len, align 8, !noundef !3
  call void @llvm.lifetime.start.p0(i64 16, ptr %_95)
  store i64 0, ptr %_95, align 8
  %9 = getelementptr inbounds i8, ptr %_95, i64 8
  store i64 %index, ptr %9, align 8
  %10 = load i64, ptr %_95, align 8, !noundef !3
  %11 = getelementptr inbounds i8, ptr %_95, i64 8
  %12 = load i64, ptr %11, align 8, !noundef !3
; call <core::ops::range::Range<usize> as core::slice::index::SliceIndex<[T]>>::index_mut
  %13 = call { ptr, i64 } @"_ZN106_$LT$core..ops..range..Range$LT$usize$GT$$u20$as$u20$core..slice..index..SliceIndex$LT$$u5b$T$u5d$$GT$$GT$9index_mut17h048b4ea69424aa51E"(i64 noundef %10, i64 noundef %12, ptr noalias noundef nonnull align 1 %dst.0, i64 noundef %dst.1, ptr noalias noundef readonly align 8 dereferenceable(24) @alloc_e29f835cd238567227661dc24e0368e1) #22
  %_0.0 = extractvalue { ptr, i64 } %13, 0
  %_0.1 = extractvalue { ptr, i64 } %13, 1
  call void @llvm.lifetime.end.p0(i64 16, ptr %_95)
  call void @llvm.lifetime.end.p0(i64 8, ptr %len)
  %14 = insertvalue { ptr, i64 } poison, ptr %_0.0, 0
  %15 = insertvalue { ptr, i64 } %14, i64 %_0.1, 1
  ret { ptr, i64 } %15

bb7:                                              ; preds = %bb3
  %a2 = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 0
  %b = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 1
  %_21 = load i32, ptr %code, align 4, !noundef !3
  %_20 = lshr i32 %_21, 6
  %_19 = and i32 %_20, 31
  %_18 = trunc i32 %_19 to i8
  %16 = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 0
  %17 = or i8 %_18, -64
  store i8 %17, ptr %16, align 1
  %_24 = load i32, ptr %code, align 4, !noundef !3
  %_23 = and i32 %_24, 63
  %_22 = trunc i32 %_23 to i8
  %18 = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 1
  %19 = or i8 %_22, -128
  store i8 %19, ptr %18, align 1
  br label %bb10

bb8:                                              ; preds = %bb4
  %a3 = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 0
  %b4 = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 1
  %c = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 2
  %_31 = load i32, ptr %code, align 4, !noundef !3
  %_30 = lshr i32 %_31, 12
  %_29 = and i32 %_30, 15
  %_28 = trunc i32 %_29 to i8
  %20 = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 0
  %21 = or i8 %_28, -32
  store i8 %21, ptr %20, align 1
  %_35 = load i32, ptr %code, align 4, !noundef !3
  %_34 = lshr i32 %_35, 6
  %_33 = and i32 %_34, 63
  %_32 = trunc i32 %_33 to i8
  %22 = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 1
  %23 = or i8 %_32, -128
  store i8 %23, ptr %22, align 1
  %_38 = load i32, ptr %code, align 4, !noundef !3
  %_37 = and i32 %_38, 63
  %_36 = trunc i32 %_37 to i8
  %24 = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 2
  %25 = or i8 %_36, -128
  store i8 %25, ptr %24, align 1
  br label %bb10

bb9:                                              ; preds = %bb5
  %a5 = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 0
  %b6 = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 1
  %c7 = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 2
  %d = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 3
  %_46 = load i32, ptr %code, align 4, !noundef !3
  %_45 = lshr i32 %_46, 18
  %_44 = and i32 %_45, 7
  %_43 = trunc i32 %_44 to i8
  %26 = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 0
  %27 = or i8 %_43, -16
  store i8 %27, ptr %26, align 1
  %_50 = load i32, ptr %code, align 4, !noundef !3
  %_49 = lshr i32 %_50, 12
  %_48 = and i32 %_49, 63
  %_47 = trunc i32 %_48 to i8
  %28 = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 1
  %29 = or i8 %_47, -128
  store i8 %29, ptr %28, align 1
  %_54 = load i32, ptr %code, align 4, !noundef !3
  %_53 = lshr i32 %_54, 6
  %_52 = and i32 %_53, 63
  %_51 = trunc i32 %_52 to i8
  %30 = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 2
  %31 = or i8 %_51, -128
  store i8 %31, ptr %30, align 1
  %_57 = load i32, ptr %code, align 4, !noundef !3
  %_56 = and i32 %_57, 63
  %_55 = trunc i32 %_56 to i8
  %32 = getelementptr inbounds [0 x i8], ptr %dst.0, i64 0, i64 3
  %33 = or i8 %_55, -128
  store i8 %33, ptr %32, align 1
  br label %bb10

bb20:                                             ; preds = %bb1
  br label %bb23

bb23:                                             ; preds = %bb20
  store ptr @alloc_d51214f097f67314513b76e97e13aa6b, ptr %_59, align 8
  %34 = getelementptr inbounds i8, ptr %_59, i64 8
  store i64 3, ptr %34, align 8
  %35 = load ptr, ptr @0, align 8, !align !5, !noundef !3
  %36 = load i64, ptr getelementptr inbounds (i8, ptr @0, i64 8), align 8
  %37 = getelementptr inbounds i8, ptr %_59, i64 32
  store ptr %35, ptr %37, align 8
  %38 = getelementptr inbounds i8, ptr %37, i64 8
  store i64 %36, ptr %38, align 8
  %39 = getelementptr inbounds i8, ptr %_59, i64 16
  store ptr %_63, ptr %39, align 8
  %40 = getelementptr inbounds i8, ptr %39, i64 8
  store i64 3, ptr %40, align 8
; call core::panicking::panic_fmt
  call void @_ZN4core9panicking9panic_fmt17h0f7a5cdbeae7e874E(ptr noalias nocapture noundef readonly align 8 dereferenceable(48) %_59, ptr noalias noundef readonly align 8 dereferenceable(24) @alloc_ead0a6452eb67e6b8ed625150350d4a0) #21
  unreachable

bb21:                                             ; No predecessors!
  br label %bb22

bb22:                                             ; preds = %bb21
  call void @llvm.lifetime.start.p0(i64 48, ptr %_92)
  store ptr @alloc_af99043bc04c419363a7f04d23183506, ptr %_92, align 8
  %41 = getelementptr inbounds i8, ptr %_92, i64 8
  store i64 1, ptr %41, align 8
  %42 = load ptr, ptr @0, align 8, !align !5, !noundef !3
  %43 = load i64, ptr getelementptr inbounds (i8, ptr @0, i64 8), align 8
  %44 = getelementptr inbounds i8, ptr %_92, i64 32
  store ptr %42, ptr %44, align 8
  %45 = getelementptr inbounds i8, ptr %44, i64 8
  store i64 %43, ptr %45, align 8
  %46 = getelementptr inbounds i8, ptr %_92, i64 16
  store ptr inttoptr (i64 8 to ptr), ptr %46, align 8
  %47 = getelementptr inbounds i8, ptr %46, i64 8
  store i64 0, ptr %47, align 8
; call core::panicking::panic_fmt
  call void @_ZN4core9panicking9panic_fmt17h0f7a5cdbeae7e874E(ptr noalias nocapture noundef readonly align 8 dereferenceable(48) %_92, ptr noalias noundef readonly align 8 dereferenceable(24) @alloc_e4fccddea0c43959feb45d791879a000) #21
  unreachable
}

; core::alloc::layout::Layout::array::inner
; Function Attrs: inlinehint nounwind
define internal { i64, i64 } @_ZN4core5alloc6layout6Layout5array5inner17h433a9d6723d6a257E(i64 noundef %element_size, i64 noundef %align, i64 noundef %n) unnamed_addr #0 {
start:
  %_18 = alloca [8 x i8], align 8
  %_13 = alloca [8 x i8], align 8
  %_9 = alloca [16 x i8], align 8
  %_0 = alloca [16 x i8], align 8
  %0 = icmp eq i64 %element_size, 0
  br i1 %0, label %bb5, label %bb1

bb5:                                              ; preds = %bb4, %start
  %array_size = mul nuw i64 %element_size, %n
  call void @llvm.lifetime.start.p0(i64 16, ptr %_9)
  call void @llvm.lifetime.start.p0(i64 8, ptr %_18)
  store i64 %align, ptr %_18, align 8
  %_19 = load i64, ptr %_18, align 8, !range !8, !noundef !3
  %_20 = icmp uge i64 %_19, 1
  %_21 = icmp ule i64 %_19, -9223372036854775808
  %_22 = and i1 %_20, %_21
  call void @llvm.assume(i1 %_22)
  call void @llvm.lifetime.end.p0(i64 8, ptr %_18)
  %1 = icmp uge i64 %_19, 1
  call void @llvm.assume(i1 %1)
  %2 = icmp ule i64 %_19, -9223372036854775808
  call void @llvm.assume(i1 %2)
  %3 = getelementptr inbounds i8, ptr %_9, i64 8
  store i64 %array_size, ptr %3, align 8
  store i64 %_19, ptr %_9, align 8
  %4 = load i64, ptr %_9, align 8, !range !8, !noundef !3
  %5 = getelementptr inbounds i8, ptr %_9, i64 8
  %6 = load i64, ptr %5, align 8, !noundef !3
  store i64 %4, ptr %_0, align 8
  %7 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %6, ptr %7, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %_9)
  br label %bb6

bb1:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 8, ptr %_13)
  store i64 %align, ptr %_13, align 8
  %_14 = load i64, ptr %_13, align 8, !range !8, !noundef !3
  %_15 = icmp uge i64 %_14, 1
  %_16 = icmp ule i64 %_14, -9223372036854775808
  %_17 = and i1 %_15, %_16
  call void @llvm.assume(i1 %_17)
  call void @llvm.lifetime.end.p0(i64 8, ptr %_13)
  %_11 = sub i64 %_14, 1
  %_6 = sub i64 9223372036854775807, %_11
  %_7 = icmp eq i64 %element_size, 0
  %8 = call i1 @llvm.expect.i1(i1 %_7, i1 false)
  br i1 %8, label %panic, label %bb2

bb2:                                              ; preds = %bb1
  %_5 = udiv i64 %_6, %element_size
  %_4 = icmp ugt i64 %n, %_5
  br i1 %_4, label %bb3, label %bb4

panic:                                            ; preds = %bb1
; call core::panicking::panic_const::panic_const_div_by_zero
  call void @_ZN4core9panicking11panic_const23panic_const_div_by_zero17hd6b7f0f5931b4251E(ptr noalias noundef readonly align 8 dereferenceable(24) @alloc_ef43001908d4e2140f0598778794310e) #21
  unreachable

bb4:                                              ; preds = %bb2
  br label %bb5

bb3:                                              ; preds = %bb2
  %9 = load i64, ptr @0, align 8, !range !9, !noundef !3
  %10 = load i64, ptr getelementptr inbounds (i8, ptr @0, i64 8), align 8
  store i64 %9, ptr %_0, align 8
  %11 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %10, ptr %11, align 8
  br label %bb6

bb6:                                              ; preds = %bb3, %bb5
  %12 = load i64, ptr %_0, align 8, !range !9, !noundef !3
  %13 = getelementptr inbounds i8, ptr %_0, i64 8
  %14 = load i64, ptr %13, align 8
  %15 = insertvalue { i64, i64 } poison, i64 %12, 0
  %16 = insertvalue { i64, i64 } %15, i64 %14, 1
  ret { i64, i64 } %16
}

; core::alloc::layout::Layout::dangling
; Function Attrs: inlinehint nounwind
define internal noundef nonnull ptr @_ZN4core5alloc6layout6Layout8dangling17h52847c726b4e461dE(ptr noalias noundef readonly align 8 dereferenceable(16) %self) unnamed_addr #0 {
start:
  %_5 = alloca [8 x i8], align 8
  %_0 = alloca [8 x i8], align 8
  %self1 = load i64, ptr %self, align 8, !range !8, !noundef !3
  call void @llvm.lifetime.start.p0(i64 8, ptr %_5)
  store i64 %self1, ptr %_5, align 8
  %_6 = load i64, ptr %_5, align 8, !range !8, !noundef !3
  %_7 = icmp uge i64 %_6, 1
  %_8 = icmp ule i64 %_6, -9223372036854775808
  %_9 = and i1 %_7, %_8
  call void @llvm.assume(i1 %_9)
  call void @llvm.lifetime.end.p0(i64 8, ptr %_5)
  %ptr = getelementptr i8, ptr null, i64 %_6
  br label %bb3

bb3:                                              ; preds = %start
  store ptr %ptr, ptr %_0, align 8
  %0 = load ptr, ptr %_0, align 8, !nonnull !3, !noundef !3
  ret ptr %0

bb1:                                              ; No predecessors!
  unreachable

bb2:                                              ; No predecessors!
  unreachable
}

; core::array::<impl core::default::Default for [T; 32]>::default
; Function Attrs: nounwind
define internal void @"_ZN4core5array76_$LT$impl$u20$core..default..Default$u20$for$u20$$u5b$T$u3b$$u20$32$u5d$$GT$7default17hf39cfabd391f7201E"(ptr dead_on_unwind noalias nocapture noundef writable sret([32 x i8]) align 1 dereferenceable(32) %_0) unnamed_addr #1 {
start:
; call <u8 as core::default::Default>::default
  %_1 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_2 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_3 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_4 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_5 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_6 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_7 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_8 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_9 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_10 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_11 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_12 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_13 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_14 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_15 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_16 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_17 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_18 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_19 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_20 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_21 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_22 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_23 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_24 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_25 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_26 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_27 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_28 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_29 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_30 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_31 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
; call <u8 as core::default::Default>::default
  %_32 = call noundef i8 @"_ZN45_$LT$u8$u20$as$u20$core..default..Default$GT$7default17h46d27924e6bc26afE"() #22
  %0 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 0
  store i8 %_1, ptr %0, align 1
  %1 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 1
  store i8 %_2, ptr %1, align 1
  %2 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 2
  store i8 %_3, ptr %2, align 1
  %3 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 3
  store i8 %_4, ptr %3, align 1
  %4 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 4
  store i8 %_5, ptr %4, align 1
  %5 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 5
  store i8 %_6, ptr %5, align 1
  %6 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 6
  store i8 %_7, ptr %6, align 1
  %7 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 7
  store i8 %_8, ptr %7, align 1
  %8 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 8
  store i8 %_9, ptr %8, align 1
  %9 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 9
  store i8 %_10, ptr %9, align 1
  %10 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 10
  store i8 %_11, ptr %10, align 1
  %11 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 11
  store i8 %_12, ptr %11, align 1
  %12 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 12
  store i8 %_13, ptr %12, align 1
  %13 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 13
  store i8 %_14, ptr %13, align 1
  %14 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 14
  store i8 %_15, ptr %14, align 1
  %15 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 15
  store i8 %_16, ptr %15, align 1
  %16 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 16
  store i8 %_17, ptr %16, align 1
  %17 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 17
  store i8 %_18, ptr %17, align 1
  %18 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 18
  store i8 %_19, ptr %18, align 1
  %19 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 19
  store i8 %_20, ptr %19, align 1
  %20 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 20
  store i8 %_21, ptr %20, align 1
  %21 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 21
  store i8 %_22, ptr %21, align 1
  %22 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 22
  store i8 %_23, ptr %22, align 1
  %23 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 23
  store i8 %_24, ptr %23, align 1
  %24 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 24
  store i8 %_25, ptr %24, align 1
  %25 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 25
  store i8 %_26, ptr %25, align 1
  %26 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 26
  store i8 %_27, ptr %26, align 1
  %27 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 27
  store i8 %_28, ptr %27, align 1
  %28 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 28
  store i8 %_29, ptr %28, align 1
  %29 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 29
  store i8 %_30, ptr %29, align 1
  %30 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 30
  store i8 %_31, ptr %30, align 1
  %31 = getelementptr inbounds [32 x i8], ptr %_0, i64 0, i64 31
  store i8 %_32, ptr %31, align 1
  ret void
}

; core::slice::iter::Iter<T>::make_slice
; Function Attrs: alwaysinline nounwind
define internal { ptr, i64 } @"_ZN4core5slice4iter13Iter$LT$T$GT$10make_slice17h5ca6add12385cc71E"(ptr noalias noundef readonly align 8 dereferenceable(16) %self) unnamed_addr #2 {
start:
  %len = alloca [8 x i8], align 8
  %self1 = load ptr, ptr %self, align 8, !nonnull !3, !noundef !3
  call void @llvm.lifetime.start.p0(i64 8, ptr %len)
  br label %bb2

bb2:                                              ; preds = %start
  %self2 = getelementptr inbounds i8, ptr %self, i64 8
  %end = load ptr, ptr %self2, align 8, !nonnull !3, !noundef !3
; call core::ptr::const_ptr::<impl *const T>::sub_ptr
  %0 = call noundef i64 @"_ZN4core3ptr9const_ptr33_$LT$impl$u20$$BP$const$u20$T$GT$7sub_ptr17h26f56479ac07e811E"(ptr noundef %end, ptr noundef %self1) #22
  store i64 %0, ptr %len, align 8
  br label %bb3

bb3:                                              ; preds = %bb2
  br label %bb7

bb1:                                              ; No predecessors!
  unreachable

bb7:                                              ; preds = %bb3
  %_18.1 = load i64, ptr %len, align 8, !noundef !3
  call void @llvm.lifetime.end.p0(i64 8, ptr %len)
  %1 = insertvalue { ptr, i64 } poison, ptr %self1, 0
  %2 = insertvalue { ptr, i64 } %1, i64 %_18.1, 1
  ret { ptr, i64 } %2

bb5:                                              ; No predecessors!
  unreachable

bb6:                                              ; No predecessors!
  unreachable
}

; core::ub_checks::is_aligned_and_not_null
; Function Attrs: inlinehint nounwind
define internal noundef zeroext i1 @_ZN4core9ub_checks23is_aligned_and_not_null17hcabcf8abc95e5d7fE(ptr noundef %ptr, i64 noundef %align) unnamed_addr #0 {
start:
  %0 = alloca [4 x i8], align 4
  %_6 = alloca [48 x i8], align 8
  %_0 = alloca [1 x i8], align 1
  %_4 = ptrtoint ptr %ptr to i64
  %1 = icmp eq i64 %_4, 0
  br i1 %1, label %bb1, label %bb2

bb1:                                              ; preds = %start
  store i8 0, ptr %_0, align 1
  br label %bb3

bb2:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 4, ptr %0)
  %2 = call i64 @llvm.ctpop.i64(i64 %align)
  %3 = trunc i64 %2 to i32
  store i32 %3, ptr %0, align 4
  %_8 = load i32, ptr %0, align 4, !noundef !3
  call void @llvm.lifetime.end.p0(i64 4, ptr %0)
  %4 = icmp eq i32 %_8, 1
  br i1 %4, label %bb4, label %bb5

bb3:                                              ; preds = %bb4, %bb1
  %5 = load i8, ptr %_0, align 1, !range !4, !noundef !3
  %6 = trunc i8 %5 to i1
  ret i1 %6

bb4:                                              ; preds = %bb2
  %_12 = sub i64 %align, 1
  %_11 = and i64 %_4, %_12
  %7 = icmp eq i64 %_11, 0
  %8 = zext i1 %7 to i8
  store i8 %8, ptr %_0, align 1
  br label %bb3

bb5:                                              ; preds = %bb2
  call void @llvm.lifetime.start.p0(i64 48, ptr %_6)
  store ptr @alloc_041983ee8170efdaaf95ba67fd072d26, ptr %_6, align 8
  %9 = getelementptr inbounds i8, ptr %_6, i64 8
  store i64 1, ptr %9, align 8
  %10 = load ptr, ptr @0, align 8, !align !5, !noundef !3
  %11 = load i64, ptr getelementptr inbounds (i8, ptr @0, i64 8), align 8
  %12 = getelementptr inbounds i8, ptr %_6, i64 32
  store ptr %10, ptr %12, align 8
  %13 = getelementptr inbounds i8, ptr %12, i64 8
  store i64 %11, ptr %13, align 8
  %14 = getelementptr inbounds i8, ptr %_6, i64 16
  store ptr inttoptr (i64 8 to ptr), ptr %14, align 8
  %15 = getelementptr inbounds i8, ptr %14, i64 8
  store i64 0, ptr %15, align 8
; call core::panicking::panic_fmt
  call void @_ZN4core9panicking9panic_fmt17h0f7a5cdbeae7e874E(ptr noalias nocapture noundef readonly align 8 dereferenceable(48) %_6, ptr noalias noundef readonly align 8 dereferenceable(24) @alloc_310ca4c1a780778a2fe8d929c908356a) #21
  unreachable
}

; <core::fmt::Error as core::fmt::Debug>::fmt
; Function Attrs: inlinehint nounwind
define internal noundef zeroext i1 @"_ZN53_$LT$core..fmt..Error$u20$as$u20$core..fmt..Debug$GT$3fmt17h85666afa16c4890eE"(ptr noalias noundef nonnull readonly align 1 %self, ptr noalias noundef align 8 dereferenceable(64) %f) unnamed_addr #0 {
start:
; call core::fmt::Formatter::write_str
  %_0 = call noundef zeroext i1 @_ZN4core3fmt9Formatter9write_str17h97ca3d8b34e3baaaE(ptr noalias noundef align 8 dereferenceable(64) %f, ptr noalias noundef nonnull readonly align 1 @alloc_99ac8a81a24cac863217ce4a5cbfabea, i64 noundef 5) #22
  ret i1 %_0
}

; <alloc::string::String as core::fmt::Write>::write_char
; Function Attrs: inlinehint nounwind
define internal noundef zeroext i1 @"_ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$10write_char17hfde5b685689164ccE"(ptr noalias noundef align 8 dereferenceable(24) %self, i32 noundef %c) unnamed_addr #0 {
start:
; call alloc::string::String::push
  call void @_ZN5alloc6string6String4push17h96dfc48c19bd6e38E(ptr noalias noundef align 8 dereferenceable(24) %self, i32 noundef %c) #22
  ret i1 false
}

; <alloc::string::String as core::fmt::Write>::write_str
; Function Attrs: inlinehint nounwind
define internal noundef zeroext i1 @"_ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$9write_str17h4b62f46a222bd5b2E"(ptr noalias noundef align 8 dereferenceable(24) %self, ptr noalias noundef nonnull readonly align 1 %s.0, i64 noundef %s.1) unnamed_addr #0 {
start:
; call alloc::vec::Vec<T,A>::extend_from_slice
  call void @"_ZN5alloc3vec16Vec$LT$T$C$A$GT$17extend_from_slice17h9db90023fcfc2b1eE"(ptr noalias noundef align 8 dereferenceable(24) %self, ptr noalias noundef nonnull readonly align 1 %s.0, i64 noundef %s.1) #22
  ret i1 false
}

; alloc::rc::RcInnerPtr::inc_strong
; Function Attrs: inlinehint nounwind
define internal void @_ZN5alloc2rc10RcInnerPtr10inc_strong17h18d97276b6a6692fE(ptr noundef nonnull align 8 %self) unnamed_addr #0 {
start:
  %0 = alloca [1 x i8], align 1
; call alloc::rc::RcInnerPtr::strong
  %strong = call noundef i64 @_ZN5alloc2rc10RcInnerPtr6strong17h24e8e3c5470a456aE(ptr noundef nonnull align 8 %self) #22
  %cond = icmp ne i64 %strong, 0
  br label %bb7

bb7:                                              ; preds = %start
  call void @llvm.assume(i1 %cond)
  %strong1 = add i64 %strong, 1
; call <alloc::rc::RcBox<T> as alloc::rc::RcInnerPtr>::strong_ref
  %self2 = call noundef nonnull align 8 ptr @"_ZN67_$LT$alloc..rc..RcBox$LT$T$GT$$u20$as$u20$alloc..rc..RcInnerPtr$GT$10strong_ref17h82e62e0b81e90042E"(ptr noundef nonnull align 8 %self) #22
  %result = load i64, ptr %self2, align 8, !noundef !3
  store i64 %strong1, ptr %self2, align 8
  %_7 = icmp eq i64 %strong1, 0
  call void @llvm.lifetime.start.p0(i64 1, ptr %0)
  %1 = call i1 @llvm.expect.i1(i1 %_7, i1 false)
  %2 = zext i1 %1 to i8
  store i8 %2, ptr %0, align 1
  %3 = load i8, ptr %0, align 1, !range !4, !noundef !3
  %_6 = trunc i8 %3 to i1
  call void @llvm.lifetime.end.p0(i64 1, ptr %0)
  br i1 %_6, label %bb4, label %bb5

bb6:                                              ; No predecessors!
  unreachable

bb5:                                              ; preds = %bb7
  ret void

bb4:                                              ; preds = %bb7
  call void @llvm.trap()
  unreachable
}

; alloc::rc::RcInnerPtr::inc_strong
; Function Attrs: inlinehint nounwind
define internal void @_ZN5alloc2rc10RcInnerPtr10inc_strong17h3d0774391efcf2ceE(ptr noundef nonnull align 8 %self) unnamed_addr #0 {
start:
  %0 = alloca [1 x i8], align 1
; call alloc::rc::RcInnerPtr::strong
  %strong = call noundef i64 @_ZN5alloc2rc10RcInnerPtr6strong17hf9beec26a82ddfc5E(ptr noundef nonnull align 8 %self) #22
  %cond = icmp ne i64 %strong, 0
  br label %bb7

bb7:                                              ; preds = %start
  call void @llvm.assume(i1 %cond)
  %strong1 = add i64 %strong, 1
; call <alloc::rc::RcBox<T> as alloc::rc::RcInnerPtr>::strong_ref
  %self2 = call noundef nonnull align 8 ptr @"_ZN67_$LT$alloc..rc..RcBox$LT$T$GT$$u20$as$u20$alloc..rc..RcInnerPtr$GT$10strong_ref17hce387b9138991019E"(ptr noundef nonnull align 8 %self) #22
  %result = load i64, ptr %self2, align 8, !noundef !3
  store i64 %strong1, ptr %self2, align 8
  %_7 = icmp eq i64 %strong1, 0
  call void @llvm.lifetime.start.p0(i64 1, ptr %0)
  %1 = call i1 @llvm.expect.i1(i1 %_7, i1 false)
  %2 = zext i1 %1 to i8
  store i8 %2, ptr %0, align 1
  %3 = load i8, ptr %0, align 1, !range !4, !noundef !3
  %_6 = trunc i8 %3 to i1
  call void @llvm.lifetime.end.p0(i64 1, ptr %0)
  br i1 %_6, label %bb4, label %bb5

bb6:                                              ; No predecessors!
  unreachable

bb5:                                              ; preds = %bb7
  ret void

bb4:                                              ; preds = %bb7
  call void @llvm.trap()
  unreachable
}

; alloc::rc::RcInnerPtr::strong
; Function Attrs: inlinehint nounwind
define internal noundef i64 @_ZN5alloc2rc10RcInnerPtr6strong17h24e8e3c5470a456aE(ptr noundef nonnull align 8 %self) unnamed_addr #0 {
start:
; call <alloc::rc::RcBox<T> as alloc::rc::RcInnerPtr>::strong_ref
  %self1 = call noundef nonnull align 8 ptr @"_ZN67_$LT$alloc..rc..RcBox$LT$T$GT$$u20$as$u20$alloc..rc..RcInnerPtr$GT$10strong_ref17h82e62e0b81e90042E"(ptr noundef nonnull align 8 %self) #22
  %_0 = load i64, ptr %self1, align 8, !noundef !3
  ret i64 %_0
}

; alloc::rc::RcInnerPtr::strong
; Function Attrs: inlinehint nounwind
define internal noundef i64 @_ZN5alloc2rc10RcInnerPtr6strong17hf9beec26a82ddfc5E(ptr noundef nonnull align 8 %self) unnamed_addr #0 {
start:
; call <alloc::rc::RcBox<T> as alloc::rc::RcInnerPtr>::strong_ref
  %self1 = call noundef nonnull align 8 ptr @"_ZN67_$LT$alloc..rc..RcBox$LT$T$GT$$u20$as$u20$alloc..rc..RcInnerPtr$GT$10strong_ref17hce387b9138991019E"(ptr noundef nonnull align 8 %self) #22
  %_0 = load i64, ptr %self1, align 8, !noundef !3
  ret i64 %_0
}

; alloc::vec::Vec<T,A>::append_elements
; Function Attrs: inlinehint nounwind
define internal void @"_ZN5alloc3vec16Vec$LT$T$C$A$GT$15append_elements17hcb02820fa3a5db71E"(ptr noalias noundef align 8 dereferenceable(24) %self, ptr noundef %other.0, i64 noundef %other.1) unnamed_addr #0 {
start:
; call alloc::vec::Vec<T,A>::reserve
  call void @"_ZN5alloc3vec16Vec$LT$T$C$A$GT$7reserve17hccdbefae89c3a2f3E"(ptr noalias noundef align 8 dereferenceable(24) %self, i64 noundef %other.1) #22
  %0 = getelementptr inbounds i8, ptr %self, i64 16
  %len = load i64, ptr %0, align 8, !noundef !3
  %1 = getelementptr inbounds i8, ptr %self, i64 8
  %self1 = load ptr, ptr %1, align 8, !nonnull !3, !noundef !3
  %dst = getelementptr inbounds i8, ptr %self1, i64 %len
  br label %bb4

bb4:                                              ; preds = %start
  %2 = mul i64 %other.1, 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %dst, ptr align 1 %other.0, i64 %2, i1 false)
  %3 = getelementptr inbounds i8, ptr %self, i64 16
  %4 = getelementptr inbounds i8, ptr %self, i64 16
  %5 = load i64, ptr %4, align 8, !noundef !3
  %6 = add i64 %5, %other.1
  store i64 %6, ptr %3, align 8
  ret void

bb2:                                              ; No predecessors!
  unreachable

bb3:                                              ; No predecessors!
  unreachable
}

; alloc::vec::Vec<T,A>::extend_from_slice
; Function Attrs: nounwind
define internal void @"_ZN5alloc3vec16Vec$LT$T$C$A$GT$17extend_from_slice17h9db90023fcfc2b1eE"(ptr noalias noundef align 8 dereferenceable(24) %self, ptr noalias noundef nonnull readonly align 1 %other.0, i64 noundef %other.1) unnamed_addr #1 {
start:
  %end_or_len = alloca [8 x i8], align 8
  %self1 = alloca [16 x i8], align 8
  %ptr = alloca [8 x i8], align 8
  %_3 = alloca [16 x i8], align 8
  call void @llvm.lifetime.start.p0(i64 16, ptr %_3)
  call void @llvm.lifetime.start.p0(i64 8, ptr %ptr)
  call void @llvm.lifetime.start.p0(i64 16, ptr %self1)
  store ptr %other.0, ptr %self1, align 8
  %0 = getelementptr inbounds i8, ptr %self1, i64 8
  store i64 %other.1, ptr %0, align 8
  store ptr %other.0, ptr %ptr, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %self1)
  call void @llvm.lifetime.start.p0(i64 8, ptr %end_or_len)
  br label %bb3

bb3:                                              ; preds = %start
  %_9 = getelementptr inbounds i8, ptr %other.0, i64 %other.1
  store ptr %_9, ptr %end_or_len, align 8
  br label %bb4

bb4:                                              ; preds = %bb3
  %_11 = load ptr, ptr %end_or_len, align 8, !noundef !3
  %1 = load ptr, ptr %ptr, align 8, !nonnull !3, !noundef !3
  store ptr %1, ptr %_3, align 8
  %2 = getelementptr inbounds i8, ptr %_3, i64 8
  store ptr %_11, ptr %2, align 8
  call void @llvm.lifetime.end.p0(i64 8, ptr %end_or_len)
  call void @llvm.lifetime.end.p0(i64 8, ptr %ptr)
  %3 = load ptr, ptr %_3, align 8, !nonnull !3, !noundef !3
  %4 = getelementptr inbounds i8, ptr %_3, i64 8
  %5 = load ptr, ptr %4, align 8, !noundef !3
; call <alloc::vec::Vec<T,A> as alloc::vec::spec_extend::SpecExtend<&T,core::slice::iter::Iter<T>>>::spec_extend
  call void @"_ZN132_$LT$alloc..vec..Vec$LT$T$C$A$GT$$u20$as$u20$alloc..vec..spec_extend..SpecExtend$LT$$RF$T$C$core..slice..iter..Iter$LT$T$GT$$GT$$GT$11spec_extend17h97a0acb7d1db89dfE"(ptr noalias noundef align 8 dereferenceable(24) %self, ptr noundef nonnull %3, ptr noundef %5) #22
  call void @llvm.lifetime.end.p0(i64 16, ptr %_3)
  ret void

bb2:                                              ; No predecessors!
  unreachable
}

; alloc::vec::Vec<T,A>::push
; Function Attrs: inlinehint nounwind
define internal void @"_ZN5alloc3vec16Vec$LT$T$C$A$GT$4push17h3eecfd24bc944e21E"(ptr noalias noundef align 8 dereferenceable(24) %self, i8 noundef %value) unnamed_addr #0 {
start:
  %_5 = alloca [8 x i8], align 8
  %0 = getelementptr inbounds i8, ptr %self, i64 16
  %len = load i64, ptr %0, align 8, !noundef !3
  call void @llvm.lifetime.start.p0(i64 8, ptr %_5)
  br label %bb6

bb6:                                              ; preds = %start
  %1 = load i64, ptr %self, align 8, !noundef !3
  store i64 %1, ptr %_5, align 8
  br label %bb7

bb7:                                              ; preds = %bb6
  %2 = load i64, ptr %_5, align 8, !noundef !3
  %_4 = icmp eq i64 %len, %2
  br i1 %_4, label %bb1, label %bb3

bb5:                                              ; No predecessors!
  unreachable

bb3:                                              ; preds = %bb7
  call void @llvm.lifetime.end.p0(i64 8, ptr %_5)
  br label %bb4

bb1:                                              ; preds = %bb7
  call void @llvm.lifetime.end.p0(i64 8, ptr %_5)
; call alloc::raw_vec::RawVec<T,A>::grow_one
  call void @"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$8grow_one17h4b15183664487c30E"(ptr noalias noundef align 8 dereferenceable(16) %self) #22
  br label %bb4

bb4:                                              ; preds = %bb1, %bb3
  %3 = getelementptr inbounds i8, ptr %self, i64 8
  %self1 = load ptr, ptr %3, align 8, !nonnull !3, !noundef !3
  %end = getelementptr inbounds i8, ptr %self1, i64 %len
  store i8 %value, ptr %end, align 1
  %4 = getelementptr inbounds i8, ptr %self, i64 16
  %5 = add i64 %len, 1
  store i64 %5, ptr %4, align 8
  ret void
}

; alloc::vec::Vec<T,A>::reserve
; Function Attrs: nounwind
define internal void @"_ZN5alloc3vec16Vec$LT$T$C$A$GT$7reserve17hccdbefae89c3a2f3E"(ptr noalias noundef align 8 dereferenceable(24) %self, i64 noundef %additional) unnamed_addr #1 {
start:
  %self1 = alloca [8 x i8], align 8
  %0 = getelementptr inbounds i8, ptr %self, i64 16
  %len = load i64, ptr %0, align 8, !noundef !3
  call void @llvm.lifetime.start.p0(i64 8, ptr %self1)
  br label %bb4

bb4:                                              ; preds = %start
  %1 = load i64, ptr %self, align 8, !noundef !3
  store i64 %1, ptr %self1, align 8
  br label %bb5

bb5:                                              ; preds = %bb4
  %2 = load i64, ptr %self1, align 8, !noundef !3
  %_7 = sub i64 %2, %len
  call void @llvm.lifetime.end.p0(i64 8, ptr %self1)
  %_5 = icmp ugt i64 %additional, %_7
  br i1 %_5, label %bb1, label %bb2

bb3:                                              ; No predecessors!
  unreachable

bb2:                                              ; preds = %bb1, %bb5
  ret void

bb1:                                              ; preds = %bb5
; call alloc::raw_vec::RawVec<T,A>::reserve::do_reserve_and_handle
  call void @"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$7reserve21do_reserve_and_handle17h841f8186853dc167E"(ptr noalias noundef align 8 dereferenceable(16) %self, i64 noundef %len, i64 noundef %additional) #22
  br label %bb2
}

; alloc::alloc::Global::alloc_impl
; Function Attrs: inlinehint nounwind
define internal { ptr, i64 } @_ZN5alloc5alloc6Global10alloc_impl17hcabadc4f9dbcac44E(ptr noalias noundef nonnull readonly align 1 %self, i64 noundef %0, i64 noundef %1, i1 noundef zeroext %zeroed) unnamed_addr #0 {
start:
  %_47 = alloca [8 x i8], align 8
  %_42 = alloca [8 x i8], align 8
  %_32 = alloca [8 x i8], align 8
  %_17 = alloca [16 x i8], align 8
  %self4 = alloca [8 x i8], align 8
  %self3 = alloca [8 x i8], align 8
  %_12 = alloca [8 x i8], align 8
  %layout2 = alloca [16 x i8], align 8
  %layout1 = alloca [16 x i8], align 8
  %raw_ptr = alloca [8 x i8], align 8
  %_6 = alloca [16 x i8], align 8
  %_0 = alloca [16 x i8], align 8
  %layout = alloca [16 x i8], align 8
  store i64 %0, ptr %layout, align 8
  %2 = getelementptr inbounds i8, ptr %layout, i64 8
  store i64 %1, ptr %2, align 8
  %3 = getelementptr inbounds i8, ptr %layout, i64 8
  %size = load i64, ptr %3, align 8, !noundef !3
  %4 = icmp eq i64 %size, 0
  br i1 %4, label %bb2, label %bb1

bb2:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 16, ptr %_6)
; call core::alloc::layout::Layout::dangling
  %data = call noundef nonnull ptr @_ZN4core5alloc6layout6Layout8dangling17h52847c726b4e461dE(ptr noalias noundef readonly align 8 dereferenceable(16) %layout) #22
  br label %bb10

bb1:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 8, ptr %raw_ptr)
  br i1 %zeroed, label %bb4, label %bb5

bb10:                                             ; preds = %bb2
  store ptr %data, ptr %_6, align 8
  %5 = getelementptr inbounds i8, ptr %_6, i64 8
  store i64 0, ptr %5, align 8
  %6 = load ptr, ptr %_6, align 8, !nonnull !3, !noundef !3
  %7 = getelementptr inbounds i8, ptr %_6, i64 8
  %8 = load i64, ptr %7, align 8, !noundef !3
  store ptr %6, ptr %_0, align 8
  %9 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %8, ptr %9, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %_6)
  br label %bb7

bb8:                                              ; No predecessors!
  unreachable

bb9:                                              ; No predecessors!
  unreachable

bb7:                                              ; preds = %bb19, %bb13, %bb10
  %10 = load ptr, ptr %_0, align 8, !noundef !3
  %11 = getelementptr inbounds i8, ptr %_0, i64 8
  %12 = load i64, ptr %11, align 8
  %13 = insertvalue { ptr, i64 } poison, ptr %10, 0
  %14 = insertvalue { ptr, i64 } %13, i64 %12, 1
  ret { ptr, i64 } %14

bb5:                                              ; preds = %bb1
  call void @llvm.lifetime.start.p0(i64 16, ptr %layout2)
  %15 = load i64, ptr %layout, align 8, !range !8, !noundef !3
  %16 = getelementptr inbounds i8, ptr %layout, i64 8
  %17 = load i64, ptr %16, align 8, !noundef !3
  store i64 %15, ptr %layout2, align 8
  %18 = getelementptr inbounds i8, ptr %layout2, i64 8
  store i64 %17, ptr %18, align 8
  %19 = getelementptr inbounds i8, ptr %layout2, i64 8
  %_37 = load i64, ptr %19, align 8, !noundef !3
  %self5 = load i64, ptr %layout2, align 8, !range !8, !noundef !3
  call void @llvm.lifetime.start.p0(i64 8, ptr %_42)
  store i64 %self5, ptr %_42, align 8
  %_43 = load i64, ptr %_42, align 8, !range !8, !noundef !3
  %_44 = icmp uge i64 %_43, 1
  %_45 = icmp ule i64 %_43, -9223372036854775808
  %_46 = and i1 %_44, %_45
  call void @llvm.assume(i1 %_46)
  call void @llvm.lifetime.end.p0(i64 8, ptr %_42)
  %20 = call noundef ptr @__rust_alloc(i64 noundef %_37, i64 noundef %_43) #22
  store ptr %20, ptr %raw_ptr, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %layout2)
  br label %bb6

bb4:                                              ; preds = %bb1
  call void @llvm.lifetime.start.p0(i64 16, ptr %layout1)
  %21 = load i64, ptr %layout, align 8, !range !8, !noundef !3
  %22 = getelementptr inbounds i8, ptr %layout, i64 8
  %23 = load i64, ptr %22, align 8, !noundef !3
  store i64 %21, ptr %layout1, align 8
  %24 = getelementptr inbounds i8, ptr %layout1, i64 8
  store i64 %23, ptr %24, align 8
  %25 = getelementptr inbounds i8, ptr %layout1, i64 8
  %_27 = load i64, ptr %25, align 8, !noundef !3
  %self6 = load i64, ptr %layout1, align 8, !range !8, !noundef !3
  call void @llvm.lifetime.start.p0(i64 8, ptr %_32)
  store i64 %self6, ptr %_32, align 8
  %_33 = load i64, ptr %_32, align 8, !range !8, !noundef !3
  %_34 = icmp uge i64 %_33, 1
  %_35 = icmp ule i64 %_33, -9223372036854775808
  %_36 = and i1 %_34, %_35
  call void @llvm.assume(i1 %_36)
  call void @llvm.lifetime.end.p0(i64 8, ptr %_32)
  %26 = call noundef ptr @__rust_alloc_zeroed(i64 noundef %_27, i64 noundef %_33) #22
  store ptr %26, ptr %raw_ptr, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %layout1)
  br label %bb6

bb6:                                              ; preds = %bb4, %bb5
  call void @llvm.lifetime.start.p0(i64 8, ptr %_12)
  call void @llvm.lifetime.start.p0(i64 8, ptr %self3)
  call void @llvm.lifetime.start.p0(i64 8, ptr %self4)
  %ptr = load ptr, ptr %raw_ptr, align 8, !noundef !3
  %_48 = ptrtoint ptr %ptr to i64
  %27 = icmp eq i64 %_48, 0
  br i1 %27, label %bb13, label %bb14

bb13:                                             ; preds = %bb6
  store ptr null, ptr %self4, align 8
  store ptr null, ptr %self3, align 8
  call void @llvm.lifetime.end.p0(i64 8, ptr %self4)
  call void @llvm.lifetime.end.p0(i64 8, ptr %self3)
  %28 = load ptr, ptr @0, align 8, !noundef !3
  %29 = load i64, ptr getelementptr inbounds (i8, ptr @0, i64 8), align 8
  store ptr %28, ptr %_0, align 8
  %30 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %29, ptr %30, align 8
  call void @llvm.lifetime.end.p0(i64 8, ptr %_12)
  call void @llvm.lifetime.end.p0(i64 8, ptr %raw_ptr)
  br label %bb7

bb14:                                             ; preds = %bb6
  call void @llvm.lifetime.start.p0(i64 8, ptr %_47)
  br label %bb16

bb16:                                             ; preds = %bb14
  store ptr %ptr, ptr %_47, align 8
  %31 = load ptr, ptr %_47, align 8, !nonnull !3, !noundef !3
  store ptr %31, ptr %self4, align 8
  call void @llvm.lifetime.end.p0(i64 8, ptr %_47)
  %v = load ptr, ptr %self4, align 8, !nonnull !3, !noundef !3
  store ptr %v, ptr %self3, align 8
  call void @llvm.lifetime.end.p0(i64 8, ptr %self4)
  %v7 = load ptr, ptr %self3, align 8, !nonnull !3, !noundef !3
  store ptr %v7, ptr %_12, align 8
  call void @llvm.lifetime.end.p0(i64 8, ptr %self3)
  %ptr8 = load ptr, ptr %_12, align 8, !nonnull !3, !noundef !3
  call void @llvm.lifetime.end.p0(i64 8, ptr %_12)
  call void @llvm.lifetime.start.p0(i64 16, ptr %_17)
  br label %bb19

bb15:                                             ; No predecessors!
  unreachable

bb19:                                             ; preds = %bb16
  store ptr %ptr8, ptr %_17, align 8
  %32 = getelementptr inbounds i8, ptr %_17, i64 8
  store i64 %size, ptr %32, align 8
  %33 = load ptr, ptr %_17, align 8, !nonnull !3, !noundef !3
  %34 = getelementptr inbounds i8, ptr %_17, i64 8
  %35 = load i64, ptr %34, align 8, !noundef !3
  store ptr %33, ptr %_0, align 8
  %36 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %35, ptr %36, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %_17)
  call void @llvm.lifetime.end.p0(i64 8, ptr %raw_ptr)
  br label %bb7

bb17:                                             ; No predecessors!
  unreachable

bb18:                                             ; No predecessors!
  unreachable
}

; alloc::alloc::Global::grow_impl
; Function Attrs: inlinehint nounwind
define internal { ptr, i64 } @_ZN5alloc5alloc6Global9grow_impl17h902bcec4ef6d3724E(ptr noalias noundef nonnull readonly align 1 %self, ptr noundef nonnull %ptr, i64 noundef %0, i64 noundef %1, i64 noundef %2, i64 noundef %3, i1 noundef zeroext %zeroed) unnamed_addr #0 {
start:
  %self6 = alloca [8 x i8], align 8
  %data_pointer = alloca [8 x i8], align 8
  %_81 = alloca [8 x i8], align 8
  %data5 = alloca [8 x i8], align 8
  %ptr4 = alloca [16 x i8], align 8
  %_70 = alloca [8 x i8], align 8
  %_65 = alloca [8 x i8], align 8
  %_52 = alloca [8 x i8], align 8
  %_46 = alloca [8 x i8], align 8
  %self3 = alloca [16 x i8], align 8
  %_38 = alloca [16 x i8], align 8
  %len = alloca [8 x i8], align 8
  %data = alloca [8 x i8], align 8
  %_34 = alloca [16 x i8], align 8
  %self2 = alloca [8 x i8], align 8
  %self1 = alloca [8 x i8], align 8
  %_27 = alloca [8 x i8], align 8
  %layout = alloca [16 x i8], align 8
  %_9 = alloca [8 x i8], align 8
  %_0 = alloca [16 x i8], align 8
  %new_layout = alloca [16 x i8], align 8
  %old_layout = alloca [16 x i8], align 8
  store i64 %0, ptr %old_layout, align 8
  %4 = getelementptr inbounds i8, ptr %old_layout, i64 8
  store i64 %1, ptr %4, align 8
  store i64 %2, ptr %new_layout, align 8
  %5 = getelementptr inbounds i8, ptr %new_layout, i64 8
  store i64 %3, ptr %5, align 8
  call void @llvm.lifetime.start.p0(i64 8, ptr %_9)
  %6 = getelementptr inbounds i8, ptr %old_layout, i64 8
  %7 = load i64, ptr %6, align 8, !noundef !3
  store i64 %7, ptr %_9, align 8
  %8 = load i64, ptr %_9, align 8, !noundef !3
  %9 = icmp eq i64 %8, 0
  br i1 %9, label %bb1, label %bb3

bb1:                                              ; preds = %start
  %_11.0 = load i64, ptr %new_layout, align 8, !range !8, !noundef !3
  %10 = getelementptr inbounds i8, ptr %new_layout, i64 8
  %_11.1 = load i64, ptr %10, align 8, !noundef !3
; call alloc::alloc::Global::alloc_impl
  %11 = call { ptr, i64 } @_ZN5alloc5alloc6Global10alloc_impl17hcabadc4f9dbcac44E(ptr noalias noundef nonnull readonly align 1 %self, i64 noundef %_11.0, i64 noundef %_11.1, i1 noundef zeroext %zeroed) #22
  %12 = extractvalue { ptr, i64 } %11, 0
  %13 = extractvalue { ptr, i64 } %11, 1
  store ptr %12, ptr %_0, align 8
  %14 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %13, ptr %14, align 8
  br label %bb11

bb3:                                              ; preds = %start
  %self7 = load i64, ptr %old_layout, align 8, !range !8, !noundef !3
  call void @llvm.lifetime.start.p0(i64 8, ptr %_46)
  store i64 %self7, ptr %_46, align 8
  %_47 = load i64, ptr %_46, align 8, !range !8, !noundef !3
  %_48 = icmp uge i64 %_47, 1
  %_49 = icmp ule i64 %_47, -9223372036854775808
  %_50 = and i1 %_48, %_49
  call void @llvm.assume(i1 %_50)
  call void @llvm.lifetime.end.p0(i64 8, ptr %_46)
  %self8 = load i64, ptr %new_layout, align 8, !range !8, !noundef !3
  call void @llvm.lifetime.start.p0(i64 8, ptr %_52)
  store i64 %self8, ptr %_52, align 8
  %_53 = load i64, ptr %_52, align 8, !range !8, !noundef !3
  %_54 = icmp uge i64 %_53, 1
  %_55 = icmp ule i64 %_53, -9223372036854775808
  %_56 = and i1 %_54, %_55
  call void @llvm.assume(i1 %_56)
  call void @llvm.lifetime.end.p0(i64 8, ptr %_52)
  %_14 = icmp eq i64 %_47, %_53
  br i1 %_14, label %bb4, label %bb5

bb11:                                             ; preds = %bb27, %bb32, %bb1
  call void @llvm.lifetime.end.p0(i64 8, ptr %_9)
  br label %bb13

bb5:                                              ; preds = %bb3
  %old_size = load i64, ptr %_9, align 8, !noundef !3
  call void @llvm.lifetime.start.p0(i64 16, ptr %_38)
  call void @llvm.lifetime.start.p0(i64 16, ptr %self3)
  %_40.0 = load i64, ptr %new_layout, align 8, !range !8, !noundef !3
  %15 = getelementptr inbounds i8, ptr %new_layout, i64 8
  %_40.1 = load i64, ptr %15, align 8, !noundef !3
; call alloc::alloc::Global::alloc_impl
  %16 = call { ptr, i64 } @_ZN5alloc5alloc6Global10alloc_impl17hcabadc4f9dbcac44E(ptr noalias noundef nonnull readonly align 1 %self, i64 noundef %_40.0, i64 noundef %_40.1, i1 noundef zeroext %zeroed) #22
  %17 = extractvalue { ptr, i64 } %16, 0
  %18 = extractvalue { ptr, i64 } %16, 1
  store ptr %17, ptr %self3, align 8
  %19 = getelementptr inbounds i8, ptr %self3, i64 8
  store i64 %18, ptr %19, align 8
  %20 = load ptr, ptr %self3, align 8, !noundef !3
  %21 = ptrtoint ptr %20 to i64
  %22 = icmp eq i64 %21, 0
  %_86 = select i1 %22, i64 1, i64 0
  switch i64 %_86, label %bb6 [
    i64 0, label %bb29
    i64 1, label %bb28
  ]

bb4:                                              ; preds = %bb3
  %old_size9 = load i64, ptr %_9, align 8, !noundef !3
  %23 = getelementptr inbounds i8, ptr %new_layout, i64 8
  %new_size = load i64, ptr %23, align 8, !noundef !3
  %24 = getelementptr inbounds i8, ptr %old_layout, i64 8
  %_22 = load i64, ptr %24, align 8, !noundef !3
  %cond = icmp uge i64 %new_size, %_22
  br label %bb15

bb6:                                              ; preds = %bb5
  unreachable

bb29:                                             ; preds = %bb5
  %v.0 = load ptr, ptr %self3, align 8, !nonnull !3, !noundef !3
  %25 = getelementptr inbounds i8, ptr %self3, i64 8
  %v.1 = load i64, ptr %25, align 8, !noundef !3
  store ptr %v.0, ptr %_38, align 8
  %26 = getelementptr inbounds i8, ptr %_38, i64 8
  store i64 %v.1, ptr %26, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %self3)
  %new_ptr.0 = load ptr, ptr %_38, align 8, !nonnull !3, !noundef !3
  %27 = getelementptr inbounds i8, ptr %_38, i64 8
  %new_ptr.1 = load i64, ptr %27, align 8, !noundef !3
  call void @llvm.lifetime.end.p0(i64 16, ptr %_38)
  call void @llvm.lifetime.start.p0(i64 8, ptr %self6)
  store ptr %new_ptr.0, ptr %self6, align 8
  call void @llvm.lifetime.end.p0(i64 8, ptr %self6)
  br label %bb32

bb28:                                             ; preds = %bb5
  call void @llvm.lifetime.end.p0(i64 16, ptr %self3)
  %28 = load ptr, ptr @0, align 8, !noundef !3
  %29 = load i64, ptr getelementptr inbounds (i8, ptr @0, i64 8), align 8
  store ptr %28, ptr %_0, align 8
  %30 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %29, ptr %30, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %_38)
  br label %bb12

bb32:                                             ; preds = %bb29
  %31 = mul i64 %old_size, 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %new_ptr.0, ptr align 1 %ptr, i64 %31, i1 false)
  %_44.0 = load i64, ptr %old_layout, align 8, !range !8, !noundef !3
  %32 = getelementptr inbounds i8, ptr %old_layout, i64 8
  %_44.1 = load i64, ptr %32, align 8, !noundef !3
; call <alloc::alloc::Global as core::alloc::Allocator>::deallocate
  call void @"_ZN63_$LT$alloc..alloc..Global$u20$as$u20$core..alloc..Allocator$GT$10deallocate17h6b30618160528bb2E"(ptr noalias noundef nonnull readonly align 1 %self, ptr noundef nonnull %ptr, i64 noundef %_44.0, i64 noundef %_44.1) #22
  store ptr %new_ptr.0, ptr %_0, align 8
  %33 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %new_ptr.1, ptr %33, align 8
  br label %bb11

bb30:                                             ; No predecessors!
  unreachable

bb31:                                             ; No predecessors!
  unreachable

bb12:                                             ; preds = %bb17, %bb28
  call void @llvm.lifetime.end.p0(i64 8, ptr %_9)
  br label %bb13

bb15:                                             ; preds = %bb4
  call void @llvm.assume(i1 %cond)
  call void @llvm.lifetime.start.p0(i64 16, ptr %layout)
  %34 = load i64, ptr %old_layout, align 8, !range !8, !noundef !3
  %35 = getelementptr inbounds i8, ptr %old_layout, i64 8
  %36 = load i64, ptr %35, align 8, !noundef !3
  store i64 %34, ptr %layout, align 8
  %37 = getelementptr inbounds i8, ptr %layout, i64 8
  store i64 %36, ptr %37, align 8
  %38 = getelementptr inbounds i8, ptr %layout, i64 8
  %_60 = load i64, ptr %38, align 8, !noundef !3
  %self10 = load i64, ptr %layout, align 8, !range !8, !noundef !3
  call void @llvm.lifetime.start.p0(i64 8, ptr %_65)
  store i64 %self10, ptr %_65, align 8
  %_66 = load i64, ptr %_65, align 8, !range !8, !noundef !3
  %_67 = icmp uge i64 %_66, 1
  %_68 = icmp ule i64 %_66, -9223372036854775808
  %_69 = and i1 %_67, %_68
  call void @llvm.assume(i1 %_69)
  call void @llvm.lifetime.end.p0(i64 8, ptr %_65)
  %raw_ptr = call noundef ptr @__rust_realloc(ptr noundef %ptr, i64 noundef %_60, i64 noundef %_66, i64 noundef %new_size) #22
  call void @llvm.lifetime.end.p0(i64 16, ptr %layout)
  call void @llvm.lifetime.start.p0(i64 8, ptr %_27)
  call void @llvm.lifetime.start.p0(i64 8, ptr %self1)
  call void @llvm.lifetime.start.p0(i64 8, ptr %self2)
  %_71 = ptrtoint ptr %raw_ptr to i64
  %39 = icmp eq i64 %_71, 0
  br i1 %39, label %bb17, label %bb18

bb14:                                             ; No predecessors!
  unreachable

bb17:                                             ; preds = %bb15
  store ptr null, ptr %self2, align 8
  store ptr null, ptr %self1, align 8
  call void @llvm.lifetime.end.p0(i64 8, ptr %self2)
  call void @llvm.lifetime.end.p0(i64 8, ptr %self1)
  %40 = load ptr, ptr @0, align 8, !noundef !3
  %41 = load i64, ptr getelementptr inbounds (i8, ptr @0, i64 8), align 8
  store ptr %40, ptr %_0, align 8
  %42 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %41, ptr %42, align 8
  call void @llvm.lifetime.end.p0(i64 8, ptr %_27)
  br label %bb12

bb18:                                             ; preds = %bb15
  call void @llvm.lifetime.start.p0(i64 8, ptr %_70)
  br label %bb20

bb13:                                             ; preds = %bb11, %bb12
  %43 = load ptr, ptr %_0, align 8, !noundef !3
  %44 = getelementptr inbounds i8, ptr %_0, i64 8
  %45 = load i64, ptr %44, align 8
  %46 = insertvalue { ptr, i64 } poison, ptr %43, 0
  %47 = insertvalue { ptr, i64 } %46, i64 %45, 1
  ret { ptr, i64 } %47

bb20:                                             ; preds = %bb19, %bb18
  store ptr %raw_ptr, ptr %_70, align 8
  %48 = load ptr, ptr %_70, align 8, !nonnull !3, !noundef !3
  store ptr %48, ptr %self2, align 8
  call void @llvm.lifetime.end.p0(i64 8, ptr %_70)
  %v = load ptr, ptr %self2, align 8, !nonnull !3, !noundef !3
  store ptr %v, ptr %self1, align 8
  call void @llvm.lifetime.end.p0(i64 8, ptr %self2)
  %v11 = load ptr, ptr %self1, align 8, !nonnull !3, !noundef !3
  store ptr %v11, ptr %_27, align 8
  call void @llvm.lifetime.end.p0(i64 8, ptr %self1)
  %ptr12 = load ptr, ptr %_27, align 8, !nonnull !3, !noundef !3
  call void @llvm.lifetime.end.p0(i64 8, ptr %_27)
  br i1 %zeroed, label %bb7, label %bb8

bb19:                                             ; No predecessors!
; call core::ptr::non_null::NonNull<T>::new_unchecked::precondition_check
  call void @"_ZN4core3ptr8non_null16NonNull$LT$T$GT$13new_unchecked18precondition_check17hdc271a756f76605cE"(ptr noundef %raw_ptr) #22
  br label %bb20

bb8:                                              ; preds = %bb24, %bb20
  call void @llvm.lifetime.start.p0(i64 16, ptr %_34)
  call void @llvm.lifetime.start.p0(i64 8, ptr %data)
  store ptr %ptr12, ptr %data, align 8
  call void @llvm.lifetime.start.p0(i64 8, ptr %len)
  store i64 %new_size, ptr %len, align 8
  call void @llvm.lifetime.start.p0(i64 8, ptr %_81)
  call void @llvm.lifetime.start.p0(i64 16, ptr %ptr4)
  call void @llvm.lifetime.start.p0(i64 8, ptr %data5)
  store ptr %ptr12, ptr %_81, align 8
  %49 = load ptr, ptr %_81, align 8, !noundef !3
  store ptr %49, ptr %data5, align 8
  call void @llvm.lifetime.start.p0(i64 8, ptr %data_pointer)
  %50 = load ptr, ptr %_81, align 8, !noundef !3
  store ptr %50, ptr %data_pointer, align 8
  %51 = load ptr, ptr %data_pointer, align 8, !noundef !3
  %52 = load i64, ptr %len, align 8, !noundef !3
  store ptr %51, ptr %ptr4, align 8
  %53 = getelementptr inbounds i8, ptr %ptr4, i64 8
  store i64 %52, ptr %53, align 8
  call void @llvm.lifetime.end.p0(i64 8, ptr %data_pointer)
  call void @llvm.lifetime.end.p0(i64 8, ptr %data5)
  br label %bb27

bb7:                                              ; preds = %bb20
  %self13 = getelementptr inbounds i8, ptr %raw_ptr, i64 %old_size9
  %count = sub i64 %new_size, %old_size9
  br label %bb24

bb24:                                             ; preds = %bb7
  %54 = mul i64 1, %count
  call void @llvm.memset.p0.i64(ptr align 1 %self13, i8 0, i64 %54, i1 false)
  br label %bb8

bb27:                                             ; preds = %bb25, %bb8
  %_85.0 = load ptr, ptr %ptr4, align 8, !noundef !3
  %55 = getelementptr inbounds i8, ptr %ptr4, i64 8
  %_85.1 = load i64, ptr %55, align 8, !noundef !3
  store ptr %_85.0, ptr %_34, align 8
  %56 = getelementptr inbounds i8, ptr %_34, i64 8
  store i64 %_85.1, ptr %56, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %ptr4)
  call void @llvm.lifetime.end.p0(i64 8, ptr %_81)
  call void @llvm.lifetime.end.p0(i64 8, ptr %len)
  call void @llvm.lifetime.end.p0(i64 8, ptr %data)
  %57 = load ptr, ptr %_34, align 8, !nonnull !3, !noundef !3
  %58 = getelementptr inbounds i8, ptr %_34, i64 8
  %59 = load i64, ptr %58, align 8, !noundef !3
  store ptr %57, ptr %_0, align 8
  %60 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %59, ptr %60, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %_34)
  br label %bb11

bb22:                                             ; No predecessors!
; call core::intrinsics::write_bytes::precondition_check
  call void @_ZN4core10intrinsics11write_bytes18precondition_check17hd24e09892c9ab5e4E(ptr noundef %self13, i64 noundef 1) #22
  %61 = mul i64 1, %count
  call void @llvm.memset.p0.i64(ptr align 1 %self13, i8 0, i64 %61, i1 false)
  call void @llvm.lifetime.start.p0(i64 16, ptr %_34)
  call void @llvm.lifetime.start.p0(i64 8, ptr %data)
  store ptr %ptr12, ptr %data, align 8
  call void @llvm.lifetime.start.p0(i64 8, ptr %len)
  store i64 %new_size, ptr %len, align 8
  call void @llvm.lifetime.start.p0(i64 8, ptr %_81)
  call void @llvm.lifetime.start.p0(i64 16, ptr %ptr4)
  call void @llvm.lifetime.start.p0(i64 8, ptr %data5)
  store ptr %ptr12, ptr %_81, align 8
  %62 = load ptr, ptr %_81, align 8, !noundef !3
  store ptr %62, ptr %data5, align 8
  call void @llvm.lifetime.start.p0(i64 8, ptr %data_pointer)
  %63 = load ptr, ptr %_81, align 8, !noundef !3
  store ptr %63, ptr %data_pointer, align 8
  %64 = load ptr, ptr %data_pointer, align 8, !noundef !3
  %65 = load i64, ptr %len, align 8, !noundef !3
  store ptr %64, ptr %ptr4, align 8
  %66 = getelementptr inbounds i8, ptr %ptr4, i64 8
  store i64 %65, ptr %66, align 8
  call void @llvm.lifetime.end.p0(i64 8, ptr %data_pointer)
  call void @llvm.lifetime.end.p0(i64 8, ptr %data5)
  br label %bb25

bb25:                                             ; preds = %bb22
  %_84 = load ptr, ptr %ptr4, align 8, !noundef !3
  %67 = getelementptr inbounds i8, ptr %ptr4, i64 8
  %68 = load i64, ptr %67, align 8, !noundef !3
; call core::ptr::non_null::NonNull<T>::new_unchecked::precondition_check
  call void @"_ZN4core3ptr8non_null16NonNull$LT$T$GT$13new_unchecked18precondition_check17hdc271a756f76605cE"(ptr noundef %_84) #22
  br label %bb27
}

; alloc::string::String::push
; Function Attrs: inlinehint nounwind
define internal void @_ZN5alloc6string6String4push17h96dfc48c19bd6e38E(ptr noalias noundef align 8 dereferenceable(24) %self, i32 noundef %ch) unnamed_addr #0 {
start:
  %_10 = alloca [4 x i8], align 1
  %_12 = icmp ult i32 %ch, 128
  br i1 %_12, label %bb4, label %bb5

bb5:                                              ; preds = %start
  %_13 = icmp ult i32 %ch, 2048
  br i1 %_13, label %bb6, label %bb7

bb4:                                              ; preds = %start
  %_4 = trunc i32 %ch to i8
; call alloc::vec::Vec<T,A>::push
  call void @"_ZN5alloc3vec16Vec$LT$T$C$A$GT$4push17h3eecfd24bc944e21E"(ptr noalias noundef align 8 dereferenceable(24) %self, i8 noundef %_4) #22
  br label %bb3

bb7:                                              ; preds = %bb5
  %_14 = icmp ult i32 %ch, 65536
  br i1 %_14, label %bb8, label %bb9

bb6:                                              ; preds = %bb5
  br label %bb11

bb9:                                              ; preds = %bb7
  br label %bb10

bb8:                                              ; preds = %bb7
  br label %bb10

bb10:                                             ; preds = %bb8, %bb9
  br label %bb11

bb11:                                             ; preds = %bb6, %bb10
  call void @llvm.lifetime.start.p0(i64 4, ptr %_10)
  call void @llvm.memset.p0.i64(ptr align 1 %_10, i8 0, i64 4, i1 false)
; call core::char::methods::encode_utf8_raw
  %0 = call { ptr, i64 } @_ZN4core4char7methods15encode_utf8_raw17h84badf475ef2bb54E(i32 noundef %ch, ptr noalias noundef nonnull align 1 %_10, i64 noundef 4) #22
  %v.0 = extractvalue { ptr, i64 } %0, 0
  %v.1 = extractvalue { ptr, i64 } %0, 1
; call alloc::vec::Vec<T,A>::extend_from_slice
  call void @"_ZN5alloc3vec16Vec$LT$T$C$A$GT$17extend_from_slice17h9db90023fcfc2b1eE"(ptr noalias noundef align 8 dereferenceable(24) %self, ptr noalias noundef nonnull readonly align 1 %v.0, i64 noundef %v.1) #22
  call void @llvm.lifetime.end.p0(i64 4, ptr %_10)
  br label %bb3

bb3:                                              ; preds = %bb4, %bb11
  ret void
}

; alloc::raw_vec::finish_grow
; Function Attrs: noinline nounwind
define internal void @_ZN5alloc7raw_vec11finish_grow17h87f821cc75349c87E(ptr dead_on_unwind noalias nocapture noundef writable sret([24 x i8]) align 8 dereferenceable(24) %_0, i64 noundef %0, i64 %1, ptr noalias nocapture noundef readonly align 8 dereferenceable(24) %current_memory, ptr noalias noundef nonnull align 1 %alloc) unnamed_addr #3 {
start:
  %self3 = alloca [16 x i8], align 8
  %_59 = alloca [16 x i8], align 8
  %_50 = alloca [8 x i8], align 8
  %_44 = alloca [8 x i8], align 8
  %_39 = alloca [16 x i8], align 8
  %_37 = alloca [16 x i8], align 8
  %self2 = alloca [16 x i8], align 8
  %old_layout = alloca [16 x i8], align 8
  %memory = alloca [16 x i8], align 8
  %residual = alloca [16 x i8], align 8
  %self = alloca [24 x i8], align 8
  %_5 = alloca [24 x i8], align 8
  %new_layout1 = alloca [16 x i8], align 8
  %new_layout = alloca [16 x i8], align 8
  store i64 %0, ptr %new_layout, align 8
  %2 = getelementptr inbounds i8, ptr %new_layout, i64 8
  store i64 %1, ptr %2, align 8
  call void @llvm.lifetime.start.p0(i64 16, ptr %new_layout1)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_5)
  call void @llvm.lifetime.start.p0(i64 24, ptr %self)
  %3 = load i64, ptr %new_layout, align 8, !range !9, !noundef !3
  %4 = icmp eq i64 %3, 0
  %_33 = select i1 %4, i64 1, i64 0
  switch i64 %_33, label %bb1 [
    i64 0, label %bb9
    i64 1, label %bb8
  ]

bb1:                                              ; preds = %bb6, %bb9, %start
  unreachable

bb9:                                              ; preds = %start
  %t.0 = load i64, ptr %new_layout, align 8, !range !8, !noundef !3
  %5 = getelementptr inbounds i8, ptr %new_layout, i64 8
  %t.1 = load i64, ptr %5, align 8, !noundef !3
  %6 = getelementptr inbounds i8, ptr %self, i64 8
  store i64 %t.0, ptr %6, align 8
  %7 = getelementptr inbounds i8, ptr %6, i64 8
  store i64 %t.1, ptr %7, align 8
  store i64 0, ptr %self, align 8
  %8 = getelementptr inbounds i8, ptr %self, i64 8
  %v.0 = load i64, ptr %8, align 8, !range !8, !noundef !3
  %9 = getelementptr inbounds i8, ptr %8, i64 8
  %v.1 = load i64, ptr %9, align 8, !noundef !3
  %10 = getelementptr inbounds i8, ptr %_5, i64 8
  store i64 %v.0, ptr %10, align 8
  %11 = getelementptr inbounds i8, ptr %10, i64 8
  store i64 %v.1, ptr %11, align 8
  store i64 0, ptr %_5, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %self)
  %12 = getelementptr inbounds i8, ptr %_5, i64 8
  %val.0 = load i64, ptr %12, align 8, !range !8, !noundef !3
  %13 = getelementptr inbounds i8, ptr %12, i64 8
  %val.1 = load i64, ptr %13, align 8, !noundef !3
  store i64 %val.0, ptr %new_layout1, align 8
  %14 = getelementptr inbounds i8, ptr %new_layout1, i64 8
  store i64 %val.1, ptr %14, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_5)
  %15 = getelementptr inbounds i8, ptr %new_layout1, i64 8
  %alloc_size = load i64, ptr %15, align 8, !noundef !3
  call void @llvm.lifetime.start.p0(i64 16, ptr %memory)
  %16 = getelementptr inbounds i8, ptr %current_memory, i64 8
  %17 = load i64, ptr %16, align 8, !range !9, !noundef !3
  %18 = icmp eq i64 %17, 0
  %_14 = select i1 %18, i64 0, i64 1
  switch i64 %_14, label %bb1 [
    i64 1, label %bb3
    i64 0, label %bb2
  ]

bb8:                                              ; preds = %start
  %19 = load i64, ptr @0, align 8, !range !9, !noundef !3
  %20 = load i64, ptr getelementptr inbounds (i8, ptr @0, i64 8), align 8
  %21 = getelementptr inbounds i8, ptr %self, i64 8
  store i64 %19, ptr %21, align 8
  %22 = getelementptr inbounds i8, ptr %21, i64 8
  store i64 %20, ptr %22, align 8
  store i64 1, ptr %self, align 8
  %23 = getelementptr inbounds i8, ptr %self, i64 8
  %e.0 = load i64, ptr %23, align 8, !range !9, !noundef !3
  %24 = getelementptr inbounds i8, ptr %23, i64 8
  %e.1 = load i64, ptr %24, align 8
  call void @llvm.lifetime.start.p0(i64 16, ptr %_37)
  store i64 %e.0, ptr %_37, align 8
  %25 = getelementptr inbounds i8, ptr %_37, i64 8
  store i64 %e.1, ptr %25, align 8
  %26 = load i64, ptr %_37, align 8, !range !9, !noundef !3
  %27 = getelementptr inbounds i8, ptr %_37, i64 8
  %28 = load i64, ptr %27, align 8
  %29 = getelementptr inbounds i8, ptr %_5, i64 8
  store i64 %26, ptr %29, align 8
  %30 = getelementptr inbounds i8, ptr %29, i64 8
  store i64 %28, ptr %30, align 8
  store i64 1, ptr %_5, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %_37)
  call void @llvm.lifetime.end.p0(i64 24, ptr %self)
  %31 = getelementptr inbounds i8, ptr %_5, i64 8
  %32 = load i64, ptr %31, align 8, !range !9, !noundef !3
  %33 = getelementptr inbounds i8, ptr %31, i64 8
  %34 = load i64, ptr %33, align 8
  store i64 %32, ptr %residual, align 8
  %35 = getelementptr inbounds i8, ptr %residual, i64 8
  store i64 %34, ptr %35, align 8
  %e.08 = load i64, ptr %residual, align 8, !range !9, !noundef !3
  %36 = getelementptr inbounds i8, ptr %residual, i64 8
  %e.19 = load i64, ptr %36, align 8
  call void @llvm.lifetime.start.p0(i64 16, ptr %_39)
  store i64 %e.08, ptr %_39, align 8
  %37 = getelementptr inbounds i8, ptr %_39, i64 8
  store i64 %e.19, ptr %37, align 8
  %38 = load i64, ptr %_39, align 8, !range !9, !noundef !3
  %39 = getelementptr inbounds i8, ptr %_39, i64 8
  %40 = load i64, ptr %39, align 8
  %41 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %38, ptr %41, align 8
  %42 = getelementptr inbounds i8, ptr %41, i64 8
  store i64 %40, ptr %42, align 8
  store i64 1, ptr %_0, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %_39)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_5)
  call void @llvm.lifetime.end.p0(i64 16, ptr %new_layout1)
  br label %bb7

bb3:                                              ; preds = %bb9
  %ptr = load ptr, ptr %current_memory, align 8, !nonnull !3, !noundef !3
  call void @llvm.lifetime.start.p0(i64 16, ptr %old_layout)
  %43 = getelementptr inbounds i8, ptr %current_memory, i64 8
  %44 = load i64, ptr %43, align 8, !range !8, !noundef !3
  %45 = getelementptr inbounds i8, ptr %43, i64 8
  %46 = load i64, ptr %45, align 8, !noundef !3
  store i64 %44, ptr %old_layout, align 8
  %47 = getelementptr inbounds i8, ptr %old_layout, i64 8
  store i64 %46, ptr %47, align 8
  %self4 = load i64, ptr %old_layout, align 8, !range !8, !noundef !3
  call void @llvm.lifetime.start.p0(i64 8, ptr %_44)
  store i64 %self4, ptr %_44, align 8
  %_45 = load i64, ptr %_44, align 8, !range !8, !noundef !3
  %_46 = icmp uge i64 %_45, 1
  %_47 = icmp ule i64 %_45, -9223372036854775808
  %_48 = and i1 %_46, %_47
  call void @llvm.assume(i1 %_48)
  call void @llvm.lifetime.end.p0(i64 8, ptr %_44)
  %self5 = load i64, ptr %new_layout1, align 8, !range !8, !noundef !3
  call void @llvm.lifetime.start.p0(i64 8, ptr %_50)
  store i64 %self5, ptr %_50, align 8
  %_51 = load i64, ptr %_50, align 8, !range !8, !noundef !3
  %_52 = icmp uge i64 %_51, 1
  %_53 = icmp ule i64 %_51, -9223372036854775808
  %_54 = and i1 %_52, %_53
  call void @llvm.assume(i1 %_54)
  call void @llvm.lifetime.end.p0(i64 8, ptr %_50)
  %cond = icmp eq i64 %_45, %_51
  br label %bb11

bb2:                                              ; preds = %bb9
  %_30.0 = load i64, ptr %new_layout1, align 8, !range !8, !noundef !3
  %48 = getelementptr inbounds i8, ptr %new_layout1, i64 8
  %_30.1 = load i64, ptr %48, align 8, !noundef !3
; call <alloc::alloc::Global as core::alloc::Allocator>::allocate
  %49 = call { ptr, i64 } @"_ZN63_$LT$alloc..alloc..Global$u20$as$u20$core..alloc..Allocator$GT$8allocate17h86fb36cfb6510ed6E"(ptr noalias noundef nonnull readonly align 1 %alloc, i64 noundef %_30.0, i64 noundef %_30.1) #22
  %50 = extractvalue { ptr, i64 } %49, 0
  %51 = extractvalue { ptr, i64 } %49, 1
  store ptr %50, ptr %memory, align 8
  %52 = getelementptr inbounds i8, ptr %memory, i64 8
  store i64 %51, ptr %52, align 8
  br label %bb6

bb11:                                             ; preds = %bb3
  call void @llvm.assume(i1 %cond)
  %_27.0 = load i64, ptr %old_layout, align 8, !range !8, !noundef !3
  %53 = getelementptr inbounds i8, ptr %old_layout, i64 8
  %_27.1 = load i64, ptr %53, align 8, !noundef !3
  %_28.0 = load i64, ptr %new_layout1, align 8, !range !8, !noundef !3
  %54 = getelementptr inbounds i8, ptr %new_layout1, i64 8
  %_28.1 = load i64, ptr %54, align 8, !noundef !3
; call <alloc::alloc::Global as core::alloc::Allocator>::grow
  %55 = call { ptr, i64 } @"_ZN63_$LT$alloc..alloc..Global$u20$as$u20$core..alloc..Allocator$GT$4grow17h26b309edff39b183E"(ptr noalias noundef nonnull readonly align 1 %alloc, ptr noundef nonnull %ptr, i64 noundef %_27.0, i64 noundef %_27.1, i64 noundef %_28.0, i64 noundef %_28.1) #22
  %56 = extractvalue { ptr, i64 } %55, 0
  %57 = extractvalue { ptr, i64 } %55, 1
  store ptr %56, ptr %memory, align 8
  %58 = getelementptr inbounds i8, ptr %memory, i64 8
  store i64 %57, ptr %58, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %old_layout)
  br label %bb6

bb10:                                             ; No predecessors!
  unreachable

bb6:                                              ; preds = %bb2, %bb11
  call void @llvm.lifetime.start.p0(i64 16, ptr %self2)
  %59 = load ptr, ptr %memory, align 8, !noundef !3
  %60 = getelementptr inbounds i8, ptr %memory, i64 8
  %61 = load i64, ptr %60, align 8
  store ptr %59, ptr %self2, align 8
  %62 = getelementptr inbounds i8, ptr %self2, i64 8
  store i64 %61, ptr %62, align 8
  %63 = load ptr, ptr %self2, align 8, !noundef !3
  %64 = ptrtoint ptr %63 to i64
  %65 = icmp eq i64 %64, 0
  %_57 = select i1 %65, i64 1, i64 0
  switch i64 %_57, label %bb1 [
    i64 0, label %bb14
    i64 1, label %bb13
  ]

bb14:                                             ; preds = %bb6
  %t.06 = load ptr, ptr %self2, align 8, !nonnull !3, !noundef !3
  %66 = getelementptr inbounds i8, ptr %self2, i64 8
  %t.17 = load i64, ptr %66, align 8, !noundef !3
  %67 = getelementptr inbounds i8, ptr %_0, i64 8
  store ptr %t.06, ptr %67, align 8
  %68 = getelementptr inbounds i8, ptr %67, i64 8
  store i64 %t.17, ptr %68, align 8
  store i64 0, ptr %_0, align 8
  br label %bb12

bb13:                                             ; preds = %bb6
  call void @llvm.lifetime.start.p0(i64 16, ptr %_59)
  call void @llvm.lifetime.start.p0(i64 16, ptr %self3)
  %_61.0 = load i64, ptr %new_layout1, align 8, !range !8, !noundef !3
  %69 = getelementptr inbounds i8, ptr %new_layout1, i64 8
  %_61.1 = load i64, ptr %69, align 8, !noundef !3
  store i64 %_61.0, ptr %self3, align 8
  %70 = getelementptr inbounds i8, ptr %self3, i64 8
  store i64 %_61.1, ptr %70, align 8
  %71 = load i64, ptr %self3, align 8, !range !9, !noundef !3
  %72 = getelementptr inbounds i8, ptr %self3, i64 8
  %73 = load i64, ptr %72, align 8
  store i64 %71, ptr %_59, align 8
  %74 = getelementptr inbounds i8, ptr %_59, i64 8
  store i64 %73, ptr %74, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %self3)
  %75 = load i64, ptr %_59, align 8, !range !9, !noundef !3
  %76 = getelementptr inbounds i8, ptr %_59, i64 8
  %77 = load i64, ptr %76, align 8
  %78 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %75, ptr %78, align 8
  %79 = getelementptr inbounds i8, ptr %78, i64 8
  store i64 %77, ptr %79, align 8
  store i64 1, ptr %_0, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %_59)
  br label %bb12

bb12:                                             ; preds = %bb13, %bb14
  call void @llvm.lifetime.end.p0(i64 16, ptr %self2)
  call void @llvm.lifetime.end.p0(i64 16, ptr %memory)
  call void @llvm.lifetime.end.p0(i64 16, ptr %new_layout1)
  br label %bb7

bb7:                                              ; preds = %bb8, %bb12
  ret void
}

; alloc::raw_vec::RawVec<T,A>::current_memory
; Function Attrs: nounwind
define internal void @"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14current_memory17hc167f39406d68977E"(ptr dead_on_unwind noalias nocapture noundef writable sret([24 x i8]) align 8 dereferenceable(24) %_0, ptr noalias noundef readonly align 8 dereferenceable(16) %self) unnamed_addr #1 {
start:
  %self1 = alloca [8 x i8], align 8
  %_9 = alloca [24 x i8], align 8
  %layout = alloca [16 x i8], align 8
  br label %bb1

bb1:                                              ; preds = %start
  %_3 = load i64, ptr %self, align 8, !noundef !3
  %0 = icmp eq i64 %_3, 0
  br i1 %0, label %bb2, label %bb4

bb2:                                              ; preds = %bb1
  br label %bb3

bb4:                                              ; preds = %bb1
  %rhs = load i64, ptr %self, align 8, !noundef !3
  %size = mul nuw i64 1, %rhs
  call void @llvm.assume(i1 true)
  call void @llvm.assume(i1 true)
  %1 = getelementptr inbounds i8, ptr %layout, i64 8
  store i64 %size, ptr %1, align 8
  store i64 1, ptr %layout, align 8
  call void @llvm.lifetime.start.p0(i64 24, ptr %_9)
  %2 = getelementptr inbounds i8, ptr %self, i64 8
  %self2 = load ptr, ptr %2, align 8, !nonnull !3, !noundef !3
  store ptr %self2, ptr %self1, align 8
  %3 = load ptr, ptr %self1, align 8, !nonnull !3, !noundef !3
  store ptr %3, ptr %_9, align 8
  %4 = load i64, ptr %layout, align 8, !range !8, !noundef !3
  %5 = getelementptr inbounds i8, ptr %layout, i64 8
  %6 = load i64, ptr %5, align 8, !noundef !3
  %7 = getelementptr inbounds i8, ptr %_9, i64 8
  store i64 %4, ptr %7, align 8
  %8 = getelementptr inbounds i8, ptr %7, i64 8
  store i64 %6, ptr %8, align 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_0, ptr align 8 %_9, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_9)
  br label %bb5

bb3:                                              ; preds = %bb2
  %9 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 0, ptr %9, align 8
  br label %bb5

bb5:                                              ; preds = %bb3, %bb4
  ret void
}

; alloc::raw_vec::RawVec<T,A>::grow_amortized
; Function Attrs: nounwind
define internal { i64, i64 } @"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14grow_amortized17h842a7461f6b52281E"(ptr noalias noundef align 8 dereferenceable(16) %self, i64 noundef %len, i64 noundef %additional) unnamed_addr #1 {
start:
  %0 = alloca [1 x i8], align 1
  %_59 = alloca [8 x i8], align 8
  %pointer = alloca [8 x i8], align 8
  %_57 = alloca [8 x i8], align 8
  %_56 = alloca [16 x i8], align 8
  %_46 = alloca [16 x i8], align 8
  %_45 = alloca [1 x i8], align 1
  %_44 = alloca [8 x i8], align 8
  %_43 = alloca [16 x i8], align 8
  %_38 = alloca [16 x i8], align 8
  %_37 = alloca [1 x i8], align 1
  %_36 = alloca [16 x i8], align 8
  %residual6 = alloca [16 x i8], align 8
  %_20 = alloca [24 x i8], align 8
  %self5 = alloca [24 x i8], align 8
  %_18 = alloca [24 x i8], align 8
  %v24 = alloca [8 x i8], align 8
  %cap3 = alloca [8 x i8], align 8
  %v2 = alloca [8 x i8], align 8
  %v1 = alloca [8 x i8], align 8
  %cap = alloca [8 x i8], align 8
  %residual = alloca [16 x i8], align 8
  %self2 = alloca [16 x i8], align 8
  %self1 = alloca [16 x i8], align 8
  %_5 = alloca [16 x i8], align 8
  %_0 = alloca [16 x i8], align 8
  br label %bb2

bb2:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 16, ptr %_5)
  call void @llvm.lifetime.start.p0(i64 16, ptr %self1)
  call void @llvm.lifetime.start.p0(i64 16, ptr %self2)
  %1 = call { i64, i1 } @llvm.uadd.with.overflow.i64(i64 %len, i64 %additional)
  %_29.0 = extractvalue { i64, i1 } %1, 0
  %_29.1 = extractvalue { i64, i1 } %1, 1
  call void @llvm.lifetime.start.p0(i64 1, ptr %0)
  %2 = call i1 @llvm.expect.i1(i1 %_29.1, i1 false)
  %3 = zext i1 %2 to i8
  store i8 %3, ptr %0, align 1
  %4 = load i8, ptr %0, align 1, !range !4, !noundef !3
  %_26 = trunc i8 %4 to i1
  call void @llvm.lifetime.end.p0(i64 1, ptr %0)
  br i1 %_26, label %bb9, label %bb10

bb10:                                             ; preds = %bb2
  %5 = getelementptr inbounds i8, ptr %self2, i64 8
  store i64 %_29.0, ptr %5, align 8
  store i64 1, ptr %self2, align 8
  %6 = getelementptr inbounds i8, ptr %self2, i64 8
  %v = load i64, ptr %6, align 8, !noundef !3
  %7 = getelementptr inbounds i8, ptr %self1, i64 8
  store i64 %v, ptr %7, align 8
  store i64 -9223372036854775807, ptr %self1, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %self2)
  %8 = getelementptr inbounds i8, ptr %self1, i64 8
  %v7 = load i64, ptr %8, align 8, !noundef !3
  %9 = getelementptr inbounds i8, ptr %_5, i64 8
  store i64 %v7, ptr %9, align 8
  store i64 -9223372036854775807, ptr %_5, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %self1)
  %10 = getelementptr inbounds i8, ptr %_5, i64 8
  %required_cap = load i64, ptr %10, align 8, !noundef !3
  call void @llvm.lifetime.end.p0(i64 16, ptr %_5)
  call void @llvm.lifetime.start.p0(i64 8, ptr %cap)
  call void @llvm.lifetime.start.p0(i64 8, ptr %v1)
  %_12 = load i64, ptr %self, align 8, !noundef !3
  %11 = mul i64 %_12, 2
  store i64 %11, ptr %v1, align 8
  call void @llvm.lifetime.start.p0(i64 8, ptr %v2)
  store i64 %required_cap, ptr %v2, align 8
  call void @llvm.lifetime.start.p0(i64 1, ptr %_37)
  call void @llvm.lifetime.start.p0(i64 16, ptr %_38)
  store ptr %v1, ptr %_38, align 8
  %12 = getelementptr inbounds i8, ptr %_38, i64 8
  store ptr %v2, ptr %12, align 8
  %13 = load ptr, ptr %_38, align 8, !nonnull !3, !align !5, !noundef !3
  %14 = getelementptr inbounds i8, ptr %_38, i64 8
  %15 = load ptr, ptr %14, align 8, !nonnull !3, !align !5, !noundef !3
; call core::ops::function::FnOnce::call_once
  %16 = call noundef i8 @_ZN4core3ops8function6FnOnce9call_once17hb1bad2e3e1b02e6cE(ptr noalias noundef readonly align 8 dereferenceable(8) %13, ptr noalias noundef readonly align 8 dereferenceable(8) %15) #22, !range !7
  store i8 %16, ptr %_37, align 1
  call void @llvm.lifetime.end.p0(i64 16, ptr %_38)
  %_41 = load i8, ptr %_37, align 1, !range !7, !noundef !3
  switch i8 %_41, label %bb3 [
    i8 -1, label %bb14
    i8 0, label %bb14
    i8 1, label %bb13
  ]

bb9:                                              ; preds = %bb2
  %17 = load i64, ptr @0, align 8, !range !2, !noundef !3
  %18 = load i64, ptr getelementptr inbounds (i8, ptr @0, i64 8), align 8
  store i64 %17, ptr %self2, align 8
  %19 = getelementptr inbounds i8, ptr %self2, i64 8
  store i64 %18, ptr %19, align 8
  %20 = load i64, ptr @0, align 8, !range !9, !noundef !3
  %21 = load i64, ptr getelementptr inbounds (i8, ptr @0, i64 8), align 8
  store i64 %20, ptr %self1, align 8
  %22 = getelementptr inbounds i8, ptr %self1, i64 8
  store i64 %21, ptr %22, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %self2)
  %e.011 = load i64, ptr %self1, align 8, !range !9, !noundef !3
  %23 = getelementptr inbounds i8, ptr %self1, i64 8
  %e.112 = load i64, ptr %23, align 8
  call void @llvm.lifetime.start.p0(i64 16, ptr %_36)
  store i64 %e.011, ptr %_36, align 8
  %24 = getelementptr inbounds i8, ptr %_36, i64 8
  store i64 %e.112, ptr %24, align 8
  %25 = load i64, ptr %_36, align 8, !range !9, !noundef !3
  %26 = getelementptr inbounds i8, ptr %_36, i64 8
  %27 = load i64, ptr %26, align 8
  store i64 %25, ptr %_5, align 8
  %28 = getelementptr inbounds i8, ptr %_5, i64 8
  store i64 %27, ptr %28, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %_36)
  call void @llvm.lifetime.end.p0(i64 16, ptr %self1)
  %29 = load i64, ptr %_5, align 8, !range !9, !noundef !3
  %30 = getelementptr inbounds i8, ptr %_5, i64 8
  %31 = load i64, ptr %30, align 8
  store i64 %29, ptr %residual, align 8
  %32 = getelementptr inbounds i8, ptr %residual, i64 8
  store i64 %31, ptr %32, align 8
  %e.013 = load i64, ptr %residual, align 8, !range !9, !noundef !3
  %33 = getelementptr inbounds i8, ptr %residual, i64 8
  %e.114 = load i64, ptr %33, align 8
  call void @llvm.lifetime.start.p0(i64 16, ptr %_43)
  store i64 %e.013, ptr %_43, align 8
  %34 = getelementptr inbounds i8, ptr %_43, i64 8
  store i64 %e.114, ptr %34, align 8
  %35 = load i64, ptr %_43, align 8, !range !9, !noundef !3
  %36 = getelementptr inbounds i8, ptr %_43, i64 8
  %37 = load i64, ptr %36, align 8
  store i64 %35, ptr %_0, align 8
  %38 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %37, ptr %38, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %_43)
  call void @llvm.lifetime.end.p0(i64 16, ptr %_5)
  br label %bb6

bb3:                                              ; preds = %bb15, %bb11, %bb10
  unreachable

bb14:                                             ; preds = %bb10, %bb10
  %39 = load i64, ptr %v2, align 8, !noundef !3
  store i64 %39, ptr %cap, align 8
  call void @llvm.lifetime.end.p0(i64 1, ptr %_37)
  br label %bb11

bb13:                                             ; preds = %bb10
  %40 = load i64, ptr %v1, align 8, !noundef !3
  store i64 %40, ptr %cap, align 8
  call void @llvm.lifetime.end.p0(i64 1, ptr %_37)
  br label %bb11

bb11:                                             ; preds = %bb13, %bb14
  call void @llvm.lifetime.end.p0(i64 8, ptr %v2)
  call void @llvm.lifetime.end.p0(i64 8, ptr %v1)
  call void @llvm.lifetime.start.p0(i64 8, ptr %cap3)
  call void @llvm.lifetime.start.p0(i64 8, ptr %v24)
  %41 = load i64, ptr %cap, align 8, !noundef !3
  store i64 %41, ptr %v24, align 8
  call void @llvm.lifetime.start.p0(i64 8, ptr %_44)
  store i64 8, ptr %_44, align 8
  call void @llvm.lifetime.start.p0(i64 1, ptr %_45)
  call void @llvm.lifetime.start.p0(i64 16, ptr %_46)
  store ptr %_44, ptr %_46, align 8
  %42 = getelementptr inbounds i8, ptr %_46, i64 8
  store ptr %v24, ptr %42, align 8
  %43 = load ptr, ptr %_46, align 8, !nonnull !3, !align !5, !noundef !3
  %44 = getelementptr inbounds i8, ptr %_46, i64 8
  %45 = load ptr, ptr %44, align 8, !nonnull !3, !align !5, !noundef !3
; call core::ops::function::FnOnce::call_once
  %46 = call noundef i8 @_ZN4core3ops8function6FnOnce9call_once17hb1bad2e3e1b02e6cE(ptr noalias noundef readonly align 8 dereferenceable(8) %43, ptr noalias noundef readonly align 8 dereferenceable(8) %45) #22, !range !7
  store i8 %46, ptr %_45, align 1
  call void @llvm.lifetime.end.p0(i64 16, ptr %_46)
  %_49 = load i8, ptr %_45, align 1, !range !7, !noundef !3
  switch i8 %_49, label %bb3 [
    i8 -1, label %bb18
    i8 0, label %bb18
    i8 1, label %bb17
  ]

bb18:                                             ; preds = %bb11, %bb11
  %47 = load i64, ptr %v24, align 8, !noundef !3
  store i64 %47, ptr %cap3, align 8
  call void @llvm.lifetime.end.p0(i64 1, ptr %_45)
  br label %bb15

bb17:                                             ; preds = %bb11
  %48 = load i64, ptr %_44, align 8, !noundef !3
  store i64 %48, ptr %cap3, align 8
  call void @llvm.lifetime.end.p0(i64 1, ptr %_45)
  br label %bb15

bb15:                                             ; preds = %bb17, %bb18
  call void @llvm.lifetime.end.p0(i64 8, ptr %_44)
  call void @llvm.lifetime.end.p0(i64 8, ptr %v24)
  %n = load i64, ptr %cap3, align 8, !noundef !3
  call void @llvm.assume(i1 true)
  call void @llvm.assume(i1 true)
; call core::alloc::layout::Layout::array::inner
  %49 = call { i64, i64 } @_ZN4core5alloc6layout6Layout5array5inner17h433a9d6723d6a257E(i64 noundef 1, i64 noundef 1, i64 noundef %n) #22
  %new_layout.0 = extractvalue { i64, i64 } %49, 0
  %new_layout.1 = extractvalue { i64, i64 } %49, 1
  call void @llvm.lifetime.start.p0(i64 24, ptr %_18)
  call void @llvm.lifetime.start.p0(i64 24, ptr %self5)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_20)
; call alloc::raw_vec::RawVec<T,A>::current_memory
  call void @"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14current_memory17hc167f39406d68977E"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_20, ptr noalias noundef readonly align 8 dereferenceable(16) %self) #22
  %_22 = getelementptr inbounds i8, ptr %self, i64 16
; call alloc::raw_vec::finish_grow
  call void @_ZN5alloc7raw_vec11finish_grow17h87f821cc75349c87E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %self5, i64 noundef %new_layout.0, i64 %new_layout.1, ptr noalias nocapture noundef readonly align 8 dereferenceable(24) %_20, ptr noalias noundef nonnull align 1 %_22) #22
  call void @llvm.lifetime.end.p0(i64 24, ptr %_20)
  %_53 = load i64, ptr %self5, align 8, !range !2, !noundef !3
  switch i64 %_53, label %bb3 [
    i64 0, label %bb21
    i64 1, label %bb20
  ]

bb21:                                             ; preds = %bb15
  %50 = getelementptr inbounds i8, ptr %self5, i64 8
  %v.0 = load ptr, ptr %50, align 8, !nonnull !3, !noundef !3
  %51 = getelementptr inbounds i8, ptr %50, i64 8
  %v.1 = load i64, ptr %51, align 8, !noundef !3
  %52 = getelementptr inbounds i8, ptr %_18, i64 8
  store ptr %v.0, ptr %52, align 8
  %53 = getelementptr inbounds i8, ptr %52, i64 8
  store i64 %v.1, ptr %53, align 8
  store i64 0, ptr %_18, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %self5)
  %54 = getelementptr inbounds i8, ptr %_18, i64 8
  %ptr.0 = load ptr, ptr %54, align 8, !nonnull !3, !noundef !3
  %55 = getelementptr inbounds i8, ptr %54, i64 8
  %ptr.1 = load i64, ptr %55, align 8, !noundef !3
  call void @llvm.lifetime.end.p0(i64 24, ptr %_18)
  %cap8 = load i64, ptr %cap3, align 8, !noundef !3
  call void @llvm.lifetime.start.p0(i64 8, ptr %_57)
  call void @llvm.lifetime.start.p0(i64 8, ptr %pointer)
  store ptr %ptr.0, ptr %pointer, align 8
  %56 = load ptr, ptr %pointer, align 8, !nonnull !3, !noundef !3
  store ptr %56, ptr %_57, align 8
  call void @llvm.lifetime.end.p0(i64 8, ptr %pointer)
  %57 = getelementptr inbounds i8, ptr %self, i64 8
  %58 = load ptr, ptr %_57, align 8, !nonnull !3, !noundef !3
  store ptr %58, ptr %57, align 8
  call void @llvm.lifetime.end.p0(i64 8, ptr %_57)
  call void @llvm.lifetime.start.p0(i64 8, ptr %_59)
  store i64 %cap8, ptr %_59, align 8
  %59 = load i64, ptr %_59, align 8, !range !10, !noundef !3
  store i64 %59, ptr %self, align 8
  call void @llvm.lifetime.end.p0(i64 8, ptr %_59)
  %60 = load i64, ptr @1, align 8, !range !11, !noundef !3
  %61 = load i64, ptr getelementptr inbounds (i8, ptr @1, i64 8), align 8
  store i64 %60, ptr %_0, align 8
  %62 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %61, ptr %62, align 8
  call void @llvm.lifetime.end.p0(i64 8, ptr %cap3)
  call void @llvm.lifetime.end.p0(i64 8, ptr %cap)
  br label %bb7

bb20:                                             ; preds = %bb15
  %63 = getelementptr inbounds i8, ptr %self5, i64 8
  %e.0 = load i64, ptr %63, align 8, !range !9, !noundef !3
  %64 = getelementptr inbounds i8, ptr %63, i64 8
  %e.1 = load i64, ptr %64, align 8
  call void @llvm.lifetime.start.p0(i64 16, ptr %_56)
  store i64 %e.0, ptr %_56, align 8
  %65 = getelementptr inbounds i8, ptr %_56, i64 8
  store i64 %e.1, ptr %65, align 8
  %66 = load i64, ptr %_56, align 8, !range !9, !noundef !3
  %67 = getelementptr inbounds i8, ptr %_56, i64 8
  %68 = load i64, ptr %67, align 8
  %69 = getelementptr inbounds i8, ptr %_18, i64 8
  store i64 %66, ptr %69, align 8
  %70 = getelementptr inbounds i8, ptr %69, i64 8
  store i64 %68, ptr %70, align 8
  store i64 1, ptr %_18, align 8
  call void @llvm.lifetime.end.p0(i64 16, ptr %_56)
  call void @llvm.lifetime.end.p0(i64 24, ptr %self5)
  %71 = getelementptr inbounds i8, ptr %_18, i64 8
  %72 = load i64, ptr %71, align 8, !range !9, !noundef !3
  %73 = getelementptr inbounds i8, ptr %71, i64 8
  %74 = load i64, ptr %73, align 8
  store i64 %72, ptr %residual6, align 8
  %75 = getelementptr inbounds i8, ptr %residual6, i64 8
  store i64 %74, ptr %75, align 8
  %e.09 = load i64, ptr %residual6, align 8, !range !9, !noundef !3
  %76 = getelementptr inbounds i8, ptr %residual6, i64 8
  %e.110 = load i64, ptr %76, align 8
  store i64 %e.09, ptr %_0, align 8
  %77 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %e.110, ptr %77, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_18)
  call void @llvm.lifetime.end.p0(i64 8, ptr %cap3)
  call void @llvm.lifetime.end.p0(i64 8, ptr %cap)
  br label %bb6

bb7:                                              ; preds = %bb6, %bb21
  %78 = load i64, ptr %_0, align 8, !range !11, !noundef !3
  %79 = getelementptr inbounds i8, ptr %_0, i64 8
  %80 = load i64, ptr %79, align 8
  %81 = insertvalue { i64, i64 } poison, i64 %78, 0
  %82 = insertvalue { i64, i64 } %81, i64 %80, 1
  ret { i64, i64 } %82

bb6:                                              ; preds = %bb9, %bb20
  br label %bb7

bb1:                                              ; No predecessors!
  unreachable
}

; alloc::raw_vec::RawVec<T,A>::reserve::do_reserve_and_handle
; Function Attrs: cold nounwind
define internal void @"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$7reserve21do_reserve_and_handle17h841f8186853dc167E"(ptr noalias noundef align 8 dereferenceable(16) %slf, i64 noundef %len, i64 noundef %additional) unnamed_addr #4 {
start:
  %_4 = alloca [16 x i8], align 8
  call void @llvm.lifetime.start.p0(i64 16, ptr %_4)
; call alloc::raw_vec::RawVec<T,A>::grow_amortized
  %0 = call { i64, i64 } @"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14grow_amortized17h842a7461f6b52281E"(ptr noalias noundef align 8 dereferenceable(16) %slf, i64 noundef %len, i64 noundef %additional) #22
  %1 = extractvalue { i64, i64 } %0, 0
  %2 = extractvalue { i64, i64 } %0, 1
  store i64 %1, ptr %_4, align 8
  %3 = getelementptr inbounds i8, ptr %_4, i64 8
  store i64 %2, ptr %3, align 8
  %4 = load i64, ptr %_4, align 8, !range !11, !noundef !3
  %5 = icmp eq i64 %4, -9223372036854775807
  %_5 = select i1 %5, i64 0, i64 1
  switch i64 %_5, label %bb4 [
    i64 1, label %bb2
    i64 0, label %bb3
  ]

bb4:                                              ; preds = %start
  unreachable

bb2:                                              ; preds = %start
  %err.0 = load i64, ptr %_4, align 8, !range !9, !noundef !3
  %6 = getelementptr inbounds i8, ptr %_4, i64 8
  %err.1 = load i64, ptr %6, align 8
; call alloc::raw_vec::handle_error
  call void @_ZN5alloc7raw_vec12handle_error17h22fdf317f3a37641E(i64 noundef %err.0, i64 %err.1) #21
  unreachable

bb3:                                              ; preds = %start
  call void @llvm.lifetime.end.p0(i64 16, ptr %_4)
  ret void
}

; alloc::raw_vec::RawVec<T,A>::grow_one
; Function Attrs: noinline nounwind
define internal void @"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$8grow_one17h4b15183664487c30E"(ptr noalias noundef align 8 dereferenceable(16) %self) unnamed_addr #3 {
start:
  %_2 = alloca [16 x i8], align 8
  call void @llvm.lifetime.start.p0(i64 16, ptr %_2)
  %_3 = load i64, ptr %self, align 8, !noundef !3
; call alloc::raw_vec::RawVec<T,A>::grow_amortized
  %0 = call { i64, i64 } @"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14grow_amortized17h842a7461f6b52281E"(ptr noalias noundef align 8 dereferenceable(16) %self, i64 noundef %_3, i64 noundef 1) #22
  %1 = extractvalue { i64, i64 } %0, 0
  %2 = extractvalue { i64, i64 } %0, 1
  store i64 %1, ptr %_2, align 8
  %3 = getelementptr inbounds i8, ptr %_2, i64 8
  store i64 %2, ptr %3, align 8
  %4 = load i64, ptr %_2, align 8, !range !11, !noundef !3
  %5 = icmp eq i64 %4, -9223372036854775807
  %_4 = select i1 %5, i64 0, i64 1
  switch i64 %_4, label %bb4 [
    i64 1, label %bb2
    i64 0, label %bb3
  ]

bb4:                                              ; preds = %start
  unreachable

bb2:                                              ; preds = %start
  %err.0 = load i64, ptr %_2, align 8, !range !9, !noundef !3
  %6 = getelementptr inbounds i8, ptr %_2, i64 8
  %err.1 = load i64, ptr %6, align 8
; call alloc::raw_vec::handle_error
  call void @_ZN5alloc7raw_vec12handle_error17h22fdf317f3a37641E(i64 noundef %err.0, i64 %err.1) #21
  unreachable

bb3:                                              ; preds = %start
  call void @llvm.lifetime.end.p0(i64 16, ptr %_2)
  ret void
}

; <alloc::alloc::Global as core::alloc::Allocator>::deallocate
; Function Attrs: inlinehint nounwind
define internal void @"_ZN63_$LT$alloc..alloc..Global$u20$as$u20$core..alloc..Allocator$GT$10deallocate17h6b30618160528bb2E"(ptr noalias noundef nonnull readonly align 1 %self, ptr noundef nonnull %ptr, i64 noundef %0, i64 noundef %1) unnamed_addr #0 {
start:
  %_14 = alloca [8 x i8], align 8
  %layout1 = alloca [16 x i8], align 8
  %layout = alloca [16 x i8], align 8
  store i64 %0, ptr %layout, align 8
  %2 = getelementptr inbounds i8, ptr %layout, i64 8
  store i64 %1, ptr %2, align 8
  %3 = getelementptr inbounds i8, ptr %layout, i64 8
  %_4 = load i64, ptr %3, align 8, !noundef !3
  %4 = icmp eq i64 %_4, 0
  br i1 %4, label %bb2, label %bb1

bb2:                                              ; preds = %start
  br label %bb3

bb1:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 16, ptr %layout1)
  %5 = load i64, ptr %layout, align 8, !range !8, !noundef !3
  %6 = getelementptr inbounds i8, ptr %layout, i64 8
  %7 = load i64, ptr %6, align 8, !noundef !3
  store i64 %5, ptr %layout1, align 8
  %8 = getelementptr inbounds i8, ptr %layout1, i64 8
  store i64 %7, ptr %8, align 8
  %9 = getelementptr inbounds i8, ptr %layout1, i64 8
  %_9 = load i64, ptr %9, align 8, !noundef !3
  %self2 = load i64, ptr %layout1, align 8, !range !8, !noundef !3
  call void @llvm.lifetime.start.p0(i64 8, ptr %_14)
  store i64 %self2, ptr %_14, align 8
  %_15 = load i64, ptr %_14, align 8, !range !8, !noundef !3
  %_16 = icmp uge i64 %_15, 1
  %_17 = icmp ule i64 %_15, -9223372036854775808
  %_18 = and i1 %_16, %_17
  call void @llvm.assume(i1 %_18)
  call void @llvm.lifetime.end.p0(i64 8, ptr %_14)
  call void @__rust_dealloc(ptr noundef %ptr, i64 noundef %_9, i64 noundef %_15) #22
  call void @llvm.lifetime.end.p0(i64 16, ptr %layout1)
  br label %bb3

bb3:                                              ; preds = %bb1, %bb2
  ret void
}

; <alloc::alloc::Global as core::alloc::Allocator>::grow
; Function Attrs: inlinehint nounwind
define internal { ptr, i64 } @"_ZN63_$LT$alloc..alloc..Global$u20$as$u20$core..alloc..Allocator$GT$4grow17h26b309edff39b183E"(ptr noalias noundef nonnull readonly align 1 %self, ptr noundef nonnull %ptr, i64 noundef %old_layout.0, i64 noundef %old_layout.1, i64 noundef %new_layout.0, i64 noundef %new_layout.1) unnamed_addr #0 {
start:
; call alloc::alloc::Global::grow_impl
  %0 = call { ptr, i64 } @_ZN5alloc5alloc6Global9grow_impl17h902bcec4ef6d3724E(ptr noalias noundef nonnull readonly align 1 %self, ptr noundef nonnull %ptr, i64 noundef %old_layout.0, i64 noundef %old_layout.1, i64 noundef %new_layout.0, i64 noundef %new_layout.1, i1 noundef zeroext false) #22
  %_0.0 = extractvalue { ptr, i64 } %0, 0
  %_0.1 = extractvalue { ptr, i64 } %0, 1
  %1 = insertvalue { ptr, i64 } poison, ptr %_0.0, 0
  %2 = insertvalue { ptr, i64 } %1, i64 %_0.1, 1
  ret { ptr, i64 } %2
}

; <alloc::alloc::Global as core::alloc::Allocator>::allocate
; Function Attrs: inlinehint nounwind
define internal { ptr, i64 } @"_ZN63_$LT$alloc..alloc..Global$u20$as$u20$core..alloc..Allocator$GT$8allocate17h86fb36cfb6510ed6E"(ptr noalias noundef nonnull readonly align 1 %self, i64 noundef %layout.0, i64 noundef %layout.1) unnamed_addr #0 {
start:
; call alloc::alloc::Global::alloc_impl
  %0 = call { ptr, i64 } @_ZN5alloc5alloc6Global10alloc_impl17hcabadc4f9dbcac44E(ptr noalias noundef nonnull readonly align 1 %self, i64 noundef %layout.0, i64 noundef %layout.1, i1 noundef zeroext false) #22
  %_0.0 = extractvalue { ptr, i64 } %0, 0
  %_0.1 = extractvalue { ptr, i64 } %0, 1
  %1 = insertvalue { ptr, i64 } poison, ptr %_0.0, 0
  %2 = insertvalue { ptr, i64 } %1, i64 %_0.1, 1
  ret { ptr, i64 } %2
}

; <alloc::rc::RcBox<T> as alloc::rc::RcInnerPtr>::strong_ref
; Function Attrs: alwaysinline nounwind
define internal noundef nonnull align 8 ptr @"_ZN67_$LT$alloc..rc..RcBox$LT$T$GT$$u20$as$u20$alloc..rc..RcInnerPtr$GT$10strong_ref17h82e62e0b81e90042E"(ptr noundef nonnull align 8 %self) unnamed_addr #2 {
start:
  ret ptr %self
}

; <alloc::rc::RcBox<T> as alloc::rc::RcInnerPtr>::strong_ref
; Function Attrs: alwaysinline nounwind
define internal noundef nonnull align 8 ptr @"_ZN67_$LT$alloc..rc..RcBox$LT$T$GT$$u20$as$u20$alloc..rc..RcInnerPtr$GT$10strong_ref17hce387b9138991019E"(ptr noundef nonnull align 8 %self) unnamed_addr #2 {
start:
  ret ptr %self
}

; <alloc::vec::Vec<T,A> as core::ops::drop::Drop>::drop
; Function Attrs: nounwind
define internal void @"_ZN70_$LT$alloc..vec..Vec$LT$T$C$A$GT$$u20$as$u20$core..ops..drop..Drop$GT$4drop17h2fce56f4d16a6d65E"(ptr noalias noundef align 8 dereferenceable(24) %self) unnamed_addr #1 {
start:
  %0 = getelementptr inbounds i8, ptr %self, i64 8
  %self1 = load ptr, ptr %0, align 8, !nonnull !3, !noundef !3
  %1 = getelementptr inbounds i8, ptr %self, i64 16
  %len = load i64, ptr %1, align 8, !noundef !3
  ret void
}

; <core::option::Option<T> as core::cmp::PartialEq>::eq
; Function Attrs: inlinehint nounwind
define internal noundef zeroext i1 @"_ZN70_$LT$core..option..Option$LT$T$GT$$u20$as$u20$core..cmp..PartialEq$GT$2eq17hfcb7eaf5a0c0eea2E"(ptr noalias noundef readonly align 1 dereferenceable(1) %self, ptr noalias noundef readonly align 1 dereferenceable(1) %other) unnamed_addr #0 {
start:
  %_0 = alloca [1 x i8], align 1
  %0 = load i8, ptr %self, align 1, !range !12, !noundef !3
  %1 = icmp eq i8 %0, 2
  %_5 = select i1 %1, i64 0, i64 1
  switch i64 %_5, label %bb1 [
    i64 0, label %bb3
    i64 1, label %bb2
  ]

bb1:                                              ; preds = %bb2, %bb3, %start
  unreachable

bb3:                                              ; preds = %start
  %2 = load i8, ptr %other, align 1, !range !12, !noundef !3
  %3 = icmp eq i8 %2, 2
  %_4 = select i1 %3, i64 0, i64 1
  switch i64 %_4, label %bb1 [
    i64 0, label %bb4
    i64 1, label %bb8
  ]

bb2:                                              ; preds = %start
  %4 = load i8, ptr %other, align 1, !range !12, !noundef !3
  %5 = icmp eq i8 %4, 2
  %_3 = select i1 %5, i64 0, i64 1
  switch i64 %_3, label %bb1 [
    i64 0, label %bb7
    i64 1, label %bb5
  ]

bb4:                                              ; preds = %bb3
  store i8 1, ptr %_0, align 1
  br label %bb9

bb8:                                              ; preds = %bb3
  store i8 0, ptr %_0, align 1
  br label %bb9

bb9:                                              ; preds = %bb5, %bb7, %bb8, %bb4
  %6 = load i8, ptr %_0, align 1, !range !4, !noundef !3
  %7 = trunc i8 %6 to i1
  ret i1 %7

bb7:                                              ; preds = %bb2
  store i8 0, ptr %_0, align 1
  br label %bb9

bb5:                                              ; preds = %bb2
; call core::cmp::impls::<impl core::cmp::PartialEq for bool>::eq
  %8 = call noundef zeroext i1 @"_ZN4core3cmp5impls55_$LT$impl$u20$core..cmp..PartialEq$u20$for$u20$bool$GT$2eq17hc3a2858fc4477333E"(ptr noalias noundef readonly align 1 dereferenceable(1) %self, ptr noalias noundef readonly align 1 dereferenceable(1) %other) #22
  %9 = zext i1 %8 to i8
  store i8 %9, ptr %_0, align 1
  br label %bb9
}

; <solana_account_info::AccountInfo as core::clone::Clone>::clone
; Function Attrs: inlinehint nounwind
define internal void @"_ZN71_$LT$solana_account_info..AccountInfo$u20$as$u20$core..clone..Clone$GT$5clone17h759150bcde62cc00E"(ptr dead_on_unwind noalias nocapture noundef writable sret([48 x i8]) align 8 dereferenceable(48) %_0, ptr noalias noundef readonly align 8 dereferenceable(48) %self) unnamed_addr #0 {
start:
  %_4 = alloca [8 x i8], align 8
  %_3 = alloca [8 x i8], align 8
  %_2 = load ptr, ptr %self, align 8, !nonnull !3, !align !6, !noundef !3
  call void @llvm.lifetime.start.p0(i64 8, ptr %_3)
  %0 = getelementptr inbounds i8, ptr %self, i64 8
  %_12 = load ptr, ptr %0, align 8, !nonnull !3, !noundef !3
; call alloc::rc::RcInnerPtr::inc_strong
  call void @_ZN5alloc2rc10RcInnerPtr10inc_strong17h3d0774391efcf2ceE(ptr noundef nonnull align 8 %_12) #22
  store ptr %_12, ptr %_3, align 8
  call void @llvm.lifetime.start.p0(i64 8, ptr %_4)
  %1 = getelementptr inbounds i8, ptr %self, i64 16
  %_16 = load ptr, ptr %1, align 8, !nonnull !3, !noundef !3
; call alloc::rc::RcInnerPtr::inc_strong
  call void @_ZN5alloc2rc10RcInnerPtr10inc_strong17h18d97276b6a6692fE(ptr noundef nonnull align 8 %_16) #22
  store ptr %_16, ptr %_4, align 8
  %2 = getelementptr inbounds i8, ptr %self, i64 24
  %_5 = load ptr, ptr %2, align 8, !nonnull !3, !align !6, !noundef !3
  %3 = getelementptr inbounds i8, ptr %self, i64 32
  %_6 = load i64, ptr %3, align 8, !noundef !3
  %4 = getelementptr inbounds i8, ptr %self, i64 40
  %5 = load i8, ptr %4, align 8, !range !4, !noundef !3
  %_7 = trunc i8 %5 to i1
  %6 = getelementptr inbounds i8, ptr %self, i64 41
  %7 = load i8, ptr %6, align 1, !range !4, !noundef !3
  %_8 = trunc i8 %7 to i1
  %8 = getelementptr inbounds i8, ptr %self, i64 42
  %9 = load i8, ptr %8, align 2, !range !4, !noundef !3
  %_9 = trunc i8 %9 to i1
  store ptr %_2, ptr %_0, align 8
  %10 = load ptr, ptr %_3, align 8, !nonnull !3, !noundef !3
  %11 = getelementptr inbounds i8, ptr %_0, i64 8
  store ptr %10, ptr %11, align 8
  %12 = load ptr, ptr %_4, align 8, !nonnull !3, !noundef !3
  %13 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %12, ptr %13, align 8
  %14 = getelementptr inbounds i8, ptr %_0, i64 24
  store ptr %_5, ptr %14, align 8
  %15 = getelementptr inbounds i8, ptr %_0, i64 32
  store i64 %_6, ptr %15, align 8
  %16 = getelementptr inbounds i8, ptr %_0, i64 40
  %17 = zext i1 %_7 to i8
  store i8 %17, ptr %16, align 8
  %18 = getelementptr inbounds i8, ptr %_0, i64 41
  %19 = zext i1 %_8 to i8
  store i8 %19, ptr %18, align 1
  %20 = getelementptr inbounds i8, ptr %_0, i64 42
  %21 = zext i1 %_9 to i8
  store i8 %21, ptr %20, align 2
  call void @llvm.lifetime.end.p0(i64 8, ptr %_4)
  call void @llvm.lifetime.end.p0(i64 8, ptr %_3)
  ret void
}

; <&mut W as core::fmt::Write::write_fmt::SpecWriteFmt>::spec_write_fmt
; Function Attrs: inlinehint nounwind
define internal noundef zeroext i1 @"_ZN75_$LT$$RF$mut$u20$W$u20$as$u20$core..fmt..Write..write_fmt..SpecWriteFmt$GT$14spec_write_fmt17haafb67d99364a4b3E"(ptr noalias noundef align 8 dereferenceable(24) %self, ptr noalias nocapture noundef readonly align 8 dereferenceable(48) %args) unnamed_addr #0 {
start:
  %_8 = alloca [48 x i8], align 8
  %_3 = alloca [16 x i8], align 8
  %_0 = alloca [1 x i8], align 1
  call void @llvm.lifetime.start.p0(i64 16, ptr %_3)
; call core::fmt::Arguments::as_statically_known_str
  %0 = call { ptr, i64 } @_ZN4core3fmt9Arguments23as_statically_known_str17h724859523fc262c5E(ptr noalias noundef readonly align 8 dereferenceable(48) %args) #22
  %1 = extractvalue { ptr, i64 } %0, 0
  %2 = extractvalue { ptr, i64 } %0, 1
  store ptr %1, ptr %_3, align 8
  %3 = getelementptr inbounds i8, ptr %_3, i64 8
  store i64 %2, ptr %3, align 8
  %4 = load ptr, ptr %_3, align 8, !noundef !3
  %5 = ptrtoint ptr %4 to i64
  %6 = icmp eq i64 %5, 0
  %_5 = select i1 %6, i64 0, i64 1
  switch i64 %_5, label %bb6 [
    i64 1, label %bb2
    i64 0, label %bb3
  ]

bb6:                                              ; preds = %start
  unreachable

bb2:                                              ; preds = %start
  %s.0 = load ptr, ptr %_3, align 8, !nonnull !3, !align !6, !noundef !3
  %7 = getelementptr inbounds i8, ptr %_3, i64 8
  %s.1 = load i64, ptr %7, align 8, !noundef !3
; call <alloc::string::String as core::fmt::Write>::write_str
  %8 = call noundef zeroext i1 @"_ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$9write_str17h4b62f46a222bd5b2E"(ptr noalias noundef align 8 dereferenceable(24) %self, ptr noalias noundef nonnull readonly align 1 %s.0, i64 noundef %s.1) #22
  %9 = zext i1 %8 to i8
  store i8 %9, ptr %_0, align 1
  br label %bb5

bb3:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 48, ptr %_8)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_8, ptr align 8 %args, i64 48, i1 false)
; call core::fmt::write
  %10 = call noundef zeroext i1 @_ZN4core3fmt5write17h7d5c5d972f6bf082E(ptr noundef nonnull align 1 %self, ptr noalias noundef readonly align 8 dereferenceable(24) @vtable.0, ptr noalias nocapture noundef readonly align 8 dereferenceable(48) %_8) #22
  %11 = zext i1 %10 to i8
  store i8 %11, ptr %_0, align 1
  call void @llvm.lifetime.end.p0(i64 48, ptr %_8)
  br label %bb5

bb5:                                              ; preds = %bb3, %bb2
  call void @llvm.lifetime.end.p0(i64 16, ptr %_3)
  %12 = load i8, ptr %_0, align 1, !range !4, !noundef !3
  %13 = trunc i8 %12 to i1
  ret i1 %13
}

; <alloc::raw_vec::RawVec<T,A> as core::ops::drop::Drop>::drop
; Function Attrs: nounwind
define internal void @"_ZN77_$LT$alloc..raw_vec..RawVec$LT$T$C$A$GT$$u20$as$u20$core..ops..drop..Drop$GT$4drop17h3b9335e739eb6028E"(ptr noalias noundef align 8 dereferenceable(16) %self) unnamed_addr #1 {
start:
  %_2 = alloca [24 x i8], align 8
  call void @llvm.lifetime.start.p0(i64 24, ptr %_2)
; call alloc::raw_vec::RawVec<T,A>::current_memory
  call void @"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14current_memory17hc167f39406d68977E"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_2, ptr noalias noundef readonly align 8 dereferenceable(16) %self) #22
  %0 = getelementptr inbounds i8, ptr %_2, i64 8
  %1 = load i64, ptr %0, align 8, !range !9, !noundef !3
  %2 = icmp eq i64 %1, 0
  %_4 = select i1 %2, i64 0, i64 1
  switch i64 %_4, label %bb5 [
    i64 1, label %bb2
    i64 0, label %bb4
  ]

bb5:                                              ; preds = %start
  unreachable

bb2:                                              ; preds = %start
  %ptr = load ptr, ptr %_2, align 8, !nonnull !3, !noundef !3
  %3 = getelementptr inbounds i8, ptr %_2, i64 8
  %layout.0 = load i64, ptr %3, align 8, !range !8, !noundef !3
  %4 = getelementptr inbounds i8, ptr %3, i64 8
  %layout.1 = load i64, ptr %4, align 8, !noundef !3
  %_7 = getelementptr inbounds i8, ptr %self, i64 16
; call <alloc::alloc::Global as core::alloc::Allocator>::deallocate
  call void @"_ZN63_$LT$alloc..alloc..Global$u20$as$u20$core..alloc..Allocator$GT$10deallocate17h6b30618160528bb2E"(ptr noalias noundef nonnull readonly align 1 %_7, ptr noundef nonnull %ptr, i64 noundef %layout.0, i64 noundef %layout.1) #22
  br label %bb4

bb4:                                              ; preds = %bb2, %start
  call void @llvm.lifetime.end.p0(i64 24, ptr %_2)
  ret void
}

; Function Attrs: nounwind
define void @main34_validate(ptr dead_on_unwind noalias nocapture noundef writable sret([40 x i8]) align 8 dereferenceable(40) %_0, ptr noalias noundef readonly align 8 dereferenceable(48) %st, i8 noundef %0, i64 noundef %1, i64 %2, ptr noalias nocapture noundef align 1 dereferenceable(33) %new, ptr noalias noundef readonly align 1 dereferenceable(32) %holder_key, ptr noalias noundef readonly align 1 dereferenceable(32) %sharing) unnamed_addr #1 {
start:
  %3 = alloca [1 x i8], align 1
  %4 = alloca [1 x i8], align 1
  %5 = alloca [1 x i8], align 1
  %6 = alloca [1 x i8], align 1
  %7 = alloca [1 x i8], align 1
  %8 = alloca [1 x i8], align 1
  %9 = alloca [1 x i8], align 1
  %10 = alloca [1 x i8], align 1
  %11 = alloca [1 x i8], align 1
  %12 = alloca [1 x i8], align 1
  %13 = alloca [1 x i8], align 1
  %14 = alloca [1 x i8], align 1
  %15 = alloca [1 x i8], align 1
  %16 = alloca [1 x i8], align 1
  %_233 = alloca [32 x i8], align 1
  %_232 = alloca [32 x i8], align 1
  %_231 = alloca [32 x i8], align 1
  %_218 = alloca [32 x i8], align 1
  %_215 = alloca [32 x i8], align 1
  %_213 = alloca [1 x i8], align 1
  %_207 = alloca [32 x i8], align 1
  %b2 = alloca [32 x i8], align 1
  %_201 = alloca [32 x i8], align 1
  %_197 = alloca [72 x i8], align 8
  %_196 = alloca [24 x i8], align 8
  %_195 = alloca [32 x i8], align 8
  %_194 = alloca [32 x i8], align 8
  %_193 = alloca [24 x i8], align 8
  %_191 = alloca [24 x i8], align 8
  %_190 = alloca [160 x i8], align 8
  %_186 = alloca [72 x i8], align 8
  %_185 = alloca [24 x i8], align 8
  %_184 = alloca [32 x i8], align 8
  %_183 = alloca [32 x i8], align 8
  %_182 = alloca [24 x i8], align 8
  %_180 = alloca [24 x i8], align 8
  %_179 = alloca [160 x i8], align 8
  %_173 = alloca [72 x i8], align 8
  %_172 = alloca [24 x i8], align 8
  %_171 = alloca [32 x i8], align 8
  %_170 = alloca [32 x i8], align 8
  %_169 = alloca [24 x i8], align 8
  %_167 = alloca [24 x i8], align 8
  %_166 = alloca [160 x i8], align 8
  %_163 = alloca [72 x i8], align 8
  %_162 = alloca [24 x i8], align 8
  %_161 = alloca [32 x i8], align 8
  %_160 = alloca [32 x i8], align 8
  %_159 = alloca [24 x i8], align 8
  %_157 = alloca [24 x i8], align 8
  %_156 = alloca [160 x i8], align 8
  %_154 = alloca [1 x i8], align 1
  %f = alloca [8 x i8], align 8
  %_152 = alloca [8 x i8], align 8
  %cashback = alloca [1 x i8], align 1
  %b1 = alloca [32 x i8], align 1
  %_137 = alloca [72 x i8], align 8
  %_136 = alloca [24 x i8], align 8
  %_135 = alloca [32 x i8], align 8
  %_134 = alloca [32 x i8], align 8
  %_133 = alloca [24 x i8], align 8
  %_131 = alloca [24 x i8], align 8
  %_130 = alloca [160 x i8], align 8
  %_96 = alloca [32 x i8], align 1
  %_95 = alloca [32 x i8], align 1
  %_94 = alloca [64 x i8], align 1
  %_93 = alloca [72 x i8], align 8
  %_92 = alloca [24 x i8], align 8
  %_91 = alloca [32 x i8], align 8
  %_90 = alloca [32 x i8], align 8
  %_89 = alloca [24 x i8], align 8
  %_87 = alloca [24 x i8], align 8
  %_86 = alloca [160 x i8], align 8
  %_83 = alloca [32 x i8], align 1
  %_77 = alloca [72 x i8], align 8
  %_76 = alloca [24 x i8], align 8
  %_75 = alloca [32 x i8], align 8
  %_74 = alloca [32 x i8], align 8
  %_73 = alloca [24 x i8], align 8
  %_71 = alloca [24 x i8], align 8
  %_70 = alloca [160 x i8], align 8
  %t = alloca [32 x i8], align 1
  %b = alloca [32 x i8], align 1
  %_56 = alloca [72 x i8], align 8
  %_55 = alloca [24 x i8], align 8
  %_54 = alloca [32 x i8], align 8
  %_53 = alloca [32 x i8], align 8
  %_52 = alloca [24 x i8], align 8
  %_50 = alloca [24 x i8], align 8
  %_49 = alloca [160 x i8], align 8
  %_47 = alloca [72 x i8], align 8
  %_46 = alloca [24 x i8], align 8
  %_45 = alloca [32 x i8], align 8
  %_44 = alloca [32 x i8], align 8
  %_43 = alloca [24 x i8], align 8
  %_41 = alloca [24 x i8], align 8
  %_40 = alloca [160 x i8], align 8
  %_33 = alloca [72 x i8], align 8
  %_32 = alloca [24 x i8], align 8
  %_31 = alloca [32 x i8], align 8
  %_30 = alloca [32 x i8], align 8
  %_29 = alloca [24 x i8], align 8
  %_27 = alloca [24 x i8], align 8
  %_26 = alloca [160 x i8], align 8
  %target_tail = alloca [25 x i8], align 1
  %target_head = alloca [7 x i8], align 1
  %_18 = alloca [72 x i8], align 8
  %_17 = alloca [24 x i8], align 8
  %_16 = alloca [32 x i8], align 8
  %_15 = alloca [32 x i8], align 8
  %_14 = alloca [24 x i8], align 8
  %_12 = alloca [24 x i8], align 8
  %_11 = alloca [160 x i8], align 8
  %fee = alloca [16 x i8], align 8
  %hopt = alloca [1 x i8], align 1
  store i8 %0, ptr %hopt, align 1
  store i64 %1, ptr %fee, align 8
  %17 = getelementptr inbounds i8, ptr %fee, i64 8
  store i64 %2, ptr %17, align 8
; call <core::option::Option<T> as core::cmp::PartialEq>::eq
  %holder = call noundef zeroext i1 @"_ZN70_$LT$core..option..Option$LT$T$GT$$u20$as$u20$core..cmp..PartialEq$GT$2eq17hfcb7eaf5a0c0eea2E"(ptr noalias noundef readonly align 1 dereferenceable(1) %hopt, ptr noalias noundef readonly align 1 dereferenceable(1) @alloc_8821998f047ca62cad40e6bc4e4d87c4) #22
  %18 = getelementptr inbounds i8, ptr %st, i64 40
  %19 = load i8, ptr %18, align 8, !range !4, !noundef !3
  %_9 = trunc i8 %19 to i1
  br i1 %_9, label %bb2, label %bb6

bb6:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 7, ptr %target_head)
  call void @llvm.lifetime.start.p0(i64 25, ptr %target_tail)
  %20 = getelementptr inbounds i8, ptr %st, i64 41
  %21 = load i8, ptr %20, align 1, !range !4, !noundef !3
  %_22 = trunc i8 %21 to i1
  %_21 = zext i1 %_22 to i8
  %22 = icmp eq i8 %_21, 1
  br i1 %22, label %bb8, label %bb7

bb2:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 160, ptr %_11)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_12)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_12, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_eb4f91695bc6f999067c65f428fcc4d8) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_13 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 88) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_14)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_14, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_eb4f91695bc6f999067c65f428fcc4d8) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_15)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_16)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_17)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_17, align 8
  %23 = getelementptr inbounds i8, ptr %_17, i64 8
  store i64 103, ptr %23, align 8
  %24 = getelementptr inbounds i8, ptr %_17, i64 16
  store i32 19, ptr %24, align 8
  %25 = getelementptr inbounds i8, ptr %_16, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %25, ptr align 8 %_17, i64 24, i1 false)
  store i64 0, ptr %_16, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_17)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_15, ptr align 8 %_16, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_16)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_18)
  store i8 2, ptr %_18, align 8
  %26 = getelementptr inbounds i8, ptr %_11, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %26, ptr align 8 %_12, i64 24, i1 false)
  %27 = getelementptr inbounds i8, ptr %_11, i64 152
  store i32 %_13, ptr %27, align 8
  %28 = getelementptr inbounds i8, ptr %_11, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %28, ptr align 8 %_14, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_11, ptr align 8 %_15, i64 32, i1 false)
  %29 = getelementptr inbounds i8, ptr %_11, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %29, ptr align 8 %_18, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_18)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_15)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_14)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_12)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %30 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_11) #22
  %_10.0 = extractvalue { i64, ptr } %30, 0
  %_10.1 = extractvalue { i64, ptr } %30, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_11)
  %31 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_10.0, ptr %31, align 8
  %32 = getelementptr inbounds i8, ptr %31, i64 8
  store ptr %_10.1, ptr %32, align 8
  store i8 1, ptr %_0, align 8
  br label %bb85

bb8:                                              ; preds = %bb6
; call <core::option::Option<T> as core::cmp::PartialEq>::eq
  %_23 = call noundef zeroext i1 @"_ZN70_$LT$core..option..Option$LT$T$GT$$u20$as$u20$core..cmp..PartialEq$GT$2eq17hfcb7eaf5a0c0eea2E"(ptr noalias noundef readonly align 1 dereferenceable(1) %hopt, ptr noalias noundef readonly align 1 dereferenceable(1) @alloc_8821998f047ca62cad40e6bc4e4d87c4) #22
  br i1 %_23, label %bb10, label %bb11

bb7:                                              ; preds = %bb6
  %_37 = call noundef zeroext i1 @llvm.expect.with.probability.i1(i1 noundef zeroext %holder, i1 noundef zeroext true, double noundef 4.900000e-01) #22
  br i1 %_37, label %bb16, label %bb22

bb11:                                             ; preds = %bb8
  call void @llvm.lifetime.start.p0(i64 160, ptr %_26)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_27)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_27, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_8f95cb73e89711d65e95d13598508b19) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_28 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 83) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_29)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_29, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_8f95cb73e89711d65e95d13598508b19) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_30)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_31)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_32)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_32, align 8
  %33 = getelementptr inbounds i8, ptr %_32, i64 8
  store i64 103, ptr %33, align 8
  %34 = getelementptr inbounds i8, ptr %_32, i64 16
  store i32 24, ptr %34, align 8
  %35 = getelementptr inbounds i8, ptr %_31, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %35, ptr align 8 %_32, i64 24, i1 false)
  store i64 0, ptr %_31, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_32)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_30, ptr align 8 %_31, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_31)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_33)
  store i8 2, ptr %_33, align 8
  %36 = getelementptr inbounds i8, ptr %_26, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %36, ptr align 8 %_27, i64 24, i1 false)
  %37 = getelementptr inbounds i8, ptr %_26, i64 152
  store i32 %_28, ptr %37, align 8
  %38 = getelementptr inbounds i8, ptr %_26, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %38, ptr align 8 %_29, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_26, ptr align 8 %_30, i64 32, i1 false)
  %39 = getelementptr inbounds i8, ptr %_26, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %39, ptr align 8 %_33, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_33)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_30)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_29)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_27)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %40 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_26) #22
  %e.0 = extractvalue { i64, ptr } %40, 0
  %e.1 = extractvalue { i64, ptr } %40, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_26)
  call void @llvm.lifetime.start.p0(i64 1, ptr %16)
  %41 = load volatile i8, ptr %holder_key, align 1
  store i8 %41, ptr %16, align 1
  %_34 = load i8, ptr %16, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %16)
  %42 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %e.0, ptr %42, align 8
  %43 = getelementptr inbounds i8, ptr %42, i64 8
  store ptr %e.1, ptr %43, align 8
  store i8 1, ptr %_0, align 8
  br label %bb82

bb10:                                             ; preds = %bb8
  br label %bb23

bb82:                                             ; preds = %bb17, %bb11
  br label %bb83

bb23:                                             ; preds = %bb21, %bb10
  %44 = load i8, ptr %new, align 1, !range !4, !noundef !3
  %45 = trunc i8 %44 to i1
  %_208 = zext i1 %45 to i64
  switch i64 %_208, label %bb55 [
    i64 1, label %bb91
    i64 0, label %bb90
  ]

bb22:                                             ; preds = %bb7
  call void @llvm.lifetime.end.p0(i64 noundef 7, ptr noundef %target_head) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %t)
  call void @llvm.lifetime.start.p0(i64 1, ptr %_213)
  %46 = load i8, ptr %new, align 1, !range !4, !noundef !3
  %47 = trunc i8 %46 to i1
  %_214 = zext i1 %47 to i64
  switch i64 %_214, label %bb55 [
    i64 1, label %bb95
    i64 0, label %bb94
  ]

bb16:                                             ; preds = %bb7
  %48 = getelementptr inbounds i8, ptr %st, i64 44
  %49 = load i8, ptr %48, align 4, !range !4, !noundef !3
  %_38 = trunc i8 %49 to i1
  br i1 %_38, label %bb21, label %bb17

bb55:                                             ; preds = %bb53, %bb54, %bb23, %bb22
  unreachable

bb95:                                             ; preds = %bb22
  store i8 1, ptr %_213, align 1
  br label %bb93

bb94:                                             ; preds = %bb22
  store i8 0, ptr %_213, align 1
  br label %bb93

bb93:                                             ; preds = %bb94, %bb95
  %50 = load i8, ptr %_213, align 1, !range !4, !noundef !3
  %51 = trunc i8 %50 to i1
  %_68 = xor i1 %51, true
  call void @llvm.lifetime.end.p0(i64 1, ptr %_213)
  %_67 = call noundef zeroext i1 @llvm.expect.with.probability.i1(i1 noundef zeroext %_68, i1 noundef zeroext true, double noundef 7.500000e-01) #22
  br i1 %_67, label %bb29, label %bb33

bb33:                                             ; preds = %bb93
  %_79 = getelementptr inbounds i8, ptr %new, i64 1
; call core::ptr::read_unaligned
  call void @_ZN4core3ptr14read_unaligned17hfb0286d8a885119bE(ptr noalias nocapture noundef sret([32 x i8]) align 1 dereferenceable(32) %t, ptr noundef %_79) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_83)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_215)
; call core::array::<impl core::default::Default for [T; 32]>::default
  call void @"_ZN4core5array76_$LT$impl$u20$core..default..Default$u20$for$u20$$u5b$T$u3b$$u20$32$u5d$$GT$7default17hf39cfabd391f7201E"(ptr noalias nocapture noundef sret([32 x i8]) align 1 dereferenceable(32) %_215) #22
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_83, ptr align 1 %_215, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_215)
  call void @llvm.lifetime.start.p0(i64 1, ptr %15)
  %52 = call i32 @memcmp(ptr %t, ptr %_83, i64 32)
  %53 = icmp eq i32 %52, 0
  %54 = zext i1 %53 to i8
  store i8 %54, ptr %15, align 1
  %55 = load i8, ptr %15, align 1, !range !4, !noundef !3
  %_82 = trunc i8 %55 to i1
  call void @llvm.lifetime.end.p0(i64 1, ptr %15)
  br i1 %_82, label %bb35, label %bb40

bb29:                                             ; preds = %bb93
  call void @llvm.lifetime.start.p0(i64 160, ptr %_70)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_71)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_71, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_1ba5e1e397ae92b788c97e688ac0b362) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_72 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 89) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_73)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_73, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_1ba5e1e397ae92b788c97e688ac0b362) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_74)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_75)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_76)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_76, align 8
  %56 = getelementptr inbounds i8, ptr %_76, i64 8
  store i64 103, ptr %56, align 8
  %57 = getelementptr inbounds i8, ptr %_76, i64 16
  store i32 41, ptr %57, align 8
  %58 = getelementptr inbounds i8, ptr %_75, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %58, ptr align 8 %_76, i64 24, i1 false)
  store i64 0, ptr %_75, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_76)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_74, ptr align 8 %_75, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_75)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_77)
  store i8 2, ptr %_77, align 8
  %59 = getelementptr inbounds i8, ptr %_70, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %59, ptr align 8 %_71, i64 24, i1 false)
  %60 = getelementptr inbounds i8, ptr %_70, i64 152
  store i32 %_72, ptr %60, align 8
  %61 = getelementptr inbounds i8, ptr %_70, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %61, ptr align 8 %_73, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_70, ptr align 8 %_74, i64 32, i1 false)
  %62 = getelementptr inbounds i8, ptr %_70, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %62, ptr align 8 %_77, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_77)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_74)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_73)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_71)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %63 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_70) #22
  %_69.0 = extractvalue { i64, ptr } %63, 0
  %_69.1 = extractvalue { i64, ptr } %63, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_70)
  %64 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_69.0, ptr %64, align 8
  %65 = getelementptr inbounds i8, ptr %64, i64 8
  store ptr %_69.1, ptr %65, align 8
  store i8 1, ptr %_0, align 8
  br label %bb81

bb40:                                             ; preds = %bb33
  call void @llvm.lifetime.end.p0(i64 32, ptr %_83)
  call void @llvm.lifetime.start.p0(i64 1, ptr %14)
  %66 = call i32 @memcmp(ptr %t, ptr %sharing, i64 32)
  %67 = icmp eq i32 %66, 0
  %68 = zext i1 %67 to i8
  store i8 %68, ptr %14, align 1
  %69 = load i8, ptr %14, align 1, !range !4, !noundef !3
  %_102 = trunc i8 %69 to i1
  call void @llvm.lifetime.end.p0(i64 1, ptr %14)
  %_101 = zext i1 %_102 to i8
  %_100 = call noundef zeroext i8 @llvm.bpf.passthrough.i8.i8(i32 noundef zeroext 4, i8 noundef zeroext %_101) #22
  %_99 = and i8 %_100, 1
  %_98 = icmp ne i8 %_99, 0
  %_97 = call noundef zeroext i1 @llvm.expect.with.probability.i1(i1 noundef zeroext %_98, i1 noundef zeroext true, double noundef 6.250000e-01) #22
  br i1 %_97, label %bb45, label %bb43

bb35:                                             ; preds = %bb33
  call void @llvm.lifetime.end.p0(i64 32, ptr %_83)
  call void @llvm.lifetime.start.p0(i64 160, ptr %_86)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_87)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_87, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_0e3505805f4905816c1bd644811a7869) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_88 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 30) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_89)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_89, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_0e3505805f4905816c1bd644811a7869) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_90)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_91)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_92)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_92, align 8
  %70 = getelementptr inbounds i8, ptr %_92, i64 8
  store i64 103, ptr %70, align 8
  %71 = getelementptr inbounds i8, ptr %_92, i64 16
  store i32 42, ptr %71, align 8
  %72 = getelementptr inbounds i8, ptr %_91, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %72, ptr align 8 %_92, i64 24, i1 false)
  store i64 0, ptr %_91, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_92)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_90, ptr align 8 %_91, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_91)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_93)
  store i8 2, ptr %_93, align 8
  %73 = getelementptr inbounds i8, ptr %_86, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %73, ptr align 8 %_87, i64 24, i1 false)
  %74 = getelementptr inbounds i8, ptr %_86, i64 152
  store i32 %_88, ptr %74, align 8
  %75 = getelementptr inbounds i8, ptr %_86, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %75, ptr align 8 %_89, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_86, ptr align 8 %_90, i64 32, i1 false)
  %76 = getelementptr inbounds i8, ptr %_86, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %76, ptr align 8 %_93, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_93)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_90)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_89)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_87)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %77 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_86) #22
  %_85.0 = extractvalue { i64, ptr } %77, 0
  %_85.1 = extractvalue { i64, ptr } %77, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_86)
  call void @llvm.lifetime.start.p0(i64 64, ptr %_94)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_95)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_95, ptr align 1 %t, i64 32, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_96)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_218)
; call core::array::<impl core::default::Default for [T; 32]>::default
  call void @"_ZN4core5array76_$LT$impl$u20$core..default..Default$u20$for$u20$$u5b$T$u3b$$u20$32$u5d$$GT$7default17hf39cfabd391f7201E"(ptr noalias nocapture noundef sret([32 x i8]) align 1 dereferenceable(32) %_218) #22
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_96, ptr align 1 %_218, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_218)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_94, ptr align 1 %_95, i64 32, i1 false)
  %78 = getelementptr inbounds i8, ptr %_94, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %78, ptr align 1 %_96, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_96)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_95)
; call anchor_lang::error::Error::with_pubkeys
  %79 = call { i64, ptr } @_ZN11anchor_lang5error5Error12with_pubkeys17hca6dbbbe6a9a5da7E(i64 noundef %_85.0, ptr noundef %_85.1, ptr noalias nocapture noundef readonly align 1 dereferenceable(64) %_94) #22
  %_84.0 = extractvalue { i64, ptr } %79, 0
  %_84.1 = extractvalue { i64, ptr } %79, 1
  call void @llvm.lifetime.end.p0(i64 64, ptr %_94)
  %80 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_84.0, ptr %80, align 8
  %81 = getelementptr inbounds i8, ptr %80, i64 8
  store ptr %_84.1, ptr %81, align 8
  store i8 1, ptr %_0, align 8
  br label %bb81

bb43:                                             ; preds = %bb40
  call void @llvm.lifetime.start.p0(i64 1, ptr %13)
  %82 = call i32 @memcmp(ptr %t, ptr %holder_key, i64 32)
  %83 = icmp eq i32 %82, 0
  %84 = zext i1 %83 to i8
  store i8 %84, ptr %13, align 1
  %85 = load i8, ptr %13, align 1, !range !4, !noundef !3
  %_104 = trunc i8 %85 to i1
  call void @llvm.lifetime.end.p0(i64 1, ptr %13)
  %_103 = call noundef zeroext i1 @llvm.expect.i1(i1 noundef zeroext %_104, i1 noundef zeroext false) #22
  br i1 %_103, label %bb45, label %bb49

bb45:                                             ; preds = %bb43, %bb40
  call void @llvm.lifetime.start.p0(i64 1, ptr %12)
  %86 = load volatile i8, ptr %holder_key, align 1
  store i8 %86, ptr %12, align 1
  %_105 = load i8, ptr %12, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %12)
  call void @llvm.lifetime.start.p0(i64 1, ptr %11)
  %87 = load volatile i8, ptr %holder_key, align 1
  store i8 %87, ptr %11, align 1
  %_108 = load i8, ptr %11, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %11)
  call void @llvm.lifetime.start.p0(i64 1, ptr %10)
  %88 = load volatile i8, ptr %holder_key, align 1
  store i8 %88, ptr %10, align 1
  %_111 = load i8, ptr %10, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %10)
  call void @llvm.lifetime.start.p0(i64 1, ptr %9)
  %89 = load volatile i8, ptr %holder_key, align 1
  store i8 %89, ptr %9, align 1
  %_114 = load i8, ptr %9, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %9)
  call void @llvm.lifetime.start.p0(i64 1, ptr %8)
  %90 = load volatile i8, ptr %holder_key, align 1
  store i8 %90, ptr %8, align 1
  %_117 = load i8, ptr %8, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %8)
  call void @llvm.lifetime.start.p0(i64 1, ptr %7)
  %91 = load volatile i8, ptr %holder_key, align 1
  store i8 %91, ptr %7, align 1
  %_120 = load i8, ptr %7, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %7)
  call void @llvm.lifetime.start.p0(i64 1, ptr %6)
  %92 = load volatile i8, ptr %holder_key, align 1
  store i8 %92, ptr %6, align 1
  %_123 = load i8, ptr %6, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %6)
  call void @llvm.lifetime.start.p0(i64 1, ptr %5)
  %93 = load volatile i8, ptr %holder_key, align 1
  store i8 %93, ptr %5, align 1
  %_126 = load i8, ptr %5, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %5)
  call void @llvm.lifetime.start.p0(i64 160, ptr %_130)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_131)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_131, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_861c8964bbad6d9cede9df277e628fe9) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_132 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 19) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_133)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_133, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_861c8964bbad6d9cede9df277e628fe9) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_134)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_135)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_136)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_136, align 8
  %94 = getelementptr inbounds i8, ptr %_136, i64 8
  store i64 103, ptr %94, align 8
  %95 = getelementptr inbounds i8, ptr %_136, i64 16
  store i32 47, ptr %95, align 8
  %96 = getelementptr inbounds i8, ptr %_135, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %96, ptr align 8 %_136, i64 24, i1 false)
  store i64 0, ptr %_135, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_136)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_134, ptr align 8 %_135, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_135)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_137)
  store i8 2, ptr %_137, align 8
  %97 = getelementptr inbounds i8, ptr %_130, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %97, ptr align 8 %_131, i64 24, i1 false)
  %98 = getelementptr inbounds i8, ptr %_130, i64 152
  store i32 %_132, ptr %98, align 8
  %99 = getelementptr inbounds i8, ptr %_130, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %99, ptr align 8 %_133, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_130, ptr align 8 %_134, i64 32, i1 false)
  %100 = getelementptr inbounds i8, ptr %_130, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %100, ptr align 8 %_137, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_137)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_134)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_133)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_131)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %101 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_130) #22
  %_129.0 = extractvalue { i64, ptr } %101, 0
  %_129.1 = extractvalue { i64, ptr } %101, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_130)
  %102 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_129.0, ptr %102, align 8
  %103 = getelementptr inbounds i8, ptr %102, i64 8
  store ptr %_129.1, ptr %103, align 8
  store i8 1, ptr %_0, align 8
  br label %bb81

bb49:                                             ; preds = %bb43
  call void @llvm.lifetime.start.p0(i64 noundef 7, ptr noundef %target_head) #22
  call void @llvm.lifetime.start.p0(i64 noundef 25, ptr noundef %target_tail) #22
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target_head, ptr align 1 %t, i64 7, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr %b1)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_232, ptr align 1 %t, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %b1, ptr align 1 %_232, i64 32, i1 false)
  %_146 = getelementptr inbounds i8, ptr %b1, i64 7
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target_tail, ptr align 1 %_146, i64 25, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %b1)
  call void @llvm.lifetime.end.p0(i64 32, ptr %t)
  br label %bb52

bb52:                                             ; preds = %bb90, %bb49
  call void @llvm.lifetime.start.p0(i64 1, ptr %cashback)
  br i1 %holder, label %bb53, label %bb54

bb81:                                             ; preds = %bb29, %bb35, %bb45
  call void @llvm.lifetime.end.p0(i64 32, ptr %t)
  br label %bb83

bb83:                                             ; preds = %bb91, %bb82, %bb81
  br label %bb84

bb17:                                             ; preds = %bb16
  call void @llvm.lifetime.start.p0(i64 160, ptr %_40)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_41)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_41, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_f94f166953c814e4161e699857179a1e) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_42 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 84) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_43)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_43, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_f94f166953c814e4161e699857179a1e) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_44)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_45)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_46)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_46, align 8
  %104 = getelementptr inbounds i8, ptr %_46, i64 8
  store i64 103, ptr %104, align 8
  %105 = getelementptr inbounds i8, ptr %_46, i64 16
  store i32 31, ptr %105, align 8
  %106 = getelementptr inbounds i8, ptr %_45, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %106, ptr align 8 %_46, i64 24, i1 false)
  store i64 0, ptr %_45, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_46)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_44, ptr align 8 %_45, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_45)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_47)
  store i8 2, ptr %_47, align 8
  %107 = getelementptr inbounds i8, ptr %_40, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %107, ptr align 8 %_41, i64 24, i1 false)
  %108 = getelementptr inbounds i8, ptr %_40, i64 152
  store i32 %_42, ptr %108, align 8
  %109 = getelementptr inbounds i8, ptr %_40, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %109, ptr align 8 %_43, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_40, ptr align 8 %_44, i64 32, i1 false)
  %110 = getelementptr inbounds i8, ptr %_40, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %110, ptr align 8 %_47, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_47)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_44)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_43)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_41)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %111 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_40) #22
  %_39.0 = extractvalue { i64, ptr } %111, 0
  %_39.1 = extractvalue { i64, ptr } %111, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_40)
  %112 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_39.0, ptr %112, align 8
  %113 = getelementptr inbounds i8, ptr %112, i64 8
  store ptr %_39.1, ptr %113, align 8
  store i8 1, ptr %_0, align 8
  br label %bb82

bb21:                                             ; preds = %bb16
  br label %bb23

bb91:                                             ; preds = %bb23
  call void @llvm.lifetime.start.p0(i64 160, ptr %_49)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_50)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_50, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_b5f839a6bda937f2cae73e49fc88071f) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_51 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 90) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_52)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_52, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_b5f839a6bda937f2cae73e49fc88071f) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_53)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_54)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_55)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_55, align 8
  %114 = getelementptr inbounds i8, ptr %_55, i64 8
  store i64 103, ptr %114, align 8
  %115 = getelementptr inbounds i8, ptr %_55, i64 16
  store i32 33, ptr %115, align 8
  %116 = getelementptr inbounds i8, ptr %_54, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %116, ptr align 8 %_55, i64 24, i1 false)
  store i64 0, ptr %_54, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_55)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_53, ptr align 8 %_54, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_54)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_56)
  store i8 2, ptr %_56, align 8
  %117 = getelementptr inbounds i8, ptr %_49, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %117, ptr align 8 %_50, i64 24, i1 false)
  %118 = getelementptr inbounds i8, ptr %_49, i64 152
  store i32 %_51, ptr %118, align 8
  %119 = getelementptr inbounds i8, ptr %_49, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %119, ptr align 8 %_52, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_49, ptr align 8 %_53, i64 32, i1 false)
  %120 = getelementptr inbounds i8, ptr %_49, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %120, ptr align 8 %_56, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_56)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_53)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_52)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_50)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %121 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_49) #22
  %_48.0 = extractvalue { i64, ptr } %121, 0
  %_48.1 = extractvalue { i64, ptr } %121, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_49)
  %122 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_48.0, ptr %122, align 8
  %123 = getelementptr inbounds i8, ptr %122, i64 8
  store ptr %_48.1, ptr %123, align 8
  store i8 1, ptr %_0, align 8
  br label %bb83

bb90:                                             ; preds = %bb23
  call void @llvm.lifetime.start.p0(i64 32, ptr %b)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_231, ptr align 1 %holder_key, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %b, ptr align 1 %_231, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target_head, ptr align 1 %b, i64 7, i1 false)
  %_62 = getelementptr inbounds i8, ptr %b, i64 7
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target_tail, ptr align 1 %_62, i64 25, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %b)
  br label %bb52

bb84:                                             ; preds = %bb80, %bb83
  call void @llvm.lifetime.end.p0(i64 25, ptr %target_tail)
  call void @llvm.lifetime.end.p0(i64 7, ptr %target_head)
  br label %bb85

bb54:                                             ; preds = %bb52
  %124 = getelementptr inbounds i8, ptr %st, i64 42
  %125 = load i8, ptr %124, align 2, !range !4, !noundef !3
  %126 = trunc i8 %125 to i1
  %127 = zext i1 %126 to i8
  store i8 %127, ptr %cashback, align 1
  %128 = load i64, ptr %fee, align 8, !range !2, !noundef !3
  store i64 %128, ptr %_152, align 8
  %129 = load i64, ptr %_152, align 8, !noundef !3
  switch i64 %129, label %bb55 [
    i64 0, label %bb79
    i64 1, label %bb56
  ]

bb53:                                             ; preds = %bb52
  store i8 0, ptr %cashback, align 1
  %130 = load i64, ptr %fee, align 8, !range !2, !noundef !3
  store i64 %130, ptr %_152, align 8
  %131 = load i64, ptr %_152, align 8, !noundef !3
  switch i64 %131, label %bb55 [
    i64 0, label %bb79
    i64 1, label %bb118
  ]

bb79:                                             ; preds = %bb74, %bb53, %bb54
  call void @llvm.lifetime.start.p0(i64 32, ptr %_201)
  call void @llvm.lifetime.start.p0(i64 32, ptr %b2)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %b2, ptr align 1 %target_head, i64 7, i1 false)
  %_206 = getelementptr inbounds i8, ptr %b2, i64 7
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_206, ptr align 1 %target_tail, i64 25, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_207)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_207, ptr align 1 %b2, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_233, ptr align 1 %_207, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_207)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_201, ptr align 1 %_233, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %b2)
  %132 = getelementptr inbounds i8, ptr %_0, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %132, ptr align 1 %_201, i64 32, i1 false)
  store i8 0, ptr %_0, align 8
  call void @llvm.lifetime.end.p0(i64 32, ptr %_201)
  call void @llvm.lifetime.end.p0(i64 1, ptr %cashback)
  call void @llvm.lifetime.end.p0(i64 25, ptr %target_tail)
  call void @llvm.lifetime.end.p0(i64 7, ptr %target_head)
  br label %bb85

bb56:                                             ; preds = %bb54
  %133 = getelementptr inbounds i8, ptr %fee, i64 8
  %134 = load i64, ptr %133, align 8, !noundef !3
  store i64 %134, ptr %f, align 8
  call void @llvm.lifetime.start.p0(i64 1, ptr %_154)
  %135 = getelementptr inbounds i8, ptr %st, i64 43
  %136 = load i8, ptr %135, align 1, !range !4, !noundef !3
  %137 = trunc i8 %136 to i1
  %138 = zext i1 %137 to i8
  store i8 %138, ptr %_154, align 1
  %139 = load i8, ptr %_154, align 1, !range !4, !noundef !3
  %140 = trunc i8 %139 to i1
  br i1 %140, label %bb57, label %bb61

bb61:                                             ; preds = %bb56
  call void @llvm.lifetime.end.p0(i64 1, ptr %_154)
  %141 = load i8, ptr %cashback, align 1, !range !4, !noundef !3
  %_164 = trunc i8 %141 to i1
  br i1 %_164, label %bb62, label %bb63

bb57:                                             ; preds = %bb118, %bb56
  call void @llvm.lifetime.start.p0(i64 160, ptr %_156)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_157)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_157, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_e75cefee4bb91125af0ea8444b842ed0) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_158 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 91) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_159)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_159, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_e75cefee4bb91125af0ea8444b842ed0) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_160)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_161)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_162)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_162, align 8
  %142 = getelementptr inbounds i8, ptr %_162, i64 8
  store i64 103, ptr %142, align 8
  %143 = getelementptr inbounds i8, ptr %_162, i64 16
  store i32 61, ptr %143, align 8
  %144 = getelementptr inbounds i8, ptr %_161, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %144, ptr align 8 %_162, i64 24, i1 false)
  store i64 0, ptr %_161, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_162)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_160, ptr align 8 %_161, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_161)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_163)
  store i8 2, ptr %_163, align 8
  %145 = getelementptr inbounds i8, ptr %_156, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %145, ptr align 8 %_157, i64 24, i1 false)
  %146 = getelementptr inbounds i8, ptr %_156, i64 152
  store i32 %_158, ptr %146, align 8
  %147 = getelementptr inbounds i8, ptr %_156, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %147, ptr align 8 %_159, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_156, ptr align 8 %_160, i64 32, i1 false)
  %148 = getelementptr inbounds i8, ptr %_156, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %148, ptr align 8 %_163, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_163)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_160)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_159)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_157)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %149 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_156) #22
  %_155.0 = extractvalue { i64, ptr } %149, 0
  %_155.1 = extractvalue { i64, ptr } %149, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_156)
  %150 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_155.0, ptr %150, align 8
  %151 = getelementptr inbounds i8, ptr %150, i64 8
  store ptr %_155.1, ptr %151, align 8
  store i8 1, ptr %_0, align 8
  call void @llvm.lifetime.end.p0(i64 1, ptr %_154)
  br label %bb80

bb63:                                             ; preds = %bb119, %bb61
  call void @llvm.lifetime.start.p0(i64 1, ptr %4)
  %152 = load volatile i8, ptr %holder_key, align 1
  store i8 %152, ptr %4, align 1
  %_174 = load i8, ptr %4, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %4)
  %153 = getelementptr inbounds i8, ptr %st, i64 45
  %154 = load i8, ptr %153, align 1, !range !4, !noundef !3
  %_177 = trunc i8 %154 to i1
  br i1 %_177, label %bb71, label %bb67

bb62:                                             ; preds = %bb61
  call void @llvm.lifetime.start.p0(i64 160, ptr %_166)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_167)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_167, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_835bb996f1795bf0338da0490417da62) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_168 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 80) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_169)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_169, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_835bb996f1795bf0338da0490417da62) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_170)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_171)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_172)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_172, align 8
  %155 = getelementptr inbounds i8, ptr %_172, i64 8
  store i64 103, ptr %155, align 8
  %156 = getelementptr inbounds i8, ptr %_172, i64 16
  store i32 65, ptr %156, align 8
  %157 = getelementptr inbounds i8, ptr %_171, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %157, ptr align 8 %_172, i64 24, i1 false)
  store i64 0, ptr %_171, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_172)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_170, ptr align 8 %_171, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_171)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_173)
  store i8 2, ptr %_173, align 8
  %158 = getelementptr inbounds i8, ptr %_166, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %158, ptr align 8 %_167, i64 24, i1 false)
  %159 = getelementptr inbounds i8, ptr %_166, i64 152
  store i32 %_168, ptr %159, align 8
  %160 = getelementptr inbounds i8, ptr %_166, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %160, ptr align 8 %_169, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_166, ptr align 8 %_170, i64 32, i1 false)
  %161 = getelementptr inbounds i8, ptr %_166, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %161, ptr align 8 %_173, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_173)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_170)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_169)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_167)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %162 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_166) #22
  %_165.0 = extractvalue { i64, ptr } %162, 0
  %_165.1 = extractvalue { i64, ptr } %162, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_166)
  %163 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_165.0, ptr %163, align 8
  %164 = getelementptr inbounds i8, ptr %163, i64 8
  store ptr %_165.1, ptr %164, align 8
  store i8 1, ptr %_0, align 8
  br label %bb80

bb80:                                             ; preds = %bb57, %bb75, %bb67, %bb62
  call void @llvm.lifetime.end.p0(i64 1, ptr %cashback)
  br label %bb84

bb118:                                            ; preds = %bb53
  %165 = getelementptr inbounds i8, ptr %fee, i64 8
  %166 = load i64, ptr %165, align 8, !noundef !3
  store i64 %166, ptr %f, align 8
  call void @llvm.lifetime.start.p0(i64 1, ptr %_154)
  %167 = getelementptr inbounds i8, ptr %st, i64 43
  %168 = load i8, ptr %167, align 1, !range !4, !noundef !3
  %169 = trunc i8 %168 to i1
  %170 = zext i1 %169 to i8
  store i8 %170, ptr %_154, align 1
  %171 = load i8, ptr %_154, align 1, !range !4, !noundef !3
  %172 = trunc i8 %171 to i1
  br i1 %172, label %bb57, label %bb119

bb119:                                            ; preds = %bb118
  call void @llvm.lifetime.end.p0(i64 1, ptr %_154)
  br label %bb63

bb67:                                             ; preds = %bb63
  call void @llvm.lifetime.start.p0(i64 160, ptr %_179)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_180)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_180, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_01eaaa187d2be542d4425f23ab284310) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_181 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 77) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_182)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_182, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_01eaaa187d2be542d4425f23ab284310) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_183)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_184)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_185)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_185, align 8
  %173 = getelementptr inbounds i8, ptr %_185, i64 8
  store i64 103, ptr %173, align 8
  %174 = getelementptr inbounds i8, ptr %_185, i64 16
  store i32 69, ptr %174, align 8
  %175 = getelementptr inbounds i8, ptr %_184, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %175, ptr align 8 %_185, i64 24, i1 false)
  store i64 0, ptr %_184, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_185)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_183, ptr align 8 %_184, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_184)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_186)
  store i8 2, ptr %_186, align 8
  %176 = getelementptr inbounds i8, ptr %_179, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %176, ptr align 8 %_180, i64 24, i1 false)
  %177 = getelementptr inbounds i8, ptr %_179, i64 152
  store i32 %_181, ptr %177, align 8
  %178 = getelementptr inbounds i8, ptr %_179, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %178, ptr align 8 %_182, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_179, ptr align 8 %_183, i64 32, i1 false)
  %179 = getelementptr inbounds i8, ptr %_179, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %179, ptr align 8 %_186, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_186)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_183)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_182)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_180)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %180 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_179) #22
  %_178.0 = extractvalue { i64, ptr } %180, 0
  %_178.1 = extractvalue { i64, ptr } %180, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_179)
  %181 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_178.0, ptr %181, align 8
  %182 = getelementptr inbounds i8, ptr %181, i64 8
  store ptr %_178.1, ptr %182, align 8
  store i8 1, ptr %_0, align 8
  br label %bb80

bb71:                                             ; preds = %bb63
  %183 = load i64, ptr %f, align 8, !noundef !3
  %184 = icmp eq i64 %183, 0
  br i1 %184, label %bb75, label %bb72

bb75:                                             ; preds = %bb73, %bb71
  call void @llvm.lifetime.start.p0(i64 160, ptr %_190)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_191)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_191, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_973adb9e8664e25d4750ddb14e0de56a) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_192 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 78) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_193)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_193, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_973adb9e8664e25d4750ddb14e0de56a) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_194)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_195)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_196)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_196, align 8
  %185 = getelementptr inbounds i8, ptr %_196, i64 8
  store i64 103, ptr %185, align 8
  %186 = getelementptr inbounds i8, ptr %_196, i64 16
  store i32 73, ptr %186, align 8
  %187 = getelementptr inbounds i8, ptr %_195, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %187, ptr align 8 %_196, i64 24, i1 false)
  store i64 0, ptr %_195, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_196)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_194, ptr align 8 %_195, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_195)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_197)
  store i8 2, ptr %_197, align 8
  %188 = getelementptr inbounds i8, ptr %_190, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %188, ptr align 8 %_191, i64 24, i1 false)
  %189 = getelementptr inbounds i8, ptr %_190, i64 152
  store i32 %_192, ptr %189, align 8
  %190 = getelementptr inbounds i8, ptr %_190, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %190, ptr align 8 %_193, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_190, ptr align 8 %_194, i64 32, i1 false)
  %191 = getelementptr inbounds i8, ptr %_190, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %191, ptr align 8 %_197, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_197)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_194)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_193)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_191)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %192 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_190) #22
  %_189.0 = extractvalue { i64, ptr } %192, 0
  %_189.1 = extractvalue { i64, ptr } %192, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_190)
  %193 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_189.0, ptr %193, align 8
  %194 = getelementptr inbounds i8, ptr %193, i64 8
  store ptr %_189.1, ptr %194, align 8
  store i8 1, ptr %_0, align 8
  br label %bb80

bb72:                                             ; preds = %bb71
  %195 = getelementptr inbounds i8, ptr %st, i64 32
  %_188 = load i64, ptr %195, align 8, !noundef !3
  %196 = load i64, ptr %f, align 8, !noundef !3
  %_187 = icmp ugt i64 %196, %_188
  br i1 %_187, label %bb73, label %bb74

bb74:                                             ; preds = %bb72
  call void @llvm.lifetime.start.p0(i64 1, ptr %3)
  %197 = load volatile i8, ptr %holder_key, align 1
  store i8 %197, ptr %3, align 1
  %_198 = load i8, ptr %3, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %3)
  br label %bb79

bb73:                                             ; preds = %bb72
  br label %bb75

bb85:                                             ; preds = %bb2, %bb84, %bb79
  ret void
}

; Function Attrs: nounwind
define void @custom_mir_validate(ptr dead_on_unwind noalias nocapture noundef writable sret([40 x i8]) align 8 dereferenceable(40) %_0, ptr noalias noundef readonly align 8 dereferenceable(48) %_1, i8 noundef %0, i64 noundef %1, i64 %2, ptr noalias nocapture noundef align 1 dereferenceable(33) %_4, ptr noalias noundef readonly align 1 dereferenceable(32) %_5, ptr noalias noundef readonly align 1 dereferenceable(32) %_6) unnamed_addr #1 {
start:
  %3 = alloca [1 x i8], align 1
  %4 = alloca [1 x i8], align 1
  %5 = alloca [1 x i8], align 1
  %6 = alloca [1 x i8], align 1
  %7 = alloca [1 x i8], align 1
  %8 = alloca [1 x i8], align 1
  %9 = alloca [1 x i8], align 1
  %10 = alloca [1 x i8], align 1
  %11 = alloca [1 x i8], align 1
  %_219 = alloca [8 x i8], align 8
  %_218 = alloca [8 x i8], align 8
  %_217 = alloca [1 x i8], align 1
  %_202 = alloca [32 x i8], align 1
  %_201 = alloca [32 x i8], align 1
  %_200 = alloca [32 x i8], align 1
  %_194 = alloca [32 x i8], align 1
  %_191 = alloca [32 x i8], align 1
  %_189 = alloca [1 x i8], align 1
  %_187 = alloca [32 x i8], align 1
  %_186 = alloca [32 x i8], align 1
  %_184 = alloca [32 x i8], align 1
  %_180 = alloca [72 x i8], align 8
  %_179 = alloca [24 x i8], align 8
  %_178 = alloca [32 x i8], align 8
  %_177 = alloca [32 x i8], align 8
  %_176 = alloca [24 x i8], align 8
  %_174 = alloca [24 x i8], align 8
  %_173 = alloca [160 x i8], align 8
  %_169 = alloca [72 x i8], align 8
  %_168 = alloca [24 x i8], align 8
  %_167 = alloca [32 x i8], align 8
  %_166 = alloca [32 x i8], align 8
  %_165 = alloca [24 x i8], align 8
  %_163 = alloca [24 x i8], align 8
  %_162 = alloca [160 x i8], align 8
  %_156 = alloca [72 x i8], align 8
  %_155 = alloca [24 x i8], align 8
  %_154 = alloca [32 x i8], align 8
  %_153 = alloca [32 x i8], align 8
  %_152 = alloca [24 x i8], align 8
  %_150 = alloca [24 x i8], align 8
  %_149 = alloca [160 x i8], align 8
  %_146 = alloca [72 x i8], align 8
  %_145 = alloca [24 x i8], align 8
  %_144 = alloca [32 x i8], align 8
  %_143 = alloca [32 x i8], align 8
  %_142 = alloca [24 x i8], align 8
  %_140 = alloca [24 x i8], align 8
  %_139 = alloca [160 x i8], align 8
  %_137 = alloca [1 x i8], align 1
  %_136 = alloca [8 x i8], align 8
  %_135 = alloca [8 x i8], align 8
  %_134 = alloca [1 x i8], align 1
  %_133 = alloca [32 x i8], align 1
  %_130 = alloca [72 x i8], align 8
  %_129 = alloca [24 x i8], align 8
  %_128 = alloca [32 x i8], align 8
  %_127 = alloca [32 x i8], align 8
  %_126 = alloca [24 x i8], align 8
  %_124 = alloca [24 x i8], align 8
  %_123 = alloca [160 x i8], align 8
  %_89 = alloca [32 x i8], align 1
  %_88 = alloca [32 x i8], align 1
  %_87 = alloca [64 x i8], align 1
  %_86 = alloca [72 x i8], align 8
  %_85 = alloca [24 x i8], align 8
  %_84 = alloca [32 x i8], align 8
  %_83 = alloca [32 x i8], align 8
  %_82 = alloca [24 x i8], align 8
  %_80 = alloca [24 x i8], align 8
  %_79 = alloca [160 x i8], align 8
  %_76 = alloca [32 x i8], align 1
  %_70 = alloca [72 x i8], align 8
  %_69 = alloca [24 x i8], align 8
  %_68 = alloca [32 x i8], align 8
  %_67 = alloca [32 x i8], align 8
  %_66 = alloca [24 x i8], align 8
  %_64 = alloca [24 x i8], align 8
  %_63 = alloca [160 x i8], align 8
  %_59 = alloca [32 x i8], align 1
  %_56 = alloca [32 x i8], align 1
  %_55 = alloca [72 x i8], align 8
  %_54 = alloca [24 x i8], align 8
  %_53 = alloca [32 x i8], align 8
  %_52 = alloca [32 x i8], align 8
  %_51 = alloca [24 x i8], align 8
  %_49 = alloca [24 x i8], align 8
  %_48 = alloca [160 x i8], align 8
  %_46 = alloca [72 x i8], align 8
  %_45 = alloca [24 x i8], align 8
  %_44 = alloca [32 x i8], align 8
  %_43 = alloca [32 x i8], align 8
  %_42 = alloca [24 x i8], align 8
  %_40 = alloca [24 x i8], align 8
  %_39 = alloca [160 x i8], align 8
  %_32 = alloca [72 x i8], align 8
  %_31 = alloca [24 x i8], align 8
  %_30 = alloca [32 x i8], align 8
  %_29 = alloca [32 x i8], align 8
  %_28 = alloca [24 x i8], align 8
  %_26 = alloca [24 x i8], align 8
  %_25 = alloca [160 x i8], align 8
  %_19 = alloca [32 x i8], align 1
  %_18 = alloca [72 x i8], align 8
  %_17 = alloca [24 x i8], align 8
  %_16 = alloca [32 x i8], align 8
  %_15 = alloca [32 x i8], align 8
  %_14 = alloca [24 x i8], align 8
  %_12 = alloca [24 x i8], align 8
  %_11 = alloca [160 x i8], align 8
  %_3 = alloca [16 x i8], align 8
  %_2 = alloca [1 x i8], align 1
  store i8 %0, ptr %_2, align 1
  store i64 %1, ptr %_3, align 8
  %12 = getelementptr inbounds i8, ptr %_3, i64 8
  store i64 %2, ptr %12, align 8
; call <core::option::Option<T> as core::cmp::PartialEq>::eq
  %_7 = call noundef zeroext i1 @"_ZN70_$LT$core..option..Option$LT$T$GT$$u20$as$u20$core..cmp..PartialEq$GT$2eq17hfcb7eaf5a0c0eea2E"(ptr noalias noundef readonly align 1 dereferenceable(1) %_2, ptr noalias noundef readonly align 1 dereferenceable(1) @alloc_8821998f047ca62cad40e6bc4e4d87c4) #22
  %13 = getelementptr inbounds i8, ptr %_1, i64 40
  %14 = load i8, ptr %13, align 8, !range !4, !noundef !3
  %_9 = trunc i8 %14 to i1
  br i1 %_9, label %bb2, label %bb6

bb6:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 32, ptr %_19)
  %15 = getelementptr inbounds i8, ptr %_1, i64 41
  %16 = load i8, ptr %15, align 1, !range !4, !noundef !3
  %_21 = trunc i8 %16 to i1
  %_20 = zext i1 %_21 to i8
  %17 = icmp eq i8 %_20, 1
  br i1 %17, label %bb8, label %bb7

bb2:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 160, ptr %_11)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_12)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_12, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_eb4f91695bc6f999067c65f428fcc4d8) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_13 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 88) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_14)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_14, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_eb4f91695bc6f999067c65f428fcc4d8) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_15)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_16)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_17)
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_17, align 8
  %18 = getelementptr inbounds i8, ptr %_17, i64 8
  store i64 38, ptr %18, align 8
  %19 = getelementptr inbounds i8, ptr %_17, i64 16
  store i32 284, ptr %19, align 8
  %20 = getelementptr inbounds i8, ptr %_16, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %20, ptr align 8 %_17, i64 24, i1 false)
  store i64 0, ptr %_16, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_17)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_15, ptr align 8 %_16, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_16)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_18)
  store i8 2, ptr %_18, align 8
  %21 = getelementptr inbounds i8, ptr %_11, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %21, ptr align 8 %_12, i64 24, i1 false)
  %22 = getelementptr inbounds i8, ptr %_11, i64 152
  store i32 %_13, ptr %22, align 8
  %23 = getelementptr inbounds i8, ptr %_11, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %23, ptr align 8 %_14, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_11, ptr align 8 %_15, i64 32, i1 false)
  %24 = getelementptr inbounds i8, ptr %_11, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %24, ptr align 8 %_18, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_18)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_15)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_14)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_12)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %25 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_11) #22
  %_10.0 = extractvalue { i64, ptr } %25, 0
  %_10.1 = extractvalue { i64, ptr } %25, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_11)
  %26 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_10.0, ptr %26, align 8
  %27 = getelementptr inbounds i8, ptr %26, i64 8
  store ptr %_10.1, ptr %27, align 8
  store i8 1, ptr %_0, align 8
  br label %bb84

bb8:                                              ; preds = %bb6
; call <core::option::Option<T> as core::cmp::PartialEq>::eq
  %_22 = call noundef zeroext i1 @"_ZN70_$LT$core..option..Option$LT$T$GT$$u20$as$u20$core..cmp..PartialEq$GT$2eq17hfcb7eaf5a0c0eea2E"(ptr noalias noundef readonly align 1 dereferenceable(1) %_2, ptr noalias noundef readonly align 1 dereferenceable(1) @alloc_8821998f047ca62cad40e6bc4e4d87c4) #22
  br i1 %_22, label %bb10, label %bb11

bb7:                                              ; preds = %bb6
  %_36 = call noundef zeroext i1 @llvm.expect.with.probability.i1(i1 noundef zeroext %_7, i1 noundef zeroext true, double noundef 5.000000e-01) #22
  br i1 %_36, label %bb16, label %bb22

bb11:                                             ; preds = %bb8
  call void @llvm.lifetime.start.p0(i64 160, ptr %_25)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_26)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_26, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_8f95cb73e89711d65e95d13598508b19) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_27 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 83) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_28)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_28, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_8f95cb73e89711d65e95d13598508b19) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_29)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_30)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_31)
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_31, align 8
  %28 = getelementptr inbounds i8, ptr %_31, i64 8
  store i64 38, ptr %28, align 8
  %29 = getelementptr inbounds i8, ptr %_31, i64 16
  store i32 289, ptr %29, align 8
  %30 = getelementptr inbounds i8, ptr %_30, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %30, ptr align 8 %_31, i64 24, i1 false)
  store i64 0, ptr %_30, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_31)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_29, ptr align 8 %_30, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_30)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_32)
  store i8 2, ptr %_32, align 8
  %31 = getelementptr inbounds i8, ptr %_25, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %31, ptr align 8 %_26, i64 24, i1 false)
  %32 = getelementptr inbounds i8, ptr %_25, i64 152
  store i32 %_27, ptr %32, align 8
  %33 = getelementptr inbounds i8, ptr %_25, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %33, ptr align 8 %_28, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_25, ptr align 8 %_29, i64 32, i1 false)
  %34 = getelementptr inbounds i8, ptr %_25, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %34, ptr align 8 %_32, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_32)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_29)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_28)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_26)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %35 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_25) #22
  %_24.0 = extractvalue { i64, ptr } %35, 0
  %_24.1 = extractvalue { i64, ptr } %35, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_25)
  call void @llvm.lifetime.start.p0(i64 1, ptr %11)
  %36 = load volatile i8, ptr %_5, align 1
  store i8 %36, ptr %11, align 1
  %_33 = load i8, ptr %11, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %11)
  %37 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_24.0, ptr %37, align 8
  %38 = getelementptr inbounds i8, ptr %37, i64 8
  store ptr %_24.1, ptr %38, align 8
  store i8 1, ptr %_0, align 8
  br label %bb81

bb10:                                             ; preds = %bb8
  br label %bb23

bb81:                                             ; preds = %bb17, %bb11
  br label %bb82

bb23:                                             ; preds = %bb21, %bb10
  %39 = load i8, ptr %_4, align 1, !range !4, !noundef !3
  %40 = trunc i8 %39 to i1
  %_185 = zext i1 %40 to i64
  switch i64 %_185, label %bb54 [
    i64 1, label %bb90
    i64 0, label %bb89
  ]

bb22:                                             ; preds = %bb7
  call void @llvm.lifetime.end.p0(i64 noundef 32, ptr noundef %_19) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_59)
  call void @llvm.lifetime.start.p0(i64 1, ptr %_189)
  %41 = load i8, ptr %_4, align 1, !range !4, !noundef !3
  %42 = trunc i8 %41 to i1
  %_190 = zext i1 %42 to i64
  switch i64 %_190, label %bb54 [
    i64 1, label %bb94
    i64 0, label %bb93
  ]

bb16:                                             ; preds = %bb7
  %43 = getelementptr inbounds i8, ptr %_1, i64 44
  %44 = load i8, ptr %43, align 4, !range !4, !noundef !3
  %_37 = trunc i8 %44 to i1
  br i1 %_37, label %bb21, label %bb17

bb54:                                             ; preds = %bb52, %bb53, %bb23, %bb123, %bb127, %bb22
  unreachable

bb94:                                             ; preds = %bb22
  store i8 1, ptr %_189, align 1
  br label %bb92

bb93:                                             ; preds = %bb22
  store i8 0, ptr %_189, align 1
  br label %bb92

bb92:                                             ; preds = %bb93, %bb94
  %45 = load i8, ptr %_189, align 1, !range !4, !noundef !3
  %46 = trunc i8 %45 to i1
  %_61 = xor i1 %46, true
  call void @llvm.lifetime.end.p0(i64 1, ptr %_189)
  %_60 = call noundef zeroext i1 @llvm.expect.with.probability.i1(i1 noundef zeroext %_61, i1 noundef zeroext true, double noundef 5.000000e-01) #22
  br i1 %_60, label %bb29, label %bb119

bb119:                                            ; preds = %bb92
  call void @llvm.lifetime.start.p0(i64 1, ptr %10)
  %47 = load volatile i8, ptr %_5, align 1
  store i8 %47, ptr %10, align 1
  %_212 = load i8, ptr %10, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %10)
  call void @llvm.lifetime.start.p0(i64 1, ptr %9)
  %48 = load volatile i8, ptr %_5, align 1
  store i8 %48, ptr %9, align 1
  %_213 = load i8, ptr %9, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %9)
  %_214 = icmp ne i8 %_212, %_213
  %_215 = call noundef zeroext i1 @llvm.expect.with.probability.i1(i1 noundef zeroext %_214, i1 noundef zeroext true, double noundef 5.000000e-01) #22
  br i1 %_215, label %bb123, label %bb33

bb29:                                             ; preds = %bb92
  call void @llvm.lifetime.start.p0(i64 160, ptr %_63)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_64)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_64, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_1ba5e1e397ae92b788c97e688ac0b362) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_65 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 89) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_66)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_66, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_1ba5e1e397ae92b788c97e688ac0b362) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_67)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_68)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_69)
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_69, align 8
  %49 = getelementptr inbounds i8, ptr %_69, i64 8
  store i64 38, ptr %49, align 8
  %50 = getelementptr inbounds i8, ptr %_69, i64 16
  store i32 306, ptr %50, align 8
  %51 = getelementptr inbounds i8, ptr %_68, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %51, ptr align 8 %_69, i64 24, i1 false)
  store i64 0, ptr %_68, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_69)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_67, ptr align 8 %_68, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_68)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_70)
  store i8 2, ptr %_70, align 8
  %52 = getelementptr inbounds i8, ptr %_63, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %52, ptr align 8 %_64, i64 24, i1 false)
  %53 = getelementptr inbounds i8, ptr %_63, i64 152
  store i32 %_65, ptr %53, align 8
  %54 = getelementptr inbounds i8, ptr %_63, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %54, ptr align 8 %_66, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_63, ptr align 8 %_67, i64 32, i1 false)
  %55 = getelementptr inbounds i8, ptr %_63, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %55, ptr align 8 %_70, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_70)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_67)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_66)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_64)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %56 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_63) #22
  %_62.0 = extractvalue { i64, ptr } %56, 0
  %_62.1 = extractvalue { i64, ptr } %56, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_63)
  %57 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_62.0, ptr %57, align 8
  %58 = getelementptr inbounds i8, ptr %57, i64 8
  store ptr %_62.1, ptr %58, align 8
  store i8 1, ptr %_0, align 8
  br label %bb80

bb33:                                             ; preds = %bb119
  %_72 = getelementptr inbounds i8, ptr %_4, i64 1
; call core::ptr::read_unaligned
  call void @_ZN4core3ptr14read_unaligned17hfb0286d8a885119bE(ptr noalias nocapture noundef sret([32 x i8]) align 1 dereferenceable(32) %_59, ptr noundef %_72) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_76)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_191)
; call core::array::<impl core::default::Default for [T; 32]>::default
  call void @"_ZN4core5array76_$LT$impl$u20$core..default..Default$u20$for$u20$$u5b$T$u3b$$u20$32$u5d$$GT$7default17hf39cfabd391f7201E"(ptr noalias nocapture noundef sret([32 x i8]) align 1 dereferenceable(32) %_191) #22
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_76, ptr align 1 %_191, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_191)
  call void @llvm.lifetime.start.p0(i64 1, ptr %8)
  %59 = call i32 @memcmp(ptr %_59, ptr %_76, i64 32)
  %60 = icmp eq i32 %59, 0
  %61 = zext i1 %60 to i8
  store i8 %61, ptr %8, align 1
  %62 = load i8, ptr %8, align 1, !range !4, !noundef !3
  %_75 = trunc i8 %62 to i1
  call void @llvm.lifetime.end.p0(i64 1, ptr %8)
  br i1 %_75, label %bb35, label %bb40

bb123:                                            ; preds = %bb119
  store ptr %_5, ptr %_219, align 8
  %63 = load ptr, ptr %_219, align 8, !noundef !3
  store ptr %63, ptr %_218, align 8
  %64 = load ptr, ptr %_218, align 8, !noundef !3
  %65 = load volatile i8, ptr %64, align 1
  store i8 %65, ptr %_217, align 1
  call void @llvm.trap() #22
  br label %bb54

bb40:                                             ; preds = %bb33
  call void @llvm.lifetime.end.p0(i64 32, ptr %_76)
  call void @llvm.lifetime.start.p0(i64 1, ptr %7)
  %66 = call i32 @memcmp(ptr %_59, ptr %_5, i64 32)
  %67 = icmp eq i32 %66, 0
  %68 = zext i1 %67 to i8
  store i8 %68, ptr %7, align 1
  %69 = load i8, ptr %7, align 1, !range !4, !noundef !3
  %_95 = trunc i8 %69 to i1
  call void @llvm.lifetime.end.p0(i64 1, ptr %7)
  %_94 = zext i1 %_95 to i8
  %_93 = call noundef zeroext i8 @llvm.bpf.passthrough.i8.i8(i32 noundef zeroext 4, i8 noundef zeroext %_94) #22
  %_92 = and i8 %_93, 1
  %_91 = icmp ne i8 %_92, 0
  %_90 = call noundef zeroext i1 @llvm.expect.with.probability.i1(i1 noundef zeroext %_91, i1 noundef zeroext true, double noundef 6.250000e-01) #22
  br i1 %_90, label %bb124, label %bb43

bb35:                                             ; preds = %bb33
  call void @llvm.lifetime.end.p0(i64 32, ptr %_76)
  call void @llvm.lifetime.start.p0(i64 160, ptr %_79)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_80)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_80, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_0e3505805f4905816c1bd644811a7869) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_81 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 30) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_82)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_82, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_0e3505805f4905816c1bd644811a7869) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_83)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_84)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_85)
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_85, align 8
  %70 = getelementptr inbounds i8, ptr %_85, i64 8
  store i64 38, ptr %70, align 8
  %71 = getelementptr inbounds i8, ptr %_85, i64 16
  store i32 307, ptr %71, align 8
  %72 = getelementptr inbounds i8, ptr %_84, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %72, ptr align 8 %_85, i64 24, i1 false)
  store i64 0, ptr %_84, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_85)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_83, ptr align 8 %_84, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_84)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_86)
  store i8 2, ptr %_86, align 8
  %73 = getelementptr inbounds i8, ptr %_79, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %73, ptr align 8 %_80, i64 24, i1 false)
  %74 = getelementptr inbounds i8, ptr %_79, i64 152
  store i32 %_81, ptr %74, align 8
  %75 = getelementptr inbounds i8, ptr %_79, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %75, ptr align 8 %_82, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_79, ptr align 8 %_83, i64 32, i1 false)
  %76 = getelementptr inbounds i8, ptr %_79, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %76, ptr align 8 %_86, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_86)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_83)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_82)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_80)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %77 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_79) #22
  %_78.0 = extractvalue { i64, ptr } %77, 0
  %_78.1 = extractvalue { i64, ptr } %77, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_79)
  call void @llvm.lifetime.start.p0(i64 64, ptr %_87)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_88)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_88, ptr align 1 %_59, i64 32, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_89)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_194)
; call core::array::<impl core::default::Default for [T; 32]>::default
  call void @"_ZN4core5array76_$LT$impl$u20$core..default..Default$u20$for$u20$$u5b$T$u3b$$u20$32$u5d$$GT$7default17hf39cfabd391f7201E"(ptr noalias nocapture noundef sret([32 x i8]) align 1 dereferenceable(32) %_194) #22
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_89, ptr align 1 %_194, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_194)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_87, ptr align 1 %_88, i64 32, i1 false)
  %78 = getelementptr inbounds i8, ptr %_87, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %78, ptr align 1 %_89, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_89)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_88)
; call anchor_lang::error::Error::with_pubkeys
  %79 = call { i64, ptr } @_ZN11anchor_lang5error5Error12with_pubkeys17hca6dbbbe6a9a5da7E(i64 noundef %_78.0, ptr noundef %_78.1, ptr noalias nocapture noundef readonly align 1 dereferenceable(64) %_87) #22
  %_77.0 = extractvalue { i64, ptr } %79, 0
  %_77.1 = extractvalue { i64, ptr } %79, 1
  call void @llvm.lifetime.end.p0(i64 64, ptr %_87)
  %80 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_77.0, ptr %80, align 8
  %81 = getelementptr inbounds i8, ptr %80, i64 8
  store ptr %_77.1, ptr %81, align 8
  store i8 1, ptr %_0, align 8
  br label %bb80

bb43:                                             ; preds = %bb40
  call void @llvm.lifetime.start.p0(i64 1, ptr %6)
  %82 = call i32 @memcmp(ptr %_59, ptr %_6, i64 32)
  %83 = icmp eq i32 %82, 0
  %84 = zext i1 %83 to i8
  store i8 %84, ptr %6, align 1
  %85 = load i8, ptr %6, align 1, !range !4, !noundef !3
  %_97 = trunc i8 %85 to i1
  call void @llvm.lifetime.end.p0(i64 1, ptr %6)
  %_96 = call noundef zeroext i1 @llvm.expect.i1(i1 noundef zeroext %_97, i1 noundef zeroext false) #22
  br i1 %_96, label %bb124, label %bb49

bb124:                                            ; preds = %bb43, %bb40
  call void @llvm.lifetime.start.p0(i64 1, ptr %5)
  %86 = load volatile i8, ptr %_5, align 1
  store i8 %86, ptr %5, align 1
  %_203 = load i8, ptr %5, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %5)
  call void @llvm.lifetime.start.p0(i64 1, ptr %4)
  %87 = load volatile i8, ptr %_5, align 1
  store i8 %87, ptr %4, align 1
  %_204 = load i8, ptr %4, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %4)
  %_205 = icmp ne i8 %_203, %_204
  br i1 %_205, label %bb127, label %bb109

bb49:                                             ; preds = %bb43
  call void @llvm.lifetime.start.p0(i64 noundef 32, ptr noundef %_19) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_133)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_133, ptr align 1 %_59, i64 32, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_200)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_201)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_201, ptr align 1 %_133, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_200, ptr align 1 %_201, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_201)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_19, ptr align 1 %_200, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_200)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_133)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_59)
  br label %bb51

bb51:                                             ; preds = %bb89, %bb49
  call void @llvm.lifetime.start.p0(i64 1, ptr %_134)
  br i1 %_7, label %bb52, label %bb53

bb127:                                            ; preds = %bb124
  store ptr %_5, ptr %_219, align 8
  %88 = load ptr, ptr %_219, align 8, !noundef !3
  store ptr %88, ptr %_218, align 8
  %89 = load ptr, ptr %_218, align 8, !noundef !3
  %90 = load volatile i8, ptr %89, align 1
  store i8 %90, ptr %_217, align 1
  call void @llvm.trap() #22
  br label %bb54

bb109:                                            ; preds = %bb124
  call void @llvm.lifetime.start.p0(i64 160, ptr %_123)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_124)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_124, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_861c8964bbad6d9cede9df277e628fe9) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_125 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 19) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_126)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_126, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_861c8964bbad6d9cede9df277e628fe9) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_127)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_128)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_129)
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_129, align 8
  %91 = getelementptr inbounds i8, ptr %_129, i64 8
  store i64 38, ptr %91, align 8
  %92 = getelementptr inbounds i8, ptr %_129, i64 16
  store i32 312, ptr %92, align 8
  %93 = getelementptr inbounds i8, ptr %_128, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %93, ptr align 8 %_129, i64 24, i1 false)
  store i64 0, ptr %_128, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_129)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_127, ptr align 8 %_128, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_128)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_130)
  store i8 2, ptr %_130, align 8
  %94 = getelementptr inbounds i8, ptr %_123, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %94, ptr align 8 %_124, i64 24, i1 false)
  %95 = getelementptr inbounds i8, ptr %_123, i64 152
  store i32 %_125, ptr %95, align 8
  %96 = getelementptr inbounds i8, ptr %_123, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %96, ptr align 8 %_126, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_123, ptr align 8 %_127, i64 32, i1 false)
  %97 = getelementptr inbounds i8, ptr %_123, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %97, ptr align 8 %_130, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_130)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_127)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_126)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_124)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %98 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_123) #22
  %_122.0 = extractvalue { i64, ptr } %98, 0
  %_122.1 = extractvalue { i64, ptr } %98, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_123)
  %99 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_122.0, ptr %99, align 8
  %100 = getelementptr inbounds i8, ptr %99, i64 8
  store ptr %_122.1, ptr %100, align 8
  store i8 1, ptr %_0, align 8
  br label %bb80

bb80:                                             ; preds = %bb29, %bb35, %bb109
  call void @llvm.lifetime.end.p0(i64 32, ptr %_59)
  br label %bb82

bb82:                                             ; preds = %bb90, %bb81, %bb80
  br label %bb83

bb17:                                             ; preds = %bb16
  call void @llvm.lifetime.start.p0(i64 160, ptr %_39)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_40)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_40, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_f94f166953c814e4161e699857179a1e) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_41 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 84) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_42)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_42, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_f94f166953c814e4161e699857179a1e) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_43)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_44)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_45)
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_45, align 8
  %101 = getelementptr inbounds i8, ptr %_45, i64 8
  store i64 38, ptr %101, align 8
  %102 = getelementptr inbounds i8, ptr %_45, i64 16
  store i32 296, ptr %102, align 8
  %103 = getelementptr inbounds i8, ptr %_44, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %103, ptr align 8 %_45, i64 24, i1 false)
  store i64 0, ptr %_44, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_45)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_43, ptr align 8 %_44, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_44)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_46)
  store i8 2, ptr %_46, align 8
  %104 = getelementptr inbounds i8, ptr %_39, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %104, ptr align 8 %_40, i64 24, i1 false)
  %105 = getelementptr inbounds i8, ptr %_39, i64 152
  store i32 %_41, ptr %105, align 8
  %106 = getelementptr inbounds i8, ptr %_39, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %106, ptr align 8 %_42, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_39, ptr align 8 %_43, i64 32, i1 false)
  %107 = getelementptr inbounds i8, ptr %_39, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %107, ptr align 8 %_46, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_46)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_43)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_42)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_40)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %108 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_39) #22
  %_38.0 = extractvalue { i64, ptr } %108, 0
  %_38.1 = extractvalue { i64, ptr } %108, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_39)
  %109 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_38.0, ptr %109, align 8
  %110 = getelementptr inbounds i8, ptr %109, i64 8
  store ptr %_38.1, ptr %110, align 8
  store i8 1, ptr %_0, align 8
  br label %bb81

bb21:                                             ; preds = %bb16
  br label %bb23

bb90:                                             ; preds = %bb23
  call void @llvm.lifetime.start.p0(i64 160, ptr %_48)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_49)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_49, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_b5f839a6bda937f2cae73e49fc88071f) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_50 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 90) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_51)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_51, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_b5f839a6bda937f2cae73e49fc88071f) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_52)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_53)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_54)
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_54, align 8
  %111 = getelementptr inbounds i8, ptr %_54, i64 8
  store i64 38, ptr %111, align 8
  %112 = getelementptr inbounds i8, ptr %_54, i64 16
  store i32 298, ptr %112, align 8
  %113 = getelementptr inbounds i8, ptr %_53, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %113, ptr align 8 %_54, i64 24, i1 false)
  store i64 0, ptr %_53, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_54)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_52, ptr align 8 %_53, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_53)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_55)
  store i8 2, ptr %_55, align 8
  %114 = getelementptr inbounds i8, ptr %_48, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %114, ptr align 8 %_49, i64 24, i1 false)
  %115 = getelementptr inbounds i8, ptr %_48, i64 152
  store i32 %_50, ptr %115, align 8
  %116 = getelementptr inbounds i8, ptr %_48, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %116, ptr align 8 %_51, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_48, ptr align 8 %_52, i64 32, i1 false)
  %117 = getelementptr inbounds i8, ptr %_48, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %117, ptr align 8 %_55, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_55)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_52)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_51)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_49)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %118 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_48) #22
  %_47.0 = extractvalue { i64, ptr } %118, 0
  %_47.1 = extractvalue { i64, ptr } %118, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_48)
  %119 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_47.0, ptr %119, align 8
  %120 = getelementptr inbounds i8, ptr %119, i64 8
  store ptr %_47.1, ptr %120, align 8
  store i8 1, ptr %_0, align 8
  br label %bb82

bb89:                                             ; preds = %bb23
  call void @llvm.lifetime.start.p0(i64 32, ptr %_56)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_56, ptr align 1 %_5, i64 32, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_186)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_187)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_187, ptr align 1 %_56, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_186, ptr align 1 %_187, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_187)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_19, ptr align 1 %_186, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_186)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_56)
  br label %bb51

bb83:                                             ; preds = %bb79, %bb82
  call void @llvm.lifetime.end.p0(i64 32, ptr %_19)
  br label %bb84

bb53:                                             ; preds = %bb51
  %121 = getelementptr inbounds i8, ptr %_1, i64 42
  %122 = load i8, ptr %121, align 2, !range !4, !noundef !3
  %123 = trunc i8 %122 to i1
  %124 = zext i1 %123 to i8
  store i8 %124, ptr %_134, align 1
  %125 = load i64, ptr %_3, align 8, !range !2, !noundef !3
  store i64 %125, ptr %_135, align 8
  %126 = load i64, ptr %_135, align 8, !noundef !3
  switch i64 %126, label %bb54 [
    i64 0, label %bb78
    i64 1, label %bb55
  ]

bb52:                                             ; preds = %bb51
  store i8 0, ptr %_134, align 1
  %127 = load i64, ptr %_3, align 8, !range !2, !noundef !3
  store i64 %127, ptr %_135, align 8
  %128 = load i64, ptr %_135, align 8, !noundef !3
  switch i64 %128, label %bb54 [
    i64 0, label %bb78
    i64 1, label %bb117
  ]

bb78:                                             ; preds = %bb73, %bb52, %bb53
  call void @llvm.lifetime.start.p0(i64 32, ptr %_184)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_184, ptr align 1 %_19, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_202, ptr align 1 %_184, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_184)
  %129 = getelementptr inbounds i8, ptr %_0, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %129, ptr align 1 %_202, i64 32, i1 false)
  store i8 0, ptr %_0, align 8
  call void @llvm.lifetime.end.p0(i64 1, ptr %_134)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_19)
  br label %bb84

bb55:                                             ; preds = %bb53
  %130 = getelementptr inbounds i8, ptr %_3, i64 8
  %131 = load i64, ptr %130, align 8, !noundef !3
  store i64 %131, ptr %_136, align 8
  call void @llvm.lifetime.start.p0(i64 1, ptr %_137)
  %132 = getelementptr inbounds i8, ptr %_1, i64 43
  %133 = load i8, ptr %132, align 1, !range !4, !noundef !3
  %134 = trunc i8 %133 to i1
  %135 = zext i1 %134 to i8
  store i8 %135, ptr %_137, align 1
  %136 = load i8, ptr %_137, align 1, !range !4, !noundef !3
  %137 = trunc i8 %136 to i1
  br i1 %137, label %bb56, label %bb60

bb60:                                             ; preds = %bb55
  call void @llvm.lifetime.end.p0(i64 1, ptr %_137)
  %138 = load i8, ptr %_134, align 1, !range !4, !noundef !3
  %_147 = trunc i8 %138 to i1
  br i1 %_147, label %bb61, label %bb62

bb56:                                             ; preds = %bb117, %bb55
  call void @llvm.lifetime.start.p0(i64 160, ptr %_139)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_140)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_140, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_e75cefee4bb91125af0ea8444b842ed0) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_141 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 91) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_142)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_142, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_e75cefee4bb91125af0ea8444b842ed0) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_143)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_144)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_145)
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_145, align 8
  %139 = getelementptr inbounds i8, ptr %_145, i64 8
  store i64 38, ptr %139, align 8
  %140 = getelementptr inbounds i8, ptr %_145, i64 16
  store i32 326, ptr %140, align 8
  %141 = getelementptr inbounds i8, ptr %_144, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %141, ptr align 8 %_145, i64 24, i1 false)
  store i64 0, ptr %_144, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_145)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_143, ptr align 8 %_144, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_144)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_146)
  store i8 2, ptr %_146, align 8
  %142 = getelementptr inbounds i8, ptr %_139, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %142, ptr align 8 %_140, i64 24, i1 false)
  %143 = getelementptr inbounds i8, ptr %_139, i64 152
  store i32 %_141, ptr %143, align 8
  %144 = getelementptr inbounds i8, ptr %_139, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %144, ptr align 8 %_142, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_139, ptr align 8 %_143, i64 32, i1 false)
  %145 = getelementptr inbounds i8, ptr %_139, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %145, ptr align 8 %_146, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_146)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_143)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_142)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_140)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %146 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_139) #22
  %_138.0 = extractvalue { i64, ptr } %146, 0
  %_138.1 = extractvalue { i64, ptr } %146, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_139)
  %147 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_138.0, ptr %147, align 8
  %148 = getelementptr inbounds i8, ptr %147, i64 8
  store ptr %_138.1, ptr %148, align 8
  store i8 1, ptr %_0, align 8
  call void @llvm.lifetime.end.p0(i64 1, ptr %_137)
  br label %bb79

bb62:                                             ; preds = %bb118, %bb60
  %149 = getelementptr inbounds i8, ptr %_1, i64 45
  %150 = load i8, ptr %149, align 1, !range !4, !noundef !3
  %_160 = trunc i8 %150 to i1
  br i1 %_160, label %bb70, label %bb66

bb61:                                             ; preds = %bb60
  call void @llvm.lifetime.start.p0(i64 160, ptr %_149)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_150)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_150, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_835bb996f1795bf0338da0490417da62) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_151 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 80) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_152)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_152, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_835bb996f1795bf0338da0490417da62) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_153)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_154)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_155)
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_155, align 8
  %151 = getelementptr inbounds i8, ptr %_155, i64 8
  store i64 38, ptr %151, align 8
  %152 = getelementptr inbounds i8, ptr %_155, i64 16
  store i32 330, ptr %152, align 8
  %153 = getelementptr inbounds i8, ptr %_154, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %153, ptr align 8 %_155, i64 24, i1 false)
  store i64 0, ptr %_154, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_155)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_153, ptr align 8 %_154, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_154)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_156)
  store i8 2, ptr %_156, align 8
  %154 = getelementptr inbounds i8, ptr %_149, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %154, ptr align 8 %_150, i64 24, i1 false)
  %155 = getelementptr inbounds i8, ptr %_149, i64 152
  store i32 %_151, ptr %155, align 8
  %156 = getelementptr inbounds i8, ptr %_149, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %156, ptr align 8 %_152, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_149, ptr align 8 %_153, i64 32, i1 false)
  %157 = getelementptr inbounds i8, ptr %_149, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %157, ptr align 8 %_156, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_156)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_153)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_152)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_150)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %158 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_149) #22
  %_148.0 = extractvalue { i64, ptr } %158, 0
  %_148.1 = extractvalue { i64, ptr } %158, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_149)
  %159 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_148.0, ptr %159, align 8
  %160 = getelementptr inbounds i8, ptr %159, i64 8
  store ptr %_148.1, ptr %160, align 8
  store i8 1, ptr %_0, align 8
  br label %bb79

bb79:                                             ; preds = %bb56, %bb74, %bb66, %bb61
  call void @llvm.lifetime.end.p0(i64 1, ptr %_134)
  br label %bb83

bb117:                                            ; preds = %bb52
  %161 = getelementptr inbounds i8, ptr %_3, i64 8
  %162 = load i64, ptr %161, align 8, !noundef !3
  store i64 %162, ptr %_136, align 8
  call void @llvm.lifetime.start.p0(i64 1, ptr %_137)
  %163 = getelementptr inbounds i8, ptr %_1, i64 43
  %164 = load i8, ptr %163, align 1, !range !4, !noundef !3
  %165 = trunc i8 %164 to i1
  %166 = zext i1 %165 to i8
  store i8 %166, ptr %_137, align 1
  %167 = load i8, ptr %_137, align 1, !range !4, !noundef !3
  %168 = trunc i8 %167 to i1
  br i1 %168, label %bb56, label %bb118

bb118:                                            ; preds = %bb117
  call void @llvm.lifetime.end.p0(i64 1, ptr %_137)
  br label %bb62

bb66:                                             ; preds = %bb62
  call void @llvm.lifetime.start.p0(i64 160, ptr %_162)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_163)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_163, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_01eaaa187d2be542d4425f23ab284310) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_164 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 77) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_165)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_165, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_01eaaa187d2be542d4425f23ab284310) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_166)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_167)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_168)
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_168, align 8
  %169 = getelementptr inbounds i8, ptr %_168, i64 8
  store i64 38, ptr %169, align 8
  %170 = getelementptr inbounds i8, ptr %_168, i64 16
  store i32 334, ptr %170, align 8
  %171 = getelementptr inbounds i8, ptr %_167, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %171, ptr align 8 %_168, i64 24, i1 false)
  store i64 0, ptr %_167, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_168)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_166, ptr align 8 %_167, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_167)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_169)
  store i8 2, ptr %_169, align 8
  %172 = getelementptr inbounds i8, ptr %_162, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %172, ptr align 8 %_163, i64 24, i1 false)
  %173 = getelementptr inbounds i8, ptr %_162, i64 152
  store i32 %_164, ptr %173, align 8
  %174 = getelementptr inbounds i8, ptr %_162, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %174, ptr align 8 %_165, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_162, ptr align 8 %_166, i64 32, i1 false)
  %175 = getelementptr inbounds i8, ptr %_162, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %175, ptr align 8 %_169, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_169)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_166)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_165)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_163)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %176 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_162) #22
  %_161.0 = extractvalue { i64, ptr } %176, 0
  %_161.1 = extractvalue { i64, ptr } %176, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_162)
  %177 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_161.0, ptr %177, align 8
  %178 = getelementptr inbounds i8, ptr %177, i64 8
  store ptr %_161.1, ptr %178, align 8
  store i8 1, ptr %_0, align 8
  br label %bb79

bb70:                                             ; preds = %bb62
  %179 = load i64, ptr %_136, align 8, !noundef !3
  %180 = icmp eq i64 %179, 0
  br i1 %180, label %bb74, label %bb71

bb74:                                             ; preds = %bb72, %bb70
  call void @llvm.lifetime.start.p0(i64 160, ptr %_173)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_174)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_174, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_973adb9e8664e25d4750ddb14e0de56a) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_175 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 78) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_176)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_176, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_973adb9e8664e25d4750ddb14e0de56a) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_177)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_178)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_179)
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_179, align 8
  %181 = getelementptr inbounds i8, ptr %_179, i64 8
  store i64 38, ptr %181, align 8
  %182 = getelementptr inbounds i8, ptr %_179, i64 16
  store i32 338, ptr %182, align 8
  %183 = getelementptr inbounds i8, ptr %_178, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %183, ptr align 8 %_179, i64 24, i1 false)
  store i64 0, ptr %_178, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_179)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_177, ptr align 8 %_178, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_178)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_180)
  store i8 2, ptr %_180, align 8
  %184 = getelementptr inbounds i8, ptr %_173, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %184, ptr align 8 %_174, i64 24, i1 false)
  %185 = getelementptr inbounds i8, ptr %_173, i64 152
  store i32 %_175, ptr %185, align 8
  %186 = getelementptr inbounds i8, ptr %_173, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %186, ptr align 8 %_176, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_173, ptr align 8 %_177, i64 32, i1 false)
  %187 = getelementptr inbounds i8, ptr %_173, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %187, ptr align 8 %_180, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_180)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_177)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_176)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_174)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %188 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_173) #22
  %_172.0 = extractvalue { i64, ptr } %188, 0
  %_172.1 = extractvalue { i64, ptr } %188, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_173)
  %189 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_172.0, ptr %189, align 8
  %190 = getelementptr inbounds i8, ptr %189, i64 8
  store ptr %_172.1, ptr %190, align 8
  store i8 1, ptr %_0, align 8
  br label %bb79

bb71:                                             ; preds = %bb70
  %191 = getelementptr inbounds i8, ptr %_1, i64 32
  %_171 = load i64, ptr %191, align 8, !noundef !3
  %192 = load i64, ptr %_136, align 8, !noundef !3
  %_170 = icmp ugt i64 %192, %_171
  br i1 %_170, label %bb72, label %bb73

bb73:                                             ; preds = %bb71
  call void @llvm.lifetime.start.p0(i64 1, ptr %3)
  %193 = load volatile i8, ptr %_5, align 1
  store i8 %193, ptr %3, align 1
  %_181 = load i8, ptr %3, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %3)
  br label %bb78

bb72:                                             ; preds = %bb71
  br label %bb74

bb84:                                             ; preds = %bb2, %bb83, %bb78
  ret void
}

; Function Attrs: nounwind
define noundef i64 @actual_curve_size() unnamed_addr #1 {
start:
  ret i64 160
}

; Function Attrs: nounwind
define noundef i64 @actual_account_size() unnamed_addr #1 {
start:
  ret i64 168
}

; Function Attrs: nounwind
define noundef i64 @actual_box_size() unnamed_addr #1 {
start:
  ret i64 8
}

; Function Attrs: nounwind
define noundef i64 @actual_curve_holder_offset(ptr noalias noundef readonly align 8 dereferenceable(160) %x) unnamed_addr #1 {
start:
  %_3 = getelementptr inbounds i8, ptr %x, i64 157
  %_2 = ptrtoint ptr %_3 to i64
  %_4 = ptrtoint ptr %x to i64
  %_6.0 = sub i64 %_2, %_4
  %_6.1 = icmp ult i64 %_2, %_4
  %0 = call i1 @llvm.expect.i1(i1 %_6.1, i1 false)
  br i1 %0, label %panic, label %bb1

bb1:                                              ; preds = %start
  ret i64 %_6.0

panic:                                            ; preds = %start
; call core::panicking::panic_const::panic_const_sub_overflow
  call void @_ZN4core9panicking11panic_const24panic_const_sub_overflow17hce3a200f706adb1cE(ptr noalias noundef readonly align 8 dereferenceable(24) @alloc_e4468c65f8d1e2b77e8f88d0bdfc7833) #21
  unreachable
}

; Function Attrs: nounwind
define noundef i64 @actual_account_holder_offset(ptr noalias noundef readonly align 8 dereferenceable(168) %x) unnamed_addr #1 {
start:
  %0 = getelementptr inbounds i8, ptr %x, i64 8
  %_3 = getelementptr inbounds i8, ptr %0, i64 157
  %_2 = ptrtoint ptr %_3 to i64
  %_4 = ptrtoint ptr %x to i64
  %_6.0 = sub i64 %_2, %_4
  %_6.1 = icmp ult i64 %_2, %_4
  %1 = call i1 @llvm.expect.i1(i1 %_6.1, i1 false)
  br i1 %1, label %panic, label %bb1

bb1:                                              ; preds = %start
  ret i64 %_6.0

panic:                                            ; preds = %start
; call core::panicking::panic_const::panic_const_sub_overflow
  call void @_ZN4core9panicking11panic_const24panic_const_sub_overflow17hce3a200f706adb1cE(ptr noalias noundef readonly align 8 dereferenceable(24) @alloc_a9c7f39c0aa194410e7398e0248fb345) #21
  unreachable
}

; Function Attrs: nounwind
define noundef i8 @actual_account_raw_hold(ptr noalias noundef readonly align 8 dereferenceable(8) %x) unnamed_addr #1 {
start:
  %0 = alloca [1 x i8], align 1
  %1 = alloca [8 x i8], align 8
  call void @llvm.lifetime.start.p0(i64 8, ptr %1)
  %2 = load volatile ptr, ptr %x, align 8
  store ptr %2, ptr %1, align 8
  %cvk = load ptr, ptr %1, align 8, !noundef !3
  call void @llvm.lifetime.end.p0(i64 8, ptr %1)
  %_5 = getelementptr inbounds i8, ptr %cvk, i64 165
  call void @llvm.lifetime.start.p0(i64 1, ptr %0)
  %3 = load volatile i8, ptr %_5, align 1
  store i8 %3, ptr %0, align 1
  %_0 = load i8, ptr %0, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %0)
  ret i8 %_0
}

; Function Attrs: nounwind
define noundef zeroext i1 @actual_account_holder(ptr noalias noundef readonly align 8 dereferenceable(8) %x) unnamed_addr #1 {
start:
  %_2 = load ptr, ptr %x, align 8, !nonnull !3, !align !5, !noundef !3
  %0 = getelementptr inbounds i8, ptr %_2, i64 8
  %1 = getelementptr inbounds i8, ptr %0, i64 157
  %2 = load i8, ptr %1, align 1, !range !4, !noundef !3
  %_0 = trunc i8 %2 to i1
  ret i1 %_0
}

; Function Attrs: nounwind
define void @actual_clone(ptr dead_on_unwind noalias nocapture noundef writable sret([48 x i8]) align 8 dereferenceable(48) %_0, ptr noalias noundef readonly align 8 dereferenceable(48) %x) unnamed_addr #1 {
start:
  %_2 = alloca [48 x i8], align 8
  call void @llvm.lifetime.start.p0(i64 48, ptr %_2)
; call <solana_account_info::AccountInfo as core::clone::Clone>::clone
  call void @"_ZN71_$LT$solana_account_info..AccountInfo$u20$as$u20$core..clone..Clone$GT$5clone17h759150bcde62cc00E"(ptr noalias nocapture noundef sret([48 x i8]) align 8 dereferenceable(48) %_2, ptr noalias noundef readonly align 8 dereferenceable(48) %x) #22
  call void @llvm.var.annotation.p0.p0(ptr noundef %_2, ptr noundef @alloc_914b2c69d7eca30497b9feaf15ac92f1, ptr noundef @alloc_914b2c69d7eca30497b9feaf15ac92f1, i32 noundef zeroext 0, ptr noundef null) #22
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_0, ptr align 8 %_2, i64 48, i1 false)
  call void @llvm.lifetime.end.p0(i64 48, ptr %_2)
  ret void
}

; Function Attrs: nounwind
define noundef i8 @nested_outer_none() unnamed_addr #1 {
start:
  %x = alloca [33 x i8], align 1
  call void @llvm.lifetime.start.p0(i64 33, ptr %x)
  store i8 2, ptr %x, align 1
  %_0 = load i8, ptr %x, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 33, ptr %x)
  ret i8 %_0
}

; Function Attrs: nounwind
define noundef i8 @nested_inner_none() unnamed_addr #1 {
start:
  %_2 = alloca [33 x i8], align 1
  %x = alloca [33 x i8], align 1
  call void @llvm.lifetime.start.p0(i64 33, ptr %x)
  call void @llvm.lifetime.start.p0(i64 33, ptr %_2)
  store i8 0, ptr %_2, align 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %x, ptr align 1 %_2, i64 33, i1 false)
  call void @llvm.lifetime.end.p0(i64 33, ptr %_2)
  %_0 = load i8, ptr %x, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 33, ptr %x)
  ret i8 %_0
}

; Function Attrs: nounwind
define noundef i8 @nested_some(ptr noalias nocapture noundef readonly align 1 dereferenceable(32) %v) unnamed_addr #1 {
start:
  %_3 = alloca [33 x i8], align 1
  %x = alloca [33 x i8], align 1
  call void @llvm.lifetime.start.p0(i64 33, ptr %x)
  call void @llvm.lifetime.start.p0(i64 33, ptr %_3)
  %0 = getelementptr inbounds i8, ptr %_3, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %0, ptr align 1 %v, i64 32, i1 false)
  store i8 1, ptr %_3, align 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %x, ptr align 1 %_3, i64 33, i1 false)
  call void @llvm.lifetime.end.p0(i64 33, ptr %_3)
  %_0 = load i8, ptr %x, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 33, ptr %x)
  ret i8 %_0
}

; Function Attrs: nounwind
define void @nested_raw(ptr dead_on_unwind noalias nocapture noundef writable sret([33 x i8]) align 1 dereferenceable(33) %_0, ptr noalias noundef readonly align 1 dereferenceable(33) %x) unnamed_addr #1 {
start:
  %out = alloca [33 x i8], align 1
  %ntag = load i8, ptr %x, align 1, !noundef !3
  %np = getelementptr inbounds i8, ptr %x, i64 1
  call void @llvm.lifetime.start.p0(i64 33, ptr %out)
  store i8 2, ptr %out, align 1
  store i8 %ntag, ptr %out, align 1
  %_9 = getelementptr inbounds i8, ptr %out, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_9, ptr align 1 %np, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_0, ptr align 1 %out, i64 33, i1 false)
  call void @llvm.lifetime.end.p0(i64 33, ptr %out)
  ret void
}

; Function Attrs: nounwind
define void @nested_control(ptr dead_on_unwind noalias nocapture noundef writable sret([33 x i8]) align 1 dereferenceable(33) %_0, ptr noalias noundef readonly align 1 dereferenceable(33) %x) unnamed_addr #1 {
start:
  %_2 = alloca [33 x i8], align 1
  call void @llvm.lifetime.start.p0(i64 33, ptr %_2)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_2, ptr align 1 %x, i64 33, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_0, ptr align 1 %_2, i64 33, i1 false)
  call void @llvm.lifetime.end.p0(i64 33, ptr %_2)
  ret void
}

; Function Attrs: nounwind
define noundef zeroext i1 @annotation_bool(i1 noundef zeroext %v) unnamed_addr #1 {
start:
  %_0 = call noundef zeroext i1 @llvm.annotation.i1.p0(i1 noundef zeroext %v, ptr noundef @alloc_914b2c69d7eca30497b9feaf15ac92f1, ptr noundef @alloc_914b2c69d7eca30497b9feaf15ac92f1, i32 noundef zeroext 0) #22
  ret i1 %_0
}

; Function Attrs: nounwind
define noundef zeroext i1 @annotation_control(i1 noundef zeroext %v) unnamed_addr #1 {
start:
  ret i1 %v
}

; Function Attrs: nounwind
define void @ordinary4158_validate(ptr dead_on_unwind noalias nocapture noundef writable sret([40 x i8]) align 8 dereferenceable(40) %_0, ptr noalias noundef readonly align 8 dereferenceable(48) %st, i8 noundef %0, i64 noundef %1, i64 %2, ptr noalias noundef readonly align 1 dereferenceable(33) %new, ptr noalias noundef readonly align 1 dereferenceable(32) %holder_key, ptr noalias noundef readonly align 1 dereferenceable(32) %sharing) unnamed_addr #1 {
start:
  %3 = alloca [1 x i8], align 1
  %4 = alloca [1 x i8], align 1
  %5 = alloca [1 x i8], align 1
  %6 = alloca [1 x i8], align 1
  %7 = alloca [1 x i8], align 1
  %8 = alloca [1 x i8], align 1
  %9 = alloca [1 x i8], align 1
  %_230 = alloca [32 x i8], align 1
  %_229 = alloca [32 x i8], align 1
  %_228 = alloca [32 x i8], align 1
  %_212 = alloca [32 x i8], align 1
  %_209 = alloca [32 x i8], align 1
  %_207 = alloca [1 x i8], align 1
  %_201 = alloca [32 x i8], align 1
  %b2 = alloca [32 x i8], align 1
  %_195 = alloca [32 x i8], align 1
  %_191 = alloca [72 x i8], align 8
  %_190 = alloca [24 x i8], align 8
  %_189 = alloca [32 x i8], align 8
  %_188 = alloca [32 x i8], align 8
  %_187 = alloca [24 x i8], align 8
  %_185 = alloca [24 x i8], align 8
  %_184 = alloca [160 x i8], align 8
  %_180 = alloca [72 x i8], align 8
  %_179 = alloca [24 x i8], align 8
  %_178 = alloca [32 x i8], align 8
  %_177 = alloca [32 x i8], align 8
  %_176 = alloca [24 x i8], align 8
  %_174 = alloca [24 x i8], align 8
  %_173 = alloca [160 x i8], align 8
  %_167 = alloca [72 x i8], align 8
  %_166 = alloca [24 x i8], align 8
  %_165 = alloca [32 x i8], align 8
  %_164 = alloca [32 x i8], align 8
  %_163 = alloca [24 x i8], align 8
  %_161 = alloca [24 x i8], align 8
  %_160 = alloca [160 x i8], align 8
  %_157 = alloca [72 x i8], align 8
  %_156 = alloca [24 x i8], align 8
  %_155 = alloca [32 x i8], align 8
  %_154 = alloca [32 x i8], align 8
  %_153 = alloca [24 x i8], align 8
  %_151 = alloca [24 x i8], align 8
  %_150 = alloca [160 x i8], align 8
  %_148 = alloca [1 x i8], align 1
  %f = alloca [8 x i8], align 8
  %_146 = alloca [8 x i8], align 8
  %cashback = alloca [1 x i8], align 1
  %_144 = alloca [72 x i8], align 8
  %_143 = alloca [24 x i8], align 8
  %_142 = alloca [32 x i8], align 8
  %_141 = alloca [32 x i8], align 8
  %_140 = alloca [24 x i8], align 8
  %_138 = alloca [24 x i8], align 8
  %_137 = alloca [160 x i8], align 8
  %b1 = alloca [32 x i8], align 1
  %_98 = alloca [32 x i8], align 1
  %_97 = alloca [32 x i8], align 1
  %_96 = alloca [64 x i8], align 1
  %_95 = alloca [72 x i8], align 8
  %_94 = alloca [24 x i8], align 8
  %_93 = alloca [32 x i8], align 8
  %_92 = alloca [32 x i8], align 8
  %_91 = alloca [24 x i8], align 8
  %_89 = alloca [24 x i8], align 8
  %_88 = alloca [160 x i8], align 8
  %_85 = alloca [32 x i8], align 1
  %_79 = alloca [72 x i8], align 8
  %_78 = alloca [24 x i8], align 8
  %_77 = alloca [32 x i8], align 8
  %_76 = alloca [32 x i8], align 8
  %_75 = alloca [24 x i8], align 8
  %_73 = alloca [24 x i8], align 8
  %_72 = alloca [160 x i8], align 8
  %t = alloca [32 x i8], align 1
  %b = alloca [32 x i8], align 1
  %_58 = alloca [72 x i8], align 8
  %_57 = alloca [24 x i8], align 8
  %_56 = alloca [32 x i8], align 8
  %_55 = alloca [32 x i8], align 8
  %_54 = alloca [24 x i8], align 8
  %_52 = alloca [24 x i8], align 8
  %_51 = alloca [160 x i8], align 8
  %_49 = alloca [72 x i8], align 8
  %_48 = alloca [24 x i8], align 8
  %_47 = alloca [32 x i8], align 8
  %_46 = alloca [32 x i8], align 8
  %_45 = alloca [24 x i8], align 8
  %_43 = alloca [24 x i8], align 8
  %_42 = alloca [160 x i8], align 8
  %_33 = alloca [72 x i8], align 8
  %_32 = alloca [24 x i8], align 8
  %_31 = alloca [32 x i8], align 8
  %_30 = alloca [32 x i8], align 8
  %_29 = alloca [24 x i8], align 8
  %_27 = alloca [24 x i8], align 8
  %_26 = alloca [160 x i8], align 8
  %target_tail = alloca [25 x i8], align 1
  %target_head = alloca [7 x i8], align 1
  %_18 = alloca [72 x i8], align 8
  %_17 = alloca [24 x i8], align 8
  %_16 = alloca [32 x i8], align 8
  %_15 = alloca [32 x i8], align 8
  %_14 = alloca [24 x i8], align 8
  %_12 = alloca [24 x i8], align 8
  %_11 = alloca [160 x i8], align 8
  %fee = alloca [16 x i8], align 8
  %hopt = alloca [1 x i8], align 1
  store i8 %0, ptr %hopt, align 1
  store i64 %1, ptr %fee, align 8
  %10 = getelementptr inbounds i8, ptr %fee, i64 8
  store i64 %2, ptr %10, align 8
; call <core::option::Option<T> as core::cmp::PartialEq>::eq
  %holder = call noundef zeroext i1 @"_ZN70_$LT$core..option..Option$LT$T$GT$$u20$as$u20$core..cmp..PartialEq$GT$2eq17hfcb7eaf5a0c0eea2E"(ptr noalias noundef readonly align 1 dereferenceable(1) %hopt, ptr noalias noundef readonly align 1 dereferenceable(1) @alloc_8821998f047ca62cad40e6bc4e4d87c4) #22
  %11 = getelementptr inbounds i8, ptr %st, i64 40
  %12 = load i8, ptr %11, align 8, !range !4, !noundef !3
  %_9 = trunc i8 %12 to i1
  br i1 %_9, label %bb2, label %bb6

bb6:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 7, ptr %target_head)
  call void @llvm.lifetime.start.p0(i64 25, ptr %target_tail)
  %13 = getelementptr inbounds i8, ptr %st, i64 41
  %14 = load i8, ptr %13, align 1, !range !4, !noundef !3
  %_22 = trunc i8 %14 to i1
  %_21 = zext i1 %_22 to i8
  %15 = icmp eq i8 %_21, 1
  br i1 %15, label %bb8, label %bb7

bb2:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 160, ptr %_11)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_12)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_12, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_eb4f91695bc6f999067c65f428fcc4d8) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_13 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 88) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_14)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_14, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_eb4f91695bc6f999067c65f428fcc4d8) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_15)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_16)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_17)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_17, align 8
  %16 = getelementptr inbounds i8, ptr %_17, i64 8
  store i64 103, ptr %16, align 8
  %17 = getelementptr inbounds i8, ptr %_17, i64 16
  store i32 154, ptr %17, align 8
  %18 = getelementptr inbounds i8, ptr %_16, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %18, ptr align 8 %_17, i64 24, i1 false)
  store i64 0, ptr %_16, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_17)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_15, ptr align 8 %_16, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_16)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_18)
  store i8 2, ptr %_18, align 8
  %19 = getelementptr inbounds i8, ptr %_11, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %19, ptr align 8 %_12, i64 24, i1 false)
  %20 = getelementptr inbounds i8, ptr %_11, i64 152
  store i32 %_13, ptr %20, align 8
  %21 = getelementptr inbounds i8, ptr %_11, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %21, ptr align 8 %_14, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_11, ptr align 8 %_15, i64 32, i1 false)
  %22 = getelementptr inbounds i8, ptr %_11, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %22, ptr align 8 %_18, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_18)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_15)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_14)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_12)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %23 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_11) #22
  %_10.0 = extractvalue { i64, ptr } %23, 0
  %_10.1 = extractvalue { i64, ptr } %23, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_11)
  %24 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_10.0, ptr %24, align 8
  %25 = getelementptr inbounds i8, ptr %24, i64 8
  store ptr %_10.1, ptr %25, align 8
  store i8 1, ptr %_0, align 8
  br label %bb91

bb8:                                              ; preds = %bb6
; call <core::option::Option<T> as core::cmp::PartialEq>::eq
  %_23 = call noundef zeroext i1 @"_ZN70_$LT$core..option..Option$LT$T$GT$$u20$as$u20$core..cmp..PartialEq$GT$2eq17hfcb7eaf5a0c0eea2E"(ptr noalias noundef readonly align 1 dereferenceable(1) %hopt, ptr noalias noundef readonly align 1 dereferenceable(1) @alloc_8821998f047ca62cad40e6bc4e4d87c4) #22
  br i1 %_23, label %bb10, label %bb11

bb7:                                              ; preds = %bb6
  %_34 = call noundef zeroext i1 @llvm.expect.with.probability.i1(i1 noundef zeroext %holder, i1 noundef zeroext true, double noundef 4.900000e-01) #22
  br i1 %_34, label %bb16, label %bb23

bb11:                                             ; preds = %bb8
  call void @llvm.lifetime.start.p0(i64 160, ptr %_26)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_27)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_27, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_8f95cb73e89711d65e95d13598508b19) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_28 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 83) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_29)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_29, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_8f95cb73e89711d65e95d13598508b19) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_30)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_31)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_32)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_32, align 8
  %26 = getelementptr inbounds i8, ptr %_32, i64 8
  store i64 103, ptr %26, align 8
  %27 = getelementptr inbounds i8, ptr %_32, i64 16
  store i32 159, ptr %27, align 8
  %28 = getelementptr inbounds i8, ptr %_31, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %28, ptr align 8 %_32, i64 24, i1 false)
  store i64 0, ptr %_31, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_32)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_30, ptr align 8 %_31, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_31)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_33)
  store i8 2, ptr %_33, align 8
  %29 = getelementptr inbounds i8, ptr %_26, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %29, ptr align 8 %_27, i64 24, i1 false)
  %30 = getelementptr inbounds i8, ptr %_26, i64 152
  store i32 %_28, ptr %30, align 8
  %31 = getelementptr inbounds i8, ptr %_26, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %31, ptr align 8 %_29, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_26, ptr align 8 %_30, i64 32, i1 false)
  %32 = getelementptr inbounds i8, ptr %_26, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %32, ptr align 8 %_33, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_33)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_30)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_29)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_27)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %33 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_26) #22
  %_25.0 = extractvalue { i64, ptr } %33, 0
  %_25.1 = extractvalue { i64, ptr } %33, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_26)
  %34 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_25.0, ptr %34, align 8
  %35 = getelementptr inbounds i8, ptr %34, i64 8
  store ptr %_25.1, ptr %35, align 8
  store i8 1, ptr %_0, align 8
  br label %bb88

bb10:                                             ; preds = %bb8
  br label %bb24

bb88:                                             ; preds = %bb18, %bb11
  br label %bb89

bb24:                                             ; preds = %bb22, %bb10
  %36 = load i8, ptr %new, align 1, !range !4, !noundef !3
  %37 = trunc i8 %36 to i1
  %_202 = zext i1 %37 to i64
  switch i64 %_202, label %bb61 [
    i64 1, label %bb96
    i64 0, label %bb95
  ]

bb23:                                             ; preds = %bb7
  call void @llvm.lifetime.end.p0(i64 noundef 7, ptr noundef %target_head) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %t)
  call void @llvm.lifetime.start.p0(i64 1, ptr %_207)
  %38 = load i8, ptr %new, align 1, !range !4, !noundef !3
  %39 = trunc i8 %38 to i1
  %_208 = zext i1 %39 to i64
  switch i64 %_208, label %bb61 [
    i64 1, label %bb100
    i64 0, label %bb99
  ]

bb16:                                             ; preds = %bb7
  %_40 = call noundef i64 @llvm.bpf.passthrough.i64.i64(i32 noundef zeroext 12, i64 noundef 44) #22
  %_36 = getelementptr inbounds i8, ptr %st, i64 %_40
  %_35 = load i8, ptr %_36, align 1, !noundef !3
  %40 = icmp eq i8 %_35, 0
  br i1 %40, label %bb18, label %bb22

bb61:                                             ; preds = %bb59, %bb60, %bb24, %bb23
  unreachable

bb100:                                            ; preds = %bb23
  store i8 1, ptr %_207, align 1
  br label %bb98

bb99:                                             ; preds = %bb23
  store i8 0, ptr %_207, align 1
  br label %bb98

bb98:                                             ; preds = %bb99, %bb100
  %41 = load i8, ptr %_207, align 1, !range !4, !noundef !3
  %42 = trunc i8 %41 to i1
  %_70 = xor i1 %42, true
  call void @llvm.lifetime.end.p0(i64 1, ptr %_207)
  %_69 = call noundef zeroext i1 @llvm.expect.with.probability.i1(i1 noundef zeroext %_70, i1 noundef zeroext true, double noundef 5.000000e-01) #22
  br i1 %_69, label %bb30, label %bb34

bb34:                                             ; preds = %bb98
  %_81 = getelementptr inbounds i8, ptr %new, i64 1
; call core::ptr::read_unaligned
  call void @_ZN4core3ptr14read_unaligned17hfb0286d8a885119bE(ptr noalias nocapture noundef sret([32 x i8]) align 1 dereferenceable(32) %t, ptr noundef %_81) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_85)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_209)
; call core::array::<impl core::default::Default for [T; 32]>::default
  call void @"_ZN4core5array76_$LT$impl$u20$core..default..Default$u20$for$u20$$u5b$T$u3b$$u20$32$u5d$$GT$7default17hf39cfabd391f7201E"(ptr noalias nocapture noundef sret([32 x i8]) align 1 dereferenceable(32) %_209) #22
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_85, ptr align 1 %_209, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_209)
  call void @llvm.lifetime.start.p0(i64 1, ptr %9)
  %43 = call i32 @memcmp(ptr %t, ptr %_85, i64 32)
  %44 = icmp eq i32 %43, 0
  %45 = zext i1 %44 to i8
  store i8 %45, ptr %9, align 1
  %46 = load i8, ptr %9, align 1, !range !4, !noundef !3
  %_84 = trunc i8 %46 to i1
  call void @llvm.lifetime.end.p0(i64 1, ptr %9)
  br i1 %_84, label %bb36, label %bb41

bb30:                                             ; preds = %bb98
  call void @llvm.lifetime.start.p0(i64 160, ptr %_72)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_73)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_73, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_1ba5e1e397ae92b788c97e688ac0b362) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_74 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 89) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_75)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_75, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_1ba5e1e397ae92b788c97e688ac0b362) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_76)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_77)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_78)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_78, align 8
  %47 = getelementptr inbounds i8, ptr %_78, i64 8
  store i64 103, ptr %47, align 8
  %48 = getelementptr inbounds i8, ptr %_78, i64 16
  store i32 176, ptr %48, align 8
  %49 = getelementptr inbounds i8, ptr %_77, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %49, ptr align 8 %_78, i64 24, i1 false)
  store i64 0, ptr %_77, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_78)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_76, ptr align 8 %_77, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_77)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_79)
  store i8 2, ptr %_79, align 8
  %50 = getelementptr inbounds i8, ptr %_72, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %50, ptr align 8 %_73, i64 24, i1 false)
  %51 = getelementptr inbounds i8, ptr %_72, i64 152
  store i32 %_74, ptr %51, align 8
  %52 = getelementptr inbounds i8, ptr %_72, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %52, ptr align 8 %_75, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_72, ptr align 8 %_76, i64 32, i1 false)
  %53 = getelementptr inbounds i8, ptr %_72, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %53, ptr align 8 %_79, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_79)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_76)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_75)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_73)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %54 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_72) #22
  %_71.0 = extractvalue { i64, ptr } %54, 0
  %_71.1 = extractvalue { i64, ptr } %54, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_72)
  %55 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_71.0, ptr %55, align 8
  %56 = getelementptr inbounds i8, ptr %55, i64 8
  store ptr %_71.1, ptr %56, align 8
  store i8 1, ptr %_0, align 8
  br label %bb87

bb41:                                             ; preds = %bb34
  call void @llvm.lifetime.end.p0(i64 32, ptr %_85)
  call void @llvm.lifetime.start.p0(i64 1, ptr %8)
  %57 = call i32 @memcmp(ptr %t, ptr %holder_key, i64 32)
  %58 = icmp eq i32 %57, 0
  %59 = zext i1 %58 to i8
  store i8 %59, ptr %8, align 1
  %60 = load i8, ptr %8, align 1, !range !4, !noundef !3
  %_104 = trunc i8 %60 to i1
  call void @llvm.lifetime.end.p0(i64 1, ptr %8)
  %_103 = zext i1 %_104 to i8
  %_102 = call noundef zeroext i8 @llvm.bpf.passthrough.i8.i8(i32 noundef zeroext 4, i8 noundef zeroext %_103) #22
  %_101 = and i8 %_102, 1
  %_100 = icmp eq i8 %_101, 0
  %_99 = call noundef zeroext i1 @llvm.expect.with.probability.i1(i1 noundef zeroext %_100, i1 noundef zeroext true, double noundef 5.000000e-01) #22
  br i1 %_99, label %bb44, label %bb54

bb36:                                             ; preds = %bb34
  call void @llvm.lifetime.end.p0(i64 32, ptr %_85)
  call void @llvm.lifetime.start.p0(i64 160, ptr %_88)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_89)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_89, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_0e3505805f4905816c1bd644811a7869) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_90 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 30) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_91)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_91, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_0e3505805f4905816c1bd644811a7869) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_92)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_93)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_94)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_94, align 8
  %61 = getelementptr inbounds i8, ptr %_94, i64 8
  store i64 103, ptr %61, align 8
  %62 = getelementptr inbounds i8, ptr %_94, i64 16
  store i32 177, ptr %62, align 8
  %63 = getelementptr inbounds i8, ptr %_93, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %63, ptr align 8 %_94, i64 24, i1 false)
  store i64 0, ptr %_93, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_94)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_92, ptr align 8 %_93, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_93)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_95)
  store i8 2, ptr %_95, align 8
  %64 = getelementptr inbounds i8, ptr %_88, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %64, ptr align 8 %_89, i64 24, i1 false)
  %65 = getelementptr inbounds i8, ptr %_88, i64 152
  store i32 %_90, ptr %65, align 8
  %66 = getelementptr inbounds i8, ptr %_88, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %66, ptr align 8 %_91, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_88, ptr align 8 %_92, i64 32, i1 false)
  %67 = getelementptr inbounds i8, ptr %_88, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %67, ptr align 8 %_95, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_95)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_92)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_91)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_89)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %68 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_88) #22
  %_87.0 = extractvalue { i64, ptr } %68, 0
  %_87.1 = extractvalue { i64, ptr } %68, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_88)
  call void @llvm.lifetime.start.p0(i64 64, ptr %_96)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_97)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_97, ptr align 1 %t, i64 32, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_98)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_212)
; call core::array::<impl core::default::Default for [T; 32]>::default
  call void @"_ZN4core5array76_$LT$impl$u20$core..default..Default$u20$for$u20$$u5b$T$u3b$$u20$32$u5d$$GT$7default17hf39cfabd391f7201E"(ptr noalias nocapture noundef sret([32 x i8]) align 1 dereferenceable(32) %_212) #22
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_98, ptr align 1 %_212, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_212)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_96, ptr align 1 %_97, i64 32, i1 false)
  %69 = getelementptr inbounds i8, ptr %_96, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %69, ptr align 1 %_98, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_98)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_97)
; call anchor_lang::error::Error::with_pubkeys
  %70 = call { i64, ptr } @_ZN11anchor_lang5error5Error12with_pubkeys17hca6dbbbe6a9a5da7E(i64 noundef %_87.0, ptr noundef %_87.1, ptr noalias nocapture noundef readonly align 1 dereferenceable(64) %_96) #22
  %_86.0 = extractvalue { i64, ptr } %70, 0
  %_86.1 = extractvalue { i64, ptr } %70, 1
  call void @llvm.lifetime.end.p0(i64 64, ptr %_96)
  %71 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_86.0, ptr %71, align 8
  %72 = getelementptr inbounds i8, ptr %71, i64 8
  store ptr %_86.1, ptr %72, align 8
  store i8 1, ptr %_0, align 8
  br label %bb87

bb54:                                             ; preds = %bb44, %bb41
  call void @llvm.lifetime.start.p0(i64 1, ptr %6)
  %73 = load volatile i8, ptr %holder_key, align 1
  store i8 %73, ptr %6, align 1
  %_130 = load i8, ptr %6, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %6)
  call void @llvm.lifetime.start.p0(i64 1, ptr %5)
  %74 = load volatile i8, ptr %holder_key, align 1
  store i8 %74, ptr %5, align 1
  %_133 = load i8, ptr %5, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %5)
  call void @llvm.lifetime.start.p0(i64 160, ptr %_137)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_138)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_138, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_861c8964bbad6d9cede9df277e628fe9) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_139 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 19) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_140)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_140, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_861c8964bbad6d9cede9df277e628fe9) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_141)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_142)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_143)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_143, align 8
  %75 = getelementptr inbounds i8, ptr %_143, i64 8
  store i64 103, ptr %75, align 8
  %76 = getelementptr inbounds i8, ptr %_143, i64 16
  store i32 182, ptr %76, align 8
  %77 = getelementptr inbounds i8, ptr %_142, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %77, ptr align 8 %_143, i64 24, i1 false)
  store i64 0, ptr %_142, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_143)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_141, ptr align 8 %_142, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_142)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_144)
  store i8 2, ptr %_144, align 8
  %78 = getelementptr inbounds i8, ptr %_137, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %78, ptr align 8 %_138, i64 24, i1 false)
  %79 = getelementptr inbounds i8, ptr %_137, i64 152
  store i32 %_139, ptr %79, align 8
  %80 = getelementptr inbounds i8, ptr %_137, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %80, ptr align 8 %_140, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_137, ptr align 8 %_141, i64 32, i1 false)
  %81 = getelementptr inbounds i8, ptr %_137, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %81, ptr align 8 %_144, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_144)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_141)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_140)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_138)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %82 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_137) #22
  %_136.0 = extractvalue { i64, ptr } %82, 0
  %_136.1 = extractvalue { i64, ptr } %82, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_137)
  %83 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_136.0, ptr %83, align 8
  %84 = getelementptr inbounds i8, ptr %83, i64 8
  store ptr %_136.1, ptr %84, align 8
  store i8 1, ptr %_0, align 8
  br label %bb87

bb44:                                             ; preds = %bb41
  call void @llvm.lifetime.start.p0(i64 1, ptr %7)
  %85 = call i32 @memcmp(ptr %t, ptr %sharing, i64 32)
  %86 = icmp eq i32 %85, 0
  %87 = zext i1 %86 to i8
  store i8 %87, ptr %7, align 1
  %88 = load i8, ptr %7, align 1, !range !4, !noundef !3
  %_215 = trunc i8 %88 to i1
  call void @llvm.lifetime.end.p0(i64 1, ptr %7)
  %_106 = xor i1 %_215, true
  %_105 = call noundef zeroext i1 @llvm.expect.with.probability.i1(i1 noundef zeroext %_106, i1 noundef zeroext true, double noundef 3.700000e-01) #22
  br i1 %_105, label %bb46, label %bb54

bb46:                                             ; preds = %bb44
  call void @llvm.lifetime.start.p0(i64 noundef 7, ptr noundef %target_head) #22
  call void @llvm.lifetime.start.p0(i64 noundef 25, ptr noundef %target_tail) #22
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target_head, ptr align 1 %t, i64 7, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr %b1)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_229, ptr align 1 %t, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %b1, ptr align 1 %_229, i64 32, i1 false)
  %_115 = getelementptr inbounds i8, ptr %b1, i64 7
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target_tail, ptr align 1 %_115, i64 25, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %b1)
  %_122 = load i64, ptr %fee, align 8, !noundef !3
  %_121 = icmp eq i64 %_122, 0
  %_120 = call noundef zeroext i1 @llvm.expect.with.probability.i1(i1 noundef zeroext %_121, i1 noundef zeroext true, double noundef 5.000000e-01) #22
  br i1 %_120, label %bb50, label %bb52

bb87:                                             ; preds = %bb30, %bb36, %bb54
  call void @llvm.lifetime.end.p0(i64 32, ptr %t)
  br label %bb89

bb52:                                             ; preds = %bb46
  br label %bb53

bb50:                                             ; preds = %bb46
  %_125 = call noundef zeroext i1 @llvm.annotation.i1.p0(i1 noundef zeroext true, ptr noundef @alloc_914b2c69d7eca30497b9feaf15ac92f1, ptr noundef @alloc_914b2c69d7eca30497b9feaf15ac92f1, i32 noundef zeroext 0) #22
  br label %bb53

bb53:                                             ; preds = %bb50, %bb52
  call void @llvm.lifetime.end.p0(i64 32, ptr %t)
  br label %bb58

bb58:                                             ; preds = %bb95, %bb53
  call void @llvm.lifetime.start.p0(i64 1, ptr %cashback)
  br i1 %holder, label %bb59, label %bb60

bb89:                                             ; preds = %bb96, %bb88, %bb87
  br label %bb90

bb18:                                             ; preds = %bb16
  call void @llvm.lifetime.start.p0(i64 160, ptr %_42)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_43)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_43, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_f94f166953c814e4161e699857179a1e) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_44 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 84) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_45)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_45, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_f94f166953c814e4161e699857179a1e) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_46)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_47)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_48)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_48, align 8
  %89 = getelementptr inbounds i8, ptr %_48, i64 8
  store i64 103, ptr %89, align 8
  %90 = getelementptr inbounds i8, ptr %_48, i64 16
  store i32 166, ptr %90, align 8
  %91 = getelementptr inbounds i8, ptr %_47, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %91, ptr align 8 %_48, i64 24, i1 false)
  store i64 0, ptr %_47, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_48)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_46, ptr align 8 %_47, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_47)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_49)
  store i8 2, ptr %_49, align 8
  %92 = getelementptr inbounds i8, ptr %_42, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %92, ptr align 8 %_43, i64 24, i1 false)
  %93 = getelementptr inbounds i8, ptr %_42, i64 152
  store i32 %_44, ptr %93, align 8
  %94 = getelementptr inbounds i8, ptr %_42, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %94, ptr align 8 %_45, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_42, ptr align 8 %_46, i64 32, i1 false)
  %95 = getelementptr inbounds i8, ptr %_42, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %95, ptr align 8 %_49, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_49)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_46)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_45)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_43)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %96 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_42) #22
  %_41.0 = extractvalue { i64, ptr } %96, 0
  %_41.1 = extractvalue { i64, ptr } %96, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_42)
  %97 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_41.0, ptr %97, align 8
  %98 = getelementptr inbounds i8, ptr %97, i64 8
  store ptr %_41.1, ptr %98, align 8
  store i8 1, ptr %_0, align 8
  br label %bb88

bb22:                                             ; preds = %bb16
  br label %bb24

bb96:                                             ; preds = %bb24
  call void @llvm.lifetime.start.p0(i64 160, ptr %_51)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_52)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_52, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_b5f839a6bda937f2cae73e49fc88071f) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_53 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 90) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_54)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_54, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_b5f839a6bda937f2cae73e49fc88071f) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_55)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_56)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_57)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_57, align 8
  %99 = getelementptr inbounds i8, ptr %_57, i64 8
  store i64 103, ptr %99, align 8
  %100 = getelementptr inbounds i8, ptr %_57, i64 16
  store i32 168, ptr %100, align 8
  %101 = getelementptr inbounds i8, ptr %_56, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %101, ptr align 8 %_57, i64 24, i1 false)
  store i64 0, ptr %_56, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_57)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_55, ptr align 8 %_56, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_56)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_58)
  store i8 2, ptr %_58, align 8
  %102 = getelementptr inbounds i8, ptr %_51, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %102, ptr align 8 %_52, i64 24, i1 false)
  %103 = getelementptr inbounds i8, ptr %_51, i64 152
  store i32 %_53, ptr %103, align 8
  %104 = getelementptr inbounds i8, ptr %_51, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %104, ptr align 8 %_54, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_51, ptr align 8 %_55, i64 32, i1 false)
  %105 = getelementptr inbounds i8, ptr %_51, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %105, ptr align 8 %_58, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_58)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_55)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_54)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_52)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %106 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_51) #22
  %_50.0 = extractvalue { i64, ptr } %106, 0
  %_50.1 = extractvalue { i64, ptr } %106, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_51)
  %107 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_50.0, ptr %107, align 8
  %108 = getelementptr inbounds i8, ptr %107, i64 8
  store ptr %_50.1, ptr %108, align 8
  store i8 1, ptr %_0, align 8
  br label %bb89

bb95:                                             ; preds = %bb24
  call void @llvm.lifetime.start.p0(i64 32, ptr %b)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_228, ptr align 1 %holder_key, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %b, ptr align 1 %_228, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target_head, ptr align 1 %b, i64 7, i1 false)
  %_64 = getelementptr inbounds i8, ptr %b, i64 7
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target_tail, ptr align 1 %_64, i64 25, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %b)
  br label %bb58

bb90:                                             ; preds = %bb86, %bb89
  call void @llvm.lifetime.end.p0(i64 25, ptr %target_tail)
  call void @llvm.lifetime.end.p0(i64 7, ptr %target_head)
  br label %bb91

bb60:                                             ; preds = %bb58
  %109 = getelementptr inbounds i8, ptr %st, i64 42
  %110 = load i8, ptr %109, align 2, !range !4, !noundef !3
  %111 = trunc i8 %110 to i1
  %112 = zext i1 %111 to i8
  store i8 %112, ptr %cashback, align 1
  %113 = load i64, ptr %fee, align 8, !range !2, !noundef !3
  store i64 %113, ptr %_146, align 8
  %114 = load i64, ptr %_146, align 8, !noundef !3
  switch i64 %114, label %bb61 [
    i64 0, label %bb85
    i64 1, label %bb62
  ]

bb59:                                             ; preds = %bb58
  store i8 0, ptr %cashback, align 1
  %115 = load i64, ptr %fee, align 8, !range !2, !noundef !3
  store i64 %115, ptr %_146, align 8
  %116 = load i64, ptr %_146, align 8, !noundef !3
  switch i64 %116, label %bb61 [
    i64 0, label %bb85
    i64 1, label %bb117
  ]

bb85:                                             ; preds = %bb80, %bb59, %bb60
  call void @llvm.lifetime.start.p0(i64 32, ptr %_195)
  call void @llvm.lifetime.start.p0(i64 32, ptr %b2)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %b2, ptr align 1 %target_head, i64 7, i1 false)
  %_200 = getelementptr inbounds i8, ptr %b2, i64 7
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_200, ptr align 1 %target_tail, i64 25, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_201)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_201, ptr align 1 %b2, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_230, ptr align 1 %_201, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_201)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_195, ptr align 1 %_230, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %b2)
  %117 = getelementptr inbounds i8, ptr %_0, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %117, ptr align 1 %_195, i64 32, i1 false)
  store i8 0, ptr %_0, align 8
  call void @llvm.lifetime.end.p0(i64 32, ptr %_195)
  call void @llvm.lifetime.end.p0(i64 1, ptr %cashback)
  call void @llvm.lifetime.end.p0(i64 25, ptr %target_tail)
  call void @llvm.lifetime.end.p0(i64 7, ptr %target_head)
  br label %bb91

bb62:                                             ; preds = %bb60
  %118 = getelementptr inbounds i8, ptr %fee, i64 8
  %119 = load i64, ptr %118, align 8, !noundef !3
  store i64 %119, ptr %f, align 8
  call void @llvm.lifetime.start.p0(i64 1, ptr %_148)
  %120 = getelementptr inbounds i8, ptr %st, i64 43
  %121 = load i8, ptr %120, align 1, !range !4, !noundef !3
  %122 = trunc i8 %121 to i1
  %123 = zext i1 %122 to i8
  store i8 %123, ptr %_148, align 1
  %124 = load i8, ptr %_148, align 1, !range !4, !noundef !3
  %125 = trunc i8 %124 to i1
  br i1 %125, label %bb63, label %bb67

bb67:                                             ; preds = %bb62
  call void @llvm.lifetime.end.p0(i64 1, ptr %_148)
  %126 = load i8, ptr %cashback, align 1, !range !4, !noundef !3
  %_158 = trunc i8 %126 to i1
  br i1 %_158, label %bb68, label %bb69

bb63:                                             ; preds = %bb117, %bb62
  call void @llvm.lifetime.start.p0(i64 160, ptr %_150)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_151)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_151, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_e75cefee4bb91125af0ea8444b842ed0) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_152 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 91) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_153)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_153, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_e75cefee4bb91125af0ea8444b842ed0) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_154)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_155)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_156)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_156, align 8
  %127 = getelementptr inbounds i8, ptr %_156, i64 8
  store i64 103, ptr %127, align 8
  %128 = getelementptr inbounds i8, ptr %_156, i64 16
  store i32 196, ptr %128, align 8
  %129 = getelementptr inbounds i8, ptr %_155, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %129, ptr align 8 %_156, i64 24, i1 false)
  store i64 0, ptr %_155, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_156)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_154, ptr align 8 %_155, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_155)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_157)
  store i8 2, ptr %_157, align 8
  %130 = getelementptr inbounds i8, ptr %_150, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %130, ptr align 8 %_151, i64 24, i1 false)
  %131 = getelementptr inbounds i8, ptr %_150, i64 152
  store i32 %_152, ptr %131, align 8
  %132 = getelementptr inbounds i8, ptr %_150, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %132, ptr align 8 %_153, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_150, ptr align 8 %_154, i64 32, i1 false)
  %133 = getelementptr inbounds i8, ptr %_150, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %133, ptr align 8 %_157, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_157)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_154)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_153)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_151)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %134 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_150) #22
  %_149.0 = extractvalue { i64, ptr } %134, 0
  %_149.1 = extractvalue { i64, ptr } %134, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_150)
  %135 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_149.0, ptr %135, align 8
  %136 = getelementptr inbounds i8, ptr %135, i64 8
  store ptr %_149.1, ptr %136, align 8
  store i8 1, ptr %_0, align 8
  call void @llvm.lifetime.end.p0(i64 1, ptr %_148)
  br label %bb86

bb69:                                             ; preds = %bb118, %bb67
  call void @llvm.lifetime.start.p0(i64 1, ptr %4)
  %137 = load volatile i8, ptr %holder_key, align 1
  store i8 %137, ptr %4, align 1
  %_168 = load i8, ptr %4, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %4)
  %138 = getelementptr inbounds i8, ptr %st, i64 45
  %139 = load i8, ptr %138, align 1, !range !4, !noundef !3
  %_171 = trunc i8 %139 to i1
  br i1 %_171, label %bb77, label %bb73

bb68:                                             ; preds = %bb67
  call void @llvm.lifetime.start.p0(i64 160, ptr %_160)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_161)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_161, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_835bb996f1795bf0338da0490417da62) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_162 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 80) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_163)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_163, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_835bb996f1795bf0338da0490417da62) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_164)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_165)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_166)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_166, align 8
  %140 = getelementptr inbounds i8, ptr %_166, i64 8
  store i64 103, ptr %140, align 8
  %141 = getelementptr inbounds i8, ptr %_166, i64 16
  store i32 200, ptr %141, align 8
  %142 = getelementptr inbounds i8, ptr %_165, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %142, ptr align 8 %_166, i64 24, i1 false)
  store i64 0, ptr %_165, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_166)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_164, ptr align 8 %_165, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_165)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_167)
  store i8 2, ptr %_167, align 8
  %143 = getelementptr inbounds i8, ptr %_160, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %143, ptr align 8 %_161, i64 24, i1 false)
  %144 = getelementptr inbounds i8, ptr %_160, i64 152
  store i32 %_162, ptr %144, align 8
  %145 = getelementptr inbounds i8, ptr %_160, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %145, ptr align 8 %_163, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_160, ptr align 8 %_164, i64 32, i1 false)
  %146 = getelementptr inbounds i8, ptr %_160, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %146, ptr align 8 %_167, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_167)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_164)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_163)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_161)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %147 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_160) #22
  %_159.0 = extractvalue { i64, ptr } %147, 0
  %_159.1 = extractvalue { i64, ptr } %147, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_160)
  %148 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_159.0, ptr %148, align 8
  %149 = getelementptr inbounds i8, ptr %148, i64 8
  store ptr %_159.1, ptr %149, align 8
  store i8 1, ptr %_0, align 8
  br label %bb86

bb86:                                             ; preds = %bb63, %bb81, %bb73, %bb68
  call void @llvm.lifetime.end.p0(i64 1, ptr %cashback)
  br label %bb90

bb117:                                            ; preds = %bb59
  %150 = getelementptr inbounds i8, ptr %fee, i64 8
  %151 = load i64, ptr %150, align 8, !noundef !3
  store i64 %151, ptr %f, align 8
  call void @llvm.lifetime.start.p0(i64 1, ptr %_148)
  %152 = getelementptr inbounds i8, ptr %st, i64 43
  %153 = load i8, ptr %152, align 1, !range !4, !noundef !3
  %154 = trunc i8 %153 to i1
  %155 = zext i1 %154 to i8
  store i8 %155, ptr %_148, align 1
  %156 = load i8, ptr %_148, align 1, !range !4, !noundef !3
  %157 = trunc i8 %156 to i1
  br i1 %157, label %bb63, label %bb118

bb118:                                            ; preds = %bb117
  call void @llvm.lifetime.end.p0(i64 1, ptr %_148)
  br label %bb69

bb73:                                             ; preds = %bb69
  call void @llvm.lifetime.start.p0(i64 160, ptr %_173)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_174)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_174, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_01eaaa187d2be542d4425f23ab284310) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_175 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 77) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_176)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_176, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_01eaaa187d2be542d4425f23ab284310) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_177)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_178)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_179)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_179, align 8
  %158 = getelementptr inbounds i8, ptr %_179, i64 8
  store i64 103, ptr %158, align 8
  %159 = getelementptr inbounds i8, ptr %_179, i64 16
  store i32 204, ptr %159, align 8
  %160 = getelementptr inbounds i8, ptr %_178, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %160, ptr align 8 %_179, i64 24, i1 false)
  store i64 0, ptr %_178, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_179)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_177, ptr align 8 %_178, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_178)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_180)
  store i8 2, ptr %_180, align 8
  %161 = getelementptr inbounds i8, ptr %_173, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %161, ptr align 8 %_174, i64 24, i1 false)
  %162 = getelementptr inbounds i8, ptr %_173, i64 152
  store i32 %_175, ptr %162, align 8
  %163 = getelementptr inbounds i8, ptr %_173, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %163, ptr align 8 %_176, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_173, ptr align 8 %_177, i64 32, i1 false)
  %164 = getelementptr inbounds i8, ptr %_173, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %164, ptr align 8 %_180, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_180)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_177)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_176)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_174)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %165 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_173) #22
  %_172.0 = extractvalue { i64, ptr } %165, 0
  %_172.1 = extractvalue { i64, ptr } %165, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_173)
  %166 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_172.0, ptr %166, align 8
  %167 = getelementptr inbounds i8, ptr %166, i64 8
  store ptr %_172.1, ptr %167, align 8
  store i8 1, ptr %_0, align 8
  br label %bb86

bb77:                                             ; preds = %bb69
  %168 = load i64, ptr %f, align 8, !noundef !3
  %169 = icmp eq i64 %168, 0
  br i1 %169, label %bb81, label %bb78

bb81:                                             ; preds = %bb79, %bb77
  call void @llvm.lifetime.start.p0(i64 160, ptr %_184)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_185)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_185, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_973adb9e8664e25d4750ddb14e0de56a) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_186 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 78) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_187)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_187, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_973adb9e8664e25d4750ddb14e0de56a) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_188)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_189)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_190)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_190, align 8
  %170 = getelementptr inbounds i8, ptr %_190, i64 8
  store i64 103, ptr %170, align 8
  %171 = getelementptr inbounds i8, ptr %_190, i64 16
  store i32 208, ptr %171, align 8
  %172 = getelementptr inbounds i8, ptr %_189, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %172, ptr align 8 %_190, i64 24, i1 false)
  store i64 0, ptr %_189, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_190)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_188, ptr align 8 %_189, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_189)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_191)
  store i8 2, ptr %_191, align 8
  %173 = getelementptr inbounds i8, ptr %_184, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %173, ptr align 8 %_185, i64 24, i1 false)
  %174 = getelementptr inbounds i8, ptr %_184, i64 152
  store i32 %_186, ptr %174, align 8
  %175 = getelementptr inbounds i8, ptr %_184, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %175, ptr align 8 %_187, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_184, ptr align 8 %_188, i64 32, i1 false)
  %176 = getelementptr inbounds i8, ptr %_184, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %176, ptr align 8 %_191, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_191)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_188)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_187)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_185)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %177 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_184) #22
  %_183.0 = extractvalue { i64, ptr } %177, 0
  %_183.1 = extractvalue { i64, ptr } %177, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_184)
  %178 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_183.0, ptr %178, align 8
  %179 = getelementptr inbounds i8, ptr %178, i64 8
  store ptr %_183.1, ptr %179, align 8
  store i8 1, ptr %_0, align 8
  br label %bb86

bb78:                                             ; preds = %bb77
  %180 = getelementptr inbounds i8, ptr %st, i64 32
  %_182 = load i64, ptr %180, align 8, !noundef !3
  %181 = load i64, ptr %f, align 8, !noundef !3
  %_181 = icmp ugt i64 %181, %_182
  br i1 %_181, label %bb79, label %bb80

bb80:                                             ; preds = %bb78
  call void @llvm.lifetime.start.p0(i64 1, ptr %3)
  %182 = load volatile i8, ptr %holder_key, align 1
  store i8 %182, ptr %3, align 1
  %_192 = load i8, ptr %3, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %3)
  br label %bb85

bb79:                                             ; preds = %bb78
  br label %bb81

bb91:                                             ; preds = %bb2, %bb90, %bb85
  ret void
}

; Function Attrs: nounwind
define void @updated4149_validate(ptr dead_on_unwind noalias nocapture noundef writable sret([40 x i8]) align 8 dereferenceable(40) %_0, ptr noalias noundef readonly align 8 dereferenceable(48) %st, i8 noundef %0, i64 noundef %1, i64 %2, ptr noalias nocapture noundef align 1 dereferenceable(33) %new, ptr noalias noundef readonly align 1 dereferenceable(32) %holder_key, ptr noalias noundef readonly align 1 dereferenceable(32) %sharing) unnamed_addr #1 {
start:
  %3 = alloca [1 x i8], align 1
  %4 = alloca [1 x i8], align 1
  %5 = alloca [1 x i8], align 1
  %6 = alloca [1 x i8], align 1
  %7 = alloca [1 x i8], align 1
  %8 = alloca [1 x i8], align 1
  %9 = alloca [1 x i8], align 1
  %10 = alloca [1 x i8], align 1
  %11 = alloca [1 x i8], align 1
  %12 = alloca [1 x i8], align 1
  %13 = alloca [1 x i8], align 1
  %14 = alloca [1 x i8], align 1
  %15 = alloca [1 x i8], align 1
  %16 = alloca [1 x i8], align 1
  %17 = alloca [1 x i8], align 1
  %18 = alloca [1 x i8], align 1
  %19 = alloca [1 x i8], align 1
  %20 = alloca [1 x i8], align 1
  %_266 = alloca [32 x i8], align 1
  %_265 = alloca [32 x i8], align 1
  %_264 = alloca [32 x i8], align 1
  %_263 = alloca [32 x i8], align 1
  %_250 = alloca [32 x i8], align 1
  %_247 = alloca [8 x i8], align 8
  %_243 = alloca [32 x i8], align 1
  %_235 = alloca [32 x i8], align 1
  %b2 = alloca [32 x i8], align 1
  %_229 = alloca [32 x i8], align 1
  %_225 = alloca [72 x i8], align 8
  %_224 = alloca [24 x i8], align 8
  %_223 = alloca [32 x i8], align 8
  %_222 = alloca [32 x i8], align 8
  %_221 = alloca [24 x i8], align 8
  %_219 = alloca [24 x i8], align 8
  %_218 = alloca [160 x i8], align 8
  %_214 = alloca [72 x i8], align 8
  %_213 = alloca [24 x i8], align 8
  %_212 = alloca [32 x i8], align 8
  %_211 = alloca [32 x i8], align 8
  %_210 = alloca [24 x i8], align 8
  %_208 = alloca [24 x i8], align 8
  %_207 = alloca [160 x i8], align 8
  %_201 = alloca [72 x i8], align 8
  %_200 = alloca [24 x i8], align 8
  %_199 = alloca [32 x i8], align 8
  %_198 = alloca [32 x i8], align 8
  %_197 = alloca [24 x i8], align 8
  %_195 = alloca [24 x i8], align 8
  %_194 = alloca [160 x i8], align 8
  %_191 = alloca [72 x i8], align 8
  %_190 = alloca [24 x i8], align 8
  %_189 = alloca [32 x i8], align 8
  %_188 = alloca [32 x i8], align 8
  %_187 = alloca [24 x i8], align 8
  %_185 = alloca [24 x i8], align 8
  %_184 = alloca [160 x i8], align 8
  %_182 = alloca [1 x i8], align 1
  %f = alloca [8 x i8], align 8
  %_180 = alloca [8 x i8], align 8
  %cashback = alloca [1 x i8], align 1
  %b1 = alloca [32 x i8], align 1
  %_164 = alloca [72 x i8], align 8
  %_163 = alloca [24 x i8], align 8
  %_162 = alloca [32 x i8], align 8
  %_161 = alloca [32 x i8], align 8
  %_160 = alloca [24 x i8], align 8
  %_158 = alloca [24 x i8], align 8
  %_157 = alloca [160 x i8], align 8
  %_114 = alloca [32 x i8], align 1
  %_113 = alloca [32 x i8], align 1
  %k = alloca [32 x i8], align 1
  %_101 = alloca [64 x i8], align 1
  %_100 = alloca [72 x i8], align 8
  %_99 = alloca [24 x i8], align 8
  %_98 = alloca [32 x i8], align 8
  %_97 = alloca [32 x i8], align 8
  %_96 = alloca [24 x i8], align 8
  %_94 = alloca [24 x i8], align 8
  %_93 = alloca [160 x i8], align 8
  %_90 = alloca [32 x i8], align 1
  %_84 = alloca [72 x i8], align 8
  %_83 = alloca [24 x i8], align 8
  %_82 = alloca [32 x i8], align 8
  %_81 = alloca [32 x i8], align 8
  %_80 = alloca [24 x i8], align 8
  %_78 = alloca [24 x i8], align 8
  %_77 = alloca [160 x i8], align 8
  %t = alloca [32 x i8], align 1
  %b = alloca [32 x i8], align 1
  %_56 = alloca [72 x i8], align 8
  %_55 = alloca [24 x i8], align 8
  %_54 = alloca [32 x i8], align 8
  %_53 = alloca [32 x i8], align 8
  %_52 = alloca [24 x i8], align 8
  %_50 = alloca [24 x i8], align 8
  %_49 = alloca [160 x i8], align 8
  %_47 = alloca [72 x i8], align 8
  %_46 = alloca [24 x i8], align 8
  %_45 = alloca [32 x i8], align 8
  %_44 = alloca [32 x i8], align 8
  %_43 = alloca [24 x i8], align 8
  %_41 = alloca [24 x i8], align 8
  %_40 = alloca [160 x i8], align 8
  %_32 = alloca [72 x i8], align 8
  %_31 = alloca [24 x i8], align 8
  %_30 = alloca [32 x i8], align 8
  %_29 = alloca [32 x i8], align 8
  %_28 = alloca [24 x i8], align 8
  %_26 = alloca [24 x i8], align 8
  %_25 = alloca [160 x i8], align 8
  %target_tail = alloca [25 x i8], align 1
  %target_head = alloca [7 x i8], align 1
  %holder = alloca [1 x i8], align 1
  %_16 = alloca [72 x i8], align 8
  %_15 = alloca [24 x i8], align 8
  %_14 = alloca [32 x i8], align 8
  %_13 = alloca [32 x i8], align 8
  %_12 = alloca [24 x i8], align 8
  %_10 = alloca [24 x i8], align 8
  %_9 = alloca [160 x i8], align 8
  %fee = alloca [16 x i8], align 8
  %hopt = alloca [1 x i8], align 1
  store i8 %0, ptr %hopt, align 1
  store i64 %1, ptr %fee, align 8
  %21 = getelementptr inbounds i8, ptr %fee, i64 8
  store i64 %2, ptr %21, align 8
  %22 = getelementptr inbounds i8, ptr %st, i64 40
  %23 = load i8, ptr %22, align 8, !range !4, !noundef !3
  %_7 = trunc i8 %23 to i1
  br i1 %_7, label %bb1, label %bb5

bb5:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 1, ptr %holder)
  %24 = load i8, ptr %hopt, align 1, !range !12, !noundef !3
  %25 = icmp eq i8 %24, 2
  %_236 = select i1 %25, i64 0, i64 1
  switch i64 %_236, label %bb54 [
    i64 0, label %bb87
    i64 1, label %bb88
  ]

bb1:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 160, ptr %_9)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_10)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_10, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_eb4f91695bc6f999067c65f428fcc4d8) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_11 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 88) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_12)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_12, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_eb4f91695bc6f999067c65f428fcc4d8) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_13)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_14)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_15)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_15, align 8
  %26 = getelementptr inbounds i8, ptr %_15, i64 8
  store i64 103, ptr %26, align 8
  %27 = getelementptr inbounds i8, ptr %_15, i64 16
  store i32 212, ptr %27, align 8
  %28 = getelementptr inbounds i8, ptr %_14, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %28, ptr align 8 %_15, i64 24, i1 false)
  store i64 0, ptr %_14, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_15)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_13, ptr align 8 %_14, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_14)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_16)
  store i8 2, ptr %_16, align 8
  %29 = getelementptr inbounds i8, ptr %_9, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %29, ptr align 8 %_10, i64 24, i1 false)
  %30 = getelementptr inbounds i8, ptr %_9, i64 152
  store i32 %_11, ptr %30, align 8
  %31 = getelementptr inbounds i8, ptr %_9, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %31, ptr align 8 %_12, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_9, ptr align 8 %_13, i64 32, i1 false)
  %32 = getelementptr inbounds i8, ptr %_9, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %32, ptr align 8 %_16, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_16)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_13)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_12)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_10)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %33 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_9) #22
  %_8.0 = extractvalue { i64, ptr } %33, 0
  %_8.1 = extractvalue { i64, ptr } %33, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_9)
  %34 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_8.0, ptr %34, align 8
  %35 = getelementptr inbounds i8, ptr %34, i64 8
  store ptr %_8.1, ptr %35, align 8
  store i8 1, ptr %_0, align 8
  br label %bb84

bb54:                                             ; preds = %bb52, %bb53, %bb22, %bb5
  unreachable

bb87:                                             ; preds = %bb5
  store i8 0, ptr %holder, align 1
  br label %bb86

bb88:                                             ; preds = %bb5
  %36 = load i8, ptr %hopt, align 1, !range !4, !noundef !3
  %_237 = trunc i8 %36 to i1
  %37 = zext i1 %_237 to i8
  store i8 %37, ptr %holder, align 1
  br label %bb86

bb86:                                             ; preds = %bb88, %bb87
  call void @llvm.lifetime.start.p0(i64 7, ptr %target_head)
  call void @llvm.lifetime.start.p0(i64 25, ptr %target_tail)
  %38 = getelementptr inbounds i8, ptr %st, i64 41
  %39 = load i8, ptr %38, align 1, !range !4, !noundef !3
  %_21 = trunc i8 %39 to i1
  %_20 = zext i1 %_21 to i8
  %40 = icmp eq i8 %_20, 1
  br i1 %40, label %bb7, label %bb6

bb7:                                              ; preds = %bb86
  %41 = load i8, ptr %holder, align 1, !range !4, !noundef !3
  %_23 = trunc i8 %41 to i1
  %_22 = call noundef zeroext i1 @llvm.expect.with.probability.i1(i1 noundef zeroext %_23, i1 noundef zeroext true, double noundef 6.250000e-01) #22
  br i1 %_22, label %bb13, label %bb9

bb6:                                              ; preds = %bb86
  %42 = load i8, ptr %holder, align 1, !range !4, !noundef !3
  %_37 = trunc i8 %42 to i1
  %_36 = call noundef zeroext i1 @llvm.expect.with.probability.i1(i1 noundef zeroext %_37, i1 noundef zeroext true, double noundef 4.900000e-01) #22
  br i1 %_36, label %bb15, label %bb21

bb9:                                              ; preds = %bb7
  call void @llvm.lifetime.start.p0(i64 160, ptr %_25)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_26)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_26, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_8f95cb73e89711d65e95d13598508b19) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_27 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 83) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_28)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_28, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_8f95cb73e89711d65e95d13598508b19) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_29)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_30)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_31)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_31, align 8
  %43 = getelementptr inbounds i8, ptr %_31, i64 8
  store i64 103, ptr %43, align 8
  %44 = getelementptr inbounds i8, ptr %_31, i64 16
  store i32 217, ptr %44, align 8
  %45 = getelementptr inbounds i8, ptr %_30, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %45, ptr align 8 %_31, i64 24, i1 false)
  store i64 0, ptr %_30, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_31)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_29, ptr align 8 %_30, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_30)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_32)
  store i8 2, ptr %_32, align 8
  %46 = getelementptr inbounds i8, ptr %_25, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %46, ptr align 8 %_26, i64 24, i1 false)
  %47 = getelementptr inbounds i8, ptr %_25, i64 152
  store i32 %_27, ptr %47, align 8
  %48 = getelementptr inbounds i8, ptr %_25, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %48, ptr align 8 %_28, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_25, ptr align 8 %_29, i64 32, i1 false)
  %49 = getelementptr inbounds i8, ptr %_25, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %49, ptr align 8 %_32, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_32)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_29)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_28)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_26)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %50 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_25) #22
  %e.0 = extractvalue { i64, ptr } %50, 0
  %e.1 = extractvalue { i64, ptr } %50, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_25)
  call void @llvm.lifetime.start.p0(i64 1, ptr %20)
  %51 = load volatile i8, ptr %holder_key, align 1
  store i8 %51, ptr %20, align 1
  %_33 = load i8, ptr %20, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %20)
  %52 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %e.0, ptr %52, align 8
  %53 = getelementptr inbounds i8, ptr %52, i64 8
  store ptr %e.1, ptr %53, align 8
  store i8 1, ptr %_0, align 8
  br label %bb81

bb13:                                             ; preds = %bb7
  br label %bb22

bb81:                                             ; preds = %bb16, %bb9
  br label %bb82

bb22:                                             ; preds = %bb20, %bb13
  %54 = load i8, ptr %new, align 1, !range !4, !noundef !3
  %55 = trunc i8 %54 to i1
  %_238 = zext i1 %55 to i64
  switch i64 %_238, label %bb54 [
    i64 1, label %bb93
    i64 0, label %bb92
  ]

bb21:                                             ; preds = %bb6
  call void @llvm.lifetime.end.p0(i64 noundef 7, ptr noundef %target_head) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %t)
  %_70 = load i8, ptr %new, align 1, !noundef !3
  %_69 = and i8 %_70, 1
  %_68 = icmp eq i8 %_69, 0
  %_67 = call noundef zeroext i1 @llvm.expect.with.probability.i1(i1 noundef zeroext %_68, i1 noundef zeroext true, double noundef 7.500000e-01) #22
  br i1 %_67, label %bb28, label %bb32

bb15:                                             ; preds = %bb6
  %56 = getelementptr inbounds i8, ptr %st, i64 44
  %57 = load i8, ptr %56, align 4, !range !4, !noundef !3
  %_38 = trunc i8 %57 to i1
  br i1 %_38, label %bb20, label %bb16

bb32:                                             ; preds = %bb21
  %_86 = getelementptr inbounds i8, ptr %new, i64 1
; call core::ptr::read_unaligned
  call void @_ZN4core3ptr14read_unaligned17hfb0286d8a885119bE(ptr noalias nocapture noundef sret([32 x i8]) align 1 dereferenceable(32) %t, ptr noundef %_86) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_90)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_243)
; call core::array::<impl core::default::Default for [T; 32]>::default
  call void @"_ZN4core5array76_$LT$impl$u20$core..default..Default$u20$for$u20$$u5b$T$u3b$$u20$32$u5d$$GT$7default17hf39cfabd391f7201E"(ptr noalias nocapture noundef sret([32 x i8]) align 1 dereferenceable(32) %_243) #22
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_90, ptr align 1 %_243, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_243)
  call void @llvm.lifetime.start.p0(i64 1, ptr %19)
  %58 = call i32 @memcmp(ptr %t, ptr %_90, i64 32)
  %59 = icmp eq i32 %58, 0
  %60 = zext i1 %59 to i8
  store i8 %60, ptr %19, align 1
  %61 = load i8, ptr %19, align 1, !range !4, !noundef !3
  %_89 = trunc i8 %61 to i1
  call void @llvm.lifetime.end.p0(i64 1, ptr %19)
  br i1 %_89, label %bb34, label %bb39

bb28:                                             ; preds = %bb21
  call void @llvm.lifetime.start.p0(i64 1, ptr %5)
  %62 = load volatile i8, ptr %holder_key, align 1
  store i8 %62, ptr %5, align 1
  %_73 = load i8, ptr %5, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %5)
  call void @llvm.lifetime.start.p0(i64 160, ptr %_77)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_78)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_78, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_1ba5e1e397ae92b788c97e688ac0b362) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_79 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 89) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_80)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_80, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_1ba5e1e397ae92b788c97e688ac0b362) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_81)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_82)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_83)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_83, align 8
  %63 = getelementptr inbounds i8, ptr %_83, i64 8
  store i64 103, ptr %63, align 8
  %64 = getelementptr inbounds i8, ptr %_83, i64 16
  store i32 234, ptr %64, align 8
  %65 = getelementptr inbounds i8, ptr %_82, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %65, ptr align 8 %_83, i64 24, i1 false)
  store i64 0, ptr %_82, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_83)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_81, ptr align 8 %_82, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_82)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_84)
  store i8 2, ptr %_84, align 8
  %66 = getelementptr inbounds i8, ptr %_77, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %66, ptr align 8 %_78, i64 24, i1 false)
  %67 = getelementptr inbounds i8, ptr %_77, i64 152
  store i32 %_79, ptr %67, align 8
  %68 = getelementptr inbounds i8, ptr %_77, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %68, ptr align 8 %_80, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_77, ptr align 8 %_81, i64 32, i1 false)
  %69 = getelementptr inbounds i8, ptr %_77, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %69, ptr align 8 %_84, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_84)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_81)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_80)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_78)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %70 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_77) #22
  %_76.0 = extractvalue { i64, ptr } %70, 0
  %_76.1 = extractvalue { i64, ptr } %70, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_77)
  %71 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_76.0, ptr %71, align 8
  %72 = getelementptr inbounds i8, ptr %71, i64 8
  store ptr %_76.1, ptr %72, align 8
  store i8 1, ptr %_0, align 8
  br label %bb80

bb39:                                             ; preds = %bb32
  call void @llvm.lifetime.end.p0(i64 32, ptr %_90)
  call void @llvm.lifetime.start.p0(i64 1, ptr %18)
  %73 = call i32 @memcmp(ptr %t, ptr %sharing, i64 32)
  %74 = icmp eq i32 %73, 0
  %75 = zext i1 %74 to i8
  store i8 %75, ptr %18, align 1
  %76 = load i8, ptr %18, align 1, !range !4, !noundef !3
  %_120 = trunc i8 %76 to i1
  call void @llvm.lifetime.end.p0(i64 1, ptr %18)
  %_119 = zext i1 %_120 to i8
  %_118 = call noundef zeroext i8 @llvm.bpf.passthrough.i8.i8(i32 noundef zeroext 4, i8 noundef zeroext %_119) #22
  %_117 = and i8 %_118, 1
  %_116 = icmp ne i8 %_117, 0
  %_115 = call noundef zeroext i1 @llvm.expect.with.probability.i1(i1 noundef zeroext %_116, i1 noundef zeroext true, double noundef 6.250000e-01) #22
  br i1 %_115, label %bb44, label %bb42

bb34:                                             ; preds = %bb32
  call void @llvm.lifetime.end.p0(i64 32, ptr %_90)
  call void @llvm.lifetime.start.p0(i64 160, ptr %_93)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_94)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_94, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_0e3505805f4905816c1bd644811a7869) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_95 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 30) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_96)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_96, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_0e3505805f4905816c1bd644811a7869) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_97)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_98)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_99)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_99, align 8
  %77 = getelementptr inbounds i8, ptr %_99, i64 8
  store i64 103, ptr %77, align 8
  %78 = getelementptr inbounds i8, ptr %_99, i64 16
  store i32 235, ptr %78, align 8
  %79 = getelementptr inbounds i8, ptr %_98, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %79, ptr align 8 %_99, i64 24, i1 false)
  store i64 0, ptr %_98, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_99)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_97, ptr align 8 %_98, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_98)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_100)
  store i8 2, ptr %_100, align 8
  %80 = getelementptr inbounds i8, ptr %_93, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %80, ptr align 8 %_94, i64 24, i1 false)
  %81 = getelementptr inbounds i8, ptr %_93, i64 152
  store i32 %_95, ptr %81, align 8
  %82 = getelementptr inbounds i8, ptr %_93, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %82, ptr align 8 %_96, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_93, ptr align 8 %_97, i64 32, i1 false)
  %83 = getelementptr inbounds i8, ptr %_93, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %83, ptr align 8 %_100, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_100)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_97)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_96)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_94)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %84 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_93) #22
  %_92.0 = extractvalue { i64, ptr } %84, 0
  %_92.1 = extractvalue { i64, ptr } %84, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_93)
  call void @llvm.lifetime.start.p0(i64 64, ptr %_101)
  call void @llvm.lifetime.start.p0(i64 32, ptr %k)
  %_104 = getelementptr inbounds i8, ptr %t, i64 8
  %_107 = getelementptr inbounds i8, ptr %k, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_107, ptr align 1 %_104, i64 24, i1 false)
  %_110 = getelementptr inbounds i8, ptr %new, i64 1
; call core::ptr::read_unaligned
  %_108 = call noundef i64 @_ZN4core3ptr14read_unaligned17h516ffa4b8b8a8286E(ptr noundef %_110) #22
  call void @llvm.lifetime.start.p0(i64 8, ptr %_247)
  store i64 %_108, ptr %_247, align 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %k, ptr align 1 %_247, i64 8, i1 false)
  call void @llvm.lifetime.end.p0(i64 8, ptr %_247)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_113)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_113, ptr align 1 %k, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_265, ptr align 1 %_113, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_113)
  call void @llvm.lifetime.end.p0(i64 32, ptr %k)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_114)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_250)
; call core::array::<impl core::default::Default for [T; 32]>::default
  call void @"_ZN4core5array76_$LT$impl$u20$core..default..Default$u20$for$u20$$u5b$T$u3b$$u20$32$u5d$$GT$7default17hf39cfabd391f7201E"(ptr noalias nocapture noundef sret([32 x i8]) align 1 dereferenceable(32) %_250) #22
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_114, ptr align 1 %_250, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_250)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_101, ptr align 1 %_265, i64 32, i1 false)
  %85 = getelementptr inbounds i8, ptr %_101, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %85, ptr align 1 %_114, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_114)
; call anchor_lang::error::Error::with_pubkeys
  %86 = call { i64, ptr } @_ZN11anchor_lang5error5Error12with_pubkeys17hca6dbbbe6a9a5da7E(i64 noundef %_92.0, ptr noundef %_92.1, ptr noalias nocapture noundef readonly align 1 dereferenceable(64) %_101) #22
  %_91.0 = extractvalue { i64, ptr } %86, 0
  %_91.1 = extractvalue { i64, ptr } %86, 1
  call void @llvm.lifetime.end.p0(i64 64, ptr %_101)
  %87 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_91.0, ptr %87, align 8
  %88 = getelementptr inbounds i8, ptr %87, i64 8
  store ptr %_91.1, ptr %88, align 8
  store i8 1, ptr %_0, align 8
  br label %bb80

bb42:                                             ; preds = %bb39
  call void @llvm.lifetime.start.p0(i64 1, ptr %17)
  %89 = call i32 @memcmp(ptr %t, ptr %holder_key, i64 32)
  %90 = icmp eq i32 %89, 0
  %91 = zext i1 %90 to i8
  store i8 %91, ptr %17, align 1
  %92 = load i8, ptr %17, align 1, !range !4, !noundef !3
  %_122 = trunc i8 %92 to i1
  call void @llvm.lifetime.end.p0(i64 1, ptr %17)
  %_121 = call noundef zeroext i1 @llvm.expect.i1(i1 noundef zeroext %_122, i1 noundef zeroext false) #22
  br i1 %_121, label %bb44, label %bb48

bb44:                                             ; preds = %bb42, %bb39
  call void @llvm.lifetime.start.p0(i64 1, ptr %16)
  %93 = load volatile i8, ptr %holder_key, align 1
  store i8 %93, ptr %16, align 1
  %_123 = load i8, ptr %16, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %16)
  call void @llvm.lifetime.start.p0(i64 1, ptr %15)
  %94 = load volatile i8, ptr %holder_key, align 1
  store i8 %94, ptr %15, align 1
  %_126 = load i8, ptr %15, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %15)
  call void @llvm.lifetime.start.p0(i64 1, ptr %14)
  %95 = load volatile i8, ptr %holder_key, align 1
  store i8 %95, ptr %14, align 1
  %_129 = load i8, ptr %14, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %14)
  call void @llvm.lifetime.start.p0(i64 1, ptr %13)
  %96 = load volatile i8, ptr %holder_key, align 1
  store i8 %96, ptr %13, align 1
  %_132 = load i8, ptr %13, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %13)
  call void @llvm.lifetime.start.p0(i64 1, ptr %12)
  %97 = load volatile i8, ptr %holder_key, align 1
  store i8 %97, ptr %12, align 1
  %_135 = load i8, ptr %12, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %12)
  call void @llvm.lifetime.start.p0(i64 1, ptr %11)
  %98 = load volatile i8, ptr %holder_key, align 1
  store i8 %98, ptr %11, align 1
  %_138 = load i8, ptr %11, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %11)
  call void @llvm.lifetime.start.p0(i64 1, ptr %10)
  %99 = load volatile i8, ptr %holder_key, align 1
  store i8 %99, ptr %10, align 1
  %_141 = load i8, ptr %10, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %10)
  call void @llvm.lifetime.start.p0(i64 1, ptr %9)
  %100 = load volatile i8, ptr %holder_key, align 1
  store i8 %100, ptr %9, align 1
  %_144 = load i8, ptr %9, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %9)
  call void @llvm.lifetime.start.p0(i64 1, ptr %8)
  %101 = load volatile i8, ptr %holder_key, align 1
  store i8 %101, ptr %8, align 1
  %_147 = load i8, ptr %8, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %8)
  call void @llvm.lifetime.start.p0(i64 1, ptr %7)
  %102 = load volatile i8, ptr %holder_key, align 1
  store i8 %102, ptr %7, align 1
  %_150 = load i8, ptr %7, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %7)
  call void @llvm.lifetime.start.p0(i64 1, ptr %6)
  %103 = load volatile i8, ptr %holder_key, align 1
  store i8 %103, ptr %6, align 1
  %_153 = load i8, ptr %6, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %6)
  call void @llvm.lifetime.start.p0(i64 160, ptr %_157)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_158)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_158, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_861c8964bbad6d9cede9df277e628fe9) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_159 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 19) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_160)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_160, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_861c8964bbad6d9cede9df277e628fe9) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_161)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_162)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_163)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_163, align 8
  %104 = getelementptr inbounds i8, ptr %_163, i64 8
  store i64 103, ptr %104, align 8
  %105 = getelementptr inbounds i8, ptr %_163, i64 16
  store i32 240, ptr %105, align 8
  %106 = getelementptr inbounds i8, ptr %_162, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %106, ptr align 8 %_163, i64 24, i1 false)
  store i64 0, ptr %_162, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_163)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_161, ptr align 8 %_162, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_162)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_164)
  store i8 2, ptr %_164, align 8
  %107 = getelementptr inbounds i8, ptr %_157, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %107, ptr align 8 %_158, i64 24, i1 false)
  %108 = getelementptr inbounds i8, ptr %_157, i64 152
  store i32 %_159, ptr %108, align 8
  %109 = getelementptr inbounds i8, ptr %_157, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %109, ptr align 8 %_160, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_157, ptr align 8 %_161, i64 32, i1 false)
  %110 = getelementptr inbounds i8, ptr %_157, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %110, ptr align 8 %_164, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_164)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_161)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_160)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_158)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %111 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_157) #22
  %_156.0 = extractvalue { i64, ptr } %111, 0
  %_156.1 = extractvalue { i64, ptr } %111, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_157)
  %112 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_156.0, ptr %112, align 8
  %113 = getelementptr inbounds i8, ptr %112, i64 8
  store ptr %_156.1, ptr %113, align 8
  store i8 1, ptr %_0, align 8
  br label %bb80

bb48:                                             ; preds = %bb42
  call void @llvm.lifetime.start.p0(i64 noundef 7, ptr noundef %target_head) #22
  call void @llvm.lifetime.start.p0(i64 noundef 25, ptr noundef %target_tail) #22
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target_head, ptr align 1 %t, i64 7, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr %b1)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_264, ptr align 1 %t, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %b1, ptr align 1 %_264, i64 32, i1 false)
  %_173 = getelementptr inbounds i8, ptr %b1, i64 7
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target_tail, ptr align 1 %_173, i64 25, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %b1)
  call void @llvm.lifetime.end.p0(i64 32, ptr %t)
  br label %bb51

bb51:                                             ; preds = %bb92, %bb48
  call void @llvm.lifetime.start.p0(i64 1, ptr %cashback)
  %114 = load i8, ptr %holder, align 1, !range !4, !noundef !3
  %_179 = trunc i8 %114 to i1
  br i1 %_179, label %bb52, label %bb53

bb80:                                             ; preds = %bb28, %bb34, %bb44
  call void @llvm.lifetime.end.p0(i64 32, ptr %t)
  br label %bb82

bb82:                                             ; preds = %bb93, %bb81, %bb80
  br label %bb83

bb16:                                             ; preds = %bb15
  call void @llvm.lifetime.start.p0(i64 160, ptr %_40)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_41)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_41, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_f94f166953c814e4161e699857179a1e) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_42 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 84) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_43)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_43, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_f94f166953c814e4161e699857179a1e) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_44)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_45)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_46)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_46, align 8
  %115 = getelementptr inbounds i8, ptr %_46, i64 8
  store i64 103, ptr %115, align 8
  %116 = getelementptr inbounds i8, ptr %_46, i64 16
  store i32 224, ptr %116, align 8
  %117 = getelementptr inbounds i8, ptr %_45, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %117, ptr align 8 %_46, i64 24, i1 false)
  store i64 0, ptr %_45, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_46)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_44, ptr align 8 %_45, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_45)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_47)
  store i8 2, ptr %_47, align 8
  %118 = getelementptr inbounds i8, ptr %_40, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %118, ptr align 8 %_41, i64 24, i1 false)
  %119 = getelementptr inbounds i8, ptr %_40, i64 152
  store i32 %_42, ptr %119, align 8
  %120 = getelementptr inbounds i8, ptr %_40, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %120, ptr align 8 %_43, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_40, ptr align 8 %_44, i64 32, i1 false)
  %121 = getelementptr inbounds i8, ptr %_40, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %121, ptr align 8 %_47, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_47)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_44)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_43)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_41)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %122 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_40) #22
  %_39.0 = extractvalue { i64, ptr } %122, 0
  %_39.1 = extractvalue { i64, ptr } %122, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_40)
  %123 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_39.0, ptr %123, align 8
  %124 = getelementptr inbounds i8, ptr %123, i64 8
  store ptr %_39.1, ptr %124, align 8
  store i8 1, ptr %_0, align 8
  br label %bb81

bb20:                                             ; preds = %bb15
  br label %bb22

bb93:                                             ; preds = %bb22
  call void @llvm.lifetime.start.p0(i64 160, ptr %_49)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_50)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_50, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_b5f839a6bda937f2cae73e49fc88071f) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_51 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 90) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_52)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_52, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_b5f839a6bda937f2cae73e49fc88071f) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_53)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_54)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_55)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_55, align 8
  %125 = getelementptr inbounds i8, ptr %_55, i64 8
  store i64 103, ptr %125, align 8
  %126 = getelementptr inbounds i8, ptr %_55, i64 16
  store i32 226, ptr %126, align 8
  %127 = getelementptr inbounds i8, ptr %_54, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %127, ptr align 8 %_55, i64 24, i1 false)
  store i64 0, ptr %_54, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_55)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_53, ptr align 8 %_54, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_54)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_56)
  store i8 2, ptr %_56, align 8
  %128 = getelementptr inbounds i8, ptr %_49, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %128, ptr align 8 %_50, i64 24, i1 false)
  %129 = getelementptr inbounds i8, ptr %_49, i64 152
  store i32 %_51, ptr %129, align 8
  %130 = getelementptr inbounds i8, ptr %_49, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %130, ptr align 8 %_52, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_49, ptr align 8 %_53, i64 32, i1 false)
  %131 = getelementptr inbounds i8, ptr %_49, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %131, ptr align 8 %_56, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_56)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_53)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_52)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_50)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %132 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_49) #22
  %_48.0 = extractvalue { i64, ptr } %132, 0
  %_48.1 = extractvalue { i64, ptr } %132, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_49)
  %133 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_48.0, ptr %133, align 8
  %134 = getelementptr inbounds i8, ptr %133, i64 8
  store ptr %_48.1, ptr %134, align 8
  store i8 1, ptr %_0, align 8
  br label %bb82

bb92:                                             ; preds = %bb22
  call void @llvm.lifetime.start.p0(i64 32, ptr %b)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_263, ptr align 1 %holder_key, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %b, ptr align 1 %_263, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target_head, ptr align 1 %b, i64 7, i1 false)
  %_62 = getelementptr inbounds i8, ptr %b, i64 7
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target_tail, ptr align 1 %_62, i64 25, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %b)
  br label %bb51

bb83:                                             ; preds = %bb79, %bb82
  call void @llvm.lifetime.end.p0(i64 25, ptr %target_tail)
  call void @llvm.lifetime.end.p0(i64 7, ptr %target_head)
  call void @llvm.lifetime.end.p0(i64 1, ptr %holder)
  br label %bb84

bb53:                                             ; preds = %bb51
  %135 = getelementptr inbounds i8, ptr %st, i64 42
  %136 = load i8, ptr %135, align 2, !range !4, !noundef !3
  %137 = trunc i8 %136 to i1
  %138 = zext i1 %137 to i8
  store i8 %138, ptr %cashback, align 1
  %139 = load i64, ptr %fee, align 8, !range !2, !noundef !3
  store i64 %139, ptr %_180, align 8
  %140 = load i64, ptr %_180, align 8, !noundef !3
  switch i64 %140, label %bb54 [
    i64 0, label %bb78
    i64 1, label %bb55
  ]

bb52:                                             ; preds = %bb51
  store i8 0, ptr %cashback, align 1
  %141 = load i64, ptr %fee, align 8, !range !2, !noundef !3
  store i64 %141, ptr %_180, align 8
  %142 = load i64, ptr %_180, align 8, !noundef !3
  switch i64 %142, label %bb54 [
    i64 0, label %bb78
    i64 1, label %bb122
  ]

bb78:                                             ; preds = %bb73, %bb52, %bb53
  call void @llvm.lifetime.start.p0(i64 32, ptr %_229)
  call void @llvm.lifetime.start.p0(i64 32, ptr %b2)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %b2, ptr align 1 %target_head, i64 7, i1 false)
  %_234 = getelementptr inbounds i8, ptr %b2, i64 7
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_234, ptr align 1 %target_tail, i64 25, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_235)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_235, ptr align 1 %b2, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_266, ptr align 1 %_235, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_235)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_229, ptr align 1 %_266, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %b2)
  %143 = getelementptr inbounds i8, ptr %_0, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %143, ptr align 1 %_229, i64 32, i1 false)
  store i8 0, ptr %_0, align 8
  call void @llvm.lifetime.end.p0(i64 32, ptr %_229)
  call void @llvm.lifetime.end.p0(i64 1, ptr %cashback)
  call void @llvm.lifetime.end.p0(i64 25, ptr %target_tail)
  call void @llvm.lifetime.end.p0(i64 7, ptr %target_head)
  call void @llvm.lifetime.end.p0(i64 1, ptr %holder)
  br label %bb84

bb55:                                             ; preds = %bb53
  %144 = getelementptr inbounds i8, ptr %fee, i64 8
  %145 = load i64, ptr %144, align 8, !noundef !3
  store i64 %145, ptr %f, align 8
  call void @llvm.lifetime.start.p0(i64 1, ptr %_182)
  %146 = getelementptr inbounds i8, ptr %st, i64 43
  %147 = load i8, ptr %146, align 1, !range !4, !noundef !3
  %148 = trunc i8 %147 to i1
  %149 = zext i1 %148 to i8
  store i8 %149, ptr %_182, align 1
  %150 = load i8, ptr %_182, align 1, !range !4, !noundef !3
  %151 = trunc i8 %150 to i1
  br i1 %151, label %bb56, label %bb60

bb60:                                             ; preds = %bb55
  call void @llvm.lifetime.end.p0(i64 1, ptr %_182)
  %152 = load i8, ptr %cashback, align 1, !range !4, !noundef !3
  %_192 = trunc i8 %152 to i1
  br i1 %_192, label %bb61, label %bb62

bb56:                                             ; preds = %bb122, %bb55
  call void @llvm.lifetime.start.p0(i64 160, ptr %_184)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_185)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_185, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_e75cefee4bb91125af0ea8444b842ed0) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_186 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 91) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_187)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_187, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_e75cefee4bb91125af0ea8444b842ed0) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_188)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_189)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_190)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_190, align 8
  %153 = getelementptr inbounds i8, ptr %_190, i64 8
  store i64 103, ptr %153, align 8
  %154 = getelementptr inbounds i8, ptr %_190, i64 16
  store i32 254, ptr %154, align 8
  %155 = getelementptr inbounds i8, ptr %_189, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %155, ptr align 8 %_190, i64 24, i1 false)
  store i64 0, ptr %_189, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_190)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_188, ptr align 8 %_189, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_189)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_191)
  store i8 2, ptr %_191, align 8
  %156 = getelementptr inbounds i8, ptr %_184, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %156, ptr align 8 %_185, i64 24, i1 false)
  %157 = getelementptr inbounds i8, ptr %_184, i64 152
  store i32 %_186, ptr %157, align 8
  %158 = getelementptr inbounds i8, ptr %_184, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %158, ptr align 8 %_187, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_184, ptr align 8 %_188, i64 32, i1 false)
  %159 = getelementptr inbounds i8, ptr %_184, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %159, ptr align 8 %_191, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_191)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_188)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_187)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_185)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %160 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_184) #22
  %_183.0 = extractvalue { i64, ptr } %160, 0
  %_183.1 = extractvalue { i64, ptr } %160, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_184)
  %161 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_183.0, ptr %161, align 8
  %162 = getelementptr inbounds i8, ptr %161, i64 8
  store ptr %_183.1, ptr %162, align 8
  store i8 1, ptr %_0, align 8
  call void @llvm.lifetime.end.p0(i64 1, ptr %_182)
  br label %bb79

bb62:                                             ; preds = %bb123, %bb60
  call void @llvm.lifetime.start.p0(i64 1, ptr %4)
  %163 = load volatile i8, ptr %holder_key, align 1
  store i8 %163, ptr %4, align 1
  %_202 = load i8, ptr %4, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %4)
  %164 = getelementptr inbounds i8, ptr %st, i64 45
  %165 = load i8, ptr %164, align 1, !range !4, !noundef !3
  %_205 = trunc i8 %165 to i1
  br i1 %_205, label %bb70, label %bb66

bb61:                                             ; preds = %bb60
  call void @llvm.lifetime.start.p0(i64 160, ptr %_194)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_195)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_195, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_835bb996f1795bf0338da0490417da62) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_196 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 80) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_197)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_197, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_835bb996f1795bf0338da0490417da62) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_198)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_199)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_200)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_200, align 8
  %166 = getelementptr inbounds i8, ptr %_200, i64 8
  store i64 103, ptr %166, align 8
  %167 = getelementptr inbounds i8, ptr %_200, i64 16
  store i32 258, ptr %167, align 8
  %168 = getelementptr inbounds i8, ptr %_199, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %168, ptr align 8 %_200, i64 24, i1 false)
  store i64 0, ptr %_199, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_200)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_198, ptr align 8 %_199, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_199)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_201)
  store i8 2, ptr %_201, align 8
  %169 = getelementptr inbounds i8, ptr %_194, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %169, ptr align 8 %_195, i64 24, i1 false)
  %170 = getelementptr inbounds i8, ptr %_194, i64 152
  store i32 %_196, ptr %170, align 8
  %171 = getelementptr inbounds i8, ptr %_194, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %171, ptr align 8 %_197, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_194, ptr align 8 %_198, i64 32, i1 false)
  %172 = getelementptr inbounds i8, ptr %_194, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %172, ptr align 8 %_201, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_201)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_198)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_197)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_195)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %173 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_194) #22
  %_193.0 = extractvalue { i64, ptr } %173, 0
  %_193.1 = extractvalue { i64, ptr } %173, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_194)
  %174 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_193.0, ptr %174, align 8
  %175 = getelementptr inbounds i8, ptr %174, i64 8
  store ptr %_193.1, ptr %175, align 8
  store i8 1, ptr %_0, align 8
  br label %bb79

bb79:                                             ; preds = %bb56, %bb74, %bb66, %bb61
  call void @llvm.lifetime.end.p0(i64 1, ptr %cashback)
  br label %bb83

bb122:                                            ; preds = %bb52
  %176 = getelementptr inbounds i8, ptr %fee, i64 8
  %177 = load i64, ptr %176, align 8, !noundef !3
  store i64 %177, ptr %f, align 8
  call void @llvm.lifetime.start.p0(i64 1, ptr %_182)
  %178 = getelementptr inbounds i8, ptr %st, i64 43
  %179 = load i8, ptr %178, align 1, !range !4, !noundef !3
  %180 = trunc i8 %179 to i1
  %181 = zext i1 %180 to i8
  store i8 %181, ptr %_182, align 1
  %182 = load i8, ptr %_182, align 1, !range !4, !noundef !3
  %183 = trunc i8 %182 to i1
  br i1 %183, label %bb56, label %bb123

bb123:                                            ; preds = %bb122
  call void @llvm.lifetime.end.p0(i64 1, ptr %_182)
  br label %bb62

bb66:                                             ; preds = %bb62
  call void @llvm.lifetime.start.p0(i64 160, ptr %_207)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_208)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_208, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_01eaaa187d2be542d4425f23ab284310) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_209 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 77) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_210)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_210, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_01eaaa187d2be542d4425f23ab284310) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_211)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_212)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_213)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_213, align 8
  %184 = getelementptr inbounds i8, ptr %_213, i64 8
  store i64 103, ptr %184, align 8
  %185 = getelementptr inbounds i8, ptr %_213, i64 16
  store i32 262, ptr %185, align 8
  %186 = getelementptr inbounds i8, ptr %_212, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %186, ptr align 8 %_213, i64 24, i1 false)
  store i64 0, ptr %_212, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_213)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_211, ptr align 8 %_212, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_212)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_214)
  store i8 2, ptr %_214, align 8
  %187 = getelementptr inbounds i8, ptr %_207, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %187, ptr align 8 %_208, i64 24, i1 false)
  %188 = getelementptr inbounds i8, ptr %_207, i64 152
  store i32 %_209, ptr %188, align 8
  %189 = getelementptr inbounds i8, ptr %_207, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %189, ptr align 8 %_210, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_207, ptr align 8 %_211, i64 32, i1 false)
  %190 = getelementptr inbounds i8, ptr %_207, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %190, ptr align 8 %_214, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_214)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_211)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_210)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_208)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %191 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_207) #22
  %_206.0 = extractvalue { i64, ptr } %191, 0
  %_206.1 = extractvalue { i64, ptr } %191, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_207)
  %192 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_206.0, ptr %192, align 8
  %193 = getelementptr inbounds i8, ptr %192, i64 8
  store ptr %_206.1, ptr %193, align 8
  store i8 1, ptr %_0, align 8
  br label %bb79

bb70:                                             ; preds = %bb62
  %194 = load i64, ptr %f, align 8, !noundef !3
  %195 = icmp eq i64 %194, 0
  br i1 %195, label %bb74, label %bb71

bb74:                                             ; preds = %bb72, %bb70
  call void @llvm.lifetime.start.p0(i64 160, ptr %_218)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_219)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_219, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_973adb9e8664e25d4750ddb14e0de56a) #22
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_220 = call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 78) #22
  call void @llvm.lifetime.start.p0(i64 24, ptr %_221)
; call <T as alloc::string::ToString>::to_string
  call void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef sret([24 x i8]) align 8 dereferenceable(24) %_221, ptr noalias noundef readonly align 4 dereferenceable(4) @alloc_973adb9e8664e25d4750ddb14e0de56a) #22
  call void @llvm.lifetime.start.p0(i64 32, ptr %_222)
  call void @llvm.lifetime.start.p0(i64 32, ptr %_223)
  call void @llvm.lifetime.start.p0(i64 24, ptr %_224)
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_224, align 8
  %196 = getelementptr inbounds i8, ptr %_224, i64 8
  store i64 103, ptr %196, align 8
  %197 = getelementptr inbounds i8, ptr %_224, i64 16
  store i32 266, ptr %197, align 8
  %198 = getelementptr inbounds i8, ptr %_223, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %198, ptr align 8 %_224, i64 24, i1 false)
  store i64 0, ptr %_223, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr %_224)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_222, ptr align 8 %_223, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_223)
  call void @llvm.lifetime.start.p0(i64 72, ptr %_225)
  store i8 2, ptr %_225, align 8
  %199 = getelementptr inbounds i8, ptr %_218, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %199, ptr align 8 %_219, i64 24, i1 false)
  %200 = getelementptr inbounds i8, ptr %_218, i64 152
  store i32 %_220, ptr %200, align 8
  %201 = getelementptr inbounds i8, ptr %_218, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %201, ptr align 8 %_221, i64 24, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %_218, ptr align 8 %_222, i64 32, i1 false)
  %202 = getelementptr inbounds i8, ptr %_218, i64 80
  call void @llvm.memcpy.p0.p0.i64(ptr align 8 %202, ptr align 8 %_225, i64 72, i1 false)
  call void @llvm.lifetime.end.p0(i64 72, ptr %_225)
  call void @llvm.lifetime.end.p0(i64 32, ptr %_222)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_221)
  call void @llvm.lifetime.end.p0(i64 24, ptr %_219)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %203 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %_218) #22
  %_217.0 = extractvalue { i64, ptr } %203, 0
  %_217.1 = extractvalue { i64, ptr } %203, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr %_218)
  %204 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_217.0, ptr %204, align 8
  %205 = getelementptr inbounds i8, ptr %204, i64 8
  store ptr %_217.1, ptr %205, align 8
  store i8 1, ptr %_0, align 8
  br label %bb79

bb71:                                             ; preds = %bb70
  %206 = getelementptr inbounds i8, ptr %st, i64 32
  %_216 = load i64, ptr %206, align 8, !noundef !3
  %207 = load i64, ptr %f, align 8, !noundef !3
  %_215 = icmp ugt i64 %207, %_216
  br i1 %_215, label %bb72, label %bb73

bb73:                                             ; preds = %bb71
  call void @llvm.lifetime.start.p0(i64 1, ptr %3)
  %208 = load volatile i8, ptr %holder_key, align 1
  store i8 %208, ptr %3, align 1
  %_226 = load i8, ptr %3, align 1, !noundef !3
  call void @llvm.lifetime.end.p0(i64 1, ptr %3)
  br label %bb78

bb72:                                             ; preds = %bb71
  br label %bb74

bb84:                                             ; preds = %bb1, %bb83, %bb78
  ret void
}

; core::slice::index::slice_end_index_len_fail
; Function Attrs: cold noinline noreturn nounwind
declare void @_ZN4core5slice5index24slice_end_index_len_fail17h3f8438963677f5b8E(i64 noundef, i64 noundef, ptr noalias noundef readonly align 8 dereferenceable(24)) unnamed_addr #5

; core::slice::index::slice_index_order_fail
; Function Attrs: cold noinline noreturn nounwind
declare void @_ZN4core5slice5index22slice_index_order_fail17hcc61bcee7ef2204dE(i64 noundef, i64 noundef, ptr noalias noundef readonly align 8 dereferenceable(24)) unnamed_addr #5

; Function Attrs: nocallback nofree nounwind willreturn memory(argmem: readwrite)
declare void @llvm.memcpy.p0.p0.i64(ptr noalias nocapture writeonly, ptr noalias nocapture readonly, i64, i1 immarg) #6

; <pump_recovered::PumpError as core::fmt::Display>::fmt
; Function Attrs: nounwind
declare noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef readonly align 4 dereferenceable(4), ptr noalias noundef align 8 dereferenceable(64)) unnamed_addr #1

; core::result::unwrap_failed
; Function Attrs: cold noinline noreturn nounwind
declare void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1, i64 noundef, ptr noundef nonnull align 1, ptr noalias noundef readonly align 8 dereferenceable(24), ptr noalias noundef readonly align 8 dereferenceable(24)) unnamed_addr #5

; core::panicking::panic_nounwind
; Function Attrs: cold noinline noreturn nounwind
declare void @_ZN4core9panicking14panic_nounwind17h59c09f9524fc568aE(ptr noalias noundef nonnull readonly align 1, i64 noundef) unnamed_addr #5

; Function Attrs: convergent nocallback nofree nosync nounwind willreturn memory(none)
declare hidden i1 @llvm.is.constant.i1(i1) #7

; core::panicking::panic
; Function Attrs: cold noinline noreturn nounwind
declare void @_ZN4core9panicking5panic17h0d41b9de9b340d2cE(ptr noalias noundef nonnull readonly align 1, i64 noundef, ptr noalias noundef readonly align 8 dereferenceable(24)) unnamed_addr #5

; core::fmt::num::imp::<impl core::fmt::Display for usize>::fmt
; Function Attrs: nounwind
declare noundef zeroext i1 @"_ZN4core3fmt3num3imp54_$LT$impl$u20$core..fmt..Display$u20$for$u20$usize$GT$3fmt17h1fc8323720f2b108E"(ptr noalias noundef readonly align 8 dereferenceable(8), ptr noalias noundef align 8 dereferenceable(64)) unnamed_addr #1

; core::fmt::num::<impl core::fmt::UpperHex for u32>::fmt
; Function Attrs: nounwind
declare noundef zeroext i1 @"_ZN4core3fmt3num53_$LT$impl$u20$core..fmt..UpperHex$u20$for$u20$u32$GT$3fmt17hf4c59f29dbc8ac3eE"(ptr noalias noundef readonly align 4 dereferenceable(4), ptr noalias noundef align 8 dereferenceable(64)) unnamed_addr #1

; core::panicking::panic_fmt
; Function Attrs: cold noinline noreturn nounwind
declare void @_ZN4core9panicking9panic_fmt17h0f7a5cdbeae7e874E(ptr noalias nocapture noundef readonly align 8 dereferenceable(48), ptr noalias noundef readonly align 8 dereferenceable(24)) unnamed_addr #5

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(inaccessiblemem: write)
declare hidden void @llvm.assume(i1 noundef) #8

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(none)
declare hidden i1 @llvm.expect.i1(i1, i1) #9

; core::panicking::panic_const::panic_const_div_by_zero
; Function Attrs: cold noinline noreturn nounwind
declare void @_ZN4core9panicking11panic_const23panic_const_div_by_zero17hd6b7f0f5931b4251E(ptr noalias noundef readonly align 8 dereferenceable(24)) unnamed_addr #5

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare hidden i64 @llvm.ctpop.i64(i64) #10

; core::fmt::Formatter::write_str
; Function Attrs: nounwind
declare noundef zeroext i1 @_ZN4core3fmt9Formatter9write_str17h97ca3d8b34e3baaaE(ptr noalias noundef align 8 dereferenceable(64), ptr noalias noundef nonnull readonly align 1, i64 noundef) unnamed_addr #1

; Function Attrs: cold noreturn nounwind memory(inaccessiblemem: write)
declare hidden void @llvm.trap() #11

; Function Attrs: nounwind allockind("alloc,uninitialized,aligned") allocsize(0)
declare noalias noundef ptr @__rust_alloc(i64 noundef, i64 allocalign noundef) unnamed_addr #12

; Function Attrs: nounwind allockind("alloc,zeroed,aligned") allocsize(0)
declare noalias noundef ptr @__rust_alloc_zeroed(i64 noundef, i64 allocalign noundef) unnamed_addr #13

; Function Attrs: nounwind allockind("realloc,aligned") allocsize(3)
declare noalias noundef ptr @__rust_realloc(ptr allocptr noundef, i64 noundef, i64 allocalign noundef, i64 noundef) unnamed_addr #14

; Function Attrs: nocallback nofree nounwind willreturn memory(argmem: write)
declare void @llvm.memset.p0.i64(ptr nocapture writeonly, i8, i64, i1 immarg) #15

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare hidden { i64, i1 } @llvm.uadd.with.overflow.i64(i64, i64) #10

; alloc::raw_vec::handle_error
; Function Attrs: cold noreturn nounwind
declare void @_ZN5alloc7raw_vec12handle_error17h22fdf317f3a37641E(i64 noundef, i64) unnamed_addr #16

; Function Attrs: nounwind allockind("free")
declare void @__rust_dealloc(ptr allocptr noundef, i64 noundef, i64 noundef) unnamed_addr #17

; core::fmt::write
; Function Attrs: nounwind
declare noundef zeroext i1 @_ZN4core3fmt5write17h7d5c5d972f6bf082E(ptr noundef nonnull align 1, ptr noalias noundef readonly align 8 dereferenceable(24), ptr noalias nocapture noundef readonly align 8 dereferenceable(48)) unnamed_addr #1

; pump_recovered::PumpError::name
; Function Attrs: nounwind
declare void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr dead_on_unwind noalias nocapture noundef writable sret([24 x i8]) align 8 dereferenceable(24), ptr noalias noundef readonly align 4 dereferenceable(4)) unnamed_addr #1

; pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
; Function Attrs: nounwind
declare noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef) unnamed_addr #1

; <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
; Function Attrs: nounwind
declare { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(160)) unnamed_addr #1

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(none)
declare i1 @llvm.expect.with.probability.i1(i1, i1, double immarg) unnamed_addr #9

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(argmem: readwrite)
declare void @llvm.lifetime.end.p0(i64 immarg, ptr nocapture) unnamed_addr #18

declare hidden i32 @memcmp(ptr, ptr, i64)

; Function Attrs: nounwind memory(none)
declare i8 @llvm.bpf.passthrough.i8.i8(i32, i8) unnamed_addr #19

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(argmem: readwrite)
declare void @llvm.lifetime.start.p0(i64 immarg, ptr nocapture) unnamed_addr #18

; anchor_lang::error::Error::with_pubkeys
; Function Attrs: nounwind
declare { i64, ptr } @_ZN11anchor_lang5error5Error12with_pubkeys17hca6dbbbe6a9a5da7E(i64 noundef, ptr noundef, ptr noalias nocapture noundef readonly align 1 dereferenceable(64)) unnamed_addr #1

; core::panicking::panic_const::panic_const_sub_overflow
; Function Attrs: cold noinline noreturn nounwind
declare void @_ZN4core9panicking11panic_const24panic_const_sub_overflow17hce3a200f706adb1cE(ptr noalias noundef readonly align 8 dereferenceable(24)) unnamed_addr #5

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(inaccessiblemem: readwrite)
declare void @llvm.var.annotation.p0.p0(ptr, ptr, ptr, i32, ptr) unnamed_addr #20

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(inaccessiblemem: readwrite)
declare i1 @llvm.annotation.i1.p0(i1, ptr, ptr, i32) unnamed_addr #20

; Function Attrs: nounwind memory(none)
declare i64 @llvm.bpf.passthrough.i64.i64(i32, i64) unnamed_addr #19

attributes #0 = { inlinehint nounwind "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #1 = { nounwind "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #2 = { alwaysinline nounwind "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #3 = { noinline nounwind "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #4 = { cold nounwind "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #5 = { cold noinline noreturn nounwind "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #6 = { nocallback nofree nounwind willreturn memory(argmem: readwrite) }
attributes #7 = { convergent nocallback nofree nosync nounwind willreturn memory(none) }
attributes #8 = { nocallback nofree nosync nounwind willreturn memory(inaccessiblemem: write) }
attributes #9 = { nocallback nofree nosync nounwind willreturn memory(none) }
attributes #10 = { nocallback nofree nosync nounwind speculatable willreturn memory(none) }
attributes #11 = { cold noreturn nounwind memory(inaccessiblemem: write) }
attributes #12 = { nounwind allockind("alloc,uninitialized,aligned") allocsize(0) "alloc-family"="__rust_alloc" "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #13 = { nounwind allockind("alloc,zeroed,aligned") allocsize(0) "alloc-family"="__rust_alloc" "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #14 = { nounwind allockind("realloc,aligned") allocsize(3) "alloc-family"="__rust_alloc" "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #15 = { nocallback nofree nounwind willreturn memory(argmem: write) }
attributes #16 = { cold noreturn nounwind "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #17 = { nounwind allockind("free") "alloc-family"="__rust_alloc" "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #18 = { nocallback nofree nosync nounwind willreturn memory(argmem: readwrite) }
attributes #19 = { nounwind memory(none) }
attributes #20 = { nocallback nofree nosync nounwind willreturn memory(inaccessiblemem: readwrite) }
attributes #21 = { noreturn nounwind }
attributes #22 = { nounwind }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 8, !"PIC Level", i32 2}
!1 = !{!"rustc version 1.79.0-dev"}
!2 = !{i64 0, i64 2}
!3 = !{}
!4 = !{i8 0, i8 2}
!5 = !{i64 8}
!6 = !{i64 1}
!7 = !{i8 -1, i8 2}
!8 = !{i64 1, i64 -9223372036854775807}
!9 = !{i64 0, i64 -9223372036854775807}
!10 = !{i64 0, i64 -9223372036854775808}
!11 = !{i64 0, i64 -9223372036854775806}
!12 = !{i8 0, i8 3}
