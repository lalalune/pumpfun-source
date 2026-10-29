import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { parse } from "@babel/parser";
import prettier from "prettier";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  member,
  propertyName,
  sha256,
} from "./original-contracts/source.mjs";
export const APP_ROOT = fileURLToPath(new URL("..", import.meta.url));
export const DIRECTORY = "reconstruction/notifications-controller";
const SOURCES = [
  [
    32596,
    "9bafadffbe6dc98b.js",
    "2043420e15f1b6542bea4e38a8f66f3a9fed93c4e543485fd94ae3f438cfd973",
  ],
  [
    979364,
    "c9d58b1f7b1c6f01.js",
    "db3246114ccffa1cfbee1b6dbf3c07a1162ad3faf236919041d828b76aa5e76b",
  ],
  [
    917781,
    "c9d58b1f7b1c6f01.js",
    "d1d7a6dcbad811206039a166046faaf8bf8aa513b483cab9731c013ce5b29573",
  ],
  [
    589428,
    "9bafadffbe6dc98b.js",
    "4d12898c1c6cd0bc4e8518537175ecf57e5edf14a6723c4c15f8aad0bf97a400",
  ],
  [
    779106,
    "fd402d4185b44ce9.js",
    "e1e29868ec56b56bdbc68b58127f2c71583094d14645020b53c733a7be06423b",
  ],
  [
    132838,
    "fd402d4185b44ce9.js",
    "fbc2c07dc4a3b6115974dbb1450e6ae908076af074bdec1639ade3013ec0331a",
  ],
  [
    484018,
    "9bafadffbe6dc98b.js",
    "af69e8c3ce32e52df2d3b68167cf562cc78b494fbc10c171e314193e06471fbe",
  ],
];
function declarations(f) {
  return f.node.body.body.flatMap((n) =>
    n.type === "VariableDeclaration"
      ? n.declarations
      : n.type === "FunctionDeclaration"
        ? [n]
        : [],
  );
}
function local(f, name) {
  return exactlyOne(
    declarations(f).filter((n) => n.id?.name === name),
    "module declaration " + name,
  );
}
function exportsOf(f, id) {
  const call = exactlyOne(
      findNodes(
        f.node,
        (n) =>
          n.type === "CallExpression" &&
          member(n.callee, f.runtime, "s") &&
          (n.arguments[1]?.value === id ||
            (!n.arguments[1] && f.ids.length === 1)),
      ),
      "actual exports " + id,
    ),
    a = call.arguments[0].elements,
    out = new Map();
  for (let i = 0; i < a.length; i += 3) {
    assert.equal(a[i].type, "StringLiteral");
    assert.equal(a[i + 1].value, 0);
    let v = a[i + 2];
    if (v.type === "Identifier") {
      const n = local(f, v.name);
      v = n.type === "VariableDeclarator" ? n.init : n;
    }
    out.set(a[i].value, v);
  }
  return out;
}
const cite = (f, n, label) => ({ ...f.witness(n, label), text: f.text(n) });
const ignored = new Set([
  "start",
  "end",
  "loc",
  "extra",
  "leadingComments",
  "trailingComments",
  "innerComments",
]);
// Strict singleton-context AST equality. No lexical/type/operation masking.
function ast(v) {
  if (Array.isArray(v)) return v.map(ast);
  if (!v || typeof v !== "object") return v;
  return Object.fromEntries(
    Object.entries(v)
      .filter(([k]) => !ignored.has(k))
      .map(([k, v]) => [k, ast(v)]),
  );
}
const required = [
  "memoCache",
  "useAvailability",
  "useFlag",
  "useAuthSnapshot",
  "useViewerKey",
  "usePathname",
  "useApiClient",
  "useQueryClient",
  "useMutation",
  "getConfigurationIndicator",
  "getDeviceHandle",
  "getMessagingHandle",
  "getRegistrationHandle",
  "removeRegistration",
  "onMessage",
  "foregroundMessage",
  "invalidateInbox",
  "reportError",
  "useTranslation",
];
export async function recover(root = APP_ROOT) {
  const corpus = await openCorpus(root),
    selected = new Map(),
    factories = [];
  for (const [id, file, hash] of SOURCES) {
    const cohort = corpus.index.modules.filter((m) => m.ids.includes(id));
    assert.equal(cohort.length, 1, "new variants require review " + id);
    const f = await corpus.factory(id, {
      source: "evidence/web/objects/" + file,
    });
    assert.equal(f.provenance.sha256, hash, "factory changed " + id);
    selected.set(id, f);
    factories.push(f.provenance);
  }
  const f = selected.get(32596),
    ex = exportsOf(f, 32596),
    provider = ex.get("Q"),
    reader = ex.get("y"),
    permission = local(f, "C").init,
    prompt = selected.get(979364),
    promptFn = exportsOf(prompt, 979364).get("NotificationPermissionPrompt");
  const flag = await corpus.factory(322315),
    flagDM = exactlyOne(
      findNodes(
        flag.node,
        (n) =>
          n.type === "AssignmentExpression" &&
          propertyName(n.left.property) === "WEB_DIRECT_MESSAGES",
      ),
      "DM flag literal",
    );
  assert.equal(flagDM.right.value, "webDirectMessages");
  const namespace = [
    "const t=ports.jsxRuntime,n={c:ports.memoCache},i=ports.React,r={D:{WEB_DIRECT_MESSAGES:" +
      JSON.stringify(flagDM.right.value) +
      "}},a={k:ports.useFlag},s={useHermesApiClient:ports.useApiClient},l={F:ports.useAuthSnapshot},o={useQueryClient:ports.useQueryClient},u={f:ports.useAvailability},d={usePathname:ports.usePathname},f={f:ports.useMutation},ei={f:ports.useViewerKey},en={l:ports.reportError},m={O:ports.invalidateInbox},c={onMessage:ports.onMessage};",
    "const w=ports.getConfigurationIndicator,g=ports.getDeviceHandle,S=ports.getMessagingHandle,U=ports.getRegistrationHandle,R=ports.removeRegistration,et=ports.foregroundMessage;",
    'const window=Object.create(ports.browserFacade),Notification=ports.notificationFacade;Object.defineProperty(window,"localStorage",{value:ports.markerStorage});',
  ].join("\n");
  const decls = ["er", "ea", "es", "el"];
  const providerSource = [
    namespace,
    ...decls.map((n) => "let " + f.text(local(f, n)) + ";"),
    "const C=" + f.text(permission) + ";",
    "const Provider=" + f.text(provider) + ";",
    "const useNotificationsContext=" + f.text(reader) + ";",
  ].join("\n");
  const promptCode = [
    "function createPermissionPrompt(ports,useNotificationsContext){",
    "const t=ports.jsxRuntime,i={c:ports.memoCache},a={K:ports.Button},n={default:ports.Link},r={f:ports.useTranslation},s={f:ports.useAvailability},l={y:useNotificationsContext};",
    "return " + prompt.text(promptFn) + ";",
    "}",
  ].join("\n");
  const text = await prettier.format(
    [
      "// Full selected original controller; every acquisition/provider/browser capability is explicit.",
      promptCode,
      "export function createNotificationsController(ports){",
      "for(const name of " +
        JSON.stringify(required) +
        ')if(typeof ports?.[name]!=="function")throw new TypeError("Explicit notification capability required: "+name);',
      'for(const name of ["createContext","useContext","useState","useRef","useEffect","useCallback"])if(typeof ports.React?.[name]!=="function")throw new TypeError("Explicit React capability required: "+name);',
      'if(!["jsx","jsxs"].every(n=>typeof ports.jsxRuntime?.[n]==="function"))throw new TypeError("Explicit JSX runtime required");',
      'if(!ports.browserFacade||typeof ports.browserFacade!=="object"||!Object.hasOwn(ports,"notificationFacade"))throw new TypeError("Explicit inert browser/Notification facades required");',
      'if(!["getItem","setItem","removeItem"].every(n=>typeof ports.markerStorage?.[n]==="function"))throw new TypeError("Explicit marker storage facade required");',
      'if(!ports.Button||!ports.Link)throw new TypeError("Explicit source button/link rendering capabilities required");',
      providerSource,
      "return {Provider,useNotificationsContext,PermissionPrompt:createPermissionPrompt(ports,useNotificationsContext),requestPermission:C};",
      "}",
    ].join("\n"),
    { parser: "babel", singleQuote: false },
  );
  const emitted = parse(text, { sourceType: "module" });
  const constructor = exactlyOne(
    findNodes(
      emitted,
      (n) =>
        n.type === "FunctionDeclaration" &&
        n.id.name === "createNotificationsController",
    ),
    "controller constructor",
  );
  const emittedDeclarations = constructor.body.body.flatMap((n) =>
    n.type === "VariableDeclaration" ? n.declarations : [],
  );
  for (const [name, node] of [
    ["Provider", provider],
    ["useNotificationsContext", reader],
    ["C", permission],
    ...decls.map((n) => [n, local(f, n).init]),
  ]) {
    const out = exactlyOne(
      emittedDeclarations.filter((n) => n.id?.name === name),
      "emitted constructor binding " + name,
    ).init;
    assert.deepEqual(
      ast(out),
      ast(node),
      "complete original node changed " + name,
    );
  }
  const emittedPrompt = exactlyOne(
    findNodes(
      emitted,
      (n) =>
        n.type === "FunctionDeclaration" &&
        n.id.name === "createPermissionPrompt",
    ),
    "prompt wrapper",
  ).body.body.at(-1).argument;
  assert.deepEqual(
    ast(emittedPrompt),
    ast(promptFn),
    "complete original prompt changed",
  );
  const mutation = exactlyOne(
    findNodes(
      provider,
      (n) =>
        (n.type === "ObjectProperty" || n.type === "ObjectMethod") &&
        propertyName(n.key) === "mutationFn",
    ),
    "used registration mutation callback",
  );
  const mount = selected.get(589428),
    mountImport = exactlyOne(
      findNodes(
        mount.node,
        (n) =>
          n.type === "VariableDeclarator" &&
          n.init?.arguments?.[0]?.value === 32596,
      ),
      "actual provider import",
    ),
    mountCall = exactlyOne(
      findNodes(
        mount.node,
        (n) =>
          n.type === "CallExpression" &&
          n.arguments[0]?.type === "MemberExpression" &&
          member(n.arguments[0], mountImport.id.name, "Q"),
      ),
      "actual provider mount",
    );
  const settings = selected.get(917781),
    settingsUse = exactlyOne(
      findNodes(
        settings.node,
        (n) =>
          n.type === "ObjectProperty" &&
          propertyName(n.key) === "enablePushNotifications",
      ),
      "actual settings consumer",
    );
  const dependencies = [];
  for (const p of [
    "reconstruction/notifications-foreground/client.mjs",
    "reconstruction/notifications-foreground/contract.json",
    "reconstruction/notifications-inbox/client.mjs",
    "reconstruction/notifications-inbox/contract.json",
    "contracts/settings-client-recovery.json",
  ])
    dependencies.push({
      path: p,
      sha256: sha256(await readFile(path.join(root, p))),
    });
  const contract = {
    schemaVersion: 1,
    base: "094a06f18df738d41e77070c1a009e135671ac1a",
    scope:
      "Full selected32596Q/y provider/controller +C permission helper +full979364prompt; inert source-signature ports only",
    factories,
    module: {
      path: DIRECTORY + "/client.mjs",
      sha256: sha256(Buffer.from(text)),
    },
    strictAstProof: {
      normalization:
        "Parser positions/comments/raw spelling metadata only; all original identifiers/types/operations/branches/bindings retained; no alpha or operation masks",
      nodes: [
        ["Provider", provider],
        ["useNotificationsContext", reader],
        ["requestPermission", permission],
        ...decls.map((n) => [n, local(f, n).init]),
      ].map(([name, n]) => ({
        name,
        sha256: sha256(JSON.stringify(ast(n))),
        source: cite(f, n, name),
      })),
      prompt: {
        sha256: sha256(JSON.stringify(ast(promptFn))),
        source: cite(prompt, promptFn, "complete permission prompt"),
      },
    },
    mutation: cite(
      f,
      mutation,
      "actual token/platform/device request builder; no provider request executed",
    ),
    flag: {
      factory: flag.provenance,
      witness: cite(flag, flagDM, "actual DM feature flag literal"),
    },
    caller: {
      settings: cite(
        settings,
        settingsUse,
        "actual settings context callback consumption",
      ),
      mountImport: cite(mount, mountImport, "actual provider import"),
      mount: cite(
        mount,
        mountCall,
        "actual provider mount only; auth root excluded",
      ),
    },
    dependencies,
    acquisitionPorts: [
      {
        name: "getConfigurationIndicator",
        source: cite(
          f,
          local(f, "w"),
          "original unavailable configuration acquisition; attribution only",
        ),
        contract:
          "() => null | nonnull opaque indicator; controller consumes nullness only, no configuration/env values acquired",
      },
      {
        name: "getDeviceHandle",
        source: cite(
          f,
          local(f, "g"),
          "original device acquisition; attribution only",
        ),
        contract:
          "() => supplied synthetic noncredential string; no device/storage/random acquisition",
      },
      ...[
        [
          "getMessagingHandle",
          "S",
          "() => Promise<opaque messaging handle|null>",
        ],
        [
          "getRegistrationHandle",
          "U",
          "() => Promise<supplied synthetic noncredential string|null>",
        ],
        ["removeRegistration", "R", "() => Promise<unknown>"],
      ].map(([name, n, signature]) => ({
        name,
        source: cite(
          f,
          local(f, n),
          "original provider boundary; not adapted or executed",
        ),
        contract:
          signature +
          "; no Firebase/SW/registration/deletion/subscription/provider acquisition",
      })),
    ],
    externalHooks: {
      required,
      viewer: {
        factory: selected.get(779106).provenance,
        signature:
          'useViewerKey("push-token") => supplied viewer identity key|null; auth/identity acquisition remains outside',
      },
      mutation: {
        factory: selected.get(132838).provenance,
        signature:
          "useMutation({mutationFn}) => {mutateAsync}; opaque actual query lifecycle, no TanStack scheduling implementation",
      },
      browser:
        "Explicit inert availability/Notification facade and selected-marker Storage-shaped methods only. No fallback to real window/Notification/storage APIs.",
      messaging:
        "onMessage(handle,callback) => unsubscribe; explicit synthetic callback host only, no actual subscription",
      foreground:
        "foregroundMessage({payload,pathname,hermesApi,queryClient,isDirectMessagesEnabled}); bridge to credited existing foreground handler with host-owned capabilities",
      inbox: {
        factory: selected.get(484018).provenance,
        signature: "invalidateInbox({queryClient,viewer})",
      },
      readiness:
        "useAuthSnapshot() => {authReady,fetchUser}; external read-only auth state/callback, no session or account acquisition",
    },
    credit: [
      "Existing foreground received-message handler/confirmation/inbox/Hermes settings attribution unchanged",
      "Existing917781field/callback inventory/settings UI unchanged; new recovery is whole controller/lifecycle+full prompt source",
      "Existing12dated Hermes configurations are false; no current availability/provider winner is established",
    ],
    limits: [
      "No real credentials/config/env/cookie/session/token/device/storage/NotificationAPI/Firebase/SW/network/subscription acquisition or calls",
      "Tests may supply only explicitly synthetic noncredential strings/results and inert facades",
      "Registration callbacks preserve source equality refs/ordering/finally; no stronger concurrency/ownership/security/cancellation guarantee",
      "Token state can precede registration success; registration continuation has no added unmount guard; late messaging installation alone is canceled",
      "No backend/auth/provider implementation, live notifications, product mount, native/API/visual/security equivalence or completion milestone",
    ],
  };
  return { text, contract };
}
export async function verify(root = APP_ROOT) {
  const r = await recover(root);
  assert.equal(
    await readFile(path.join(root, DIRECTORY, "client.mjs"), "utf8"),
    r.text,
    "notification controller module differs",
  );
  assert.equal(
    await readFile(path.join(root, DIRECTORY, "contract.json"), "utf8"),
    JSON.stringify(r.contract, null, 2) + "\n",
    "notification controller contract bytes differ",
  );
  return r.contract;
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  assert.ok(
    process.argv.length === 3 &&
      ["--write", "--check"].includes(process.argv[2]),
    "Use --write|--check",
  );
  if (process.argv[2] === "--write") {
    const r = await recover();
    await mkdir(path.join(APP_ROOT, DIRECTORY), { recursive: true });
    await writeFile(path.join(APP_ROOT, DIRECTORY, "client.mjs"), r.text);
    await writeFile(
      path.join(APP_ROOT, DIRECTORY, "contract.json"),
      JSON.stringify(r.contract, null, 2) + "\n",
    );
  } else await verify();
  console.log(
    "PASS strict full Notifications controller/context/permission/prompt ASTs; all acquisition ports explicit",
  );
}
