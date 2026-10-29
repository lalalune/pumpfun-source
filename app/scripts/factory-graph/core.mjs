import { createHash } from "node:crypto";
import {
  lstat,
  mkdir,
  readFile,
  readdir,
  realpath,
  rename,
  rm,
  writeFile,
} from "node:fs/promises";
import { dirname, join, relative, resolve, sep } from "node:path";
import { gzipSync, gunzipSync } from "node:zlib";
import { parse } from "@babel/parser";
import prettier from "prettier";

export const GRAPH_VERSION = 1;
export const DEFAULT_ROUTES = [
  "/",
  "/explore",
  "/leaderboard",
  "/live",
  "/go",
  "/mayhem",
  "/create",
  "/holder-rewards",
  "/profile/:id",
  "/portfolio",
];

const sha256 = (value) => createHash("sha256").update(value).digest("hex");
const stable = (value) => `${JSON.stringify(value, null, 2)}\n`;
const lexical = (a, b) => String(a).localeCompare(String(b), "en");
const byKey = (a, b) => lexical(a.key, b.key);
const FACTORY_BANNER =
  "// Recovered Turbopack factory. Requires original runtime/import IDs; not a standalone source module.\n";

export function countSourceLines(source) {
  let ast;
  try {
    ast = parse(source, {
      sourceType: "script",
      plugins: ["jsx", "typescript"],
      tokens: true,
    });
  } catch (error) {
    throw new Error(`cannot count malformed source: ${error.message}`);
  }
  return countTokenLines(ast.tokens);
}

function countTokenLines(tokens) {
  const lines = new Set();
  for (const token of tokens || []) {
    const kind =
      typeof token.type === "string" ? token.type : token.type?.label;
    if (!kind || kind === "eof" || kind.startsWith("Comment")) continue;
    for (let line = token.loc.start.line; line <= token.loc.end.line; line += 1)
      lines.add(line);
  }
  return lines.size;
}

async function safeFile(root, relativePath) {
  if (
    typeof relativePath !== "string" ||
    !relativePath ||
    relativePath.includes("\0")
  ) {
    throw new Error(`unsafe path: ${String(relativePath)}`);
  }
  const absolute = resolve(root, relativePath);
  if (absolute !== root && !absolute.startsWith(`${root}${sep}`))
    throw new Error(`path escapes root: ${relativePath}`);
  let cursor = absolute;
  while (cursor !== root) {
    const stat = await lstat(cursor);
    if (stat.isSymbolicLink())
      throw new Error(`symlink rejected: ${relativePath}`);
    cursor = dirname(cursor);
  }
  const canonicalRoot = await realpath(root);
  const canonical = await realpath(absolute);
  if (
    canonical !== canonicalRoot &&
    !canonical.startsWith(`${canonicalRoot}${sep}`)
  ) {
    throw new Error(`real path escapes root: ${relativePath}`);
  }
  return absolute;
}

function walk(node, visit) {
  if (!node || typeof node !== "object") return;
  visit(node);
  for (const [key, value] of Object.entries(node)) {
    if (
      key === "loc" ||
      key === "extra" ||
      key === "comments" ||
      key === "tokens"
    )
      continue;
    if (Array.isArray(value)) for (const child of value) walk(child, visit);
    else if (
      value &&
      typeof value === "object" &&
      typeof value.type === "string"
    )
      walk(value, visit);
  }
}

function literalValue(node) {
  if (!node) return undefined;
  if (node.type === "NumericLiteral" || node.type === "StringLiteral")
    return node.value;
  return undefined;
}

// The captured runtime's `s` decoder consumes getter pairs, optional setter
// functions, and numeric-tag-0 constant triples. Never evaluate descriptor
// expressions: dynamic forms cannot establish a static export inventory.
function exportNames(argument) {
  if (argument?.type !== "ArrayExpression") return [];
  const values = argument.elements;
  const names = [];
  const isFunction = (node) =>
    ["ArrowFunctionExpression", "FunctionExpression"].includes(node?.type);
  for (let index = 0; index < values.length; ) {
    const name = values[index++];
    if (name?.type !== "StringLiteral") return [];
    const descriptor = values[index++];
    if (!descriptor) return [];
    if (descriptor.type === "NumericLiteral" && descriptor.value === 0) {
      const value = values[index++];
      if (!value || value.type === "SpreadElement") return [];
    } else {
      if (!isFunction(descriptor)) return [];
      if (isFunction(values[index])) index += 1;
    }
    names.push(name.value);
  }
  return names;
}

