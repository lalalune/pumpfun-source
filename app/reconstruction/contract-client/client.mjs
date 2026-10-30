// Independent executable reconstruction of the whole 898661 request compiler.
// The existing HTTP-error decoder keeps its original attribution/class identity.
import { normalizeContractHttpError } from '../contract-http-errors/decode.mjs';

export function createContractClient(transport, {
  contracts, routeErrorSchema, contractErrorBody,
  FormDataType = globalThis.FormData, BlobType = globalThis.Blob,
}) {
  const filesFor = route => contracts[route]?.multipart
    ? (contracts[route].multipartFiles ?? ['image']) : undefined;
  const descriptor = value => typeof value === 'object' && value !== null &&
    ['uri', 'name', 'type'].every(key => typeof value[key] === 'string');
  return async (route, options = {}) => {
    const [method, template] = route.split(' ', 2);
    const { params, query, body, ...overrides } = options;
    let searchParams;
    if (query) {
      const shape = contracts[route]?.query?.shape;
      searchParams = {};
      for (const [name, value] of Object.entries(query)) {
        if (value === undefined) continue;
        if (Array.isArray(value)) {
          const items = value.map(String);
          if (items.length === 0) {
            if (shape?.[name]?.safeParse(undefined).success) continue;
            throw TypeError(`${route}: query.${name} requires at least one item`);
          }
          const comma = items.find(item => item.includes(','));
          if (comma !== undefined) throw TypeError(`${route}: query.${name} item ${JSON.stringify(comma)} contains a comma, which is the array separator`);
          searchParams[name] = items.join(',');
        } else searchParams[name] = String(value);
      }
    }
    let multipart;
    if (typeof body === 'object' && body !== null && filesFor(route)) {
      if (body instanceof FormDataType) throw TypeError(`${route}: a hand-built FormData is not accepted (contract 0.57.0, TASK-5101); pass the JSON fields and the file parts as one object`);
      if (filesFor(route).some(name => body[name] != null)) {
        multipart = new FormDataType();
        const fileNames = new Set(filesFor(route));
        const native = typeof multipart.getParts === 'function';
        for (const [name, value] of Object.entries(body)) {
          if (value === undefined) continue;
          if (fileNames.has(name)) {
            if (value === null) continue;
            if (native ? descriptor(value) : value instanceof BlobType) multipart.append(name, value);
            else throw TypeError(value instanceof BlobType
              ? `${route}: ${name} is a Blob, which React Native's FormData cannot send; pass a { uri, name, type } descriptor`
              : descriptor(value)
                ? `${route}: ${name} is a { uri, name, type } descriptor, which only React Native's FormData can send; pass a Blob`
                : `${route}: ${name} is neither a Blob nor a { uri, name, type } descriptor`);
          } else multipart.append(name, typeof value === 'object' ? JSON.stringify(value) : String(value));
        }
      }
    }
    // Query/multipart construction occurs before this catch in the source.
    try {
      const relative = template.slice(1).replace(/\{(\w+)\}/g,
        (_match, name) => encodeURIComponent(String((params === undefined ? {} : params)[name])));
      return await transport(relative, {
        method: method.toLowerCase(),
        ...(searchParams && { searchParams }),
        ...(multipart ? { body: multipart } : body !== undefined && { json: body }),
        ...overrides,
      }).json();
    } catch (error) {
      throw (await normalizeContractHttpError(route, error,
        { contracts, routeErrorSchema, contractErrorBody })) ?? error;
    }
  };
}
