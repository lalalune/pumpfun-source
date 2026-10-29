import {
  openCorpus,
  findNodes,
  exactlyOne,
  member,
} from "../original-contracts/source.mjs";

export const RUNTIME_SOURCE = "evidence/web/objects/f25d7686d048ae16.js";
const RUNTIME_SHA256 =
  "b5f9b5199b99ab6c141f4540f0b7d0fe803c4ecf6956849ecb6e59d3d439272e";
const isFunction = (node) =>
  ["ArrowFunctionExpression", "FunctionExpression"].includes(node?.type);
const isLiteral = (node) =>
  node?.type === "StringLiteral" ||
  (node?.type === "NumericLiteral" && Number.isFinite(node.value));
const zero = (node) => node?.type === "NumericLiteral" && node.value === 0;

function witness(source, node, label) {
  return {
    ...source.witness(node, label),
    text: source.text.slice(node.start, node.end),
  };
}

export async function runtimeEvidence(corpus) {
  const source = await corpus.javascript(RUNTIME_SOURCE);
  if (source.record.sha256 !== RUNTIME_SHA256)
    throw new Error("unsupported export-provider runtime");
  const assignment = (name) =>
    exactlyOne(
      findNodes(
        source.ast,
        (node) =>
          node.type === "AssignmentExpression" && member(node.left, "u", name),
      ),
      `runtime u.${name}`,
    );
  const helper = (name) =>
    exactlyOne(
      findNodes(
        source.ast,
        (node) => node.type === "FunctionDeclaration" && node.id?.name === name,
      ),
      `runtime helper ${name}`,
    );
  return [
    ...["s", "S", "c", "i"].map((name) =>
      witness(source, assignment(name), `runtime u.${name}`),
    ),
    ...["m", "d", "h", "f", "p", "w"].map((name) =>
      witness(source, helper(name), `runtime helper ${name}`),
    ),
    witness(
      source,
      exactlyOne(
        findNodes(
          source.ast,
          (node) =>
            node.type === "VariableDeclarator" &&
            node.id?.name === "F" &&
            node.init?.type === "ArrowFunctionExpression",
        ),
        "runtime F",
      ),
      "runtime helper F",
    ),
  ];
}

// Deliberately limited to direct expression statements in a physical factory,
// including their direct comma sequence. No nested scopes or control flow are
// traversed, and this does not resolve aliases or lexical bindings (#1180).
function directExpressions(node) {
  return node?.type === "SequenceExpression"
    ? node.expressions.flatMap(directExpressions)
    : [node];
}

function targetOf(call, ids, source) {
  const node = call.arguments[1];
  if (!node || node.type === "NullLiteral") {
    return {
      kind: "current-module",
      ids,
      raw: node ? witness(source, node, "null target") : null,
    };
  }
  if (isLiteral(node))
    return {
      kind: "literal",
      value: node.value,
      valueType: typeof node.value,
      raw: witness(source, node, "explicit target"),
    };
  return {
    kind: "dynamic",
    raw: witness(source, node, "unsupported target expression"),
  };
}

function lowerDescriptors(array, source) {
  const descriptors = [];
  for (let i = 0; i < array.elements.length; ) {
    const name = array.elements[i++];
    if (!isLiteral(name))
      return {
        status: "unsupported",
        reason: "nonliteral export name",
        descriptors: [],
      };
    const value = array.elements[i++];
    if (!value || value.type === "SpreadElement")
      return {
        status: "unsupported",
        reason: "incomplete/dynamic descriptor",
        descriptors: [],
      };
    const entry = {
      exportName: name.value,
      exportNameType: typeof name.value,
      name: witness(source, name, "export name"),
    };
    if (zero(value)) {
      const constant = array.elements[i++];
      if (!constant || constant.type === "SpreadElement")
        return {
          status: "unsupported",
          reason: "incomplete constant",
          descriptors: [],
        };
      descriptors.push({
        ...entry,
        kind: "constant",
        value: witness(source, constant, "constant expression"),
      });
    } else if (isFunction(value)) {
      const setter = isFunction(array.elements[i]) ? array.elements[i++] : null;
      descriptors.push({
        ...entry,
        kind: "accessor",
        getter: witness(source, value, "getter expression"),
        setter: setter ? witness(source, setter, "setter expression") : null,
      });
    } else
      return {
        status: "unsupported",
        reason: "non-inline accessor or nonzero tag",
        descriptors: [],
      };
  }
  return { status: "decoded", descriptors };
}

