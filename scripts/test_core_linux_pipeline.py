"""Synthetic preparation/provenance tests; no compiler, installer, tracer or network."""
from pathlib import Path
import ast,gzip,hashlib,importlib.util,io,json,os,shutil,sys,tarfile,tempfile,unittest
from unittest import mock
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pipeline_helper',HERE/'core_linux_v144_build.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='pipeline-unit-',dir=HERE)
        self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.process=mock.patch.object(h.subprocess,'run',side_effect=AssertionError('No real subprocess allowed'))
        self.process.start();self.addCleanup(self.process.stop)
        self.fetch=mock.patch.object(h.urllib.request,'urlopen',side_effect=AssertionError('No network allowed'))
        self.fetch.start();self.addCleanup(self.fetch.stop)
        self.count=mock.patch.object(h,'REGISTRY_PACKAGE_COUNT',2);self.count.start();self.addCleanup(self.count.stop)
        self.cargo=self.root/'cargo';self.source=self.root/'source';self.source.mkdir();self.evidence=self.root/'evidence';self.evidence.mkdir()

    def registry(self):
        namespace=h.REGISTRY_NAMESPACES[0];lock=['version = 4\n']
        for name in ['alpha','beta']:
            stem=name+'-1.0.0';files={'Cargo.toml':('[package]\nname="'+name+'"\nversion="1.0.0"\n').encode(),'src/lib.rs':b'// synthetic public source\n'}
            data=io.BytesIO()
            with tarfile.open(fileobj=data,mode='w')as t:
                for path,value in files.items():
                    m=tarfile.TarInfo(stem+'/'+path);m.size=len(value);t.addfile(m,io.BytesIO(value))
            compressed=gzip.compress(data.getvalue(),mtime=0)
            archive=self.cargo/'registry/cache'/namespace/(stem+'.crate');archive.parent.mkdir(parents=True,exist_ok=True);archive.write_bytes(compressed)
            directory=self.cargo/'registry/src'/namespace/stem
            for path,value in files.items():
                p=directory/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(value)
            (directory/'.cargo-ok').write_bytes(b'{"v":1}')
            index=self.cargo/'registry/index'/namespace/'.cache'/name;index.parent.mkdir(parents=True,exist_ok=True);index.write_bytes(b'synthetic index fixture')
            lock+=['[[package]]',f'name = "{name}"','version = "1.0.0"','source = "registry+https://github.com/rust-lang/crates.io-index"',f'checksum = "{hashlib.sha256(compressed).hexdigest()}"','']
        (self.cargo/'registry/index'/namespace/'config.json').write_text('{"dl":"https://static.crates.io/crates"}')
        (self.source/'Cargo.lock').write_text('\n'.join(lock))
        return namespace

    def prepare(self):
        self.registry();return h.prepare_registry_views(self.cargo,self.source,self.evidence)

    def test_prepare_both_views_preserves_all_authentic_bytes_and_lock(self):
        ns=self.registry();before=h.digest(self.source/'Cargo.lock')
        proof=h.prepare_registry_views(self.cargo,self.source,self.evidence)
        self.assertEqual(proof['fetched_namespaces'],[ns]);self.assertEqual(len(proof['copied_views']),3)
        self.assertFalse(proof['symlink_aliases_created']);self.assertFalse(proof['metadata_markers_fabricated'])
        self.assertEqual(h.digest(self.source/'Cargo.lock'),before)
        inventory=h.dependency_inventory(self.cargo,self.source,self.evidence,'before')
        self.assertEqual(len(inventory),2)
        for p in inventory:
            a,b=p['registry_views'];self.assertEqual(a['archive_sha256'],b['archive_sha256']);self.assertEqual(a['files'],b['files'])
        self.assertFalse(any(p.is_symlink()for p in self.cargo.rglob('*')))

    def test_preexisting_complete_two_views_are_checked_without_copy(self):
        self.prepare();proof=h.prepare_registry_views(self.cargo,self.source,self.evidence)
        self.assertEqual(proof['copied_views'],[]);self.assertEqual(set(proof['fetched_namespaces']),set(h.REGISTRY_NAMESPACES))

    def test_inventory_rejects_missing_second_view(self):
        self.registry()
        with self.assertRaisesRegex(ValueError,'both verified'):h.dependency_inventory(self.cargo,self.source,self.evidence,'before')

    def test_bad_host_archive_stops_before_creating_second_view(self):
        ns=self.registry();(self.cargo/'registry/cache'/ns/'alpha-1.0.0.crate').write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'checksum'):h.prepare_registry_views(self.cargo,self.source,self.evidence)
        self.assertFalse((self.cargo/'registry/cache'/h.REGISTRY_NAMESPACES[1]).exists())

    def test_secondary_archive_corruption_is_rejected(self):
        self.prepare();(self.cargo/'registry/cache'/h.REGISTRY_NAMESPACES[1]/'alpha-1.0.0.crate').write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'checksum'):h.dependency_inventory(self.cargo,self.source,self.evidence,'after')

    def test_secondary_source_corruption_is_rejected(self):
        self.prepare();(self.cargo/'registry/src'/h.REGISTRY_NAMESPACES[1]/'alpha-1.0.0/src/lib.rs').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'Unpacked source'):h.dependency_inventory(self.cargo,self.source,self.evidence,'after')

    def test_extra_selected_archive_or_source_is_rejected(self):
        ns=self.registry();(self.cargo/'registry/cache'/ns/'unplanned-1.0.0.crate').write_bytes(b'extra')
        with self.assertRaisesRegex(ValueError,'Archive path set'):h.prepare_registry_views(self.cargo,self.source,self.evidence)

    def test_extra_source_file_is_rejected(self):
        ns=self.registry();(self.cargo/'registry/src'/ns/'alpha-1.0.0/extra.rs').write_bytes(b'extra')
        with self.assertRaisesRegex(ValueError,'Unexpected files'):h.prepare_registry_views(self.cargo,self.source,self.evidence)

    def test_namespace_symlink_alias_is_rejected(self):
        ns=self.registry()
        for kind in ['cache','src','index']:
            (self.cargo/'registry'/kind/h.REGISTRY_NAMESPACES[1]).symlink_to(ns,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'real directories'):h.prepare_registry_views(self.cargo,self.source,self.evidence)

    def test_registry_root_symlinks_are_rejected(self):
        self.registry()
        for relative in ['registry/cache','registry']:
            with self.subTest(relative=relative):
                target=self.cargo/relative;external=self.root/('external-'+relative.replace('/','-'))
                target.rename(external);target.symlink_to(external,target_is_directory=True)
                with self.assertRaisesRegex(ValueError,'real directories'):h.registry_namespace_sets(self.cargo)
                target.unlink();external.rename(target)

    def test_unknown_namespace_is_rejected(self):
        self.registry()
        for kind in ['cache','src','index']:(self.cargo/'registry'/kind/'unplanned-registry').mkdir()
        with self.assertRaisesRegex(ValueError,'Unexpected registry namespace'):h.prepare_registry_views(self.cargo,self.source,self.evidence)

    def test_source_link_is_rejected(self):
        ns=self.registry();p=self.cargo/'registry/src'/ns/'alpha-1.0.0/src/lib.rs';data=p.read_bytes();p.unlink();real=self.root/'real.rs';real.write_bytes(data);p.symlink_to(real)
        with self.assertRaisesRegex(ValueError,'source contains symlink'):h.prepare_registry_views(self.cargo,self.source,self.evidence)

    def test_cargo_bookkeeping_is_recorded_separately_from_public_bytes(self):
        self.prepare();before=h.dependency_inventory(self.cargo,self.source,self.evidence,'before')
        marker=self.cargo/'registry/src'/h.REGISTRY_NAMESPACES[1]/'alpha-1.0.0/.cargo-ok';marker.write_bytes(b'changed synthetic Cargo metadata')
        after=h.dependency_inventory(self.cargo,self.source,self.evidence,'after');self.assertEqual(before,after)
        self.assertNotEqual((self.evidence/'dependency-cargo-metadata-before.json').read_bytes(),(self.evidence/'dependency-cargo-metadata-after.json').read_bytes())

    def sdk(self):
        sdk=self.root/'sdk'
        for name in ['dump','install','objcopy','package','strip']:
            p=sdk/'scripts'/(name+'.sh');p.parent.mkdir(parents=True,exist_ok=True);p.write_text('#!/bin/sh\n# synthetic; never executed\n');p.chmod(0o755)
        return sdk

    def test_sdk_modes_are_verified_without_chmod(self):
        sdk=self.sdk();before=h.tree_hashes(sdk);rows=h.check_sdk_executable_modes(sdk,self.evidence,'unit')
        self.assertEqual(len(rows),5);self.assertTrue(all(r['mode']=='0o755'and r['executable']for r in rows.values()));self.assertEqual(h.tree_hashes(sdk),before)

    def test_sdk_nonexecutable_mode_is_recorded_and_rejected(self):
        sdk=self.sdk();(sdk/'scripts/strip.sh').chmod(0o644)
        with self.assertRaisesRegex(ValueError,'0755'):h.check_sdk_executable_modes(sdk,self.evidence,'unit')
        self.assertEqual(json.loads((self.evidence/'sdk-script-modes-unit.json').read_text())['scripts/strip.sh']['mode'],'0o644')

    def test_sdk_script_symlink_is_rejected(self):
        sdk=self.sdk();(sdk/'scripts/strip.sh').unlink();(sdk/'scripts/strip.sh').symlink_to(sdk/'scripts/install.sh')
        with self.assertRaisesRegex(ValueError,'regular files'):h.check_sdk_executable_modes(sdk,self.evidence,'unit')

    def tracer_attempt(self,code=0,trace=True,success=True,package_status=0):
        attempt=h.Attempt(self.root/'attempt');commands=[]
        tracer=self.root/'fake-strace';tracer.write_bytes(b'synthetic observer fixture, never executed');tracer.chmod(0o755)
        actual_digest=h.digest
        # The real target is Linux /bin/true; tests never read or execute it.
        patch=mock.patch.object(h,'digest',side_effect=lambda p:hashlib.sha256(b'synthetic true fixture').hexdigest()if Path(p)==Path('/bin/true')else actual_digest(p))
        patch.start();self.addCleanup(patch.stop)
        def fake_run(name,command,cwd,env,check=True):
            commands.append((name,command));log=attempt.evidence/'logs'/(name+'.log');log.parent.mkdir(parents=True,exist_ok=True)
            # This deliberately resembles trace output: the helper must not
            # accept its own diagnostic .log instead of a numeric PID file.
            log.write_text('1.0 execve("/bin/true", ["/bin/true"], []) = 0\n')
            if name=='tracer-preflight'and trace:
                prefix=Path(command[command.index('-o')+1]);Path(str(prefix)+'.1234').write_text('1.0 execve("/bin/true", ["/bin/true"], []) = '+('0'if success else'-1 EPERM')+'\n')
            return package_status if name=='tracer-package'else code if name=='tracer-preflight'else 0
        attempt.run=fake_run
        return attempt,tracer,commands

    def test_tracer_absence_does_not_count_compiler_attempt(self):
        attempt=h.Attempt(self.root/'attempt')
        with mock.patch.object(h.shutil,'which',return_value=None),self.assertRaisesRegex(ValueError,'absent'):h.preflight_tracer(attempt,self.source,{})
        self.assertEqual(attempt.state['build_attempts'],0)

    def test_tracer_denied_preflight_records_failure_without_compiler_attempt(self):
        attempt,tracer,_=self.tracer_attempt(code=1,success=False)
        with mock.patch.object(h.shutil,'which',return_value=str(tracer)),self.assertRaisesRegex(ValueError,'compiler not attempted'):h.preflight_tracer(attempt,self.source,{})
        proof=json.loads((attempt.evidence/'tracer-preflight.json').read_text());self.assertEqual(proof['returncode'],1);self.assertEqual(proof['build_attempts'],0)

    def test_tracer_zero_exit_without_pid_trace_is_rejected(self):
        attempt,tracer,_=self.tracer_attempt(trace=False)
        with mock.patch.object(h.shutil,'which',return_value=str(tracer)),self.assertRaisesRegex(ValueError,'compiler not attempted'):h.preflight_tracer(attempt,self.source,{})
        self.assertEqual(json.loads((attempt.evidence/'tracer-preflight.json').read_text())['trace_files'],[])

    def test_tracer_valid_pid_exec_proof_preserves_actual_package_status(self):
        attempt,tracer,commands=self.tracer_attempt(package_status=1)
        with mock.patch.object(h.shutil,'which',return_value=str(tracer)):result=h.preflight_tracer(attempt,self.source,{})
        self.assertEqual(result,tracer);proof=json.loads((attempt.evidence/'tracer-preflight.json').read_text());self.assertTrue(proof['successful_true_exec_recorded']);self.assertEqual(proof['package_query_returncode'],1);self.assertEqual(proof['build_attempts'],0)
        self.assertEqual([n for n,_ in commands],['tracer-version','tracer-package','tracer-preflight'])
        self.assertEqual(proof['command'][-2:],['--','/bin/true']);self.assertIn(h.TRACE_FILTER,proof['command'])

    def test_lifecycle_and_preparation_order_are_present_without_build_command_change(self):
        selector=set(h.TRACE_FILTER.split('=')[1].split(','));self.assertTrue({'fork','vfork','clone','clone3'}<=selector)
        tree=ast.parse((HERE/'core_linux_v144_build.py').read_text());build=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='build')
        calls=[(n.lineno,ast.unparse(n.func),n)for n in ast.walk(build)if isinstance(n,ast.Call)]
        at=lambda name:min(line for line,fn,_ in calls if fn==name)
        self.assertLess(at('preflight_tracer'),at('attempt.download'));self.assertLess(at('check_sdk_executable_modes'),at('attempt.download'))
        fetch=min(line for line,fn,n in calls if fn=='attempt.run'and n.args and isinstance(n.args[0],ast.Constant)and n.args[0].value=='public-locked-fetch')
        self.assertLess(fetch,at('prepare_registry_views'));self.assertLess(at('prepare_registry_views'),at('prepare_compile_inputs'))
        command=next(n.value for n in ast.walk(build)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='command'for t in n.targets))
        frozen=ast.parse('command = ["cargo", "build-sbf", "--manifest-path", str(manifest), "--tools-version", "v1.44", "--offline", "--sbf-sdk", str(sdk), "--sbf-out-dir", str(output / "artifacts"), "--", "--locked", "--offline"]').body[0].value
        self.assertEqual(ast.dump(command),ast.dump(frozen))

if __name__=='__main__':unittest.main(verbosity=2)
