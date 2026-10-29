import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import {
  openCorpus, findNodes, exactlyOne, objectProperty, literal, propertyName, sha256,
} from '../source.mjs';

const defaultRoot = fileURLToPath(new URL('../../../', import.meta.url));
const packetPath = 'contracts/original-create-video-upload.json';
const contexts = {
  create: [734638, '89ce7de3b9bad421.js'],
  media: [586090, '6a1606765ef3e83e.js'],
  classifier: [807757, '6a1606765ef3e83e.js'],
  metadata: [778435, '1147ad0a1bf513f9.js'],
  resolvedMetadata: [421159, '1147ad0a1bf513f9.js'],
  client: [759257, '1e479323ffe53c14.js'],
  origins: [503630, '1e479323ffe53c14.js'],
  transport: [30181, '01ad4f413e529b60.js'],
  contract: [402030, '2b47dd0b38a1608f.js'],
  contractClient: [898661, '2b47dd0b38a1608f.js'],
  videoRoute: [717721, '2b47dd0b38a1608f.js'],
  authContext: [574472, '1e479323ffe53c14.js'],
  selectorLoader: [320853, '01f240a1f9100e9d.js'],
  selector: [658259, '762f0784b7be61c0.js'],
};

function exact(factory, scope, text, label) {
  const matches = findNodes(scope, (node) => factory.text(node).replace(/;$/, '') === text);
  // An expression and its wrapping ExpressionStatement may differ only by a
  // trailing semicolon. Keep the expression, with its actual original range.
  return exactlyOne(matches.length > 1 ? matches.filter((n) => n.type !== 'ExpressionStatement') : matches, label);
}

