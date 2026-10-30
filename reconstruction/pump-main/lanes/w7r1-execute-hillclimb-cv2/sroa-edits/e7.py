def edit(f):
    import runpy; a=runpy.run_path('sx/e6.py')['edit'](f)
    return a.replace('%_270.1 = load ptr, ptr %269, align 8','%_270.1i = load i64, ptr %269, align 8\n  %_270.1 = inttoptr i64 %_270.1i to ptr')
