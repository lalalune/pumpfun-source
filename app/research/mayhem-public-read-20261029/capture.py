"""One source-authorized anonymous GET, no redirect/cookie handler or retry."""
from pathlib import Path
import datetime, hashlib, json, urllib.request, urllib.error

root=Path(__file__).resolve().parent
assert not (root/'RESPONSE.json').exists(), 'Never silently repeat this bounded read'
trace=json.loads((root/'SOURCE-TRACE.json').read_text())
url=trace['plannedRead']['url']
assert url=='https://frontend-api-v3.pump.fun/coins/mayhem-mode?limit=1'
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None
headers={'Accept':'application/json','X-Pump-Source':'WEB','X-Pump-Platform':'web'}
request=urllib.request.Request(url,method='GET',headers=headers)
opener=urllib.request.build_opener(NoRedirect())
record={'requestedUrl':url,'method':'GET','requestHeaders':headers,'startedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'maxResponseBytes':1048576,'redirectsAllowed':False,'retries':0,'cookiesSent':False,'authorizationSent':False,'sourceTraceSha256':hashlib.sha256((root/'SOURCE-TRACE.json').read_bytes()).hexdigest()}
try:
    try:
        response=opener.open(request,timeout=25)
    except urllib.error.HTTPError as error:
        response=error
    with response:
        kept=[(name,value) for name,value in response.headers.items() if name.lower() not in {'set-cookie','set-cookie2'}]
        omitted=[name for name in response.headers.keys() if name.lower() in {'set-cookie','set-cookie2'}]
        body=response.read(record['maxResponseBytes']+1)
        truncated=len(body)>record['maxResponseBytes']
        if truncated:body=body[:record['maxResponseBytes']]
        (root/'body.bin').write_bytes(body)
        record.update({'status':response.status,'responseUrl':response.geturl(),'headers':kept,'omittedCookieHeaderNames':omitted,'headerRepresentation':'http.client parsed header values, cookie fields omitted; not raw wire bytes','bodyPath':'body.bin','retainedBodyBytes':len(body),'retainedBodySha256':hashlib.sha256(body).hexdigest(),'truncated':truncated})
        try:
            data=json.loads(body.decode('utf-8'))
            record['jsonSummary']={'type':type(data).__name__,'rows':len(data) if isinstance(data,list) else None,'firstRowFields':sorted(data[0]) if isinstance(data,list) and data and isinstance(data[0],dict) else None}
        except (UnicodeDecodeError,json.JSONDecodeError):
            record['jsonSummary']=None
except (OSError,urllib.error.URLError) as error:
    record['transportError']={'type':type(error).__name__,'message':str(error)}
finally:
    record['finishedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    record['collectorSha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (root/'RESPONSE.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({key:record[key] for key in ['requestedUrl','status','retainedBodyBytes','retainedBodySha256','truncated','jsonSummary','transportError'] if key in record},indent=2))
