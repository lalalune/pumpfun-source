; ModuleID = 'pass114_late_probe.c42a7eae2abfd033-cgu.0'
source_filename = "pass114_late_probe.c42a7eae2abfd033-cgu.0"
target datalayout = "e-m:e-p:64:64-i64:64-n32:64-S128"
target triple = "sbf"

@vtable.0 = private unnamed_addr constant <{ ptr, [16 x i8], ptr, ptr, ptr }> <{ ptr @"_ZN4core3ptr42drop_in_place$LT$alloc..string..String$GT$17hd1d278fe2cba7629E", [16 x i8] c"\18\00\00\00\00\00\00\00\08\00\00\00\00\00\00\00", ptr @"_ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$9write_str17h4b62f46a222bd5b2E", ptr @"_ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$10write_char17hfde5b685689164ccE", ptr @_ZN4core3fmt5Write9write_fmt17hf607f0d92912dfd2E }>, align 8
@alloc_cc656815297f75969399c3f4b1ad3de4 = private unnamed_addr constant <{ [55 x i8] }> <{ [55 x i8] c"a Display implementation returned an error unexpectedly" }>, align 1
@vtable.1 = private unnamed_addr constant <{ ptr, [16 x i8], ptr }> <{ ptr @"_ZN4core3ptr37drop_in_place$LT$core..fmt..Error$GT$17hc55e87063dbb1cfcE", [16 x i8] c"\00\00\00\00\00\00\00\00\01\00\00\00\00\00\00\00", ptr @"_ZN53_$LT$core..fmt..Error$u20$as$u20$core..fmt..Debug$GT$3fmt17h85666afa16c4890eE" }>, align 8
@alloc_0c7342d701a2219de6bddb6c078f5127 = private unnamed_addr constant <{ [84 x i8] }> <{ [84 x i8] c"/home/runner/work/platform-tools/platform-tools/out/rust/library/alloc/src/string.rs" }>, align 1
@alloc_d5d9fccaf545b6e0545ef73245a3c43f = private unnamed_addr constant <{ ptr, [16 x i8] }> <{ ptr @alloc_0c7342d701a2219de6bddb6c078f5127, [16 x i8] c"T\00\00\00\00\00\00\00\FF\09\00\00\0E\00\00\00" }>, align 8
@alloc_99ac8a81a24cac863217ce4a5cbfabea = private unnamed_addr constant <{ [5 x i8] }> <{ [5 x i8] c"Error" }>, align 1
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
@alloc_914b2c69d7eca30497b9feaf15ac92f1 = private unnamed_addr constant <{ [1 x i8] }> zeroinitializer, align 1

; <T as alloc::string::ToString>::to_string
; Function Attrs: inlinehint nounwind
define internal fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr dead_on_unwind noalias nocapture noundef writable writeonly align 8 dereferenceable(24) %_0, ptr noalias noundef readonly align 4 dereferenceable(4) %self) unnamed_addr #0 {
start:
  %_11 = alloca [0 x i8], align 1
  %formatter = alloca [64 x i8], align 8
  %buf = alloca [24 x i8], align 8
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf)
  store i64 0, ptr %buf, align 8
  %_9.sroa.4.0.buf.sroa_idx = getelementptr inbounds i8, ptr %buf, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx, align 8
  %_9.sroa.5.0.buf.sroa_idx = getelementptr inbounds i8, ptr %buf, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx, align 8
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter)
  %0 = getelementptr inbounds i8, ptr %formatter, i64 52
  store i32 0, ptr %0, align 4
  %1 = getelementptr inbounds i8, ptr %formatter, i64 48
  store i32 32, ptr %1, align 8
  %2 = getelementptr inbounds i8, ptr %formatter, i64 56
  store i8 3, ptr %2, align 8
  store i64 0, ptr %formatter, align 8
  %3 = getelementptr inbounds i8, ptr %formatter, i64 16
  store i64 0, ptr %3, align 8
  %4 = getelementptr inbounds i8, ptr %formatter, i64 32
  store ptr %buf, ptr %4, align 8
  %5 = getelementptr inbounds i8, ptr %formatter, i64 40
  store ptr @vtable.0, ptr %5, align 8
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %6 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) %self, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter) #26
  br i1 %6, label %bb3, label %bb4

bb4:                                              ; preds = %start
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %_0, ptr noundef nonnull align 8 dereferenceable(24) %buf, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter)
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf)
  ret void

bb3:                                              ; preds = %start
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27
  unreachable
}

; core::fmt::Write::write_fmt
; Function Attrs: nounwind
define internal noundef zeroext i1 @_ZN4core3fmt5Write9write_fmt17hf607f0d92912dfd2E(ptr noalias noundef align 8 dereferenceable(24) %self, ptr noalias nocapture noundef readonly align 8 dereferenceable(48) %args) unnamed_addr #1 {
start:
; call core::fmt::write
  %0 = tail call noundef zeroext i1 @_ZN4core3fmt5write17h7d5c5d972f6bf082E(ptr noundef nonnull align 1 %self, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.0, ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(48) %args) #26
  ret i1 %0
}

; core::ptr::drop_in_place<core::fmt::Error>
; Function Attrs: inlinehint mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define internal void @"_ZN4core3ptr37drop_in_place$LT$core..fmt..Error$GT$17hc55e87063dbb1cfcE"(ptr noalias nocapture nonnull readnone align 1 %_1) unnamed_addr #2 {
start:
  ret void
}

; core::ptr::drop_in_place<alloc::string::String>
; Function Attrs: nounwind
define internal void @"_ZN4core3ptr42drop_in_place$LT$alloc..string..String$GT$17hd1d278fe2cba7629E"(ptr noalias nocapture noundef readonly align 8 dereferenceable(24) %_1) unnamed_addr #1 {
start:
  %_1.val = load i64, ptr %_1, align 8, !noundef !2
  %0 = icmp eq i64 %_1.val, 0
  br i1 %0, label %"_ZN4core3ptr46drop_in_place$LT$alloc..vec..Vec$LT$u8$GT$$GT$17hb09713401b9fe8c0E.exit", label %"_ZN63_$LT$alloc..alloc..Global$u20$as$u20$core..alloc..Allocator$GT$10deallocate17h6b30618160528bb2E.exit.i.i.i"

"_ZN63_$LT$alloc..alloc..Global$u20$as$u20$core..alloc..Allocator$GT$10deallocate17h6b30618160528bb2E.exit.i.i.i": ; preds = %start
  %1 = getelementptr inbounds i8, ptr %_1, i64 8
  %_1.val1 = load ptr, ptr %1, align 8, !nonnull !2, !noundef !2
  tail call void @__rust_dealloc(ptr noundef nonnull %_1.val1, i64 noundef %_1.val, i64 noundef 1) #26
  br label %"_ZN4core3ptr46drop_in_place$LT$alloc..vec..Vec$LT$u8$GT$$GT$17hb09713401b9fe8c0E.exit"

"_ZN4core3ptr46drop_in_place$LT$alloc..vec..Vec$LT$u8$GT$$GT$17hb09713401b9fe8c0E.exit": ; preds = %start, %"_ZN63_$LT$alloc..alloc..Global$u20$as$u20$core..alloc..Allocator$GT$10deallocate17h6b30618160528bb2E.exit.i.i.i"
  ret void
}

; <core::fmt::Error as core::fmt::Debug>::fmt
; Function Attrs: inlinehint nounwind
define internal noundef zeroext i1 @"_ZN53_$LT$core..fmt..Error$u20$as$u20$core..fmt..Debug$GT$3fmt17h85666afa16c4890eE"(ptr noalias nocapture nonnull readonly align 1 %self, ptr noalias noundef align 8 dereferenceable(64) %f) unnamed_addr #0 {
start:
; call core::fmt::Formatter::write_str
  %_0 = tail call noundef zeroext i1 @_ZN4core3fmt9Formatter9write_str17h97ca3d8b34e3baaaE(ptr noalias noundef nonnull align 8 dereferenceable(64) %f, ptr noalias noundef nonnull readonly align 1 @alloc_99ac8a81a24cac863217ce4a5cbfabea, i64 noundef 5) #26
  ret i1 %_0
}

; <alloc::string::String as core::fmt::Write>::write_char
; Function Attrs: inlinehint nounwind
define internal noundef zeroext i1 @"_ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$10write_char17hfde5b685689164ccE"(ptr noalias nocapture noundef align 8 dereferenceable(24) %self, i32 noundef %c) unnamed_addr #0 {
start:
  %_10.sroa.0.i = alloca i32, align 4
  tail call void @llvm.experimental.noalias.scope.decl(metadata !3)
  %_12.i = icmp ult i32 %c, 128
  br i1 %_12.i, label %bb4.i, label %bb12.i.i

bb12.i.i:                                         ; preds = %start
  call void @llvm.lifetime.start.p0(i64 4, ptr nonnull %_10.sroa.0.i)
  store i32 0, ptr %_10.sroa.0.i, align 4, !noalias !3
  %_73.i.i = icmp ult i32 %c, 2048
  br i1 %_73.i.i, label %bb7.i.i, label %bb14.i.i

bb14.i.i:                                         ; preds = %bb12.i.i
  %_74.i.i = icmp ult i32 %c, 65536
  br i1 %_74.i.i, label %bb8.i.i, label %bb9.i.i

bb7.i.i:                                          ; preds = %bb12.i.i
  %_20.i.i = lshr i32 %c, 6
  %0 = trunc i32 %_20.i.i to i8
  %1 = or disjoint i8 %0, -64
  store i8 %1, ptr %_10.sroa.0.i, align 4, !alias.scope !6, !noalias !3
  %2 = trunc i32 %c to i8
  %_22.i.i = and i8 %2, 63
  %3 = or disjoint i8 %_22.i.i, -128
  %_10.sroa.0.i.1.sroa_idx11 = getelementptr inbounds i8, ptr %_10.sroa.0.i, i64 1
  store i8 %3, ptr %_10.sroa.0.i.1.sroa_idx11, align 1, !alias.scope !6, !noalias !3
  br label %_ZN4core4char7methods15encode_utf8_raw17h84badf475ef2bb54E.exit.i

bb8.i.i:                                          ; preds = %bb14.i.i
  %_30.i.i = lshr i32 %c, 12
  %4 = trunc i32 %_30.i.i to i8
  %5 = or disjoint i8 %4, -32
  store i8 %5, ptr %_10.sroa.0.i, align 4, !alias.scope !6, !noalias !3
  %_34.i.i = lshr i32 %c, 6
  %6 = trunc i32 %_34.i.i to i8
  %_32.i.i = and i8 %6, 63
  %7 = or disjoint i8 %_32.i.i, -128
  %_10.sroa.0.i.1.sroa_idx = getelementptr inbounds i8, ptr %_10.sroa.0.i, i64 1
  store i8 %7, ptr %_10.sroa.0.i.1.sroa_idx, align 1, !alias.scope !6, !noalias !3
  %8 = trunc i32 %c to i8
  %_36.i.i = and i8 %8, 63
  %9 = or disjoint i8 %_36.i.i, -128
  %_10.sroa.0.i.2.sroa_idx12 = getelementptr inbounds i8, ptr %_10.sroa.0.i, i64 2
  store i8 %9, ptr %_10.sroa.0.i.2.sroa_idx12, align 2, !alias.scope !6, !noalias !3
  br label %_ZN4core4char7methods15encode_utf8_raw17h84badf475ef2bb54E.exit.i

bb9.i.i:                                          ; preds = %bb14.i.i
  %_45.i.i = lshr i32 %c, 18
  %10 = trunc i32 %_45.i.i to i8
  %_43.i.i = and i8 %10, 7
  %11 = or disjoint i8 %_43.i.i, -16
  store i8 %11, ptr %_10.sroa.0.i, align 4, !alias.scope !6, !noalias !3
  %_49.i.i = lshr i32 %c, 12
  %12 = trunc i32 %_49.i.i to i8
  %_47.i.i = and i8 %12, 63
  %13 = or disjoint i8 %_47.i.i, -128
  %_10.sroa.0.i.1.sroa_idx10 = getelementptr inbounds i8, ptr %_10.sroa.0.i, i64 1
  store i8 %13, ptr %_10.sroa.0.i.1.sroa_idx10, align 1, !alias.scope !6, !noalias !3
  %_53.i.i = lshr i32 %c, 6
  %14 = trunc i32 %_53.i.i to i8
  %_51.i.i = and i8 %14, 63
  %15 = or disjoint i8 %_51.i.i, -128
  %_10.sroa.0.i.2.sroa_idx = getelementptr inbounds i8, ptr %_10.sroa.0.i, i64 2
  store i8 %15, ptr %_10.sroa.0.i.2.sroa_idx, align 2, !alias.scope !6, !noalias !3
  %16 = trunc i32 %c to i8
  %_55.i.i = and i8 %16, 63
  %17 = or disjoint i8 %_55.i.i, -128
  %_10.sroa.0.i.3.sroa_idx = getelementptr inbounds i8, ptr %_10.sroa.0.i, i64 3
  store i8 %17, ptr %_10.sroa.0.i.3.sroa_idx, align 1, !alias.scope !6, !noalias !3
  br label %_ZN4core4char7methods15encode_utf8_raw17h84badf475ef2bb54E.exit.i

_ZN4core4char7methods15encode_utf8_raw17h84badf475ef2bb54E.exit.i: ; preds = %bb9.i.i, %bb8.i.i, %bb7.i.i
  %_510.i.i = phi i64 [ 4, %bb9.i.i ], [ 3, %bb8.i.i ], [ 2, %bb7.i.i ]
  tail call void @llvm.experimental.noalias.scope.decl(metadata !9)
  tail call void @llvm.experimental.noalias.scope.decl(metadata !12)
  tail call void @llvm.experimental.noalias.scope.decl(metadata !15)
  %18 = getelementptr inbounds i8, ptr %self, i64 16
  %len.i.i.i.i.i = load i64, ptr %18, align 8, !alias.scope !18, !noalias !19, !noundef !2
  %19 = load i64, ptr %self, align 8, !alias.scope !21, !noalias !19, !noundef !2
  %_7.i.i.i.i.i = sub i64 %19, %len.i.i.i.i.i
  %_5.i.i.i.i.i = icmp ult i64 %_7.i.i.i.i.i, %_510.i.i
  br i1 %_5.i.i.i.i.i, label %bb1.i.i.i.i.i, label %"_ZN5alloc3vec16Vec$LT$T$C$A$GT$17extend_from_slice17h9db90023fcfc2b1eE.exit.i"

bb1.i.i.i.i.i:                                    ; preds = %_ZN4core4char7methods15encode_utf8_raw17h84badf475ef2bb54E.exit.i
; call alloc::raw_vec::RawVec<T,A>::reserve::do_reserve_and_handle
  tail call fastcc void @"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$7reserve21do_reserve_and_handle17h841f8186853dc167E"(ptr noalias noundef nonnull align 8 dereferenceable(16) %self, i64 noundef %len.i.i.i.i.i, i64 noundef %_510.i.i) #26, !noalias !19
  %len.pre.i.i.i.i = load i64, ptr %18, align 8, !alias.scope !18, !noalias !19
  br label %"_ZN5alloc3vec16Vec$LT$T$C$A$GT$17extend_from_slice17h9db90023fcfc2b1eE.exit.i"

"_ZN5alloc3vec16Vec$LT$T$C$A$GT$17extend_from_slice17h9db90023fcfc2b1eE.exit.i": ; preds = %bb1.i.i.i.i.i, %_ZN4core4char7methods15encode_utf8_raw17h84badf475ef2bb54E.exit.i
  %len.i.i.i.i = phi i64 [ %len.i.i.i.i.i, %_ZN4core4char7methods15encode_utf8_raw17h84badf475ef2bb54E.exit.i ], [ %len.pre.i.i.i.i, %bb1.i.i.i.i.i ]
  %20 = getelementptr inbounds i8, ptr %self, i64 8
  %self1.i1.i.i.i = load ptr, ptr %20, align 8, !alias.scope !18, !noalias !19, !nonnull !2, !noundef !2
  %dst.i.i.i.i = getelementptr inbounds i8, ptr %self1.i1.i.i.i, i64 %len.i.i.i.i
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(1) %dst.i.i.i.i, ptr noundef nonnull align 4 dereferenceable(1) %_10.sroa.0.i, i64 %_510.i.i, i1 false), !noalias !18
  %21 = add i64 %len.i.i.i.i, %_510.i.i
  store i64 %21, ptr %18, align 8, !alias.scope !18, !noalias !19
  call void @llvm.lifetime.end.p0(i64 4, ptr nonnull %_10.sroa.0.i)
  br label %_ZN5alloc6string6String4push17h96dfc48c19bd6e38E.exit

bb4.i:                                            ; preds = %start
  %_4.i = trunc i32 %c to i8
  tail call void @llvm.experimental.noalias.scope.decl(metadata !24)
  %22 = getelementptr inbounds i8, ptr %self, i64 16
  %len.i.i = load i64, ptr %22, align 8, !alias.scope !27, !noundef !2
  %23 = load i64, ptr %self, align 8, !alias.scope !27, !noundef !2
  %_4.i.i = icmp eq i64 %len.i.i, %23
  br i1 %_4.i.i, label %bb1.i.i, label %"_ZN5alloc3vec16Vec$LT$T$C$A$GT$4push17h3eecfd24bc944e21E.exit.i"

bb1.i.i:                                          ; preds = %bb4.i
; call alloc::raw_vec::RawVec<T,A>::grow_one
  tail call fastcc void @"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$8grow_one17h4b15183664487c30E"(ptr noalias noundef nonnull align 8 dereferenceable(16) %self) #26
  br label %"_ZN5alloc3vec16Vec$LT$T$C$A$GT$4push17h3eecfd24bc944e21E.exit.i"

"_ZN5alloc3vec16Vec$LT$T$C$A$GT$4push17h3eecfd24bc944e21E.exit.i": ; preds = %bb1.i.i, %bb4.i
  %24 = getelementptr inbounds i8, ptr %self, i64 8
  %self1.i.i = load ptr, ptr %24, align 8, !alias.scope !27, !nonnull !2, !noundef !2
  %end.i.i = getelementptr inbounds i8, ptr %self1.i.i, i64 %len.i.i
  store i8 %_4.i, ptr %end.i.i, align 1, !noalias !27
  %25 = add i64 %len.i.i, 1
  store i64 %25, ptr %22, align 8, !alias.scope !27
  br label %_ZN5alloc6string6String4push17h96dfc48c19bd6e38E.exit

_ZN5alloc6string6String4push17h96dfc48c19bd6e38E.exit: ; preds = %"_ZN5alloc3vec16Vec$LT$T$C$A$GT$17extend_from_slice17h9db90023fcfc2b1eE.exit.i", %"_ZN5alloc3vec16Vec$LT$T$C$A$GT$4push17h3eecfd24bc944e21E.exit.i"
  ret i1 false
}

; <alloc::string::String as core::fmt::Write>::write_str
; Function Attrs: inlinehint nounwind
define internal noundef zeroext i1 @"_ZN58_$LT$alloc..string..String$u20$as$u20$core..fmt..Write$GT$9write_str17h4b62f46a222bd5b2E"(ptr noalias nocapture noundef align 8 dereferenceable(24) %self, ptr noalias nocapture noundef nonnull readonly align 1 %s.0, i64 noundef %s.1) unnamed_addr #0 {
start:
  tail call void @llvm.experimental.noalias.scope.decl(metadata !28)
  tail call void @llvm.experimental.noalias.scope.decl(metadata !31)
  tail call void @llvm.experimental.noalias.scope.decl(metadata !34)
  %0 = getelementptr inbounds i8, ptr %self, i64 16
  %len.i.i.i.i = load i64, ptr %0, align 8, !alias.scope !37, !noalias !38, !noundef !2
  %1 = load i64, ptr %self, align 8, !alias.scope !40, !noalias !38, !noundef !2
  %_7.i.i.i.i = sub i64 %1, %len.i.i.i.i
  %_5.i.i.i.i = icmp ult i64 %_7.i.i.i.i, %s.1
  br i1 %_5.i.i.i.i, label %bb1.i.i.i.i, label %"_ZN5alloc3vec16Vec$LT$T$C$A$GT$17extend_from_slice17h9db90023fcfc2b1eE.exit"

bb1.i.i.i.i:                                      ; preds = %start
; call alloc::raw_vec::RawVec<T,A>::reserve::do_reserve_and_handle
  tail call fastcc void @"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$7reserve21do_reserve_and_handle17h841f8186853dc167E"(ptr noalias noundef nonnull align 8 dereferenceable(16) %self, i64 noundef %len.i.i.i.i, i64 noundef %s.1) #26, !noalias !38
  %len.pre.i.i.i = load i64, ptr %0, align 8, !alias.scope !37, !noalias !38
  br label %"_ZN5alloc3vec16Vec$LT$T$C$A$GT$17extend_from_slice17h9db90023fcfc2b1eE.exit"

"_ZN5alloc3vec16Vec$LT$T$C$A$GT$17extend_from_slice17h9db90023fcfc2b1eE.exit": ; preds = %start, %bb1.i.i.i.i
  %len.i.i.i = phi i64 [ %len.i.i.i.i, %start ], [ %len.pre.i.i.i, %bb1.i.i.i.i ]
  %2 = getelementptr inbounds i8, ptr %self, i64 8
  %self1.i1.i.i = load ptr, ptr %2, align 8, !alias.scope !37, !noalias !38, !nonnull !2, !noundef !2
  %dst.i.i.i = getelementptr inbounds i8, ptr %self1.i1.i.i, i64 %len.i.i.i
  tail call void @llvm.memcpy.p0.p0.i64(ptr nonnull align 1 %dst.i.i.i, ptr nonnull align 1 %s.0, i64 %s.1, i1 false), !noalias !37
  %3 = add i64 %len.i.i.i, %s.1
  store i64 %3, ptr %0, align 8, !alias.scope !37, !noalias !38
  ret i1 false
}

; alloc::raw_vec::finish_grow
; Function Attrs: noinline nounwind
define internal fastcc void @_ZN5alloc7raw_vec11finish_grow17h87f821cc75349c87E(ptr dead_on_unwind noalias nocapture noundef writable writeonly align 8 dereferenceable(24) %_0, i64 noundef %0, i64 %1, ptr noalias nocapture noundef readonly align 8 dereferenceable(24) %current_memory) unnamed_addr #3 {
start:
  %2 = icmp eq i64 %0, 0
  br i1 %2, label %bb8, label %bb9

bb9:                                              ; preds = %start
  %3 = getelementptr inbounds i8, ptr %current_memory, i64 8
  %4 = load i64, ptr %3, align 8, !range !43, !noundef !2
  %5 = icmp eq i64 %4, 0
  br i1 %5, label %bb2, label %bb3

bb8:                                              ; preds = %start
  %6 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 0, ptr %6, align 8
  br label %bb7

bb3:                                              ; preds = %bb9
  %ptr = load ptr, ptr %current_memory, align 8, !nonnull !2, !noundef !2
  %7 = getelementptr inbounds i8, ptr %current_memory, i64 16
  %8 = load i64, ptr %7, align 8, !noundef !2
  %cond = icmp eq i64 %4, %0
  tail call void @llvm.assume(i1 %cond)
  %9 = icmp eq i64 %8, 0
  br i1 %9, label %bb1.i.i, label %bb4.i.i

bb1.i.i:                                          ; preds = %bb3
  %10 = icmp eq i64 %1, 0
  br i1 %10, label %bb6, label %bb5.i.i.i

bb5.i.i.i:                                        ; preds = %bb1.i.i
  %11 = tail call noundef ptr @__rust_alloc(i64 noundef %1, i64 noundef %0) #26
  %12 = icmp eq ptr %11, null
  br i1 %12, label %bb6.thread, label %bb14

bb4.i.i:                                          ; preds = %bb3
  %cond.i.i = icmp ule i64 %8, %1
  tail call void @llvm.assume(i1 %cond.i.i)
  %raw_ptr.i.i = tail call noundef ptr @__rust_realloc(ptr noundef nonnull %ptr, i64 noundef %8, i64 noundef %0, i64 noundef %1) #26
  %13 = icmp eq ptr %raw_ptr.i.i, null
  br i1 %13, label %bb6.thread, label %bb14

bb2:                                              ; preds = %bb9
  %14 = icmp eq i64 %1, 0
  br i1 %14, label %bb6, label %bb5.i.i25

bb5.i.i25:                                        ; preds = %bb2
  %15 = tail call noundef ptr @__rust_alloc(i64 noundef %1, i64 noundef %0) #26
  %16 = icmp eq ptr %15, null
  br i1 %16, label %bb6.thread, label %bb14

bb6.thread:                                       ; preds = %bb4.i.i, %bb5.i.i.i, %bb5.i.i25
  %17 = getelementptr inbounds i8, ptr %_0, i64 8
  %18 = getelementptr inbounds i8, ptr %_0, i64 16
  store i64 %0, ptr %17, align 8
  store i64 %1, ptr %18, align 8
  br label %bb7

bb6:                                              ; preds = %bb2, %bb1.i.i
  %ptr.i.i.i = getelementptr i8, ptr null, i64 %0
  br label %bb14

bb14:                                             ; preds = %bb5.i.i25, %bb4.i.i, %bb5.i.i.i, %bb6
  %_0.sroa.4.0.i.i.pn10 = phi i64 [ 0, %bb6 ], [ %1, %bb5.i.i.i ], [ %1, %bb4.i.i ], [ %1, %bb5.i.i25 ]
  %_0.sroa.0.0.i.i.pn9 = phi ptr [ %ptr.i.i.i, %bb6 ], [ %11, %bb5.i.i.i ], [ %raw_ptr.i.i, %bb4.i.i ], [ %15, %bb5.i.i25 ]
  %19 = getelementptr inbounds i8, ptr %_0, i64 8
  %20 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_0.sroa.0.0.i.i.pn9, ptr %19, align 8
  store i64 %_0.sroa.4.0.i.i.pn10, ptr %20, align 8
  br label %bb7

bb7:                                              ; preds = %bb14, %bb6.thread, %bb8
  %storemerge24 = phi i64 [ 1, %bb8 ], [ 0, %bb14 ], [ 1, %bb6.thread ]
  store i64 %storemerge24, ptr %_0, align 8
  ret void
}

; alloc::raw_vec::RawVec<T,A>::reserve::do_reserve_and_handle
; Function Attrs: cold nounwind
define internal fastcc void @"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$7reserve21do_reserve_and_handle17h841f8186853dc167E"(ptr noalias nocapture noundef align 8 dereferenceable(16) %slf, i64 noundef %len, i64 noundef %additional) unnamed_addr #4 {
start:
  %_20.i = alloca [24 x i8], align 8
  %self5.i = alloca [24 x i8], align 8
  tail call void @llvm.experimental.noalias.scope.decl(metadata !44)
  %0 = tail call { i64, i1 } @llvm.uadd.with.overflow.i64(i64 %len, i64 %additional)
  %_29.1.i = extractvalue { i64, i1 } %0, 1
  br i1 %_29.1.i, label %bb2, label %bb10.i

bb10.i:                                           ; preds = %start
  %_29.0.i = extractvalue { i64, i1 } %0, 0
  %_12.i = load i64, ptr %slf, align 8, !alias.scope !44, !noundef !2
  %1 = shl i64 %_12.i, 1
  %cap.sroa.0.0.sroa.speculated.i = tail call i64 @llvm.umax.i64(i64 %1, i64 %_29.0.i)
  %cap3.sroa.0.0.sroa.speculated.i = tail call i64 @llvm.umax.i64(i64 %cap.sroa.0.0.sroa.speculated.i, i64 8)
  %_4.i.i = icmp sgt i64 %cap3.sroa.0.0.sroa.speculated.i, -1
  %_0.sroa.0.0.i.i = zext i1 %_4.i.i to i64
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %self5.i), !noalias !44
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_20.i), !noalias !44
  %2 = getelementptr inbounds i8, ptr %slf, i64 8
  %3 = icmp eq i64 %_12.i, 0
  br i1 %3, label %"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14current_memory17hc167f39406d68977E.exit.i", label %bb4.i.i

