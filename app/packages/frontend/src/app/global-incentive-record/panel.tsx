"use client";

import { useEffect, useRef, useState } from "react";
import { fetchGlobalIncentiveRecord } from "./client";
import type { GlobalIncentiveRecord } from "./types";

export function GlobalIncentiveRecordPanel() {
  const [state, setState] = useState<"idle" | "loading" | "error" | "ready">(
    "idle",
  );
  const [value, setValue] = useState<GlobalIncentiveRecord | null>(null);
  const active = useRef<AbortController | null>(null);
  const generation = useRef(0);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(
    () => () => {
      generation.current++;
      active.current?.abort();
      if (timer.current !== null) clearTimeout(timer.current);
    },
    [],
  );
  async function read() {
    const sequence = ++generation.current;
    active.current?.abort();
    if (timer.current !== null) clearTimeout(timer.current);
    const controller = new AbortController();
    active.current = controller;
    setValue(null);
    setState("loading");
    const timeout = setTimeout(() => {
      if (sequence !== generation.current) return;
      generation.current++;
      controller.abort();
      setState("error");
    }, 20_000);
    timer.current = timeout;
    try {
      const result = await fetchGlobalIncentiveRecord(controller.signal);
      if (sequence === generation.current && !controller.signal.aborted) {
        setValue(result);
        setState("ready");
      }
    } catch {
      if (sequence === generation.current && !controller.signal.aborted)
        setState("error");
    } finally {
      clearTimeout(timeout);
      if (timer.current === timeout) timer.current = null;
      if (active.current === controller) active.current = null;
    }
  }
  const record = value?.record ?? null;
  return (
    <section
      className="mt-6 min-w-0 rounded-xl border border-border-secondary p-4"
      aria-labelledby="public-incentive-schedule-title"
      data-testid="public-incentive-schedule"
    >
      <h3 id="public-incentive-schedule-title" className="font-semibold">
        Public Pump incentive schedule
      </h3>
      <p className="mt-2 text-sm leading-6 text-text-secondary">
        Optionally inspect the separate program-wide schedule used by the SDK's
        incentive functions. These stored parameters and raw aggregate counters
        are not your rewards, an active-campaign determination or a claim quote.
      </p>
      <button
        type="button"
        className="portfolio-secondary-button mt-4"
        disabled={state === "loading"}
        onClick={() => void read()}
      >
        {state === "loading"
          ? "Reading incentive schedule…"
          : value
            ? "Refresh public incentive schedule"
            : "Read public incentive schedule"}
      </button>
      {state === "loading" && (
        <p role="status" className="mt-3 text-sm">
          Reading the separate public Global account…
        </p>
      )}
      {state === "error" && (
        <p role="alert" className="mt-3 text-sm">
          The public incentive schedule is unavailable or unsupported. No
          previous or estimated schedule was substituted.
        </p>
      )}
      {value && (
        <div
          className="mt-4 min-w-0"
          data-testid="public-incentive-schedule-result"
        >
          <p className="break-all text-sm leading-6 text-text-secondary">
            Response slot {value.contextSlot} · mainnet-beta · confirmed ·{" "}
            {value.endpointHost} ·{" "}
            <time dateTime={value.observedAt}>{value.observedAt}</time>
          </p>
          <p className="mt-2 break-all text-sm">
            Global record address <code>{value.recordPda}</code>
          </p>
          {record === null ? (
            <p className="mt-3 text-sm">
              No Global incentive record was returned at this PDA. This does not
              establish zero rewards or ineligibility.
            </p>
          ) : (
            <>
              <dl className="mt-4 grid min-w-0 gap-3 text-sm sm:grid-cols-2">
                <div>
                  <dt>Stored start timestamp (Unix seconds)</dt>
                  <dd className="break-all font-mono">{record.startTime}</dd>
                </div>
                <div>
                  <dt>Stored end timestamp (Unix seconds)</dt>
                  <dd className="break-all font-mono">{record.endTime}</dd>
                </div>
                <div>
                  <dt>Stored seconds in a day</dt>
                  <dd className="break-all font-mono">
                    {record.secondsInADay}
                  </dd>
                </div>
                <div>
                  <dt>Stored token mint</dt>
                  <dd className="break-all font-mono">{record.mint}</dd>
                </div>
              </dl>
              <div
                className="mt-4 overflow-x-auto"
                role="region"
                aria-label="Stored schedule entries"
                tabIndex={0}
              >
                <table className="w-full text-left text-xs">
                  <caption className="mb-2 text-left text-sm text-text-secondary">
                    30 stored schedule entries. Token supply and SOL volume are
                    raw integers; decimals, prices and reward shares are not
                    inferred.
                  </caption>
                  <thead>
                    <tr>
                      <th className="p-2" scope="col">
                        Entry
                      </th>
                      <th className="p-2" scope="col">
                        Token supply (raw)
                      </th>
                      <th className="p-2" scope="col">
                        SOL volume (raw)
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {record.totalTokenSupply.map((supply, index) => (
                      <tr
                        className="border-t border-border-secondary"
                        key={index}
                      >
                        <th className="p-2" scope="row">
                          {index + 1}
                        </th>
                        <td className="p-2 font-mono">{supply}</td>
                        <td className="p-2 font-mono">
                          {record.solVolumes[index]}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
          <p className="mt-3 text-sm leading-6 text-text-secondary">
            This Global record and your separate user record can be observed at
            different slots. Neither SDK incentive calculation is run. Claim
            eligibility and current entitlement remain unknown; no signing or
            claim action is enabled. Nothing is persisted.
          </p>
        </div>
      )}
    </section>
  );
}
