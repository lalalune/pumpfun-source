import React, {
  useState,
  useEffect,
  useRef,
  useContext,
} from "../../packages/frontend/node_modules/react/index.js";
import { createRoot } from "../../packages/frontend/node_modules/react-dom/client.js";
import { c } from "../../packages/frontend/node_modules/react/compiler-runtime.js";
import { createBountyEnrichment } from "../../reconstruction/go-enrichment/client.mjs";
const Context = React.createContext(null),
  events = [];
let root,
  latest,
  serial = 0,
  patchScope,
  patchRows,
  forceRender,
  clock = Date.parse("2026-01-02T00:00:00.000Z");
let oldMints, oldOptions, oldProfiles;
const useScope = () => useContext(Context);
const adapter = createBountyEnrichment({
  memoCache: (n) => {
    events.push({ type: "memo", size: n });
    return c(n);
  },
  useViewerSnapshot: () => {
    const s = useScope();
    events.push({ type: "viewer-port", address: s.viewer });
    return { address: s.viewer };
  },
  useBatchProfiles: (options) => {
    const s = useScope();
    events.push({
      type: "profile-port",
      addresses: [...options.userAddresses],
      sameOptions: options === oldProfiles,
    });
    oldProfiles = options;
    return s.profiles;
  },
  useCoinQuery: (mints, options) => {
    const s = useScope();
    events.push({
      type: "coin-port",
      mints: [...mints],
      options: { ...options },
      sameMints: mints === oldMints,
      sameOptions: options === oldOptions,
    });
    oldMints = mints;
    oldOptions = options;
    return s.coins;
  },
  useIpfsPrefix: () => ({ ipfsPrefix: useScope().prefix }),
  nowMs: () => {
    events.push({ type: "clock-port", clock });
    return clock;
  },
});
const row = {
  taskId: "synthetic-task",
  title: "Synthetic",
  bodyMarkdown: "Summary\n\nDetail",
  criteria: [{ order: 1, text: "deliverable" }],
  rewardLegs: [
    { mintAddress: "reward-token", amountAtomic: "25", decimalsSnapshot: 1 },
  ],
  status: "OPEN",
  payoutMode: "WINNER_BY_WINNER",
  resolution: {
    outcomeType: "REFUND",
    refundClaims: [{ depositor: "CREATOR" }],
  },
  createdAt: "2026-01-01T00:00:00.000Z",
  creatorAddress: "Creator",
  coinAddress: "synthetic-coin",
  counts: { submissionCount: 2 },
};
const scope = {
  viewer: "other",
  coins: { data: undefined, isLoading: true, error: null },
  profiles: { data: undefined, isPending: true },
  prefix: "https://synthetic.invalid/ipfs/",
};
function Observer({ rows, kind }) {
  const value = adapter[kind](rows),
    previous = useRef();
  useEffect(() => {
    const tokenOnly = value instanceof Map,
      tokens = tokenOnly ? value : value.liveTokens;
    latest = {
      kind,
      sameResult: previous.current === value,
      rows: tokenOnly
        ? []
        : value.bounties.map((b) => ({
            id: b.id,
            creator: b.creator,
            token: b.token,
            viewerIsCreator: b.viewerIsCreator,
            refundStatus: b.refundStatus,
            acceptsSubmissions: b.acceptsSubmissions,
            allowsSubmissionMutations: b.allowsSubmissionMutations,
          })),
      tokens: [...tokens].map(([mint, t]) => ({
        mint,
        name: t.liveName,
        symbol: t.liveSymbol,
        marketCap: t.liveMarketCap,
        price: t.livePriceUsd,
      })),
      isEnriching: tokenOnly ? null : value.isEnriching,
    };
    previous.current = value;
    serial++;
    events.push({ type: "commit", serial, state: latest });
  });
  return React.createElement("output", null, "Synthetic enrichment host");
}
function App({ initialRows, initialScope, kind }) {
  const [rows, setRows] = useState(initialRows),
    [current, setScope] = useState(initialScope),
    [, tick] = useState(0);
  patchRows = setRows;
  patchScope = (patch) => setScope((s) => ({ ...s, ...patch }));
  forceRender = () => tick((n) => n + 1);
  return React.createElement(
    Context.Provider,
    { value: current },
    React.createElement(Observer, { rows, kind }),
  );
}
function mount(rows = [row], current = scope, kind = "useEnrichedBounties") {
  latest = null;
  root = createRoot(document.getElementById("root"));
  root.render(
    React.createElement(App, {
      initialRows: rows,
      initialScope: current,
      kind,
    }),
  );
}
window.enrichmentHarness = {
  state: () => structuredClone(latest),
  events: () => structuredClone(events),
  serial: () => serial,
  scope: (patch) => patchScope(patch),
  setRows: (rows) => patchRows(rows),
  tick: () => forceRender(),
  setClock: (value) => {
    clock = value;
  },
  initialRow: () => structuredClone(row),
  unmount: () => root.unmount(),
  mountTokens: () => {
    root.unmount();
    mount(
      [row],
      { ...scope, coins: { data: [], isLoading: true } },
      "useBountyTokens",
    );
  },
};
mount();