bb4.i.i:                                          ; preds = %bb10.i
  %self.val22.i = load ptr, ptr %2, align 8, !alias.scope !44, !nonnull !2, !noundef !2
  store ptr %self.val22.i, ptr %_20.i, align 8, !alias.scope !47, !noalias !44
  %_9.sroa.5.0._0.sroa_idx.i.i = getelementptr inbounds i8, ptr %_20.i, i64 16
  store i64 %_12.i, ptr %_9.sroa.5.0._0.sroa_idx.i.i, align 8, !alias.scope !47, !noalias !44
  br label %"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14current_memory17hc167f39406d68977E.exit.i"

"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14current_memory17hc167f39406d68977E.exit.i": ; preds = %bb4.i.i, %bb10.i
  %.sink.i.i = phi i64 [ 1, %bb4.i.i ], [ 0, %bb10.i ]
  %4 = getelementptr inbounds i8, ptr %_20.i, i64 8
  store i64 %.sink.i.i, ptr %4, align 8, !alias.scope !47, !noalias !44
; call alloc::raw_vec::finish_grow
  call fastcc void @_ZN5alloc7raw_vec11finish_grow17h87f821cc75349c87E(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %self5.i, i64 noundef %_0.sroa.0.0.i.i, i64 %cap3.sroa.0.0.sroa.speculated.i, ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(24) %_20.i) #26, !noalias !44
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_20.i), !noalias !44
  %_53.i = load i64, ptr %self5.i, align 8, !range !50, !noalias !44, !noundef !2
  %trunc.not.i = icmp eq i64 %_53.i, 0
  %5 = getelementptr inbounds i8, ptr %self5.i, i64 8
  br i1 %trunc.not.i, label %bb3, label %bb20.i

bb20.i:                                           ; preds = %"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14current_memory17hc167f39406d68977E.exit.i"
  %e.0.i = load i64, ptr %5, align 8, !range !43, !noalias !44, !noundef !2
  %6 = getelementptr inbounds i8, ptr %self5.i, i64 16
  %e.1.i = load i64, ptr %6, align 8, !noalias !44
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %self5.i), !noalias !44
  br label %bb2

bb2:                                              ; preds = %bb20.i, %start
  %_0.sroa.4.0.i.ph = phi i64 [ undef, %start ], [ %e.1.i, %bb20.i ]
  %_0.sroa.0.0.i.ph = phi i64 [ 0, %start ], [ %e.0.i, %bb20.i ]
; call alloc::raw_vec::handle_error
  tail call void @_ZN5alloc7raw_vec12handle_error17h22fdf317f3a37641E(i64 noundef %_0.sroa.0.0.i.ph, i64 %_0.sroa.4.0.i.ph) #27
  unreachable

bb3:                                              ; preds = %"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14current_memory17hc167f39406d68977E.exit.i"
  %v.0.i = load ptr, ptr %5, align 8, !noalias !44, !nonnull !2, !noundef !2
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %self5.i), !noalias !44
  store ptr %v.0.i, ptr %2, align 8, !alias.scope !44
  store i64 %cap3.sroa.0.0.sroa.speculated.i, ptr %slf, align 8, !alias.scope !44
  ret void
}

; alloc::raw_vec::RawVec<T,A>::grow_one
; Function Attrs: noinline nounwind
define internal fastcc void @"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$8grow_one17h4b15183664487c30E"(ptr noalias nocapture noundef align 8 dereferenceable(16) %self) unnamed_addr #3 {
start:
  %_20.i = alloca [24 x i8], align 8
  %self5.i = alloca [24 x i8], align 8
  %_3 = load i64, ptr %self, align 8, !noundef !2
  tail call void @llvm.experimental.noalias.scope.decl(metadata !51)
  %0 = tail call { i64, i1 } @llvm.uadd.with.overflow.i64(i64 %_3, i64 1)
  %_29.1.i = extractvalue { i64, i1 } %0, 1
  br i1 %_29.1.i, label %bb2, label %bb10.i

bb10.i:                                           ; preds = %start
  %_29.0.i = extractvalue { i64, i1 } %0, 0
  %1 = shl i64 %_3, 1
  %cap.sroa.0.0.sroa.speculated.i = tail call i64 @llvm.umax.i64(i64 %1, i64 %_29.0.i)
  %cap3.sroa.0.0.sroa.speculated.i = tail call i64 @llvm.umax.i64(i64 %cap.sroa.0.0.sroa.speculated.i, i64 8)
  %_4.i.i = icmp sgt i64 %cap3.sroa.0.0.sroa.speculated.i, -1
  %_0.sroa.0.0.i.i = zext i1 %_4.i.i to i64
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %self5.i), !noalias !51
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_20.i), !noalias !51
  %2 = getelementptr inbounds i8, ptr %self, i64 8
  %3 = icmp eq i64 %_3, 0
  br i1 %3, label %"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14current_memory17hc167f39406d68977E.exit.i", label %bb4.i.i

bb4.i.i:                                          ; preds = %bb10.i
  %self.val22.i = load ptr, ptr %2, align 8, !alias.scope !51, !nonnull !2, !noundef !2
  store ptr %self.val22.i, ptr %_20.i, align 8, !alias.scope !54, !noalias !51
  %_9.sroa.5.0._0.sroa_idx.i.i = getelementptr inbounds i8, ptr %_20.i, i64 16
  store i64 %_3, ptr %_9.sroa.5.0._0.sroa_idx.i.i, align 8, !alias.scope !54, !noalias !51
  br label %"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14current_memory17hc167f39406d68977E.exit.i"

"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14current_memory17hc167f39406d68977E.exit.i": ; preds = %bb4.i.i, %bb10.i
  %.sink.i.i = phi i64 [ 1, %bb4.i.i ], [ 0, %bb10.i ]
  %4 = getelementptr inbounds i8, ptr %_20.i, i64 8
  store i64 %.sink.i.i, ptr %4, align 8, !alias.scope !54, !noalias !51
; call alloc::raw_vec::finish_grow
  call fastcc void @_ZN5alloc7raw_vec11finish_grow17h87f821cc75349c87E(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %self5.i, i64 noundef %_0.sroa.0.0.i.i, i64 %cap3.sroa.0.0.sroa.speculated.i, ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(24) %_20.i) #26, !noalias !51
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_20.i), !noalias !51
  %_53.i = load i64, ptr %self5.i, align 8, !range !50, !noalias !51, !noundef !2
  %trunc.not.i = icmp eq i64 %_53.i, 0
  %5 = getelementptr inbounds i8, ptr %self5.i, i64 8
  br i1 %trunc.not.i, label %bb3, label %bb20.i

bb20.i:                                           ; preds = %"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14current_memory17hc167f39406d68977E.exit.i"
  %e.0.i = load i64, ptr %5, align 8, !range !43, !noalias !51, !noundef !2
  %6 = getelementptr inbounds i8, ptr %self5.i, i64 16
  %e.1.i = load i64, ptr %6, align 8, !noalias !51
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %self5.i), !noalias !51
  br label %bb2

bb2:                                              ; preds = %bb20.i, %start
  %_0.sroa.4.0.i.ph = phi i64 [ undef, %start ], [ %e.1.i, %bb20.i ]
  %_0.sroa.0.0.i.ph = phi i64 [ 0, %start ], [ %e.0.i, %bb20.i ]
; call alloc::raw_vec::handle_error
  tail call void @_ZN5alloc7raw_vec12handle_error17h22fdf317f3a37641E(i64 noundef %_0.sroa.0.0.i.ph, i64 %_0.sroa.4.0.i.ph) #27
  unreachable

bb3:                                              ; preds = %"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14current_memory17hc167f39406d68977E.exit.i"
  %v.0.i = load ptr, ptr %5, align 8, !noalias !51, !nonnull !2, !noundef !2
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %self5.i), !noalias !51
  store ptr %v.0.i, ptr %2, align 8, !alias.scope !51
  store i64 %cap3.sroa.0.0.sroa.speculated.i, ptr %self, align 8, !alias.scope !51
  ret void
}

; Function Attrs: nounwind
define void @main34_validate(ptr dead_on_unwind noalias nocapture noundef writable writeonly sret([40 x i8]) align 8 dereferenceable(40) %_0, ptr noalias nocapture noundef readonly align 8 dereferenceable(48) %st, i8 noundef %0, i64 noundef %1, i64 %2, ptr noalias nocapture noundef readonly align 1 dereferenceable(33) %new, ptr noalias noundef readonly align 1 dereferenceable(32) %holder_key, ptr noalias nocapture noundef readonly align 1 dereferenceable(32) %sharing) unnamed_addr #1 {
start:
  %_11.i56 = alloca [0 x i8], align 1
  %formatter.i57 = alloca [64 x i8], align 8
  %buf.i58 = alloca [24 x i8], align 8
  %formatter.i50 = alloca [64 x i8], align 8
  %buf.i51 = alloca [24 x i8], align 8
  %formatter.i43 = alloca [64 x i8], align 8
  %buf.i44 = alloca [24 x i8], align 8
  %formatter.i36 = alloca [64 x i8], align 8
  %buf.i37 = alloca [24 x i8], align 8
  %formatter.i29 = alloca [64 x i8], align 8
  %buf.i30 = alloca [24 x i8], align 8
  %formatter.i = alloca [64 x i8], align 8
  %buf.i = alloca [24 x i8], align 8
  %b2 = alloca [32 x i8], align 1
  %_190 = alloca [160 x i8], align 8
  %_179 = alloca [160 x i8], align 8
  %_166 = alloca [160 x i8], align 8
  %_157 = alloca [24 x i8], align 8
  %_156 = alloca [160 x i8], align 8
  %b1 = alloca [32 x i8], align 1
  %_130 = alloca [160 x i8], align 8
  %_94 = alloca [64 x i8], align 1
  %_86 = alloca [160 x i8], align 8
  %_83 = alloca [32 x i8], align 1
  %_71 = alloca [24 x i8], align 8
  %_70 = alloca [160 x i8], align 8
  %t = alloca [32 x i8], align 1
  %_50 = alloca [24 x i8], align 8
  %_49 = alloca [160 x i8], align 8
  %_41 = alloca [24 x i8], align 8
  %_40 = alloca [160 x i8], align 8
  %_27 = alloca [24 x i8], align 8
  %_26 = alloca [160 x i8], align 8
  %target_tail = alloca [25 x i8], align 1
  %target_head = alloca [7 x i8], align 1
  %_12 = alloca [24 x i8], align 8
  %_11 = alloca [160 x i8], align 8
  %3 = and i8 %0, -3
  %_0.sroa.0.0.off0.i.not = icmp eq i8 %3, 0
  %4 = getelementptr inbounds i8, ptr %st, i64 40
  %5 = load i8, ptr %4, align 8, !range !57, !noundef !2
  %_9.not = icmp eq i8 %5, 0
  br i1 %_9.not, label %bb6, label %bb2

bb6:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 7, ptr nonnull %target_head)
  call void @llvm.lifetime.start.p0(i64 25, ptr nonnull %target_tail)
  %6 = getelementptr inbounds i8, ptr %st, i64 41
  %7 = load i8, ptr %6, align 1, !range !57, !noundef !2
  %_22.not = icmp eq i8 %7, 0
  br i1 %_22.not, label %bb7, label %bb8

bb2:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_11)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_12)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_12, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_eb4f91695bc6f999067c65f428fcc4d8) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_13 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 88) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i56)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i), !noalias !58
  store i64 0, ptr %buf.i, align 8, !noalias !58
  %_9.sroa.4.0.buf.sroa_idx.i = getelementptr inbounds i8, ptr %buf.i, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i, align 8, !noalias !58
  %_9.sroa.5.0.buf.sroa_idx.i = getelementptr inbounds i8, ptr %buf.i, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i, align 8, !noalias !58
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i), !noalias !58
  %8 = getelementptr inbounds i8, ptr %formatter.i, i64 52
  store i32 0, ptr %8, align 4, !noalias !58
  %9 = getelementptr inbounds i8, ptr %formatter.i, i64 48
  store i32 32, ptr %9, align 8, !noalias !58
  %10 = getelementptr inbounds i8, ptr %formatter.i, i64 56
  store i8 3, ptr %10, align 8, !noalias !58
  store i64 0, ptr %formatter.i, align 8, !noalias !58
  %11 = getelementptr inbounds i8, ptr %formatter.i, i64 16
  store i64 0, ptr %11, align 8, !noalias !58
  %12 = getelementptr inbounds i8, ptr %formatter.i, i64 32
  store ptr %buf.i, ptr %12, align 8, !noalias !58
  %13 = getelementptr inbounds i8, ptr %formatter.i, i64 40
  store ptr @vtable.0, ptr %13, align 8, !noalias !58
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %14 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_eb4f91695bc6f999067c65f428fcc4d8, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i) #26, !noalias !62
  br i1 %14, label %bb3.i, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit"

bb3.i:                                            ; preds = %bb2
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i56, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !62
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit": ; preds = %bb2
  %15 = getelementptr inbounds i8, ptr %_11, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %15, ptr noundef nonnull align 8 dereferenceable(24) %buf.i, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i), !noalias !58
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i), !noalias !58
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i56)
  %16 = getelementptr inbounds i8, ptr %_11, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %16, ptr noundef nonnull align 8 dereferenceable(24) %_12, i64 24, i1 false)
  %17 = getelementptr inbounds i8, ptr %_11, i64 152
  store i32 %_13, ptr %17, align 8
  store i64 0, ptr %_11, align 8
  %_15.sroa.4.0._11.sroa_idx = getelementptr inbounds i8, ptr %_11, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_15.sroa.4.0._11.sroa_idx, align 8
  %_15.sroa.4.sroa.4.0._15.sroa.4.0._11.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_11, i64 16
  store i64 103, ptr %_15.sroa.4.sroa.4.0._15.sroa.4.0._11.sroa_idx.sroa_idx, align 8
  %_15.sroa.4.sroa.5.0._15.sroa.4.0._11.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_11, i64 24
  store i32 19, ptr %_15.sroa.4.sroa.5.0._15.sroa.4.0._11.sroa_idx.sroa_idx, align 8
  %18 = getelementptr inbounds i8, ptr %_11, i64 80
  store i8 2, ptr %18, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_12)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %19 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_11) #26
  %_10.0 = extractvalue { i64, ptr } %19, 0
  %_10.1 = extractvalue { i64, ptr } %19, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_11)
  %20 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_10.0, ptr %20, align 8
  %21 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_10.1, ptr %21, align 8
  store i8 1, ptr %_0, align 8
  br label %bb85

bb8:                                              ; preds = %bb6
  br i1 %_0.sroa.0.0.off0.i.not, label %bb11, label %bb23

bb7:                                              ; preds = %bb6
  br i1 %_0.sroa.0.0.off0.i.not, label %bb22, label %bb16, !prof !63

bb11:                                             ; preds = %bb8
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_26)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_27)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_27, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_8f95cb73e89711d65e95d13598508b19) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_28 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 83) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i56)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i30), !noalias !64
  store i64 0, ptr %buf.i30, align 8, !noalias !64
  %_9.sroa.4.0.buf.sroa_idx.i31 = getelementptr inbounds i8, ptr %buf.i30, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i31, align 8, !noalias !64
  %_9.sroa.5.0.buf.sroa_idx.i32 = getelementptr inbounds i8, ptr %buf.i30, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i32, align 8, !noalias !64
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i29), !noalias !64
  %22 = getelementptr inbounds i8, ptr %formatter.i29, i64 52
  store i32 0, ptr %22, align 4, !noalias !64
  %23 = getelementptr inbounds i8, ptr %formatter.i29, i64 48
  store i32 32, ptr %23, align 8, !noalias !64
  %24 = getelementptr inbounds i8, ptr %formatter.i29, i64 56
  store i8 3, ptr %24, align 8, !noalias !64
  store i64 0, ptr %formatter.i29, align 8, !noalias !64
  %25 = getelementptr inbounds i8, ptr %formatter.i29, i64 16
  store i64 0, ptr %25, align 8, !noalias !64
  %26 = getelementptr inbounds i8, ptr %formatter.i29, i64 32
  store ptr %buf.i30, ptr %26, align 8, !noalias !64
  %27 = getelementptr inbounds i8, ptr %formatter.i29, i64 40
  store ptr @vtable.0, ptr %27, align 8, !noalias !64
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %28 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_8f95cb73e89711d65e95d13598508b19, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i29) #26, !noalias !68
  br i1 %28, label %bb3.i33, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit34"

bb3.i33:                                          ; preds = %bb11
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i56, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !68
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit34": ; preds = %bb11
  %29 = getelementptr inbounds i8, ptr %_26, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %29, ptr noundef nonnull align 8 dereferenceable(24) %buf.i30, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i29), !noalias !64
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i30), !noalias !64
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i56)
  %30 = getelementptr inbounds i8, ptr %_26, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %30, ptr noundef nonnull align 8 dereferenceable(24) %_27, i64 24, i1 false)
  %31 = getelementptr inbounds i8, ptr %_26, i64 152
  store i32 %_28, ptr %31, align 8
  store i64 0, ptr %_26, align 8
  %_30.sroa.4.0._26.sroa_idx = getelementptr inbounds i8, ptr %_26, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_30.sroa.4.0._26.sroa_idx, align 8
  %_30.sroa.4.sroa.4.0._30.sroa.4.0._26.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_26, i64 16
  store i64 103, ptr %_30.sroa.4.sroa.4.0._30.sroa.4.0._26.sroa_idx.sroa_idx, align 8
  %_30.sroa.4.sroa.5.0._30.sroa.4.0._26.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_26, i64 24
  store i32 24, ptr %_30.sroa.4.sroa.5.0._30.sroa.4.0._26.sroa_idx.sroa_idx, align 8
  %32 = getelementptr inbounds i8, ptr %_26, i64 80
  store i8 2, ptr %32, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_27)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %33 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_26) #26
  %e.0 = extractvalue { i64, ptr } %33, 0
  %e.1 = extractvalue { i64, ptr } %33, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_26)
  %34 = load volatile i8, ptr %holder_key, align 1
  %35 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %e.0, ptr %35, align 8
  %36 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %e.1, ptr %36, align 8
  store i8 1, ptr %_0, align 8
  br label %bb84

bb23:                                             ; preds = %bb16, %bb8
  %37 = load i8, ptr %new, align 1, !range !57, !noundef !2
  %trunc21.not.not = icmp eq i8 %37, 0
  br i1 %trunc21.not.not, label %bb53, label %bb91

bb22:                                             ; preds = %bb7
  call void @llvm.lifetime.end.p0(i64 7, ptr nonnull %target_head)
  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %t)
  %38 = load i8, ptr %new, align 1, !range !57, !noundef !2
  %trunc.not = icmp eq i8 %38, 0
  br i1 %trunc.not, label %bb29, label %bb33, !prof !69

bb16:                                             ; preds = %bb7
  %39 = getelementptr inbounds i8, ptr %st, i64 44
  %40 = load i8, ptr %39, align 4, !range !57, !noundef !2
  %_38.not = icmp eq i8 %40, 0
  br i1 %_38.not, label %bb17, label %bb23

bb33:                                             ; preds = %bb22
  %_79 = getelementptr inbounds i8, ptr %new, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %t, ptr noundef nonnull align 1 dereferenceable(32) %_79, i64 32, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %_83)
  call void @llvm.memset.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %_83, i8 0, i64 32, i1 false)
  %41 = call i32 @memcmp(ptr noundef nonnull dereferenceable(32) %t, ptr noundef nonnull dereferenceable(32) %_83, i64 32)
  %42 = icmp eq i32 %41, 0
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %_83)
  br i1 %42, label %bb35, label %bb40

bb29:                                             ; preds = %bb22
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_70)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_71)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_71, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_1ba5e1e397ae92b788c97e688ac0b362) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_72 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 89) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i56)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i37), !noalias !70
  store i64 0, ptr %buf.i37, align 8, !noalias !70
  %_9.sroa.4.0.buf.sroa_idx.i38 = getelementptr inbounds i8, ptr %buf.i37, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i38, align 8, !noalias !70
  %_9.sroa.5.0.buf.sroa_idx.i39 = getelementptr inbounds i8, ptr %buf.i37, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i39, align 8, !noalias !70
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i36), !noalias !70
  %43 = getelementptr inbounds i8, ptr %formatter.i36, i64 52
  store i32 0, ptr %43, align 4, !noalias !70
  %44 = getelementptr inbounds i8, ptr %formatter.i36, i64 48
  store i32 32, ptr %44, align 8, !noalias !70
  %45 = getelementptr inbounds i8, ptr %formatter.i36, i64 56
  store i8 3, ptr %45, align 8, !noalias !70
  store i64 0, ptr %formatter.i36, align 8, !noalias !70
  %46 = getelementptr inbounds i8, ptr %formatter.i36, i64 16
  store i64 0, ptr %46, align 8, !noalias !70
  %47 = getelementptr inbounds i8, ptr %formatter.i36, i64 32
  store ptr %buf.i37, ptr %47, align 8, !noalias !70
  %48 = getelementptr inbounds i8, ptr %formatter.i36, i64 40
  store ptr @vtable.0, ptr %48, align 8, !noalias !70
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %49 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_1ba5e1e397ae92b788c97e688ac0b362, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i36) #26, !noalias !74
  br i1 %49, label %bb3.i40, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit41"

bb3.i40:                                          ; preds = %bb29
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i56, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !74
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit41": ; preds = %bb29
  %50 = getelementptr inbounds i8, ptr %_70, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %50, ptr noundef nonnull align 8 dereferenceable(24) %buf.i37, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i36), !noalias !70
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i37), !noalias !70
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i56)
  %51 = getelementptr inbounds i8, ptr %_70, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %51, ptr noundef nonnull align 8 dereferenceable(24) %_71, i64 24, i1 false)
  %52 = getelementptr inbounds i8, ptr %_70, i64 152
  store i32 %_72, ptr %52, align 8
  store i64 0, ptr %_70, align 8
  %_74.sroa.4.0._70.sroa_idx = getelementptr inbounds i8, ptr %_70, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_74.sroa.4.0._70.sroa_idx, align 8
  %_74.sroa.4.sroa.4.0._74.sroa.4.0._70.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_70, i64 16
  store i64 103, ptr %_74.sroa.4.sroa.4.0._74.sroa.4.0._70.sroa_idx.sroa_idx, align 8
  %_74.sroa.4.sroa.5.0._74.sroa.4.0._70.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_70, i64 24
  store i32 41, ptr %_74.sroa.4.sroa.5.0._74.sroa.4.0._70.sroa_idx.sroa_idx, align 8
  %53 = getelementptr inbounds i8, ptr %_70, i64 80
  store i8 2, ptr %53, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_71)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %54 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_70) #26
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_70)
  br label %bb81

bb40:                                             ; preds = %bb33
  %55 = call i32 @memcmp(ptr noundef nonnull dereferenceable(32) %t, ptr noundef nonnull dereferenceable(32) %sharing, i64 32)
  %56 = icmp eq i32 %55, 0
  %57 = zext i1 %56 to i8
  %_100 = tail call noundef zeroext i8 @llvm.bpf.passthrough.i8.i8(i32 noundef zeroext 4, i8 noundef zeroext %57) #26
  %_99 = and i8 %_100, 1
  %_98.not = icmp eq i8 %_99, 0
  br i1 %_98.not, label %bb43, label %bb45, !prof !75

bb35:                                             ; preds = %bb33
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_86)
  %58 = getelementptr inbounds i8, ptr %_86, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %58, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_0e3505805f4905816c1bd644811a7869) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_88 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 30) #26
  %59 = getelementptr inbounds i8, ptr %_86, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %59, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_0e3505805f4905816c1bd644811a7869) #26
  %60 = getelementptr inbounds i8, ptr %_86, i64 152
  store i32 %_88, ptr %60, align 8
  store i64 0, ptr %_86, align 8
  %_90.sroa.4.0._86.sroa_idx = getelementptr inbounds i8, ptr %_86, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_90.sroa.4.0._86.sroa_idx, align 8
  %_90.sroa.4.sroa.4.0._90.sroa.4.0._86.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_86, i64 16
  store i64 103, ptr %_90.sroa.4.sroa.4.0._90.sroa.4.0._86.sroa_idx.sroa_idx, align 8
  %_90.sroa.4.sroa.5.0._90.sroa.4.0._86.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_86, i64 24
  store i32 42, ptr %_90.sroa.4.sroa.5.0._90.sroa.4.0._86.sroa_idx.sroa_idx, align 8
  %61 = getelementptr inbounds i8, ptr %_86, i64 80
  store i8 2, ptr %61, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %62 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_86) #26
  %_85.0 = extractvalue { i64, ptr } %62, 0
  %_85.1 = extractvalue { i64, ptr } %62, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_86)
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %_94)
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %_94, ptr noundef nonnull align 1 dereferenceable(32) %_79, i64 32, i1 false)
  %63 = getelementptr inbounds i8, ptr %_94, i64 32
  call void @llvm.memset.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %63, i8 0, i64 32, i1 false)
; call anchor_lang::error::Error::with_pubkeys
  %64 = call { i64, ptr } @_ZN11anchor_lang5error5Error12with_pubkeys17hca6dbbbe6a9a5da7E(i64 noundef %_85.0, ptr noundef %_85.1, ptr noalias nocapture noundef nonnull readonly align 1 dereferenceable(64) %_94) #26
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %_94)
  br label %bb81

bb43:                                             ; preds = %bb40
  %65 = call i32 @memcmp(ptr noundef nonnull dereferenceable(32) %t, ptr noundef nonnull dereferenceable(32) %holder_key, i64 32)
  %66 = icmp eq i32 %65, 0
  br i1 %66, label %bb45, label %bb54, !prof !76

bb45:                                             ; preds = %bb43, %bb40
  %67 = load volatile i8, ptr %holder_key, align 1
  %68 = load volatile i8, ptr %holder_key, align 1
  %69 = load volatile i8, ptr %holder_key, align 1
  %70 = load volatile i8, ptr %holder_key, align 1
  %71 = load volatile i8, ptr %holder_key, align 1
  %72 = load volatile i8, ptr %holder_key, align 1
  %73 = load volatile i8, ptr %holder_key, align 1
  %74 = load volatile i8, ptr %holder_key, align 1
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_130)
  %75 = getelementptr inbounds i8, ptr %_130, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %75, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_861c8964bbad6d9cede9df277e628fe9) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_132 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 19) #26
  %76 = getelementptr inbounds i8, ptr %_130, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %76, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_861c8964bbad6d9cede9df277e628fe9) #26
  %77 = getelementptr inbounds i8, ptr %_130, i64 152
  store i32 %_132, ptr %77, align 8
  store i64 0, ptr %_130, align 8
  %_134.sroa.4.0._130.sroa_idx = getelementptr inbounds i8, ptr %_130, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_134.sroa.4.0._130.sroa_idx, align 8
  %_134.sroa.4.sroa.4.0._134.sroa.4.0._130.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_130, i64 16
  store i64 103, ptr %_134.sroa.4.sroa.4.0._134.sroa.4.0._130.sroa_idx.sroa_idx, align 8
  %_134.sroa.4.sroa.5.0._134.sroa.4.0._130.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_130, i64 24
  store i32 47, ptr %_134.sroa.4.sroa.5.0._134.sroa.4.0._130.sroa_idx.sroa_idx, align 8
  %78 = getelementptr inbounds i8, ptr %_130, i64 80
  store i8 2, ptr %78, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %79 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_130) #26
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_130)
  br label %bb81

