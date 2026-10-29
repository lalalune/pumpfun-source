"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useSidebar } from "@/components/ui/sidebar";
import { SearchMobileIcon } from "../captured-icons";
import { LocalUserSearch } from "./LocalUserSearch";
import { onOpenSearch } from "./search-events";
import { createSearchShortcutHandler } from "./search-shortcuts.mjs";

/**
 * The shell's search entry point (the captured search box and ⌘K hint open it).
 * The local user list reads validated synthetic profiles; live market results
 * remain unavailable, so submitting hands the query to Explore. A native <dialog> provides the modal focus
 * handling and Escape-to-close.
 */
export function SearchDialog() {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const currentQuery = params.get("q") ?? "";
  const [query, setQuery] = useState(currentQuery);
  const pendingClear = useRef(false);
  const [open, setOpen] = useState(false);
  const { closeMobile } = useSidebar();
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    // Observe the native state without changing the source-bound shortcut effect.
    const syncOpen = () => setOpen(dialog.open);
    const observer = new MutationObserver(syncOpen);
    observer.observe(dialog, { attributes: true, attributeFilter: ["open"] });
    syncOpen();
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    // Clear already updated the input; its delayed URL commit must not erase
    // text entered since that click. Other navigation still follows the URL.
    const completedClear = pendingClear.current && currentQuery === "";
    pendingClear.current = false;
    if (!completedClear) setQuery(currentQuery);
  }, [currentQuery]);

  useEffect(() => {
    const open = () => {
      closeMobile();
      const dialog = dialogRef.current;
      if (dialog && !dialog.open) dialog.showModal();
    };
    const toggle = () => {
      const dialog = dialogRef.current;
      if (dialog?.open) {
        dialog.close();
        setQuery("");
      } else {
        open();
      }
    };
    const onKeyDown = createSearchShortcutHandler([
      { keys: ["Meta", "k"], callback: toggle },
      { keys: ["Control", "k"], callback: toggle },
      { keys: ["/"], callback: toggle },
    ]);
    const onPopState = () => {
      pendingClear.current = false;
    };
    window.addEventListener("popstate", onPopState);
    window.addEventListener("keydown", onKeyDown);
    const stopListening = onOpenSearch(open);
    return () => {
      window.removeEventListener("popstate", onPopState);
      window.removeEventListener("keydown", onKeyDown);
      stopListening();
    };
  }, [closeMobile]);

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    pendingClear.current = false;
    const normalized = query.trim();
    dialogRef.current?.close();
    router.push(
      normalized
        ? `/explore?${new URLSearchParams({ q: normalized })}`
        : "/explore",
    );
  }

  return (
    <dialog
      ref={dialogRef}
      aria-label="Search for coins and users"
      onKeyDown={(event) => {
        if (event.key !== "Escape") return;
        // A populated search input otherwise clears itself before native
        // dialog cancellation. The modal owns this key and preserves the draft.
        event.preventDefault();
        event.stopPropagation();
        event.currentTarget.close();
      }}
      className="mx-auto mt-[12vh] w-[min(560px,calc(100vw-32px))] overflow-hidden rounded-xl border border-border-tertiary bg-bg-secondary p-0 text-text-primary shadow-lg backdrop:bg-black/60"
    >
      <form
        onSubmit={onSubmit}
        role="search"
        className="flex items-center gap-2 px-3"
      >
        <SearchMobileIcon className="size-4 shrink-0 text-text-quaternary" />
        <input
          id="global-search"
          name="q"
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          autoFocus
          autoComplete="off"
          aria-label="Search for coins and users"
          placeholder="Search for coins and users..."
          className="h-12 w-full bg-transparent text-[14px] outline-none placeholder:text-text-quaternary"
        />
        {query ? (
          <button
            type="button"
            aria-label="Clear search"
            className="px-2 py-3 text-sm"
            onClick={() => {
              setQuery("");
              if (pathname === "/explore" && currentQuery) {
                pendingClear.current = true;
                router.push("/explore");
              }
            }}
          >
            ×
          </button>
        ) : null}
        <button
          type="submit"
          className="rounded-md bg-bg-accent px-3 py-2 text-sm text-text-on-accent"
        >
          Search
        </button>
        <kbd className="h-5 shrink-0 rounded-sm bg-bg-quaternary px-1.5 text-xs leading-5 text-text-quaternary">
          Esc
        </kbd>
      </form>
      <LocalUserSearch
        query={query}
        open={open}
        onNavigate={() => dialogRef.current?.close()}
      />
      <p className="border-t border-border-secondary px-3 py-2 text-xs text-text-tertiary">
        Live results need the market-discovery API, which is not implemented
        locally. Press Enter to search on Explore.
      </p>
    </dialog>
  );
}
