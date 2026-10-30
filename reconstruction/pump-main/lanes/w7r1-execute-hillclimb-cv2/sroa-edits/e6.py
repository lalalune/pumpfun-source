import re
def edit(f):
    # Err ptr stores at +16 -> i64 stores
    n=[0]
    def rep(m):
        n[0]+=1; return f'%pi{n[0]} = ptrtoint ptr {m.group(1)} to i64\n  store i64 %pi{n[0]}, ptr {m.group(2)}'
    g16=set(re.findall(r'(%[\w.$"]+) = getelementptr inbounds i8, ptr %_84, i64 16',f))
    for v in g16:
        f=re.sub(r'store ptr (%[\w.$"]+), ptr ('+re.escape(v)+r')(?=,)',rep,f)
    return f
