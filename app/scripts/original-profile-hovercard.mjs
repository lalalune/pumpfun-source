import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from '@babel/parser';
import { generate } from '@babel/generator';
import { openCorpus, findNodes, exactlyOne, propertyName, objectProperty, sha256 } from './original-contracts/source.mjs';

export const APP_ROOT = fileURLToPath(new URL('..', import.meta.url));
export const CLIENT = 'reconstruction/profile-hovercard/client.mjs';
export const CONTRACT = 'reconstruction/profile-hovercard/contract.json';
const EXPECTED = [
  {
    "id": 432626,
    "source": "evidence/web/objects/da58569257a3fbc5.js",
    "start": 25553,
    "end": 39733,
    "sha256": "98be45485d8453bae71b3fa5eaf90f97bedf30169d8987ea51734f168abe889d",
    "actualRegistrationIds": [
      432626
    ]
  },
  {
    "id": 528600,
    "source": "evidence/web/objects/7128bd47b219d222.js",
    "start": 40694,
    "end": 42758,
    "sha256": "e39bef17254305a3d6a56ab31a0b4ab3917c4c45bb2f02e7f6f97bcef9fe9b42",
    "actualRegistrationIds": [
      528600,
      448341
    ]
  },
  {
    "id": 528600,
    "source": "evidence/web/objects/27a1ee00eb5909ec.js",
    "start": 28499,
    "end": 30563,
    "sha256": "4a32db97ba300fa1f7aec4b46ad310a27e3851230dfcdb98f6e08b7c4915907d",
    "actualRegistrationIds": [
      528600,
      448341
    ]
  },
  {
    "id": 528600,
    "source": "evidence/web/objects/d048caae282716b0.js",
    "start": 16339,
    "end": 18403,
    "sha256": "3b89fd7cd809c05ef7403fea617b9d69af3ed23106b34a095144e463ebb74df5",
    "actualRegistrationIds": [
      528600,
      448341
    ]
  },
  {
    "id": 179736,
    "source": "evidence/web/objects/da58569257a3fbc5.js",
    "start": 49880,
    "end": 51270,
    "sha256": "65c55fd94aae19033823800ac95d722d88c4cd549c869927bfe53b6b675596f1",
    "actualRegistrationIds": [
      179736
    ]
  },
  {
    "id": 179736,
    "source": "evidence/web/objects/c7e25d5561f3a8f8.js",
    "start": 12115,
    "end": 13505,
    "sha256": "8b4fa23b4c652bb17188ff843e8878e509e6f1bb661a7ccefea3d84710cf150b",
    "actualRegistrationIds": [
      179736
    ]
  },
  {
    "id": 498936,
    "source": "evidence/web/objects/da58569257a3fbc5.js",
    "start": 17709,
    "end": 18474,
    "sha256": "c2af9052dd4125aa42368c666728d23ab9cd05aada8487a192d66aa5f1637080",
    "actualRegistrationIds": [
      498936
    ]
  },
  {
    "id": 498936,
    "source": "evidence/web/objects/87a44458ebf665fe.js",
    "start": 27951,
    "end": 28716,
    "sha256": "a89ac6ebc0e1b63d52ea9280009245bddcbbebde1af07936d94c143b3c675f2e",
    "actualRegistrationIds": [
      498936
    ]
  },
  {
    "id": 498936,
    "source": "evidence/web/objects/864111a9a40a97f0.js",
    "start": 39336,
    "end": 40101,
    "sha256": "41846166053e8db85eb03ae4d14cf70ac6d5dd0dd4c3ae3a6637b99c3c55df18",
    "actualRegistrationIds": [
      498936
    ]
  },
  {
    "id": 498936,
    "source": "evidence/web/objects/d96bd90b2de3d9da.js",
    "start": 58910,
    "end": 59675,
    "sha256": "d54f81d9554c764dfaab63f220e16c170a2da1f9717add127d0824e2ce8e01f7",
    "actualRegistrationIds": [
      498936
    ]
  },
  {
    "id": 498936,
    "source": "evidence/web/objects/5c900f5590ba04fe.js",
    "start": 13793,
    "end": 14558,
    "sha256": "ce8d21da69745a2bba808bf480b04809061560e8c28e6bf539b263dff60d7464",
    "actualRegistrationIds": [
      498936
    ]
  },
  {
    "id": 653706,
    "source": "evidence/web/objects/da58569257a3fbc5.js",
    "start": 47678,
    "end": 48410,
    "sha256": "187fb1fe50599fe8ba6b5048960647482fa1ba765c8c50bb25c4d6938777073e",
    "actualRegistrationIds": [
      653706
    ]
  },
  {
    "id": 653706,
    "source": "evidence/web/objects/95be9180237024f4.js",
    "start": 24244,
    "end": 24976,
    "sha256": "b9acd40f701f527ca44ad4abd23ec81f81491f5426c27a3d8eac704f89105510",
    "actualRegistrationIds": [
      653706
    ]
  },
  {
    "id": 653706,
    "source": "evidence/web/objects/c9d58b1f7b1c6f01.js",
    "start": 70329,
    "end": 71061,
    "sha256": "2100de7133e0375c8500c92b74732062e50f32e5bf275d9d65ff5b42925539e9",
    "actualRegistrationIds": [
      653706
    ]
  },
  {
    "id": 69399,
    "source": "evidence/web/objects/da58569257a3fbc5.js",
    "start": 18481,
    "end": 18682,
    "sha256": "35ee9b42b2197b69c4f65475eaafa8097929e9e2e1f0657cce4fc2d79565d075",
    "actualRegistrationIds": [
      69399
    ]
  },
  {
    "id": 69399,
    "source": "evidence/web/objects/ea5d7a76f15713d7.js",
    "start": 12668,
    "end": 12869,
    "sha256": "4043938d1f3547190132378541afc93d48c24d0dc55898853f2b2b987071eeb1",
    "actualRegistrationIds": [
      69399
    ]
  },
  {
    "id": 584582,
    "source": "evidence/web/objects/da58569257a3fbc5.js",
    "start": 18690,
    "end": 19634,
    "sha256": "f3bf642333a630d253a166fbdf15329dd8e6ce24a264c3c648c54acae0d1c405",
    "actualRegistrationIds": [
      584582
    ]
  },
  {
    "id": 360827,
    "source": "evidence/web/objects/ff33be86d72ef271.js",
    "start": 20328,
    "end": 20450,
    "sha256": "a7e8c373e26d211ce2321932e5e2bbe4d4e067de13ededbd31d7427932b8615e",
    "actualRegistrationIds": [
      360827
    ]
  },
  {
    "id": 938277,
    "source": "evidence/web/objects/fd402d4185b44ce9.js",
    "start": 28526,
    "end": 29798,
    "sha256": "545894110a73dff365be7a9abf03f0e26f66033993f80b40e125fe1697bd19f6",
    "actualRegistrationIds": [
      938277
    ]
  },
  {
    "id": 938277,
    "source": "evidence/web/objects/87a44458ebf665fe.js",
    "start": 28724,
    "end": 29996,
    "sha256": "88db731a9e6cae25cc2d89b46bda5bd2aad0299984f114c04b69bc753c87b5de",
    "actualRegistrationIds": [
      938277
    ]
  },
  {
    "id": 540805,
    "source": "evidence/web/objects/ad7136d0b3a7f323.js",
    "start": 33160,
    "end": 34396,
    "sha256": "058ef17f92b13d44c2ead869a78a52961abc88fd4814fa72514f5c11c1fc85be",
    "actualRegistrationIds": [
      540805
    ]
  },
  {
    "id": 365089,
    "source": "evidence/web/objects/ad7136d0b3a7f323.js",
    "start": 34404,
    "end": 34983,
    "sha256": "8957b61a69e89f0148cf9a43ca9bc4089cc0c2c892e476af960d1a02c966f4d1",
    "actualRegistrationIds": [
      365089
    ]
  },
  {
    "id": 426091,
    "source": "evidence/web/objects/92f43c917bbc50e2.js",
    "start": 119,
    "end": 20735,
    "sha256": "93b70fac45ba969c312e0f7ec965b181d06a8332f7e1a4bba6751a63fd5555a4",
    "actualRegistrationIds": [
      426091
    ]
  },
  {
    "id": 322315,
    "source": "evidence/web/objects/256f83f9b5d323e6.js",
    "start": 7353,
    "end": 35793,
    "sha256": "5d08c12f771cccf43ebfa2740e4a0fbf8c67c9df5a781e8cd2c1183997178f26",
    "actualRegistrationIds": [
      322315
    ]
  },
  {
    "id": 254010,
    "source": "evidence/web/objects/256f83f9b5d323e6.js",
    "start": 36275,
    "end": 39483,
    "sha256": "68c2bf6f4fa12591ba132bd96e6e09f9d5cdb13093bde04cd29ef0d6ec0182dd",
    "actualRegistrationIds": [
      254010,
      30824
    ]
  },
  {
    "id": 98525,
    "source": "evidence/web/objects/da58569257a3fbc5.js",
    "start": 48417,
    "end": 49872,
    "sha256": "38b7b65f7e40c1463314e2e5d484a63675c6d48338435ee54a71a4c5593f046b",
    "actualRegistrationIds": [
      98525
    ]
  },
  {
    "id": 705313,
    "source": "evidence/web/objects/d048caae282716b0.js",
    "start": 5004,
    "end": 7798,
    "sha256": "d20ae1800486b11692b11f5a2172e262d6e11c84a1c8912eaa73b615d8d058b9",
    "actualRegistrationIds": [
      705313
    ]
  },
  {
    "id": 630164,
    "source": "evidence/web/objects/6bc86057d6de0291.js",
    "start": 20067,
    "end": 27996,
    "sha256": "ba600e4b8d1914e9a3315af614297dfad2b43f12abc5ae6d9b684008a94f5d5b",
    "actualRegistrationIds": [
      630164
    ]
  },
  {
    "id": 630164,
    "source": "evidence/web/objects/da58569257a3fbc5.js",
    "start": 39741,
    "end": 47670,
    "sha256": "85b7bffab53cfd9f8f101be9c78f5aec69f3f8615e422c98dc44764cfdefcffd",
    "actualRegistrationIds": [
      630164
    ]
  },
  {
    "id": 598883,
    "source": "evidence/web/objects/6bc86057d6de0291.js",
    "start": 14163,
    "end": 20059,
    "sha256": "19c6c1d0c6bae47e48685f18313e9b033122e88abec4181a1907a2597a6fe1ec",
    "actualRegistrationIds": [
      598883,
      532047
    ]
  },
  {
    "id": 598883,
    "source": "evidence/web/objects/da58569257a3fbc5.js",
    "start": 19649,
    "end": 25545,
    "sha256": "d8355323fbf416470cb2233c10c31d5973dae0518c0e3adca8699719ecca8ce9",
    "actualRegistrationIds": [
      598883,
      532047
    ]
  },
  {
    "id": 96224,
    "source": "evidence/web/objects/a0ec47219f76f808.js",
    "start": 22925,
    "end": 23559,
    "sha256": "5a7aacd1e02cdcba6278e50454f2b919f6e5cfc1cc3006855c0be0d0f4344c4e",
    "actualRegistrationIds": [
      96224
    ]
  },
  {
    "id": 690877,
    "source": "evidence/web/objects/d53e210f3ad485f2.js",
    "start": 21939,
    "end": 22033,
    "sha256": "d7f6154cd14d89343ad7f9e12d735a944bdc0061f2dee2ed1d679793c885ab95",
    "actualRegistrationIds": [
      690877
    ]
  },
  {
    "id": 445242,
    "source": "evidence/web/objects/01ad4f413e529b60.js",
    "start": 4795,
    "end": 4839,
    "sha256": "2d7f3e592645b5e2d997e444ee9b10be6dc8c357680552dccddafb63e4887576",
    "actualRegistrationIds": [
      445242
    ]
  },
  {
    "id": 732486,
    "source": "evidence/web/objects/e01139c6299580b1.js",
    "start": 25883,
    "end": 25927,
    "sha256": "1327928dc08f8c5ad213c67d8b2b042e579ca141db8b23ac448bf178077cfadd",
    "actualRegistrationIds": [
      732486
    ]
  },
  {
    "id": 352386,
    "source": "evidence/web/objects/e01139c6299580b1.js",
    "start": 25831,
    "end": 25875,
    "sha256": "94c140de6329c130f107d5731a5574eec51cc1a23c2266c2d99db6dea7a71d88",
    "actualRegistrationIds": [
      352386
    ]
  },
  {
    "id": 149502,
    "source": "evidence/web/objects/e01139c6299580b1.js",
    "start": 799,
    "end": 942,
    "sha256": "a77a97f1bdda36afacb17701d889ea2c15af0fb6731dac1d39380aba7cc29b3c",
    "actualRegistrationIds": [
      149502
    ]
  },
  {
    "id": 745018,
    "source": "evidence/web/objects/c8e855c81e05ca28.js",
    "start": 119,
    "end": 166147,
    "sha256": "4cc46a6d51b6a9b0fe8ce9f64d77e130e7961309e881fe14f64efa16fb09f660",
    "actualRegistrationIds": [
      745018
    ]
  }
];
const one = (scope, test, label) => exactlyOne(findNodes(scope, test), label);
const print = (node) => generate(node, { comments: false }).code;
const cite = (f, n, label, includeText = true) => ({ ...f.witness(n, label), astType: n.type, ...(includeText ? { text: f.text(n) } : {}) });
const declarations = (f) => f.node.body.body.flatMap((n) => n.type === 'VariableDeclaration' ? n.declarations : [n]);
const declaration = (f, name) => exactlyOne(declarations(f).filter((n) => n.id?.name === name), name);
function exported(f, key) {
  const matches = [];
  for (const s of f.node.body.body) {
    const n = s.expression;
    if (n?.type !== 'CallExpression' || n.callee.object?.name !== f.runtime || propertyName(n.callee.property) !== 's' ||
      (n.arguments[1] && n.arguments[1].value !== f.provenance.id)) continue;
    const values = n.arguments[0].elements;
    for (let i = 0; i < values.length; i += 3) if (values[i]?.value === key) matches.push(values[i + 2]);
  }
  return exactlyOne(matches, `export ${f.provenance.id}.${key}`);
}
const resolve = (f, n) => n.type === 'Identifier' ? declaration(f, n.name).init ?? declaration(f, n.name) : n;
const imported = (f, id) => exactlyOne(declarations(f).filter((n) => n.init?.type === 'CallExpression' &&
  n.init.callee.object?.name === f.runtime && n.init.arguments[0]?.value === id), `import ${id}`);

