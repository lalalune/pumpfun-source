import os
def edit(f):
    f=f.replace("bb60:                                             ; preds = %start\n  %12 = extractvalue { i64, ptr } %2, 1\n","bb60:                                             ; preds = %start\n")
    if os.environ.get('EVPOS')=='before':
        return f.replace("  %3 = extractvalue { i64, ptr } %2, 0\n","  %12 = extractvalue { i64, ptr } %2, 1\n  %3 = extractvalue { i64, ptr } %2, 0\n")
    return f.replace("  %3 = extractvalue { i64, ptr } %2, 0\n","  %3 = extractvalue { i64, ptr } %2, 0\n  %12 = extractvalue { i64, ptr } %2, 1\n")
