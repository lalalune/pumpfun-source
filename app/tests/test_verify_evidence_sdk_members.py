import base64,hashlib,io,json,pathlib,shutil,subprocess,sys,tarfile,tempfile,unittest
class SdkArchiveIdentity(unittest.TestCase):
    def test_duplicate_source_members_are_not_an_unambiguous_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            for folder in ['scripts','evidence/web','evidence/sdk','packages/sdk/src']:(root/folder).mkdir(parents=True)
            script=root/'scripts/verify-evidence.py';shutil.copyfile(pathlib.Path(__file__).resolve().parents[1]/'scripts/verify-evidence.py',script)
            (root/'evidence/web/manifest.json').write_text('{"records":[]}')
            for name in ['api-probes.json','source-map-probes.json']:(root/'evidence'/name).write_text('[]')
            (root/'packages/sdk/src/index.ts').write_bytes(b'export {};')
            archive=root/'evidence/sdk/pump-sdk-4.3.1.tgz'
            with tarfile.open(archive,'w:gz') as tar:
                package_meta = json.dumps({'name':'@pump-fun/pump-sdk','version':'4.3.1'}).encode('utf-8')
                (root/'packages/sdk/package.json').write_bytes(package_meta)
                identity = tarfile.TarInfo('package/package.json'); identity.size = len(package_meta)
                tar.addfile(identity, io.BytesIO(package_meta))
                for _ in range(2):
                    item=tarfile.TarInfo('package/src/index.ts');item.size=10;tar.addfile(item,io.BytesIO(b'export {};'))
            integrity='sha512-'+base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode()
            (root/'evidence/sdk/registry.json').write_text(json.dumps({'name':'@pump-fun/pump-sdk','version':'4.3.1','dist':{'integrity':integrity}}))
            for flags in [[],['-O']]:
                result=subprocess.run([sys.executable,*flags,str(script)],capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0);self.assertIn('Duplicate SDK source',result.stderr)