bb81:                                             ; preds = %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit41", %bb35, %bb45
  %.pn = phi { i64, ptr } [ %54, %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit41" ], [ %64, %bb35 ], [ %79, %bb45 ]
  %_69.1.sink = extractvalue { i64, ptr } %.pn, 1
  %_69.0.sink = extractvalue { i64, ptr } %.pn, 0
  %80 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_69.0.sink, ptr %80, align 8
  %81 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_69.1.sink, ptr %81, align 8
  store i8 1, ptr %_0, align 8
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %t)
  br label %bb84

bb17:                                             ; preds = %bb16
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_40)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_41)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_41, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_f94f166953c814e4161e699857179a1e) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_42 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 84) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i56)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i44), !noalias !77
  store i64 0, ptr %buf.i44, align 8, !noalias !77
  %_9.sroa.4.0.buf.sroa_idx.i45 = getelementptr inbounds i8, ptr %buf.i44, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i45, align 8, !noalias !77
  %_9.sroa.5.0.buf.sroa_idx.i46 = getelementptr inbounds i8, ptr %buf.i44, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i46, align 8, !noalias !77
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i43), !noalias !77
  %82 = getelementptr inbounds i8, ptr %formatter.i43, i64 52
  store i32 0, ptr %82, align 4, !noalias !77
  %83 = getelementptr inbounds i8, ptr %formatter.i43, i64 48
  store i32 32, ptr %83, align 8, !noalias !77
  %84 = getelementptr inbounds i8, ptr %formatter.i43, i64 56
  store i8 3, ptr %84, align 8, !noalias !77
  store i64 0, ptr %formatter.i43, align 8, !noalias !77
  %85 = getelementptr inbounds i8, ptr %formatter.i43, i64 16
  store i64 0, ptr %85, align 8, !noalias !77
  %86 = getelementptr inbounds i8, ptr %formatter.i43, i64 32
  store ptr %buf.i44, ptr %86, align 8, !noalias !77
  %87 = getelementptr inbounds i8, ptr %formatter.i43, i64 40
  store ptr @vtable.0, ptr %87, align 8, !noalias !77
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %88 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_f94f166953c814e4161e699857179a1e, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i43) #26, !noalias !81
  br i1 %88, label %bb3.i47, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit48"

bb3.i47:                                          ; preds = %bb17
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i56, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !81
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit48": ; preds = %bb17
  %89 = getelementptr inbounds i8, ptr %_40, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %89, ptr noundef nonnull align 8 dereferenceable(24) %buf.i44, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i43), !noalias !77
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i44), !noalias !77
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i56)
  %90 = getelementptr inbounds i8, ptr %_40, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %90, ptr noundef nonnull align 8 dereferenceable(24) %_41, i64 24, i1 false)
  %91 = getelementptr inbounds i8, ptr %_40, i64 152
  store i32 %_42, ptr %91, align 8
  store i64 0, ptr %_40, align 8
  %_44.sroa.4.0._40.sroa_idx = getelementptr inbounds i8, ptr %_40, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_44.sroa.4.0._40.sroa_idx, align 8
  %_44.sroa.4.sroa.4.0._44.sroa.4.0._40.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_40, i64 16
  store i64 103, ptr %_44.sroa.4.sroa.4.0._44.sroa.4.0._40.sroa_idx.sroa_idx, align 8
  %_44.sroa.4.sroa.5.0._44.sroa.4.0._40.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_40, i64 24
  store i32 31, ptr %_44.sroa.4.sroa.5.0._44.sroa.4.0._40.sroa_idx.sroa_idx, align 8
  %92 = getelementptr inbounds i8, ptr %_40, i64 80
  store i8 2, ptr %92, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_41)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %93 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_40) #26
  %_39.0 = extractvalue { i64, ptr } %93, 0
  %_39.1 = extractvalue { i64, ptr } %93, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_40)
  %94 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_39.0, ptr %94, align 8
  %95 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_39.1, ptr %95, align 8
  store i8 1, ptr %_0, align 8
  br label %bb84

bb91:                                             ; preds = %bb23
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_49)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_50)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_50, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_b5f839a6bda937f2cae73e49fc88071f) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_51 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 90) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i56)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i51), !noalias !82
  store i64 0, ptr %buf.i51, align 8, !noalias !82
  %_9.sroa.4.0.buf.sroa_idx.i52 = getelementptr inbounds i8, ptr %buf.i51, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i52, align 8, !noalias !82
  %_9.sroa.5.0.buf.sroa_idx.i53 = getelementptr inbounds i8, ptr %buf.i51, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i53, align 8, !noalias !82
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i50), !noalias !82
  %96 = getelementptr inbounds i8, ptr %formatter.i50, i64 52
  store i32 0, ptr %96, align 4, !noalias !82
  %97 = getelementptr inbounds i8, ptr %formatter.i50, i64 48
  store i32 32, ptr %97, align 8, !noalias !82
  %98 = getelementptr inbounds i8, ptr %formatter.i50, i64 56
  store i8 3, ptr %98, align 8, !noalias !82
  store i64 0, ptr %formatter.i50, align 8, !noalias !82
  %99 = getelementptr inbounds i8, ptr %formatter.i50, i64 16
  store i64 0, ptr %99, align 8, !noalias !82
  %100 = getelementptr inbounds i8, ptr %formatter.i50, i64 32
  store ptr %buf.i51, ptr %100, align 8, !noalias !82
  %101 = getelementptr inbounds i8, ptr %formatter.i50, i64 40
  store ptr @vtable.0, ptr %101, align 8, !noalias !82
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %102 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_b5f839a6bda937f2cae73e49fc88071f, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i50) #26, !noalias !86
  br i1 %102, label %bb3.i54, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit55"

bb3.i54:                                          ; preds = %bb91
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i56, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !86
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit55": ; preds = %bb91
  %103 = getelementptr inbounds i8, ptr %_49, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %103, ptr noundef nonnull align 8 dereferenceable(24) %buf.i51, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i50), !noalias !82
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i51), !noalias !82
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i56)
  %104 = getelementptr inbounds i8, ptr %_49, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %104, ptr noundef nonnull align 8 dereferenceable(24) %_50, i64 24, i1 false)
  %105 = getelementptr inbounds i8, ptr %_49, i64 152
  store i32 %_51, ptr %105, align 8
  store i64 0, ptr %_49, align 8
  %_53.sroa.4.0._49.sroa_idx = getelementptr inbounds i8, ptr %_49, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_53.sroa.4.0._49.sroa_idx, align 8
  %_53.sroa.4.sroa.4.0._53.sroa.4.0._49.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_49, i64 16
  store i64 103, ptr %_53.sroa.4.sroa.4.0._53.sroa.4.0._49.sroa_idx.sroa_idx, align 8
  %_53.sroa.4.sroa.5.0._53.sroa.4.0._49.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_49, i64 24
  store i32 33, ptr %_53.sroa.4.sroa.5.0._53.sroa.4.0._49.sroa_idx.sroa_idx, align 8
  %106 = getelementptr inbounds i8, ptr %_49, i64 80
  store i8 2, ptr %106, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_50)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %107 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_49) #26
  %_48.0 = extractvalue { i64, ptr } %107, 0
  %_48.1 = extractvalue { i64, ptr } %107, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_49)
  %108 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_48.0, ptr %108, align 8
  %109 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_48.1, ptr %109, align 8
  store i8 1, ptr %_0, align 8
  br label %bb84

bb84:                                             ; preds = %bb62, %bb67, %bb75, %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit62", %bb81, %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit55", %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit48", %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit34"
  call void @llvm.lifetime.end.p0(i64 25, ptr nonnull %target_tail)
  call void @llvm.lifetime.end.p0(i64 7, ptr nonnull %target_head)
  br label %bb85

bb54:                                             ; preds = %bb43
  call void @llvm.lifetime.start.p0(i64 7, ptr nonnull %target_head)
  call void @llvm.lifetime.start.p0(i64 25, ptr nonnull %target_tail)
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(7) %target_head, ptr noundef nonnull align 1 dereferenceable(7) %_79, i64 7, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %b1)
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %b1, ptr noundef nonnull align 1 dereferenceable(32) %_79, i64 32, i1 false)
  %_146 = getelementptr inbounds i8, ptr %b1, i64 7
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(25) %target_tail, ptr noundef nonnull align 1 dereferenceable(25) %_146, i64 25, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %b1)
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %t)
  %110 = getelementptr inbounds i8, ptr %st, i64 42
  %111 = load i8, ptr %110, align 2, !range !57, !noundef !2
  %.not = icmp eq i8 %111, 0
  %switch24 = icmp eq i64 %1, 0
  br i1 %switch24, label %bb79, label %bb56

bb53:                                             ; preds = %bb23
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(7) %target_head, ptr noundef nonnull align 1 dereferenceable(7) %holder_key, i64 7, i1 false)
  %_62 = getelementptr inbounds i8, ptr %holder_key, i64 7
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(25) %target_tail, ptr noundef nonnull align 1 dereferenceable(25) %_62, i64 25, i1 false)
  %switch25 = icmp eq i64 %1, 0
  br i1 %switch25, label %bb79, label %bb118

bb79:                                             ; preds = %bb53, %bb54, %bb74
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(7) %b2, ptr noundef nonnull align 1 dereferenceable(7) %target_head, i64 7, i1 false)
  %_206 = getelementptr inbounds i8, ptr %b2, i64 7
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(25) %_206, ptr noundef nonnull align 1 dereferenceable(25) %target_tail, i64 25, i1 false)
  %112 = getelementptr inbounds i8, ptr %_0, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %112, ptr noundef nonnull align 1 dereferenceable(32) %b2, i64 32, i1 false)
  store i8 0, ptr %_0, align 8
  call void @llvm.lifetime.end.p0(i64 25, ptr nonnull %target_tail)
  call void @llvm.lifetime.end.p0(i64 7, ptr nonnull %target_head)
  br label %bb85

bb56:                                             ; preds = %bb54
  %113 = getelementptr inbounds i8, ptr %st, i64 43
  %114 = load i8, ptr %113, align 1, !range !57, !noundef !2
  %.not22 = icmp eq i8 %114, 0
  br i1 %.not22, label %bb61, label %bb57

bb61:                                             ; preds = %bb56
  br i1 %.not, label %bb63, label %bb62

bb57:                                             ; preds = %bb118, %bb56
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_156)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_157)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_157, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_e75cefee4bb91125af0ea8444b842ed0) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_158 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 91) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i56)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i58), !noalias !87
  store i64 0, ptr %buf.i58, align 8, !noalias !87
  %_9.sroa.4.0.buf.sroa_idx.i59 = getelementptr inbounds i8, ptr %buf.i58, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i59, align 8, !noalias !87
  %_9.sroa.5.0.buf.sroa_idx.i60 = getelementptr inbounds i8, ptr %buf.i58, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i60, align 8, !noalias !87
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i57), !noalias !87
  %115 = getelementptr inbounds i8, ptr %formatter.i57, i64 52
  store i32 0, ptr %115, align 4, !noalias !87
  %116 = getelementptr inbounds i8, ptr %formatter.i57, i64 48
  store i32 32, ptr %116, align 8, !noalias !87
  %117 = getelementptr inbounds i8, ptr %formatter.i57, i64 56
  store i8 3, ptr %117, align 8, !noalias !87
  store i64 0, ptr %formatter.i57, align 8, !noalias !87
  %118 = getelementptr inbounds i8, ptr %formatter.i57, i64 16
  store i64 0, ptr %118, align 8, !noalias !87
  %119 = getelementptr inbounds i8, ptr %formatter.i57, i64 32
  store ptr %buf.i58, ptr %119, align 8, !noalias !87
  %120 = getelementptr inbounds i8, ptr %formatter.i57, i64 40
  store ptr @vtable.0, ptr %120, align 8, !noalias !87
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %121 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_e75cefee4bb91125af0ea8444b842ed0, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i57) #26, !noalias !91
  br i1 %121, label %bb3.i61, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit62"

bb3.i61:                                          ; preds = %bb57
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i56, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !91
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit62": ; preds = %bb57
  %122 = getelementptr inbounds i8, ptr %_156, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %122, ptr noundef nonnull align 8 dereferenceable(24) %buf.i58, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i57), !noalias !87
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i58), !noalias !87
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i56)
  %123 = getelementptr inbounds i8, ptr %_156, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %123, ptr noundef nonnull align 8 dereferenceable(24) %_157, i64 24, i1 false)
  %124 = getelementptr inbounds i8, ptr %_156, i64 152
  store i32 %_158, ptr %124, align 8
  store i64 0, ptr %_156, align 8
  %_160.sroa.4.0._156.sroa_idx = getelementptr inbounds i8, ptr %_156, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_160.sroa.4.0._156.sroa_idx, align 8
  %_160.sroa.4.sroa.4.0._160.sroa.4.0._156.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_156, i64 16
  store i64 103, ptr %_160.sroa.4.sroa.4.0._160.sroa.4.0._156.sroa_idx.sroa_idx, align 8
  %_160.sroa.4.sroa.5.0._160.sroa.4.0._156.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_156, i64 24
  store i32 61, ptr %_160.sroa.4.sroa.5.0._160.sroa.4.0._156.sroa_idx.sroa_idx, align 8
  %125 = getelementptr inbounds i8, ptr %_156, i64 80
  store i8 2, ptr %125, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_157)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %126 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_156) #26
  %_155.0 = extractvalue { i64, ptr } %126, 0
  %_155.1 = extractvalue { i64, ptr } %126, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_156)
  %127 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_155.0, ptr %127, align 8
  %128 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_155.1, ptr %128, align 8
  store i8 1, ptr %_0, align 8
  br label %bb84

bb63:                                             ; preds = %bb118, %bb61
  %129 = load volatile i8, ptr %holder_key, align 1
  %130 = getelementptr inbounds i8, ptr %st, i64 45
  %131 = load i8, ptr %130, align 1, !range !57, !noundef !2
  %_177.not = icmp eq i8 %131, 0
  br i1 %_177.not, label %bb67, label %bb71

bb62:                                             ; preds = %bb61
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_166)
  %132 = getelementptr inbounds i8, ptr %_166, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %132, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_835bb996f1795bf0338da0490417da62) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_168 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 80) #26
  %133 = getelementptr inbounds i8, ptr %_166, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %133, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_835bb996f1795bf0338da0490417da62) #26
  %134 = getelementptr inbounds i8, ptr %_166, i64 152
  store i32 %_168, ptr %134, align 8
  store i64 0, ptr %_166, align 8
  %_170.sroa.4.0._166.sroa_idx = getelementptr inbounds i8, ptr %_166, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_170.sroa.4.0._166.sroa_idx, align 8
  %_170.sroa.4.sroa.4.0._170.sroa.4.0._166.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_166, i64 16
  store i64 103, ptr %_170.sroa.4.sroa.4.0._170.sroa.4.0._166.sroa_idx.sroa_idx, align 8
  %_170.sroa.4.sroa.5.0._170.sroa.4.0._166.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_166, i64 24
  store i32 65, ptr %_170.sroa.4.sroa.5.0._170.sroa.4.0._166.sroa_idx.sroa_idx, align 8
  %135 = getelementptr inbounds i8, ptr %_166, i64 80
  store i8 2, ptr %135, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %136 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_166) #26
  %_165.0 = extractvalue { i64, ptr } %136, 0
  %_165.1 = extractvalue { i64, ptr } %136, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_166)
  %137 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_165.0, ptr %137, align 8
  %138 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_165.1, ptr %138, align 8
  store i8 1, ptr %_0, align 8
  br label %bb84

bb118:                                            ; preds = %bb53
  %139 = getelementptr inbounds i8, ptr %st, i64 43
  %140 = load i8, ptr %139, align 1, !range !57, !noundef !2
  %.not23 = icmp eq i8 %140, 0
  br i1 %.not23, label %bb63, label %bb57

bb67:                                             ; preds = %bb63
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_179)
  %141 = getelementptr inbounds i8, ptr %_179, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %141, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_01eaaa187d2be542d4425f23ab284310) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_181 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 77) #26
  %142 = getelementptr inbounds i8, ptr %_179, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %142, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_01eaaa187d2be542d4425f23ab284310) #26
  %143 = getelementptr inbounds i8, ptr %_179, i64 152
  store i32 %_181, ptr %143, align 8
  store i64 0, ptr %_179, align 8
  %_183.sroa.4.0._179.sroa_idx = getelementptr inbounds i8, ptr %_179, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_183.sroa.4.0._179.sroa_idx, align 8
  %_183.sroa.4.sroa.4.0._183.sroa.4.0._179.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_179, i64 16
  store i64 103, ptr %_183.sroa.4.sroa.4.0._183.sroa.4.0._179.sroa_idx.sroa_idx, align 8
  %_183.sroa.4.sroa.5.0._183.sroa.4.0._179.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_179, i64 24
  store i32 69, ptr %_183.sroa.4.sroa.5.0._183.sroa.4.0._179.sroa_idx.sroa_idx, align 8
  %144 = getelementptr inbounds i8, ptr %_179, i64 80
  store i8 2, ptr %144, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %145 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_179) #26
  %_178.0 = extractvalue { i64, ptr } %145, 0
  %_178.1 = extractvalue { i64, ptr } %145, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_179)
  %146 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_178.0, ptr %146, align 8
  %147 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_178.1, ptr %147, align 8
  store i8 1, ptr %_0, align 8
  br label %bb84

bb71:                                             ; preds = %bb63
  %148 = getelementptr inbounds i8, ptr %st, i64 32
  %_188 = load i64, ptr %148, align 8
  %149 = freeze i64 %_188
  %150 = add i64 %2, -1
  %or.cond.not = icmp ult i64 %150, %149
  br i1 %or.cond.not, label %bb74, label %bb75

bb75:                                             ; preds = %bb71
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_190)
  %151 = getelementptr inbounds i8, ptr %_190, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %151, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_973adb9e8664e25d4750ddb14e0de56a) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_192 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 78) #26
  %152 = getelementptr inbounds i8, ptr %_190, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %152, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_973adb9e8664e25d4750ddb14e0de56a) #26
  %153 = getelementptr inbounds i8, ptr %_190, i64 152
  store i32 %_192, ptr %153, align 8
  store i64 0, ptr %_190, align 8
  %_194.sroa.4.0._190.sroa_idx = getelementptr inbounds i8, ptr %_190, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_194.sroa.4.0._190.sroa_idx, align 8
  %_194.sroa.4.sroa.4.0._194.sroa.4.0._190.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_190, i64 16
  store i64 103, ptr %_194.sroa.4.sroa.4.0._194.sroa.4.0._190.sroa_idx.sroa_idx, align 8
  %_194.sroa.4.sroa.5.0._194.sroa.4.0._190.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_190, i64 24
  store i32 73, ptr %_194.sroa.4.sroa.5.0._194.sroa.4.0._190.sroa_idx.sroa_idx, align 8
  %154 = getelementptr inbounds i8, ptr %_190, i64 80
  store i8 2, ptr %154, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %155 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_190) #26
  %_189.0 = extractvalue { i64, ptr } %155, 0
  %_189.1 = extractvalue { i64, ptr } %155, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_190)
  %156 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_189.0, ptr %156, align 8
  %157 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_189.1, ptr %157, align 8
  store i8 1, ptr %_0, align 8
  br label %bb84

bb74:                                             ; preds = %bb71
  %158 = load volatile i8, ptr %holder_key, align 1
  br label %bb79

bb85:                                             ; preds = %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit", %bb84, %bb79
  ret void
}

; Function Attrs: nounwind
define void @custom_mir_validate(ptr dead_on_unwind noalias nocapture noundef writable writeonly sret([40 x i8]) align 8 dereferenceable(40) %_0, ptr noalias nocapture noundef readonly align 8 dereferenceable(48) %_1, i8 noundef %0, i64 noundef %1, i64 %2, ptr noalias nocapture noundef readonly align 1 dereferenceable(33) %_4, ptr noalias noundef readonly align 1 dereferenceable(32) %_5, ptr noalias nocapture noundef readonly align 1 dereferenceable(32) %_6) unnamed_addr #1 {
start:
  %_11.i51 = alloca [0 x i8], align 1
  %formatter.i52 = alloca [64 x i8], align 8
  %buf.i53 = alloca [24 x i8], align 8
  %formatter.i45 = alloca [64 x i8], align 8
  %buf.i46 = alloca [24 x i8], align 8
  %formatter.i38 = alloca [64 x i8], align 8
  %buf.i39 = alloca [24 x i8], align 8
  %formatter.i31 = alloca [64 x i8], align 8
  %buf.i32 = alloca [24 x i8], align 8
  %formatter.i24 = alloca [64 x i8], align 8
  %buf.i25 = alloca [24 x i8], align 8
  %formatter.i = alloca [64 x i8], align 8
  %buf.i = alloca [24 x i8], align 8
  %_173 = alloca [160 x i8], align 8
  %_162 = alloca [160 x i8], align 8
  %_149 = alloca [160 x i8], align 8
  %_140 = alloca [24 x i8], align 8
  %_139 = alloca [160 x i8], align 8
  %_123 = alloca [160 x i8], align 8
  %_87 = alloca [64 x i8], align 1
  %_79 = alloca [160 x i8], align 8
  %_76 = alloca [32 x i8], align 1
  %_64 = alloca [24 x i8], align 8
  %_63 = alloca [160 x i8], align 8
  %_59 = alloca [32 x i8], align 1
  %_49 = alloca [24 x i8], align 8
  %_48 = alloca [160 x i8], align 8
  %_40 = alloca [24 x i8], align 8
  %_39 = alloca [160 x i8], align 8
  %_26 = alloca [24 x i8], align 8
  %_25 = alloca [160 x i8], align 8
  %_19 = alloca [32 x i8], align 1
  %_12 = alloca [24 x i8], align 8
  %_11 = alloca [160 x i8], align 8
  %3 = and i8 %0, -3
  %_0.sroa.0.0.off0.i.not = icmp eq i8 %3, 0
  %4 = getelementptr inbounds i8, ptr %_1, i64 40
  %5 = load i8, ptr %4, align 8, !range !57, !noundef !2
  %_9.not = icmp eq i8 %5, 0
  br i1 %_9.not, label %bb6, label %bb2

bb6:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %_19)
  %6 = getelementptr inbounds i8, ptr %_1, i64 41
  %7 = load i8, ptr %6, align 1, !range !57, !noundef !2
  %_21.not = icmp eq i8 %7, 0
  br i1 %_21.not, label %bb7, label %bb8

bb2:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_11)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_12)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_12, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_eb4f91695bc6f999067c65f428fcc4d8) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_13 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 88) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i51)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i), !noalias !92
  store i64 0, ptr %buf.i, align 8, !noalias !92
  %_9.sroa.4.0.buf.sroa_idx.i = getelementptr inbounds i8, ptr %buf.i, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i, align 8, !noalias !92
  %_9.sroa.5.0.buf.sroa_idx.i = getelementptr inbounds i8, ptr %buf.i, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i, align 8, !noalias !92
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i), !noalias !92
  %8 = getelementptr inbounds i8, ptr %formatter.i, i64 52
  store i32 0, ptr %8, align 4, !noalias !92
  %9 = getelementptr inbounds i8, ptr %formatter.i, i64 48
  store i32 32, ptr %9, align 8, !noalias !92
  %10 = getelementptr inbounds i8, ptr %formatter.i, i64 56
  store i8 3, ptr %10, align 8, !noalias !92
  store i64 0, ptr %formatter.i, align 8, !noalias !92
  %11 = getelementptr inbounds i8, ptr %formatter.i, i64 16
  store i64 0, ptr %11, align 8, !noalias !92
  %12 = getelementptr inbounds i8, ptr %formatter.i, i64 32
  store ptr %buf.i, ptr %12, align 8, !noalias !92
  %13 = getelementptr inbounds i8, ptr %formatter.i, i64 40
  store ptr @vtable.0, ptr %13, align 8, !noalias !92
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %14 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_eb4f91695bc6f999067c65f428fcc4d8, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i) #26, !noalias !96
  br i1 %14, label %bb3.i, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit"

bb3.i:                                            ; preds = %bb2
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i51, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !96
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit": ; preds = %bb2
  %15 = getelementptr inbounds i8, ptr %_11, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %15, ptr noundef nonnull align 8 dereferenceable(24) %buf.i, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i), !noalias !92
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i), !noalias !92
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i51)
  %16 = getelementptr inbounds i8, ptr %_11, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %16, ptr noundef nonnull align 8 dereferenceable(24) %_12, i64 24, i1 false)
  %17 = getelementptr inbounds i8, ptr %_11, i64 152
  store i32 %_13, ptr %17, align 8
  store i64 0, ptr %_11, align 8
  %_15.sroa.4.0._11.sroa_idx = getelementptr inbounds i8, ptr %_11, i64 8
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_15.sroa.4.0._11.sroa_idx, align 8
  %_15.sroa.4.sroa.4.0._15.sroa.4.0._11.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_11, i64 16
  store i64 38, ptr %_15.sroa.4.sroa.4.0._15.sroa.4.0._11.sroa_idx.sroa_idx, align 8
  %_15.sroa.4.sroa.5.0._15.sroa.4.0._11.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_11, i64 24
  store i32 284, ptr %_15.sroa.4.sroa.5.0._15.sroa.4.0._11.sroa_idx.sroa_idx, align 8
  %18 = getelementptr inbounds i8, ptr %_11, i64 80
  store i8 2, ptr %18, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_12)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %19 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_11) #26
  %_10.0 = extractvalue { i64, ptr } %19, 0
  %_10.1 = extractvalue { i64, ptr } %19, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_11)
  %20 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_10.0, ptr %20, align 8
  %21 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_10.1, ptr %21, align 8
  store i8 1, ptr %_0, align 8
  br label %bb84

bb8:                                              ; preds = %bb6
  br i1 %_0.sroa.0.0.off0.i.not, label %bb11, label %bb23

bb7:                                              ; preds = %bb6
  br i1 %_0.sroa.0.0.off0.i.not, label %bb22, label %bb16, !prof !97

bb11:                                             ; preds = %bb8
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_25)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_26)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_26, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_8f95cb73e89711d65e95d13598508b19) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_27 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 83) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i51)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i25), !noalias !98
  store i64 0, ptr %buf.i25, align 8, !noalias !98
  %_9.sroa.4.0.buf.sroa_idx.i26 = getelementptr inbounds i8, ptr %buf.i25, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i26, align 8, !noalias !98
  %_9.sroa.5.0.buf.sroa_idx.i27 = getelementptr inbounds i8, ptr %buf.i25, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i27, align 8, !noalias !98
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i24), !noalias !98
  %22 = getelementptr inbounds i8, ptr %formatter.i24, i64 52
  store i32 0, ptr %22, align 4, !noalias !98
  %23 = getelementptr inbounds i8, ptr %formatter.i24, i64 48
  store i32 32, ptr %23, align 8, !noalias !98
  %24 = getelementptr inbounds i8, ptr %formatter.i24, i64 56
  store i8 3, ptr %24, align 8, !noalias !98
  store i64 0, ptr %formatter.i24, align 8, !noalias !98
  %25 = getelementptr inbounds i8, ptr %formatter.i24, i64 16
  store i64 0, ptr %25, align 8, !noalias !98
  %26 = getelementptr inbounds i8, ptr %formatter.i24, i64 32
  store ptr %buf.i25, ptr %26, align 8, !noalias !98
  %27 = getelementptr inbounds i8, ptr %formatter.i24, i64 40
  store ptr @vtable.0, ptr %27, align 8, !noalias !98
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %28 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_8f95cb73e89711d65e95d13598508b19, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i24) #26, !noalias !102
  br i1 %28, label %bb3.i28, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit29"

