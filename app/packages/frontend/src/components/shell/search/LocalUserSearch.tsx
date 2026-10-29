"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  createUserSearchQuery,
  type UserSearchRequestOptions,
} from "../../../../../../reconstruction/user-search/query.mjs";
import {
  isLocalUserSearchRows,
  type LocalUserSearchRow,
} from "@/lib/local-user-search-data";
import styles from "./local-user-search.module.css";

type State = {
  term: string;
  status: "loading" | "ready" | "error";
  rows: LocalUserSearchRow[];
};

async function readLocalUsers(
  operation: string,
  options: UserSearchRequestOptions,
): Promise<LocalUserSearchRow[]> {
  if (
    operation !== "GET /users/search-v2" ||
    options.query.offset !== 0 ||
    options.query.limit !== 20 ||
    options.query.includeLabelledWallets !== true
  )
    throw new Error("Unsupported local search request.");
  const response = await fetch(
    `/api/local-users/search?${new URLSearchParams({ q: options.query.searchTerm ?? "" })}`,
    {
      signal: options.signal,
      credentials: options.credentials,
      headers: options.headers,
      cache: "no-store",
    },
  );
  for (const hook of options.hooks.afterResponse)
    hook(undefined, options, response);
  const rows: unknown = await response.json();
  if (!isLocalUserSearchRows(rows))
    throw new Error("Invalid local profile response.");
  return rows;
}

export function LocalUserSearch({
  query,
  open,
  onNavigate,
}: {
  query: string;
  open: boolean;
  onNavigate: () => void;
}) {
  const term = query.trim();
  const [state, setState] = useState<State>({
    term: "",
    status: "loading",
    rows: [],
  });
  useEffect(() => {
    const snapshot = createUserSearchQuery<LocalUserSearchRow>(
      { searchTerm: query, debouncedTerm: term, enabled: open },
      () => readLocalUsers,
    );
    if (!snapshot.queryOptions.enabled || term.length > 200) return;
    const controller = new AbortController();
    let active = true;
    setState({ term, status: "loading", rows: [] });
    const timer = setTimeout(async () => {
      try {
        const page = await snapshot.queryOptions.queryFn({
          pageParam: snapshot.queryOptions.initialPageParam,
          signal: controller.signal,
        });
        if (active && !controller.signal.aborted)
          setState({
            term,
            status: "ready",
            rows: snapshot.queryOptions.select({ pages: [page] }),
          });
      } catch {
        if (active && !controller.signal.aborted)
          setState({ term, status: "error", rows: [] });
      }
    }, snapshot.debounceMs);
    return () => {
      active = false;
      clearTimeout(timer);
      controller.abort();
    };
  }, [term, open]);

  if (!open) return null;
  const current = state.term === term;
  return (
    <section className={styles.results} aria-label="Local profile search">
      <h2>Local synthetic profiles</h2>
      <p className={styles.note}>
        Search the five local examples. These are not real Pump.fun users.
      </p>
      {term.length < 2 ? (
        <p role="status">
          Enter at least two characters to search local profiles.
        </p>
      ) : term.length > 200 ? (
        <p role="status">Local profile search supports up to 200 characters.</p>
      ) : !current || state.status === "loading" ? (
        <p role="status">Searching local profiles…</p>
      ) : state.status === "error" ? (
        <p role="status">
          Local profiles are unavailable. Change the search to try again.
        </p>
      ) : state.rows.length === 0 ? (
        <p role="status">No matching local profiles.</p>
      ) : (
        <ul>
          {state.rows.map((row) => (
            <li key={row.identifier}>
              <Link
                href={`/profile/${encodeURIComponent(row.identifier)}`}
                prefetch={false}
                onClick={onNavigate}
              >
                {row.displayName}
              </Link>
              <span>
                Local {row.kind === "group" ? "group" : "profile"}
                {row.banned ? " · Marked banned" : ""}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
