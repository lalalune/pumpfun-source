// Complete maintained adaptation of original application factory 646908.
// Captured factories are parsed only; no original runtime or network is installed.
export function createChainIdentity() {
  let t = [
      "solana",
      "base",
      "bsc",
      "ethereum",
      "monad",
      "robinhood",
      "hyperevm",
      "ink",
      "arc",
      "megaeth",
      "xlayer",
      "polygon",
      "arbitrum",
    ],
    r = "starknet",
    n = "near",
    o = [...t, "ton", r, n],
    i = "ton:-239",
    s = /^EQ[A-Za-z0-9_-]{46}$/,
    a = "starknet:SN_MAIN",
    l = /^0x[0-9a-f]{64}$/,
    u = /^0x[0-9a-fA-F]{1,64}$/,
    c = (e) => {
      if ("string" != typeof e) return null;
      let t = e.trim();
      if (!u.test(t)) return null;
      let r = t.slice(2).toLowerCase().padStart(64, "0");
      return "0" !== r[0] || r[1] > "7" ? null : `0x${r}`;
    },
    d = "near:mainnet",
    f = /^(?:(?:[a-z\d]+[-_])*[a-z\d]+\.)+(?:[a-z\d]+[-_])*[a-z\d]+$/,
    p = /^[0-9a-f]{64}$/,
    h = /^(?!0x[0-9a-f]*$)(?=.{2,31}$)(?:[a-z\d]+[-_])*[a-z\d]+$/,
    g =
      /^(?=.{2,64}$)(?:(?:[a-z\d]+[-_])*[a-z\d]+\.)*(?:[a-z\d]+[-_])*[a-z\d]+$/,
    m = {
      ethereum: "eip155:1",
      base: "eip155:8453",
      bsc: "eip155:56",
      monad: "eip155:143",
      robinhood: "eip155:4663",
      hyperevm: "eip155:999",
      ink: "eip155:57073",
      arc: "eip155:5042",
      megaeth: "eip155:4326",
      xlayer: "eip155:196",
      polygon: "eip155:137",
      arbitrum: "eip155:42161",
    },
    w = Object.fromEntries(Object.entries(m).map(([e, t]) => [t.slice(7), e]));
  return {
    H: m,
    c: t,
    d: d,
    Q: n,
    W: a,
    h: r,
    J: i,
    z: "ton",
    l: o,
    Y: c,
    U: function (e) {
      if ("string" != typeof e) return null;
      let t = e.trim();
      return t ? (w[t.startsWith("eip155:") ? t.slice(7) : t] ?? null) : null;
    },
    C: (e) => e === i || e === a || e === d,
    n: (e) => g.test(e),
    B: (e) => e === d,
    a: (e) => e.chain_id === d,
    R: (e) =>
      "string" == typeof e &&
      e.length >= 2 &&
      e.length <= 64 &&
      (f.test(e) || h.test(e) || p.test(e)),
    V: (e) => "string" == typeof e && l.test(e),
    _: (e) => e === a,
    X: (e) => e.chain_id === a,
    M: (e) =>
      "string" == typeof e && !/^0x[0-9a-fA-F]{40}$/.test(e) && null !== c(e),
    L: (e) => e === i,
    e: (e) => e.chain_id === i,
    u: (e) => "string" == typeof e && s.test(e),
    f: (e) => (e.length > 12 ? `${e.slice(0, 6)}…${e.slice(-4)}` : e),
  };
}
