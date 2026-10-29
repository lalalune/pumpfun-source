import base64,hashlib,io,json,shutil,subprocess,sys,tarfile,tempfile,unittest
from pathlib import Path
class ByteCountVerification(unittest.TestCase):
    def test_declared_byte_counts_are_checked_even_with_matching_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name in ('scripts','evidence/web/objects','evidence/sdk','packages/sdk/src'):
                (root/name).mkdir(parents=True)
            script=root/'scripts/verify-evidence.py'
            shutil.copyfile(Path(__file__).resolve().parents[1]/'scripts/verify-evidence.py',script)
            body=b'captured';(root/'evidence/web/objects/item').write_bytes(body)
            record={'path':'evidence/web/objects/item','sha256':hashlib.sha256(body).hexdigest()}
            for name in ('api-probes.json','source-map-probes.json'):
                (root/'evidence'/name).write_text('[]',encoding='utf-8')
            source=b'export {};';(root/'packages/sdk/src/index.ts').write_bytes(source)
            archive=root/'evidence/sdk/pump-sdk-4.3.1.tgz'
            with tarfile.open(archive,'w:gz') as tar:
                package_meta = json.dumps({'name':'@pump-fun/pump-sdk','version':'4.3.1'}).encode('utf-8')
                (root/'packages/sdk/package.json').write_bytes(package_meta)
                identity = tarfile.TarInfo('package/package.json'); identity.size = len(package_meta)
                tar.addfile(identity, io.BytesIO(package_meta))
                member=tarfile.TarInfo('package/src/index.ts');member.size=len(source)
                tar.addfile(member,io.BytesIO(source))
            integrity='sha512-'+base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode()
            (root/'evidence/sdk/registry.json').write_text(json.dumps({'name':'@pump-fun/pump-sdk','version':'4.3.1','dist':{'integrity':integrity}}),encoding='utf-8')
            manifest=root/'evidence/web/manifest.json'
            for flags in ([],['-O']):
                for count in (len(body),None,len(body)+1,-1,True,'8'):
                    with self.subTest(flags=flags,count=count):
                        row=dict(record)
                        if count is not None:row['bytes']=count
                        manifest.write_text(json.dumps({'records':[row]}),encoding='utf-8')
                        result=subprocess.run([sys.executable,*flags,str(script)],capture_output=True)
                        if count is None or type(count) is int and count==len(body):
                            self.assertEqual(result.returncode,0,result.stderr)
                        else:
                            self.assertNotEqual(result.returncode,0)
                            self.assertIn(b'byte count mismatch',result.stderr)
