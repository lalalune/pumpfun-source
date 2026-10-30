import base64,json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
from pathlib import Path
import tempfile,unittest
from unittest import mock
import capture_retry
ROOT=Path(__file__).resolve().parents[2]
class CaptureContextTests(unittest.TestCase):
 def test_string_encoding_option_remains_supported(self):
  response={'context':{'slot':100},'value':None}
  with mock.patch.object(capture_retry,'_archived_rpc',return_value=response):
   self.assertEqual(capture_retry.contextual_rpc('local','getAccountInfo',['pubkey','base64']),response)
 def exercise(self,second,valid):
  payload=(ROOT/'evidence/original/pump/deployed.so').read_bytes()
  requests=[]
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_POST(self):
    request=json.loads(self.rfile.read(int(self.headers['Content-Length'])));requests.append(request)
    if request['method']=='getGenesisHash':result='local-fixture-genesis'
    else:
     slot=100 if len(requests)==1 else second
     result={'context':{'slot':slot},'value':{'owner':'BPFLoader2111111111111111111111111111111111','executable':True,'data':[base64.b64encode(payload).decode(),'base64']}}
    data=json.dumps({'jsonrpc':'2.0','id':1,'result':result}).encode();self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   with tempfile.TemporaryDirectory() as temporary:
    out=Path(temporary)/'capture';url='http://127.0.0.1:'+str(server.server_port)
    if valid:
     capture_retry.capture(url,'fixture','fixture-program',out)
     self.assertEqual((out/'deployed.so').read_bytes(),payload)
     self.assertEqual(json.loads((out/'capture.json').read_text())['context_slots'],[100,second])
    else:
     with self.assertRaises(ValueError):capture_retry.capture(url,'fixture','fixture-program',out)
     self.assertFalse(out.exists())
    self.assertEqual(requests[1]['params'][1]['minContextSlot'],100)
  finally:server.shutdown();server.server_close();thread.join()
 def test_stale_and_invalid_contexts_cannot_publish(self):
  for slot in (99,-1,True,None):
   with self.subTest(slot=slot):self.exercise(slot,False)
 def test_equal_or_newer_contexts_preserve_real_capture_bytes(self):
  for slot in (100,101):self.exercise(slot,True)
