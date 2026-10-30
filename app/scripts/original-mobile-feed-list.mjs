import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {parse} from '@babel/parser';
import {generate} from '@babel/generator';
import {openCorpus,findNodes,exactlyOne,objectProperty,propertyName,sha256} from './original-contracts/source.mjs';
export const APP_ROOT=fileURLToPath(new URL('..',import.meta.url));
export const CLIENT='reconstruction/mobile-feed-list/client.mjs';
export const CONTRACT='reconstruction/mobile-feed-list/contract.json';
const EXPECTED=[
  {
    "id": 163807,
    "source": "evidence/web/objects/decc1b8a23be2e25.js",
    "start": 119,
    "end": 28697,
    "sha256": "828b7d1e93dd4135f930646c9f29729e82209232a020fca54e3e775a20eafe44",
    "actualRegistrationIds": [
      163807
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
    "id": 745018,
    "source": "evidence/web/objects/c8e855c81e05ca28.js",
    "start": 119,
    "end": 166147,
    "sha256": "4cc46a6d51b6a9b0fe8ce9f64d77e130e7961309e881fe14f64efa16fb09f660",
    "actualRegistrationIds": [
      745018
    ]
  },
  {
    "id": 349919,
    "source": "evidence/web/objects/91795a66d4097dbd.js",
    "start": 1737,
    "end": 7293,
    "sha256": "d9e37561efe6c7dfc134d7ace63aa44c5f74e6c406700bd925e0fb7cd4569bc6",
    "actualRegistrationIds": [
      349919
    ]
  },
  {
    "id": 146695,
    "source": "evidence/web/objects/fd402d4185b44ce9.js",
    "start": 29806,
    "end": 30355,
    "sha256": "bb995bc856796eb404e21763f5a72275af2b0efa06b46f0d12507e1c6a3d90a1",
    "actualRegistrationIds": [
      146695
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
    "id": 458310,
    "source": "evidence/web/objects/1e479323ffe53c14.js",
    "start": 17256,
    "end": 20495,
    "sha256": "637fd83c895d24a43cfd4243adbb9daea8b61e6c81df9feb82fb844f1e0cbe43",
    "actualRegistrationIds": [
      458310
    ]
  },
  {
    "id": 335703,
    "source": "evidence/web/objects/257d1f445453cc81.js",
    "start": 159,
    "end": 6298,
    "sha256": "ac958e6c1ea5ae37647619da80cee73000e79667bdb7e1ac2f0c49a2b43c4c20",
    "actualRegistrationIds": [
      335703,
      309265,
      985688,
      186434
    ]
  },
  {
    "id": 204478,
    "source": "evidence/web/objects/2560599a20517277.js",
    "start": 19372,
    "end": 72983,
    "sha256": "27cc0223b79ff95cac02f490600cc4de894dee66af739beca525502c424dae3f",
    "actualRegistrationIds": [
      204478,
      941006,
      710416,
      690814,
      774388,
      481522,
      627092,
      462570,
      673259
    ]
  },
  {
    "id": 741084,
    "source": "evidence/web/objects/257d1f445453cc81.js",
    "start": 27315,
    "end": 27398,
    "sha256": "1877fed09a6363588057a816a53c9d14fa46d3a3cb285321349a29a6ce48812a",
    "actualRegistrationIds": [
      741084
    ]
  },
  {
    "id": 741084,
    "source": "evidence/web/objects/ea5d7a76f15713d7.js",
    "start": 120,
    "end": 203,
    "sha256": "64085dc31cc9ebbcde019719b8096cfd198d84216b08826b70461fdfa689dc55",
    "actualRegistrationIds": [
      741084
    ]
  },
  {
    "id": 741084,
    "source": "evidence/web/objects/0746572aecdcf595.js",
    "start": 9345,
    "end": 9428,
    "sha256": "9fa49ca7090d955ed1650833d4a5adb620e11fd63ee88437701c50bd419832a2",
    "actualRegistrationIds": [
      741084
    ]
  },
  {
    "id": 860787,
    "source": "evidence/web/objects/16874c7781a81f3b.js",
    "start": 1626,
    "end": 2082,
    "sha256": "d27771d5ffd2a78b9b5857b8125fc606122c7b40a1e8e377da8cb34681036183",
    "actualRegistrationIds": [
      860787
    ]
  },
  {
    "id": 42413,
    "source": "evidence/web/objects/57cc59637a8b8f78.js",
    "start": 151,
    "end": 3615,
    "sha256": "f0b202d26ad75e1d9aadc926061d785b47852903a52e23b7e9d857947701b390",
    "actualRegistrationIds": [
      42413,
      124498,
      538661
    ]
  },
  {
    "id": 42413,
    "source": "evidence/web/objects/dd1b7e2a0ecbaed0.js",
    "start": 769,
    "end": 4233,
    "sha256": "f878ea2a9acadb4d09f80d1aa362916646f2e51555c822504e8d5b73b6604f3b",
    "actualRegistrationIds": [
      42413,
      124498,
      538661
    ]
  },
  {
    "id": 42413,
    "source": "evidence/web/objects/792e4653ff5b8a73.js",
    "start": 6397,
    "end": 9861,
    "sha256": "488d1075af93ee981e6f84f9445fc30a290528a553aec6e30992c60f8d3f074e",
    "actualRegistrationIds": [
      42413,
      124498,
      538661
    ]
  },
  {
    "id": 901423,
    "source": "evidence/web/objects/11be0c4b34eb27cb.js",
    "start": 138,
    "end": 983,
    "sha256": "f515cd70a96d9f3b7e526e1db1562addfc836f342bc8a03cd458b3bfe4b653c9",
    "actualRegistrationIds": [
      901423
    ]
  },
  {
    "id": 910976,
    "source": "evidence/web/objects/caaf847d63c97cce.js",
    "start": 138,
    "end": 20796,
    "sha256": "b04bad164bee7eb5d2d522441333d604f8717335f346bbdddbf21da0218068c5",
    "actualRegistrationIds": [
      910976
    ]
  },
  {
    "id": 910976,
    "source": "evidence/web/objects/57cc59637a8b8f78.js",
    "start": 3623,
    "end": 24281,
    "sha256": "647dd0376ef663b6da340773b4a58769cc066c178d915beb73c09226e1476af3",
    "actualRegistrationIds": [
      910976
    ]
  },
  {
    "id": 910976,
    "source": "evidence/web/objects/9535b69d76e2a69b.js",
    "start": 138,
    "end": 20796,
    "sha256": "0738155da4af4202bbeedb9bab586bc4de7fb3b88758f8eff110c4db187377f5",
    "actualRegistrationIds": [
      910976
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
    "id": 224540,
    "source": "evidence/web/objects/91795a66d4097dbd.js",
    "start": 18986,
    "end": 20088,
    "sha256": "fa4c24a30173babbf1ee7d3330994113f21398ac223eec0451855d0f0a719ca3",
    "actualRegistrationIds": [
      224540
    ]
  },
  {
    "id": 609252,
    "source": "evidence/web/objects/11ee2a97b2772408.js",
    "start": 10627,
    "end": 11967,
    "sha256": "912f6120ed5c5adada18e702e39e564e7331850bd43e70dba8e2a463322b1ac2",
    "actualRegistrationIds": [
      609252
    ]
  },
  {
    "id": 609252,
    "source": "evidence/web/objects/4a89a99471a66194.js",
    "start": 18026,
    "end": 19366,
    "sha256": "fd62996aae4f9d46364558e32c54cf36a60ea45f9f179828d2401919d8a1e10f",
    "actualRegistrationIds": [
      609252
    ]
  },
  {
    "id": 609252,
    "source": "evidence/web/objects/dd1b7e2a0ecbaed0.js",
    "start": 37360,
    "end": 38700,
    "sha256": "c438d25a94216ad8a89a14f0ce71124596a4a8b580ac1710ee533ea9a9c3f98a",
    "actualRegistrationIds": [
      609252
    ]
  },
  {
    "id": 609252,
    "source": "evidence/web/objects/8748d5c4832dda34.js",
    "start": 18026,
    "end": 19366,
    "sha256": "8771ebc2df8dd955abc0b4ef42903f675d51316eabc1b6eb986aaf3d4d6fd5dd",
    "actualRegistrationIds": [
      609252
    ]
  },
  {
    "id": 609252,
    "source": "evidence/web/objects/95be9180237024f4.js",
    "start": 16137,
    "end": 17477,
    "sha256": "7ef61705e1c15ac2dcf2d6153c2d6843ceb6f53c306560ee5165227139f9d873",
    "actualRegistrationIds": [
      609252
    ]
  },
  {
    "id": 609252,
    "source": "evidence/web/objects/767cc801e3f88f8b.js",
    "start": 21355,
    "end": 22695,
    "sha256": "cb75f05f0e1d6b8bf78ad8cf9cd47f6286c1d74f17a31c65605c7bc928752801",
    "actualRegistrationIds": [
      609252
    ]
  },
  {
    "id": 609252,
    "source": "evidence/web/objects/97dc53c5c25c1fdc.js",
    "start": 36171,
    "end": 37511,
    "sha256": "928189cf25fa929570eb47da831ac66ae42a85d448691959a830b3b633b497bc",
    "actualRegistrationIds": [
      609252
    ]
  },
  {
    "id": 609252,
    "source": "evidence/web/objects/7a7f27bff952614d.js",
    "start": 13383,
    "end": 14723,
    "sha256": "c331cdee07265e37444c19db6f0e4ff9adc834ca3ef104127606f1ac2e1b894a",
    "actualRegistrationIds": [
      609252
    ]
  },
  {
    "id": 609252,
    "source": "evidence/web/objects/a6c540af7c959989.js",
    "start": 39945,
    "end": 41285,
    "sha256": "3b7c5cf337dfbbf876d64310606abc6ca27b623d36e123fa582e1dc9514e6e0f",
    "actualRegistrationIds": [
      609252
    ]
  },
  {
    "id": 996699,
    "source": "evidence/web/objects/11be0c4b34eb27cb.js",
    "start": 35569,
    "end": 38436,
    "sha256": "ed63e668ee4c1a152a8ed9cf978da712d77e6d8ee907d78ae79638f5d35c9fca",
    "actualRegistrationIds": [
      996699
    ]
  },
  {
    "id": 576766,
    "source": "evidence/web/objects/11ee2a97b2772408.js",
    "start": 9003,
    "end": 10521,
    "sha256": "d71d7cbc509b8619fc3591afd3a1c5aeb2aa2b5a7580088698fcb59ad790aaf8",
    "actualRegistrationIds": [
      576766
    ]
  },
  {
    "id": 576766,
    "source": "evidence/web/objects/4a89a99471a66194.js",
    "start": 16402,
    "end": 17920,
    "sha256": "c9d2362d19eee6536aaab116d9ec019ec011c995017c6886b6a9a8f2ca86b936",
    "actualRegistrationIds": [
      576766
    ]
  },
  {
    "id": 576766,
    "source": "evidence/web/objects/dd1b7e2a0ecbaed0.js",
    "start": 35638,
    "end": 37156,
    "sha256": "b3de96c81ae6d6205cd5f13d449e55815c85619b58ed73ba22f10e6993dbfc4d",
    "actualRegistrationIds": [
      576766
    ]
  },
  {
    "id": 576766,
    "source": "evidence/web/objects/8748d5c4832dda34.js",
    "start": 16402,
    "end": 17920,
    "sha256": "fb0100b9baa71969933aebd94def4557e7b53edec061da398eaee8bd05f90900",
    "actualRegistrationIds": [
      576766
    ]
  },
  {
    "id": 576766,
    "source": "evidence/web/objects/7a7f27bff952614d.js",
    "start": 11759,
    "end": 13277,
    "sha256": "c4deda268fb386274132b30f774327d67cb46c49b45191fef2819a7ed427a342",
    "actualRegistrationIds": [
      576766
    ]
  },
  {
    "id": 576766,
    "source": "evidence/web/objects/7e6f3893ff9ff0f9.js",
    "start": 6925,
    "end": 8443,
    "sha256": "07ee5c11655dc8061867fc1f02c4403b5d47ff92060f9ac86581978ae46bb368",
    "actualRegistrationIds": [
      576766
    ]
  },
  {
    "id": 917341,
    "source": "evidence/web/objects/3740fc4e7a24596d.js",
    "start": 1201,
    "end": 8886,
    "sha256": "bd59c4bee5702bebd7d5a2b91640d9ed9c3170493c0809861e33f4c926744f3d",
    "actualRegistrationIds": [
      735821,
      917341,
      119675
    ]
  },
  {
    "id": 917341,
    "source": "evidence/web/objects/cf2bb278631744da.js",
    "start": 1201,
    "end": 8886,
    "sha256": "3adabf21c26e22024c9c08c3e218b88d0c052d972cf3c25779c1c8efc3350ba2",
    "actualRegistrationIds": [
      735821,
      917341,
      119675
    ]
  },
  {
    "id": 662986,
    "source": "evidence/web/objects/0fea5750534737b2.js",
    "start": 26153,
    "end": 29400,
    "sha256": "e3ade9570aef5bef1709871e34a348d5175fede0689284312028c2ca0f7517a4",
    "actualRegistrationIds": [
      790658,
      121742,
      662986
    ]
  },
  {
    "id": 662986,
    "source": "evidence/web/objects/316ff95d024f8997.js",
    "start": 26153,
    "end": 29400,
    "sha256": "5dcc6ddfc4d1c08e2852d9903a39eccd09764b4cd4d3d6b71db7a06b5178c5ce",
    "actualRegistrationIds": [
      790658,
      121742,
      662986
    ]
  },
  {
    "id": 187611,
    "source": "evidence/web/objects/a0ec47219f76f808.js",
    "start": 8440,
    "end": 8488,
    "sha256": "bd62a3ae8bc3cb897b656e246f762a897468e49c9752cfbe9e82f51de8397c3b",
    "actualRegistrationIds": [
      187611
    ]
  },
  {
    "id": 605587,
    "source": "evidence/web/objects/2c867fef5c76d400.js",
    "start": 138,
    "end": 1247,
    "sha256": "bceabd6341b002dbe14334459e7470c27ca90281762d8c10db07ed3044f57ea1",
    "actualRegistrationIds": [
      605587
    ]
  },
  {
    "id": 639374,
    "source": "evidence/web/objects/3740fc4e7a24596d.js",
    "start": 64056,
    "end": 64157,
    "sha256": "491277c531d85bf7569a6e10587108c9b7658ffe5dd0ee76852939c4e20b16c4",
    "actualRegistrationIds": [
      639374
    ]
  },
  {
    "id": 38406,
    "source": "evidence/web/objects/91795a66d4097dbd.js",
    "start": 18376,
    "end": 18978,
    "sha256": "3bcee2b7376565196f6beb836cf2c3021ac8a7217011c44af2540224baca8b3c",
    "actualRegistrationIds": [
      38406
    ]
  },
  {
    "id": 38406,
    "source": "evidence/web/objects/d5940e58ffa3866e.js",
    "start": 4134,
    "end": 4736,
    "sha256": "443fc5edd85a221e72dcf93299daff821d6fc2b56e0b048e6a9db838cbb78f9a",
    "actualRegistrationIds": [
      38406
    ]
  },
  {
    "id": 38406,
    "source": "evidence/web/objects/0e0a55c249b456d7.js",
    "start": 44327,
    "end": 44929,
    "sha256": "4c7f51745732930441e8216a94a3913e97a079c5ea96f80a207da71cf11b2ba6",
    "actualRegistrationIds": [
      38406
    ]
  },
  {
    "id": 38406,
    "source": "evidence/web/objects/a6c540af7c959989.js",
    "start": 37431,
    "end": 38033,
    "sha256": "7a9e3b4e49a53d22cce2c61f6cc3db125cede2d69ade524e9389a25d9a7bdd04",
    "actualRegistrationIds": [
      38406
    ]
  }
];
const print=n=>generate(n,{comments:false}).code;
const one=(node,p,label)=>exactlyOne(findNodes(node,p),label);
function declared(f,name){return exactlyOne(f.node.body.body.flatMap(n=>n.type==='VariableDeclaration'?n.declarations:n.type==='FunctionDeclaration'?[n]:[]).filter(n=>n.id?.name===name),`top-level declaration ${name}`);}
function exported(f,name){const arrays=findNodes(f.node,n=>n.type==='CallExpression'&&n.callee?.object?.name===f.runtime&&n.callee.property?.name==='s').map(n=>n.arguments[0]);const values=[];for(const a of arrays){if(a?.type!=='ArrayExpression')continue;for(let j=0;j<a.elements.length;j+=3)if(a.elements[j]?.value===name)values.push(a.elements[j+2]);}return exactlyOne(values,`export ${name}`);}
function cite(f,n,label,text=true){return{...f.witness(n,label),astType:n.type,...text?{text:f.text(n)}:{}};}
async function role(c,s){const cap=await c.javascript(s.source),reg=exactlyOne(cap.factories.filter(r=>r.node.start===s.start&&r.node.end===s.end&&r.ids.includes(s.id)),`actual physical registration ${s.id}`),w=cap.witness(reg.node,`factory ${s.id}`);assert.equal(w.sha256,s.sha256);assert.ok(c.index.modules.some(m=>m.sha256===s.sha256&&m.ids.includes(s.id)&&m.origins.some(o=>o.source===s.source&&o.start===s.start&&o.end===s.end)));assert.deepEqual(reg.ids,s.actualRegistrationIds);return{id:s.id,node:reg.node,runtime:reg.node.params[0].name,text:(n=reg.node)=>cap.text.slice(n.start,n.end),witness:(n,label)=>cap.witness(n,label),provenance:{id:s.id,actualRegistrationIds:reg.ids,...w}};}
async function mainAdmission(c){const cap=await c.capture('evidence/web/objects/b713215f09b03c14');assert.equal(cap.record.url,'https://pump.fun/');assert.equal(cap.record.sha256,'5c54a668997394767a338ff5efe132ba3400bd5e1c4b6bb16c9c075b6a389409');const fragments=[];for(const m of cap.text.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)){if(!m[1].includes('__next_f'))continue;const ast=parse(m[1],{sourceType:'script'});for(const call of findNodes(ast,n=>n.type==='CallExpression'&&n.callee?.object?.type==='MemberExpression'&&n.callee.object.object?.name==='self'&&n.callee.object.property?.name==='__next_f'&&n.callee.property?.name==='push')){const a=call.arguments[0];if(a?.type==='ArrayExpression'&&a.elements[0]?.value===1&&a.elements[1]?.type==='StringLiteral')fragments.push(a.elements[1].value);}}const flight=new Map(fragments.join('').split('\n').map(line=>{const i=line.indexOf(':');return[line.slice(0,i),line.slice(i+1)];}));assert.equal(flight.get('8f')[0],'I');const imported=JSON.parse(flight.get('8f').slice(1));assert.equal(imported[0],163807);assert.equal(imported[2],'HomeView');const uses=[];function walk(n,p=[]){if(!n||typeof n!=='object')return;if(Array.isArray(n)&&n[0]==='$'&&n[1]==='$L8f')uses.push({path:['18',...p],props:n[3]});for(const[k,v]of Object.entries(n))walk(v,[...p,k]);}walk(JSON.parse(flight.get('18')));assert.equal(uses.length,1);return{root:{source:'evidence/web/objects/b713215f09b03c14',url:cap.record.url,bytes:cap.bytes.length,sha256:cap.record.sha256},flightImport:{id:'8f',value:imported},elementUses:uses,path:'root Flight→163807.HomeView conditional mobile eH→ez→eG',scope:'Static conditional MAIN admission only; no captured row observation or Home/eH/provider execution.'};}
export async function recover(root=APP_ROOT){
 const corpus=await openCorpus(root),roles=[];for(const s of EXPECTED)roles.push(await role(corpus,s));
 for(const id of new Set(EXPECTED.map(r=>r.id)))assert.deepEqual(corpus.index.modules.filter(m=>m.ids.includes(id)).map(m=>m.sha256).sort(),EXPECTED.filter(r=>r.id===id).map(r=>r.sha256).sort(),`all indexed physical variants ${id}`);
 const get=id=>exactlyOne(roles.filter(r=>r.id===id),`unique dependency ${id}`),core=get(163807),home=exported(core,'HomeView'),parent=declared(core,'eH');
 const names=['eD','eB','eG','eO','eq','eK','ez'],variables=names.map(n=>declared(core,n)),fnNames=['h','eW','eV','eZ','eJ','eX','eY'],functions=fnNames.map(n=>declared(core,n));
 const kinds=Object.fromEntries(variables.map(n=>[n.id.name,exactlyOne(core.node.body.body.filter(s=>s.type==='VariableDeclaration'&&s.declarations.includes(n)),`parent declaration ${n.id.name}`).kind]));for(const kind of Object.values(kinds))assert.equal(kind,'let');
 const slots=n=>findNodes(n,x=>x.type==='CallExpression'&&x.callee.type==='SequenceExpression'&&x.callee.expressions.at(-1)?.object?.name==='l'&&x.callee.expressions.at(-1)?.property?.name==='c').map(x=>x.arguments[0]?.value);
 assert.deepEqual(slots(declared(core,'eG')),[91]);assert.deepEqual(slots(declared(core,'eB')),[9]);assert.deepEqual(slots(declared(core,'h')),[42]);assert.deepEqual(slots(declared(core,'eq')),[8]);assert.deepEqual(slots(declared(core,'eO')),[1]);
 const flag=n=>one(get(322315).node,x=>x.type==='AssignmentExpression'&&x.left?.property?.name===n&&x.right?.type==='StringLiteral',`actual flag ${n}`).right;
 const perps=flag('WEB_PERPS'),packs=flag('WEB_PACKS'),width=objectProperty(exported(get(860787),'z'),'list');assert.equal(width.value,40);
 const select=declared(core,'ez'),incoming=one(parent,n=>n.type==='CallExpression'&&n.callee?.name==='ez','complete actual parent selection call'),outgoing=one(select,n=>n.type==='CallExpression'&&n.arguments[0]?.name==='eG','complete actual list JSX handoff');
 const list=declared(core,'eG');const effect=one(list,n=>n.type==='CallExpression'&&n.callee.type==='SequenceExpression'&&n.callee.expressions.at(-1)?.property?.name==='useEffect','complete list scroll effect');
 const hookCalls=findNodes(list,n=>n.type==='CallExpression'&&n.callee.type==='SequenceExpression'&&['ef','e_','eg','ev'].includes(n.callee.expressions.at(-1)?.object?.name));assert.equal(hookCalls.length,4);
 const mapCall=one(list,n=>n.type==='CallExpression'&&n.callee?.object?.name==='eo'&&n.callee?.property?.name==='map','complete list row dispatcher');
 const rowCallback=one(list,n=>n.type==='ArrowFunctionExpression'&&n.params.length===2&&findNodes(n,x=>x.type==='CallExpression'&&x.arguments[0]?.name==='eB').length===1&&findNodes(n,x=>x.type==='CallExpression'&&x.arguments[0]?.name==='h').length===1,'complete memoized row map callback');
 const rowCalls=findNodes(rowCallback,n=>n.type==='CallExpression'&&['h','eB'].includes(n.arguments[0]?.name)||n.type==='CallExpression'&&n.arguments[0]?.object?.name==='c'&&n.arguments[0]?.property?.name==='f');assert.equal(rowCalls.length,3);
 const source=`export function createMobileFeedList({React,compiler,jsxRuntime,window,useFeatureFlag,usePositionsRead,useCoins,usePackCards,useUsers,isCollectibleEntry,isBase58Pubkey,normalizeMintKey,isPerpRow,useOpenPositionGate,PendingBanner,LoadMore,CalloutEntry,MainFeedRow,PositionInsert,RootCallout,Link,profileRoute,shortenAddress,normalizeImage,buildImage,RepostIcon,EmptyIcon,labelText}){
 const t=jsxRuntime,l={c:compiler},i=React,a={I3:RepostIcon,EX:EmptyIcon},n={D:{WEB_PERPS:${print(perps)},WEB_PACKS:${print(packs)}}},o={k:useFeatureFlag},c={f:MainFeedRow},u={$:profileRoute},m={d:shortenAddress},f={default:Link},p={f:PositionInsert},g={f:RootCallout},b={f:normalizeImage},x={Z:buildImage,z:{list:${print(width)}}},w={f:LoadMore},y={f:PendingBanner},v={f:CalloutEntry},J={f:useOpenPositionGate},ef={f:usePositionsRead},e_={f:useCoins},eg={f:usePackCards},ev={f:useUsers},eN={Q:isCollectibleEntry},ek={l:isPerpRow},eM={T:labelText},eP={c:normalizeMintKey},eT={f:isBase58Pubkey};
 ${variables.map(n=>`${kinds[n.id.name]} ${print(n)};`).join('\n')}
 ${functions.map(print).join('\n')}
 return{FeedList:eG,selectFeed:ez,RepostRow:h,EmptyState:eq,Skeleton:eO};
 }`;
 const client=generate(parse(source,{sourceType:'module'}),{comments:false}).code+'\n';
 const witnesses=[...variables.map(n=>cite(core,n,`complete used variable ${n.id.name}`)),...functions.map(n=>cite(core,n,`complete used helper ${n.id.name}`)),cite(core,home,'complete original MAIN Home viewport boundary, static only',false),cite(core,parent,'complete incoming mobile Home owner, static only',false),cite(core,incoming,'actual incoming eH to ez call'),cite(core,outgoing,'actual complete ez to list descriptor'),cite(core,effect,'complete passive scroll effect handoff'),cite(core,mapCall,'actual row map application'),cite(core,rowCallback,'complete memoized all row dispatch branches'),...hookCalls.map((n,k)=>cite(core,n,`actual required read snapshot port ${k}`)),...rowCalls.map((n,k)=>cite(core,n,`actual row renderer handoff ${k}`)),cite(get(322315),perps,'actual WEB_PERPS key'),cite(get(322315),packs,'actual WEB_PACKS key'),cite(get(860787),width,'credited source list image width'),...roles.filter(r=>r.id!==163807).map(r=>cite(r,r.node,`required external dependency ${r.id}`,false))];
 const admission=await mainAdmission(corpus);
 const contract={schemaVersion:1,baseCommit:'094a06f18df738d41e77070c1a009e135671ac1a',sources:roles.map(r=>r.provenance),mainAdmission:admission,witnesses,
 implementation:{factory:163807,owners:['eG','eB','h','eq','eO'],selection:'ez',declarationKinds:kinds,compilerFrames:[91,9,42,8,1],compilerSlots:151,clientSha256:sha256(Buffer.from(client)),mounted:false},
 incoming:{parent:'eH',call:core.witness(incoming,'actual incoming eH to ez'),outgoing:core.witness(outgoing,'actual ez to eG'),scope:'Full parent/provider/auth/read implementations remain static evidence; only selected complete display owner and its used helpers are emitted.'},
 ports:{readerNamespaces:{ef:224540,e_:609252,eg:996699,ev:576766,J:38406},renderNamespaces:{c:349919,g:204478,v:910976,p:335703,y:901423,w:42413},classifiers:{eN:917341,eT:639374,eP:605587,ek:662986},clock:'Required supplied window scrollY/scrollTo/addEventListener/removeEventListener; no global acquisition.'},
 preserved:{ordering:'All user/mint/position collection and read-snapshot hooks precede loading/error/empty return. Metadata intake uses unfiltered raw rows; feature admission only changes displayed rows.',joins:'Raw Set identity for input mints/users, normalized last-wins coin map, raw last-wins user map, pending-preview image handoff; pack requests skip source-defined conditions without additional schema admission.',rows:'Callout gate hook always runs per mounted callout; hide only for applyOpenPositionGate&&shouldHide. Trade returns null; reply/quote/repost exact metadata and supplied positionRead handoffs.',reveal:'Tap calls showNew({trigger:tap}) then smooth scrollTo. Auto effect admits nonzero count and supplied scrollY<=8, invokes immediately then passive listener, removes on dependency change/unmount.',selection:'Complete three-tab label mapping and signed-out empty state are preserved from actual ez/eH boundary.',helpers:'Complete original repost attribution/root-card props, six skeleton row shapes, empty display and all collectors are emitted; shared row/banner/pagination primitives remain required credited ports.'},
 credited:['Accepted/open Home99859/Following1966/TOP read-state work remains external, no query/read/cache core copied.','349919/710416/204478 ordinary row/root-card owners are required exact renderer ports; no open-PR runtime import.','Existing profile-route/image/classifier/user-batch/coin/pack/position APIs retain their exact source interfaces and all selected variants; no new financial/provider implementation credit.'],
 limits:['Captured factories and parent eH are parsed/inert source evidence, never executed. Only the authored/transcribed selected full display owner executes through supplied capabilities.','No actual Home/provider/cache/query/financial reader/schema/calculation/action, account/wallet/auth/follow/session/credential/cookie, protected acquisition, submit/upload/signing/transaction, link/media navigation or original runtime/native/API/visual/security/milestone claim.','Supplied read/flag/classifier/render/scroll ports qualify exact argument/result/branch delegation, not original provider admission or policies. All52selected source variants are bound; no active loader/provider winner inferred.']};
 return{client,contract};
}
export async function verify(root=APP_ROOT,supplied={}){const{client,contract}=await recover(root),expected={client:Buffer.from(client),contract:Buffer.from(JSON.stringify(contract,null,2)+'\n')};for(const[key,p]of[['client',CLIENT],['contract',CONTRACT]])assert.ok((supplied[key]??await readFile(path.join(root,p))).equals(expected[key]),`${key} canonical source-derived bytes differ`);return{sources:contract.sources.length,witnesses:contract.witnesses.length,compilerSlots:151,mainConditional:true,mounted:false};}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){try{assert.equal(process.argv.length,3);assert.ok(['--write','--check'].includes(process.argv[2]));if(process.argv[2]==='--write'){const{client,contract}=await recover();await mkdir(path.dirname(path.join(APP_ROOT,CLIENT)),{recursive:true});await writeFile(path.join(APP_ROOT,CLIENT),client);await writeFile(path.join(APP_ROOT,CONTRACT),JSON.stringify(contract,null,2)+'\n');}console.log(JSON.stringify(await verify()));}catch(error){console.error(error.stack);process.exitCode=1;}}
