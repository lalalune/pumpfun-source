import React, { createContext, useContext, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { createCompetitionViewerComponents } from "../../packages/frontend/src/components/leaderboard/viewer/CompetitionViewerDisplay.tsx";
import { translateViewer } from "./competition-viewer-data.mjs";
const Price = createContext(undefined),
  query = new URL(location.href).searchParams;
window.__price = { mounts: 0, unmounts: 0, active: 0 };
window.__avatars = [];
const { ViewerConsumer } = createCompetitionViewerComponents({
  squadVariant: query.get("squad"),
  imageVariant: query.get("image"),
  useTranslation: () => ({ t: translateViewer }),
  useSolPrice: (options) => {
    if (Object.keys(options).length) throw Error("unexpected price options");
    const data = useContext(Price);
    useEffect(() => {
      window.__price.mounts++;
      window.__price.active++;
      return () => {
        window.__price.unmounts++;
        window.__price.active--;
      };
    }, []);
    return { data };
  },
  Avatar: (props) => {
    window.__avatars.push({ ...props });
    return React.createElement(
      "span",
      {
        className: props.className,
        "data-avatar": props.address,
        style: {
          width: 40,
          height: 40,
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#303035",
        },
        "aria-label": "Synthetic avatar capability",
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
});
function App() {
  const [entry, setEntry] = useState(null),
    [price, setPrice] = useState(undefined),
    [error, setError] = useState(false);
  async function load(kind) {
    setEntry(null);
    setError(false);
    const r = await fetch("/fixture/" + kind);
    if (!r.ok) {
      setError(true);
      return;
    }
    setEntry(await r.json());
  }
  return React.createElement(
    "main",
    { style: { maxWidth: 700, margin: "0 auto", padding: 16 } },
    React.createElement(
      "h1",
      {},
      "Original competition viewer card — synthetic host",
    ),
    React.createElement(
      "p",
      {},
      "Supplied entry and price; local Avatar/Link/translation capabilities. No account lookup or financial calculation service.",
    ),
    React.createElement(
      "div",
      {
        style: { display: "flex", gap: 12, flexWrap: "wrap", margin: "12px 0" },
      },
      React.createElement(
        "button",
        { id: "load", onClick: () => load("valid") },
        "Load viewer entry",
      ),
      React.createElement(
        "button",
        { id: "price", onClick: () => setPrice(6000) },
        "Supply price",
      ),
      React.createElement(
        "button",
        { id: "zero", onClick: () => setPrice(0) },
        "Zero price",
      ),
      React.createElement(
        "button",
        {
          id: "update",
          disabled: !entry,
          onClick: () =>
            setEntry((e) => ({
              ...e,
              username:
                "Updated viewer with a very long supplied name that must truncate on mobile",
              rank: 0,
              pnlUsd: -0.5,
              realizedPnlUsd: 12,
              unrealizedPnlUsd: -0.004,
            })),
        },
        "Update supplied entry",
      ),
      React.createElement(
        "button",
        {
          id: "group",
          disabled: !entry,
          onClick: () =>
            setEntry((e) => ({
              ...e,
              kind: "group",
              username: null,
              participantId: "group/fixture",
              walletAddress: null,
            })),
        },
        "Supply squad",
      ),
      React.createElement(
        "button",
        { id: "invalid", onClick: () => load("invalid") },
        "Reject fixture",
      ),
      React.createElement(
        "button",
        {
          id: "clear",
          onClick: () => {
            setEntry(null);
            setError(false);
          },
        },
        "Clear",
      ),
    ),
    error
      ? React.createElement("p", { role: "alert" }, "Fixture admission failed")
      : null,
    React.createElement(
      Price.Provider,
      { value: price },
      entry
        ? React.createElement(ViewerConsumer, { row: { entry } })
        : React.createElement("p", { id: "empty" }, "No viewer entry supplied"),
    ),
  );
}
createRoot(document.getElementById("root")).render(React.createElement(App));
