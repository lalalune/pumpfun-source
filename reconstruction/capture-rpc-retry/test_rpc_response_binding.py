import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
import unittest
from unittest.mock import patch
import capture_retry
class RpcEnvelopeTests(unittest.TestCase):
 def exercise(self,envelope,valid):
  requests=[]
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_POST(self):
    requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
    data=json.dumps(envelope).encode();self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   with patch.object(capture_retry.module.time,'sleep'):
    if valid:self.assertEqual(capture_retry.module.rpc('http://127.0.0.1:'+str(server.server_port),'getSlot',[]),42)
    else:
     with self.assertRaises(AssertionError):capture_retry.module.rpc('http://127.0.0.1:'+str(server.server_port),'getSlot',[])
   self.assertEqual(len(requests),1 if valid else 6)
   self.assertTrue(all(r['id']==1 and r['jsonrpc']=='2.0' for r in requests))
  finally:server.shutdown();server.server_close();thread.join()
 def test_wrong_missing_boolean_ids_and_protocol_rejected(self):
  for response in ({'jsonrpc':'2.0','id':2,'result':42},{'jsonrpc':'2.0','id':True,'result':42},{'jsonrpc':'2.0','result':42},{'jsonrpc':'1.0','id':1,'result':42}):
   with self.subTest(response=response):self.exercise(response,False)
 def test_matching_numeric_id_and_protocol_remain_valid(self):
  for identifier in (1,1.0):self.exercise({'jsonrpc':'2.0','id':identifier,'result':42},True)