export async function recover(appRoot = defaultRoot) {
  const corpus = await openCorpus(appRoot);
  const html = await corpus.capture('evidence/web/objects/5e15667ed36cac85');
  assert.equal(html.record.url, 'https://pump.fun/create');
  const scripts = new Set([...html.text.matchAll(/<script[^>]+src="([^"]+)"/g)].map((m) => m[1]));
  const loader = await corpus.factory(320853, { source: 'evidence/web/objects/01f240a1f9100e9d.js' });
  assert.ok(scripts.has(new URL(loader.provenance.url).pathname));
  const chunk = exactlyOne(findNodes(loader.node, (n) => n.type === 'StringLiteral' &&
    n.value.startsWith('static/immutable/chunks/')), 'selector lazy chunk');
  assert.equal(chunk.value, 'static/immutable/chunks/3r6p9e97ury3w.js');
  const allowedScripts = new Set([...scripts, `/_next/${chunk.value}`]);
  const factories = {};
  for (const [name, [id, basename]] of Object.entries(contexts)) {
    const factory = await corpus.factory(id, { source: `evidence/web/objects/${basename}` });
    const routeScripts = name === 'selector' ? allowedScripts : scripts;
    assert.ok(routeScripts.has(new URL(factory.provenance.url).pathname), `${name}: not in Create route closure`);
    const choices = new Set(corpus.index.modules.flatMap((variant) => variant.ids.includes(id)
      ? variant.origins.filter((o) => routeScripts.has(new URL(o.url).pathname))
        .map((o) => `${variant.sha256}:${o.source}:${o.start}:${o.end}`) : []));
    assert.deepEqual(choices, new Set([`${factory.provenance.sha256}:${factory.provenance.source}:${factory.node.start}:${factory.node.end}`]));
    factories[name] = factory;
  }
  const witnesses = [];
  function used(name, scope, text, label) {
    const f = factories[name];
    const node = exact(f, scope ?? f.node, text, label);
    witnesses.push({ ...f.witness(node, label), astType: node.type });
    return node;
  }
  const create = factories.create;
  used('create', null, 'e.A(320853).then(e=>({default:e.FileDropzoneInner}))', 'Create lazily resolves selector export');
  used('selectorLoader', null, 'm(658259)', 'lazy bridge resolves selector factory');
  used('selectorLoader', null, '["static/immutable/chunks/3r6p9e97ury3w.js"].map(m=>t.l(m))', 'lazy bridge loads authenticated selector chunk');
  used('create', null, 'onDrop:e=>er(e[0])', 'file selector passes first File to page handler');
  used('create', null, 'handleFileUpload:D', 'hook exposes actual handler');
  const selectorCall = exactlyOne(findNodes(create.node, (n) => n.type === 'CallExpression' &&
    n.arguments[0]?.name === 'K' && n.arguments[1]?.type === 'ObjectExpression' &&
    n.arguments[1].properties.some((p) => propertyName(p.key) === 'onDrop' && create.text(p.value) === 'e=>er(e[0])')), 'actual media selector call');
  assert.equal(create.text(objectProperty(selectorCall.arguments[1], 'isLoggedIn')), '!!eL');
  witnesses.push({ ...create.witness(selectorCall, 'actual media selector receives wallet-derived login flag'), astType: selectorCall.type });
  used('selector', null, 'T=void 0===w||w', 'selector login flag default');
  used('selector', null, 'S=void 0!==h&&h||!T', 'selector disables click when login flag false');
  used('selector', null, 'L=!T', 'selector disables drag when login flag false');
  used('selector', null, '{onDrop:v,onDropRejected:g,accept:b,maxFiles:C,noClick:S,noDrag:L,children:u}', 'selector forwards login-derived admission props');
  used('selector', null, 'e=>{e.preventDefault(),e.stopPropagation(),j?.()}', 'logged-out button invokes supplied wallet UI callback');
  const request = exactlyOne(findNodes(create.node, (n) => n.type === 'CallExpression' &&
    n.arguments[0]?.type === 'StringLiteral' && n.arguments[0].value === 'GET /videos/get-signed-url'), 'signed video request');
  const handler = exactlyOne(findNodes(create.node, (n) => n.type === 'VariableDeclarator' &&
    n.id.name === 'D' && n.init?.type === 'ArrowFunctionExpression' &&
    n.start < request.start && n.end > request.end), 'actual media handler');
  const video = exactlyOne(findNodes(handler, (n) => n.type === 'IfStatement' &&
    create.text(n.test) === '"video"===i'), 'actual video branch');
  used('create', handler, 'await (0,eY.x)(e)', 'selected File passed to classifier');
  used('create', handler, 'if(!r)throw Error("Invalid file type")', 'unclassified file rejects');
  used('create', handler, 'r.split("/")[0]', 'category from classifier result');
  used('create', handler, 'r.split("/")[1]', 'extension from classifier result');
  used('create', video, '(0,et.j)()', 'request uses website client j');
  const options = request.arguments[1];
  const extension = objectProperty(objectProperty(options, 'query'), 'extension');
  assert.equal(extension.type, 'Identifier');
  assert.equal(extension.name, 'l');
  assert.equal(literal(objectProperty(options, 'credentials')), 'include');
  assert.equal(literal(objectProperty(options, 'throwHttpErrors')), false);
  assert.equal(literal(objectProperty(objectProperty(options, 'headers'), 'Content-Type')), 'application/json');
  witnesses.push({ ...create.witness(request, 'credentialed signed video request'), astType: request.type });
  used('create', video, 'if(!r.ok)throw Error(`Failed to get signed URL: ${r.statusText}`)', 'non-ok presign response rejects');
  used('create', video, 'r=c.url', 'presign payload handed to uploader');
  const promise = exactlyOne(findNodes(video, (n) => n.type === 'NewExpression' && n.callee.name === 'Promise'), 'actual upload promise');
  used('create', promise, 'new XMLHttpRequest', 'browser XHR constructed');
  const open = used('create', promise, 's.open("POST",r.url,!0)', 'POST to returned provider URL');
  const fields = used('create', promise, 'Object.entries(r.fields).forEach(([e,t])=>{console.log("Adding form field:",e),n.append(e,t)})', 'append all returned provider fields');
  used('create', promise, 'new FormData', 'multipart body constructed');
  const file = used('create', promise, 'n.append("file",e)', 'append original selected File');
  const send = used('create', promise, 's.send(n)', 'send multipart body');
  const load = used('create', promise, 's.onload=()=>{console.log("XHR upload complete, status:",s.status),s.status>=200&&s.status<300?t(s.response):a(Error(`Upload failed with status ${s.status}`))}', '2xx resolves; other upload statuses reject');
  used('create', promise, 's.onerror=()=>{console.error("XHR upload error"),a(Error("Network error occurred during upload"))}', 'network error rejects');
  used('create', promise, 's.onabort=()=>{console.error("XHR upload aborted"),a(Error("Upload was aborted"))}', 'abort event rejects');
  used('create', promise, 's.upload.onprogress=e=>{if(e.lengthComputable){let t=e.loaded/e.total*100;console.log("Upload progress event:",t),i(t)}}', 'computable progress only');
  used('create', promise, '{cancel:()=>s.abort()}', 'executor returns cancel object, not the promise value');
  assert.equal(findNodes(promise, (n) => n.type === 'AssignmentExpression' &&
    n.left.type === 'MemberExpression' && propertyName(n.left.property) === 'withCredentials').length, 0);
  assert.equal(findNodes(promise, (n) => n.type === 'AssignmentExpression' &&
    n.left.type === 'MemberExpression' && propertyName(n.left.property) === 'timeout').length, 0);
  assert.equal(findNodes(promise, (n) => n.type === 'CallExpression' &&
    n.callee.type === 'MemberExpression' && propertyName(n.callee.property) === 'setRequestHeader').length, 0);
  const uri = used('create', video, 'eX.z+"videos/"+c.filename', 'display URI derives from signed-response filename');
  const filename = used('create', video, 'u(c.filename)', 'store filename after successful provider upload');
  used('create', video, 'x(d)', 'store derived video display URI');
  used('create', video, 'v(!0)', 'mark video uploaded after provider success');
  used('create', video, 'g(!1)', 'clear uploading before thumbnail extraction');
  const thumbnails = used('create', video, 'await (0,eY.b)(e,3)', 'thumbnail extraction happens after provider upload');
  assert.ok(request.end < promise.start && open.start < fields.start && fields.end < file.start &&
    file.end < send.start && promise.end < uri.start && filename.end < thumbnails.start);
  used('create', handler, 'catch(e){throw console.error("Error handling file upload:",e),e}', 'handler logs and rethrows failure');
  used('create', create.node, 'L=(0,m.useRef)(null)', 'returned XHR ref initialized null');
  used('create', create.node, 'xhrRef:L', 'XHR ref returned from hook');
  assert.equal(findNodes(handler, (n) => n.type === 'AssignmentExpression' &&
    n.left.type === 'MemberExpression' && create.text(n.left) === 'L.current').length, 0);
  used('create', create.node, 'videoFileName:d', 'hook result exposes stored filename');
  const pageState = exactlyOne(findNodes(create.node, (n) => n.type === 'ObjectPattern' &&
    n.properties.some((p) => propertyName(p.key) === 'videoFileName' && p.value?.name === 'M')), 'page media-state destructuring');
  witnesses.push({ ...create.witness(pageState, 'page destructuring retains filename alias M'), astType: pageState.type });
  assert.equal(objectProperty({ properties: pageState.properties }, 'handleFileUpload').name, 'er');

  const metadataCalls = findNodes(create.node, (n) => n.type === 'CallExpression' &&
    ['0,tl.f', '0,to.f'].includes(create.text(n.callee)));
  assert.equal(metadataCalls.length, 2);
  for (const call of metadataCalls) {
    const resolved = create.text(call.callee) === '0,tl.f';
    const data = resolved ? objectProperty(call.arguments[0], 'metadata') : call.arguments[0];
    for (const [field, variable] of [['video', 'O'], ['videoUploaded', 'q'], ['videoFileName', 'M'], ['imageIpfsHash', 'd']]) {
      assert.equal(objectProperty(data, field).name, variable);
    }
    witnesses.push({ ...create.witness(call, resolved ? 'resolved-mint metadata caller' : 'direct metadata caller'), astType: call.type });
  }
  used('create', null, 'm=e.preResolvedMint,u=e.metadata,x=e.metadataUri', 'resolved metadata result retained by caller');
  used('create', null, 'u=e.metadata,x=e.metadataUri', 'direct metadata result retained by caller');
  used('create', create.node, 'if(!e)throw Error("Connect your wallet and sign in to create a coin")', 'submission validator requires decoded context value');
  used('create', create.node, 'if(s&&!o)throw Error("Video not uploaded yet")', 'submission requires uploaded video state');
  used('create', create.node, 'if(o&&2!==l&&(!c||!c.length))throw Error("Please select a thumbnail")', 'submission thumbnail guard');
  used('create', create.node, 'if(s&&s.size>eX.O.VIDEO)throw Error("Video too large: it must be less than 10 megabytes")', 'submission size guard, not a pre-upload guard');
  used('create', create.node, '{decodedJwt:eD}=(0,n.F)()', 'submission gets decoded value from existing context');
  used('authContext', null, '()=>(0,t.useContext)(r)', 'context accessor; auth implementation outside boundary');
  used('media', null, '"https://media.pump.fun/"', 'captured media URL prefix');
  used('media', null, '{IMAGE:45e5,VIDEO:1e7,BANNER:45e5}', 'captured submit byte limits');
  used('classifier', null, 'a.startsWith("0000")?"video/mp4":a.startsWith("1a45")?"video/webm":a.startsWith("5249")?"video/avi":a.startsWith("66747970")?"video/mp4":a.startsWith("1a45")?"video/mkv":null', 'ordered video classifier suffix; preceding image cases retained in factory');
  const classifier = exactlyOne(findNodes(factories.classifier.node, (n) => n.type === 'VariableDeclarator' &&
    n.id.name === 'r' && n.init?.async === true), 'complete existing media classifier');
  witnesses.push({ ...factories.classifier.witness(classifier, 'complete existing first-twelve-byte classifier, with ordered image/video cases'), astType: classifier.type });
  used('metadata', null, '...t&&a&&{video:e.z+"videos/"+u}', 'video metadata uses filename only when video and uploaded state are truthy');
  used('metadata', null, 'throw Error("No image hash provided")', 'metadata still requires independent uploaded image hash');
  used('metadata', null, 'await (0,r.o)(g)', 'metadata object passed to existing Pinata helper');
  used('metadata', null, '{metadata:g,metadataUri:m}', 'direct metadata result returned');
  used('resolvedMetadata', null, 'await a({...s,coinAddress:c,includeCoinCommunity:!0})', 'resolved-mint wrapper uses same metadata assembly');
  used('resolvedMetadata', null, '{preResolvedMint:u,metadata:l,metadataUri:d}', 'resolved metadata result returned');
  used('create', create.node, 'if(!n)return void await te({metadata:u,metadataUri:x})', 'zero-initial-purchase branch hands off resulting metadata');
  used('create', create.node, 'video:t.video', 'website create request consumes assembled video URI');
  const creationRequest = exactlyOne(findNodes(create.node, (n) => n.type === 'CallExpression' &&
    n.arguments[0]?.value === 'POST /coins/create-v2'), 'website creation handoff');
  assert.equal(create.text(objectProperty(objectProperty(creationRequest.arguments[1], 'body'), 'metadataUri')), 'r');
  witnesses.push({ ...create.witness(creationRequest, 'creation HTTP boundary consumes metadata URI and video field; never executed'), astType: creationRequest.type });
  const transactionHandoff = exactlyOne(findNodes(create.node, (n) => n.type === 'CallExpression' &&
    n.callee.type === 'Identifier' && n.callee.name === 'eF'), 'existing transaction helper handoff');
  assert.equal(objectProperty(transactionHandoff.arguments[0], 'uri').name, 'x');
  witnesses.push({ ...create.witness(transactionHandoff, 'existing transaction helper receives metadata URI; helper and signing outside scope'), astType: transactionHandoff.type });

  for (const [from, to, alias] of [['create', 'client', 'et'], ['create', 'classifier', 'eY'],
    ['create', 'media', 'eX'], ['create', 'authContext', 'n'], ['create', 'metadata', 'to'],
    ['create', 'resolvedMetadata', 'tl'], ['client', 'origins', 'r'], ['client', 'transport', 't'],
    ['transport', 'contract', 'e'], ['contract', 'videoRoute', 'ew'], ['contract', 'contractClient', 'eO']]) {
    const id = contexts[to][0];
    used(from, null, `${alias}=${factories[from].runtime}.${from === 'contract' ? 'r' : 'i'}(${id})`, `${from} imports ${to}`);
  }
  used('origins', null, '()=>"https://frontend-api-v3.pump.fun"', 'website API origin accessor');
  used('client', null, 'e=>(0,t.K)({clientServerUrl:(0,r.R)()},i({...s,...e}))', 'website client j selects origin and builder');
  used('transport', null, 't=>L.create({prefixUrl:t.clientServerUrl,credentials:"include",hooks:{beforeRequest:[I,M]}})', 'HTTP prefix and credential defaults');
  used('transport', null, '(t,r)=>(0,e.createContractClient)(_(t).extend({...j,...r}))', 'website builder uses contract client');
  used('transport', null, '{"x-pump-source":"WEB","x-pump-platform":"web"}', 'shared website source headers');
  used('contract', null, '...ew.videosRoutes', 'video declaration is in actual website contract registry');
  used('contract', null, 'Object.defineProperty(r,"createContractClient",{enumerable:!0,get:function(){return eO.createContractClient}})', 'actual contract client reexport');
  const route = exactlyOne(findNodes(factories.videoRoute.node, (n) => n.type === 'ObjectProperty' &&
    propertyName(n.key) === 'GET /videos/get-signed-url'), 'declared video route');
  witnesses.push({ ...factories.videoRoute.witness(route, 'declared response filename and nested URL/form fields'), astType: route.type });
  assert.equal(factories.videoRoute.text(objectProperty(route.value, 'query')), 'o.z.object({extension:o.z.string()})');
  assert.equal(factories.videoRoute.text(objectProperty(route.value, 'response')), 'o.z.object({filename:o.z.string().describe("Generated object filename"),url:o.z.object({url:o.z.string(),fields:o.z.record(o.z.string(),o.z.string())}).describe("S3 presigned POST payload (url and required form fields)")})');
  used('contractClient', null, 't.split(" ",2)', 'contract operation splits method from path');
  used('contractClient', null, 'method:o.toLowerCase()', 'operation method reaches HTTP transport');
  used('contractClient', null, '...p&&{searchParams:p}', 'query reaches HTTP transport');
  used('contractClient', null, 'o[n]=String(s)', 'scalar query value stringification');
  const prior = await readFile(path.join(corpus.root, 'contracts/create-media-bindings.json'));
  return {
    schemaVersion: 1,
    scope: 'Captured website Create signed-video upload caller and metadata handoff; inert source attribution only',
    capture: { route: '/create', capturedAt: corpus.manifest.captured_at, userAgent: corpus.manifest.user_agent,
      routeObject: Object.fromEntries(['path', 'url', 'bytes', 'sha256', 'status'].map((key) => [key, html.record[key]])), ...corpus.anchors },
    sources: Object.fromEntries(Object.entries(factories).map(([name, f]) => [name, f.provenance])),
    request: { origin: 'https://frontend-api-v3.pump.fun', method: 'GET', path: '/videos/get-signed-url',
      query: { extension: 'classifier MIME suffix (l), serialized as a string' }, body: null,
      credentials: 'include', headers: { 'Content-Type': 'application/json', 'x-pump-source': 'WEB', 'x-pump-platform': 'web' },
      success: 'response.ok required by afterResponse hook; parsed JSON consumed',
      declaredResponse: { filename: 'string', url: { url: 'string', fields: 'record<string,string>' } },
      responseValidation: 'declared schema only; success transport calls .json() without validating that schema' },
    providerUpload: { method: literal(open.arguments[0]), url: 'signedResponse.url.url (opaque, not a fixed provider origin)',
      encoding: 'browser FormData', orderedParts: ['every Object.entries(signedResponse.url.fields) pair', 'file: original selected File'],
      success: '200 <= XMLHttpRequest.status < 300; resolves response without parsing or consuming it',
      failures: ['non-2xx status', 'network error', 'abort event'], progress: 'loaded / total * 100 only when lengthComputable',
      timeoutAndRetry: 'no explicit XHR timeout or retry in this uploader',
      credentialMode: 'no explicit withCredentials assignment; no setRequestHeader call in this uploader',
      cancellation: 'cancel object is returned by the Promise executor; no caller-visible cancellation or xhrRef assignment is established',
      errorState: 'handler logs and rethrows without a finally reset; do not infer later UI state recovery' },
    handoff: { afterUpload: ['derive display URL', 'store signedResponse.filename', 'mark uploaded', 'clear uploading', 'extract three thumbnails'],
      displayUrl: 'https://media.pump.fun/videos/${signedResponse.filename}',
      filenameValidation: 'no separate filename validation in this used client path',
      metadataCallers: ['778435 direct assembly', '421159 resolved-mint wrapper calling the same assembly'],
      metadataVideo: 'included only when video && videoUploaded; https://media.pump.fun/videos/${videoFileName}',
      separateImageHash: 'still required by metadata assembly; the uploaded video does not supply it',
      existingImageAndJsonUpload: { path: 'contracts/create-media-bindings.json', sha256: sha256(prior) },
      finalConsumer: 'assembled metadata.video is passed to the website create request; metadataUri is separately handed to creation branches, neither executed here' },
    prerequisites: { selection: 'page passes !!wallet as isLoggedIn; selector forwards noClick/noDrag when false and shows the supplied wallet UI callback',
      upload: 'website credentialed request and a valid returned presigned POST payload; server eligibility and enforcement unknown',
      submission: ['truthy decodedJwt from existing context', 'video size <= 10000000 bytes', 'videoUploaded true', 'thumbnail condition satisfied'],
      timing: 'submission validation is later than file-selection upload; it is not a proven pre-upload auth or byte-limit gate',
      provider: 'declared as S3 presigned POST payload; concrete provider host, policy fields, expiry, ownership and persistence unknown' },
    limits: ['No service request, upload, signing, wallet operation, captured-code evaluation or observed successful upload response.',
      'No backend implementation, mounted UI, npm SDK change, production compatibility or feature-milestone credit.',
      'Client error branches do not establish server error schemas; static credential options do not establish anonymous or authenticated eligibility.',
      'Original classifier order is retained in the authenticated factory; later duplicate signatures are not repaired or reinterpreted.'],
    productionOperationsImplemented: 0, productionOperationsQualified: 0, mounted: false,
    witnesses,
  };
}

export async function verify(appRoot = defaultRoot, packet) {
  const actual = await recover(appRoot);
  assert.deepEqual(packet ?? JSON.parse(await readFile(path.join(appRoot, packetPath))), actual);
  return { factoryRoles: Object.keys(actual.sources).length,
    uniqueFactories: new Set(Object.values(actual.sources).map((s) => s.sha256)).size,
    witnesses: actual.witnesses.length, productionOperationsQualified: 0 };
}

async function main() {
  const args = process.argv.slice(2);
  let root = defaultRoot;
  let mode;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--app-root' && args[i + 1]) root = path.resolve(args[++i]);
    else if (['--check', '--write'].includes(args[i]) && !mode) mode = args[i];
    else throw new Error('usage: verify.mjs [--app-root PATH] --check|--write');
  }
  if (!mode) throw new Error('explicit --check or --write is required');
  if (mode === '--write') await writeFile(path.join(root, packetPath), `${JSON.stringify(await recover(root), null, 2)}\n`, { flag: 'w' });
  console.log(JSON.stringify(await verify(root)));
}
if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) await main();
