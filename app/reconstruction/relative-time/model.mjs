// Independent reconstruction of original668487,632817 and used633311/890088
// behavior. Captured modules remain inert evidence and are never executed.
export function createServerClock({
  now = () => Date.now(),
  fetch: fetchTime = (...args) => globalThis.fetch(...args),
  timeoutSignal = (milliseconds) => AbortSignal.timeout(milliseconds),
} = {}) {
  let offset = 0;
  let synchronized = false;
  let nextAttempt = 0;
  let inFlight = null;
  async function sample() {
    const started = now();
    try {
      const response = await fetchTime("/api/server-time", {
        cache: "no-store",
        credentials: "omit",
        signal: timeoutSignal(5000),
      });
      if (!response.ok) throw Error(`server-time ${response.status}`);
      const body = await response.json();
      let serverNow = null;
      if (typeof body === "object" && body !== null) {
        const { nowMs } = body;
        if (typeof nowMs === "number" && Number.isFinite(nowMs))
          serverNow = nowMs;
      }
      if (serverNow === null) throw Error("server-time malformed body");
      const received = now();
      const difference = serverNow - (started + (received - started) / 2);
      offset = Math.abs(difference) < 5000 ? 0 : Math.round(difference);
      synchronized = true;
      nextAttempt = received + 900000;
    } catch {
      nextAttempt = now() + 60000;
    }
  }
  return {
    offset: () => offset,
    hasSynchronized: () => synchronized,
    now: () => now() + offset,
    synchronize() {
      return (
        inFlight ||
        (now() < nextAttempt
          ? Promise.resolve()
          : (inFlight = sample().finally(() => {
              inFlight = null;
            })))
      );
    },
  };
}

export function createClockTicks({
  clock = createServerClock(),
  document: visibility = globalThis.document,
  setTimeout: schedule = (callback, milliseconds) =>
    globalThis.setTimeout(callback, milliseconds),
  clearTimeout: cancel = (handle) => globalThis.clearTimeout(handle),
} = {}) {
  let snapshot = clock.now();
  const listeners = new Set();
  let timer = null;
  let listening = false;
  function emit() {
    snapshot = clock.now();
    for (const listener of [...listeners]) listener();
  }
  function stopTimer() {
    if (timer !== null) {
      cancel(timer);
      timer = null;
    }
  }
  function scheduleTick() {
    stopTimer();
    timer = schedule(
      () => {
        emit();
        scheduleTick();
      },
      1000 - (clock.now() % 1000),
    );
  }
  function synchronize() {
    const before = clock.offset();
    clock.synchronize().then(() => {
      if (listeners.size > 0 && clock.offset() !== before) emit();
    });
  }
  function visibilityChanged() {
    if (visibility.hidden) stopTimer();
    else {
      emit();
      scheduleTick();
      synchronize();
    }
  }
  return {
    getSnapshot: () => snapshot,
    getServerSnapshot: () => 0,
    subscribe(listener) {
      const first = listeners.size === 0;
      listeners.add(listener);
      if (first) {
        if (!listening) {
          visibility.addEventListener("visibilitychange", visibilityChanged);
          listening = true;
        }
        snapshot = clock.now();
        if (!visibility.hidden) scheduleTick();
        synchronize();
      }
      return () => {
        listeners.delete(listener);
        if (listeners.size === 0) {
          stopTimer();
          if (listening) {
            visibility.removeEventListener(
              "visibilitychange",
              visibilityChanged,
            );
            listening = false;
          }
        }
      };
    },
  };
}

export function parseTimestamp(value) {
  if (value === null || value === undefined) return null;
  if (value instanceof Date) {
    const milliseconds = value.getTime();
    return Number.isFinite(milliseconds) ? milliseconds : null;
  }
  if (typeof value === "number")
    return Number.isFinite(value)
      ? value < 10000000000
        ? value * 1000
        : value
      : null;
  const milliseconds = Date.parse(value);
  return Number.isFinite(milliseconds) ? milliseconds : null;
}

// English labels are bound separately to the captured locale=en Flight resource.
const units = [
  [31104000000, "y"],
  [2592000000, "mo"],
  [86400000, "d"],
  [3600000, "h"],
  [60000, "m"],
  [1000, "s"],
];
export function formatElapsed(elapsed, suffix = true) {
  if (!Number.isFinite(elapsed)) return "";
  const clamped = Math.max(1000, elapsed);
  const [milliseconds, label] =
    units.find(([milliseconds]) => clamped >= milliseconds) ?? units.at(-1);
  return `${Math.floor(clamped / milliseconds)}${label}${suffix ? " ago" : ""}`;
}
