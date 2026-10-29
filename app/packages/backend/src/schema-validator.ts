/**
 * Minimal JSON Schema validator for the subset used by contracts/developer.openapi.json.
 *
 * Purpose: let tests assert that a response body conforms to the documented contract
 * without adding a runtime dependency.
 *
 * Supported keywords, chosen by measuring what the OpenAPI snapshot actually uses:
 *   type, nullable, enum, const, properties, required, additionalProperties,
 *   items, minItems, maxItems, minLength, maxLength, minimum, maximum,
 *   pattern, oneOf, anyOf, allOf, and local $ref ("#/components/...").
 *
 * Measured keyword usage across the snapshot's paths: type 4372, description 2133,
 * nullable 1501, $ref 798, required 703, properties 489, additionalProperties 473,
 * enum 265, items 210, minimum 126, maximum 116, anyOf 109, allOf 22, maxLength 21,
 * maxItems 11, pattern 11, format 7, minItems 6, minLength 3, oneOf 2.
 *
 * `$ref` and `allOf` dominate, so both are resolved. Without them the validator would
 * silently pass payloads it should reject, which is worse than having no validator.
 *
 * Deliberately NOT implemented: `format` (7 uses, advisory rather than asserting in
 * JSON Schema) and `not` (unused). If a contract later depends on either for
 * correctness, this validator must grow or the test must check the property directly.
 *
 * This validator is strict about extra properties when additionalProperties is false:
 * the contract uses that flag heavily, and a response that leaks undocumented keys is a
 * contract violation even if a looser check would pass.
 */

export interface SchemaNode {
  type?: string | string[];
  nullable?: boolean;
  enum?: unknown[];
  const?: unknown;
  properties?: Record<string, SchemaNode>;
  required?: string[];
  additionalProperties?: boolean | SchemaNode;
  items?: SchemaNode;
  minItems?: number;
  maxItems?: number;
  minLength?: number;
  maxLength?: number;
  minimum?: number;
  maximum?: number;
  pattern?: string;
  oneOf?: SchemaNode[];
  anyOf?: SchemaNode[];
  allOf?: SchemaNode[];
  $ref?: string;
  description?: string;
}

export interface ValidationIssue {
  path: string;
  message: string;
}

export type SchemaRoot = Record<string, unknown>;

/** Equality of decoded JSON values, independent of object key order. */
function jsonEqual(left: unknown, right: unknown): boolean {
  if (left === right) return true;
  if (Array.isArray(left) || Array.isArray(right)) {
    return Array.isArray(left) && Array.isArray(right) && left.length === right.length &&
      left.every((item, index) => jsonEqual(item, right[index]));
  }
  if (left !== null && right !== null && typeof left === 'object' && typeof right === 'object') {
    const a = left as Record<string, unknown>;
    const b = right as Record<string, unknown>;
    const keys = Object.keys(a);
    return keys.length === Object.keys(b).length && keys.every(key => Object.hasOwn(b, key) && jsonEqual(a[key], b[key]));
  }
  return false;
}

function typeMatches(value: unknown, type: string): boolean {
  switch (type) {
    case 'null':
      return value === null;
    case 'boolean':
      return typeof value === 'boolean';
    case 'string':
      return typeof value === 'string';
    case 'integer':
      return typeof value === 'number' && Number.isInteger(value);
    case 'number':
      return typeof value === 'number' && Number.isFinite(value);
    case 'array':
      return Array.isArray(value);
    case 'object':
      return typeof value === 'object' && value !== null && !Array.isArray(value);
    default:
      return true; // unknown type keyword: do not fail on it
  }
}

/** Resolve a local JSON pointer such as "#/components/schemas/User". */
function resolveRef(ref: string, root?: SchemaRoot): SchemaNode | undefined {
  if (!ref.startsWith('#') || !root) return undefined;
  let node: unknown = root;
  let pointer: string;
  try { pointer = decodeURIComponent(ref.slice(1)); } catch { return undefined; }
  if (pointer === '') return root as SchemaNode;
  if (!pointer.startsWith('/')) return undefined;
  for (const rawPart of pointer.slice(1).split('/')) {
    if (/~(?![01])/.test(rawPart)) return undefined;
    const part = rawPart.replace(/~1/g, '/').replace(/~0/g, '~');
    if (node === null || typeof node !== 'object' || !Object.hasOwn(node, part)) return undefined;
    node = (node as Record<string, unknown>)[part];
  }
  return node && typeof node === 'object' ? (node as SchemaNode) : undefined;
}

/**
 * Validate `value` against `schema`, returning a list of issues (empty means pass).
 * Pass `root` (the whole OpenAPI document) to enable `$ref` resolution.
 */
