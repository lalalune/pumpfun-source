# helper: move a defining line to after an anchor line
def mvline(t, line, anchor, before=False):
    assert t.count(line)==1, ('line', line, t.count(line))
    t=t.replace(line,'',1)
    assert t.count(anchor)==1, ('anchor', anchor, t.count(anchor))
    return t.replace(anchor, (line+anchor) if before else (anchor+line), 1)
G='  %_218 = getelementptr inbounds i8, ptr %_618, i64 8\n'
