#!/usr/bin/env python3
"""Portable FROZEN1ddb artifact/source/score admission; no compiler, SDK or network."""
import argparse,gzip,importlib.util,json,os,re,stat,subprocess,sys,tempfile,zipfile
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.path.insert(0,str(HERE))
import qualification as q
p=q
M='1ddb12553ccdb4ed45407ffe53f12f4644be172a'
OP='49bf18401f5138b4d0bdb9446d7a3ef1a129509b'
TREE='687251140df8f2b1f4e3bc50185efd191ffd1c2c'
SOURCE='6e061e8785371cbe427c8ff591bc1a35846deafad89b8d922137a6c52c5579b9'
ARCHIVE='4a1e1d7ebd4ffa8911bbf8a9904593d917fc7e798f7911039598c914a8dbc69a'
OPS=('.github/workflows/qualify-pump-macos-v144.yml','reconstruction/pump-main/lanes/current-native-control/pump_current_control.py','reconstruction/pump-main/lanes/current-native-control/README.md')
PASS13='reconstruction/pump-main/checkpoints/completion-pass13-20261030/'

def prepare_reference(a):
    metadata=q.read_json(HERE/'CHECKPOINT.json')
    q.need(metadata['sourceCommit']==M and metadata['controllerCommit']==OP and metadata['run']==41065537974 and metadata['artifactId']==12982692412 and metadata['artifactZip']=={'bytes':2515348,'sha256':ARCHIVE},'frozen hosted/source identity differs')
    manifest=q.read_json(HERE/'MANIFEST.json')
    for rel,row in manifest.items():
        q.need(rel and not rel.startswith('/') and '..' not in Path(rel).parts,'unsafe packet member')
        data=(HERE/rel).read_bytes();q.need(len(data)==row['bytes'] and q.sha(data)==row['sha256'],'packet member differs: '+rel)
    reference=HERE/'reference'
    return reference,q.read_json(reference/'PREFLIGHT.json')

