import React, {
  useCallback,
  useEffect,
  useState,
  useSyncExternalStore,
} from "react";
import { createRoot } from "react-dom/client";
import { createCompetitionBoardComponents } from "../../packages/frontend/src/components/leaderboard/board/CompetitionBoardDisplay.tsx";
import { useMemoCache } from "../../packages/frontend/src/components/leaderboard/original-prize-formats.mjs";
import { createCompetitionClient } from "../../reconstruction/competition-client/client.mjs";
import { createCompetitionFetchTransport } from "../../reconstruction/competition-client/fetch-transport.mjs";
import { translateBoard } from "./competition-board-data.mjs";
const params = new URL(location.href).searchParams,
  scenario = params.get("scenario") ?? "normal";
window.__board = {
  queryOptions: [],
  queries: 0,
  aborts: 0,
  foregroundActive: 0,
  hero: [],
  highlights: [],
  rules: [],
  avatars: [],
};
// This small local port executes real recovered queryFns, not original query/cache policy.
// staleTime/refetchInterval are recorded, not emulated; there is no polling/retry cache.
function useLocalQuery(options) {
  const key = JSON.stringify(options.queryKey),
    enabled = options.enabled !== false;
  const [state, setState] = useState({
      key: null,
      data: undefined,
      isLoading: false,
      isError: false,
    }),
    [version, bump] = useState(0);
  const refetch = useCallback(() => bump((v) => v + 1), []);
  useEffect(() => {
    if (!enabled) return;
    let active = true;
    const controller = new AbortController();
    window.__board.queries++;
    window.__board.queryOptions.push({
      key: options.queryKey,
      staleTime: options.staleTime,
      refetchInterval: options.refetchInterval,
    });
    setState({ key, data: undefined, isLoading: true, isError: false });
    Promise.resolve()
      .then(() => options.queryFn({ signal: controller.signal }))
      .then(
        (data) => {
          if (active) setState({ key, data, isLoading: false, isError: false });
        },
        (error) => {
          if (active && !controller.signal.aborted)
            setState({ key, data: undefined, isLoading: false, isError: true });
        },
      );
    return () => {
      active = false;
      controller.abort();
      window.__board.aborts++;
    };
  }, [key, enabled, options.queryFn, version]);
  return {
    ...(state.key === key
      ? state
      : { data: undefined, isLoading: enabled, isError: false }),
    isRefetching: false,
    refetch,
  };
}
function browserPort(target) {
  return {
    get visibilityState() {
      return document.visibilityState;
    },
    hasFocus: () => document.hasFocus(),
    addEventListener: (name, cb) => {
      window.__board.foregroundActive++;
      target.addEventListener(name, cb);
    },
    removeEventListener: (name, cb) => {
      window.__board.foregroundActive--;
      target.removeEventListener(name, cb);
    },
  };
}
const transport = createCompetitionFetchTransport({
  baseUrl: location.origin + "/fixture/" + scenario,
  fetch: (r) => fetch(r),
});
const client = createCompetitionClient({
  foregroundVariant: params.get("foreground"),
  document: browserPort(document),
  window: browserPort(window),
  useSyncExternalStore,
  useMemoCache,
  useQuery: useLocalQuery,
  useClientServerContract: () => transport,
  useViewerKey: () => "unverified-synthetic-ui-key",
});
const { PersonConsumer, GroupConsumer } = createCompetitionBoardComponents({
  squadVariant: params.get("squad"),
  imageVariant: params.get("image"),
  numberVariant: params.get("number"),
  client,
  useTranslation: () => ({ t: translateBoard, i18n: { language: "en" } }),
  useSolPrice: () => ({ data: 100 }),
  useReducedMotion: () => true,
  Avatar: (p) => {
    window.__board.avatars.push(p);
    return React.createElement(
      "span",
      {
        className: p.className,
        "data-avatar": p.address,
        style: {
          width: 40,
          height: 40,
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#303035",
        },
      },
      "A",
    );
  },
  Link: ({ href, prefetch, children, ...p }) =>
    React.createElement(
      "a",
      {
        ...p,
        href,
        "data-prefetch": String(prefetch),
        onClick: (e) => e.preventDefault(),
      },
      children,
    ),
  Hero: (p) => {
    window.__board.hero.push({
      ...p,
      topControl: !!p.topControl,
      onRetry: undefined,
      onOpenRules: undefined,
    });
    return React.createElement(
      "section",
      {
        "data-testid": "host-hero",
        "aria-busy": p.isLoading,
        style: { border: "1px dashed #777", padding: 12, borderRadius: 12 },
      },
      React.createElement(
        "h2",
        {},
        p.competition?.title ??
          (p.isError
            ? "fixture-list-error"
            : p.isLoading
              ? "fixture-list-loading"
              : "fixture-no-competition"),
      ),
      p.topControl,
      p.isError
        ? React.createElement(
            "button",
            { id: "retry-list", onClick: p.onRetry },
            "Retry fixture list",
          )
        : null,
      p.competition
        ? React.createElement(
            "button",
            { id: "open-rules", onClick: p.onOpenRules },
            "Open fixture rules port",
          )
        : null,
    );
  },
  Highlights: (p) => {
    window.__board.highlights.push(p);
    return React.createElement(
      "aside",
      { "data-testid": "host-highlights" },
      "Explicit highlights port: " + p.entries.length + " supplied entries",
    );
  },
  Rules: (p) => {
    window.__board.rules.push({ open: p.open, id: p.competition.id });
    return p.open
      ? React.createElement(
          "div",
          {
            role: "dialog",
            "aria-label": "Fixture rules port",
            style: { border: "1px dashed #777", padding: 12 },
          },
          "Explicit rules port",
          React.createElement(
            "button",
            { id: "close-rules", onClick: () => p.onOpenChange(false) },
            "Close",
          ),
        )
      : null;
  },
  Card: ({ ariaLabel, testId, children }) =>
    React.createElement(
      "section",
      {
        "aria-label": ariaLabel,
        "data-testid": testId,
        className:
          "overflow-hidden rounded-3xl border border-border-tertiary bg-bg-primary",
      },
      children,
    ),
});
function App() {
  const [mounted, setMounted] = useState(false),
    [group, setGroup] = useState(false);
  return React.createElement(
    "main",
    { style: { maxWidth: 700, margin: "0 auto", padding: 16 } },
    React.createElement(
      "h1",
      {},
      "Original competition-board coordinator — explicit local ports",
    ),
    React.createElement(
      "p",
      {},
      "Captured query hooks, coordinator, rows, viewer and prizes. Hero/highlights/rules/motion/query-runtime ports are local; no native media/auth/API parity.",
    ),
    React.createElement(
      "div",
      { style: { display: "flex", gap: 16, margin: "12px 0" } },
      React.createElement(
        "button",
        { id: "mount", onClick: () => setMounted((v) => !v) },
        mounted ? "Unmount board" : "Mount board",
      ),
      React.createElement(
        "button",
        { id: "kind", onClick: () => setGroup((v) => !v) },
        group ? "Person board" : "Squad board",
      ),
    ),
    mounted
      ? React.createElement(group ? GroupConsumer : PersonConsumer, {
          periodControl: React.createElement(
            "span",
            {},
            "Explicit period-control port",
          ),
          periodControlTopPx: 10,
        })
      : React.createElement("p", { id: "unmounted" }, "Board unmounted"),
  );
}
createRoot(document.getElementById("root")).render(React.createElement(App));
