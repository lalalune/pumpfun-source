import re
def edit(f):
    return re.sub(r'\n\s*call void @llvm\.lifetime\.(start|end)\.p0\(i64 136, ptr nonnull %completion\)','',f)
