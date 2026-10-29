export type ServerClock = {
  offset(): number;
  hasSynchronized(): boolean;
  now(): number;
  synchronize(): Promise<void>;
};
export function createServerClock(options?: {
  now?: () => number;
  fetch?: typeof globalThis.fetch;
  timeoutSignal?: (milliseconds: number) => AbortSignal;
}): ServerClock;
export function createClockTicks(options?: {
  clock?: ServerClock;
  document?: Pick<
    Document,
    "hidden" | "addEventListener" | "removeEventListener"
  >;
  setTimeout?: (callback: () => void, milliseconds: number) => unknown;
  clearTimeout?: (handle: unknown) => void;
}): {
  getSnapshot(): number;
  getServerSnapshot(): 0;
  subscribe(listener: () => void): () => void;
};
export function parseTimestamp(value: unknown): number | null;
export function formatElapsed(elapsed: number, suffix?: boolean): string;
