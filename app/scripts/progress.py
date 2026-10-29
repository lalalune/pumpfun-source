#!/usr/bin/env python3
"""Render deterministic source/feature progress from evidence and an explicit ledger."""
import argparse, collections, hashlib, json, pathlib, re, tarfile
from urllib.parse import urlsplit
ROOT = pathlib.Path(__file__).resolve().parents[1]
BEGIN = '<!-- app-progress:start -->'
END = '<!-- app-progress:end -->'
def read(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))

def require(condition, message):
    if not condition: raise ValueError(message)
def score(items):
    applicable=[v for v in items.values() if v['status']!='not-applicable']
    for item in items.values():
        require(item['status'] in {'pending','accepted','not-applicable'}, 'Unknown milestone status')
        if item['status'] in {'accepted','not-applicable'}:
            require(item['evidence'], 'Accepted/excluded gates require evidence or an explicit applicability decision')
            for evidence in item['evidence']: require((ROOT/evidence.split('#')[0]).is_file(), evidence)
    complete=sum(v['status']=='accepted' for v in applicable)
    return 'N/A' if not applicable else f'{complete}/{len(applicable)} ({100*complete/len(applicable):.0f}%)'
def replace_readme(text,block):
    section=f'{BEGIN}\n{block}\n{END}\n\n'
    if BEGIN in text or END in text:
        require(text.count(BEGIN)==text.count(END)==1, 'Expected one progress marker pair')
        require(text.index(BEGIN)<text.index(END), 'Progress start marker must precede end marker')
        return re.sub(re.escape(BEGIN)+r'.*?'+re.escape(END)+r'\n*',lambda _:section,text,flags=re.S)
    anchor='## Remaining work' if '## Remaining work' in text else '## License'
    require(anchor in text, 'README progress insertion anchor is missing')
    return text.replace(anchor,section+anchor,1)