const AST_METADATA_KEYS = new Set([
  "comments",
  "end",
  "errors",
  "extra",
  "innerComments",
  "leadingComments",
  "loc",
  "start",
  "tokens",
  "trailingComments",
]);

function canonicalAstDigest(value) {
  const digest = createHash("sha256");
  const update = (node) => {
    if (Array.isArray(node)) {
      digest.update("[");
      for (const child of node) {
        if (child?.type === "EmptyStatement") continue;
        update(child);
        digest.update(",");
      }
      digest.update("]");
      return;
    }
    if (!node || typeof node !== "object") {
      digest.update(`${typeof node}:${JSON.stringify(node)};`);
      return;
    }
    digest.update("{");
    for (const key of Object.keys(node).sort(lexical)) {
      if (AST_METADATA_KEYS.has(key) || node[key] === undefined) continue;
      digest.update(`${JSON.stringify(key)}:`);
      update(node[key]);
    }
    digest.update("}");
  };
  update(value);
  return digest.digest("hex");
}

export function analyzeFactory(source, label = "factory") {
  let ast;
  try {
    ast = parse(source, {
      sourceType: "script",
      errorRecovery: false,
      plugins: ["jsx", "typescript"],
      tokens: true,
    });
  } catch (error) {
    try {
      ast = parse(`(${source})`, {
        sourceType: "script",
        errorRecovery: false,
        plugins: ["jsx", "typescript"],
        tokens: true,
      });
    } catch {
      throw new Error(`malformed factory ${label}: ${error.message}`);
    }
  }
  const expression = ast.program.body.find(
    (entry) => entry.type === "ExpressionStatement",
  )?.expression;
  if (
    !expression ||
    !["ArrowFunctionExpression", "FunctionExpression"].includes(expression.type)
  ) {
    throw new Error(
      `factory ${label} does not contain a top-level function expression`,
    );
  }
  const runtime = expression.params[0];
  if (!runtime || runtime.type !== "Identifier")
    throw new Error(`factory ${label} has no runtime parameter`);
  const imports = [];
  const exports = new Set();
  walk(expression.body, (node) => {
    if (
      node.type !== "CallExpression" ||
      node.callee?.type !== "MemberExpression" ||
      node.callee.computed
    )
      return;
    if (
      node.callee.object?.type !== "Identifier" ||
      node.callee.object.name !== runtime.name
    )
      return;
    const method = node.callee.property?.name;
    if (method === "i" || method === "A") {
      const target = literalValue(node.arguments[0]);
      imports.push({
        kind: method === "A" ? "dynamic" : "direct",
        runtimeMethod: method,
        target: target === undefined ? null : target,
        static: target !== undefined,
        line: node.loc?.start.line ?? null,
        column: node.loc?.start.column ?? null,
      });
    } else if (method === "s") {
      for (const name of exportNames(node.arguments[0])) exports.add(name);
    }
  });
  imports.sort(
    (a, b) => a.line - b.line || a.column - b.column || lexical(a.kind, b.kind),
  );
  return {
    imports,
    exports: [...exports].sort(lexical),
    lineCount: countTokenLines(ast.tokens),
    canonicalAstSha256: canonicalAstDigest(expression),
  };
}

function identityKey(id, hash, origin) {
  return `${id}@${hash}:${origin.source}:${origin.start}-${origin.end}`;
}

function capturePathFromUrl(url, recordsByUrl) {
  return recordsByUrl.get(url)?.path ?? null;
}

function capturedAssets(html, baseUrl, recordsByUrl) {
  const found = new Set();
  const patterns = [
    /<script\b[^>]*\bsrc=["']([^"']+\.js(?:\?[^"']*)?)["']/gi,
    /["'](\/_next\/static\/[^"']+\.js(?:\?[^"']*)?)["']/g,
  ];
  for (const pattern of patterns) {
    for (const match of html.matchAll(pattern)) {
      try {
        const url = new URL(match[1], baseUrl).href;
        const path = capturePathFromUrl(url, recordsByUrl);
        if (path) found.add(path);
      } catch {
        /* invalid captured URL is not an association */
      }
    }
  }
  return [...found].sort(lexical);
}

