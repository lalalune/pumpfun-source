import re,sys
def make(which, vol=True):
    """which: set of use tags among {'err','tok','ens','tn'}"""
    def edit(f):
        L=f.split('\n')
        out=[]; first_alloca=True
        V='volatile ' if vol else ''
        for l in L:
            s=l.strip()
            if first_alloca and re.match(r'%\S+ = alloca',s):
                out.append('  %vs.slot = alloca ptr, align 8'); first_alloca=False
            uses=[]
            if '%327' in l and not s.startswith('%327 ='):
                tag=None
                if '%_194.i = load ptr, ptr %327' in l: tag='err'
                elif 'ensure_rent_exempt' in l: tag='ens'
                elif 'collect_transfer_native' in l: tag='tn'
                elif 'Clone$GT$5clone' in l: tag='tok'
                if tag in which:
                    n='%vsl.'+tag
                    out.append(f'  {n} = load {V}ptr, ptr %vs.slot, align 8')
                    l=re.sub(r'%327\b',n,l)
            out.append(l)
            if s.startswith('%327 = getelementptr'):
                out.append(f'  store {V}ptr %327, ptr %vs.slot, align 8')
        return '\n'.join(out)
    return edit

def bump(vol=True, ty='i64'):
    def edit(f):
        V='volatile ' if vol else ''
        L=f.split('\n'); out=[]; first=True
        for l in L:
            s=l.strip()
            if first and re.match(r'%\S+ = alloca',s):
                out.append(f'  %bs.slot = alloca {ty}, align 8'); first=False
            if s.startswith('store i8 %ctx.val44, ptr %_98.i'):
                if ty=='i8':
                    out.append(f'  %bsl = load {V}i8, ptr %bs.slot, align 8')
                else:
                    out.append(f'  %bsl64 = load {V}i64, ptr %bs.slot, align 8'); out.append('  %bsl = trunc i64 %bsl64 to i8')
                l=l.replace('%ctx.val44','%bsl')
            out.append(l)
            if s.startswith('%ctx.val44 = load'):
                if ty=='i8': out.append(f'  store {V}i8 %ctx.val44, ptr %bs.slot, align 8')
                else: out.append('  %bz = zext i8 %ctx.val44 to i64'); out.append(f'  store {V}i64 %bz, ptr %bs.slot, align 8')
        return '\n'.join(out)
    return edit
def chain(*fs):
    def edit(f):
        for g in fs: f=g(f)
        return f
    return edit

def late(vals, vol=True, block='bb7.i87:'):
    """split spill: store each value at the top of `block` (after the 648 memcmp), reload before its later uses.
    vals subset of {'bump','vault'}"""
    def edit(f):
        V='volatile ' if vol else ''
        L=f.split('\n'); out=[]; first=True; inblk=False
        for l in L:
            s=l.strip()
            if first and re.match(r'%\S+ = alloca',s):
                if 'bump' in vals: out.append('  %bs.slot = alloca i64, align 8')
                if 'vault' in vals: out.append('  %vs.slot = alloca ptr, align 8')
                first=False
            if 'bump' in vals and s.startswith('store i8 %ctx.val44, ptr %_98.i'):
                out.append(f'  %bsl64 = load {V}i64, ptr %bs.slot, align 8'); out.append('  %bsl = trunc i64 %bsl64 to i8')
                l=l.replace('%ctx.val44','%bsl')
            if 'vault' in vals and '%327' in l and not s.startswith('%327 =') and ('ensure_rent_exempt' in l or 'collect_transfer_native' in l or 'Clone$GT$5clone' in l):
                tag=str(len(out)); out.append(f'  %vsl.{tag} = load {V}ptr, ptr %vs.slot, align 8'); l=re.sub(r'%327\b',f'%vsl.{tag}',l)
            out.append(l)
            if l.startswith(block):
                inblk=True; continue
            if inblk and not s.startswith(';'):
                # insert before first instruction of block
                ins=l; out.pop()
                if 'bump' in vals: out.append('  %bz = zext i8 %ctx.val44 to i64'); out.append(f'  store {V}i64 %bz, ptr %bs.slot, align 8')
                if 'vault' in vals: out.append(f'  store {V}ptr %327, ptr %vs.slot, align 8')
                out.append(ins); inblk=False
        return '\n'.join(out)
    return edit