function importInitializers(factory, identifier, before, source) {
  const candidates = [];
  for (const statement of factory.node.body.body) {
    if (statement.start >= before || statement.type !== "VariableDeclaration")
      continue;
    for (const declaration of statement.declarations) {
      const init = declaration.init;
      if (
        declaration.id?.name === identifier &&
        init?.type === "CallExpression" &&
        member(init.callee, factory.runtime, "i") &&
        init.arguments.length === 1 &&
        isLiteral(init.arguments[0])
      ) {
        candidates.push({
          moduleId: init.arguments[0].value,
          moduleIdType: typeof init.arguments[0].value,
          raw: witness(
            source,
            declaration,
            "preceding import initializer candidate",
          ),
        });
      }
    }
  }
  return candidates;
}

function upperDescriptors(array, source, factory, call) {
  const descriptors = [];
  const values = array.elements;
  for (let i = 0; i < values.length; ) {
    const namespace = values[i++];
    if (!namespace || namespace.type === "SpreadElement")
      return {
        status: "unsupported",
        reason: "dynamic namespace segment",
        descriptors: [],
      };
    const start = i;
    while (i < values.length && !zero(values[i])) i++;
    const fields = values.slice(start, i);
    i++;
    if (fields.some((field) => !isLiteral(field)))
      return {
        status: "unsupported",
        reason: "dynamic alias descriptor",
        descriptors: [],
      };
    const namespaceRecord = {
      kind: isLiteral(namespace) ? "module-id" : "expression",
      raw: witness(source, namespace, "namespace expression"),
      ...(isLiteral(namespace)
        ? { moduleId: namespace.value, moduleIdType: typeof namespace.value }
        : {}),
      importInitializerCandidates:
        namespace.type === "Identifier"
          ? importInitializers(factory, namespace.name, call.start, source)
          : [],
    };
    const packed = fields.length === 1;
    if (packed && fields[0].type !== "StringLiteral")
      return {
        status: "unsupported",
        reason: "packed alias requires string",
        descriptors: [],
      };
    const aliases = packed
      ? fields[0].value.split(",")
      : fields.map((field) => field.value);
    for (let j = 0; j < aliases.length; j += 2) {
      descriptors.push({
        kind: "namespace-property",
        exportName: aliases[j],
        exportNameType: typeof aliases[j],
        // m does not default a missing source property to the export name.
        property:
          j + 1 < aliases.length
            ? {
                kind: "literal",
                value: aliases[j + 1],
                valueType: typeof aliases[j + 1],
              }
            : { kind: "undefined" },
        namespace: namespaceRecord,
        encoding: packed ? "comma-packed" : "alternating",
        aliasFields: (packed ? fields : fields.slice(j, j + 2)).map((field) =>
          witness(source, field, "raw alias field"),
        ),
      });
    }
  }
  return { status: "decoded", descriptors };
}

export function exportDeclarations(factory) {
  if (!factory.runtime || factory.node.body?.type !== "BlockStatement")
    return [];
  const source = factory.capture;
  const declarations = [];
  for (const statement of factory.node.body.body) {
    if (statement.type !== "ExpressionStatement") continue;
    for (const call of directExpressions(statement.expression)) {
      if (
        call?.type !== "CallExpression" ||
        !["s", "S"].some((name) => member(call.callee, factory.runtime, name))
      )
        continue;
      const method = call.callee.property.name;
      const argument = call.arguments[0];
      const decoded =
        argument?.type !== "ArrayExpression"
          ? {
              status: "unsupported",
              reason: "nonliteral descriptor array",
              descriptors: [],
            }
          : method === "s"
            ? lowerDescriptors(argument, source)
            : upperDescriptors(argument, source, factory, call);
      declarations.push({
        method,
        target: targetOf(call, factory.ids, source),
        raw: witness(source, call, `runtime.${method} declaration`),
        ...decoded,
      });
    }
  }
  return declarations;
}