function routePath(url) {
  try {
    return new URL(url).pathname.replace(/\/$/, "") || "/";
  } catch {
    return null;
  }
}

function operationParts(operation) {
  const match = /^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(.+)$/.exec(
    operation,
  );
  return match
    ? { method: match[1], path: match[2] }
    : { method: null, path: operation };
}

async function readJson(root, path) {
  return JSON.parse(await readFile(await safeFile(root, path), "utf8"));
}

async function authenticateRecord(root, record) {
  const path = await safeFile(root, record.path);
  const bytes = await readFile(path);
  if (bytes.length !== record.bytes)
    throw new Error(`byte length mismatch: ${record.path}`);
  if (sha256(bytes) !== record.sha256)
    throw new Error(`capture hash mismatch: ${record.path}`);
  let text;
  try {
    text = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes);
  } catch {
    throw new Error(`invalid UTF-8: ${record.path}`);
  }
  return { bytes, text };
}

export async function buildGraph(root, options = {}) {
  const targetLines = options.targetLines ?? 250_000;
  const maximumLines = options.maximumLines ?? 300_000;
  const routes = options.routes ?? DEFAULT_ROUTES;
  const modulesIndex = await readJson(root, "recovered/modules.json");
  const capture = await readJson(root, "evidence/web/manifest.json");
  const internal = await readJson(root, "contracts/internal-operations.json");
  const developer = await readJson(root, "contracts/developer-bindings.json");
  if (
    modulesIndex.rangeEncoding !==
    "UTF-16 code-unit half-open offsets in UTF-8 decoded source"
  ) {
    throw new Error("unsupported source range encoding");
  }

  const recordsByPath = new Map(
    capture.records.map((record) => [record.path, record]),
  );
  const recordsByUrl = new Map();
  for (const record of capture.records) {
    recordsByUrl.set(record.url, record);
    if (record.final_url) recordsByUrl.set(record.final_url, record);
  }
  const sourceCache = new Map();
  const getCapture = async (path) => {
    if (!recordsByPath.has(path))
      throw new Error(`unmanifested capture: ${path}`);
    if (!sourceCache.has(path))
      sourceCache.set(
        path,
        await authenticateRecord(root, recordsByPath.get(path)),
      );
    return sourceCache.get(path);
  };

  const variants = [];
  const authenticatedAnalysisByHash = new Map();
  const formattedDerivationByHash = new Map();
  for (const module of modulesIndex.modules) {
    const formattedPath = await safeFile(root, module.path);
    const formatted = await readFile(formattedPath, "utf8");
    let authenticatedSource;
    for (const origin of module.origins) {
      const captured = await getCapture(origin.source);
      if (
        !Number.isSafeInteger(origin.start) ||
        !Number.isSafeInteger(origin.end) ||
        origin.start < 0 ||
        origin.end <= origin.start ||
        origin.end > captured.text.length
      ) {
        throw new Error(
          `invalid UTF-16 range: ${module.path} at ${origin.source}`,
        );
      }
      const original = captured.text.slice(origin.start, origin.end);
      if (sha256(original) !== module.sha256) {
        throw new Error(
          `source range mismatch: ${module.path} at ${origin.source}`,
        );
      }
      authenticatedSource ??= original;
    }
    const analysis = analyzeFactory(formatted, module.path);
    if (!authenticatedAnalysisByHash.has(module.sha256))
      authenticatedAnalysisByHash.set(
        module.sha256,
        analyzeFactory(
          authenticatedSource,
          `${module.path} authenticated origin`,
        ),
      );
    const originalAnalysis = authenticatedAnalysisByHash.get(module.sha256);
    let authenticityMethod = "CANONICAL_AST";
    if (analysis.canonicalAstSha256 !== originalAnalysis.canonicalAstSha256) {
      if (!formattedDerivationByHash.has(module.sha256))
        formattedDerivationByHash.set(
          module.sha256,
          FACTORY_BANNER +
            (await prettier.format(`(${authenticatedSource});`, {
              parser: "babel",
            })),
        );
      if (formatted !== formattedDerivationByHash.get(module.sha256))
        throw new Error(
          `recovered factory authenticity mismatch: ${module.path} matches neither the complete canonical AST nor the exact inventory formatter derivation of its authenticated origins`,
        );
      authenticityMethod = "EXACT_FORMATTER_DERIVATION";
    }
    const lineCount = analysis.lineCount;
    variants.push({
      ...module,
      analysis,
      lineCount,
      authenticityMethod,
    });
  }

  const routeAssets = {};
  for (const route of routes) {
    if (route.includes(":")) {
      routeAssets[route] = {
        status: "NO_EXACT_CAPTURE",
        html: null,
        assets: [],
      };
      continue;
    }
    const candidates = capture.records.filter(
      (record) =>
        record.status === 200 &&
        routePath(record.final_url || record.url) === route &&
        /text\/html/i.test(record.headers?.["content-type"] || ""),
    );
    candidates.sort((a, b) => lexical(a.path, b.path));
    if (!candidates.length) {
      routeAssets[route] = {
        status: "NO_EXACT_CAPTURE",
        html: null,
        assets: [],
      };
      continue;
    }
    const record = candidates[0];
    const authenticated = await getCapture(record.path);
    routeAssets[route] = {
      status: "AUTHENTICATED",
      html: {
        path: record.path,
        url: record.final_url || record.url,
        sha256: record.sha256,
        bytes: record.bytes,
      },
      assets: capturedAssets(
        authenticated.text,
        record.final_url || record.url,
        recordsByUrl,
      ),
    };
  }

  const directlyAttributed = new Map();
  const originsBySource = new Map();
  for (const variant of variants) {
    for (const origin of variant.origins) {
      if (!originsBySource.has(origin.source))
        originsBySource.set(origin.source, []);
      originsBySource.get(origin.source).push({ variant, origin });
    }
  }
  for (const [route, evidence] of Object.entries(routeAssets)) {
    for (const asset of evidence.assets) {
      for (const { variant, origin } of originsBySource.get(asset) || []) {
        for (const id of variant.ids) {
          const key = identityKey(id, variant.sha256, origin);
          if (!directlyAttributed.has(key))
            directlyAttributed.set(key, new Set());
          directlyAttributed.get(key).add(route);
        }
      }
    }
  }
  const operationSources = new Set();
  for (const operation of internal.operations || [])
    if (operation.source) operationSources.add(operation.source);
  for (const binding of developer.bindings || []) {
    for (const site of binding.evidence?.clientCallSites || [])
      if (site.source) operationSources.add(site.source);
  }

  const ordered = [...variants].sort((a, b) => {
    const hasRouteSeed = (variant) =>
      variant.origins.some((origin) =>
        variant.ids.some((id) =>
          directlyAttributed.has(identityKey(id, variant.sha256, origin)),
        ),
      );
    const aRoute = hasRouteSeed(a) ? 0 : 1;
    const bRoute = hasRouteSeed(b) ? 0 : 1;
    if (aRoute !== bRoute) return aRoute - bRoute;
    const aApi = a.origins.some((origin) => operationSources.has(origin.source))
      ? 0
      : 1;
    const bApi = b.origins.some((origin) => operationSources.has(origin.source))
      ? 0
      : 1;
    return aApi - bApi || lexical(a.sha256, b.sha256);
  });
  const selected = [];
  let totalLines = 0;
  for (const variant of ordered) {
    if (totalLines >= targetLines) break;
    if (totalLines + variant.lineCount > maximumLines) continue;
    selected.push(variant);
    totalLines += variant.lineCount;
  }
  if (totalLines < targetLines || totalLines > maximumLines)
    throw new Error(
      `honest source selection outside requested range: ${totalLines}`,
    );

  const identities = [];
  for (const variant of selected) {
    for (const origin of variant.origins) {
      for (const id of variant.ids) {
        identities.push({
          key: identityKey(id, variant.sha256, origin),
          id,
          sha256: variant.sha256,
          path: variant.path,
          lineCount: variant.lineCount,
          origin,
          exports: variant.analysis.exports,
          routeSeeds: [
            ...(directlyAttributed.get(
              identityKey(id, variant.sha256, origin),
            ) || []),
          ].sort(lexical),
        });
      }
    }
  }
  identities.sort(byKey);
  const identityByKey = new Map(identities.map((entry) => [entry.key, entry]));
  const byId = new Map();
  for (const identity of identities) {
    if (!byId.has(String(identity.id))) byId.set(String(identity.id), []);
    byId.get(String(identity.id)).push(identity);
  }

  const variantByHash = new Map(selected.map((entry) => [entry.sha256, entry]));
  const edges = [];
  for (const source of identities) {
    const variant = variantByHash.get(source.sha256);
    for (const imported of variant.analysis.imports) {
      const edge = {
        key: `${source.key}:${imported.line}:${imported.column}:${imported.kind}`,
        source: source.key,
        kind: imported.kind,
        runtimeMethod: imported.runtimeMethod,
        requestedId: imported.target,
        line: imported.line,
        column: imported.column,
        resolution: "UNRESOLVED",
        target: null,
        candidates: [],
        crossChunk: null,
      };
      if (!imported.static) edge.reason = "dynamic target is not a literal";
      else if (typeof imported.target === "string") {
        edge.resolution = "EXTERNAL";
        edge.reason = "string runtime boundary";
      } else {
        const candidates = byId.get(String(imported.target)) || [];
        const sameObject = candidates.filter(
          (candidate) => candidate.origin.source === source.origin.source,
        );
        if (sameObject.length === 1) {
          edge.resolution = "EXACT";
          edge.target = sameObject[0].key;
          edge.crossChunk = false;
        } else if (candidates.length === 1) {
          edge.resolution = "EXACT";
          edge.target = candidates[0].key;
          edge.crossChunk =
            candidates[0].origin.source !== source.origin.source;
        } else if (candidates.length > 1) {
          edge.resolution = "AMBIGUOUS";
          edge.candidates = candidates
            .map((candidate) => candidate.key)
            .sort(lexical);
          edge.reason =
            sameObject.length > 1
              ? "conflicting variants in captured chunk context"
              : "multiple captured variants remain";
        } else edge.reason = "target absent from selected authenticated corpus";
      }
      edges.push(edge);
    }
  }
  edges.sort(byKey);

  const routeReport = {};
  const edgesBySource = new Map();
  for (const edge of edges) {
    if (!edgesBySource.has(edge.source)) edgesBySource.set(edge.source, []);
    edgesBySource.get(edge.source).push(edge);
  }
  for (const route of routes) {
    const seeds = identities
      .filter((identity) => identity.routeSeeds.includes(route))
      .map((entry) => entry.key);
    const reachable = new Set(seeds);
    const queue = [...seeds];
    while (queue.length) {
      const source = queue.shift();
      for (const edge of edgesBySource.get(source) || []) {
        if (edge.resolution === "EXACT" && !reachable.has(edge.target)) {
          reachable.add(edge.target);
          queue.push(edge.target);
        }
      }
    }
    routeReport[route] = {
      ...routeAssets[route],
      seedNodes: seeds.sort(lexical),
      reachableNodes: [...reachable].sort(lexical),
    };
  }

  const findIdentitiesForOccurrence = (occurrence) =>
    identities
      .filter(
        (identity) =>
          identity.origin.source === occurrence.source &&
          occurrence.start >= identity.origin.start &&
          occurrence.end <= identity.origin.end,
      )
      .map((identity) => identity.key)
      .sort(lexical);
  const internalAttribution = [];
  for (const operation of internal.operations || []) {
    const sites = [];
    const nodes = findIdentitiesForOccurrence(operation);
    if (nodes.length)
      sites.push({
        source: operation.source,
        start: operation.start,
        end: operation.end,
        nodes,
      });
    if (sites.length)
      internalAttribution.push({
        operation: operation.operation,
        ...operationParts(operation.operation),
        classification: "DECLARED_STATIC_LITERAL",
        sites,
      });
  }
  const developerAttribution = [];
  for (const binding of developer.bindings || []) {
    const sites = [];
    for (const site of binding.evidence?.clientCallSites || []) {
      const nodes = findIdentitiesForOccurrence(site);
      if (nodes.length) sites.push({ ...site, nodes });
    }
    if (sites.length)
      developerAttribution.push({
        operationId: binding.operationId,
        classification: "DECLARED_DEVELOPER_BINDING",
        sites,
      });
  }

  const selectedObjects = [
    ...new Set(
      selected.flatMap((variant) =>
        variant.origins.map((origin) => origin.source),
      ),
    ),
  ].sort(lexical);
  const sourceManifest = selectedObjects.map((path) => {
    const record = recordsByPath.get(path);
    return {
      path,
      url: record.url,
      finalUrl: record.final_url,
      status: record.status,
      bytes: record.bytes,
      sha256: record.sha256,
    };
  });
  const lineCensus = {
    methodology:
      "Unique factory content hashes; lines are counted from Babel AST token locations. Generated recovery banners, blank lines, comment-only lines, and duplicate content hashes are excluded.",
    targetLines,
    maximumLines,
    analyzedLines: totalLines,
    uniqueFactories: selected.length,
    factories: selected
      .map((variant) => ({
        sha256: variant.sha256,
        path: variant.path,
        lineCount: variant.lineCount,
        ids: variant.ids,
      }))
      .sort((a, b) => lexical(a.sha256, b.sha256)),
  };
  const counts = edges.reduce(
    (result, edge) => {
      result[edge.resolution] += 1;
      return result;
    },
    { EXACT: 0, AMBIGUOUS: 0, UNRESOLVED: 0, EXTERNAL: 0 },
  );
  const summary = {
    schemaVersion: GRAPH_VERSION,
    analyzedLines: totalLines,
    uniqueFactories: selected.length,
    identities: identities.length,
    capturedObjects: sourceManifest.length,
    edges: edges.length,
    directEdges: edges.filter((edge) => edge.kind === "direct").length,
    dynamicEdges: edges.filter((edge) => edge.kind === "dynamic").length,
    crossChunkExactEdges: edges.filter(
      (edge) => edge.resolution === "EXACT" && edge.crossChunk,
    ).length,
    resolutions: counts,
    authenticatedRoutes: Object.values(routeAssets).filter(
      (entry) => entry.status === "AUTHENTICATED",
    ).length,
    routeAttributedNodes: new Set(
      Object.values(routeReport).flatMap((entry) => entry.reachableNodes),
    ).size,
    internalOperationsAttributed: internalAttribution.length,
    developerOperationsAttributed: developerAttribution.length,
  };
  const ambiguities = edges
    .filter((edge) => edge.resolution === "AMBIGUOUS")
    .map(({ key, source, requestedId, candidates, reason }) => ({
      key,
      source,
      requestedId,
      candidates,
      reason,
    }));
  const readme = `# Authenticated Turbopack route graph\n\nThis packet is a deterministic static analysis of retained Pump.fun frontend evidence. It does not execute captured JavaScript and does not claim recovery of original TypeScript or runtime/API compatibility.\n\n## Measured scope\n\n- Analyzed code lines: ${summary.analyzedLines}\n- Unique factory content hashes: ${summary.uniqueFactories}\n- Provenance-qualified identities: ${summary.identities}\n- Authenticated captured JavaScript objects: ${summary.capturedObjects}\n- Import boundaries: ${summary.edges}\n- Exact / ambiguous / unresolved: ${summary.resolutions.EXACT} / ${summary.resolutions.AMBIGUOUS} / ${summary.resolutions.UNRESOLVED}\n- Exact cross-chunk edges: ${summary.crossChunkExactEdges}\n- Authenticated route captures: ${summary.authenticatedRoutes}\n- Internal / developer operations attributed: ${summary.internalOperationsAttributed} / ${summary.developerOperationsAttributed}\n\n## Reproduction\n\nFrom \`app/\` run:\n\n\`\`\`sh\npnpm install --frozen-lockfile\npnpm graph:build\npnpm graph:verify\npnpm test:graph\n\`\`\`\n\nThe builder authenticates manifest hashes and byte lengths, decodes UTF-8 strictly, and checks every recovered factory's UTF-16 half-open source range. Each recovered formatted factory must have a complete canonical AST equal to its authenticated raw factory. The canonical form excludes parser locations, comments, tokens, raw literal spelling, and empty no-op statements while preserving executable structure. For the small set where the pinned formatter itself changes Babel AST shape, exact byte-for-byte re-derivation through that formatter is required instead. Route seeds are keyed by module ID, factory hash, captured object, and source range, so identical bytes in an unreferenced object do not inherit another object's route. Captured factories are parsed without evaluation, and publication uses a temporary directory. \`MANIFEST.json\` binds every generated record; verification rebuilds the packet from current authenticated inputs.\n\n## Interpretation boundaries\n\n\`EXACT\` means the selected captured chunk context has one supported target, or the selected corpus contains one target identity. \`AMBIGUOUS\` preserves multiple compatible variants. \`UNRESOLVED\` means no target is present in the selected authenticated corpus; it is not evidence that the original application failed to resolve it. Route attribution requires captured HTML to reference an authenticated asset that contains the exact provenance-qualified factory identity. API attribution links existing ledgers to enclosing factory ranges and remains static evidence, not a live-service qualification. Exact captures were unavailable for \`/profile/:id\` and \`/portfolio\`; those entries are deliberately empty.\n`;
  return {
    "README.md": readme,
    "SOURCE-MANIFEST.json": sourceManifest,
    "LINE-CENSUS.json": lineCensus,
    "GRAPH-SUMMARY.json": summary,
    "MODULE-IDENTITIES.json.gz": identities,
    "IMPORT-EDGES.json.gz": edges,
    "ROUTE-ATTRIBUTION.json": routeReport,
    "API-ATTRIBUTION.json": {
      internal: internalAttribution,
      developer: developerAttribution,
    },
    "AMBIGUITIES.json": ambiguities,
    "VERIFY-RESULTS.json": {
      schemaVersion: GRAPH_VERSION,
      captureObjectsVerified: sourceCache.size,
      selectedCaptureObjects: sourceManifest.length,
      factoryRangesVerified: variants.reduce(
        (sum, variant) => sum + variant.origins.length,
        0,
      ),
      selectedFactoryRangesVerified: selected.reduce(
        (sum, variant) => sum + variant.origins.length,
        0,
      ),
      formattedFactoriesParsed: variants.length,
      selectedFormattedFactories: selected.length,
      formattedFactoriesAstAuthenticated: variants.filter(
        (variant) => variant.authenticityMethod === "CANONICAL_AST",
      ).length,
      formattedFactoriesDerivationAuthenticated: variants.filter(
        (variant) =>
          variant.authenticityMethod === "EXACT_FORMATTER_DERIVATION",
      ).length,
      formattedAuthenticityPolicy:
        "Complete canonical factory AST, with exact pinned-formatter derivation required when the formatter changes Babel AST shape",
      selectionWithinRange: true,
      unsafePathsRejected: true,
      symlinksRejected: true,
      capturedCodeExecuted: false,
    },
  };
}

