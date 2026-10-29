import sys,pathlib,json,hashlib,os,tempfile
stage=pathlib.Path('/workspace/pump-app-prize-page-staging');app=pathlib.Path('/workspace/pump-app-leaderboard-navigation/app');mode=sys.argv[1]
assert mode in ('baseline','candidate') and len(sys.argv)==2
for row in json.loads((stage/'SOURCE-SWAP.json').read_bytes()):
 target=app/row['path'];old=target.read_bytes();digest=hashlib.sha256(old).hexdigest();assert digest in (row['baselineSha256'],row['candidateSha256']),(target,digest)
 data=pathlib.Path(row[mode]).read_bytes();assert hashlib.sha256(data).hexdigest()==row[mode+'Sha256']
 fd,name=tempfile.mkstemp(prefix='.prize-source-',dir=target.parent)
 with os.fdopen(fd,'wb') as f:f.write(data)
 os.replace(name,target)
 print(json.dumps({'mode':mode,'path':row['path'],'sha256':hashlib.sha256(data).hexdigest()}))
