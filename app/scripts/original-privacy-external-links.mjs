#!/usr/bin/env node
// Authenticate and parse captured factories as data; never execute them.
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { generate } from "@babel/generator";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  propertyName,
  objectProperty,
  literal,
  sha256,
} from "./original-contracts/source.mjs";
const defaultRoot = fileURLToPath(new URL("..", import.meta.url));
export const outputPath = "reconstruction/privacy-external-links/contract.json";

// Current UI qualification selects a new packet. The original app-browser
// receipt/screenshots remain immutable historical evidence for the old control.
export const appBrowserDirectory =
  "research/footer-link-confirmation-20261029/browser";
export const appBrowserInputs = [
  "reconstruction/privacy-external-links/client.mjs",
  "reconstruction/privacy-external-links/client.d.mts",
  outputPath,
  "packages/frontend/src/components/settings/privacy-setting-control.tsx",
  "packages/frontend/src/components/settings/privacy-setting-control.module.css",
  "packages/frontend/src/components/settings/settings-control.tsx",
  "packages/frontend/src/components/links/footer-outbound-links.tsx",
  "packages/frontend/src/components/links/footer-outbound-links.module.css",
  "packages/frontend/src/components/shell/SiteFooter.tsx",
  "packages/frontend/src/components/shell/FooterMenu.tsx",
  "packages/frontend/src/components/ui/dropdown-menu.tsx",
  "packages/frontend/src/config/navigation.ts",
  "packages/frontend/src/lib/body-scroll-lock.ts",
  "packages/frontend/src/app/create-draft-links.tsx",
  "packages/frontend/src/app/create-draft-links.module.css",
  "packages/frontend/playwright.config.ts",
  "packages/frontend/tests/footer-privacy.spec.ts",
  "tests/footer_privacy.browser.mjs",
  "scripts/original-privacy-external-links.mjs",
];
export const appBrowserCaseTitles = [
  "footer Blog confirms and cancellation preserves its native anchor and page",
  "remembered footer choice updates Settings and survives reload",
  "footer portal menu can unmount while confirmation survives and returns focus",
  "mobile footer Resources and SVG social links use the same preference",
  "opening exceptions retain recovery, retry and a native browser fallback",
  "failed remembered-choice storage warns and its page fallback resets on reload",
  "footer choice is immediately shared with unchanged Create preview links",
  "server-rendered footer preserves native anchors before enhancement",
];

const compact = (node) =>
  generate(node, { compact: true, comments: false }).code;
const require = (ok, reason) => {
  if (!ok) throw Error(`Privacy recovery: ${reason}`);
};
const target = (node) =>
  node?.type === "SequenceExpression" ? node.expressions.at(-1) : node;
const call = (node, property) =>
  node?.type === "CallExpression" &&
  propertyName(target(node.callee)?.property) === property;
const one = (node, predicate, label) =>
  exactlyOne(findNodes(node, predicate), label);
const imported = (mod) =>
  new Map(
    findNodes(
      mod.node,
      (n) => n.type === "VariableDeclarator" && call(n.init, "i"),
    ).map((n) => [n.id.name, literal(n.init.arguments[0])]),
  );
function exported(mod, id, name) {
  const result = [];
  for (const node of findNodes(
    mod.node,
    (n) => call(n, "s") && n.arguments[0]?.type === "ArrayExpression",
  )) {
    if (node.arguments[1] ? literal(node.arguments[1]) !== id : mod.id !== id)
      continue;
    const values = node.arguments[0].elements;
    for (let i = 0; i < values.length; i += 3)
      if (literal(values[i]) === name) result.push(values[i + 2]);
  }
  return exactlyOne(result, `${id}.${name} export`);
}
const topFunction = (mod, id) =>
  one(
    mod.node,
    (n) => n.type === "FunctionDeclaration" && n.id.name === id,
    `function ${id}`,
  );

