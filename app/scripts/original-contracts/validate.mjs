// Acceptance checks for the bounded declarative output of schema.mjs. This is
// an offline tool, not captured Zod execution or a server compatibility claim.
export function validateDeclared(document, schema, value) {
  const issues = [];
  function visit(rule, input, path, depth) {
    if (depth > 200) throw new Error('declaration validation depth limit exceeded');
    const fail = (message) => issues.push({ path, message });
    if (input === undefined && rule['x-zod-optional']) return;
    if (rule.$ref) {
      if (!rule.$ref.startsWith('#/$defs/')) throw new Error('unsupported external schema reference');
      const name = rule.$ref.slice('#/$defs/'.length);
      if (!document.$defs || !Object.hasOwn(document.$defs, name)) throw new Error(`unresolved schema ${rule.$ref}`);
      const target = document.$defs[name];
      if (!target) throw new Error(`unresolved schema ${rule.$ref}`);
      visit(target, input, path, depth + 1);
    }
    if (rule.anyOf) {
      const before = issues.length;
      let accepted = false;
      for (const alternative of rule.anyOf) {
        visit(alternative, input, path, depth + 1);
        if (issues.length === before) { accepted = true; break; }
        issues.splice(before);
      }
      if (!accepted) { fail('does not satisfy any declared alternative'); return; }
    }
    if ('const' in rule && input !== rule.const) fail('does not equal declared literal');
    if (rule.enum && !rule.enum.includes(input)) fail('not in declared enum');
    if (rule.type === 'null' && input !== null) fail('expected null');
    if (rule.type === 'boolean' && typeof input !== 'boolean') fail('expected boolean');
    if (rule.type === 'string') {
      if (typeof input !== 'string') fail('expected string');
      else {
        const length = Array.from(input).length;
        if (rule.minLength !== undefined && length < rule.minLength) fail('below declared code-point string length');
        if (rule.maxLength !== undefined && length > rule.maxLength) fail('above declared code-point string length');
      }
    }
    if (rule.type === 'number' || rule.type === 'integer') {
      if (typeof input !== 'number' || !Number.isFinite(input)) fail('expected finite number');
      else {
        if (rule.type === 'integer' && !Number.isInteger(input)) fail('expected integer');
        if (rule.minimum !== undefined && input < rule.minimum) fail('below declared minimum');
        if (rule.maximum !== undefined && input > rule.maximum) fail('above declared maximum');
      }
    }
    if (rule.type === 'array') {
      if (!Array.isArray(input)) fail('expected array');
      else {
        if (rule.minItems !== undefined && input.length < rule.minItems) fail('below declared item minimum');
        if (rule.maxItems !== undefined && input.length > rule.maxItems) fail('above declared item maximum');
        for (const [index, item] of input.entries()) visit(rule.items, item, `${path}/${index}`, depth + 1);
      }
    }
    if (rule.type === 'object') {
      if (input === null || typeof input !== 'object' || Array.isArray(input)) fail('expected object');
      else for (const [name, child] of Object.entries(rule.properties)) {
        // Missing properties and explicit undefined have Zod's same optional
        // boundary. No defaults, stripping or transformations are performed.
        visit(child, Object.hasOwn(input, name) ? input[name] : undefined, `${path}/${name}`, depth + 1);
      }
    }
  }
  visit(schema, value, '', 0);
  return { success: issues.length === 0, issues };
}