bb3.i28:                                          ; preds = %bb11
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i51, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !102
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit29": ; preds = %bb11
  %29 = getelementptr inbounds i8, ptr %_25, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %29, ptr noundef nonnull align 8 dereferenceable(24) %buf.i25, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i24), !noalias !98
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i25), !noalias !98
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i51)
  %30 = getelementptr inbounds i8, ptr %_25, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %30, ptr noundef nonnull align 8 dereferenceable(24) %_26, i64 24, i1 false)
  %31 = getelementptr inbounds i8, ptr %_25, i64 152
  store i32 %_27, ptr %31, align 8
  store i64 0, ptr %_25, align 8
  %_29.sroa.4.0._25.sroa_idx = getelementptr inbounds i8, ptr %_25, i64 8
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_29.sroa.4.0._25.sroa_idx, align 8
  %_29.sroa.4.sroa.4.0._29.sroa.4.0._25.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_25, i64 16
  store i64 38, ptr %_29.sroa.4.sroa.4.0._29.sroa.4.0._25.sroa_idx.sroa_idx, align 8
  %_29.sroa.4.sroa.5.0._29.sroa.4.0._25.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_25, i64 24
  store i32 289, ptr %_29.sroa.4.sroa.5.0._29.sroa.4.0._25.sroa_idx.sroa_idx, align 8
  %32 = getelementptr inbounds i8, ptr %_25, i64 80
  store i8 2, ptr %32, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_26)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %33 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_25) #26
  %_24.0 = extractvalue { i64, ptr } %33, 0
  %_24.1 = extractvalue { i64, ptr } %33, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_25)
  %34 = load volatile i8, ptr %_5, align 1
  %35 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_24.0, ptr %35, align 8
  %36 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_24.1, ptr %36, align 8
  store i8 1, ptr %_0, align 8
  br label %bb83

bb23:                                             ; preds = %bb16, %bb8
  %37 = load i8, ptr %_4, align 1, !range !57, !noundef !2
  %trunc16.not.not = icmp eq i8 %37, 0
  br i1 %trunc16.not.not, label %bb52, label %bb90

bb22:                                             ; preds = %bb7
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %_19)
  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %_59)
  %38 = load i8, ptr %_4, align 1, !range !57, !noundef !2
  %trunc.not = icmp eq i8 %38, 0
  br i1 %trunc.not, label %bb29, label %bb119, !prof !97

bb16:                                             ; preds = %bb7
  %39 = getelementptr inbounds i8, ptr %_1, i64 44
  %40 = load i8, ptr %39, align 4, !range !57, !noundef !2
  %_37.not = icmp eq i8 %40, 0
  br i1 %_37.not, label %bb17, label %bb23

bb119:                                            ; preds = %bb22
  %41 = load volatile i8, ptr %_5, align 1
  %42 = load volatile i8, ptr %_5, align 1
  %_214.not = icmp eq i8 %41, %42
  br i1 %_214.not, label %bb33, label %bb123, !prof !97

bb29:                                             ; preds = %bb22
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_63)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_64)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_64, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_1ba5e1e397ae92b788c97e688ac0b362) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_65 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 89) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i51)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i32), !noalias !103
  store i64 0, ptr %buf.i32, align 8, !noalias !103
  %_9.sroa.4.0.buf.sroa_idx.i33 = getelementptr inbounds i8, ptr %buf.i32, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i33, align 8, !noalias !103
  %_9.sroa.5.0.buf.sroa_idx.i34 = getelementptr inbounds i8, ptr %buf.i32, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i34, align 8, !noalias !103
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i31), !noalias !103
  %43 = getelementptr inbounds i8, ptr %formatter.i31, i64 52
  store i32 0, ptr %43, align 4, !noalias !103
  %44 = getelementptr inbounds i8, ptr %formatter.i31, i64 48
  store i32 32, ptr %44, align 8, !noalias !103
  %45 = getelementptr inbounds i8, ptr %formatter.i31, i64 56
  store i8 3, ptr %45, align 8, !noalias !103
  store i64 0, ptr %formatter.i31, align 8, !noalias !103
  %46 = getelementptr inbounds i8, ptr %formatter.i31, i64 16
  store i64 0, ptr %46, align 8, !noalias !103
  %47 = getelementptr inbounds i8, ptr %formatter.i31, i64 32
  store ptr %buf.i32, ptr %47, align 8, !noalias !103
  %48 = getelementptr inbounds i8, ptr %formatter.i31, i64 40
  store ptr @vtable.0, ptr %48, align 8, !noalias !103
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %49 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_1ba5e1e397ae92b788c97e688ac0b362, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i31) #26, !noalias !107
  br i1 %49, label %bb3.i35, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit36"

bb3.i35:                                          ; preds = %bb29
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i51, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !107
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit36": ; preds = %bb29
  %50 = getelementptr inbounds i8, ptr %_63, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %50, ptr noundef nonnull align 8 dereferenceable(24) %buf.i32, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i31), !noalias !103
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i32), !noalias !103
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i51)
  %51 = getelementptr inbounds i8, ptr %_63, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %51, ptr noundef nonnull align 8 dereferenceable(24) %_64, i64 24, i1 false)
  %52 = getelementptr inbounds i8, ptr %_63, i64 152
  store i32 %_65, ptr %52, align 8
  store i64 0, ptr %_63, align 8
  %_67.sroa.4.0._63.sroa_idx = getelementptr inbounds i8, ptr %_63, i64 8
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_67.sroa.4.0._63.sroa_idx, align 8
  %_67.sroa.4.sroa.4.0._67.sroa.4.0._63.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_63, i64 16
  store i64 38, ptr %_67.sroa.4.sroa.4.0._67.sroa.4.0._63.sroa_idx.sroa_idx, align 8
  %_67.sroa.4.sroa.5.0._67.sroa.4.0._63.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_63, i64 24
  store i32 306, ptr %_67.sroa.4.sroa.5.0._67.sroa.4.0._63.sroa_idx.sroa_idx, align 8
  %53 = getelementptr inbounds i8, ptr %_63, i64 80
  store i8 2, ptr %53, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_64)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %54 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_63) #26
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_63)
  br label %bb80

bb33:                                             ; preds = %bb119
  %_72 = getelementptr inbounds i8, ptr %_4, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %_59, ptr noundef nonnull align 1 dereferenceable(32) %_72, i64 32, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %_76)
  call void @llvm.memset.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %_76, i8 0, i64 32, i1 false)
  %55 = call i32 @memcmp(ptr noundef nonnull dereferenceable(32) %_59, ptr noundef nonnull dereferenceable(32) %_76, i64 32)
  %56 = icmp eq i32 %55, 0
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %_76)
  br i1 %56, label %bb35, label %bb40

bb123:                                            ; preds = %bb119
  %57 = load volatile i8, ptr %_5, align 1
  tail call void @llvm.trap() #26
  unreachable

bb40:                                             ; preds = %bb33
  %58 = call i32 @memcmp(ptr noundef nonnull dereferenceable(32) %_59, ptr noundef nonnull dereferenceable(32) %_5, i64 32)
  %59 = icmp eq i32 %58, 0
  %60 = zext i1 %59 to i8
  %_93 = tail call noundef zeroext i8 @llvm.bpf.passthrough.i8.i8(i32 noundef zeroext 4, i8 noundef zeroext %60) #26
  %_92 = and i8 %_93, 1
  %_91.not = icmp eq i8 %_92, 0
  br i1 %_91.not, label %bb43, label %bb124, !prof !75

bb35:                                             ; preds = %bb33
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_79)
  %61 = getelementptr inbounds i8, ptr %_79, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %61, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_0e3505805f4905816c1bd644811a7869) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_81 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 30) #26
  %62 = getelementptr inbounds i8, ptr %_79, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %62, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_0e3505805f4905816c1bd644811a7869) #26
  %63 = getelementptr inbounds i8, ptr %_79, i64 152
  store i32 %_81, ptr %63, align 8
  store i64 0, ptr %_79, align 8
  %_83.sroa.4.0._79.sroa_idx = getelementptr inbounds i8, ptr %_79, i64 8
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_83.sroa.4.0._79.sroa_idx, align 8
  %_83.sroa.4.sroa.4.0._83.sroa.4.0._79.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_79, i64 16
  store i64 38, ptr %_83.sroa.4.sroa.4.0._83.sroa.4.0._79.sroa_idx.sroa_idx, align 8
  %_83.sroa.4.sroa.5.0._83.sroa.4.0._79.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_79, i64 24
  store i32 307, ptr %_83.sroa.4.sroa.5.0._83.sroa.4.0._79.sroa_idx.sroa_idx, align 8
  %64 = getelementptr inbounds i8, ptr %_79, i64 80
  store i8 2, ptr %64, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %65 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_79) #26
  %_78.0 = extractvalue { i64, ptr } %65, 0
  %_78.1 = extractvalue { i64, ptr } %65, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_79)
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %_87)
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %_87, ptr noundef nonnull align 1 dereferenceable(32) %_72, i64 32, i1 false)
  %66 = getelementptr inbounds i8, ptr %_87, i64 32
  call void @llvm.memset.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %66, i8 0, i64 32, i1 false)
; call anchor_lang::error::Error::with_pubkeys
  %67 = call { i64, ptr } @_ZN11anchor_lang5error5Error12with_pubkeys17hca6dbbbe6a9a5da7E(i64 noundef %_78.0, ptr noundef %_78.1, ptr noalias nocapture noundef nonnull readonly align 1 dereferenceable(64) %_87) #26
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %_87)
  br label %bb80

bb43:                                             ; preds = %bb40
  %68 = call i32 @memcmp(ptr noundef nonnull dereferenceable(32) %_59, ptr noundef nonnull dereferenceable(32) %_6, i64 32)
  %69 = icmp eq i32 %68, 0
  br i1 %69, label %bb124, label %bb53, !prof !76

bb124:                                            ; preds = %bb43, %bb40
  %70 = load volatile i8, ptr %_5, align 1
  %71 = load volatile i8, ptr %_5, align 1
  %_205.not = icmp eq i8 %70, %71
  br i1 %_205.not, label %bb109, label %bb127

bb127:                                            ; preds = %bb124
  %72 = load volatile i8, ptr %_5, align 1
  tail call void @llvm.trap() #26
  unreachable

bb109:                                            ; preds = %bb124
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_123)
  %73 = getelementptr inbounds i8, ptr %_123, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %73, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_861c8964bbad6d9cede9df277e628fe9) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_125 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 19) #26
  %74 = getelementptr inbounds i8, ptr %_123, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %74, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_861c8964bbad6d9cede9df277e628fe9) #26
  %75 = getelementptr inbounds i8, ptr %_123, i64 152
  store i32 %_125, ptr %75, align 8
  store i64 0, ptr %_123, align 8
  %_127.sroa.4.0._123.sroa_idx = getelementptr inbounds i8, ptr %_123, i64 8
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_127.sroa.4.0._123.sroa_idx, align 8
  %_127.sroa.4.sroa.4.0._127.sroa.4.0._123.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_123, i64 16
  store i64 38, ptr %_127.sroa.4.sroa.4.0._127.sroa.4.0._123.sroa_idx.sroa_idx, align 8
  %_127.sroa.4.sroa.5.0._127.sroa.4.0._123.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_123, i64 24
  store i32 312, ptr %_127.sroa.4.sroa.5.0._127.sroa.4.0._123.sroa_idx.sroa_idx, align 8
  %76 = getelementptr inbounds i8, ptr %_123, i64 80
  store i8 2, ptr %76, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %77 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_123) #26
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_123)
  br label %bb80

bb80:                                             ; preds = %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit36", %bb35, %bb109
  %.pn = phi { i64, ptr } [ %54, %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit36" ], [ %67, %bb35 ], [ %77, %bb109 ]
  %_62.1.sink = extractvalue { i64, ptr } %.pn, 1
  %_62.0.sink = extractvalue { i64, ptr } %.pn, 0
  %78 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_62.0.sink, ptr %78, align 8
  %79 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_62.1.sink, ptr %79, align 8
  store i8 1, ptr %_0, align 8
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %_59)
  br label %bb83

bb17:                                             ; preds = %bb16
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_39)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_40)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_40, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_f94f166953c814e4161e699857179a1e) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_41 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 84) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i51)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i39), !noalias !108
  store i64 0, ptr %buf.i39, align 8, !noalias !108
  %_9.sroa.4.0.buf.sroa_idx.i40 = getelementptr inbounds i8, ptr %buf.i39, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i40, align 8, !noalias !108
  %_9.sroa.5.0.buf.sroa_idx.i41 = getelementptr inbounds i8, ptr %buf.i39, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i41, align 8, !noalias !108
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i38), !noalias !108
  %80 = getelementptr inbounds i8, ptr %formatter.i38, i64 52
  store i32 0, ptr %80, align 4, !noalias !108
  %81 = getelementptr inbounds i8, ptr %formatter.i38, i64 48
  store i32 32, ptr %81, align 8, !noalias !108
  %82 = getelementptr inbounds i8, ptr %formatter.i38, i64 56
  store i8 3, ptr %82, align 8, !noalias !108
  store i64 0, ptr %formatter.i38, align 8, !noalias !108
  %83 = getelementptr inbounds i8, ptr %formatter.i38, i64 16
  store i64 0, ptr %83, align 8, !noalias !108
  %84 = getelementptr inbounds i8, ptr %formatter.i38, i64 32
  store ptr %buf.i39, ptr %84, align 8, !noalias !108
  %85 = getelementptr inbounds i8, ptr %formatter.i38, i64 40
  store ptr @vtable.0, ptr %85, align 8, !noalias !108
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %86 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_f94f166953c814e4161e699857179a1e, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i38) #26, !noalias !112
  br i1 %86, label %bb3.i42, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit43"

bb3.i42:                                          ; preds = %bb17
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i51, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !112
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit43": ; preds = %bb17
  %87 = getelementptr inbounds i8, ptr %_39, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %87, ptr noundef nonnull align 8 dereferenceable(24) %buf.i39, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i38), !noalias !108
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i39), !noalias !108
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i51)
  %88 = getelementptr inbounds i8, ptr %_39, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %88, ptr noundef nonnull align 8 dereferenceable(24) %_40, i64 24, i1 false)
  %89 = getelementptr inbounds i8, ptr %_39, i64 152
  store i32 %_41, ptr %89, align 8
  store i64 0, ptr %_39, align 8
  %_43.sroa.4.0._39.sroa_idx = getelementptr inbounds i8, ptr %_39, i64 8
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_43.sroa.4.0._39.sroa_idx, align 8
  %_43.sroa.4.sroa.4.0._43.sroa.4.0._39.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_39, i64 16
  store i64 38, ptr %_43.sroa.4.sroa.4.0._43.sroa.4.0._39.sroa_idx.sroa_idx, align 8
  %_43.sroa.4.sroa.5.0._43.sroa.4.0._39.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_39, i64 24
  store i32 296, ptr %_43.sroa.4.sroa.5.0._43.sroa.4.0._39.sroa_idx.sroa_idx, align 8
  %90 = getelementptr inbounds i8, ptr %_39, i64 80
  store i8 2, ptr %90, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_40)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %91 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_39) #26
  %_38.0 = extractvalue { i64, ptr } %91, 0
  %_38.1 = extractvalue { i64, ptr } %91, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_39)
  %92 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_38.0, ptr %92, align 8
  %93 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_38.1, ptr %93, align 8
  store i8 1, ptr %_0, align 8
  br label %bb83

bb90:                                             ; preds = %bb23
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_48)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_49)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_49, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_b5f839a6bda937f2cae73e49fc88071f) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_50 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 90) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i51)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i46), !noalias !113
  store i64 0, ptr %buf.i46, align 8, !noalias !113
  %_9.sroa.4.0.buf.sroa_idx.i47 = getelementptr inbounds i8, ptr %buf.i46, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i47, align 8, !noalias !113
  %_9.sroa.5.0.buf.sroa_idx.i48 = getelementptr inbounds i8, ptr %buf.i46, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i48, align 8, !noalias !113
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i45), !noalias !113
  %94 = getelementptr inbounds i8, ptr %formatter.i45, i64 52
  store i32 0, ptr %94, align 4, !noalias !113
  %95 = getelementptr inbounds i8, ptr %formatter.i45, i64 48
  store i32 32, ptr %95, align 8, !noalias !113
  %96 = getelementptr inbounds i8, ptr %formatter.i45, i64 56
  store i8 3, ptr %96, align 8, !noalias !113
  store i64 0, ptr %formatter.i45, align 8, !noalias !113
  %97 = getelementptr inbounds i8, ptr %formatter.i45, i64 16
  store i64 0, ptr %97, align 8, !noalias !113
  %98 = getelementptr inbounds i8, ptr %formatter.i45, i64 32
  store ptr %buf.i46, ptr %98, align 8, !noalias !113
  %99 = getelementptr inbounds i8, ptr %formatter.i45, i64 40
  store ptr @vtable.0, ptr %99, align 8, !noalias !113
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %100 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_b5f839a6bda937f2cae73e49fc88071f, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i45) #26, !noalias !117
  br i1 %100, label %bb3.i49, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit50"

bb3.i49:                                          ; preds = %bb90
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i51, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !117
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit50": ; preds = %bb90
  %101 = getelementptr inbounds i8, ptr %_48, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %101, ptr noundef nonnull align 8 dereferenceable(24) %buf.i46, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i45), !noalias !113
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i46), !noalias !113
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i51)
  %102 = getelementptr inbounds i8, ptr %_48, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %102, ptr noundef nonnull align 8 dereferenceable(24) %_49, i64 24, i1 false)
  %103 = getelementptr inbounds i8, ptr %_48, i64 152
  store i32 %_50, ptr %103, align 8
  store i64 0, ptr %_48, align 8
  %_52.sroa.4.0._48.sroa_idx = getelementptr inbounds i8, ptr %_48, i64 8
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_52.sroa.4.0._48.sroa_idx, align 8
  %_52.sroa.4.sroa.4.0._52.sroa.4.0._48.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_48, i64 16
  store i64 38, ptr %_52.sroa.4.sroa.4.0._52.sroa.4.0._48.sroa_idx.sroa_idx, align 8
  %_52.sroa.4.sroa.5.0._52.sroa.4.0._48.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_48, i64 24
  store i32 298, ptr %_52.sroa.4.sroa.5.0._52.sroa.4.0._48.sroa_idx.sroa_idx, align 8
  %104 = getelementptr inbounds i8, ptr %_48, i64 80
  store i8 2, ptr %104, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_49)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %105 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_48) #26
  %_47.0 = extractvalue { i64, ptr } %105, 0
  %_47.1 = extractvalue { i64, ptr } %105, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_48)
  %106 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_47.0, ptr %106, align 8
  %107 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_47.1, ptr %107, align 8
  store i8 1, ptr %_0, align 8
  br label %bb83

bb83:                                             ; preds = %bb61, %bb66, %bb74, %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit57", %bb80, %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit50", %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit43", %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit29"
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %_19)
  br label %bb84

bb53:                                             ; preds = %bb43
  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %_19)
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %_19, ptr noundef nonnull align 1 dereferenceable(32) %_72, i64 32, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %_59)
  %108 = getelementptr inbounds i8, ptr %_1, i64 42
  %109 = load i8, ptr %108, align 2, !range !57, !noundef !2
  %.not = icmp eq i8 %109, 0
  %switch19 = icmp eq i64 %1, 0
  br i1 %switch19, label %bb78, label %bb55

bb52:                                             ; preds = %bb23
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %_19, ptr noundef nonnull align 1 dereferenceable(32) %_5, i64 32, i1 false)
  %switch20 = icmp eq i64 %1, 0
  br i1 %switch20, label %bb78, label %bb117

bb78:                                             ; preds = %bb52, %bb53, %bb73
  %110 = getelementptr inbounds i8, ptr %_0, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %110, ptr noundef nonnull align 1 dereferenceable(32) %_19, i64 32, i1 false)
  store i8 0, ptr %_0, align 8
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %_19)
  br label %bb84

bb55:                                             ; preds = %bb53
  %111 = getelementptr inbounds i8, ptr %_1, i64 43
  %112 = load i8, ptr %111, align 1, !range !57, !noundef !2
  %.not17 = icmp eq i8 %112, 0
  br i1 %.not17, label %bb60, label %bb56

bb60:                                             ; preds = %bb55
  br i1 %.not, label %bb62, label %bb61

bb56:                                             ; preds = %bb117, %bb55
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_139)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_140)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_140, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_e75cefee4bb91125af0ea8444b842ed0) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_141 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 91) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i51)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i53), !noalias !118
  store i64 0, ptr %buf.i53, align 8, !noalias !118
  %_9.sroa.4.0.buf.sroa_idx.i54 = getelementptr inbounds i8, ptr %buf.i53, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i54, align 8, !noalias !118
  %_9.sroa.5.0.buf.sroa_idx.i55 = getelementptr inbounds i8, ptr %buf.i53, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i55, align 8, !noalias !118
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i52), !noalias !118
  %113 = getelementptr inbounds i8, ptr %formatter.i52, i64 52
  store i32 0, ptr %113, align 4, !noalias !118
  %114 = getelementptr inbounds i8, ptr %formatter.i52, i64 48
  store i32 32, ptr %114, align 8, !noalias !118
  %115 = getelementptr inbounds i8, ptr %formatter.i52, i64 56
  store i8 3, ptr %115, align 8, !noalias !118
  store i64 0, ptr %formatter.i52, align 8, !noalias !118
  %116 = getelementptr inbounds i8, ptr %formatter.i52, i64 16
  store i64 0, ptr %116, align 8, !noalias !118
  %117 = getelementptr inbounds i8, ptr %formatter.i52, i64 32
  store ptr %buf.i53, ptr %117, align 8, !noalias !118
  %118 = getelementptr inbounds i8, ptr %formatter.i52, i64 40
  store ptr @vtable.0, ptr %118, align 8, !noalias !118
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %119 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_e75cefee4bb91125af0ea8444b842ed0, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i52) #26, !noalias !122
  br i1 %119, label %bb3.i56, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit57"

bb3.i56:                                          ; preds = %bb56
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i51, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !122
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit57": ; preds = %bb56
  %120 = getelementptr inbounds i8, ptr %_139, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %120, ptr noundef nonnull align 8 dereferenceable(24) %buf.i53, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i52), !noalias !118
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i53), !noalias !118
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i51)
  %121 = getelementptr inbounds i8, ptr %_139, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %121, ptr noundef nonnull align 8 dereferenceable(24) %_140, i64 24, i1 false)
  %122 = getelementptr inbounds i8, ptr %_139, i64 152
  store i32 %_141, ptr %122, align 8
  store i64 0, ptr %_139, align 8
  %_143.sroa.4.0._139.sroa_idx = getelementptr inbounds i8, ptr %_139, i64 8
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_143.sroa.4.0._139.sroa_idx, align 8
  %_143.sroa.4.sroa.4.0._143.sroa.4.0._139.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_139, i64 16
  store i64 38, ptr %_143.sroa.4.sroa.4.0._143.sroa.4.0._139.sroa_idx.sroa_idx, align 8
  %_143.sroa.4.sroa.5.0._143.sroa.4.0._139.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_139, i64 24
  store i32 326, ptr %_143.sroa.4.sroa.5.0._143.sroa.4.0._139.sroa_idx.sroa_idx, align 8
  %123 = getelementptr inbounds i8, ptr %_139, i64 80
  store i8 2, ptr %123, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_140)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %124 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_139) #26
  %_138.0 = extractvalue { i64, ptr } %124, 0
  %_138.1 = extractvalue { i64, ptr } %124, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_139)
  %125 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_138.0, ptr %125, align 8
  %126 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_138.1, ptr %126, align 8
  store i8 1, ptr %_0, align 8
  br label %bb83

bb62:                                             ; preds = %bb117, %bb60
  %127 = getelementptr inbounds i8, ptr %_1, i64 45
  %128 = load i8, ptr %127, align 1, !range !57, !noundef !2
  %_160.not = icmp eq i8 %128, 0
  br i1 %_160.not, label %bb66, label %bb70

bb61:                                             ; preds = %bb60
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_149)
  %129 = getelementptr inbounds i8, ptr %_149, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %129, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_835bb996f1795bf0338da0490417da62) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_151 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 80) #26
  %130 = getelementptr inbounds i8, ptr %_149, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %130, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_835bb996f1795bf0338da0490417da62) #26
  %131 = getelementptr inbounds i8, ptr %_149, i64 152
  store i32 %_151, ptr %131, align 8
  store i64 0, ptr %_149, align 8
  %_153.sroa.4.0._149.sroa_idx = getelementptr inbounds i8, ptr %_149, i64 8
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_153.sroa.4.0._149.sroa_idx, align 8
  %_153.sroa.4.sroa.4.0._153.sroa.4.0._149.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_149, i64 16
  store i64 38, ptr %_153.sroa.4.sroa.4.0._153.sroa.4.0._149.sroa_idx.sroa_idx, align 8
  %_153.sroa.4.sroa.5.0._153.sroa.4.0._149.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_149, i64 24
  store i32 330, ptr %_153.sroa.4.sroa.5.0._153.sroa.4.0._149.sroa_idx.sroa_idx, align 8
  %132 = getelementptr inbounds i8, ptr %_149, i64 80
  store i8 2, ptr %132, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %133 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_149) #26
  %_148.0 = extractvalue { i64, ptr } %133, 0
  %_148.1 = extractvalue { i64, ptr } %133, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_149)
  %134 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_148.0, ptr %134, align 8
  %135 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_148.1, ptr %135, align 8
  store i8 1, ptr %_0, align 8
  br label %bb83

bb117:                                            ; preds = %bb52
  %136 = getelementptr inbounds i8, ptr %_1, i64 43
  %137 = load i8, ptr %136, align 1, !range !57, !noundef !2
  %.not18 = icmp eq i8 %137, 0
  br i1 %.not18, label %bb62, label %bb56

bb66:                                             ; preds = %bb62
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_162)
  %138 = getelementptr inbounds i8, ptr %_162, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %138, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_01eaaa187d2be542d4425f23ab284310) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_164 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 77) #26
  %139 = getelementptr inbounds i8, ptr %_162, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %139, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_01eaaa187d2be542d4425f23ab284310) #26
  %140 = getelementptr inbounds i8, ptr %_162, i64 152
  store i32 %_164, ptr %140, align 8
  store i64 0, ptr %_162, align 8
  %_166.sroa.4.0._162.sroa_idx = getelementptr inbounds i8, ptr %_162, i64 8
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_166.sroa.4.0._162.sroa_idx, align 8
  %_166.sroa.4.sroa.4.0._166.sroa.4.0._162.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_162, i64 16
  store i64 38, ptr %_166.sroa.4.sroa.4.0._166.sroa.4.0._162.sroa_idx.sroa_idx, align 8
  %_166.sroa.4.sroa.5.0._166.sroa.4.0._162.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_162, i64 24
  store i32 334, ptr %_166.sroa.4.sroa.5.0._166.sroa.4.0._162.sroa_idx.sroa_idx, align 8
  %141 = getelementptr inbounds i8, ptr %_162, i64 80
  store i8 2, ptr %141, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %142 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_162) #26
  %_161.0 = extractvalue { i64, ptr } %142, 0
  %_161.1 = extractvalue { i64, ptr } %142, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_162)
  %143 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_161.0, ptr %143, align 8
  %144 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_161.1, ptr %144, align 8
  store i8 1, ptr %_0, align 8
  br label %bb83

