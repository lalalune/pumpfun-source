"use client";

import {
  useCallback,
  useMemo,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import {
  createClockTicks,
  createServerClock,
  formatElapsed,
  parseTimestamp,
} from "../../../../../reconstruction/relative-time/model.mjs";

const clock = createServerClock();
const ticks = createClockTicks({ clock });
const noSubscription = () => () => {};
const clientMounted = () => true;
const serverMounted = () => false;
const titleFormat = new Intl.DateTimeFormat("en", {
  dateStyle: "medium",
  timeStyle: "short",
});

type RelativeTimeProps = {
  timestamp: string | number | Date | null | undefined;
  live?: boolean;
  density?: "comfortable" | "terminal";
  suffix?: boolean;
  showTitle?: boolean;
  fallback?: ReactNode;
};

/** Captured529841.f behavior for the current application's English UI. */
export function RelativeTime({
  timestamp,
  live = true,
  density = "comfortable",
  suffix,
  showTitle = false,
  fallback = null,
}: RelativeTimeProps) {
  const milliseconds = parseTimestamp(timestamp);
  const withSuffix = suffix ?? density === "comfortable";
  const mounted = useSyncExternalStore(
    noSubscription,
    clientMounted,
    serverMounted,
  );
  const enabled = live && milliseconds !== null;
  const formatSnapshot = useCallback(
    (now: number) =>
      milliseconds === null || now === 0
        ? ""
        : formatElapsed(now - milliseconds, withSuffix),
    [milliseconds, withSuffix],
  );
  const getSnapshot = useCallback(
    () => formatSnapshot(enabled ? ticks.getSnapshot() : 0),
    [enabled, formatSnapshot],
  );
  const getServerSnapshot = useCallback(
    () => formatSnapshot(0),
    [formatSnapshot],
  );
  const current = useSyncExternalStore(
    enabled ? ticks.subscribe : noSubscription,
    getSnapshot,
    getServerSnapshot,
  );
  const title = useMemo(
    () =>
      !showTitle || milliseconds === null
        ? undefined
        : titleFormat.format(milliseconds),
    [showTitle, milliseconds],
  );
  if (milliseconds === null) return <>{fallback}</>;
  return (
    <time
      dateTime={new Date(milliseconds).toISOString()}
      title={mounted ? title : undefined}
      suppressHydrationWarning
      className="tabular-nums"
    >
      {mounted && live
        ? current
        : formatElapsed(clock.now() - milliseconds, withSuffix)}
    </time>
  );
}
