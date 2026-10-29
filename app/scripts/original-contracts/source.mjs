import { readFile, lstat, realpath } from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { parse } from '@babel/parser';

export const RANGE_ENCODING = 'UTF-16 code-unit half-open offsets in UTF-8 decoded source';
export const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');

export function walk(node, visit, parents = []) {
  if (!node || typeof node !== 'object') return;
  if (Array.isArray(node)) {
    for (const child of node) walk(child, visit, parents);
    return;
  }
  if (typeof node.type !== 'string') return;
  visit(node, parents);
  for (const [key, value] of Object.entries(node)) {
    if (!['loc', 'start', 'end', 'comments', 'tokens', 'extra'].includes(key)) {
      walk(value, visit, [...parents, node]);
    }
  }
}

export function findNodes(node, predicate) {
  const found = [];
  walk(node, (child, parents) => {
    if (predicate(child, parents)) found.push(child);
  });
  return found;
}

export function exactlyOne(nodes, label) {
  if (nodes.length !== 1) throw new Error(`${label}: expected one AST node, got ${nodes.length}`);
  return nodes[0];
}

export function propertyName(node) {
  return node?.type === 'Identifier' ? node.name :
    ['StringLiteral', 'NumericLiteral'].includes(node?.type) ? String(node.value) : null;
}

export function member(node, object, property) {
  return node?.type === 'MemberExpression' && !node.computed &&
    node.object?.type === 'Identifier' && node.object.name === object &&
    propertyName(node.property) === property;
}

export function objectProperty(object, name) {
  return exactlyOne((object?.properties ?? []).filter((entry) =>
    entry.type === 'ObjectProperty' && !entry.computed && propertyName(entry.key) === name),
  `object property ${name}`).value;
}

export function literal(node) {
  if (['StringLiteral', 'NumericLiteral', 'BooleanLiteral'].includes(node?.type)) return node.value;
  if (node?.type === 'NullLiteral') return null;
  if (node?.type === 'UnaryExpression' && node.operator === '-' && node.argument.type === 'NumericLiteral') return -node.argument.value;
  if (node?.type === 'UnaryExpression' && node.operator === '!' && node.argument.type === 'NumericLiteral') return !node.argument.value;
  throw new Error(`unsupported literal AST: ${node?.type}`);
}

// Decode without replacing malformed bytes or discarding a UTF-8 BOM. A UTF-16
// offset inside a surrogate pair deliberately has no corresponding byte offset.
export function decodeSource(bytes) {
  const text = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes);
  if (!Buffer.from(text, 'utf8').equals(bytes)) throw new Error('non-roundtripping UTF-8 source');
  const byteOffsets = new Int32Array(text.length + 1).fill(-1);
  let units = 0;
  let offset = 0;
  byteOffsets[0] = 0;
  for (const character of text) {
    units += character.length;
    offset += Buffer.byteLength(character, 'utf8');
    byteOffsets[units] = offset;
  }
  return { text, byteOffsets };
}

async function safeFile(root, relative) {
  if (typeof relative !== 'string' || path.isAbsolute(relative) ||
      relative.split(/[\\/]/).some((part) => !part || part === '.' || part === '..')) {
    throw new Error(`unsafe source path: ${relative}`);
  }
  let current = root;
  for (const part of relative.split('/')) {
    current = path.join(current, part);
    if ((await lstat(current)).isSymbolicLink()) throw new Error(`source symlink: ${relative}`);
  }
  if (await realpath(current) !== current) throw new Error(`noncanonical source path: ${relative}`);
  return current;
}

function isFactoryRegistration(node) {
  if (node.type !== 'CallExpression' || node.callee?.type !== 'MemberExpression' ||
      propertyName(node.callee.property) !== 'push' || node.arguments[0]?.type !== 'ArrayExpression') return false;
  return findNodes(node.callee.object, (child) => child.type === 'MemberExpression' &&
    member(child, 'globalThis', 'TURBOPACK')).length > 0;
}