function content(value) {
  return Buffer.from(typeof value === "string" ? value : stable(value));
}

function encoded(name, value) {
  const json = content(value);
  return name.endsWith(".gz") ? gzipSync(json, { level: 9, mtime: 0 }) : json;
}

// Compressed bytes depend on the zlib build bundled with Node, so `.json.gz`
// records are also pinned by the sha256 and length of their decompressed
// content. Rebuild comparisons use that content identity, never gzip bytes.
function manifestEntry(name, bytes, raw) {
  const entry = { path: name, bytes: bytes.length, sha256: sha256(bytes) };
  if (name.endsWith(".gz")) {
    entry.contentBytes = raw.length;
    entry.contentSha256 = sha256(raw);
  }
  return entry;
}

export async function publishGraph(root, outputRelative, options = {}) {
  const output = resolve(root, outputRelative);
  if (output === resolve(root) || !output.startsWith(`${resolve(root)}${sep}`))
    throw new Error("output path escapes root");
  const reports = await buildGraph(root, options);
  const temporary = `${output}.tmp-${process.pid}`;
  const backup = `${output}.previous-${process.pid}`;
  await rm(temporary, { recursive: true, force: true });
  await rm(backup, { recursive: true, force: true });
  await mkdir(temporary, { recursive: true });
  const manifestFiles = [];
  for (const name of Object.keys(reports).sort(lexical)) {
    const bytes = encoded(name, reports[name]);
    await writeFile(join(temporary, name), bytes);
    manifestFiles.push(manifestEntry(name, bytes, content(reports[name])));
  }
  const manifest = { schemaVersion: GRAPH_VERSION, files: manifestFiles };
  await writeFile(join(temporary, "MANIFEST.json"), stable(manifest));
  let previous = false;
  try {
    try {
      await lstat(output);
      await rename(output, backup);
      previous = true;
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
    await options.onPublishStage?.("backup-created");
    await rename(temporary, output);
    if (previous) await rm(backup, { recursive: true, force: true });
  } catch (error) {
    await rm(output, { recursive: true, force: true });
    if (previous) await rename(backup, output);
    await rm(temporary, { recursive: true, force: true });
    throw error;
  }
  return { output, summary: reports["GRAPH-SUMMARY.json"], manifest };
}

export async function verifyGraph(root, outputRelative, options = {}) {
  const output = await safeFile(root, outputRelative);
  const manifest = JSON.parse(
    await readFile(join(output, "MANIFEST.json"), "utf8"),
  );
  const expected = new Set([
    "MANIFEST.json",
    ...manifest.files.map((entry) => entry.path),
  ]);
  const actual = await readdir(output);
  for (const name of actual) {
    const stat = await lstat(join(output, name));
    if (stat.isSymbolicLink()) throw new Error(`symlink rejected: ${name}`);
    if (!stat.isFile() || !expected.has(name))
      throw new Error(`unexpected generated evidence: ${name}`);
  }
  for (const name of expected)
    if (!actual.includes(name))
      throw new Error(`missing generated evidence: ${name}`);
  for (const entry of manifest.files) {
    const path = await safeFile(output, entry.path);
    const bytes = await readFile(path);
    if (bytes.length !== entry.bytes || sha256(bytes) !== entry.sha256)
      throw new Error(`generated evidence mismatch: ${entry.path}`);
    if (entry.path.endsWith(".gz")) {
      if (
        typeof entry.contentSha256 !== "string" ||
        !Number.isSafeInteger(entry.contentBytes)
      )
        throw new Error(`generated evidence lacks content pin: ${entry.path}`);
      let raw;
      try {
        raw = gunzipSync(bytes);
      } catch {
        throw new Error(`generated evidence mismatch: ${entry.path}`);
      }
      if (
        raw.length !== entry.contentBytes ||
        sha256(raw) !== entry.contentSha256
      )
        throw new Error(`generated evidence mismatch: ${entry.path}`);
      JSON.parse(raw.toString("utf8"));
    } else if (entry.path.endsWith(".json")) {
      JSON.parse(bytes.toString("utf8"));
    }
  }
  const rebuilt = await buildGraph(root, options);
  const listed = manifest.files.map((entry) => entry.path);
  if (new Set(listed).size !== listed.length ||
      listed.length !== Object.keys(rebuilt).length ||
      Object.keys(rebuilt).some((name) => !listed.includes(name)))
    throw new Error("generated evidence inventory differs from rebuilt reports");
  for (const entry of manifest.files) {
    if (!(entry.path in rebuilt))
      throw new Error(`generated evidence is not reproducible: ${entry.path}`);
    const raw = content(rebuilt[entry.path]);
    const fresh = entry.path.endsWith(".gz")
      ? raw.length === entry.contentBytes && sha256(raw) === entry.contentSha256
      : raw.length === entry.bytes && sha256(raw) === entry.sha256;
    if (!fresh) throw new Error(`generated evidence is stale: ${entry.path}`);
  }
  return {
    files: manifest.files.length,
    schemaVersion: manifest.schemaVersion,
    sourceRebuildVerified: true,
  };
}

export async function readReport(root, outputRelative, name) {
  const output = await safeFile(root, outputRelative);
  const bytes = await readFile(await safeFile(output, name));
  return JSON.parse(
    (name.endsWith(".gz") ? gunzipSync(bytes) : bytes).toString("utf8"),
  );
}