export function validateAgainstSchema(
  value: unknown,
  schema: SchemaNode,
  path = '$',
  root?: SchemaRoot,
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  if (!schema || typeof schema !== 'object') return issues;

  if (value === null && schema.nullable === true) {
    if (schema.enum && !schema.enum.includes(null)) {
      issues.push({ path, message: `value null is not one of ${JSON.stringify(schema.enum)}` });
    }
    if ('const' in schema && schema.const !== null) {
      issues.push({ path, message: `value null is not the required const ${JSON.stringify(schema.const)}` });
    }
    return issues;
  }

  if (schema.$ref) {
    const target = resolveRef(schema.$ref, root);
    if (!target) {
      return [{ path, message: `unresolved $ref ${schema.$ref}` }];
    }
    return validateAgainstSchema(value, target, path, root);
  }

  for (const branch of schema.allOf ?? []) {
    issues.push(...validateAgainstSchema(value, branch, path, root));
  }

  if (schema.type !== undefined) {
    const types = Array.isArray(schema.type) ? schema.type : [schema.type];
    if (!types.some(t => typeMatches(value, t))) {
      issues.push({ path, message: `expected type ${types.join('|')}, received ${describe(value)}` });
      return issues; // further checks would be noise
    }
  }

  if (schema.enum && !schema.enum.some(candidate => jsonEqual(candidate, value))) {
    issues.push({ path, message: `value ${JSON.stringify(value)} is not one of ${JSON.stringify(schema.enum)}` });
  }
  if ('const' in schema && !jsonEqual(schema.const, value)) {
    issues.push({ path, message: `value ${JSON.stringify(value)} is not the required const ${JSON.stringify(schema.const)}` });
  }

  if (schema.oneOf) {
    const matches = schema.oneOf.filter(branch => validateAgainstSchema(value, branch, path, root).length === 0).length;
    if (matches !== 1) {
      issues.push({ path, message: matches === 0 ? 'value matched none of the oneOf branches' : 'value matched multiple oneOf branches' });
    }
  }
  if (schema.anyOf && schema.anyOf.length > 0) {
    const passed = schema.anyOf.some(branch => validateAgainstSchema(value, branch, path, root).length === 0);
    if (!passed) issues.push({ path, message: 'value matched none of the anyOf branches' });
  }

  if (typeof value === 'string') {
    const length = [...value].length;
    if (schema.minLength !== undefined && length < schema.minLength) {
      issues.push({ path, message: `string shorter than minLength ${schema.minLength}` });
    }
    if (schema.maxLength !== undefined && length > schema.maxLength) {
      issues.push({ path, message: `string longer than maxLength ${schema.maxLength}` });
    }
    if (schema.pattern !== undefined) {
      let re: RegExp | undefined;
      try {
        re = new RegExp(schema.pattern);
      } catch {
        issues.push({ path, message: `schema pattern is not a valid regular expression: ${schema.pattern}` });
      }
      if (re && !re.test(value)) {
        issues.push({ path, message: `string does not match pattern ${schema.pattern}` });
      }
    }
  }

  if (typeof value === 'number') {
    if (schema.minimum !== undefined && value < schema.minimum) {
      issues.push({ path, message: `number below minimum ${schema.minimum}` });
    }
    if (schema.maximum !== undefined && value > schema.maximum) {
      issues.push({ path, message: `number above maximum ${schema.maximum}` });
    }
  }

  if (Array.isArray(value)) {
    if (schema.minItems !== undefined && value.length < schema.minItems) {
      issues.push({ path, message: `array shorter than minItems ${schema.minItems}` });
    }
    if (schema.maxItems !== undefined && value.length > schema.maxItems) {
      issues.push({ path, message: `array longer than maxItems ${schema.maxItems}` });
    }
    if (schema.items) {
      for (let i = 0; i < value.length; i++) {
        issues.push(...validateAgainstSchema(value[i], schema.items as SchemaNode, `${path}[${i}]`, root));
      }
    }
  }

  if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
    const obj = value as Record<string, unknown>;
    for (const key of schema.required ?? []) {
      if (!Object.hasOwn(obj, key)) issues.push({ path: `${path}.${key}`, message: 'required property is missing' });
    }
    const props = schema.properties ?? {};
    for (const [key, v] of Object.entries(obj)) {
      if (Object.hasOwn(props, key)) {
        issues.push(...validateAgainstSchema(v, props[key], `${path}.${key}`, root));
      } else if (schema.additionalProperties === false) {
        issues.push({ path: `${path}.${key}`, message: 'property is not allowed by additionalProperties: false' });
      } else if (typeof schema.additionalProperties === 'object') {
        issues.push(...validateAgainstSchema(v, schema.additionalProperties, `${path}.${key}`, root));
      }
    }
  }

  return issues;
}

function describe(value: unknown): string {
  if (value === null) return 'null';
  if (Array.isArray(value)) return 'array';
  return typeof value;
}

/** Throw with a readable message when the value does not conform. */
export function assertSchema(
  value: unknown,
  schema: SchemaNode,
  label: string,
  root?: SchemaRoot,
): void {
  const issues = validateAgainstSchema(value, schema, '$', root);
  if (issues.length > 0) {
    const rendered = issues.slice(0, 10).map(i => `  ${i.path}: ${i.message}`).join('\n');
    throw new Error(`${label} does not conform to the contract:\n${rendered}`);
  }
}