export async function openCorpus(appRoot) {
  const root = await realpath(appRoot);
  const read = async (relative) => readFile(await safeFile(root, relative));
  const manifestBytes = await read('evidence/web/manifest.json');
  const indexBytes = await read('recovered/modules.json');
  const manifest = JSON.parse(manifestBytes);
  const index = JSON.parse(indexBytes);
  if (index.rangeEncoding !== RANGE_ENCODING) throw new Error('unsupported inventory range encoding');
  const records = new Map();
  for (const record of manifest.records) {
    // capture.py records transport failures as {url, error}, with no file.
    if (Object.keys(record).length === 2 && typeof record.url === 'string' && typeof record.error === 'string') continue;
    if (records.has(record.path)) throw new Error(`duplicate capture path: ${record.path}`);
    records.set(record.path, record);
  }
  const captureCache = new Map();
  async function capture(relative) {
    // A manifest is evidence data, not authority to read arbitrary repository
    // files. Only retained object basenames can reach the filesystem reader.
    if (typeof relative !== 'string' || !/^evidence\/web\/objects\/[A-Za-z0-9][A-Za-z0-9._-]*$/.test(relative)) {
      throw new Error(`non-object capture path: ${relative}`);
    }
    if (!captureCache.has(relative)) {
      const record = records.get(relative);
      if (!record || record.status !== 200) throw new Error(`unmanifested successful capture: ${relative}`);
      const bytes = await read(relative);
      if (bytes.length !== record.bytes || sha256(bytes) !== record.sha256) throw new Error(`capture authentication failed: ${relative}`);
      const decoded = decodeSource(bytes);
      const result = { record, bytes, ...decoded };
      result.witness = (node, label) => {
        const { start, end } = node;
        if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start < 0 ||
            end <= start || end > result.text.length || result.byteOffsets[start] < 0 || result.byteOffsets[end] < 0) {
          throw new Error(`invalid UTF-16/UTF-8 boundary: ${relative}:${start}-${end}`);
        }
        const byteStart = result.byteOffsets[start];
        const byteEnd = result.byteOffsets[end];
        return { label, source: relative, url: record.url, sourceSha256: record.sha256,
          sourceBytes: record.bytes, utf16: [start, end], utf8: [byteStart, byteEnd],
          sha256: sha256(bytes.subarray(byteStart, byteEnd)) };
      };
      captureCache.set(relative, result);
    }
    return captureCache.get(relative);
  }
  async function javascript(relative) {
    const result = await capture(relative);
    if (!new URL(result.record.url).pathname.endsWith('.js')) throw new Error(`not captured JS: ${relative}`);
    if (!result.ast) {
      result.ast = parse(result.text, { sourceType: 'unambiguous', errorRecovery: false });
      result.factories = [];
      // The captured runtime's X decoder recurses only into the leading
      // array at each level, then scans ID groups up to their factory. Arrays
      // at arbitrary later positions are not another registration container.
      function registrations(elements, first) {
        let cursor = first;
        if (elements[cursor]?.type === 'ArrayExpression') {
          registrations(elements[cursor].elements, 0);
          cursor += 1;
        }
        let ids = [];
        for (const entry of elements.slice(cursor)) {
          if (['NumericLiteral', 'StringLiteral'].includes(entry?.type)) ids.push(entry.value);
          else if (['ArrowFunctionExpression', 'FunctionExpression'].includes(entry?.type)) {
            result.factories.push({ node: entry, ids });
            ids = [];
          } else ids = [];
        }
      }
      for (const registration of findNodes(result.ast, isFactoryRegistration)) {
        // X treats an outer two-element tuple as chunk metadata. A nested
        // leading [id, factory] pair is different and still recurses above.
        if (registration.arguments[0].elements.length === 2) continue;
        registrations(registration.arguments[0].elements, 1);
      }
    }
    return result;
  }
  async function factory(id, options = {}) {
    const choices = [];
    for (const variant of index.modules.filter((module) => module.ids.includes(id))) {
      for (const origin of variant.origins) {
        if (!options.source || origin.source === options.source) choices.push({ variant, origin });
      }
    }
    if (choices.length !== 1) throw new Error(`factory ${id}: ${choices.length} origins; explicit chunk context required`);
    const { variant, origin } = choices[0];
    const source = await javascript(origin.source);
    if (origin.url !== source.record.url) throw new Error(`factory URL mismatch: ${id}`);
    const registration = exactlyOne(source.factories.filter((entry) =>
      entry.node.start === origin.start && entry.node.end === origin.end && entry.ids.includes(id)),
    `factory ${id} registration`);
    const witness = source.witness(registration.node, `factory ${id}`);
    if (witness.sha256 !== variant.sha256) throw new Error(`factory content mismatch: ${id}`);
    return { id, ids: registration.ids, node: registration.node, capture: source,
      runtime: registration.node.params[0]?.name,
      witness: (node, label) => source.witness(node, label),
      text: (node = registration.node) => source.text.slice(node.start, node.end),
      provenance: { id, ids: registration.ids, ...witness } };
  }
  return { root, manifest, index, records, capture, javascript, factory,
    anchors: { manifestSha256: sha256(manifestBytes), inventorySha256: sha256(indexBytes) } };
}
