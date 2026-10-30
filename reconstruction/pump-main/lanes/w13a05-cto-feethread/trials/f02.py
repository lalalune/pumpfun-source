# whole-file transform: validation inline in execute (validate fn removed)
import os
ARM=os.environ.get('ARM','0')=='1'
def transform(s):
    L=s.split('\n')
    v0=L[282]; assert v0.startswith('fn validate(')
    ex=L[338]; i=ex.index('pub fn execute(')
    tail=ex[i:]
    head_end=tail.index('let mut target=validate(')
    head=tail[:head_end]   # 'pub fn execute(...){ let a=..;...;let (holder,...)={let st=CtoState{..}; let holder=..;let cashback=..;'
    rest=tail[head_end:]
    rest=rest[rest.index('?;')+2:]  # after validate call
    L[282]=head
    for k in range(283,338):
        l=L[k]
        l=l.replace('*holder_key','holder_key').replace('t==*sharing','t==a.sharing_config.key()')
        L[k]=l
    # line 312 ends with '...}t};' -> keep 'let target=if holder{...' (line 298 starts 'let target=')
    if ARM:
        L[311]=L[311].replace('}t};','}if shared{st.creator}else{t}};')
        rest=rest.replace('else{target=st.creator;(Some(new),false)}','else{(Some(new),false)}')
    L[338]=' '+rest if not ARM else ' '+rest
    # 338 ends with 'None=>{}}' ; line 339 originally began with ' Ok(target)}' before execute
    assert ex.startswith(' Ok(target)}'),ex[:20]
    if not ARM:
        L[338]=' let mut target=target;'+rest
    return '\n'.join(L)
