import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import { createCompetitionEntryComponents } from "../../packages/frontend/src/components/leaderboard/entry/CompetitionEntryDisplay.tsx";
import { syntheticTranslate } from "./competition-entry-data.mjs";
const query = new URL(location.href).searchParams;
window.__avatarProps = [];
const { EntryConsumer } = createCompetitionEntryComponents({
  squadVariant: query.get("squad"),
  imageVariant: query.get("image"),
  useTranslation: () => ({ t: syntheticTranslate }),
  Avatar: (props) => {
    window.__avatarProps.push({ ...props });
    return React.createElement(
      "span",
      {
        className: props.className,
        "data-avatar": props.address,
        style: {
          display: "inline-flex",
          width: 40,
          height: 40,
          alignItems: "center",
          justifyContent: "center",
          background: "#303035",
        },
        "aria-label": "Synthetic avatar capability",
      },
      "A",
    );
  },
  Link: ({ href, prefetch, children, ...props }) =>
    React.createElement(
      "a",
      {
        ...props,
        href,
        "data-prefetch": String(prefetch),
        onClick: (event) => event.preventDefault(),
      },
      children,
    ),
});
function App() {
  const [data, setData] = useState(null),
    [error, setError] = useState(false);
  async function load(kind) {
    setData(null);
    setError(false);
    const result = await fetch("/fixture/" + kind);
    if (!result.ok) {
      setError(true);
      return;
    }
    setData(await result.json());
  }
  function update() {
    setData((data) =>
      data.map((row, i) =>
        i
          ? row
          : {
              ...row,
              entry: {
                ...row.entry,
                username: "UpdatedFixture",
                pnlUsd: -0.5,
                verifiedBadgeVisible: false,
                profileImageUrl: "  https://fixture.invalid/updated.png  ",
              },
            },
      ),
    );
  }
  return React.createElement(
    "main",
    { style: { maxWidth: 700, margin: "0 auto", padding: 16 } },
    React.createElement(
      "h1",
      {},
      "Original competition entry — synthetic host",
    ),
    React.createElement(
      "p",
      {},
      "Supplied entries and local Link/Avatar capabilities; no profile lookup, ranking or PnL calculation.",
    ),
    React.createElement(
      "div",
      {
        style: { display: "flex", gap: 12, flexWrap: "wrap", margin: "12px 0" },
      },
      React.createElement(
        "button",
        { id: "load", onClick: () => load("valid") },
        "Load entries",
      ),
      React.createElement(
        "button",
        { id: "update", disabled: !data, onClick: update },
        "Update supplied props",
      ),
      React.createElement(
        "button",
        { id: "invalid", onClick: () => load("invalid") },
        "Reject invalid fixture",
      ),
      React.createElement(
        "button",
        {
          id: "clear",
          onClick: () => {
            setData(null);
            setError(false);
          },
        },
        "Clear",
      ),
    ),
    error
      ? React.createElement("p", { role: "alert" }, "Fixture admission failed")
      : null,
    data
      ? React.createElement(
          "section",
          {
            id: "entries",
            className: "rounded-xl border border-border-primary",
          },
          ...data.map((row) =>
            React.createElement(EntryConsumer, { key: row.entry.entryId, row }),
          ),
        )
      : React.createElement("p", { id: "empty" }, "No entry props supplied"),
  );
}
createRoot(document.getElementById("root")).render(React.createElement(App));
