import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import integrate


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.base=self.crate('base');self.part=self.crate('part')
        self.scope=patch.object(integrate,'SC',self.root/'reconstruction');self.scope.start();self.addCleanup(self.scope.stop)

    def crate(self,name):
        path=self.root/name; (path/'src').mkdir(parents=True)
        (path/'Cargo.toml').write_text('[package]\nname="fixture"\n');(path/'Cargo.lock').write_text('version = 3\n')
        (path/'src/lib.rs').write_text('pub fn same() {}\n')
        return path

    def test_preserves_order_and_resolves_override(self):
        out,base,parts=integrate.preflight('trial',self.base,[f'b={self.part}',f'a={self.base}'],[f'b={self.base}'])
        self.assertEqual([p[0] for p in parts],['b','a'])
        self.assertEqual(parts[0][2],base)
        self.assertFalse(out.exists())

    def test_invalid_labels_duplicates_and_overrides(self):
        bad=[('../escape',[],[]),('trial',[f'../x={self.part}'],[]),('trial',['missing-equals'],[]),
             ('trial',[f'x={self.part}',f'x={self.base}'],[]),('trial',[],[f'x={self.base}']),
             ('trial',[f'x={self.part}'],[f'x={self.base}',f'x={self.part}']),('trial',['x='],[])]
        for name,parts,bases in bad:
            with self.subTest(parts=parts,bases=bases),self.assertRaises(ValueError):
                integrate.preflight(name,self.base,parts,bases)

    def test_all_inputs_checked_before_output_is_touched(self):
        for existing in (False, True):
            with self.subTest(existing=existing):
                name = 'existing' if existing else 'fresh'
                output=integrate.SC/'integ'/name
                sentinel=output/'keep'
                if existing:
                    output.mkdir(parents=True);sentinel.write_text('previous')
                args=['integrate','--name',name,'--base-src',str(self.base),'--part',f'good={self.part}','--part',f'bad={self.root / "absent"}','--no-build']
                with patch('sys.argv',args),contextlib.redirect_stderr(io.StringIO()),patch.object(integrate.shutil,'copytree') as copy:
                    with self.assertRaises(SystemExit) as caught:integrate.main()
                    copy.assert_not_called()
                self.assertEqual(caught.exception.code,2)
                if existing:
                    self.assertEqual(sentinel.read_text(),'previous')
                else:
                    self.assertFalse((integrate.SC/'integ').exists())

    def test_source_and_output_overlap_in_both_directions(self):
        for source in [integrate.SC/'integ/trial',integrate.SC/'integ/trial/input',integrate.SC]:
            with self.subTest(source=source),self.assertRaisesRegex(ValueError,'overlaps'):
                integrate.preflight('trial',source,[],[])

    def test_missing_manifest_lock_and_src_are_reported(self):
        for required in ['Cargo.toml','Cargo.lock','src']:
            source=self.crate('missing-'+required.replace('.','-'))
            path=source/required
            if path.is_dir(): (path/'lib.rs').unlink();path.rmdir()
            else:path.unlink()
            with self.assertRaises(ValueError):integrate.preflight('trial',source,[],[])

    def test_real_no_build_composition_of_equal_snapshots(self):
        args=['integrate','--name','trial','--base-src',str(self.base),'--part',f'equal={self.part}','--no-build']
        with patch('sys.argv',args),contextlib.redirect_stdout(io.StringIO()):integrate.main()
        self.assertEqual((integrate.SC/'integ/trial/src/src/lib.rs').read_text(),'pub fn same() {}\n')
        self.assertTrue((integrate.SC/'integ/trial/report.json').is_file())


if __name__=='__main__':unittest.main()
