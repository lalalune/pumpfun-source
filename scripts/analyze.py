#!/usr/bin/env python3
"""Offline ELF layout, string provenance and public-interface inventory."""
import hashlib,json,pathlib,re,struct
ROOT=pathlib.Path(__file__).resolve().parents[1]
IDL_INTERNAL_NAMES = (
    'IdlCreateAccount', 'IdlResizeAccount', 'IdlCloseAccount',
    'IdlCreateBuffer', 'IdlWrite', 'IdlSetAuthority', 'IdlSetBuffer',
)


def known_instruction_names(name):
    """Return IDL instruction names in the CamelCase form used by logs."""
    path = ROOT / 'evidence/upstream' / f'{name}.json'
    if not path.is_file():
        return ()
    data = json.loads(path.read_text(encoding='utf-8'))
    names = {
        ''.join(part[:1].upper() + part[1:] for part in item['name'].split('_'))
        for item in data.get('instructions', [])
    }
    names.update(IDL_INTERNAL_NAMES)
    return tuple(sorted(names, key=len, reverse=True))


def program_names(root=ROOT):
    """Use the archived mapping when present, otherwise the captured programs."""
    path = root / 'repro/programs.json'
    if path.is_file():
        return json.loads(path.read_text())
    order = ('pump', 'pump_amm', 'pump_fees', 'mayhem')
    return [
        name for name in order
        if (root / 'evidence/original' / name / 'deployed.so').is_file()
    ]


def program_addresses():
    """Map program names to addresses from the archive or each capture."""
    path = ROOT / 'repro/programs.json'
    if path.is_file():
        return json.loads(path.read_text())
    return {
        name: json.loads(
            (ROOT / 'evidence/original' / name / 'capture.json').read_text()
        )['program']
        for name in program_names()
    }


def instruction_log_names(b, known=()):
    """Extract exact instruction names, longest known prefix first.

    A log site may be immediately followed by a lowercase suffix or another
    string, e.g. `Instruction: ClaimCashbacksol_destination...`. Matching the
    known IDL names first avoids absorbing that adjacent text; programs without
    an IDL keep the original alphanumeric fallback.
    """
    names = set()
    for match in re.finditer(rb'Instruction: ', b):
        rest = b[match.end():]
        exact = next((name for name in known if rest.startswith(name.encode())), None)
        if exact is not None:
            names.add(exact)
            continue
        fallback = re.match(rb'[A-Z][A-Za-z0-9]*', rest)
        if fallback:
            name = fallback.group().decode()
            if name.endswith('Instruction') and name != 'Instruction':
                name = name[:-len('Instruction')]
            names.add(name)
    return sorted(names)


def elf_layout(b):
    assert b[:6]==b'\x7fELF\x02\x01'
    h=struct.unpack_from('<HHIQQQIHHHHHH',b,16)
    _,machine,_,entry,phoff,shoff,flags,ehsize,phsize,phnum,shsize,shnum,shstr=h
    assert phsize==56 and shsize==64 and shnum>0
    raw=[struct.unpack_from('<IIQQQQIIQQ',b,shoff+i*shsize) for i in range(shnum)]
    names=b[raw[shstr][4]:raw[shstr][4]+raw[shstr][5]]
    end=max(ehsize,phoff+phsize*phnum,shoff+shsize*shnum)
    sections=[]
    for s in raw:
        name=names[s[0]:].split(b'\0')[0].decode()
        if s[1]!=8: end=max(end,s[4]+s[5])
        sections.append({'name':name,'type':s[1],'offset':s[4],'size':s[5],'address':s[3],'flags':s[2]})
    for i in range(phnum):
        p=struct.unpack_from('<IIQQQQQQ',b,phoff+i*phsize); end=max(end,p[2]+p[5])
    assert end<=len(b)
    return {'machine':machine,'entry':entry,'flags':flags,'elf_extent':end,'allocation_bytes':len(b),'trailing_bytes':len(b)-end,'trailing_all_zero':not any(b[end:]),'elf_sha256':hashlib.sha256(b[:end]).hexdigest(),'sections':sections}
def analyze():
    out={}
    for name in program_names():
        b=(ROOT/f'evidence/original/{name}/deployed.so').read_bytes(); r=elf_layout(b)
        r['source_path_evidence']=[{'offset':m.start(),'path':m.group().decode()} for m in re.finditer(rb'(?:programs|/home/runner/work/platform-tools)[a-zA-Z0-9_./-]+?\.rs',b)]
        r['instruction_log_names']=instruction_log_names(b, known_instruction_names(name))
        r['compiler_version']='unresolved'; r['dependency_versions']='unresolved'; out[name]=r
    (ROOT/'evidence/binary-analysis.json').write_text(json.dumps(out,indent=2)+'\n')
    inventory={}
    for f in (ROOT/'evidence/upstream').glob('pump*.json'):
        d=json.loads(f.read_text()); addresses={}
        def walk(accounts,ix):
            for a in accounts:
                if 'address' in a: addresses.setdefault(a['address'],[]).append({'instruction':ix,'account':a['name']})
                walk(a.get('accounts',[]),ix)
        for ix in d['instructions']: walk(ix['accounts'],ix['name'])
        inventory[f.stem]={'address':d['address'],'metadata':d.get('metadata'),'instructions':len(d['instructions']),'fixed_addresses':addresses}
    (ROOT/'evidence/interface-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    for n,r in out.items(): print(n,'ELF',r['elf_extent'],'padding',r['trailing_bytes'],'zero',r['trailing_all_zero'])
if __name__=='__main__': analyze()
