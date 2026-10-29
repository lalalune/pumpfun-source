// Captured 359516/961415 policies: the query provider receives these intervals.
// This native scheduling port does not implement that provider's cache/staleTime.
export function competitionRefreshInterval(
  category: string,
  competitionId: string | null,
): 60_000 | 15_000 | false {
  return category === "competitions"
    ? competitionId
      ? 15_000
      : 60_000
    : false;
}

type Read = (options: { signal: AbortSignal }) => Promise<void>;

type Browser = {
  document: Pick<
    Document,
    "visibilityState" | "hasFocus" | "addEventListener" | "removeEventListener"
  >;
  window: Pick<Window, "addEventListener" | "removeEventListener">;
  setTimeout: (callback: () => void, delay: number) => unknown;
  clearTimeout: (id: unknown) => void;
};

// Both physical 85324 variants use this same snapshot, including the AND.
export function competitionIsForeground(document: Browser["document"]) {
  return "visible" === document.visibilityState && document.hasFocus();
}

/**
 * Initial reads remain unconditional. Recurring native reads wait for settlement
 * before another full interval; this avoids overlap without guessing cache or
 * retry internals. The caller owns response admission and error presentation.
 */
export function startCompetitionReads(
  read: Read,
  interval: 60_000 | 15_000 | false,
  browser: Browser = {
    document,
    window,
    setTimeout: (callback, delay) => window.setTimeout(callback, delay),
    clearTimeout: (id) => window.clearTimeout(id as number),
  },
) {
  let stopped = false;
  let running = false;
  let timeout: unknown;
  let active: AbortController | undefined;
  let foreground = interval ? competitionIsForeground(browser.document) : false;

  function unschedule() {
    if (timeout !== undefined) browser.clearTimeout(timeout);
    timeout = undefined;
  }
  function schedule() {
    unschedule();
    if (!stopped && !running && interval && foreground) {
      timeout = browser.setTimeout(() => {
        timeout = undefined;
        void run();
      }, interval);
    }
  }
  async function run() {
    if (stopped || running) return;
    running = true;
    const controller = new AbortController();
    active = controller;
    try {
      await read({ signal: controller.signal });
    } finally {
      active = undefined;
      running = false;
      schedule();
    }
  }
  function foregroundChanged() {
    const next = competitionIsForeground(browser.document);
    if (next === foreground) return;
    foreground = next;
    schedule();
  }
  if (interval) {
    browser.document.addEventListener("visibilitychange", foregroundChanged);
    browser.window.addEventListener("focus", foregroundChanged);
    browser.window.addEventListener("blur", foregroundChanged);
  }
  void run();
  return () => {
    stopped = true;
    unschedule();
    active?.abort();
    if (interval) {
      browser.document.removeEventListener(
        "visibilitychange",
        foregroundChanged,
      );
      browser.window.removeEventListener("focus", foregroundChanged);
      browser.window.removeEventListener("blur", foregroundChanged);
    }
  };
}