def run(a):
    a.source_base = M
    p.outer(a)
    reference, preflight = prepare_reference(a)
    p.parent(a.repo, OP, M)
    q.need(q.git(a.repo, 'rev-parse', OP+'^{tree}').decode().strip() == TREE, 'operational tree differs')
    q.need(set(q.git(a.repo, 'diff', '--name-only', '--no-renames', M, OP).decode().splitlines()) == set(OPS), 'operator differs beyond three reviewed files')
    ops = p.rows(a.repo, OP, OPS)
    q.need(q.read_json(a.artifact / 'operational-inputs.json') == {'checkout': OP, 'files': ops}, 'operator Git vector differs')
    controller = q.read_json(a.artifact / 'controller-inputs.json')
    q.need(controller['checkout'] == OP and controller['runnerSha256'] == q.sha(q.git_file(a.repo,OP,OPS[1])) and controller['workflowSha256'] == q.sha(q.git_file(a.repo,OP,OPS[0])), 'actual controller/workflow differs')
    q.need(controller['recipe'] == 'identity' and controller['triple'] == 'sbpf-solana-solana' and controller['gitSourceManifest'] == 'program-source-inputs.json' and controller['builderSourceManifest'] == 'source-inputs.json', 'actual control profile differs')
    source_rows = p.rows(a.repo,M,('programs/pump',)); core = p.rows(a.repo,M,p.CORE)
    q.need(len(source_rows) == 135 and len(core) == 215, 'frozen Git inventory count differs')
    q.need(q.read_json(a.artifact/'program-source-inputs.json') == {'base':M,'files':source_rows}, 'full source Git vector differs')
    q.need(q.read_json(a.artifact/'toolchain-source-inputs.json') == {'base':M,'files':core}, 'full core Git vector differs')
    q.HEAD=M; q.SCORER_PATHS=q.discover_scorer_paths(a.repo)
    q.INPUT_PATHS=tuple(dict.fromkeys((*q.SCORER_PATHS,*q.INPUT_PATHS)))
    source,baseline,domain,pins,historical,original=q.frozen_inputs(a.repo,a.original)
    snap=p.snapshot(source)
    q.need(snap['sha256'] == SOURCE and len(snap['files']) == 135, 'actual maintained selection/source aggregate differs')
    selection=q.read_json(a.artifact/'source-selection.json')
    q.need(selection == q.read_json(reference/'source-selection.json') and selection['excludedGitPaths'] == [], 'current selection differs from frozen maintained helper')
    q.need(selection['helper'] == next(r for r in core if r['path']=='reconstruction/harness/source_inputs.py'), 'source-selection helper differs')
    q.need(q.read_json(a.artifact/'preflight-builder-source-inputs.json') == snap, 'preflight source receipt differs')
    staged=q.read_json(reference/'compiled-workspace-inputs.json')
    q.need(len(staged) == 136 and q.read_json(a.artifact/'compiled-workspace-inputs.json') == staged, 'actual staged vector differs from authentic frozen staging')
    p.tar_check(a.artifact/'program-source.tar.gz',{r['path']:{'bytes':r['bytes'],'sha256':r['sha256'],'executable':r['mode']=='100755'} for r in source_rows},{r['path']:r['mode'] for r in source_rows})
    p.tar_check(a.artifact/'compiled-workspace.tar.gz',staged)
    ap=q.read_json(a.artifact/'PREFLIGHT.json')
    expected=dict(preflight,preflightOnly=False)
    q.need(ap == expected, 'native operational source/stage/script preflight differs')
    missing=[name for name in ('build.json','cold-build.log','build.log','source-inputs.json','unstripped.so','candidate.so','cold-target-inputs.json','cargo-fingerprints.json','native-lld-input-before.json','native-lld-input-after.json','tool-inputs-before.json','tool-inputs-after.json','registry-source-inputs.json','registry-source-inputs-after.json','score.json','RESULT.json','link-order-admission.json','link-receipt.json','link.map') if not (a.artifact/name).is_file()]
    if missing or (a.artifact/'FAILURE.json').exists():
        return {'status':'INCOMPLETE_CONTROL_REJECTED','accepted':False,'missing':missing,'failureRecordPresent':(a.artifact/'FAILURE.json').exists(),'sourceBase':M,'operation':OP,'sourceSha256':SOURCE},2
    commands=[json.loads(line) for line in (a.artifact/'commands.jsonl').read_text().splitlines() if line.strip()]
    q.need([x['name'] for x in commands] == ['bootstrap-before','fetch-locked','cold-build','bootstrap-after','score'] and all(x['returncode']==0 for x in commands), 'actual command order/status differs')
    host=q.read_json(a.artifact/'host.json')
    q.need(host['base']==M and host['machine']=='arm64' and host['platform'].startswith('macOS-26.'), 'native host differs')
    downloads=q.read_json(a.artifact/'sdk-downloads.json')
    expected_downloads={'v1.44':'66e20d135fddd70ff519baf7ff320d762957f9aedf93a50e23756db23ad79351','v1.52':'1727dfb31e833ce777d01e70cb4b3cebd26b376bf09d80527f02457d4cf6fd00'}
    q.need(len(downloads)==2 and {r['version']:r['archiveSha256'] for r in downloads}==expected_downloads and all(r['expectedArchiveSha256']==expected_downloads[r['version']] for r in downloads), 'SDK archive pins differ')
    inv=json.loads(q.git_file(a.repo,M,'reconstruction/toolchain/v1.44-macos-inventory.json'))['entries']
    for name in ('bootstrap-before.log','bootstrap-after.log'):
        text=(a.artifact/name).read_text()
        q.need(f'SDK verified (full, {len(inv)} entries)' in text and 'Linux v1.44 sbpf target libraries verified (25 rlibs)' in text, 'full before/after SDK/library guard absent')
    env=controller['documentedEnvironment']
    q.need(env['PUMP_BUILD_SLOTS']=='1' and env['CARGO_BUILD_JOBS']=='2' and env['PYTHONDONTWRITEBYTECODE']=='1' and env['PUMP_OBJDUMP'].endswith('/v1.52/platform-tools/llvm/bin/llvm-objdump'), 'actual inherited environment differs')
    native=q.read_json(a.artifact/'native-lld-input-before.json'); row=inv[native['sdkRelativePath']]
    q.need(row['type']=='file' and native['sha256']==row['sha256'] and native['bytes']==row['bytes'] and int(native['mode'],8)==int(row['mode'],8), 'native LLD inventory differs')
    q.need(re.fullmatch(re.escape(env['PUMP_RECON_HOME'])+r'/toolchains/hybrid144/rust/lib/rustlib/[^/]+/bin/rust-lld',native['path']) and native['resolvedPath'].endswith('/v1.44/platform-tools/'+native['sdkRelativePath']), 'native LLD path/resolution differs')
    sdk=native['resolvedPath'].split('/v1.44/platform-tools/',1)[0]+'/v1.44/platform-tools/'
    rels=['rust/bin/rustc','rust/bin/cargo','llvm/bin/llvm-objcopy']+[r for r in inv if re.fullmatch(r'rust/lib/lib[^/]+\.dylib',r)]
    expected_tools={sdk+r:inv[r]['sha256'] for r in rels}
    expected_tools.update({env['PUMP_RECON_HOME']+'/toolchains/hybrid144/rust/bin/rustc':inv['rust/bin/rustc']['sha256'],env['PUMP_OBJDUMP']:'bc7127fa0f182f4e198b670f6df7f407f54c8c6f25c2e61863d706da0bb35dcd',native['path']:native['sha256']})
    tools=q.read_json(a.artifact/'tool-inputs-before.json')
    q.need(tools==expected_tools and q.read_json(a.artifact/'tool-inputs-after.json')==tools and q.read_json(a.artifact/'native-lld-input-after.json')==native, 'native SDK/analysis/hybrid tools changed or unbound')
    registry=q.read_json(a.artifact/'registry-source-inputs.json')
    q.need(registry and q.read_json(a.artifact/'registry-source-inputs-after.json')==registry, 'registry before/after differs')
    for rel,digest in registry.items():
        q.need(rel and not rel.startswith('/') and '..' not in Path(rel).parts and re.fullmatch('[0-9a-f]{64}',digest), 'invalid registry member')
        if a.registry_source:q.need(q.sha((a.registry_source/rel).read_bytes())==digest,'explicit immutable local registry differs: '+rel)
    build=q.read_json(a.artifact/'build.json')
    q.need(p.recorded_json((a.artifact/'cold-build.log').read_text())==build and build['ok'] is True and build['runtime_valid'] is True and build['stack_warnings']==[] and build['recipe']=='identity' and build['triple']=='sbpf-solana-solana', 'actual build profile/guard differs')
    q.need(q.read_json(a.artifact/'source-inputs.json')==snap and build['source_sha256']==SOURCE, 'actual compiler source differs')
    cold=q.read_json(a.artifact/'cold-target-inputs.json')
    q.need(cold['base']==M and cold['sourceSha256']==SOURCE and cold['targetAbsentBeforeBuild'] is True and cold['dependencyTemplatesAbsent'] is True and cold['toolInputs']==tools, 'cold target/template/tool proof differs')
    raw={}
    for name,key in [('unstripped.so','unstripped_sha256'),('candidate.so','candidate_sha256')]:
        data=(a.artifact/name).read_bytes();q.need(q.sha(data)==build[key], 'actual ELF differs')
        raw[name]={'sha256':q.sha(data),'bytes':len(data),'wholeCapturedOriginalEqual':data==original}
    log=(a.artifact/'build.log').read_text()
    q.need('exceeded max offset' not in log,'stack diagnostic retained')
    fp=q.read_json(a.artifact/'cargo-fingerprints.json')
    for package in ('pump-recovered','pump-token-ext'):
        q.need(re.search(r'(?m)^\s*Compiling '+package+r' v',log) and any('/.fingerprint/'+package+'-' in name for name in fp),'fresh local build/fingerprint absent')
    q.need(fp and all(row.get('rustflags')==['-Zremap-cwd-prefix='] for row in fp.values()),'target compiler flags differ')
    link=p.link_check(a,'.',source,build,native,core)
    baseline_record=q.read_json(a.artifact/'baseline-input.json')
    q.need(baseline_record['path']=='reconstruction/pump-main/baseline/score.json' and baseline_record['sha256']==pins[baseline_record['path']]['sha256'],'historical reporting baseline differs')
    scorer=q.load_scorer(a.repo,a.original,a.output)
    windows,digest=scorer.score_with_hash(a.artifact/'unstripped.so')
    q.need(set(windows)==set(domain) and len(windows)==1035 and digest==build['unstripped_sha256'],'fresh official full census domain/hash differs')
    for key,row in windows.items():q.need(row['bytes']==domain[key] and type(row['raw']) is bool and type(row['normalized']) is bool and (not row['raw'] or row['normalized']),'invalid raw/normalized window record')
    report={'summary':p.summary(windows,{int(k):v for k,v in baseline.items()},digest),'windows':{str(k):v for k,v in windows.items()}}
    q.need(q.read_json(a.artifact/'score.json')==report,'actual full1035 score/summary differs from unchanged official M replay')
    final=q.read_json(a.artifact/'RESULT.json')
    q.need(final['base']==M and final['builderSourceSha256']==SOURCE and final['summary']==report['summary'] and final['unstrippedSha256']==raw['unstripped.so']['sha256'] and final['candidateSha256']==raw['candidate.so']['sha256'],'final source/score/ELF declarations differ')
    q.need(all(final[k] is True for k in ('sourceUnchanged','registrySourceUnchanged','toolInputsUnchanged','coldTarget')) and final['programGitFiles']==135 and final['selectedSourceFiles']==135 and final['workspaceFiles']==136 and final['coreFiles']==215 and final['nativeLld']==native and final['linkOrder']==build['link_order'],'final invariant declarations differ')
    q.need(final['gitSourceManifest']=='program-source-inputs.json' and final['builderSourceManifest']=='source-inputs.json','final source receipt names differ')
    p.emit(a.output,'FRESH-OFFICIAL-SCORE.json',report)
    # Historical corroboration only: neither archive/ELF equality nor this score is forced.
    old=json.loads(q.git_file(a.repo,M,PASS13+'summary.json'))
    old_source=json.loads(q.git_file(a.repo,M,PASS13+'source-inputs.json'))
    old_score=json.loads(gzip.decompress(q.git_file(a.repo,M,PASS13+'score.json.gz')))
    old_rows=old_source['files'];old_by={r['path']:r for r in old_rows};new_by={r['path']:r for r in snap['files']}
    q.need(len(old_rows)==133 and old_source['sha256']==old['source_sha256'] and all(new_by.get(k)==v for k,v in old_by.items()),'historical pass13 source comparison differs')
    q.need(set(map(int,old_score['windows']))==set(domain),'historical pass13 window domain differs')
    history={'label':'separate historical133-input measurement, never expected current output','sourceSha256':old['source_sha256'],'unstrippedSha256':old['unstripped_sha256'],'strippedSha256':old['stripped_sha256'],'retainedSourceFiles':len(old_rows),'additionalCurrentSelectedPaths':sorted(set(new_by)-set(old_by)),'currentUnstrippedEqualsHistorical':raw['unstripped.so']['sha256']==old['unstripped_sha256'],'currentStrippedEqualsHistorical':raw['candidate.so']['sha256']==old['stripped_sha256'],'normalizedChangedStarts':[hex(k) for k in sorted(windows) if windows[k]['normalized']!=old_score['windows'][str(k)]['normalized']],'rawChangedStarts':[hex(k) for k in sorted(windows) if windows[k]['raw']!=old_score['windows'][str(k)]['raw']]}
    return {'status':'AUTHENTIC_FROZEN_SINGLE_CONTROL_ACCEPTED','accepted':True,'run':41065537974,'sourceBase':M,'operation':OP,'operationalTree':TREE,'sourceSha256':SOURCE,'programGitFiles':135,'selectedSourceFiles':135,'workspaceFiles':136,'coreFiles':215,'rawFiles':raw,'summary':report['summary'],'unmatched':[hex(k) for k in sorted(windows) if not windows[k]['normalized']],'scorerClosure':list(q.SCORER_PATHS),'scorerBindings':pins,'link':link,'nativeLld':native,'registryFiles':len(registry),'physicalLocalRegistry':'PASS' if a.registry_source else 'NOT RUN; explicit local registry root absent','physicalNativeMacSdk':'NOT RUN locally; recorded full SDK checks and pinned archive/tool/LLD bindings admitted','historicalPass13':history,'compilerSdkLinkerExecutionsByVerifier':0,'networkPolicy':'Git reads use --no-lazy-fetch; verifier makes no network calls','limits':'One actual frozen single-source control. No candidate, source gain, latest-main, runtime or whole meaningful-ELF equality claim.'},0


