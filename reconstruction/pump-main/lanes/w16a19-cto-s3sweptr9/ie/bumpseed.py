# oracle: load ctx.bumps.creator_vault at the vault-seed block (bb26.i122) instead of the sweep head (undo ArgumentPromotion hoist)
import re
def renum(t):
    i=t.index('define hidden { i64, ptr } @_ZN14pump_recovered9admin_cto7execute'); j=t.index('\n}\n',i)
    body=t[i:j]
    body=re.sub(r'%(\d+)(?![\w.])', lambda m: '%'+str(int(m.group(1))-1) if int(m.group(1))>=323 else m.group(0), body)
    return t[:i]+body+t[j:]
EDITS=[
 ("  %322 = getelementptr inbounds i8, ptr %ctx, i64 35\n  %ctx.val62 = load i8, ptr %322, align 1\n",""),
 ("  call void @llvm.lifetime.start.p0(i64 1, ptr nonnull %_113.i), !noalias !8629\n  store i8 %ctx.val62, ptr %_113.i, align 1, !noalias !8629\n",
  "  call void @llvm.lifetime.start.p0(i64 1, ptr nonnull %_113.i), !noalias !8629\n  %bumpgep = getelementptr inbounds i8, ptr %ctx, i64 35\n  %ctx.val62 = load i8, ptr %bumpgep, align 1\n  store i8 %ctx.val62, ptr %_113.i, align 1, !noalias !8629\n"),
 (lambda t: renum(t)),
]
