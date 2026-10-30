def edit(t):
    old = "  %_1056 = load ptr, ptr %h.val, align 8"
    assert t.count(old) == 1
    return t.replace(old, "  %hv2 = load ptr, ptr %1, align 8\n  %_1056 = load ptr, ptr %hv2, align 8")
