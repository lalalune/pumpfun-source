# oracle: drop dest.i's lifetime.end in bb56.i so the sweep's inner error join can fold into sweep.exit (more preds for the ? test)
EDITS=[
 ("  %_426.sroa.18.2 = phi i64 [ %_426.sroa.18.1, %bb53.i124 ], [ %498, %bb79.i147 ], [ %516, %bb22.i116 ], [ %510, %bb81.i114 ], [ %352, %bb60.i112 ], [ %347, %\"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h4b386cbefe3ebd9eE.exit.i\" ]\n  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %dest.i), !noalias !8629\n",
  "  %_426.sroa.18.2 = phi i64 [ %_426.sroa.18.1, %bb53.i124 ], [ %498, %bb79.i147 ], [ %516, %bb22.i116 ], [ %510, %bb81.i114 ], [ %352, %bb60.i112 ], [ %347, %\"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h4b386cbefe3ebd9eE.exit.i\" ]\n"),
]