const MAIN_WITNESSES = [
  {
    "label": "complete original HomeView viewport branch",
    "source": "evidence/web/objects/decc1b8a23be2e25.js",
    "utf16": [
      28315,
      28687
    ],
    "utf8": [
      28315,
      28687
    ],
    "sha256": "3191546823e13c8cc85a6616f9d669abf053f1b4e625327c8ca02c1371dd3b89",
    "sourceSha256": "fc31766f488fbfffd8af33b176bb779d66dabbd9c45fa1c030888ae6ccbbde11"
  },
  {
    "label": "complete mobile Home owner static admission only",
    "source": "evidence/web/objects/decc1b8a23be2e25.js",
    "utf16": [
      11338,
      20104
    ],
    "utf8": [
      11338,
      20104
    ],
    "sha256": "967da20d46237b0a5fd502caa3b5752f07463679082c89188304b55c2109a59f",
    "sourceSha256": "fc31766f488fbfffd8af33b176bb779d66dabbd9c45fa1c030888ae6ccbbde11"
  },
  {
    "label": "complete mobile Home tab\u2192feed-list handoff",
    "source": "evidence/web/objects/decc1b8a23be2e25.js",
    "utf16": [
      20111,
      20694
    ],
    "utf8": [
      20111,
      20694
    ],
    "sha256": "9109eecd2d3f7c06abb387d61a00ed8a6127114b785787b444a318b8b908bfd2",
    "sourceSha256": "fc31766f488fbfffd8af33b176bb779d66dabbd9c45fa1c030888ae6ccbbde11"
  },
  {
    "label": "actual admitted MAIN reply-row import",
    "source": "evidence/web/objects/decc1b8a23be2e25.js",
    "utf16": [
      281,
      294
    ],
    "utf8": [
      281,
      294
    ],
    "sha256": "6bf02b41ab03bbbfeb8d24fab96c9a41065b53664f3d9e6f65e1fd749b287edd",
    "sourceSha256": "fc31766f488fbfffd8af33b176bb779d66dabbd9c45fa1c030888ae6ccbbde11"
  },
  {
    "label": "actual MAIN non-repost row\u2192349919 descriptor",
    "source": "evidence/web/objects/decc1b8a23be2e25.js",
    "utf16": [
      24853,
      24984
    ],
    "utf8": [
      24853,
      24984
    ],
    "sha256": "53474b01f33eafa9af9ff9b33e24f3c7a6a10f0149b8fb23711823b4bd1bcbee",
    "sourceSha256": "fc31766f488fbfffd8af33b176bb779d66dabbd9c45fa1c030888ae6ccbbde11"
  },
  {
    "label": "complete ordinary MAIN parent frame static context",
    "source": "evidence/web/objects/91795a66d4097dbd.js",
    "utf16": [
      1981,
      7290
    ],
    "utf8": [
      1981,
      7292
    ],
    "sha256": "696bc40cc37b0b2eae8ea29f3948316591664b6c2e19a5d4a75fd6938dd690ba",
    "sourceSha256": "1494220a9285d9b73c85be1dfbe5c4d0cbb65767b1c0d12f0de5459e5332e1c1"
  },
  {
    "label": "actual ordinary MAIN reply-cell invocation with full props",
    "source": "evidence/web/objects/91795a66d4097dbd.js",
    "utf16": [
      3612,
      3755
    ],
    "utf8": [
      3612,
      3755
    ],
    "sha256": "7624785ea8ccc0e581b673e0cccc8ef66b0b1ef40f386ea69b79393d73d99493",
    "sourceSha256": "1494220a9285d9b73c85be1dfbe5c4d0cbb65767b1c0d12f0de5459e5332e1c1"
  },
  {
    "label": "actual ordinary MAIN reply-cell invocation with full props",
    "source": "evidence/web/objects/91795a66d4097dbd.js",
    "utf16": [
      6581,
      6849
    ],
    "utf8": [
      6583,
      6851
    ],
    "sha256": "148d206994f3ca5eaeeeb6ad8b70df247793a7f09bb903e3f693868d3a0040c6",
    "sourceSha256": "1494220a9285d9b73c85be1dfbe5c4d0cbb65767b1c0d12f0de5459e5332e1c1"
  },
  {
    "label": "actual ordinary MAIN reply-cell invocation with full props",
    "source": "evidence/web/objects/91795a66d4097dbd.js",
    "utf16": [
      6853,
      7029
    ],
    "utf8": [
      6855,
      7031
    ],
    "sha256": "b0c86a59cd9000faa3cc5ee2db8867c4c788a8b36f1872a8a399078dacd7dd2f",
    "sourceSha256": "1494220a9285d9b73c85be1dfbe5c4d0cbb65767b1c0d12f0de5459e5332e1c1"
  }
];
async function role(corpus, spec) {
 const cap=await corpus.javascript(spec.source);
 const reg=exactlyOne(cap.factories.filter(r=>r.node.start===spec.start&&r.node.end===spec.end&&r.ids.includes(spec.id)),`physical registration ${spec.id}`);
 const witness=cap.witness(reg.node,`factory ${spec.id}`);assert.equal(witness.sha256,spec.sha256);
 assert.ok(corpus.index.modules.some(m=>m.sha256===spec.sha256&&m.ids.includes(spec.id)&&m.origins.some(o=>o.source===spec.source&&o.start===spec.start&&o.end===spec.end)),'physical source/index binding');
 return{id:spec.id,ids:reg.ids,node:reg.node,runtime:reg.node.params[0]?.name,text:(n=reg.node)=>cap.text.slice(n.start,n.end),witness:(n,label)=>cap.witness(n,label),provenance:{id:spec.id,ids:reg.ids,...witness}};
}
export async function recover(root=APP_ROOT){
 const corpus=await openCorpus(root),roles=[];
 for(const spec of EXPECTED)roles.push(await role(corpus,spec));
 for(const id of new Set(EXPECTED.map(r=>r.id)))assert.deepEqual(corpus.index.modules.filter(m=>m.ids.includes(id)).map(m=>m.sha256).sort(),EXPECTED.filter(r=>r.id===id).map(r=>r.sha256).sort(),`explicit variants ${id}`);
 const get=(id)=>exactlyOne(roles.filter(r=>r.id===id),`unique role ${id}`);
 const core=get(432626),component=exported(core,'f'),XLink=declaration(core,'W'),stat=declaration(core,'Y');
 const slots=n=>findNodes(n,x=>x.type==='CallExpression'&&x.callee.type==='SequenceExpression'&&x.callee.expressions.at(-1)?.object?.name==='n'&&x.callee.expressions.at(-1)?.property?.name==='c').map(x=>x.arguments[0]?.value);
 assert.deepEqual(slots(component),[111,10,9]);assert.deepEqual(slots(XLink),[15]);assert.deepEqual(slots(stat),[14]);
 const constants=['z','O','L','q','V','X','B','H'].map(name=>declaration(core,name));
 const xStop=declaration(core,'E');
 const xDeclaration=exactlyOne(core.node.body.body.filter(n=>n.type==='VariableDeclaration'&&n.declarations.includes(XLink)),'original XLink declaration statement');assert.equal(xDeclaration.kind,'let');
 const fallback=resolve(get(426091),exported(get(426091),'A'));assert.equal(fallback.type,'StringLiteral');
 const surface=exported(get(360827),'V');assert.equal(surface.type,'StringLiteral');
 const feature=one(get(322315).node,n=>n.type==='AssignmentExpression'&&n.left?.property?.name==='WEB_SQUADS'&&n.right?.type==='StringLiteral','actual WEB_SQUADS flag literal').right;
 const fetchSummary=declaration(core,'$'),fetchPnl=declaration(core,'R'),schema=['D','F','T'].map(name=>declaration(core,name));
 const profileCall=one(component,n=>n.type==='CallExpression'&&n.callee.type==='SequenceExpression'&&n.callee.expressions.at(-1)?.object?.name==='y'&&n.callee.expressions.at(-1)?.property?.name==='C','actual profile lookup');
 const verification=one(component,n=>n.type==='CallExpression'&&n.callee.type==='SequenceExpression'&&n.callee.expressions.at(-1)?.object?.name==='g','actual verified lookup');
 const queryHooks=findNodes(component,n=>n.type==='ArrowFunctionExpression'&&[10,9].includes(slots(n)[0]));assert.equal(queryHooks.length,2);
 const effect=one(component,n=>n.type==='CallExpression'&&n.callee.type==='SequenceExpression'&&n.callee.expressions.at(-1)?.object?.name==='v'&&n.callee.expressions.at(-1)?.property?.name==='useEffect','complete update interval effect');
 const clipboard=one(component,n=>n.type==='ArrowFunctionExpression'&&n.async&&findNodes(n,x=>x.type==='AwaitExpression'&&x.argument?.callee?.property?.name==='writeText').length===1,'complete clipboard callback');
 const rawSources=['2560599a20517277','1bdf4f1b5f429664','2fe17dced92b840b','b9583b0184693a91','eb0b23ee6feb7543','df5a88be773ee688'];
 const callerLedger=[],callerWitnesses=[];
 for(const name of rawSources){const source=`evidence/web/objects/${name}.js`,cap=await corpus.javascript(source);for(const reg of cap.factories){
   const imports=findNodes(reg.node,n=>n.type==='VariableDeclarator'&&n.init?.type==='CallExpression'&&n.init.callee?.object?.name===reg.node.params[0]?.name&&n.init.arguments[0]?.value===432626);
   for(const imported of imports){const alias=imported.id.name,calls=findNodes(reg.node,n=>n.type==='CallExpression'&&n.arguments[0]?.type==='MemberExpression'&&n.arguments[0].object?.name===alias&&propertyName(n.arguments[0].property)==='f');
     callerLedger.push({source,actualRegistrationIds:reg.ids,factorySha256:cap.witness(reg.node,'consumer factory').sha256,calls:calls.map(n=>cap.witness(n,'actual ProfileHover JSX caller'))});callerWitnesses.push({...cap.witness(imported,'actual ProfileHover import'),astType:imported.type,text:cap.text.slice(imported.start,imported.end)},...calls.map(n=>({...cap.witness(n,'actual ProfileHover JSX caller'),astType:n.type,text:cap.text.slice(n.start,n.end)})));
   }
 }}
 assert.equal(callerLedger.length,7);assert.equal(callerLedger.reduce((n,r)=>n+r.calls.length,0),13);
 const twin=await corpus.factory(432626,{source:'evidence/web/objects/faf3bcbd59e7e996.js'});assert.equal(twin.provenance.sha256,core.provenance.sha256);
 const reply=await corpus.factory(710416,{source:'evidence/web/objects/2560599a20517277.js'}),ordinary=resolve(reply,exported(reply,'f'));
 const ordinaryCalls=callerLedger.find(r=>r.source===reply.provenance.source).calls.filter(w=>w.utf16[0]>=ordinary.start&&w.utf16[1]<=ordinary.end);assert.equal(ordinaryCalls.length,1,'one actual conditional wrapper in ordinary MAIN reply');
 const ordinaryWrapper=one(ordinary,n=>n.type==='ArrowFunctionExpression'&&findNodes(n,x=>x.type==='CallExpression'&&x.arguments[0]?.object?.name==='s'&&x.arguments[0]?.property?.name==='f').length===1,'complete conditional ordinary MAIN wrapper');
 const rootCapture=await corpus.capture('evidence/web/objects/b713215f09b03c14');
 assert.equal(rootCapture.record.url,'https://pump.fun/');assert.equal(rootCapture.record.sha256,'5c54a668997394767a338ff5efe132ba3400bd5e1c4b6bb16c9c075b6a389409');
 const fragments=[];
 for(const match of rootCapture.text.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)){
  if(!match[1].includes('__next_f'))continue;
  const ast=parse(match[1],{sourceType:'script'});
  for(const call of findNodes(ast,n=>n.type==='CallExpression'&&n.callee?.object?.type==='MemberExpression'&&n.callee.object.object?.name==='self'&&n.callee.object.property?.name==='__next_f'&&n.callee.property?.name==='push')){
   const a=call.arguments[0];if(a?.type==='ArrayExpression'&&a.elements[0]?.value===1&&a.elements[1]?.type==='StringLiteral')fragments.push(a.elements[1].value);
  }
 }
 const flight=new Map(fragments.join('').split('\n').map(line=>{const i=line.indexOf(':');return[line.slice(0,i),line.slice(i+1)];}));
 assert.equal(flight.get('8f')[0],'I');const homeImport=JSON.parse(flight.get('8f').slice(1));assert.equal(homeImport[0],163807);assert.equal(homeImport[2],'HomeView');
 const uses=[];function elementWalk(n,p=[]){if(!n||typeof n!=='object')return;if(Array.isArray(n)&&n[0]==='$'&&n[1]==='$L8f')uses.push({path:['18',...p],props:n[3]});for(const[k,v]of Object.entries(n))elementWalk(v,[...p,k]);}elementWalk(JSON.parse(flight.get('18')));assert.equal(uses.length,1);
 const mainWitnesses=[];
 for(const expected of MAIN_WITNESSES){const cap=await corpus.javascript(expected.source);const matches=findNodes(cap.ast,n=>n.start===expected.utf16[0]&&n.end===expected.utf16[1]);assert.ok(matches.length>0,'admitted witness is actual AST node');const node=matches[0],proof=cap.witness(node,expected.label);assert.equal(proof.sha256,expected.sha256);assert.equal(proof.sourceSha256,expected.sourceSha256);assert.deepEqual(proof.utf8,expected.utf8);mainWitnesses.push({...proof,astType:node.type});}
 const mainAdmission={root:{source:'evidence/web/objects/b713215f09b03c14',url:rootCapture.record.url,bytes:rootCapture.bytes.length,sha256:rootCapture.record.sha256},flightImport:{id:'8f',value:homeImport},elementUses:uses,
  path:'rootFlight→163807.HomeView conditional mobile eH→ez→eG non-repost row→349919.f→710416.f→conditional432626 wrapper',
  scope:'Inert static conditional MAIN admission only. No captured row-render observation, Home/provider execution or individual coin/token-detail admission.'};
 const code=`export function createProfileHoverCard({environmentSnapshot,React,compiler,jsxRuntime,useApiClientsConfig,useVerifiedStatus,useProfileLookup,useQuery,readBalanceSummary,readWindowPnl,normalizeBalanceSummary,readXProfile,useFeatureFlag,groupRoute,shortenAddress,plural,formatMoney,formatCompact,formatSigned,formatPnlClass,formatCount,formatUpdated,classes,Avatar,VerifiedBadge,XTooltip,HoverRoot,HoverTrigger,HoverContent,XIcon,CheckIcon,CopyIcon,navigator,setInterval,clearInterval,setTimeout}){
 const t=environmentSnapshot,r=jsxRuntime,n={c:compiler},a={Tc:XIcon,sX:CheckIcon,xR:CopyIcon},i={useApiClientsConfig},l={D:{WEB_SQUADS:${print(feature)}}},o={k:useFeatureFlag},s={c:classes,A:${print(fallback)}},u={w:formatMoney},d={C:formatUpdated},c={d:shortenAddress,V:plural},f={Z:groupRoute},m={f:normalizeBalanceSummary},h={l:formatCompact,u:formatSigned,k:formatPnlClass,O:formatCount},p={f:Avatar},x={f:VerifiedBadge},g={s:useVerifiedStatus},y={C:useProfileLookup},v=React,b={c:HoverRoot,b:HoverTrigger,P:HoverContent},w={V:${print(surface)}},j={useQuery},A={a:XTooltip},I={k:readXProfile},$=readBalanceSummary,R=readWindowPnl;
 let ${constants.map(print).join(',')};
 ${xDeclaration.kind} ${print(XLink)};
 ${print(xStop)}
 ${print(stat)}
 const ProfileHoverCard=${print(component)};
 return{ProfileHoverCard};
 }`;
 const client=generate(parse(code,{sourceType:'module'}),{comments:false}).code+'\n';
 const witness=[cite(core,component,'complete profile hovercard owner'),cite(core,XLink,'complete X-profile link owner'),cite(core,stat,'complete stat row owner'),cite(core,xStop,'complete X-link propagation callback'),
 ...constants.map(n=>cite(core,n,`complete display declaration ${n.id.name}`)),...queryHooks.map((n,i)=>cite(core,n,`complete inline read coordinator ${i}`)),cite(core,profileCall,'actual profile lookup handoff'),cite(core,verification,'actual verification handoff'),cite(core,effect,'complete interval and lifetime'),cite(core,clipboard,'complete used clipboard await/feedback callback'),
 ...schema.map(n=>cite(core,n,`external schema declaration ${n.id.name}`)),cite(core,fetchSummary,'external full summary reader/schema handoff'),cite(core,fetchPnl,'external full window-PnL reader'),cite(get(426091),fallback,'credited fallback image constant'),cite(get(360827),surface,'credited hover surface class'),cite(get(322315),feature,'actual feature flag key'),
 ...roles.filter(f=>f.id!==432626).map(f=>cite(f,f.node,`external dependency context ${f.id}`,false)),...callerWitnesses,cite(reply,ordinary,'complete ordinary MAIN reply owner context only',false),cite(reply,ordinaryWrapper,'actual conditional ordinary MAIN hover wrapper')];
 witness.push(...mainWitnesses);
 const contract={schemaVersion:1,mainAdmission,baseCommit:'094a06f18df738d41e77070c1a009e135671ac1a',sources:roles.map(f=>f.provenance),twinOwnerOrigin:twin.provenance,witnesses:witness,callerLedger,
 implementation:{factory:432626,export:'f',entry:'createProfileHoverCard',declarationKinds:{W:xDeclaration.kind},compilerFrames:[111,10,9,15,14],totalSlots:159,clientSha256:sha256(Buffer.from(client)),mounted:false},
 ordinaryAdmission:{namespace:710416,source:reply.provenance.source,wrapper:ordinaryCalls[0],scope:'Conditional ordinary MAIN reply wrapper only; a wallet and absent explicit replierHref are required by caller. No reply-cell execution or observed captured rows claimed.'},
 preserved:{hooks:'Verified/profile/summary/PnL hooks run before disabled return. Disabled is a display branch, not auth or request admission.',identity:'Verification uses userId??userAddress; profile lookup uses userAddress and open with staleTime3e5. Raw fallback link/custom truthiness and trimmed strings remain.',reads:'Complete 10/9-slot inline query options/keys/order; required external readers and schema implementation, no real financial request.',display:'Supplied identity/counts/summary/PnL/X/squad projection to exact credited renderer/formatter APIs; no financial calculation engine.',clock:'Source updated callback immediately then30s interval while open with valid supplied state; interval cleanup preserved.',clipboard:'Await required supplied writeText, then feedback true and2s timeout. No source timeout cleanup, operator clipboard or stale-result repair added.',events:'Source onOpenChange sets state then optional callback; defaults only for undefined; opaque followSlot; propagation-only X/content callbacks.'},
 credited:['Existing lookup870/coalescer910 and verified1841 boundaries are required API ports, no open-PR runtime import.','Avatar1916/decoration and navigation helpers remain credited renderer/API ports.','Ordinary MAIN reply710416 ownership is separate; its source caller is inert evidence only.','Existing financial display/reader/schema source is external; no acquisition or calculation credit.'],
 limits:['Original captured factories are parsed, not executed. No real provider, profile/financial service, auth/follow, wallet/session, credential/cookie or operator clipboard access.','All selected dependency variants pinned; no active loader/provider winner or complete site reconstruction.','Synthetic query/provider/clock/clipboard/render ports qualify only this complete display/coordinator boundary. No mounted MAIN, original row observation, financial action, API/native/security/milestone claim.']};
 return{client,contract};
}
export async function verify(root=APP_ROOT,supplied={}){
 const {client,contract}=await recover(root),expected={client:Buffer.from(client),contract:Buffer.from(JSON.stringify(contract,null,2)+'\n')};
 for(const[key,p]of[['client',CLIENT],['contract',CONTRACT]])assert.ok((supplied[key]??await readFile(path.join(root,p))).equals(expected[key]),`${key} canonical source-derived bytes differ`);
 return{sources:contract.sources.length,ownerVariants:1,ownerOrigins:2,witnesses:contract.witnesses.length,callers:7,calls:13,compilerSlots:159,mounted:false};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{assert.equal(process.argv.length,3);assert.ok(['--write','--check'].includes(process.argv[2]));if(process.argv[2]==='--write'){const{client,contract}=await recover();await mkdir(path.dirname(path.join(APP_ROOT,CLIENT)),{recursive:true});await writeFile(path.join(APP_ROOT,CLIENT),client);await writeFile(path.join(APP_ROOT,CONTRACT),JSON.stringify(contract,null,2)+'\n');}console.log(JSON.stringify(await verify()));}catch(error){console.error(error.stack);process.exitCode=1;}
}