export async function recover(root = defaultRoot) {
  const corpus = await openCorpus(root);
  const modules = await Promise.all(
    [956718, 654506, 547562, 272700, 402732, 671027].map((id) =>
      corpus.factory(id),
    ),
  );
  const [definitions, storage, settingHook, registry, gate, initialization] =
    modules;
  const fixedPins = {
    654506: "cd05dc62f9956f8ea48d33067cbc67a501f0ef83c437dbecef71a5c934f426a2",
    547562: "ac16d554995f53e21d96460670653f0cfc0bf606f982870a485cecd0d9be000d",
    272700: "0678f532c48fab10585e87f8593aef21d77a29e4a69fe6d872ecc270c651eabc",
    402732: "9cc0aef7c1be1145522dfc9e78a02dd7223600dea4ec1d8dea27a5f8de4ba560",
    671027: "0b614443bf3813dea444e682593f9f8b3e4718045e2429e3c4399b09e0fe31d7",
  };
  for (const mod of modules)
    if (fixedPins[mod.id])
      require(sha256(compact(mod.node)) ===
        fixedPins[mod.id], `review changed ${mod.id} semantics`);
  const definition = one(
    definitions.node,
    (n) =>
      n.type === "ObjectProperty" &&
      propertyName(n.key) === "privacy.confirmExternalLinks",
    "privacy descriptor",
  ).value.arguments[0];
  require(literal(objectProperty(definition, "scope")) === "device" &&
    literal(objectProperty(definition, "default")) === true &&
    compact(objectProperty(definition, "coerce")) ===
      "e=>!1!==e", "device default/coercion");
  require(!definition.properties.some(
    (n) => propertyName(n.key) === "legacy",
  ), "privacy has no legacy adoption list");
  const adapter = objectProperty(definition, "adapter");
  require(imported(definitions).get(target(adapter.callee).object.name) ===
    654506, "actual storage adapter");
  const options = adapter.arguments[0],
    key = literal(objectProperty(options, "key")),
    codec = literal(objectProperty(options, "codec"));
  require(key === "privacy.confirm-external-links" &&
    codec === "json", "actual selected device key/codec");
  require(imported(settingHook).get("s") === 272700 &&
    imported(settingHook).get("i") ===
      671027, "registry and initializer edges");
  one(
    registry.node,
    (n) => n.type === "SpreadElement" && compact(n.argument) === "t.n",
    "privacy section registry spread",
  );
  require(imported(registry).get("t") ===
    956718, "actual privacy registry import");
  const eventName = one(
    storage.node,
    (n, parents) =>
      n.type === "VariableDeclarator" &&
      n.id.name === "t" &&
      parents.at(-2) === storage.node.body,
    "local event name",
  ).init;
  const hookPins = new Set([
    "d0897ba5b859535df7623a131cd66accef3ed094b377e0a93df6b954c53c1be2",
    "9083827d4fabad9af16ff21b0e9e98eb3386c0ce0c6955488e4e0d6ec7c2ab47",
    "e8c32e16bd2a06c05e099184a577c21539af09e07e3cc4f89756052b544056f2",
    "58a3695ce7f050f6d679159be3fce4702e1e7da3685b31580f9efad19c3d8f00",
  ]);
  const consumerPins = new Set([
    "13c22188acd529db0d9e815e07b79e2445be11e4570facc551957f9401d63b38",
    "d6ad3da30781819e322b4d7a1452cea7e6a8a5c9d8ca26ac3299b69a889c35c1",
    "21b8e64ed9d781eaecc85dee4cc09029639bf64c0b7dbfa29e4e91e7b856b092",
  ]);
  const hooks = [],
    consumers = [];
  for (const variant of corpus.index.modules.filter((m) =>
    m.ids.includes(225641),
  ))
    for (const origin of variant.origins) {
      const mod = await corpus.factory(225641, { source: origin.source });
      require(hookPins.has(
        sha256(compact(mod.node)),
      ), "review changed outbound hook variant semantics");
      const hook = exported(mod, 225641, "f"),
        imports = imported(mod);
      const usePreference = one(
        hook,
        (n) =>
          call(n, "l") &&
          n.arguments[0]?.value === "privacy.confirmExternalLinks",
        "actual setting hook",
      );
      require(imports.get(target(usePreference.callee).object.name) ===
        547562, "hook binds actual setting framework");
      const useGate = one(
        hook,
        (n) =>
          n.type === "CallExpression" &&
          call(n, "f") &&
          imports.get(target(n.callee).object?.name) === 402732,
        "actual settings-hub gate",
      );
      const normalize = topFunction(mod, exported(mod, 947187, "_").name),
        trusted = topFunction(mod, exported(mod, 947187, "l").name);
      const hosts = one(
        mod.node,
        (n) => n.type === "NewExpression" && n.callee.name === "Set",
        "trusted host set",
      ).arguments[0].elements.map(literal);
      require(JSON.stringify(hosts) ===
        JSON.stringify([
          "pump.fun",
          "terminal.pump.fun",
          "trade.padre.gg",
        ]), "all captured hook variants have exact trusted hosts");
      const openCall = one(
        mod.node,
        (n) => call(n, "open") && target(n.callee).object?.name === "window",
        "actual Window.open port",
      );
      require(openCall.arguments.slice(1).map(literal).join("|") ===
        "_blank|noopener,noreferrer", "actual outbound window arguments");
      hooks.push({
        source: mod.provenance,
        hosts,
        evidence: [
          mod.witness(hook, "complete outbound confirmation hook"),
          mod.witness(usePreference, "used privacy setting"),
          mod.witness(useGate, "used settings gate"),
          mod.witness(normalize, "URL normalization"),
          mod.witness(trusted, "trusted host predicate"),
          mod.witness(openCall, "actual open call"),
        ],
      });
      modules.push(mod);
    }
  require(hooks.length === 4, "review all four captured hook variants");
  for (const variant of corpus.index.modules.filter((m) =>
    m.ids.includes(634557),
  ))
    for (const origin of variant.origins) {
      const mod = await corpus.factory(634557, { source: origin.source });
      require(consumerPins.has(
        sha256(compact(mod.node)),
      ), "review changed actual link consumer semantics");
      const imports = imported(mod),
        component = exported(mod, 634557, "f");
      const useHook = one(
        component,
        (n) =>
          call(n, "f") && imports.get(target(n.callee).object?.name) === 225641,
        "actual link hook call",
      );
      const normalize = one(
        component,
        (n) =>
          call(n, "_") && imports.get(target(n.callee).object?.name) === 947187,
        "actual disabled-link normalization",
      );
      const prevent = one(
        component,
        (n) => call(n, "preventDefault"),
        "link click suppression",
      );
      consumers.push({
        source: mod.provenance,
        evidence: [
          mod.witness(component, "complete used link consumer"),
          mod.witness(useHook, "used confirmation hook"),
          mod.witness(normalize, "render eligibility"),
          mod.witness(prevent, "click prevent/stop/callback/request sequence"),
        ],
      });
      modules.push(mod);
    }
  require(consumers.length ===
    3, "review all three captured consumer variants");
  const sources = modules.map((mod) => ({
    source: mod.provenance,
    imports: [
      ...new Set(
        findNodes(
          mod.node,
          (n) =>
            n.type === "CallExpression" &&
            ["i", "r", "A"].some((p) => call(n, p)) &&
            target(n.callee).object?.name === mod.runtime &&
            n.arguments[0]?.type === "NumericLiteral",
        ).map((n) => literal(n.arguments[0])),
      ),
    ].map((id) => ({
      id,
      variants: corpus.index.modules
        .filter((m) => m.ids.includes(id))
        .map((m) => ({ ids: m.ids, sha256: m.sha256, origins: m.origins })),
    })),
  }));
  require(sources.every((m) =>
    m.imports.every((i) => i.variants.length > 0),
  ), "unresolved available direct import");
  return {
    schemaVersion: 1,
    classification:
      "Original selected device privacy preference and outbound client workflow; no native server or visual compatibility",
    compatibilityQualified: false,
    inputs: corpus.anchors,
    inventoryVariants: corpus.index.modules.length,
    captureTime: corpus.manifest.captured_at,
    preference: {
      id: literal(objectProperty(definition, "id")),
      scope: "device",
      default: true,
      coerce: "strict false alone disables; every other decoded value enables",
      key,
      codec,
      legacyAdoption: false,
      evidence: definitions.witness(definition, "selected privacy descriptor"),
    },
    storage: {
      localEvent: literal(eventName),
      read: "runtime fallback first; otherwise getItem catch->null; absent/malformed JSON->undefined before coerce; cache parsed value by exact raw string",
      write:
        "coerce first; JSON stringify before setItem try; successful write clears fallback, failed write stores runtime fallback; dispatch local event regardless",
      remove:
        "swallow remove error, clear decoded/fallback caches, dispatch local event",
      persistence:
        "working browser storage persists across reload; runtime fallback is not durable",
      subscriptions:
        "lazy storage/local-storage listeners; null/undefined event key notifies selected key, exact key notifies it, other key ignored; callback unsubscribe does not detach module-lifetime listeners",
      externalEvent: "notify only; does not clear write-failure fallback",
      evidence: storage.provenance,
    },
    outbound: {
      normalize:
        "trim; protocol-relative gains https:, non-http(s)-prefix gains https://; URL must resolve to https:; malformed/empty returns null",
      trustedHosts: hooks[0].hosts,
      trustedComparison:
        "normalize and remove one www. prefix, then exact hostname set",
      forcedConfirmation: "!WEB_SETTINGS_HUB || confirmationPreference",
      request:
        "invalid leaves state; trusted or no confirmation opens directly without clearing any existing dialog; otherwise reset checkbox, retain normalized URL, open dialog",
      confirm:
        "when pending URL exists, feature-enabled AND checked writes false before open; then close and clear URL; popup return ignored",
      cancel:
        "close and clear URL; checkbox is reset by the next prompted request",
      openArguments: ["_blank", "noopener,noreferrer"],
      persistenceAcknowledgementOrNavigationSuccessClaimed: false,
      hooks,
    },
    consumer: {
      clickOrder: [
        "preventDefault",
        "stopPropagation",
        "optional onClick(event)",
        "requestNavigation(href)",
      ],
      invalidRenderedAs: "disabled-looking span; no anchor",
      eligibleAnchor: { target: "_blank", rel: "noopener noreferrer" },
      variants: consumers,
    },
    sources,
    limits: [
      "Selected device preference only; no account ownership/session partition, remote preference endpoint or backend inference.",
      "All four hook and three consumer variants remain explicit; no active page winner is inferred.",
      "UI rendering, React scheduling/hydration, popup policies and arbitrary reentrant application-port changes are outside the controller's settled-state model.",
      "Explicit storage/events/window-open ports; no production navigation, browser permission request, analytics service or implicit network.",
      "The source trusted-host list is preserved as client behavior, not a security clearance or scope expansion into excluded destinations.",
      "The device Settings row is local UI integration; modal dismissal and shared shell remain distinct. No visual parity, native compatibility or feature-ledger credit.",
      "Direct imports retain all available inventory variants; complete transitive closure remains unresolved.",
    ],
  };
}
export async function verify(root = defaultRoot) {
  const value = await recover(root),
    saved = JSON.parse(await readFile(path.join(root, outputPath), "utf8"));
  require(JSON.stringify(value) ===
    JSON.stringify(
      saved,
    ), "generated contract differs from authenticated source");
  return value;
}
// Receipt integrity is separate from actually rerunning the browser workflow.
export async function verifyBrowserReceipt(root = defaultRoot) {
  const receipt = JSON.parse(
    await readFile(
      path.join(
        root,
        "reconstruction/privacy-external-links/browser-verification.json",
      ),
      "utf8",
    ),
  );
  for (const [field, relative] of [
    ["clientSha256", "reconstruction/privacy-external-links/client.mjs"],
    [
      "browserScriptSha256",
      "tests/original_privacy_external_links.browser.mjs",
    ],
    ["contractSha256", outputPath],
  ])
    require(receipt[field] ===
      sha256(
        await readFile(path.join(root, relative)),
      ), `stale browser receipt ${field}`);
  require(receipt.result === "PASS" &&
    receipt.browserProcessRestarts === 1 &&
    receipt.actualDestinationOpened === false &&
    receipt.capturedCodeExecuted === false, "browser receipt scope/result");
  require(Array.isArray(receipt.pageErrors) &&
    receipt.pageErrors.length === 0 &&
    Array.isArray(receipt.externalRequests) &&
    receipt.externalRequests.length ===
      0, "browser receipt reports errors/external requests");
  require(JSON.stringify(receipt.viewports) ===
    JSON.stringify([
      [1280, 900],
      [390, 844],
    ]) &&
    Array.isArray(receipt.checks) &&
    receipt.checks.length === 4, "browser receipt affected cases");
  return receipt;
}
export async function verifyAppBrowserReceipt(root = defaultRoot) {
  const directory = path.join(root, appBrowserDirectory);
  const receipt = JSON.parse(
    await readFile(path.join(directory, "verification.json"), "utf8"),
  );
  require(JSON.stringify(Object.keys(receipt.sourceInputs)) ===
    JSON.stringify(appBrowserInputs), "app receipt input set");
  // Retain the previous shared-host limit: its executed bytes are recorded,
  // but unrelated later modal edits are not qualified by this footer receipt.
  const sharedHost =
    "packages/frontend/src/components/settings/settings-control.tsx";
  for (const relative of appBrowserInputs) {
    const bytes = await readFile(path.join(root, relative));
    if (relative === sharedHost) {
      const text = bytes.toString("utf8");
      require(/^[0-9a-f]{64}$/.test(receipt.sourceInputs[relative]) &&
        text.includes(
          'import { PrivacySettingControl } from "./privacy-setting-control";',
        ) &&
        text.includes('setting.id === "privacy.confirmExternalLinks" ? (') &&
        text.includes(
          "<PrivacySettingControl label={setting.label} />",
        ), `stale app receipt ${relative} no longer mounts the privacy row control`);
      continue;
    }
    require(receipt.sourceInputs[relative] ===
      sha256(bytes), `stale app receipt ${relative}`);
  }
  const screenshots = [
    "footer-desktop.png",
    "footer-mobile.png",
    "footer-storage-failure.png",
  ];
  require(JSON.stringify(Object.keys(receipt.screenshots)) ===
    JSON.stringify(screenshots), "app receipt screenshot set");
  for (const name of screenshots)
    require(receipt.screenshots[name] ===
      sha256(
        await readFile(path.join(directory, name)),
      ), `stale app screenshot ${name}`);
  require(receipt.result === "PASS" &&
    receipt.passed === appBrowserCaseTitles.length &&
    receipt.failed === 0 &&
    receipt.skipped === 0 &&
    JSON.stringify(receipt.checks) === JSON.stringify(appBrowserCaseTitles) &&
    receipt.browserProcessRestarts === 0 &&
    receipt.reloadsExercised === true &&
    receipt.pageErrors?.length === 0 &&
    receipt.consoleErrors?.length === 0 &&
    receipt.nativeFallbacks?.length === 1 &&
    receipt.nativeFallbacks.some((item) => item.kind === "opening-exception") &&
    receipt.openRefusals === 2 &&
    receipt.storageRefusals >= 1 &&
    receipt.routedExternal?.every(
      (item) => item.action === "fulfilled" && item.method === "GET",
    ) &&
    receipt.capturedCodeExecuted === false &&
    receipt.outboundConsumersExercised === true &&
    receipt.upstreamRequestsPerformed === false &&
    receipt.upstreamFlagRolloutClaimed === false &&
    receipt.serverCompatibilityClaimed === false, "app receipt result/scope");
  return receipt;
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const args = process.argv.slice(2),
    at = args.indexOf("--root");
  require(args.every(
    (a, i) =>
      [
        "--write",
        "--check",
        "--check-browser",
        "--check-app-browser",
        "--root",
      ].includes(a) || i === at + 1,
  ), "unknown argument");
  const root = at < 0 ? defaultRoot : path.resolve(args[at + 1]);
  if (args.includes("--write")) {
    await mkdir(path.dirname(path.join(root, outputPath)), { recursive: true });
    await writeFile(
      path.join(root, outputPath),
      JSON.stringify(await recover(root), null, 2) + "\n",
    );
  }
  const value = await verify(root);
  if (args.includes("--check-browser")) await verifyBrowserReceipt(root);
  if (args.includes("--check-app-browser")) await verifyAppBrowserReceipt(root);
  console.log(
    JSON.stringify({
      result: "PASS",
      sources: value.sources.length,
      hooks: value.outbound.hooks.length,
      consumers: value.consumer.variants.length,
      browserReceiptChecked: args.includes("--check-browser"),
      appBrowserReceiptChecked: args.includes("--check-app-browser"),
      capturedCodeExecuted: false,
      productionRequests: 0,
    }),
  );
}