bb70:                                             ; preds = %bb62
  %145 = getelementptr inbounds i8, ptr %_1, i64 32
  %_171 = load i64, ptr %145, align 8
  %146 = freeze i64 %_171
  %147 = add i64 %2, -1
  %or.cond.not = icmp ult i64 %147, %146
  br i1 %or.cond.not, label %bb73, label %bb74

bb74:                                             ; preds = %bb70
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_173)
  %148 = getelementptr inbounds i8, ptr %_173, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %148, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_973adb9e8664e25d4750ddb14e0de56a) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_175 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 78) #26
  %149 = getelementptr inbounds i8, ptr %_173, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %149, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_973adb9e8664e25d4750ddb14e0de56a) #26
  %150 = getelementptr inbounds i8, ptr %_173, i64 152
  store i32 %_175, ptr %150, align 8
  store i64 0, ptr %_173, align 8
  %_177.sroa.4.0._173.sroa_idx = getelementptr inbounds i8, ptr %_173, i64 8
  store ptr @alloc_ebe040a358b3132776a16f34a7b7aa5b, ptr %_177.sroa.4.0._173.sroa_idx, align 8
  %_177.sroa.4.sroa.4.0._177.sroa.4.0._173.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_173, i64 16
  store i64 38, ptr %_177.sroa.4.sroa.4.0._177.sroa.4.0._173.sroa_idx.sroa_idx, align 8
  %_177.sroa.4.sroa.5.0._177.sroa.4.0._173.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_173, i64 24
  store i32 338, ptr %_177.sroa.4.sroa.5.0._177.sroa.4.0._173.sroa_idx.sroa_idx, align 8
  %151 = getelementptr inbounds i8, ptr %_173, i64 80
  store i8 2, ptr %151, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %152 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_173) #26
  %_172.0 = extractvalue { i64, ptr } %152, 0
  %_172.1 = extractvalue { i64, ptr } %152, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_173)
  %153 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_172.0, ptr %153, align 8
  %154 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_172.1, ptr %154, align 8
  store i8 1, ptr %_0, align 8
  br label %bb83

bb73:                                             ; preds = %bb70
  %155 = load volatile i8, ptr %_5, align 1
  br label %bb78

bb84:                                             ; preds = %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit", %bb83, %bb78
  ret void
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define noundef i64 @actual_curve_size() unnamed_addr #5 {
start:
  ret i64 160
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define noundef i64 @actual_account_size() unnamed_addr #5 {
start:
  ret i64 168
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define noundef i64 @actual_box_size() unnamed_addr #5 {
start:
  ret i64 8
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define noundef i64 @actual_curve_holder_offset(ptr noalias nocapture noundef readonly align 8 dereferenceable(160) %x) unnamed_addr #5 {
start:
  ret i64 157
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define noundef i64 @actual_account_holder_offset(ptr noalias nocapture noundef readonly align 8 dereferenceable(168) %x) unnamed_addr #5 {
start:
  ret i64 165
}

; Function Attrs: mustprogress nofree norecurse nounwind willreturn
define noundef i8 @actual_account_raw_hold(ptr noalias noundef readonly align 8 dereferenceable(8) %x) unnamed_addr #6 {
start:
  %0 = load volatile ptr, ptr %x, align 8
  %_5 = getelementptr inbounds i8, ptr %0, i64 165
  %1 = load volatile i8, ptr %_5, align 1
  ret i8 %1
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(read, inaccessiblemem: none)
define noundef zeroext i1 @actual_account_holder(ptr noalias nocapture noundef readonly align 8 dereferenceable(8) %x) unnamed_addr #7 {
start:
  %_2 = load ptr, ptr %x, align 8, !nonnull !2, !align !123, !noundef !2
  %0 = getelementptr inbounds i8, ptr %_2, i64 165
  %1 = load i8, ptr %0, align 1, !range !57, !noundef !2
  %_0 = icmp ne i8 %1, 0
  ret i1 %_0
}

; Function Attrs: nounwind
define void @actual_clone(ptr dead_on_unwind noalias nocapture noundef writable writeonly sret([48 x i8]) align 8 dereferenceable(48) %_0, ptr noalias nocapture noundef readonly align 8 dereferenceable(48) %x) unnamed_addr #1 {
start:
  %_2 = alloca [48 x i8], align 8
  call void @llvm.lifetime.start.p0(i64 48, ptr nonnull %_2)
  tail call void @llvm.experimental.noalias.scope.decl(metadata !124)
  tail call void @llvm.experimental.noalias.scope.decl(metadata !127)
  %_2.i = load ptr, ptr %x, align 8, !alias.scope !127, !noalias !124, !nonnull !2, !align !129, !noundef !2
  %0 = getelementptr inbounds i8, ptr %x, i64 8
  %_12.i = load ptr, ptr %0, align 8, !alias.scope !127, !noalias !124, !nonnull !2, !noundef !2
  %self.val.i.i = load i64, ptr %_12.i, align 8, !noalias !130, !noundef !2
  %cond.i.i = icmp ne i64 %self.val.i.i, 0
  tail call void @llvm.assume(i1 %cond.i.i)
  %strong1.i.i = add i64 %self.val.i.i, 1
  store i64 %strong1.i.i, ptr %_12.i, align 8, !noalias !130
  %_7.i.i = icmp eq i64 %strong1.i.i, 0
  br i1 %_7.i.i, label %bb4.i.i, label %_ZN5alloc2rc10RcInnerPtr10inc_strong17h3d0774391efcf2ceE.exit.i

bb4.i.i:                                          ; preds = %start
  tail call void @llvm.trap()
  unreachable

_ZN5alloc2rc10RcInnerPtr10inc_strong17h3d0774391efcf2ceE.exit.i: ; preds = %start
  %1 = getelementptr inbounds i8, ptr %x, i64 16
  %_16.i = load ptr, ptr %1, align 8, !alias.scope !127, !noalias !124, !nonnull !2, !noundef !2
  %self.val.i1.i = load i64, ptr %_16.i, align 8, !noalias !130, !noundef !2
  %cond.i2.i = icmp ne i64 %self.val.i1.i, 0
  tail call void @llvm.assume(i1 %cond.i2.i)
  %strong1.i3.i = add i64 %self.val.i1.i, 1
  store i64 %strong1.i3.i, ptr %_16.i, align 8, !noalias !130
  %_7.i4.i = icmp eq i64 %strong1.i3.i, 0
  br i1 %_7.i4.i, label %bb4.i5.i, label %"_ZN71_$LT$solana_account_info..AccountInfo$u20$as$u20$core..clone..Clone$GT$5clone17h759150bcde62cc00E.exit"

bb4.i5.i:                                         ; preds = %_ZN5alloc2rc10RcInnerPtr10inc_strong17h3d0774391efcf2ceE.exit.i
  tail call void @llvm.trap()
  unreachable

"_ZN71_$LT$solana_account_info..AccountInfo$u20$as$u20$core..clone..Clone$GT$5clone17h759150bcde62cc00E.exit": ; preds = %_ZN5alloc2rc10RcInnerPtr10inc_strong17h3d0774391efcf2ceE.exit.i
  %2 = getelementptr inbounds i8, ptr %x, i64 24
  %_5.i = load ptr, ptr %2, align 8, !alias.scope !127, !noalias !124, !nonnull !2, !align !129, !noundef !2
  %3 = getelementptr inbounds i8, ptr %x, i64 32
  %_6.i = load i64, ptr %3, align 8, !alias.scope !127, !noalias !124, !noundef !2
  %4 = getelementptr inbounds i8, ptr %x, i64 40
  %5 = load i8, ptr %4, align 8, !range !57, !alias.scope !127, !noalias !124, !noundef !2
  %6 = getelementptr inbounds i8, ptr %x, i64 41
  %7 = load i8, ptr %6, align 1, !range !57, !alias.scope !127, !noalias !124, !noundef !2
  %8 = getelementptr inbounds i8, ptr %x, i64 42
  %9 = load i8, ptr %8, align 2, !range !57, !alias.scope !127, !noalias !124, !noundef !2
  store ptr %_2.i, ptr %_2, align 8, !alias.scope !124, !noalias !127
  %10 = getelementptr inbounds i8, ptr %_2, i64 8
  store ptr %_12.i, ptr %10, align 8, !alias.scope !124, !noalias !127
  %11 = getelementptr inbounds i8, ptr %_2, i64 16
  store ptr %_16.i, ptr %11, align 8, !alias.scope !124, !noalias !127
  %12 = getelementptr inbounds i8, ptr %_2, i64 24
  store ptr %_5.i, ptr %12, align 8, !alias.scope !124, !noalias !127
  %13 = getelementptr inbounds i8, ptr %_2, i64 32
  store i64 %_6.i, ptr %13, align 8, !alias.scope !124, !noalias !127
  %14 = getelementptr inbounds i8, ptr %_2, i64 40
  store i8 %5, ptr %14, align 8, !alias.scope !124, !noalias !127
  %15 = getelementptr inbounds i8, ptr %_2, i64 41
  store i8 %7, ptr %15, align 1, !alias.scope !124, !noalias !127
  %16 = getelementptr inbounds i8, ptr %_2, i64 42
  store i8 %9, ptr %16, align 2, !alias.scope !124, !noalias !127
  call void @llvm.var.annotation.p0.p0(ptr noundef nonnull %_2, ptr noundef nonnull @alloc_914b2c69d7eca30497b9feaf15ac92f1, ptr noundef nonnull @alloc_914b2c69d7eca30497b9feaf15ac92f1, i32 noundef zeroext 0, ptr noundef null) #26
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(48) %_0, ptr noundef nonnull align 8 dereferenceable(48) %_2, i64 48, i1 false)
  call void @llvm.lifetime.end.p0(i64 48, ptr nonnull %_2)
  ret void
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define noundef i8 @nested_outer_none() unnamed_addr #5 {
start:
  ret i8 2
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define noundef i8 @nested_inner_none() unnamed_addr #5 {
start:
  ret i8 0
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define noundef i8 @nested_some(ptr noalias nocapture noundef readonly align 1 dereferenceable(32) %v) unnamed_addr #5 {
start:
  ret i8 1
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(argmem: readwrite)
define void @nested_raw(ptr dead_on_unwind noalias nocapture noundef writable writeonly sret([33 x i8]) align 1 dereferenceable(33) %_0, ptr noalias nocapture noundef readonly align 1 dereferenceable(33) %x) unnamed_addr #8 {
start:
  %ntag = load i8, ptr %x, align 1, !noundef !2
  %np = getelementptr inbounds i8, ptr %x, i64 1
  %out.sroa.5.0._0.sroa_idx = getelementptr inbounds i8, ptr %_0, i64 1
  tail call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %out.sroa.5.0._0.sroa_idx, ptr noundef nonnull align 1 dereferenceable(32) %np, i64 32, i1 false)
  store i8 %ntag, ptr %_0, align 1
  ret void
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(argmem: readwrite)
define void @nested_control(ptr dead_on_unwind noalias nocapture noundef writable writeonly sret([33 x i8]) align 1 dereferenceable(33) %_0, ptr noalias nocapture noundef readonly align 1 dereferenceable(33) %x) unnamed_addr #8 {
start:
  tail call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(33) %_0, ptr noundef nonnull align 1 dereferenceable(33) %x, i64 33, i1 false)
  ret void
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(inaccessiblemem: readwrite)
define noundef zeroext i1 @annotation_bool(i1 noundef zeroext %v) unnamed_addr #9 {
start:
  %_0 = tail call noundef zeroext i1 @llvm.annotation.i1.p0(i1 noundef zeroext %v, ptr noundef nonnull @alloc_914b2c69d7eca30497b9feaf15ac92f1, ptr noundef nonnull @alloc_914b2c69d7eca30497b9feaf15ac92f1, i32 noundef zeroext 0) #26
  ret i1 %_0
}

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(none)
define noundef zeroext i1 @annotation_control(i1 noundef returned zeroext %v) unnamed_addr #5 {
start:
  ret i1 %v
}

; Function Attrs: nounwind
define void @ordinary4158_validate(ptr dead_on_unwind noalias nocapture noundef writable writeonly sret([40 x i8]) align 8 dereferenceable(40) %_0, ptr noalias nocapture noundef readonly align 8 dereferenceable(48) %st, i8 noundef %0, i64 noundef %1, i64 %2, ptr noalias nocapture noundef readonly align 1 dereferenceable(33) %new, ptr noalias noundef readonly align 1 dereferenceable(32) %holder_key, ptr noalias nocapture noundef readonly align 1 dereferenceable(32) %sharing) unnamed_addr #1 {
start:
  %_11.i51 = alloca [0 x i8], align 1
  %formatter.i52 = alloca [64 x i8], align 8
  %buf.i53 = alloca [24 x i8], align 8
  %formatter.i45 = alloca [64 x i8], align 8
  %buf.i46 = alloca [24 x i8], align 8
  %formatter.i38 = alloca [64 x i8], align 8
  %buf.i39 = alloca [24 x i8], align 8
  %formatter.i31 = alloca [64 x i8], align 8
  %buf.i32 = alloca [24 x i8], align 8
  %formatter.i24 = alloca [64 x i8], align 8
  %buf.i25 = alloca [24 x i8], align 8
  %formatter.i = alloca [64 x i8], align 8
  %buf.i = alloca [24 x i8], align 8
  %b2 = alloca [32 x i8], align 1
  %_184 = alloca [160 x i8], align 8
  %_173 = alloca [160 x i8], align 8
  %_160 = alloca [160 x i8], align 8
  %_151 = alloca [24 x i8], align 8
  %_150 = alloca [160 x i8], align 8
  %_137 = alloca [160 x i8], align 8
  %b1 = alloca [32 x i8], align 1
  %_96 = alloca [64 x i8], align 1
  %_88 = alloca [160 x i8], align 8
  %_85 = alloca [32 x i8], align 1
  %_73 = alloca [24 x i8], align 8
  %_72 = alloca [160 x i8], align 8
  %t = alloca [32 x i8], align 1
  %_52 = alloca [24 x i8], align 8
  %_51 = alloca [160 x i8], align 8
  %_43 = alloca [24 x i8], align 8
  %_42 = alloca [160 x i8], align 8
  %_27 = alloca [24 x i8], align 8
  %_26 = alloca [160 x i8], align 8
  %target_tail = alloca [25 x i8], align 1
  %target_head = alloca [7 x i8], align 1
  %_12 = alloca [24 x i8], align 8
  %_11 = alloca [160 x i8], align 8
  %3 = and i8 %0, -3
  %_0.sroa.0.0.off0.i.not = icmp eq i8 %3, 0
  %4 = getelementptr inbounds i8, ptr %st, i64 40
  %5 = load i8, ptr %4, align 8, !range !57, !noundef !2
  %_9.not = icmp eq i8 %5, 0
  br i1 %_9.not, label %bb6, label %bb2

bb6:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 7, ptr nonnull %target_head)
  call void @llvm.lifetime.start.p0(i64 25, ptr nonnull %target_tail)
  %6 = getelementptr inbounds i8, ptr %st, i64 41
  %7 = load i8, ptr %6, align 1, !range !57, !noundef !2
  %_22.not = icmp eq i8 %7, 0
  br i1 %_22.not, label %bb7, label %bb8

bb2:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_11)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_12)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_12, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_eb4f91695bc6f999067c65f428fcc4d8) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_13 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 88) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i51)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i), !noalias !131
  store i64 0, ptr %buf.i, align 8, !noalias !131
  %_9.sroa.4.0.buf.sroa_idx.i = getelementptr inbounds i8, ptr %buf.i, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i, align 8, !noalias !131
  %_9.sroa.5.0.buf.sroa_idx.i = getelementptr inbounds i8, ptr %buf.i, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i, align 8, !noalias !131
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i), !noalias !131
  %8 = getelementptr inbounds i8, ptr %formatter.i, i64 52
  store i32 0, ptr %8, align 4, !noalias !131
  %9 = getelementptr inbounds i8, ptr %formatter.i, i64 48
  store i32 32, ptr %9, align 8, !noalias !131
  %10 = getelementptr inbounds i8, ptr %formatter.i, i64 56
  store i8 3, ptr %10, align 8, !noalias !131
  store i64 0, ptr %formatter.i, align 8, !noalias !131
  %11 = getelementptr inbounds i8, ptr %formatter.i, i64 16
  store i64 0, ptr %11, align 8, !noalias !131
  %12 = getelementptr inbounds i8, ptr %formatter.i, i64 32
  store ptr %buf.i, ptr %12, align 8, !noalias !131
  %13 = getelementptr inbounds i8, ptr %formatter.i, i64 40
  store ptr @vtable.0, ptr %13, align 8, !noalias !131
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %14 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_eb4f91695bc6f999067c65f428fcc4d8, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i) #26, !noalias !135
  br i1 %14, label %bb3.i, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit"

bb3.i:                                            ; preds = %bb2
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i51, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !135
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit": ; preds = %bb2
  %15 = getelementptr inbounds i8, ptr %_11, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %15, ptr noundef nonnull align 8 dereferenceable(24) %buf.i, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i), !noalias !131
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i), !noalias !131
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i51)
  %16 = getelementptr inbounds i8, ptr %_11, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %16, ptr noundef nonnull align 8 dereferenceable(24) %_12, i64 24, i1 false)
  %17 = getelementptr inbounds i8, ptr %_11, i64 152
  store i32 %_13, ptr %17, align 8
  store i64 0, ptr %_11, align 8
  %_15.sroa.4.0._11.sroa_idx = getelementptr inbounds i8, ptr %_11, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_15.sroa.4.0._11.sroa_idx, align 8
  %_15.sroa.4.sroa.4.0._15.sroa.4.0._11.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_11, i64 16
  store i64 103, ptr %_15.sroa.4.sroa.4.0._15.sroa.4.0._11.sroa_idx.sroa_idx, align 8
  %_15.sroa.4.sroa.5.0._15.sroa.4.0._11.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_11, i64 24
  store i32 154, ptr %_15.sroa.4.sroa.5.0._15.sroa.4.0._11.sroa_idx.sroa_idx, align 8
  %18 = getelementptr inbounds i8, ptr %_11, i64 80
  store i8 2, ptr %18, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_12)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %19 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_11) #26
  %_10.0 = extractvalue { i64, ptr } %19, 0
  %_10.1 = extractvalue { i64, ptr } %19, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_11)
  %20 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_10.0, ptr %20, align 8
  %21 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_10.1, ptr %21, align 8
  store i8 1, ptr %_0, align 8
  br label %bb91

bb8:                                              ; preds = %bb6
  br i1 %_0.sroa.0.0.off0.i.not, label %bb11, label %bb24

bb7:                                              ; preds = %bb6
  br i1 %_0.sroa.0.0.off0.i.not, label %bb23, label %bb16, !prof !63

bb11:                                             ; preds = %bb8
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_26)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_27)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_27, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_8f95cb73e89711d65e95d13598508b19) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_28 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 83) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i51)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i25), !noalias !136
  store i64 0, ptr %buf.i25, align 8, !noalias !136
  %_9.sroa.4.0.buf.sroa_idx.i26 = getelementptr inbounds i8, ptr %buf.i25, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i26, align 8, !noalias !136
  %_9.sroa.5.0.buf.sroa_idx.i27 = getelementptr inbounds i8, ptr %buf.i25, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i27, align 8, !noalias !136
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i24), !noalias !136
  %22 = getelementptr inbounds i8, ptr %formatter.i24, i64 52
  store i32 0, ptr %22, align 4, !noalias !136
  %23 = getelementptr inbounds i8, ptr %formatter.i24, i64 48
  store i32 32, ptr %23, align 8, !noalias !136
  %24 = getelementptr inbounds i8, ptr %formatter.i24, i64 56
  store i8 3, ptr %24, align 8, !noalias !136
  store i64 0, ptr %formatter.i24, align 8, !noalias !136
  %25 = getelementptr inbounds i8, ptr %formatter.i24, i64 16
  store i64 0, ptr %25, align 8, !noalias !136
  %26 = getelementptr inbounds i8, ptr %formatter.i24, i64 32
  store ptr %buf.i25, ptr %26, align 8, !noalias !136
  %27 = getelementptr inbounds i8, ptr %formatter.i24, i64 40
  store ptr @vtable.0, ptr %27, align 8, !noalias !136
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %28 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_8f95cb73e89711d65e95d13598508b19, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i24) #26, !noalias !140
  br i1 %28, label %bb3.i28, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit29"

bb3.i28:                                          ; preds = %bb11
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i51, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !140
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit29": ; preds = %bb11
  %29 = getelementptr inbounds i8, ptr %_26, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %29, ptr noundef nonnull align 8 dereferenceable(24) %buf.i25, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i24), !noalias !136
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i25), !noalias !136
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i51)
  %30 = getelementptr inbounds i8, ptr %_26, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %30, ptr noundef nonnull align 8 dereferenceable(24) %_27, i64 24, i1 false)
  %31 = getelementptr inbounds i8, ptr %_26, i64 152
  store i32 %_28, ptr %31, align 8
  store i64 0, ptr %_26, align 8
  %_30.sroa.4.0._26.sroa_idx = getelementptr inbounds i8, ptr %_26, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_30.sroa.4.0._26.sroa_idx, align 8
  %_30.sroa.4.sroa.4.0._30.sroa.4.0._26.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_26, i64 16
  store i64 103, ptr %_30.sroa.4.sroa.4.0._30.sroa.4.0._26.sroa_idx.sroa_idx, align 8
  %_30.sroa.4.sroa.5.0._30.sroa.4.0._26.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_26, i64 24
  store i32 159, ptr %_30.sroa.4.sroa.5.0._30.sroa.4.0._26.sroa_idx.sroa_idx, align 8
  %32 = getelementptr inbounds i8, ptr %_26, i64 80
  store i8 2, ptr %32, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_27)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %33 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_26) #26
  %_25.0 = extractvalue { i64, ptr } %33, 0
  %_25.1 = extractvalue { i64, ptr } %33, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_26)
  %34 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_25.0, ptr %34, align 8
  %35 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_25.1, ptr %35, align 8
  store i8 1, ptr %_0, align 8
  br label %bb90

bb24:                                             ; preds = %bb16, %bb8
  %36 = load i8, ptr %new, align 1, !range !57, !noundef !2
  %trunc15.not.not = icmp eq i8 %36, 0
  br i1 %trunc15.not.not, label %bb59, label %bb96

bb23:                                             ; preds = %bb7
  call void @llvm.lifetime.end.p0(i64 7, ptr nonnull %target_head)
  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %t)
  %37 = load i8, ptr %new, align 1, !range !57, !noundef !2
  %trunc.not = icmp eq i8 %37, 0
  br i1 %trunc.not, label %bb30, label %bb34, !prof !97

bb16:                                             ; preds = %bb7
  %_40 = tail call noundef i64 @llvm.bpf.passthrough.i64.i64(i32 noundef zeroext 12, i64 noundef 44) #26
  %_36 = getelementptr inbounds i8, ptr %st, i64 %_40
  %_35 = load i8, ptr %_36, align 1, !noundef !2
  %38 = icmp eq i8 %_35, 0
  br i1 %38, label %bb18, label %bb24

bb34:                                             ; preds = %bb23
  %_81 = getelementptr inbounds i8, ptr %new, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %t, ptr noundef nonnull align 1 dereferenceable(32) %_81, i64 32, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %_85)
  call void @llvm.memset.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %_85, i8 0, i64 32, i1 false)
  %39 = call i32 @memcmp(ptr noundef nonnull dereferenceable(32) %t, ptr noundef nonnull dereferenceable(32) %_85, i64 32)
  %40 = icmp eq i32 %39, 0
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %_85)
  br i1 %40, label %bb36, label %bb41

bb30:                                             ; preds = %bb23
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_72)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_73)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_73, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_1ba5e1e397ae92b788c97e688ac0b362) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_74 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 89) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i51)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i32), !noalias !141
  store i64 0, ptr %buf.i32, align 8, !noalias !141
  %_9.sroa.4.0.buf.sroa_idx.i33 = getelementptr inbounds i8, ptr %buf.i32, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i33, align 8, !noalias !141
  %_9.sroa.5.0.buf.sroa_idx.i34 = getelementptr inbounds i8, ptr %buf.i32, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i34, align 8, !noalias !141
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i31), !noalias !141
  %41 = getelementptr inbounds i8, ptr %formatter.i31, i64 52
  store i32 0, ptr %41, align 4, !noalias !141
  %42 = getelementptr inbounds i8, ptr %formatter.i31, i64 48
  store i32 32, ptr %42, align 8, !noalias !141
  %43 = getelementptr inbounds i8, ptr %formatter.i31, i64 56
  store i8 3, ptr %43, align 8, !noalias !141
  store i64 0, ptr %formatter.i31, align 8, !noalias !141
  %44 = getelementptr inbounds i8, ptr %formatter.i31, i64 16
  store i64 0, ptr %44, align 8, !noalias !141
  %45 = getelementptr inbounds i8, ptr %formatter.i31, i64 32
  store ptr %buf.i32, ptr %45, align 8, !noalias !141
  %46 = getelementptr inbounds i8, ptr %formatter.i31, i64 40
  store ptr @vtable.0, ptr %46, align 8, !noalias !141
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %47 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_1ba5e1e397ae92b788c97e688ac0b362, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i31) #26, !noalias !145
  br i1 %47, label %bb3.i35, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit36"

bb3.i35:                                          ; preds = %bb30
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i51, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !145
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit36": ; preds = %bb30
  %48 = getelementptr inbounds i8, ptr %_72, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %48, ptr noundef nonnull align 8 dereferenceable(24) %buf.i32, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i31), !noalias !141
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i32), !noalias !141
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i51)
  %49 = getelementptr inbounds i8, ptr %_72, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %49, ptr noundef nonnull align 8 dereferenceable(24) %_73, i64 24, i1 false)
  %50 = getelementptr inbounds i8, ptr %_72, i64 152
  store i32 %_74, ptr %50, align 8
  store i64 0, ptr %_72, align 8
  %_76.sroa.4.0._72.sroa_idx = getelementptr inbounds i8, ptr %_72, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_76.sroa.4.0._72.sroa_idx, align 8
  %_76.sroa.4.sroa.4.0._76.sroa.4.0._72.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_72, i64 16
  store i64 103, ptr %_76.sroa.4.sroa.4.0._76.sroa.4.0._72.sroa_idx.sroa_idx, align 8
  %_76.sroa.4.sroa.5.0._76.sroa.4.0._72.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_72, i64 24
  store i32 176, ptr %_76.sroa.4.sroa.5.0._76.sroa.4.0._72.sroa_idx.sroa_idx, align 8
  %51 = getelementptr inbounds i8, ptr %_72, i64 80
  store i8 2, ptr %51, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_73)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %52 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_72) #26
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_72)
  br label %bb87

bb41:                                             ; preds = %bb34
  %53 = call i32 @memcmp(ptr noundef nonnull dereferenceable(32) %t, ptr noundef nonnull dereferenceable(32) %holder_key, i64 32)
  %54 = icmp eq i32 %53, 0
  %55 = zext i1 %54 to i8
  %_102 = tail call noundef zeroext i8 @llvm.bpf.passthrough.i8.i8(i32 noundef zeroext 4, i8 noundef zeroext %55) #26
  %_101 = and i8 %_102, 1
  %_100 = icmp eq i8 %_101, 0
  br i1 %_100, label %bb44, label %bb54, !prof !97