def unpack_artifact(archive,root):
    metadata=q.read_json(HERE/'CHECKPOINT.json')
    q.need(archive.stat().st_size==metadata['artifactZip']['bytes'] and q.sha(archive.read_bytes())==ARCHIVE,'authentic external ZIP absent or different')
    seen={}
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            name=member.filename
            q.need(name and not name.startswith('/') and '\\' not in name and all(x not in ('','.','..') for x in name.split('/')),'unsafe ZIP member')
            q.need(not member.is_dir() and name not in seen and not stat.S_ISLNK(member.external_attr>>16),'ZIP type/duplicate differs')
            data=z.read(member);seen[name]={'bytes':len(data),'sha256':q.sha(data)}
            q.need(seen[name]==metadata['artifactMembers'].get(name),'ZIP member differs: '+name)
            dst=root/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
    q.need(seen==metadata['artifactMembers'],'ZIP complete member set differs')


def sdk_check(root,inventory):
    observed={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() or p.is_symlink()}
    q.need(observed==set(inventory),'explicit SDK file/symlink set differs')
    for rel,row in inventory.items():
        path=root/rel
        if row['type']=='symlink':q.need(path.is_symlink() and os.readlink(path)==row['target'],'explicit SDK symlink differs: '+rel)
        else:q.need(path.is_file() and not path.is_symlink() and path.stat().st_size==row['bytes'] and q.sha(path.read_bytes())==row['sha256'] and stat.S_IMODE(path.stat().st_mode)==int(row['mode'],8),'explicit SDK file differs: '+rel)
    return {'status':'PASS','entries':len(inventory)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True,help='Local public repository Git object store containing exact M/OP and the captured original; HEAD need not be M')
    parser.add_argument('--artifact',type=Path,required=True,help='External authentic ZIP, API SHA256 fixed by this checkpoint')
    parser.add_argument('--registry-root',type=Path,help='Optional explicit Cargo registry/src; supplied missing/changed bytes fail')
    parser.add_argument('--sdk-root',type=Path,help='Optional explicit native v1.44 platform-tools; full inventory checked')
    parser.add_argument('--report',type=Path,help='Optional NEW JSON report; existing output refused')
    args=parser.parse_args()
    try:
        q.need(args.report is None or not args.report.exists(),'report output already exists')
        with tempfile.TemporaryDirectory(prefix='pump-frozen-1ddb-') as scratch:
            temp=Path(scratch);artifact=temp/'artifact';artifact.mkdir();output=temp/'analysis';output.mkdir()
            unpack_artifact(args.artifact,artifact)
            options=SimpleNamespace(repo=args.repo,artifact=artifact,archive=args.artifact,archive_sha256=ARCHIVE,original=args.repo/'evidence/original/pump/deployed.so',output=output,registry_source=args.registry_root)
            result,code=run(options)
            if code:
                print(json.dumps(result,sort_keys=True),file=sys.stderr);return code
            metadata=q.read_json(HERE/'CHECKPOINT.json')
            q.need(result['rawFiles']=={'unstripped.so':metadata['unstripped'],'candidate.so':metadata['stripped']},'checkpoint raw output declarations differ')
            q.need(all(result[k]==metadata[k] for k in ('sourceSha256','programGitFiles','selectedSourceFiles','workspaceFiles','coreFiles')) and result['unmatched']==metadata['remaining'],'checkpoint source/count/membership declarations differ')
            q.need(all(result['summary'][k]==value for k,value in metadata['summary'].items()),'checkpoint score declaration differs')
            # Current verifier uses the exact frozen M Git inputs. A repository's
            # current working tree / HEAD is never a source or helper fallback.
            literal_root=output/'scorer-replay';capture=literal_root/'evidence/original/pump/deployed.so';capture.parent.mkdir(parents=True);capture.symlink_to(options.original.resolve())
            analyzer=literal_root/'scripts/analyze.py';analyzer.parent.mkdir();analyzer.write_bytes(q.git_file(args.repo,M,'scripts/analyze.py'))
            spec=importlib.util.spec_from_file_location('frozen_literal_closure',HERE/'literal_closure.py');literal=importlib.util.module_from_spec(spec);spec.loader.exec_module(literal)
            result['literalClosure']=literal.verify_literal(literal_root,artifact/'candidate.so')
            inventory=json.loads(q.git_file(args.repo,M,'reconstruction/toolchain/v1.44-macos-inventory.json'))['entries']
            result['nativeSdkPhysicalQualification']=sdk_check(args.sdk_root,inventory) if args.sdk_root else {'status':'NOT RUN','reason':'No explicit native SDK root supplied; recorded full SDK/archive/tool/LLD qualification is separate.'}
            result['limits']='FROZEN1ddb only. External authentic ZIP required; Git/offline objects required, not a no-Git claim. No compiler, SDK execution, new runtime, source gain, mechanism, current/latest-main or full original ELF equality claim.'
            # Hosted-run paths are used internally for exact receipt validation,
            # then omit them from the portable public report.
            result['nativeLld']={k:v for k,v in result['nativeLld'].items() if k not in ('path','resolvedPath')}
            result['verifierSha256']=q.sha(Path(__file__).read_bytes())
            if args.report:
                with args.report.open('x') as stream:json.dump(result,stream,sort_keys=True,indent=2);stream.write('\n')
            print(json.dumps({'ok':True,'checkpoint':M,'normalized':result['summary']['normalized'],'raw':result['summary']['raw'],'total':result['summary']['total'],'unmatched':result['unmatched'],'physicalRegistry':result['physicalLocalRegistry'],'nativeSdkPhysicalQualification':result['nativeSdkPhysicalQualification']},sort_keys=True))
            return 0
    except (OSError,ValueError,KeyError,TypeError,subprocess.CalledProcessError,zipfile.BadZipFile) as error:
        print(json.dumps({'ok':False,'error':str(error)}),file=sys.stderr);return 1



if __name__=='__main__':raise SystemExit(main())