def render():
    ledger=read('contracts/feature-progress.json'); manifest=read('evidence/web/manifest.json'); recovered=read('recovered/modules.json'); candidates=read('contracts/internal-operations.json')['operations']; spec=read('contracts/developer.openapi.json')
    require(len({r['id'] for r in ledger['frontend']})==len(ledger['frontend']), 'Duplicate frontend feature IDs')
    require(len({r['id'] for r in ledger['backend']})==len(ledger['backend']), 'Duplicate backend feature IDs')
    for layer in ['frontend','backend']:
        for row in ledger[layer]:
            for category in ['source','completion']:
                require(set(row[category])==set(ledger['gates'][category]), 'Milestone gates differ from the ledger');score(row[category])
            if row['completion']['source']['status'] in {'accepted','not-applicable'}:
                require(all(g['status'] in {'accepted','not-applicable'} for g in row['source'].values()), 'Source completion requires all source gates')
    scripts=[r for r in manifest['records'] if urlsplit(r['url']).path.endswith('.js')]
    verified=0
    for record in scripts:
        if record.get('status') != 200: continue
        body=(ROOT/record['path']).read_bytes()
        if 'bytes' in record:
            require(type(record['bytes']) is int and record['bytes'] >= 0 and len(body)==record['bytes'], 'Captured script byte count mismatch')
        digest = hashlib.sha256(body).hexdigest()
        require(isinstance(record.get('sha256'), str) and digest == record['sha256'], f'Captured script hash mismatch: {record.get("path")}')
        verified += 1
    script_progress=f'{100*verified/len(scripts):.0f}%' if scripts else 'N/A'
    factory_progress='100%' if recovered['modules'] else 'N/A'
    source_count=source_equal=0
    expected_sources=set()
    with tarfile.open(ROOT/'evidence/sdk/pump-sdk-4.3.1.tgz') as archive:
        for m in archive:
            if m.isfile() and m.name.startswith('package/src/'):
                expected_sources.add(m.name.removeprefix('package/src/'))
                source_count+=1;source_equal+=archive.extractfile(m).read()==(ROOT/'packages/sdk'/m.name.removeprefix('package/')).read_bytes()
    actual_sources={p.relative_to(ROOT/'packages/sdk/src').as_posix() for p in (ROOT/'packages/sdk/src').rglob('*') if p.is_file()}
    require(actual_sources==expected_sources, 'SDK source inventory differs from archive')
    operations=[(path,method,op) for path,item in spec['paths'].items() for method,op in item.items() if method in {'get','post','put','patch','delete','head','options'}]
    scope_counts=collections.Counter(op['x-api-scope'] for _,_,op in operations)
    text=['## Application source and feature progress','',f'As of **{ledger["asOf"]}**. The [app workspace](app/README.md) contains the SDK, frontend and independent API-compatible backend. [PRD](app/PRD.md) · [Detailed ledger](app/contracts/feature-progress.json) · [Validation](app/evidence/validation.json).','',
    'Source acquisition/extraction is separate from editable feature reconstruction and working behavior. Percentages below use explicit counts or accepted milestones; they are not estimates of engineering effort. The original backend source is unavailable.','',
    '| Source / evidence measure | Complete / inventoried | Progress | Meaning |','| --- | ---: | ---: | --- |',
    f'| Published SDK source | {source_equal} / {source_count} files | {100*source_equal/source_count:.0f}% | Exact npm 4.3.1 source bytes; full behavior parity still unqualified |',
    f'| Frontend JavaScript capture | {verified} / {len(scripts)} scripts | {script_progress} | Known scripts in the captured route/asset graph only |',
    f'| Frontend factory extraction | {len(recovered["modules"])} / {len(recovered["modules"])} inventoried variants | {factory_progress} | Extracted factories, not original source files; authenticated/unseen modules unknown |',
    f'| Public developer API contract | {len(operations)} / {len(operations)} documented operations | 100% | Specification captured; native compatibility 0 / {len(operations)} (0%) |',
    '| Original backend source | Not observable | N/A | Implement replacement behavior from API evidence |','',
    '**Feature scoring:** source = contract/dependency mapping, editable logic, and required adapters (3 milestones). Completion = source accepted, successful behavior, failure/auth states, and UI or data consistency checks (4 milestones). A milestone needs evidence to count. Stubs, 501 responses and historical fixture replay earn no feature credit. N/A needs an explicit applicability decision.','',
    '### Backend features','',
    '| Feature family | Static API leads¹ | Native source readiness | Feature completion | Reviewed state |','| --- | ---: | ---: | ---: | --- |']
    for row in ledger['backend']:
        leads=[r for r in candidates if any(r['operation'].split(' ',1)[1].startswith(p) for p in row['candidatePrefixes'])]
        text.append(f'| {row["label"]} | {len(leads)} | {score(row["source"])} | {score(row["completion"])} | {row["note"]} |')
    text+=['',f'¹ {len(candidates)} distinct static operation candidates overall. Family leads overlap, lack confirmed origin bindings and may include privileged/excluded paths; do not sum them or treat them as a full API denominator. The {len(operations)} public developer operations currently have **0% native compatibility qualification**: '+', '.join(f'`{scope}` 0/{n}' for scope,n in sorted(scope_counts.items()))+'.','',
    '### Frontend features','',
    '| Feature family | Reconstructed source readiness | Feature completion | Reviewed state |','| --- | ---: | ---: | --- |']
    for row in ledger['frontend']:text.append(f'| {row["label"]} | {score(row["source"])} | {score(row["completion"])} | {row["note"]} |')
    text+=['','**Excluded (N/A, outside every feature denominator):** '+ '; '.join(ledger['exclusions'])+'.',
    '**Deferred (N/A):** '+'; '.join(ledger['deferred'])+'.','',
    'All app percentages above are generated by `python3 app/scripts/progress.py` from the checked-in evidence and feature ledger. Verify freshness with `python3 app/scripts/progress.py --check`. Source capture is bounded by the recorded snapshot; original frontend source completeness and the full internal API surface remain unknown.']
    return '\n'.join(text)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();block=render()
    outputs={ROOT/'PROGRESS.md':'# Application progress report\n\n'+block.replace('](app/', '](')+'\n',ROOT.parent/'README.md':replace_readme((ROOT.parent/'README.md').read_text(encoding='utf-8'),block)}
    for file,expected in outputs.items():
        if args.check: require(file.read_text(encoding='utf-8')==expected,f'Generated progress is stale: {file}')
        else:file.write_text(expected,encoding='utf-8',newline='\n')
    print('Application source and feature progress '+('verified' if args.check else 'updated'))
if __name__=='__main__':main()