bb36:                                             ; preds = %bb34
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_88)
  %56 = getelementptr inbounds i8, ptr %_88, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %56, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_0e3505805f4905816c1bd644811a7869) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_90 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 30) #26
  %57 = getelementptr inbounds i8, ptr %_88, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %57, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_0e3505805f4905816c1bd644811a7869) #26
  %58 = getelementptr inbounds i8, ptr %_88, i64 152
  store i32 %_90, ptr %58, align 8
  store i64 0, ptr %_88, align 8
  %_92.sroa.4.0._88.sroa_idx = getelementptr inbounds i8, ptr %_88, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_92.sroa.4.0._88.sroa_idx, align 8
  %_92.sroa.4.sroa.4.0._92.sroa.4.0._88.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_88, i64 16
  store i64 103, ptr %_92.sroa.4.sroa.4.0._92.sroa.4.0._88.sroa_idx.sroa_idx, align 8
  %_92.sroa.4.sroa.5.0._92.sroa.4.0._88.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_88, i64 24
  store i32 177, ptr %_92.sroa.4.sroa.5.0._92.sroa.4.0._88.sroa_idx.sroa_idx, align 8
  %59 = getelementptr inbounds i8, ptr %_88, i64 80
  store i8 2, ptr %59, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %60 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_88) #26
  %_87.0 = extractvalue { i64, ptr } %60, 0
  %_87.1 = extractvalue { i64, ptr } %60, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_88)
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %_96)
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %_96, ptr noundef nonnull align 1 dereferenceable(32) %_81, i64 32, i1 false)
  %61 = getelementptr inbounds i8, ptr %_96, i64 32
  call void @llvm.memset.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %61, i8 0, i64 32, i1 false)
; call anchor_lang::error::Error::with_pubkeys
  %62 = call { i64, ptr } @_ZN11anchor_lang5error5Error12with_pubkeys17hca6dbbbe6a9a5da7E(i64 noundef %_87.0, ptr noundef %_87.1, ptr noalias nocapture noundef nonnull readonly align 1 dereferenceable(64) %_96) #26
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %_96)
  br label %bb87

bb54:                                             ; preds = %bb44, %bb41
  %63 = load volatile i8, ptr %holder_key, align 1
  %64 = load volatile i8, ptr %holder_key, align 1
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_137)
  %65 = getelementptr inbounds i8, ptr %_137, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %65, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_861c8964bbad6d9cede9df277e628fe9) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_139 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 19) #26
  %66 = getelementptr inbounds i8, ptr %_137, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %66, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_861c8964bbad6d9cede9df277e628fe9) #26
  %67 = getelementptr inbounds i8, ptr %_137, i64 152
  store i32 %_139, ptr %67, align 8
  store i64 0, ptr %_137, align 8
  %_141.sroa.4.0._137.sroa_idx = getelementptr inbounds i8, ptr %_137, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_141.sroa.4.0._137.sroa_idx, align 8
  %_141.sroa.4.sroa.4.0._141.sroa.4.0._137.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_137, i64 16
  store i64 103, ptr %_141.sroa.4.sroa.4.0._141.sroa.4.0._137.sroa_idx.sroa_idx, align 8
  %_141.sroa.4.sroa.5.0._141.sroa.4.0._137.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_137, i64 24
  store i32 182, ptr %_141.sroa.4.sroa.5.0._141.sroa.4.0._137.sroa_idx.sroa_idx, align 8
  %68 = getelementptr inbounds i8, ptr %_137, i64 80
  store i8 2, ptr %68, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %69 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_137) #26
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_137)
  br label %bb87

bb44:                                             ; preds = %bb41
  %70 = call i32 @memcmp(ptr noundef nonnull dereferenceable(32) %t, ptr noundef nonnull dereferenceable(32) %sharing, i64 32)
  %.not = icmp eq i32 %70, 0
  br i1 %.not, label %bb54, label %bb46, !prof !146

bb46:                                             ; preds = %bb44
  call void @llvm.lifetime.start.p0(i64 7, ptr nonnull %target_head)
  call void @llvm.lifetime.start.p0(i64 25, ptr nonnull %target_tail)
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(7) %target_head, ptr noundef nonnull align 1 dereferenceable(7) %_81, i64 7, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %b1)
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %b1, ptr noundef nonnull align 1 dereferenceable(32) %_81, i64 32, i1 false)
  %_115 = getelementptr inbounds i8, ptr %b1, i64 7
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(25) %target_tail, ptr noundef nonnull align 1 dereferenceable(25) %_115, i64 25, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %b1)
  %_121 = icmp eq i64 %1, 0
  br i1 %_121, label %bb60.thread, label %bb62, !prof !97

bb87:                                             ; preds = %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit36", %bb36, %bb54
  %.pn = phi { i64, ptr } [ %52, %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit36" ], [ %62, %bb36 ], [ %69, %bb54 ]
  %_71.1.sink = extractvalue { i64, ptr } %.pn, 1
  %_71.0.sink = extractvalue { i64, ptr } %.pn, 0
  %71 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_71.0.sink, ptr %71, align 8
  %72 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_71.1.sink, ptr %72, align 8
  store i8 1, ptr %_0, align 8
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %t)
  br label %bb90

bb60.thread:                                      ; preds = %bb46
  %_125 = tail call noundef zeroext i1 @llvm.annotation.i1.p0(i1 noundef zeroext true, ptr noundef nonnull @alloc_914b2c69d7eca30497b9feaf15ac92f1, ptr noundef nonnull @alloc_914b2c69d7eca30497b9feaf15ac92f1, i32 noundef zeroext 0) #26
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %t)
  br label %bb85

bb18:                                             ; preds = %bb16
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_42)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_43)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_43, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_f94f166953c814e4161e699857179a1e) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_44 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 84) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i51)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i39), !noalias !147
  store i64 0, ptr %buf.i39, align 8, !noalias !147
  %_9.sroa.4.0.buf.sroa_idx.i40 = getelementptr inbounds i8, ptr %buf.i39, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i40, align 8, !noalias !147
  %_9.sroa.5.0.buf.sroa_idx.i41 = getelementptr inbounds i8, ptr %buf.i39, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i41, align 8, !noalias !147
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i38), !noalias !147
  %73 = getelementptr inbounds i8, ptr %formatter.i38, i64 52
  store i32 0, ptr %73, align 4, !noalias !147
  %74 = getelementptr inbounds i8, ptr %formatter.i38, i64 48
  store i32 32, ptr %74, align 8, !noalias !147
  %75 = getelementptr inbounds i8, ptr %formatter.i38, i64 56
  store i8 3, ptr %75, align 8, !noalias !147
  store i64 0, ptr %formatter.i38, align 8, !noalias !147
  %76 = getelementptr inbounds i8, ptr %formatter.i38, i64 16
  store i64 0, ptr %76, align 8, !noalias !147
  %77 = getelementptr inbounds i8, ptr %formatter.i38, i64 32
  store ptr %buf.i39, ptr %77, align 8, !noalias !147
  %78 = getelementptr inbounds i8, ptr %formatter.i38, i64 40
  store ptr @vtable.0, ptr %78, align 8, !noalias !147
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %79 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_f94f166953c814e4161e699857179a1e, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i38) #26, !noalias !151
  br i1 %79, label %bb3.i42, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit43"

bb3.i42:                                          ; preds = %bb18
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i51, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !151
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit43": ; preds = %bb18
  %80 = getelementptr inbounds i8, ptr %_42, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %80, ptr noundef nonnull align 8 dereferenceable(24) %buf.i39, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i38), !noalias !147
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i39), !noalias !147
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i51)
  %81 = getelementptr inbounds i8, ptr %_42, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %81, ptr noundef nonnull align 8 dereferenceable(24) %_43, i64 24, i1 false)
  %82 = getelementptr inbounds i8, ptr %_42, i64 152
  store i32 %_44, ptr %82, align 8
  store i64 0, ptr %_42, align 8
  %_46.sroa.4.0._42.sroa_idx = getelementptr inbounds i8, ptr %_42, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_46.sroa.4.0._42.sroa_idx, align 8
  %_46.sroa.4.sroa.4.0._46.sroa.4.0._42.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_42, i64 16
  store i64 103, ptr %_46.sroa.4.sroa.4.0._46.sroa.4.0._42.sroa_idx.sroa_idx, align 8
  %_46.sroa.4.sroa.5.0._46.sroa.4.0._42.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_42, i64 24
  store i32 166, ptr %_46.sroa.4.sroa.5.0._46.sroa.4.0._42.sroa_idx.sroa_idx, align 8
  %83 = getelementptr inbounds i8, ptr %_42, i64 80
  store i8 2, ptr %83, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_43)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %84 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_42) #26
  %_41.0 = extractvalue { i64, ptr } %84, 0
  %_41.1 = extractvalue { i64, ptr } %84, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_42)
  %85 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_41.0, ptr %85, align 8
  %86 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_41.1, ptr %86, align 8
  store i8 1, ptr %_0, align 8
  br label %bb90

bb96:                                             ; preds = %bb24
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_51)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_52)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_52, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_b5f839a6bda937f2cae73e49fc88071f) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_53 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 90) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i51)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i46), !noalias !152
  store i64 0, ptr %buf.i46, align 8, !noalias !152
  %_9.sroa.4.0.buf.sroa_idx.i47 = getelementptr inbounds i8, ptr %buf.i46, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i47, align 8, !noalias !152
  %_9.sroa.5.0.buf.sroa_idx.i48 = getelementptr inbounds i8, ptr %buf.i46, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i48, align 8, !noalias !152
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i45), !noalias !152
  %87 = getelementptr inbounds i8, ptr %formatter.i45, i64 52
  store i32 0, ptr %87, align 4, !noalias !152
  %88 = getelementptr inbounds i8, ptr %formatter.i45, i64 48
  store i32 32, ptr %88, align 8, !noalias !152
  %89 = getelementptr inbounds i8, ptr %formatter.i45, i64 56
  store i8 3, ptr %89, align 8, !noalias !152
  store i64 0, ptr %formatter.i45, align 8, !noalias !152
  %90 = getelementptr inbounds i8, ptr %formatter.i45, i64 16
  store i64 0, ptr %90, align 8, !noalias !152
  %91 = getelementptr inbounds i8, ptr %formatter.i45, i64 32
  store ptr %buf.i46, ptr %91, align 8, !noalias !152
  %92 = getelementptr inbounds i8, ptr %formatter.i45, i64 40
  store ptr @vtable.0, ptr %92, align 8, !noalias !152
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %93 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_b5f839a6bda937f2cae73e49fc88071f, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i45) #26, !noalias !156
  br i1 %93, label %bb3.i49, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit50"

bb3.i49:                                          ; preds = %bb96
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i51, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !156
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit50": ; preds = %bb96
  %94 = getelementptr inbounds i8, ptr %_51, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %94, ptr noundef nonnull align 8 dereferenceable(24) %buf.i46, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i45), !noalias !152
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i46), !noalias !152
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i51)
  %95 = getelementptr inbounds i8, ptr %_51, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %95, ptr noundef nonnull align 8 dereferenceable(24) %_52, i64 24, i1 false)
  %96 = getelementptr inbounds i8, ptr %_51, i64 152
  store i32 %_53, ptr %96, align 8
  store i64 0, ptr %_51, align 8
  %_55.sroa.4.0._51.sroa_idx = getelementptr inbounds i8, ptr %_51, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_55.sroa.4.0._51.sroa_idx, align 8
  %_55.sroa.4.sroa.4.0._55.sroa.4.0._51.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_51, i64 16
  store i64 103, ptr %_55.sroa.4.sroa.4.0._55.sroa.4.0._51.sroa_idx.sroa_idx, align 8
  %_55.sroa.4.sroa.5.0._55.sroa.4.0._51.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_51, i64 24
  store i32 168, ptr %_55.sroa.4.sroa.5.0._55.sroa.4.0._51.sroa_idx.sroa_idx, align 8
  %97 = getelementptr inbounds i8, ptr %_51, i64 80
  store i8 2, ptr %97, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_52)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %98 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_51) #26
  %_50.0 = extractvalue { i64, ptr } %98, 0
  %_50.1 = extractvalue { i64, ptr } %98, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_51)
  %99 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_50.0, ptr %99, align 8
  %100 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_50.1, ptr %100, align 8
  store i8 1, ptr %_0, align 8
  br label %bb90

bb90:                                             ; preds = %bb68, %bb73, %bb81, %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit57", %bb87, %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit50", %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit43", %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit29"
  call void @llvm.lifetime.end.p0(i64 25, ptr nonnull %target_tail)
  call void @llvm.lifetime.end.p0(i64 7, ptr nonnull %target_head)
  br label %bb91

bb59:                                             ; preds = %bb24
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(7) %target_head, ptr noundef nonnull align 1 dereferenceable(7) %holder_key, i64 7, i1 false)
  %_64 = getelementptr inbounds i8, ptr %holder_key, i64 7
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(25) %target_tail, ptr noundef nonnull align 1 dereferenceable(25) %_64, i64 25, i1 false)
  %switch20 = icmp eq i64 %1, 0
  br i1 %switch20, label %bb85, label %bb117

bb85:                                             ; preds = %bb60.thread, %bb59, %bb80
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(7) %b2, ptr noundef nonnull align 1 dereferenceable(7) %target_head, i64 7, i1 false)
  %_200 = getelementptr inbounds i8, ptr %b2, i64 7
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(25) %_200, ptr noundef nonnull align 1 dereferenceable(25) %target_tail, i64 25, i1 false)
  %101 = getelementptr inbounds i8, ptr %_0, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %101, ptr noundef nonnull align 1 dereferenceable(32) %b2, i64 32, i1 false)
  store i8 0, ptr %_0, align 8
  call void @llvm.lifetime.end.p0(i64 25, ptr nonnull %target_tail)
  call void @llvm.lifetime.end.p0(i64 7, ptr nonnull %target_head)
  br label %bb91

bb62:                                             ; preds = %bb46
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %t)
  %102 = getelementptr inbounds i8, ptr %st, i64 43
  %103 = load i8, ptr %102, align 1, !range !57, !noundef !2
  %.not17 = icmp eq i8 %103, 0
  br i1 %.not17, label %bb67, label %bb63

bb67:                                             ; preds = %bb62
  %104 = getelementptr inbounds i8, ptr %st, i64 42
  %105 = load i8, ptr %104, align 2, !range !57, !noundef !2
  %.not16 = icmp eq i8 %105, 0
  br i1 %.not16, label %bb69, label %bb68

bb63:                                             ; preds = %bb117, %bb62
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_150)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_151)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_151, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_e75cefee4bb91125af0ea8444b842ed0) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_152 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 91) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i51)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i53), !noalias !157
  store i64 0, ptr %buf.i53, align 8, !noalias !157
  %_9.sroa.4.0.buf.sroa_idx.i54 = getelementptr inbounds i8, ptr %buf.i53, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i54, align 8, !noalias !157
  %_9.sroa.5.0.buf.sroa_idx.i55 = getelementptr inbounds i8, ptr %buf.i53, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i55, align 8, !noalias !157
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i52), !noalias !157
  %106 = getelementptr inbounds i8, ptr %formatter.i52, i64 52
  store i32 0, ptr %106, align 4, !noalias !157
  %107 = getelementptr inbounds i8, ptr %formatter.i52, i64 48
  store i32 32, ptr %107, align 8, !noalias !157
  %108 = getelementptr inbounds i8, ptr %formatter.i52, i64 56
  store i8 3, ptr %108, align 8, !noalias !157
  store i64 0, ptr %formatter.i52, align 8, !noalias !157
  %109 = getelementptr inbounds i8, ptr %formatter.i52, i64 16
  store i64 0, ptr %109, align 8, !noalias !157
  %110 = getelementptr inbounds i8, ptr %formatter.i52, i64 32
  store ptr %buf.i53, ptr %110, align 8, !noalias !157
  %111 = getelementptr inbounds i8, ptr %formatter.i52, i64 40
  store ptr @vtable.0, ptr %111, align 8, !noalias !157
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %112 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_e75cefee4bb91125af0ea8444b842ed0, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i52) #26, !noalias !161
  br i1 %112, label %bb3.i56, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit57"

bb3.i56:                                          ; preds = %bb63
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i51, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !161
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit57": ; preds = %bb63
  %113 = getelementptr inbounds i8, ptr %_150, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %113, ptr noundef nonnull align 8 dereferenceable(24) %buf.i53, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i52), !noalias !157
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i53), !noalias !157
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i51)
  %114 = getelementptr inbounds i8, ptr %_150, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %114, ptr noundef nonnull align 8 dereferenceable(24) %_151, i64 24, i1 false)
  %115 = getelementptr inbounds i8, ptr %_150, i64 152
  store i32 %_152, ptr %115, align 8
  store i64 0, ptr %_150, align 8
  %_154.sroa.4.0._150.sroa_idx = getelementptr inbounds i8, ptr %_150, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_154.sroa.4.0._150.sroa_idx, align 8
  %_154.sroa.4.sroa.4.0._154.sroa.4.0._150.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_150, i64 16
  store i64 103, ptr %_154.sroa.4.sroa.4.0._154.sroa.4.0._150.sroa_idx.sroa_idx, align 8
  %_154.sroa.4.sroa.5.0._154.sroa.4.0._150.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_150, i64 24
  store i32 196, ptr %_154.sroa.4.sroa.5.0._154.sroa.4.0._150.sroa_idx.sroa_idx, align 8
  %116 = getelementptr inbounds i8, ptr %_150, i64 80
  store i8 2, ptr %116, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_151)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %117 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_150) #26
  %_149.0 = extractvalue { i64, ptr } %117, 0
  %_149.1 = extractvalue { i64, ptr } %117, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_150)
  %118 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_149.0, ptr %118, align 8
  %119 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_149.1, ptr %119, align 8
  store i8 1, ptr %_0, align 8
  br label %bb90

bb69:                                             ; preds = %bb117, %bb67
  %120 = load volatile i8, ptr %holder_key, align 1
  %121 = getelementptr inbounds i8, ptr %st, i64 45
  %122 = load i8, ptr %121, align 1, !range !57, !noundef !2
  %_171.not = icmp eq i8 %122, 0
  br i1 %_171.not, label %bb73, label %bb77

bb68:                                             ; preds = %bb67
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_160)
  %123 = getelementptr inbounds i8, ptr %_160, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %123, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_835bb996f1795bf0338da0490417da62) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_162 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 80) #26
  %124 = getelementptr inbounds i8, ptr %_160, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %124, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_835bb996f1795bf0338da0490417da62) #26
  %125 = getelementptr inbounds i8, ptr %_160, i64 152
  store i32 %_162, ptr %125, align 8
  store i64 0, ptr %_160, align 8
  %_164.sroa.4.0._160.sroa_idx = getelementptr inbounds i8, ptr %_160, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_164.sroa.4.0._160.sroa_idx, align 8
  %_164.sroa.4.sroa.4.0._164.sroa.4.0._160.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_160, i64 16
  store i64 103, ptr %_164.sroa.4.sroa.4.0._164.sroa.4.0._160.sroa_idx.sroa_idx, align 8
  %_164.sroa.4.sroa.5.0._164.sroa.4.0._160.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_160, i64 24
  store i32 200, ptr %_164.sroa.4.sroa.5.0._164.sroa.4.0._160.sroa_idx.sroa_idx, align 8
  %126 = getelementptr inbounds i8, ptr %_160, i64 80
  store i8 2, ptr %126, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %127 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_160) #26
  %_159.0 = extractvalue { i64, ptr } %127, 0
  %_159.1 = extractvalue { i64, ptr } %127, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_160)
  %128 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_159.0, ptr %128, align 8
  %129 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_159.1, ptr %129, align 8
  store i8 1, ptr %_0, align 8
  br label %bb90

bb117:                                            ; preds = %bb59
  %130 = getelementptr inbounds i8, ptr %st, i64 43
  %131 = load i8, ptr %130, align 1, !range !57, !noundef !2
  %.not18 = icmp eq i8 %131, 0
  br i1 %.not18, label %bb69, label %bb63

bb73:                                             ; preds = %bb69
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_173)
  %132 = getelementptr inbounds i8, ptr %_173, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %132, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_01eaaa187d2be542d4425f23ab284310) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_175 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 77) #26
  %133 = getelementptr inbounds i8, ptr %_173, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %133, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_01eaaa187d2be542d4425f23ab284310) #26
  %134 = getelementptr inbounds i8, ptr %_173, i64 152
  store i32 %_175, ptr %134, align 8
  store i64 0, ptr %_173, align 8
  %_177.sroa.4.0._173.sroa_idx = getelementptr inbounds i8, ptr %_173, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_177.sroa.4.0._173.sroa_idx, align 8
  %_177.sroa.4.sroa.4.0._177.sroa.4.0._173.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_173, i64 16
  store i64 103, ptr %_177.sroa.4.sroa.4.0._177.sroa.4.0._173.sroa_idx.sroa_idx, align 8
  %_177.sroa.4.sroa.5.0._177.sroa.4.0._173.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_173, i64 24
  store i32 204, ptr %_177.sroa.4.sroa.5.0._177.sroa.4.0._173.sroa_idx.sroa_idx, align 8
  %135 = getelementptr inbounds i8, ptr %_173, i64 80
  store i8 2, ptr %135, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %136 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_173) #26
  %_172.0 = extractvalue { i64, ptr } %136, 0
  %_172.1 = extractvalue { i64, ptr } %136, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_173)
  %137 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_172.0, ptr %137, align 8
  %138 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_172.1, ptr %138, align 8
  store i8 1, ptr %_0, align 8
  br label %bb90

bb77:                                             ; preds = %bb69
  %139 = getelementptr inbounds i8, ptr %st, i64 32
  %_182 = load i64, ptr %139, align 8
  %140 = freeze i64 %_182
  %141 = add i64 %2, -1
  %or.cond.not = icmp ult i64 %141, %140
  br i1 %or.cond.not, label %bb80, label %bb81

bb81:                                             ; preds = %bb77
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_184)
  %142 = getelementptr inbounds i8, ptr %_184, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %142, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_973adb9e8664e25d4750ddb14e0de56a) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_186 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 78) #26
  %143 = getelementptr inbounds i8, ptr %_184, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %143, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_973adb9e8664e25d4750ddb14e0de56a) #26
  %144 = getelementptr inbounds i8, ptr %_184, i64 152
  store i32 %_186, ptr %144, align 8
  store i64 0, ptr %_184, align 8
  %_188.sroa.4.0._184.sroa_idx = getelementptr inbounds i8, ptr %_184, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_188.sroa.4.0._184.sroa_idx, align 8
  %_188.sroa.4.sroa.4.0._188.sroa.4.0._184.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_184, i64 16
  store i64 103, ptr %_188.sroa.4.sroa.4.0._188.sroa.4.0._184.sroa_idx.sroa_idx, align 8
  %_188.sroa.4.sroa.5.0._188.sroa.4.0._184.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_184, i64 24
  store i32 208, ptr %_188.sroa.4.sroa.5.0._188.sroa.4.0._184.sroa_idx.sroa_idx, align 8
  %145 = getelementptr inbounds i8, ptr %_184, i64 80
  store i8 2, ptr %145, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %146 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_184) #26
  %_183.0 = extractvalue { i64, ptr } %146, 0
  %_183.1 = extractvalue { i64, ptr } %146, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_184)
  %147 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_183.0, ptr %147, align 8
  %148 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_183.1, ptr %148, align 8
  store i8 1, ptr %_0, align 8
  br label %bb90

bb80:                                             ; preds = %bb77
  %149 = load volatile i8, ptr %holder_key, align 1
  br label %bb85

bb91:                                             ; preds = %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit", %bb90, %bb85
  ret void
}

; Function Attrs: nounwind
define void @updated4149_validate(ptr dead_on_unwind noalias nocapture noundef writable writeonly sret([40 x i8]) align 8 dereferenceable(40) %_0, ptr noalias nocapture noundef readonly align 8 dereferenceable(48) %st, i8 noundef %0, i64 noundef %1, i64 %2, ptr noalias nocapture noundef readonly align 1 dereferenceable(33) %new, ptr noalias noundef readonly align 1 dereferenceable(32) %holder_key, ptr noalias nocapture noundef readonly align 1 dereferenceable(32) %sharing) unnamed_addr #1 {
start:
  %_11.i61 = alloca [0 x i8], align 1
  %formatter.i62 = alloca [64 x i8], align 8
  %buf.i63 = alloca [24 x i8], align 8
  %formatter.i55 = alloca [64 x i8], align 8
  %buf.i56 = alloca [24 x i8], align 8
  %formatter.i48 = alloca [64 x i8], align 8
  %buf.i49 = alloca [24 x i8], align 8
  %formatter.i41 = alloca [64 x i8], align 8
  %buf.i42 = alloca [24 x i8], align 8
  %formatter.i34 = alloca [64 x i8], align 8
  %buf.i35 = alloca [24 x i8], align 8
  %formatter.i = alloca [64 x i8], align 8
  %buf.i = alloca [24 x i8], align 8
  %b2 = alloca [32 x i8], align 1
  %_218 = alloca [160 x i8], align 8
  %_207 = alloca [160 x i8], align 8
  %_194 = alloca [160 x i8], align 8
  %_185 = alloca [24 x i8], align 8
  %_184 = alloca [160 x i8], align 8
  %b1 = alloca [32 x i8], align 1
  %_157 = alloca [160 x i8], align 8
  %_101 = alloca [64 x i8], align 8
  %_93 = alloca [160 x i8], align 8
  %_90 = alloca [32 x i8], align 1
  %_78 = alloca [24 x i8], align 8
  %_77 = alloca [160 x i8], align 8
  %t = alloca [32 x i8], align 1
  %_50 = alloca [24 x i8], align 8
  %_49 = alloca [160 x i8], align 8
  %_41 = alloca [24 x i8], align 8
  %_40 = alloca [160 x i8], align 8
  %_26 = alloca [24 x i8], align 8
  %_25 = alloca [160 x i8], align 8
  %target_tail = alloca [25 x i8], align 1
  %target_head = alloca [7 x i8], align 1
  %_10 = alloca [24 x i8], align 8
  %_9 = alloca [160 x i8], align 8
  %3 = getelementptr inbounds i8, ptr %st, i64 40
  %4 = load i8, ptr %3, align 8, !range !57, !noundef !2
  %_7.not = icmp eq i8 %4, 0
  br i1 %_7.not, label %bb5, label %bb1

bb5:                                              ; preds = %start
  %5 = and i8 %0, 1
  %extract.t.not = icmp eq i8 %5, 0
  call void @llvm.lifetime.start.p0(i64 7, ptr nonnull %target_head)
  call void @llvm.lifetime.start.p0(i64 25, ptr nonnull %target_tail)
  %6 = getelementptr inbounds i8, ptr %st, i64 41
  %7 = load i8, ptr %6, align 1, !range !57, !noundef !2
  %_21.not = icmp eq i8 %7, 0
  br i1 %_21.not, label %bb6, label %bb7

