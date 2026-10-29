import { walk, member, propertyName, literal, findNodes, exactlyOne } from './source.mjs';

// This reads a bounded declaration language. It never invokes a captured
// function, getter, module or Zod implementation. Unsupported syntax fails.
export function createSchemaExtractor(corpus, { sources = {} } = {}) {
  const modules = new Map();
  const definitions = {};
  const witnesses = new Map();
  const pending = new Set();
  let primitiveWitnesses;
  const key = (id, name) => `${id}.${name}`;
  function importedId(node, ctx) {
    if (node?.type === 'Identifier') return ctx.imports.get(node.name);
    if (node?.type === 'CallExpression' && ['r', 'i'].some((method) => member(node.callee, ctx.factory.runtime, method)) &&
        node.arguments.length === 1 && node.arguments[0].type === 'NumericLiteral') return node.arguments[0].value;
    return undefined;
  }
  function remember(factory, node, label) {
    const record = factory.witness(node, label);
    witnesses.set(`${record.source}:${record.utf16.join(':')}`, record);
  }
  async function context(id) {
    if (modules.has(id)) return modules.get(id);
    const factory = await corpus.factory(id, sources[id] ? { source: sources[id] } : {});
    const locals = new Map();
    const exports = new Map();
    const imports = new Map();
    const output = factory.node.params[2]?.name;
    // Only declarations executed at factory scope, never inside nested code.
    walk(factory.node.body, (node, parents) => {
      if (parents.some((parent) => /Function|Method/.test(parent.type))) return;
      if (node.type === 'VariableDeclarator' && node.id.type === 'Identifier' && node.init) {
        locals.set(node.id.name, node.init);
        const init = node.init;
        if (init.type === 'CallExpression' && ['r', 'i'].some((method) => member(init.callee, factory.runtime, method)) &&
            init.arguments.length === 1 && init.arguments[0].type === 'NumericLiteral') {
          imports.set(node.id.name, init.arguments[0].value);
        }
      }
      if (node.type === 'AssignmentExpression' && node.operator === '=' && node.left.type === 'MemberExpression' &&
          !node.left.computed && node.left.object.type === 'Identifier' && node.left.object.name === output &&
          node.right.type !== 'AssignmentExpression' &&
          !(node.right.type === 'UnaryExpression' && node.right.operator === 'void')) {
        const name = propertyName(node.left.property);
        if (exports.has(name)) throw new Error(`multiple declarations: ${id}.${name}`);
        exports.set(name, node.right);
      }
    });
    const result = { factory, id, locals, exports, imports, output };
    modules.set(id, result);
    remember(factory, factory.node, `factory ${id}`);
    return result;
  }
  async function declaration(id, name) {
    const ctx = await context(id);
    const node = ctx.exports.get(name);
    if (!node) throw new Error(`missing declaration: ${id}.${name}`);
    remember(ctx.factory, node, `declaration ${id}.${name}`);
    return { node, factory: ctx.factory };
  }
  async function primitives() {
    if (!primitiveWitnesses) primitiveWitnesses = (async () => {
      const hashes = {
        876543: '4f5e713c7118058961d6d194625b7849fab8bd8cc447f079874947b4559367cc',
        599565: '375bf1a7298ca40a088210d7036d5422547ed59153f205de430426824b85caaf',
        408162: 'd27320343f07efeb58d5c33b728f3fdb687f68cfdaf361cbb07d80bb4800d1f2',
      };
      const contexts = {};
      for (const [id, hash] of Object.entries(hashes)) {
        const ctx = await context(Number(id));
        if (ctx.factory.provenance.sha256 !== hash) throw new Error(`unreviewed primitive implementation ${id}`);
        contexts[id] = ctx;
      }
      const vendor = contexts[599565].factory;
      for (const name of ['$ZodNumber', '$ZodCheckNumberFormat', '$ZodCheckMaxLength', '$ZodCheckMinLength', 'ZodNumber']) {
        const node = exactlyOne(findNodes(vendor.node, (node) => node.type === 'CallExpression' &&
          node.callee.type === 'MemberExpression' && propertyName(node.callee.property) === '$constructor' && node.arguments[0]?.value === name), name);
        remember(vendor, node, `primitive ${name}`);
      }
      for (const name of ['nb', 'u1']) remember(vendor, exactlyOne(findNodes(vendor.node,
        (node) => node.type === 'FunctionDeclaration' && node.id.name === name), name), `primitive safe integer ${name}`);
      const utility = contexts[408162].factory;
      remember(utility, exactlyOne(findNodes(utility.node, (node) => node.type === 'FunctionDeclaration' && node.id.name === 'ei'), 'codePointLength'), 'primitive codePointLength');
    })();
    await primitiveWitnesses;
  }
  async function ref(ctx, name, node, isExport = false) {
    const label = key(ctx.id, isExport ? name : `local:${name}`);
    if (!(label in definitions)) {
      definitions[label] = {};
      pending.add(label);
      remember(ctx.factory, node, `schema ${label}`);
      definitions[label] = await compileWith(node, ctx);
      pending.delete(label);
    }
    return { $ref: `#/$defs/${label}` };
  }
  async function resolveMember(node, ctx) {
    if (node.type !== 'MemberExpression' || node.computed || node.object.type !== 'Identifier') return null;
    const name = propertyName(node.property);
    if (node.object.name === ctx.output) {
      const value = ctx.exports.get(name);
      if (!value) throw new Error(`unknown export ${ctx.id}.${name}`);
      return { ctx, name, node: value };
    }
    const id = ctx.imports.get(node.object.name);
    if (id === undefined) return null;
    const target = await context(id);
    const value = target.exports.get(name);
    if (!value) throw new Error(`unknown imported declaration ${id}.${name}`);
    return { ctx: target, name, node: value };
  }
  function deref(schema) {
    const seen = new Set();
    while (schema.$ref) {
      const name = schema.$ref.slice('#/$defs/'.length);
      if (seen.has(name) || pending.has(name)) throw new Error(`recursive shape cannot be expanded: ${name}`);
      seen.add(name);
      schema = definitions[name];
      if (!schema) throw new Error(`missing definition ${name}`);
    }
    return schema;
  }
  async function constant(node, ctx) {
    if (node.type === 'Identifier') {
      if (!ctx.locals.has(node.name)) throw new Error(`unknown constant ${ctx.id}.${node.name}`);
      return constant(ctx.locals.get(node.name), ctx);
    }
    if (node.type === 'ArrayExpression') {
      const result = [];
      for (const element of node.elements) {
        if (!element) throw new Error('array hole');
        if (element.type === 'SpreadElement') {
          const value = await constant(element.argument, ctx);
          if (!Array.isArray(value)) throw new Error('non-array constant spread');
          result.push(...value);
        } else result.push(await constant(element, ctx));
      }
      return result;
    }
    if (node.type === 'TemplateLiteral') {
      let result = node.quasis[0].value.cooked;
      for (let i = 0; i < node.expressions.length; i++) result += String(await constant(node.expressions[i], ctx)) + node.quasis[i + 1].value.cooked;
      return result;
    }
    if (node.type === 'MemberExpression' && !node.computed && propertyName(node.property) === 'length') {
      const value = await constant(node.object, ctx);
      if (!Array.isArray(value)) throw new Error('length of non-array');
      return value.length;
    }
    if (node.type === 'MemberExpression' && !node.computed && propertyName(node.property) === 'options') {
      const schema = deref(await compileWith(node.object, ctx));
      if (!schema.enum) throw new Error('options of non-enum');
      return schema.enum;
    }
    const resolved = await resolveMember(node, ctx);
    if (resolved) {
      remember(resolved.ctx.factory, resolved.node, `constant ${resolved.ctx.id}.${resolved.name}`);
      return constant(resolved.node, resolved.ctx);
    }
    return literal(node);
  }
  async function shape(node, ctx) {
    if (node.type === 'Identifier') return shape(ctx.locals.get(node.name), ctx);
    if (node?.type !== 'ObjectExpression') throw new Error(`unsupported object shape: ${node?.type}`);
    const properties = {};
    for (const property of node.properties) {
      if (property.type === 'SpreadElement') {
        Object.assign(properties, await shape(property.argument, ctx));
      } else if (property.type === 'ObjectProperty' && !property.computed) {
        properties[propertyName(property.key)] = await compileWith(property.value, ctx);
      } else if (property.type === 'ObjectMethod' && property.kind === 'get' && !property.computed && property.params.length === 0 &&
          property.body.body.length === 1 && property.body.body[0].type === 'ReturnStatement') {
        // Preserve the returned declaration, without invoking the getter.
        properties[propertyName(property.key)] = await compileWith(property.body.body[0].argument, ctx);
      } else throw new Error(`unsupported shape member: ${property.type}`);
    }
    return properties;
  }
  async function compileWith(node, ctx) {
    if (!node) throw new Error('missing schema expression');
    if (node.type === 'Identifier') {
      const value = ctx.locals.get(node.name);
      if (!value) throw new Error(`unknown schema identifier ${ctx.id}.${node.name}`);
      return ref(ctx, node.name, value);
    }
    if (node.type === 'MemberExpression') {
      const target = await resolveMember(node, ctx);
      if (target) return ref(target.ctx, target.name, target.node, true);
    }
    if (node.type !== 'CallExpression') throw new Error(`unsupported schema expression in ${ctx.id}: ${node.type} ${ctx.factory.text(node)}`);
    let callee = node.callee;
    if (callee.type === 'SequenceExpression' && callee.expressions.length === 2 && callee.expressions[0].type === 'NumericLiteral' && callee.expressions[0].value === 0) callee = callee.expressions[1];
    // The captured openEnum helper admits unknown strings. Recognize its exact
    // authenticated factory, not an arbitrary function with the same name.
    if (callee.type === 'MemberExpression' && callee.object.type === 'Identifier' &&
        ctx.imports.get(callee.object.name) === 617159 && propertyName(callee.property) === 'openEnum') {
      const helper = await context(617159);
      if (helper.factory.provenance.sha256 !== 'e2578f8e5b5ad78b72da3056976e38a96e3d7e24f0768215374750f09229074e') throw new Error('unrecognized openEnum implementation');
      remember(helper.factory, helper.factory.node, 'openEnum implementation');
      const values = await constant(node.arguments[0], ctx);
      const description = await constant(node.arguments[1], ctx);
      if (!Array.isArray(values) || !values.every((value) => typeof value === 'string') || typeof description !== 'string') throw new Error('invalid openEnum arguments');
      return { anyOf: [{ enum: values }, { type: 'string' }], 'x-open-enum': true,
        description: `${description}. Known values: ${values.join(', ')}` };
    }
    if (callee.type !== 'MemberExpression' || callee.computed) throw new Error(`unsupported schema call: ${callee.type}`);
    const method = propertyName(callee.property);
    const target = callee.object;
    const isZod = target.type === 'MemberExpression' && !target.computed && propertyName(target.property) === 'z' && importedId(target.object, ctx) === 876543;
    if (isZod) {
      await primitives();
      if (['string', 'number', 'boolean', 'null'].includes(method) && node.arguments.length === 0) return { type: method };
      if (method === 'object' && node.arguments.length === 1) return { type: 'object', properties: await shape(node.arguments[0], ctx) };
      if (method === 'array' && node.arguments.length === 1) return { type: 'array', items: await compileWith(node.arguments[0], ctx) };
      if (method === 'enum' && node.arguments.length === 1) return { enum: await constant(node.arguments[0], ctx) };
      if (method === 'literal' && node.arguments.length === 1) return { const: await constant(node.arguments[0], ctx) };
      if (method === 'union' && node.arguments[0]?.type === 'ArrayExpression' && node.arguments.length === 1 && node.arguments[0].elements.length === 0) throw new Error('empty union cannot be emitted as JSON Schema anyOf');
      if (method === 'union' && node.arguments[0]?.type === 'ArrayExpression' && node.arguments.length === 1) return { anyOf: await Promise.all(node.arguments[0].elements.map((value) => compileWith(value, ctx))) };
      throw new Error(`unsupported Zod constructor ${method}`);
    }
    const base = await compileWith(target, ctx);
    if (['optional', 'nullable', 'int', 'nonnegative'].includes(method) && node.arguments.length !== 0) throw new Error(`unexpected ${method} arguments`);
    if (method === 'optional') return { ...base, 'x-zod-optional': true };
    if (method === 'nullable') return { anyOf: [base, { type: 'null' }] };
    if (method === 'describe' && node.arguments.length === 1) return { ...base, description: await constant(node.arguments[0], ctx) };
    const expanded = deref(base);
    if (method === 'int' && expanded.type === 'number') return { ...expanded, type: 'integer',
      minimum: Math.max(expanded.minimum ?? -Infinity, Number.MIN_SAFE_INTEGER),
      maximum: Math.min(expanded.maximum ?? Infinity, Number.MAX_SAFE_INTEGER) };
    if (method === 'nonnegative' && ['number', 'integer'].includes(expanded.type)) return { ...expanded, minimum: Math.max(expanded.minimum ?? -Infinity, 0) };
    if (['min', 'max'].includes(method) && node.arguments.length === 1) {
      const value = await constant(node.arguments[0], ctx);
      if (typeof value !== 'number' || !Number.isFinite(value)) throw new Error('invalid bound');
      const suffix = { string: 'Length', array: 'Items' }[expanded.type];
      const combine = method === 'min' ? Math.max : Math.min;
      if (suffix) return { ...expanded, [`${method}${suffix}`]: combine(expanded[`${method}${suffix}`] ?? (method === 'min' ? -Infinity : Infinity), value) };
      if (['number', 'integer'].includes(expanded.type)) {
        const keyword = method === 'min' ? 'minimum' : 'maximum';
        return { ...expanded, [keyword]: combine(expanded[keyword] ?? (method === 'min' ? -Infinity : Infinity), value) };
      }
    }
    if (method === 'extend' && expanded.type === 'object' && node.arguments.length === 1) return { ...expanded, properties: { ...expanded.properties, ...await shape(node.arguments[0], ctx) } };
    if (method === 'pick' && expanded.type === 'object' && node.arguments[0]?.type === 'ObjectExpression' && node.arguments.length === 1) {
      const properties = {};
      for (const property of node.arguments[0].properties) {
        if (property.type !== 'ObjectProperty' || property.computed || await constant(property.value, ctx) !== true) throw new Error('unsupported pick mask');
        const name = propertyName(property.key);
        if (!(name in expanded.properties)) throw new Error(`unknown picked property ${name}`);
        properties[name] = expanded.properties[name];
      }
      return { ...expanded, properties };
    }
    throw new Error(`unsupported schema method ${method} on ${expanded.type ?? '$ref/union'}`);
  }
  async function compile(node, factory) {
    return compileWith(node, await context(factory.id));
  }
  async function schema(id, name) {
    const { node } = await declaration(id, name);
    return ref(await context(id), name, node, true);
  }
  function document(roots) {
    function allowsUndefined(schema, seen = new Set()) {
      if (schema['x-zod-optional']) return true;
      if (schema.$ref) {
        const name = schema.$ref.slice('#/$defs/'.length);
        if (seen.has(name)) return false;
        return allowsUndefined(definitions[name], new Set([...seen, name]));
      }
      return schema.anyOf?.some((value) => allowsUndefined(value, seen)) ?? false;
    }
    const result = structuredClone({ $schema: 'https://json-schema.org/draft/2020-12/schema', ...roots, $defs: definitions });
    function finish(node) {
      if (!node || typeof node !== 'object') return;
      if (node.type === 'object') node.required = Object.entries(node.properties).filter(([, value]) => !allowsUndefined(value)).map(([name]) => name);
      for (const value of Object.values(node)) if (value && typeof value === 'object') Array.isArray(value) ? value.forEach(finish) : finish(value);
    }
    finish(result);
    return result;
  }
  return { declaration, schema, compile, document,
    constant: async (node, factory) => constant(node, await context(factory.id)),
    witnesses: () => [...witnesses.values()] };
}
