; ModuleID = 'pass114_slot_probe.836c91c48f54db30-cgu.0'
source_filename = "pass114_slot_probe.836c91c48f54db30-cgu.0"
target datalayout = "e-m:e-p:64:64-i64:64-n32:64-S128"
target triple = "sbf"

@alloc_7a7952b5e0d15f2b72d0341cef6d4739 = private unnamed_addr constant <{ [17 x i8] }> <{ [17 x i8] c"__event_authority" }>, align 1

; Function Attrs: mustprogress nofree norecurse nounwind willreturn memory(inaccessiblemem: readwrite)
define noundef i8 @low_byte_false() unnamed_addr #0 {
start:
  %_1.sroa.0 = alloca i8, align 8
  call void @llvm.lifetime.start.p0(i64 1, ptr nonnull %_1.sroa.0)
  store i8 0, ptr %_1.sroa.0, align 8
  %_1.sroa.0.0._1.sroa.0.0._1.sroa.0.0._1.sroa.0.0._1.sroa.0.0. = load volatile i8, ptr %_1.sroa.0, align 8
  call void @llvm.lifetime.end.p0(i64 1, ptr nonnull %_1.sroa.0)
  ret i8 %_1.sroa.0.0._1.sroa.0.0._1.sroa.0.0._1.sroa.0.0._1.sroa.0.0.
}

; Function Attrs: mustprogress nofree norecurse nounwind willreturn memory(inaccessiblemem: readwrite)
define noundef i8 @low_byte_true() unnamed_addr #0 {
start:
  %_1.sroa.0 = alloca i8, align 8
  call void @llvm.lifetime.start.p0(i64 1, ptr nonnull %_1.sroa.0)
  store i8 1, ptr %_1.sroa.0, align 8
  %_1.sroa.0.0._1.sroa.0.0._1.sroa.0.0._1.sroa.0.0._1.sroa.0.0. = load volatile i8, ptr %_1.sroa.0, align 8
  call void @llvm.lifetime.end.p0(i64 1, ptr nonnull %_1.sroa.0)
  ret i8 %_1.sroa.0.0._1.sroa.0.0._1.sroa.0.0._1.sroa.0.0._1.sroa.0.0.
}

; Function Attrs: nounwind
define void @scratch_slots(ptr dead_on_unwind noalias nocapture noundef writable writeonly sret([33 x i8]) align 1 dereferenceable(33) %_0, ptr noalias nocapture noundef readonly align 1 dereferenceable(32) %key, ptr noalias noundef readonly align 8 dereferenceable(48) %accounts, i1 noundef zeroext %cashback, i1 noundef zeroext %coin_empty, i8 noundef %bump) unnamed_addr #1 {
start:
  %_18 = alloca [1 x i8], align 1
  %_14 = alloca [32 x i8], align 8
  %hkx = alloca [72 x i8], align 8
  call void @llvm.lifetime.start.p0(i64 72, ptr nonnull %hkx)
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(32) %hkx, ptr noundef nonnull align 1 dereferenceable(32) %key, i64 32, i1 false)
  %_10 = getelementptr inbounds i64, ptr %hkx, i64 8
  %0 = zext i1 %coin_empty to i8
  store volatile i8 %0, ptr %_10, align 8
  store volatile i8 %0, ptr %_10, align 8
  store volatile i8 %0, ptr %_10, align 8
  store volatile i8 %0, ptr %_10, align 8
  store volatile i8 %0, ptr %_10, align 8
  store volatile i8 %0, ptr %_10, align 8
  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %_14)
  call void @llvm.lifetime.start.p0(i64 1, ptr nonnull %_18)
  store i8 %bump, ptr %_18, align 1
  store ptr @alloc_7a7952b5e0d15f2b72d0341cef6d4739, ptr %_14, align 8
  %1 = getelementptr inbounds i8, ptr %_14, i64 8
  store i64 17, ptr %1, align 8
  %2 = getelementptr inbounds [2 x { ptr, i64 }], ptr %_14, i64 0, i64 1
  store ptr %_18, ptr %2, align 8
  %3 = getelementptr inbounds [2 x { ptr, i64 }], ptr %_14, i64 0, i64 1, i32 1
  store i64 1, ptr %3, align 8
  %_20 = getelementptr inbounds i64, ptr %hkx, i64 4
  store ptr %_14, ptr %_20, align 8
  %_21.sroa.2.0._20.sroa_idx = getelementptr inbounds i64, ptr %hkx, i64 5
  store i64 2, ptr %_21.sroa.2.0._20.sroa_idx, align 8
  call void @observe_signers(ptr noundef nonnull %_20, i64 noundef 1) #4
  call void @llvm.lifetime.end.p0(i64 1, ptr nonnull %_18)
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %_14)
  %_26 = getelementptr inbounds i64, ptr %hkx, i64 6
  store volatile ptr %accounts, ptr %_26, align 8
  call void @observe_accounts(ptr noundef nonnull %accounts) #4
  %_30 = getelementptr inbounds i64, ptr %hkx, i64 7
  %_31 = zext i1 %cashback to i64
  store volatile i64 %_31, ptr %_30, align 8
  %4 = load volatile ptr, ptr %_26, align 8
  call void @observe_accounts(ptr noundef %4) #4
  %5 = load volatile i8, ptr %_30, align 8
  store volatile i8 %bump, ptr %_10, align 8
  store volatile i8 %bump, ptr %_10, align 8
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %_0, ptr noundef nonnull align 8 dereferenceable(32) %hkx, i64 32, i1 false)
  %6 = and i8 %5, 1
  %7 = getelementptr inbounds i8, ptr %_0, i64 32
  store i8 %6, ptr %7, align 1
  call void @llvm.lifetime.end.p0(i64 72, ptr nonnull %hkx)
  ret void
}

; Function Attrs: mustprogress nocallback nofree nounwind willreturn memory(argmem: readwrite)
declare void @llvm.memcpy.p0.p0.i64(ptr noalias nocapture writeonly, ptr noalias nocapture readonly, i64, i1 immarg) #2

; Function Attrs: nounwind
declare void @observe_signers(ptr noundef, i64 noundef) unnamed_addr #1

; Function Attrs: nounwind
declare void @observe_accounts(ptr noundef) unnamed_addr #1

; Function Attrs: mustprogress nocallback nofree nosync nounwind willreturn memory(argmem: readwrite)
declare void @llvm.lifetime.start.p0(i64 immarg, ptr nocapture) #3

; Function Attrs: mustprogress nocallback nofree nosync nounwind willreturn memory(argmem: readwrite)
declare void @llvm.lifetime.end.p0(i64 immarg, ptr nocapture) #3

attributes #0 = { mustprogress nofree norecurse nounwind willreturn memory(inaccessiblemem: readwrite) "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #1 = { nounwind "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #2 = { mustprogress nocallback nofree nounwind willreturn memory(argmem: readwrite) }
attributes #3 = { mustprogress nocallback nofree nosync nounwind willreturn memory(argmem: readwrite) }
attributes #4 = { nounwind }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 8, !"PIC Level", i32 2}
!1 = !{!"rustc version 1.79.0-dev"}