bb1:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_9)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_10)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_10, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_eb4f91695bc6f999067c65f428fcc4d8) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_11 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 88) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i61)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i), !noalias !162
  store i64 0, ptr %buf.i, align 8, !noalias !162
  %_9.sroa.4.0.buf.sroa_idx.i = getelementptr inbounds i8, ptr %buf.i, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i, align 8, !noalias !162
  %_9.sroa.5.0.buf.sroa_idx.i = getelementptr inbounds i8, ptr %buf.i, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i, align 8, !noalias !162
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i), !noalias !162
  %8 = getelementptr inbounds i8, ptr %formatter.i, i64 52
  store i32 0, ptr %8, align 4, !noalias !162
  %9 = getelementptr inbounds i8, ptr %formatter.i, i64 48
  store i32 32, ptr %9, align 8, !noalias !162
  %10 = getelementptr inbounds i8, ptr %formatter.i, i64 56
  store i8 3, ptr %10, align 8, !noalias !162
  store i64 0, ptr %formatter.i, align 8, !noalias !162
  %11 = getelementptr inbounds i8, ptr %formatter.i, i64 16
  store i64 0, ptr %11, align 8, !noalias !162
  %12 = getelementptr inbounds i8, ptr %formatter.i, i64 32
  store ptr %buf.i, ptr %12, align 8, !noalias !162
  %13 = getelementptr inbounds i8, ptr %formatter.i, i64 40
  store ptr @vtable.0, ptr %13, align 8, !noalias !162
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %14 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_eb4f91695bc6f999067c65f428fcc4d8, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i) #26, !noalias !166
  br i1 %14, label %bb3.i, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit"

bb3.i:                                            ; preds = %bb1
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i61, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !166
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit": ; preds = %bb1
  %15 = getelementptr inbounds i8, ptr %_9, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %15, ptr noundef nonnull align 8 dereferenceable(24) %buf.i, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i), !noalias !162
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i), !noalias !162
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i61)
  %16 = getelementptr inbounds i8, ptr %_9, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %16, ptr noundef nonnull align 8 dereferenceable(24) %_10, i64 24, i1 false)
  %17 = getelementptr inbounds i8, ptr %_9, i64 152
  store i32 %_11, ptr %17, align 8
  store i64 0, ptr %_9, align 8
  %_13.sroa.4.0._9.sroa_idx = getelementptr inbounds i8, ptr %_9, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_13.sroa.4.0._9.sroa_idx, align 8
  %_13.sroa.4.sroa.4.0._13.sroa.4.0._9.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_9, i64 16
  store i64 103, ptr %_13.sroa.4.sroa.4.0._13.sroa.4.0._9.sroa_idx.sroa_idx, align 8
  %_13.sroa.4.sroa.5.0._13.sroa.4.0._9.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_9, i64 24
  store i32 212, ptr %_13.sroa.4.sroa.5.0._13.sroa.4.0._9.sroa_idx.sroa_idx, align 8
  %18 = getelementptr inbounds i8, ptr %_9, i64 80
  store i8 2, ptr %18, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_10)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %19 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_9) #26
  %_8.0 = extractvalue { i64, ptr } %19, 0
  %_8.1 = extractvalue { i64, ptr } %19, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_9)
  %20 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_8.0, ptr %20, align 8
  %21 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_8.1, ptr %21, align 8
  store i8 1, ptr %_0, align 8
  br label %bb84

bb7:                                              ; preds = %bb5
  br i1 %extract.t.not, label %bb9, label %bb22, !prof !75

bb6:                                              ; preds = %bb5
  br i1 %extract.t.not, label %bb21, label %bb15, !prof !63

bb9:                                              ; preds = %bb7
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_25)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_26)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_26, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_8f95cb73e89711d65e95d13598508b19) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_27 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 83) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i61)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i35), !noalias !167
  store i64 0, ptr %buf.i35, align 8, !noalias !167
  %_9.sroa.4.0.buf.sroa_idx.i36 = getelementptr inbounds i8, ptr %buf.i35, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i36, align 8, !noalias !167
  %_9.sroa.5.0.buf.sroa_idx.i37 = getelementptr inbounds i8, ptr %buf.i35, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i37, align 8, !noalias !167
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i34), !noalias !167
  %22 = getelementptr inbounds i8, ptr %formatter.i34, i64 52
  store i32 0, ptr %22, align 4, !noalias !167
  %23 = getelementptr inbounds i8, ptr %formatter.i34, i64 48
  store i32 32, ptr %23, align 8, !noalias !167
  %24 = getelementptr inbounds i8, ptr %formatter.i34, i64 56
  store i8 3, ptr %24, align 8, !noalias !167
  store i64 0, ptr %formatter.i34, align 8, !noalias !167
  %25 = getelementptr inbounds i8, ptr %formatter.i34, i64 16
  store i64 0, ptr %25, align 8, !noalias !167
  %26 = getelementptr inbounds i8, ptr %formatter.i34, i64 32
  store ptr %buf.i35, ptr %26, align 8, !noalias !167
  %27 = getelementptr inbounds i8, ptr %formatter.i34, i64 40
  store ptr @vtable.0, ptr %27, align 8, !noalias !167
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %28 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_8f95cb73e89711d65e95d13598508b19, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i34) #26, !noalias !171
  br i1 %28, label %bb3.i38, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit39"

bb3.i38:                                          ; preds = %bb9
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i61, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !171
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit39": ; preds = %bb9
  %29 = getelementptr inbounds i8, ptr %_25, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %29, ptr noundef nonnull align 8 dereferenceable(24) %buf.i35, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i34), !noalias !167
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i35), !noalias !167
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i61)
  %30 = getelementptr inbounds i8, ptr %_25, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %30, ptr noundef nonnull align 8 dereferenceable(24) %_26, i64 24, i1 false)
  %31 = getelementptr inbounds i8, ptr %_25, i64 152
  store i32 %_27, ptr %31, align 8
  store i64 0, ptr %_25, align 8
  %_29.sroa.4.0._25.sroa_idx = getelementptr inbounds i8, ptr %_25, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_29.sroa.4.0._25.sroa_idx, align 8
  %_29.sroa.4.sroa.4.0._29.sroa.4.0._25.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_25, i64 16
  store i64 103, ptr %_29.sroa.4.sroa.4.0._29.sroa.4.0._25.sroa_idx.sroa_idx, align 8
  %_29.sroa.4.sroa.5.0._29.sroa.4.0._25.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_25, i64 24
  store i32 217, ptr %_29.sroa.4.sroa.5.0._29.sroa.4.0._25.sroa_idx.sroa_idx, align 8
  %32 = getelementptr inbounds i8, ptr %_25, i64 80
  store i8 2, ptr %32, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_26)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %33 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_25) #26
  %e.0 = extractvalue { i64, ptr } %33, 0
  %e.1 = extractvalue { i64, ptr } %33, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_25)
  %34 = load volatile i8, ptr %holder_key, align 1
  %35 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %e.0, ptr %35, align 8
  %36 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %e.1, ptr %36, align 8
  store i8 1, ptr %_0, align 8
  br label %bb83

bb22:                                             ; preds = %bb15, %bb7
  %37 = load i8, ptr %new, align 1, !range !57, !noundef !2
  %trunc.not.not = icmp eq i8 %37, 0
  br i1 %trunc.not.not, label %bb52, label %bb93

bb21:                                             ; preds = %bb6
  call void @llvm.lifetime.end.p0(i64 7, ptr nonnull %target_head)
  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %t)
  %_70 = load i8, ptr %new, align 1, !noundef !2
  %_69 = and i8 %_70, 1
  %_68 = icmp eq i8 %_69, 0
  br i1 %_68, label %bb28, label %bb32, !prof !69

bb15:                                             ; preds = %bb6
  %38 = getelementptr inbounds i8, ptr %st, i64 44
  %39 = load i8, ptr %38, align 4, !range !57, !noundef !2
  %_38.not = icmp eq i8 %39, 0
  br i1 %_38.not, label %bb16, label %bb22

bb32:                                             ; preds = %bb21
  %_86 = getelementptr inbounds i8, ptr %new, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %t, ptr noundef nonnull align 1 dereferenceable(32) %_86, i64 32, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %_90)
  call void @llvm.memset.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %_90, i8 0, i64 32, i1 false)
  %40 = call i32 @memcmp(ptr noundef nonnull dereferenceable(32) %t, ptr noundef nonnull dereferenceable(32) %_90, i64 32)
  %41 = icmp eq i32 %40, 0
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %_90)
  br i1 %41, label %bb34, label %bb39

bb28:                                             ; preds = %bb21
  %42 = load volatile i8, ptr %holder_key, align 1
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_77)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_78)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_78, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_1ba5e1e397ae92b788c97e688ac0b362) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_79 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 89) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i61)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i42), !noalias !172
  store i64 0, ptr %buf.i42, align 8, !noalias !172
  %_9.sroa.4.0.buf.sroa_idx.i43 = getelementptr inbounds i8, ptr %buf.i42, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i43, align 8, !noalias !172
  %_9.sroa.5.0.buf.sroa_idx.i44 = getelementptr inbounds i8, ptr %buf.i42, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i44, align 8, !noalias !172
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i41), !noalias !172
  %43 = getelementptr inbounds i8, ptr %formatter.i41, i64 52
  store i32 0, ptr %43, align 4, !noalias !172
  %44 = getelementptr inbounds i8, ptr %formatter.i41, i64 48
  store i32 32, ptr %44, align 8, !noalias !172
  %45 = getelementptr inbounds i8, ptr %formatter.i41, i64 56
  store i8 3, ptr %45, align 8, !noalias !172
  store i64 0, ptr %formatter.i41, align 8, !noalias !172
  %46 = getelementptr inbounds i8, ptr %formatter.i41, i64 16
  store i64 0, ptr %46, align 8, !noalias !172
  %47 = getelementptr inbounds i8, ptr %formatter.i41, i64 32
  store ptr %buf.i42, ptr %47, align 8, !noalias !172
  %48 = getelementptr inbounds i8, ptr %formatter.i41, i64 40
  store ptr @vtable.0, ptr %48, align 8, !noalias !172
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %49 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_1ba5e1e397ae92b788c97e688ac0b362, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i41) #26, !noalias !176
  br i1 %49, label %bb3.i45, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit46"

bb3.i45:                                          ; preds = %bb28
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i61, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !176
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit46": ; preds = %bb28
  %50 = getelementptr inbounds i8, ptr %_77, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %50, ptr noundef nonnull align 8 dereferenceable(24) %buf.i42, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i41), !noalias !172
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i42), !noalias !172
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i61)
  %51 = getelementptr inbounds i8, ptr %_77, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %51, ptr noundef nonnull align 8 dereferenceable(24) %_78, i64 24, i1 false)
  %52 = getelementptr inbounds i8, ptr %_77, i64 152
  store i32 %_79, ptr %52, align 8
  store i64 0, ptr %_77, align 8
  %_81.sroa.4.0._77.sroa_idx = getelementptr inbounds i8, ptr %_77, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_81.sroa.4.0._77.sroa_idx, align 8
  %_81.sroa.4.sroa.4.0._81.sroa.4.0._77.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_77, i64 16
  store i64 103, ptr %_81.sroa.4.sroa.4.0._81.sroa.4.0._77.sroa_idx.sroa_idx, align 8
  %_81.sroa.4.sroa.5.0._81.sroa.4.0._77.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_77, i64 24
  store i32 234, ptr %_81.sroa.4.sroa.5.0._81.sroa.4.0._77.sroa_idx.sroa_idx, align 8
  %53 = getelementptr inbounds i8, ptr %_77, i64 80
  store i8 2, ptr %53, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_78)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %54 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_77) #26
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_77)
  br label %bb80

bb39:                                             ; preds = %bb32
  %55 = call i32 @memcmp(ptr noundef nonnull dereferenceable(32) %t, ptr noundef nonnull dereferenceable(32) %sharing, i64 32)
  %56 = icmp eq i32 %55, 0
  %57 = zext i1 %56 to i8
  %_118 = tail call noundef zeroext i8 @llvm.bpf.passthrough.i8.i8(i32 noundef zeroext 4, i8 noundef zeroext %57) #26
  %_117 = and i8 %_118, 1
  %_116.not = icmp eq i8 %_117, 0
  br i1 %_116.not, label %bb42, label %bb44, !prof !75

bb34:                                             ; preds = %bb32
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_93)
  %58 = getelementptr inbounds i8, ptr %_93, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %58, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_0e3505805f4905816c1bd644811a7869) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_95 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 30) #26
  %59 = getelementptr inbounds i8, ptr %_93, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %59, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_0e3505805f4905816c1bd644811a7869) #26
  %60 = getelementptr inbounds i8, ptr %_93, i64 152
  store i32 %_95, ptr %60, align 8
  store i64 0, ptr %_93, align 8
  %_97.sroa.4.0._93.sroa_idx = getelementptr inbounds i8, ptr %_93, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_97.sroa.4.0._93.sroa_idx, align 8
  %_97.sroa.4.sroa.4.0._97.sroa.4.0._93.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_93, i64 16
  store i64 103, ptr %_97.sroa.4.sroa.4.0._97.sroa.4.0._93.sroa_idx.sroa_idx, align 8
  %_97.sroa.4.sroa.5.0._97.sroa.4.0._93.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_93, i64 24
  store i32 235, ptr %_97.sroa.4.sroa.5.0._97.sroa.4.0._93.sroa_idx.sroa_idx, align 8
  %61 = getelementptr inbounds i8, ptr %_93, i64 80
  store i8 2, ptr %61, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %62 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_93) #26
  %_92.0 = extractvalue { i64, ptr } %62, 0
  %_92.1 = extractvalue { i64, ptr } %62, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_93)
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %_101)
  %_104 = getelementptr inbounds i8, ptr %t, i64 8
  %_265.sroa.2.0._101.sroa_idx = getelementptr inbounds i8, ptr %_101, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %_265.sroa.2.0._101.sroa_idx, ptr noundef nonnull align 1 dereferenceable(24) %_104, i64 24, i1 false)
  %_86.val = load i64, ptr %_86, align 1
  %63 = getelementptr inbounds i8, ptr %_101, i64 32
  call void @llvm.memset.p0.i64(ptr noundef nonnull align 8 dereferenceable(32) %63, i8 0, i64 32, i1 false)
  store i64 %_86.val, ptr %_101, align 8
; call anchor_lang::error::Error::with_pubkeys
  %64 = call { i64, ptr } @_ZN11anchor_lang5error5Error12with_pubkeys17hca6dbbbe6a9a5da7E(i64 noundef %_92.0, ptr noundef %_92.1, ptr noalias nocapture noundef nonnull readonly align 1 dereferenceable(64) %_101) #26
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %_101)
  br label %bb80

bb42:                                             ; preds = %bb39
  %65 = call i32 @memcmp(ptr noundef nonnull dereferenceable(32) %t, ptr noundef nonnull dereferenceable(32) %holder_key, i64 32)
  %66 = icmp eq i32 %65, 0
  br i1 %66, label %bb44, label %bb53, !prof !76

bb44:                                             ; preds = %bb42, %bb39
  %67 = load volatile i8, ptr %holder_key, align 1
  %68 = load volatile i8, ptr %holder_key, align 1
  %69 = load volatile i8, ptr %holder_key, align 1
  %70 = load volatile i8, ptr %holder_key, align 1
  %71 = load volatile i8, ptr %holder_key, align 1
  %72 = load volatile i8, ptr %holder_key, align 1
  %73 = load volatile i8, ptr %holder_key, align 1
  %74 = load volatile i8, ptr %holder_key, align 1
  %75 = load volatile i8, ptr %holder_key, align 1
  %76 = load volatile i8, ptr %holder_key, align 1
  %77 = load volatile i8, ptr %holder_key, align 1
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_157)
  %78 = getelementptr inbounds i8, ptr %_157, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %78, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_861c8964bbad6d9cede9df277e628fe9) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_159 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 19) #26
  %79 = getelementptr inbounds i8, ptr %_157, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %79, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_861c8964bbad6d9cede9df277e628fe9) #26
  %80 = getelementptr inbounds i8, ptr %_157, i64 152
  store i32 %_159, ptr %80, align 8
  store i64 0, ptr %_157, align 8
  %_161.sroa.4.0._157.sroa_idx = getelementptr inbounds i8, ptr %_157, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_161.sroa.4.0._157.sroa_idx, align 8
  %_161.sroa.4.sroa.4.0._161.sroa.4.0._157.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_157, i64 16
  store i64 103, ptr %_161.sroa.4.sroa.4.0._161.sroa.4.0._157.sroa_idx.sroa_idx, align 8
  %_161.sroa.4.sroa.5.0._161.sroa.4.0._157.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_157, i64 24
  store i32 240, ptr %_161.sroa.4.sroa.5.0._161.sroa.4.0._157.sroa_idx.sroa_idx, align 8
  %81 = getelementptr inbounds i8, ptr %_157, i64 80
  store i8 2, ptr %81, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %82 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_157) #26
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_157)
  br label %bb80

bb80:                                             ; preds = %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit46", %bb34, %bb44
  %.pn = phi { i64, ptr } [ %54, %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit46" ], [ %64, %bb34 ], [ %82, %bb44 ]
  %_76.1.sink = extractvalue { i64, ptr } %.pn, 1
  %_76.0.sink = extractvalue { i64, ptr } %.pn, 0
  %83 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_76.0.sink, ptr %83, align 8
  %84 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_76.1.sink, ptr %84, align 8
  store i8 1, ptr %_0, align 8
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %t)
  br label %bb83

bb16:                                             ; preds = %bb15
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_40)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_41)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_41, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_f94f166953c814e4161e699857179a1e) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_42 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 84) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i61)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i49), !noalias !177
  store i64 0, ptr %buf.i49, align 8, !noalias !177
  %_9.sroa.4.0.buf.sroa_idx.i50 = getelementptr inbounds i8, ptr %buf.i49, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i50, align 8, !noalias !177
  %_9.sroa.5.0.buf.sroa_idx.i51 = getelementptr inbounds i8, ptr %buf.i49, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i51, align 8, !noalias !177
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i48), !noalias !177
  %85 = getelementptr inbounds i8, ptr %formatter.i48, i64 52
  store i32 0, ptr %85, align 4, !noalias !177
  %86 = getelementptr inbounds i8, ptr %formatter.i48, i64 48
  store i32 32, ptr %86, align 8, !noalias !177
  %87 = getelementptr inbounds i8, ptr %formatter.i48, i64 56
  store i8 3, ptr %87, align 8, !noalias !177
  store i64 0, ptr %formatter.i48, align 8, !noalias !177
  %88 = getelementptr inbounds i8, ptr %formatter.i48, i64 16
  store i64 0, ptr %88, align 8, !noalias !177
  %89 = getelementptr inbounds i8, ptr %formatter.i48, i64 32
  store ptr %buf.i49, ptr %89, align 8, !noalias !177
  %90 = getelementptr inbounds i8, ptr %formatter.i48, i64 40
  store ptr @vtable.0, ptr %90, align 8, !noalias !177
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %91 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_f94f166953c814e4161e699857179a1e, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i48) #26, !noalias !181
  br i1 %91, label %bb3.i52, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit53"

bb3.i52:                                          ; preds = %bb16
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i61, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !181
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit53": ; preds = %bb16
  %92 = getelementptr inbounds i8, ptr %_40, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %92, ptr noundef nonnull align 8 dereferenceable(24) %buf.i49, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i48), !noalias !177
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i49), !noalias !177
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i61)
  %93 = getelementptr inbounds i8, ptr %_40, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %93, ptr noundef nonnull align 8 dereferenceable(24) %_41, i64 24, i1 false)
  %94 = getelementptr inbounds i8, ptr %_40, i64 152
  store i32 %_42, ptr %94, align 8
  store i64 0, ptr %_40, align 8
  %_44.sroa.4.0._40.sroa_idx = getelementptr inbounds i8, ptr %_40, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_44.sroa.4.0._40.sroa_idx, align 8
  %_44.sroa.4.sroa.4.0._44.sroa.4.0._40.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_40, i64 16
  store i64 103, ptr %_44.sroa.4.sroa.4.0._44.sroa.4.0._40.sroa_idx.sroa_idx, align 8
  %_44.sroa.4.sroa.5.0._44.sroa.4.0._40.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_40, i64 24
  store i32 224, ptr %_44.sroa.4.sroa.5.0._44.sroa.4.0._40.sroa_idx.sroa_idx, align 8
  %95 = getelementptr inbounds i8, ptr %_40, i64 80
  store i8 2, ptr %95, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_41)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %96 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_40) #26
  %_39.0 = extractvalue { i64, ptr } %96, 0
  %_39.1 = extractvalue { i64, ptr } %96, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_40)
  %97 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_39.0, ptr %97, align 8
  %98 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_39.1, ptr %98, align 8
  store i8 1, ptr %_0, align 8
  br label %bb83

bb93:                                             ; preds = %bb22
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_49)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_50)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_50, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_b5f839a6bda937f2cae73e49fc88071f) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_51 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 90) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i61)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i56), !noalias !182
  store i64 0, ptr %buf.i56, align 8, !noalias !182
  %_9.sroa.4.0.buf.sroa_idx.i57 = getelementptr inbounds i8, ptr %buf.i56, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i57, align 8, !noalias !182
  %_9.sroa.5.0.buf.sroa_idx.i58 = getelementptr inbounds i8, ptr %buf.i56, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i58, align 8, !noalias !182
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i55), !noalias !182
  %99 = getelementptr inbounds i8, ptr %formatter.i55, i64 52
  store i32 0, ptr %99, align 4, !noalias !182
  %100 = getelementptr inbounds i8, ptr %formatter.i55, i64 48
  store i32 32, ptr %100, align 8, !noalias !182
  %101 = getelementptr inbounds i8, ptr %formatter.i55, i64 56
  store i8 3, ptr %101, align 8, !noalias !182
  store i64 0, ptr %formatter.i55, align 8, !noalias !182
  %102 = getelementptr inbounds i8, ptr %formatter.i55, i64 16
  store i64 0, ptr %102, align 8, !noalias !182
  %103 = getelementptr inbounds i8, ptr %formatter.i55, i64 32
  store ptr %buf.i56, ptr %103, align 8, !noalias !182
  %104 = getelementptr inbounds i8, ptr %formatter.i55, i64 40
  store ptr @vtable.0, ptr %104, align 8, !noalias !182
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %105 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_b5f839a6bda937f2cae73e49fc88071f, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i55) #26, !noalias !186
  br i1 %105, label %bb3.i59, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit60"

bb3.i59:                                          ; preds = %bb93
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i61, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !186
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit60": ; preds = %bb93
  %106 = getelementptr inbounds i8, ptr %_49, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %106, ptr noundef nonnull align 8 dereferenceable(24) %buf.i56, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i55), !noalias !182
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i56), !noalias !182
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i61)
  %107 = getelementptr inbounds i8, ptr %_49, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %107, ptr noundef nonnull align 8 dereferenceable(24) %_50, i64 24, i1 false)
  %108 = getelementptr inbounds i8, ptr %_49, i64 152
  store i32 %_51, ptr %108, align 8
  store i64 0, ptr %_49, align 8
  %_53.sroa.4.0._49.sroa_idx = getelementptr inbounds i8, ptr %_49, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_53.sroa.4.0._49.sroa_idx, align 8
  %_53.sroa.4.sroa.4.0._53.sroa.4.0._49.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_49, i64 16
  store i64 103, ptr %_53.sroa.4.sroa.4.0._53.sroa.4.0._49.sroa_idx.sroa_idx, align 8
  %_53.sroa.4.sroa.5.0._53.sroa.4.0._49.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_49, i64 24
  store i32 226, ptr %_53.sroa.4.sroa.5.0._53.sroa.4.0._49.sroa_idx.sroa_idx, align 8
  %109 = getelementptr inbounds i8, ptr %_49, i64 80
  store i8 2, ptr %109, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_50)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %110 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_49) #26
  %_48.0 = extractvalue { i64, ptr } %110, 0
  %_48.1 = extractvalue { i64, ptr } %110, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_49)
  %111 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_48.0, ptr %111, align 8
  %112 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_48.1, ptr %112, align 8
  store i8 1, ptr %_0, align 8
  br label %bb83

bb83:                                             ; preds = %bb61, %bb66, %bb74, %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit67", %bb80, %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit60", %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit53", %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit39"
  call void @llvm.lifetime.end.p0(i64 25, ptr nonnull %target_tail)
  call void @llvm.lifetime.end.p0(i64 7, ptr nonnull %target_head)
  br label %bb84

bb53:                                             ; preds = %bb42
  call void @llvm.lifetime.start.p0(i64 7, ptr nonnull %target_head)
  call void @llvm.lifetime.start.p0(i64 25, ptr nonnull %target_tail)
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(7) %target_head, ptr noundef nonnull align 1 dereferenceable(7) %_86, i64 7, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %b1)
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %b1, ptr noundef nonnull align 1 dereferenceable(32) %_86, i64 32, i1 false)
  %_173 = getelementptr inbounds i8, ptr %b1, i64 7
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(25) %target_tail, ptr noundef nonnull align 1 dereferenceable(25) %_173, i64 25, i1 false)
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %b1)
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %t)
  %113 = getelementptr inbounds i8, ptr %st, i64 42
  %114 = load i8, ptr %113, align 2, !range !57, !noundef !2
  %.not = icmp eq i8 %114, 0
  %switch31 = icmp eq i64 %1, 0
  br i1 %switch31, label %bb78, label %bb55

bb52:                                             ; preds = %bb22
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(7) %target_head, ptr noundef nonnull align 1 dereferenceable(7) %holder_key, i64 7, i1 false)
  %_62 = getelementptr inbounds i8, ptr %holder_key, i64 7
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(25) %target_tail, ptr noundef nonnull align 1 dereferenceable(25) %_62, i64 25, i1 false)
  %switch32 = icmp eq i64 %1, 0
  br i1 %switch32, label %bb78, label %bb122

bb78:                                             ; preds = %bb52, %bb53, %bb73
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(7) %b2, ptr noundef nonnull align 1 dereferenceable(7) %target_head, i64 7, i1 false)
  %_234 = getelementptr inbounds i8, ptr %b2, i64 7
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(25) %_234, ptr noundef nonnull align 1 dereferenceable(25) %target_tail, i64 25, i1 false)
  %115 = getelementptr inbounds i8, ptr %_0, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %115, ptr noundef nonnull align 1 dereferenceable(32) %b2, i64 32, i1 false)
  store i8 0, ptr %_0, align 8
  call void @llvm.lifetime.end.p0(i64 25, ptr nonnull %target_tail)
  call void @llvm.lifetime.end.p0(i64 7, ptr nonnull %target_head)
  br label %bb84

bb55:                                             ; preds = %bb53
  %116 = getelementptr inbounds i8, ptr %st, i64 43
  %117 = load i8, ptr %116, align 1, !range !57, !noundef !2
  %.not29 = icmp eq i8 %117, 0
  br i1 %.not29, label %bb60, label %bb56

bb60:                                             ; preds = %bb55
  br i1 %.not, label %bb62, label %bb61

bb56:                                             ; preds = %bb122, %bb55
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_184)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_185)
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_185, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_e75cefee4bb91125af0ea8444b842ed0) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_186 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 91) #26
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i61)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i63), !noalias !187
  store i64 0, ptr %buf.i63, align 8, !noalias !187
  %_9.sroa.4.0.buf.sroa_idx.i64 = getelementptr inbounds i8, ptr %buf.i63, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i64, align 8, !noalias !187
  %_9.sroa.5.0.buf.sroa_idx.i65 = getelementptr inbounds i8, ptr %buf.i63, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i65, align 8, !noalias !187
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i62), !noalias !187
  %118 = getelementptr inbounds i8, ptr %formatter.i62, i64 52
  store i32 0, ptr %118, align 4, !noalias !187
  %119 = getelementptr inbounds i8, ptr %formatter.i62, i64 48
  store i32 32, ptr %119, align 8, !noalias !187
  %120 = getelementptr inbounds i8, ptr %formatter.i62, i64 56
  store i8 3, ptr %120, align 8, !noalias !187
  store i64 0, ptr %formatter.i62, align 8, !noalias !187
  %121 = getelementptr inbounds i8, ptr %formatter.i62, i64 16
  store i64 0, ptr %121, align 8, !noalias !187
  %122 = getelementptr inbounds i8, ptr %formatter.i62, i64 32
  store ptr %buf.i63, ptr %122, align 8, !noalias !187
  %123 = getelementptr inbounds i8, ptr %formatter.i62, i64 40
  store ptr @vtable.0, ptr %123, align 8, !noalias !187
