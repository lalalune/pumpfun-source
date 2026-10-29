// Reconstruction of the complete captured179736 client boundary. The host
// supplies transport/timer/query capabilities; import performs no request.
export const verifiedProfileKey = (identifier) => ['user-verified', identifier];

export function requireVerifiedProfilesOk(_request, _options, response) {
  if (!response.ok) throw Error('Failed to fetch verified profiles');
}

export function createVerifiedProfileReader({ createClient, schedule, serverUrl, memo, useQuery }) {
  if (typeof createClient !== 'function' || typeof schedule !== 'function' || typeof serverUrl !== 'string') {
    throw new TypeError('Explicit client, timer and server URL capabilities are required');
  }
  const resolvers = new Map();
  async function readBatch(origin, identifiers) {
    const ids = [...new Set(identifiers)].filter(Boolean);
    return ids.length === 0 ? {} : createClient({ clientServerUrl: origin })('POST /profiles/verified', {
      body: { ids },
      credentials: 'same-origin',
      hooks: { afterResponse: [requireVerifiedProfilesOk] },
    });
  }
  async function readOrEmpty(origin, identifiers) {
    try { return await readBatch(origin, identifiers); }
    catch { return {}; }
  }
  function resolverFor(origin) {
    let resolver = resolvers.get(origin);
    if (!resolver) {
      let pending = new Map();
      let timer = null;
      const flush = () => {
        timer = null;
        const current = pending;
        pending = new Map();
        const identifiers = [...current.keys()];
        for (let offset = 0; offset < identifiers.length; offset += 100) {
          const batch = identifiers.slice(offset, offset + 100);
          readOrEmpty(origin, batch).then((response) => {
            for (const identifier of batch) {
              const value = response[identifier] ?? false;
              for (const waiter of current.get(identifier) ?? []) waiter.resolve(value);
            }
          }).catch(() => {
            for (const identifier of batch) {
              for (const waiter of current.get(identifier) ?? []) waiter.resolve(false);
            }
          });
        }
      };
      resolver = {
        fetch: (identifier) => new Promise((resolve) => {
          const waiters = pending.get(identifier) ?? [];
          waiters.push({ resolve });
          pending.set(identifier, waiters);
          if (timer === null) timer = schedule(flush, 50);
        }),
      };
      resolvers.set(origin, resolver);
    }
    return resolver;
  }
  function useVerifiedProfile(identifier, options) {
    if (typeof memo !== 'function' || typeof useQuery !== 'function') {
      throw new TypeError('Explicit compiler memo and query-hook ports are required');
    }
    const cache = memo(10);
    let input;
    if (cache[0] !== options) {
      input = options === undefined ? {} : options;
      cache[0] = options;
      cache[1] = input;
    } else input = cache[1];
    const { enabled } = input;
    const keyIdentifier = identifier ?? '';
    let key;
    if (cache[2] !== keyIdentifier) {
      key = verifiedProfileKey(keyIdentifier);
      cache[2] = keyIdentifier;
      cache[3] = key;
    } else key = cache[3];
    let queryFn;
    if (cache[4] !== identifier) {
      queryFn = () => resolverFor(serverUrl).fetch(identifier ?? '');
      cache[4] = identifier;
      cache[5] = queryFn;
    } else queryFn = cache[5];
    const queryEnabled = (enabled === undefined || enabled) && !!identifier;
    let queryOptions;
    if (cache[6] !== key || cache[7] !== queryFn || cache[8] !== queryEnabled) {
      queryOptions = { queryKey: key, queryFn, enabled: queryEnabled, staleTime: 1800000, retry: false };
      cache[6] = key;
      cache[7] = queryFn;
      cache[8] = queryEnabled;
      cache[9] = queryOptions;
    } else queryOptions = cache[9];
    const { data } = useQuery(queryOptions);
    return data === true;
  }
  return { readBatch, readOrEmpty, resolverFor, useVerifiedProfile };
}

// Actual154121 identity consumer: a supplied user ID wins by nullish choice,
// including an empty string; disabled lookup passes undefined, not the address.
export function identityVerificationSubject({ address, user, enabled }) {
  return (enabled === undefined || enabled) ? user?.userId ?? address : undefined;
}

// Only the exact address predicates used by the captured693124/107240 lookup
// gate are reproduced here. They are display policy, not wallet validation,
// ownership, chain support or authorization.
const nearAccount = /^(?:(?:[a-z\d]+[-_])*[a-z\d]+\.)+(?:[a-z\d]+[-_])*[a-z\d]+$/;
const nearImplicit = /^[0-9a-f]{64}$/;
const nearShort = /^(?!0x[0-9a-f]*$)(?=.{2,31}$)(?:[a-z\d]+[-_])*[a-z\d]+$/;
function explicitNearIdentity(value) {
  return typeof value === 'string' && value.length >= 2 && value.length <= 64 &&
    (nearAccount.test(value) || nearShort.test(value) || nearImplicit.test(value)) &&
    (value.includes('.') || nearImplicit.test(value));
}
function suppressRendererLookup({ chain, userId, address }) {
  return chain === 'near:mainnet' && !userId && !!address && !explicitNearIdentity(address) &&
    !(typeof address === 'string' && /^0x[0-9a-fA-F]{40}$/.test(address));
}
export function rendererVerificationSubject({ verified, chain, userId, address }) {
  const mode = verified !== undefined && verified;
  return mode !== 'lookup' || suppressRendererLookup({ chain, userId, address })
    ? null : userId ?? address ?? null;
}
export function rendererVerificationValue(verified, lookupResult) {
  const mode = verified !== undefined && verified;
  return mode === 'lookup' ? lookupResult : mode;
}