export async function inspectExportProviders(appRoot, id, sources) {
  if (
    typeof id !== "string" ||
    !id ||
    !Array.isArray(sources) ||
    !sources.length
  ) {
    throw new Error(
      "export providers require a module ID and explicit captured source context",
    );
  }
  const corpus = await openCorpus(appRoot);
  const runtime = await runtimeEvidence(corpus);
  const providers = [];
  const literalRegistrations = [];
  const unresolvedTargets = [];
  const sourceContexts = [];
  for (const relative of [...new Set(sources)].sort()) {
    const source = await corpus.javascript(relative);
    sourceContexts.push({
      source: relative,
      sourceSha256: source.record.sha256,
      sourceBytes: source.bytes.length,
    });
    for (const registration of source.factories) {
      const physical = source.witness(
        registration.node,
        "physical registered factory",
      );
      const indexed = corpus.index.modules.filter(
        (variant) =>
          variant.sha256 === physical.sha256 &&
          variant.origins.some(
            (origin) =>
              origin.source === relative &&
              origin.url === source.record.url &&
              origin.start === registration.node.start &&
              origin.end === registration.node.end,
          ),
      );
      if (
        indexed.length !== 1 ||
        !registration.ids.length ||
        registration.ids.some(
          (registered) => !indexed[0].ids.includes(registered),
        )
      ) {
        throw new Error(
          `physical factory inventory binding failed: ${relative}:${registration.node.start}`,
        );
      }
      const factory = {
        node: registration.node,
        ids: registration.ids,
        capture: source,
        runtime:
          registration.node.params[0]?.type === "Identifier"
            ? registration.node.params[0].name
            : null,
      };
      if (registration.ids.some((registered) => String(registered) === id)) {
        literalRegistrations.push({ ids: registration.ids, ...physical });
      }
      for (const declaration of exportDeclarations(factory)) {
        const owner = { ids: registration.ids, ...physical };
        if (declaration.target.kind === "dynamic")
          unresolvedTargets.push({ physicalFactory: owner, ...declaration });
        else if (
          declaration.target.kind === "literal"
            ? String(declaration.target.value) === id
            : declaration.target.ids.some(
                (registered) => String(registered) === id,
              )
        ) {
          providers.push({ physicalFactory: owner, ...declaration });
        }
      }
    }
  }
  return {
    kind: "source-context-export-provider-diagnostic",
    query: id,
    anchors: corpus.anchors,
    sourceContexts,
    runtime,
    ambiguous: providers.length > 1,
    literalRegistrations,
    providers,
    unresolvedTargets,
    limits: [
      "Only supplied captured objects and direct factory-body declaration statements are inspected; absence is not a whole-corpus absence proof.",
      "Receiver recognition uses the outer parameter spelling in direct statements, not the pending graph lexical-binding correction.",
      "Every physical registration/provider is retained; no active variant or initialization winner is selected.",
      "Implicit current-module IDs are possible registration/invocation contexts, not simultaneous export targets.",
      "Declarations become available only if the producing factory and preceding expressions initialize successfully; imports/control flow are not executed.",
      "Namespace initializer candidates are syntax witnesses, not alias, reassignment, lexical-binding or runtime-value resolution.",
      "Uppercase S may copy a property descriptor or create a getter; no namespace property, getter, descriptor value or factory is evaluated.",
      "Existing graph aggregate exports, literal identities, inventories, counts, route reachability and report files are unchanged.",
    ],
  };
}