; call <pump_recovered::PumpError as core::fmt::Display>::fmt
  %124 = call noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_e75cefee4bb91125af0ea8444b842ed0, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i62) #26, !noalias !191
  br i1 %124, label %bb3.i66, label %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit67"

bb3.i66:                                          ; preds = %bb56
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i61, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.1, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #27, !noalias !191
  unreachable

"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit67": ; preds = %bb56
  %125 = getelementptr inbounds i8, ptr %_184, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %125, ptr noundef nonnull align 8 dereferenceable(24) %buf.i63, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i62), !noalias !187
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i63), !noalias !187
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i61)
  %126 = getelementptr inbounds i8, ptr %_184, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %126, ptr noundef nonnull align 8 dereferenceable(24) %_185, i64 24, i1 false)
  %127 = getelementptr inbounds i8, ptr %_184, i64 152
  store i32 %_186, ptr %127, align 8
  store i64 0, ptr %_184, align 8
  %_188.sroa.4.0._184.sroa_idx = getelementptr inbounds i8, ptr %_184, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_188.sroa.4.0._184.sroa_idx, align 8
  %_188.sroa.4.sroa.4.0._188.sroa.4.0._184.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_184, i64 16
  store i64 103, ptr %_188.sroa.4.sroa.4.0._188.sroa.4.0._184.sroa_idx.sroa_idx, align 8
  %_188.sroa.4.sroa.5.0._188.sroa.4.0._184.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_184, i64 24
  store i32 254, ptr %_188.sroa.4.sroa.5.0._188.sroa.4.0._184.sroa_idx.sroa_idx, align 8
  %128 = getelementptr inbounds i8, ptr %_184, i64 80
  store i8 2, ptr %128, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_185)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %129 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_184) #26
  %_183.0 = extractvalue { i64, ptr } %129, 0
  %_183.1 = extractvalue { i64, ptr } %129, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_184)
  %130 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_183.0, ptr %130, align 8
  %131 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_183.1, ptr %131, align 8
  store i8 1, ptr %_0, align 8
  br label %bb83

bb62:                                             ; preds = %bb122, %bb60
  %132 = load volatile i8, ptr %holder_key, align 1
  %133 = getelementptr inbounds i8, ptr %st, i64 45
  %134 = load i8, ptr %133, align 1, !range !57, !noundef !2
  %_205.not = icmp eq i8 %134, 0
  br i1 %_205.not, label %bb66, label %bb70

bb61:                                             ; preds = %bb60
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_194)
  %135 = getelementptr inbounds i8, ptr %_194, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %135, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_835bb996f1795bf0338da0490417da62) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_196 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 80) #26
  %136 = getelementptr inbounds i8, ptr %_194, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %136, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_835bb996f1795bf0338da0490417da62) #26
  %137 = getelementptr inbounds i8, ptr %_194, i64 152
  store i32 %_196, ptr %137, align 8
  store i64 0, ptr %_194, align 8
  %_198.sroa.4.0._194.sroa_idx = getelementptr inbounds i8, ptr %_194, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_198.sroa.4.0._194.sroa_idx, align 8
  %_198.sroa.4.sroa.4.0._198.sroa.4.0._194.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_194, i64 16
  store i64 103, ptr %_198.sroa.4.sroa.4.0._198.sroa.4.0._194.sroa_idx.sroa_idx, align 8
  %_198.sroa.4.sroa.5.0._198.sroa.4.0._194.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_194, i64 24
  store i32 258, ptr %_198.sroa.4.sroa.5.0._198.sroa.4.0._194.sroa_idx.sroa_idx, align 8
  %138 = getelementptr inbounds i8, ptr %_194, i64 80
  store i8 2, ptr %138, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %139 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_194) #26
  %_193.0 = extractvalue { i64, ptr } %139, 0
  %_193.1 = extractvalue { i64, ptr } %139, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_194)
  %140 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_193.0, ptr %140, align 8
  %141 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_193.1, ptr %141, align 8
  store i8 1, ptr %_0, align 8
  br label %bb83

bb122:                                            ; preds = %bb52
  %142 = getelementptr inbounds i8, ptr %st, i64 43
  %143 = load i8, ptr %142, align 1, !range !57, !noundef !2
  %.not30 = icmp eq i8 %143, 0
  br i1 %.not30, label %bb62, label %bb56

bb66:                                             ; preds = %bb62
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_207)
  %144 = getelementptr inbounds i8, ptr %_207, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %144, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_01eaaa187d2be542d4425f23ab284310) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_209 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 77) #26
  %145 = getelementptr inbounds i8, ptr %_207, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %145, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_01eaaa187d2be542d4425f23ab284310) #26
  %146 = getelementptr inbounds i8, ptr %_207, i64 152
  store i32 %_209, ptr %146, align 8
  store i64 0, ptr %_207, align 8
  %_211.sroa.4.0._207.sroa_idx = getelementptr inbounds i8, ptr %_207, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_211.sroa.4.0._207.sroa_idx, align 8
  %_211.sroa.4.sroa.4.0._211.sroa.4.0._207.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_207, i64 16
  store i64 103, ptr %_211.sroa.4.sroa.4.0._211.sroa.4.0._207.sroa_idx.sroa_idx, align 8
  %_211.sroa.4.sroa.5.0._211.sroa.4.0._207.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_207, i64 24
  store i32 262, ptr %_211.sroa.4.sroa.5.0._211.sroa.4.0._207.sroa_idx.sroa_idx, align 8
  %147 = getelementptr inbounds i8, ptr %_207, i64 80
  store i8 2, ptr %147, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %148 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_207) #26
  %_206.0 = extractvalue { i64, ptr } %148, 0
  %_206.1 = extractvalue { i64, ptr } %148, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_207)
  %149 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_206.0, ptr %149, align 8
  %150 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_206.1, ptr %150, align 8
  store i8 1, ptr %_0, align 8
  br label %bb83

bb70:                                             ; preds = %bb62
  %151 = getelementptr inbounds i8, ptr %st, i64 32
  %_216 = load i64, ptr %151, align 8
  %152 = freeze i64 %_216
  %153 = add i64 %2, -1
  %or.cond.not = icmp ult i64 %153, %152
  br i1 %or.cond.not, label %bb73, label %bb74

bb74:                                             ; preds = %bb70
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_218)
  %154 = getelementptr inbounds i8, ptr %_218, i64 32
; call pump_recovered::PumpError::name
  call void @_ZN14pump_recovered9PumpError4name17h61022c7ff53288d0E(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %154, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_973adb9e8664e25d4750ddb14e0de56a) #26
; call pump_recovered::<impl core::convert::From<pump_recovered::PumpError> for u32>::from
  %_220 = tail call noundef i32 @"_ZN14pump_recovered86_$LT$impl$u20$core..convert..From$LT$pump_recovered..PumpError$GT$$u20$for$u20$u32$GT$4from17h5efe8549893543d7E"(i32 noundef 78) #26
  %155 = getelementptr inbounds i8, ptr %_218, i64 56
; call <T as alloc::string::ToString>::to_string
  call fastcc void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"(ptr noalias nocapture noundef nonnull align 8 dereferenceable(24) %155, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_973adb9e8664e25d4750ddb14e0de56a) #26
  %156 = getelementptr inbounds i8, ptr %_218, i64 152
  store i32 %_220, ptr %156, align 8
  store i64 0, ptr %_218, align 8
  %_222.sroa.4.0._218.sroa_idx = getelementptr inbounds i8, ptr %_218, i64 8
  store ptr @alloc_a6d06679426228b5e58f8de7567c2075, ptr %_222.sroa.4.0._218.sroa_idx, align 8
  %_222.sroa.4.sroa.4.0._222.sroa.4.0._218.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_218, i64 16
  store i64 103, ptr %_222.sroa.4.sroa.4.0._222.sroa.4.0._218.sroa_idx.sroa_idx, align 8
  %_222.sroa.4.sroa.5.0._222.sroa.4.0._218.sroa_idx.sroa_idx = getelementptr inbounds i8, ptr %_218, i64 24
  store i32 266, ptr %_222.sroa.4.sroa.5.0._222.sroa.4.0._218.sroa_idx.sroa_idx, align 8
  %157 = getelementptr inbounds i8, ptr %_218, i64 80
  store i8 2, ptr %157, align 8
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %158 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17h4ec711440ff80a00E"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_218) #26
  %_217.0 = extractvalue { i64, ptr } %158, 0
  %_217.1 = extractvalue { i64, ptr } %158, 1
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_218)
  %159 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %_217.0, ptr %159, align 8
  %160 = getelementptr inbounds i8, ptr %_0, i64 16
  store ptr %_217.1, ptr %160, align 8
  store i8 1, ptr %_0, align 8
  br label %bb83

bb73:                                             ; preds = %bb70
  %161 = load volatile i8, ptr %holder_key, align 1
  br label %bb78

bb84:                                             ; preds = %"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE.exit", %bb83, %bb78
  ret void
}

; Function Attrs: mustprogress nocallback nofree nounwind willreturn memory(argmem: readwrite)
declare void @llvm.memcpy.p0.p0.i64(ptr noalias nocapture writeonly, ptr noalias nocapture readonly, i64, i1 immarg) #10

; <pump_recovered::PumpError as core::fmt::Display>::fmt
; Function Attrs: nounwind
declare noundef zeroext i1 @"_ZN64_$LT$pump_recovered..PumpError$u20$as$u20$core..fmt..Display$GT$3fmt17hbf6a90ed7cf777ebE"(ptr noalias noundef readonly align 4 dereferenceable(4), ptr noalias noundef align 8 dereferenceable(64)) unnamed_addr #1

; core::result::unwrap_failed
; Function Attrs: cold noinline noreturn nounwind
declare void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1, i64 noundef, ptr noundef nonnull align 1, ptr noalias noundef readonly align 8 dereferenceable(24), ptr noalias noundef readonly align 8 dereferenceable(24)) unnamed_addr #11

; Function Attrs: mustprogress nocallback nofree nosync nounwind willreturn memory(inaccessiblemem: write)
declare hidden void @llvm.assume(i1 noundef) #12

; core::fmt::Formatter::write_str
; Function Attrs: nounwind
declare noundef zeroext i1 @_ZN4core3fmt9Formatter9write_str17h97ca3d8b34e3baaaE(ptr noalias noundef align 8 dereferenceable(64), ptr noalias noundef nonnull readonly align 1, i64 noundef) unnamed_addr #1

; Function Attrs: cold noreturn nounwind memory(inaccessiblemem: write)
declare hidden void @llvm.trap() #13

; Function Attrs: nounwind allockind("alloc,uninitialized,aligned") allocsize(0)
declare noalias noundef ptr @__rust_alloc(i64 noundef, i64 allocalign noundef) unnamed_addr #14

; Function Attrs: nounwind allockind("realloc,aligned") allocsize(3)
declare noalias noundef ptr @__rust_realloc(ptr allocptr noundef, i64 noundef, i64 allocalign noundef, i64 noundef) unnamed_addr #15

; Function Attrs: mustprogress nocallback nofree nounwind willreturn memory(argmem: write)
declare void @llvm.memset.p0.i64(ptr nocapture writeonly, i8, i64, i1 immarg) #16

; Function Attrs: mustprogress nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare hidden { i64, i1 } @llvm.uadd.with.overflow.i64(i64, i64) #17

; alloc::raw_vec::handle_error
; Function Attrs: cold noreturn nounwind
declare void @_ZN5alloc7raw_vec12handle_error17h22fdf317f3a37641E(i64 noundef, i64) unnamed_addr #18

; Function Attrs: nounwind allockind("free")
declare void @__rust_dealloc(ptr allocptr noundef, i64 noundef, i64 noundef) unnamed_addr #19

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

; Function Attrs: mustprogress nocallback nofree nosync nounwind willreturn memory(argmem: readwrite)
declare void @llvm.lifetime.end.p0(i64 immarg, ptr nocapture) unnamed_addr #20

; Function Attrs: mustprogress nofree nounwind willreturn memory(argmem: read)
declare hidden i32 @memcmp(ptr nocapture, ptr nocapture, i64) local_unnamed_addr #21

; Function Attrs: nofree nosync nounwind memory(none)
declare i8 @llvm.bpf.passthrough.i8.i8(i32, i8) unnamed_addr #22

; Function Attrs: mustprogress nocallback nofree nosync nounwind willreturn memory(argmem: readwrite)
declare void @llvm.lifetime.start.p0(i64 immarg, ptr nocapture) unnamed_addr #20

; anchor_lang::error::Error::with_pubkeys
; Function Attrs: nounwind
declare { i64, ptr } @_ZN11anchor_lang5error5Error12with_pubkeys17hca6dbbbe6a9a5da7E(i64 noundef, ptr noundef, ptr noalias nocapture noundef readonly align 1 dereferenceable(64)) unnamed_addr #1

; Function Attrs: mustprogress nocallback nofree nosync nounwind willreturn memory(inaccessiblemem: readwrite)
declare void @llvm.var.annotation.p0.p0(ptr, ptr, ptr, i32, ptr) unnamed_addr #23

; Function Attrs: mustprogress nocallback nofree nosync nounwind willreturn memory(inaccessiblemem: readwrite)
declare i1 @llvm.annotation.i1.p0(i1, ptr, ptr, i32) unnamed_addr #23

; Function Attrs: nofree nosync nounwind memory(none)
declare i64 @llvm.bpf.passthrough.i64.i64(i32, i64) unnamed_addr #22

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(inaccessiblemem: readwrite)
declare void @llvm.experimental.noalias.scope.decl(metadata) #24

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare i64 @llvm.umax.i64(i64, i64) #25

attributes #0 = { inlinehint nounwind "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #1 = { nounwind "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #2 = { inlinehint mustprogress nofree norecurse nosync nounwind willreturn memory(none) "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #3 = { noinline nounwind "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #4 = { cold nounwind "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #5 = { mustprogress nofree norecurse nosync nounwind willreturn memory(none) "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #6 = { mustprogress nofree norecurse nounwind willreturn "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #7 = { mustprogress nofree norecurse nosync nounwind willreturn memory(read, inaccessiblemem: none) "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #8 = { mustprogress nofree norecurse nosync nounwind willreturn memory(argmem: readwrite) "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #9 = { mustprogress nofree norecurse nosync nounwind willreturn memory(inaccessiblemem: readwrite) "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #10 = { mustprogress nocallback nofree nounwind willreturn memory(argmem: readwrite) }
attributes #11 = { cold noinline noreturn nounwind "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #12 = { mustprogress nocallback nofree nosync nounwind willreturn memory(inaccessiblemem: write) }
attributes #13 = { cold noreturn nounwind memory(inaccessiblemem: write) }
attributes #14 = { nounwind allockind("alloc,uninitialized,aligned") allocsize(0) "alloc-family"="__rust_alloc" "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #15 = { nounwind allockind("realloc,aligned") allocsize(3) "alloc-family"="__rust_alloc" "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #16 = { mustprogress nocallback nofree nounwind willreturn memory(argmem: write) }
attributes #17 = { mustprogress nocallback nofree nosync nounwind speculatable willreturn memory(none) }
attributes #18 = { cold noreturn nounwind "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #19 = { nounwind allockind("free") "alloc-family"="__rust_alloc" "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #20 = { mustprogress nocallback nofree nosync nounwind willreturn memory(argmem: readwrite) }
attributes #21 = { mustprogress nofree nounwind willreturn memory(argmem: read) }
attributes #22 = { nofree nosync nounwind memory(none) }
attributes #23 = { mustprogress nocallback nofree nosync nounwind willreturn memory(inaccessiblemem: readwrite) }
attributes #24 = { nocallback nofree nosync nounwind willreturn memory(inaccessiblemem: readwrite) }
attributes #25 = { nocallback nofree nosync nounwind speculatable willreturn memory(none) }
attributes #26 = { nounwind }
attributes #27 = { noreturn nounwind }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 8, !"PIC Level", i32 2}
!1 = !{!"rustc version 1.79.0-dev"}
!2 = !{}
!3 = !{!4}
!4 = distinct !{!4, !5, !"_ZN5alloc6string6String4push17h96dfc48c19bd6e38E: %self"}
!5 = distinct !{!5, !"_ZN5alloc6string6String4push17h96dfc48c19bd6e38E"}
!6 = !{!7}
!7 = distinct !{!7, !8, !"_ZN4core4char7methods15encode_utf8_raw17h84badf475ef2bb54E: %dst.0"}
!8 = distinct !{!8, !"_ZN4core4char7methods15encode_utf8_raw17h84badf475ef2bb54E"}
!9 = !{!10}
!10 = distinct !{!10, !11, !"_ZN5alloc3vec16Vec$LT$T$C$A$GT$17extend_from_slice17h9db90023fcfc2b1eE: %self"}
!11 = distinct !{!11, !"_ZN5alloc3vec16Vec$LT$T$C$A$GT$17extend_from_slice17h9db90023fcfc2b1eE"}
!12 = !{!13}
!13 = distinct !{!13, !14, !"_ZN132_$LT$alloc..vec..Vec$LT$T$C$A$GT$$u20$as$u20$alloc..vec..spec_extend..SpecExtend$LT$$RF$T$C$core..slice..iter..Iter$LT$T$GT$$GT$$GT$11spec_extend17h97a0acb7d1db89dfE: %self"}
!14 = distinct !{!14, !"_ZN132_$LT$alloc..vec..Vec$LT$T$C$A$GT$$u20$as$u20$alloc..vec..spec_extend..SpecExtend$LT$$RF$T$C$core..slice..iter..Iter$LT$T$GT$$GT$$GT$11spec_extend17h97a0acb7d1db89dfE"}
!15 = !{!16}
!16 = distinct !{!16, !17, !"_ZN5alloc3vec16Vec$LT$T$C$A$GT$15append_elements17hcb02820fa3a5db71E: %self"}
!17 = distinct !{!17, !"_ZN5alloc3vec16Vec$LT$T$C$A$GT$15append_elements17hcb02820fa3a5db71E"}
!18 = !{!16, !13, !10, !4}
!19 = !{!20}
!20 = distinct !{!20, !11, !"_ZN5alloc3vec16Vec$LT$T$C$A$GT$17extend_from_slice17h9db90023fcfc2b1eE: %other.0"}
!21 = !{!22, !16, !13, !10, !4}
!22 = distinct !{!22, !23, !"_ZN5alloc3vec16Vec$LT$T$C$A$GT$7reserve17hccdbefae89c3a2f3E: %self"}
!23 = distinct !{!23, !"_ZN5alloc3vec16Vec$LT$T$C$A$GT$7reserve17hccdbefae89c3a2f3E"}
!24 = !{!25}
!25 = distinct !{!25, !26, !"_ZN5alloc3vec16Vec$LT$T$C$A$GT$4push17h3eecfd24bc944e21E: %self"}
!26 = distinct !{!26, !"_ZN5alloc3vec16Vec$LT$T$C$A$GT$4push17h3eecfd24bc944e21E"}
!27 = !{!25, !4}
!28 = !{!29}
!29 = distinct !{!29, !30, !"_ZN5alloc3vec16Vec$LT$T$C$A$GT$17extend_from_slice17h9db90023fcfc2b1eE: %self"}
!30 = distinct !{!30, !"_ZN5alloc3vec16Vec$LT$T$C$A$GT$17extend_from_slice17h9db90023fcfc2b1eE"}
!31 = !{!32}
!32 = distinct !{!32, !33, !"_ZN132_$LT$alloc..vec..Vec$LT$T$C$A$GT$$u20$as$u20$alloc..vec..spec_extend..SpecExtend$LT$$RF$T$C$core..slice..iter..Iter$LT$T$GT$$GT$$GT$11spec_extend17h97a0acb7d1db89dfE: %self"}
!33 = distinct !{!33, !"_ZN132_$LT$alloc..vec..Vec$LT$T$C$A$GT$$u20$as$u20$alloc..vec..spec_extend..SpecExtend$LT$$RF$T$C$core..slice..iter..Iter$LT$T$GT$$GT$$GT$11spec_extend17h97a0acb7d1db89dfE"}
!34 = !{!35}
!35 = distinct !{!35, !36, !"_ZN5alloc3vec16Vec$LT$T$C$A$GT$15append_elements17hcb02820fa3a5db71E: %self"}
!36 = distinct !{!36, !"_ZN5alloc3vec16Vec$LT$T$C$A$GT$15append_elements17hcb02820fa3a5db71E"}
!37 = !{!35, !32, !29}
!38 = !{!39}
!39 = distinct !{!39, !30, !"_ZN5alloc3vec16Vec$LT$T$C$A$GT$17extend_from_slice17h9db90023fcfc2b1eE: %other.0"}
!40 = !{!41, !35, !32, !29}
!41 = distinct !{!41, !42, !"_ZN5alloc3vec16Vec$LT$T$C$A$GT$7reserve17hccdbefae89c3a2f3E: %self"}
!42 = distinct !{!42, !"_ZN5alloc3vec16Vec$LT$T$C$A$GT$7reserve17hccdbefae89c3a2f3E"}
!43 = !{i64 0, i64 -9223372036854775807}
!44 = !{!45}
!45 = distinct !{!45, !46, !"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14grow_amortized17h842a7461f6b52281E: %self"}
!46 = distinct !{!46, !"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14grow_amortized17h842a7461f6b52281E"}
!47 = !{!48}
!48 = distinct !{!48, !49, !"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14current_memory17hc167f39406d68977E: %_0"}
!49 = distinct !{!49, !"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14current_memory17hc167f39406d68977E"}
!50 = !{i64 0, i64 2}
!51 = !{!52}
!52 = distinct !{!52, !53, !"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14grow_amortized17h842a7461f6b52281E: %self"}
!53 = distinct !{!53, !"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14grow_amortized17h842a7461f6b52281E"}
!54 = !{!55}
!55 = distinct !{!55, !56, !"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14current_memory17hc167f39406d68977E: %_0"}
!56 = distinct !{!56, !"_ZN5alloc7raw_vec19RawVec$LT$T$C$A$GT$14current_memory17hc167f39406d68977E"}
!57 = !{i8 0, i8 2}
!58 = !{!59, !61}
!59 = distinct !{!59, !60, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!60 = distinct !{!60, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!61 = distinct !{!61, !60, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!62 = !{!59}
!63 = !{!"branch_weights", i32 1095216661, i32 1052266988}
!64 = !{!65, !67}
!65 = distinct !{!65, !66, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!66 = distinct !{!66, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!67 = distinct !{!67, !66, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!68 = !{!65}
!69 = !{!"branch_weights", i32 1610612736, i32 536870913}
!70 = !{!71, !73}
!71 = distinct !{!71, !72, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!72 = distinct !{!72, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!73 = distinct !{!73, !72, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!74 = !{!71}
!75 = !{!"branch_weights", i32 805306369, i32 1342177280}
!76 = !{!"branch_weights", i32 1, i32 2000}
!77 = !{!78, !80}
!78 = distinct !{!78, !79, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!79 = distinct !{!79, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!80 = distinct !{!80, !79, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!81 = !{!78}
!82 = !{!83, !85}
!83 = distinct !{!83, !84, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!84 = distinct !{!84, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!85 = distinct !{!85, !84, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!86 = !{!83}
!87 = !{!88, !90}
!88 = distinct !{!88, !89, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!89 = distinct !{!89, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!90 = distinct !{!90, !89, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!91 = !{!88}
!92 = !{!93, !95}
!93 = distinct !{!93, !94, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!94 = distinct !{!94, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!95 = distinct !{!95, !94, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!96 = !{!93}
!97 = !{!"branch_weights", i32 1073741824, i32 1073741824}
!98 = !{!99, !101}
!99 = distinct !{!99, !100, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!100 = distinct !{!100, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!101 = distinct !{!101, !100, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!102 = !{!99}
!103 = !{!104, !106}
!104 = distinct !{!104, !105, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!105 = distinct !{!105, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!106 = distinct !{!106, !105, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!107 = !{!104}
!108 = !{!109, !111}
!109 = distinct !{!109, !110, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!110 = distinct !{!110, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!111 = distinct !{!111, !110, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!112 = !{!109}
!113 = !{!114, !116}
!114 = distinct !{!114, !115, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!115 = distinct !{!115, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!116 = distinct !{!116, !115, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!117 = !{!114}
!118 = !{!119, !121}
!119 = distinct !{!119, !120, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!120 = distinct !{!120, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!121 = distinct !{!121, !120, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!122 = !{!119}
!123 = !{i64 8}
!124 = !{!125}
!125 = distinct !{!125, !126, !"_ZN71_$LT$solana_account_info..AccountInfo$u20$as$u20$core..clone..Clone$GT$5clone17h759150bcde62cc00E: %_0"}
!126 = distinct !{!126, !"_ZN71_$LT$solana_account_info..AccountInfo$u20$as$u20$core..clone..Clone$GT$5clone17h759150bcde62cc00E"}
!127 = !{!128}
!128 = distinct !{!128, !126, !"_ZN71_$LT$solana_account_info..AccountInfo$u20$as$u20$core..clone..Clone$GT$5clone17h759150bcde62cc00E: %self"}
!129 = !{i64 1}
!130 = !{!125, !128}
!131 = !{!132, !134}
!132 = distinct !{!132, !133, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!133 = distinct !{!133, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!134 = distinct !{!134, !133, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!135 = !{!132}
!136 = !{!137, !139}
!137 = distinct !{!137, !138, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!138 = distinct !{!138, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!139 = distinct !{!139, !138, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!140 = !{!137}
!141 = !{!142, !144}
!142 = distinct !{!142, !143, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!143 = distinct !{!143, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!144 = distinct !{!144, !143, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!145 = !{!142}
!146 = !{!"branch_weights", i32 1352914698, i32 794568951}
!147 = !{!148, !150}
!148 = distinct !{!148, !149, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!149 = distinct !{!149, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!150 = distinct !{!150, !149, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!151 = !{!148}
!152 = !{!153, !155}
!153 = distinct !{!153, !154, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!154 = distinct !{!154, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!155 = distinct !{!155, !154, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!156 = !{!153}
!157 = !{!158, !160}
!158 = distinct !{!158, !159, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!159 = distinct !{!159, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!160 = distinct !{!160, !159, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!161 = !{!158}
!162 = !{!163, !165}
!163 = distinct !{!163, !164, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!164 = distinct !{!164, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!165 = distinct !{!165, !164, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!166 = !{!163}
!167 = !{!168, !170}
!168 = distinct !{!168, !169, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!169 = distinct !{!169, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!170 = distinct !{!170, !169, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!171 = !{!168}
!172 = !{!173, !175}
!173 = distinct !{!173, !174, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!174 = distinct !{!174, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!175 = distinct !{!175, !174, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!176 = !{!173}
!177 = !{!178, !180}
!178 = distinct !{!178, !179, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!179 = distinct !{!179, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!180 = distinct !{!180, !179, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!181 = !{!178}
!182 = !{!183, !185}
!183 = distinct !{!183, !184, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!184 = distinct !{!184, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!185 = distinct !{!185, !184, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!186 = !{!183}
!187 = !{!188, !190}
!188 = distinct !{!188, !189, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %_0"}
!189 = distinct !{!189, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE"}
!190 = distinct !{!190, !189, !"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h3e0ddeef0401034aE: %self"}
!191 = !{!188}
