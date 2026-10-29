"use client";
import { useEffect, useRef, useState } from "react";
import { AMM_COUNTERS, fetchAmmWalletRecord } from "./client";
import type { AmmWalletRecordSuccess } from "./types";

export function PublicAmmWalletRecordPanel({ address }: { address: string }) {
  const [value, setValue] = useState<AmmWalletRecordSuccess | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "ready">(
    "idle",
  );
  const active = useRef<AbortController | null>(null);
  const deadline = useRef<ReturnType<typeof setTimeout> | null>(null);
  const generation = useRef(0);
  useEffect(() => {
    generation.current++;
    setValue(null);
    setStatus("idle");
    return () => {
      generation.current++;
      active.current?.abort();
      if (deadline.current) clearTimeout(deadline.current);
    };
  }, [address]);
  async function read() {
    active.current?.abort();
    if (deadline.current) clearTimeout(deadline.current);
    const controller = new AbortController();
    active.current = controller;
    const current = ++generation.current;
    setValue(null);
    setStatus("loading");
    const timeout = setTimeout(() => {
      if (current === generation.current) {
        controller.abort();
        setStatus("error");
      }
    }, 20_000);
    deadline.current = timeout;
    try {
      const result = await fetchAmmWalletRecord(address, controller.signal);
      if (!controller.signal.aborted && current === generation.current) {
        setValue(result);
        setStatus("ready");
      }
    } catch {
      if (!controller.signal.aborted && current === generation.current)
        setStatus("error");
    } finally {
      clearTimeout(timeout);
    }
  }
  return (
    <section
      className="min-w-0 rounded-xl border border-border-secondary bg-bg-secondary p-5"
      aria-labelledby="public-amm-record-title"
      data-testid="public-amm-record"
    >
      <h2 id="public-amm-record-title" className="text-lg font-semibold">
        Public PumpSwap activity record
      </h2>
      <p className="mt-2 text-sm leading-6 text-text-secondary">
        Optionally inspect this wallet’s stored PumpSwap program record. Pump
        and PumpSwap records are separate observations; their counters are not
        combined. It is separate from wallet balances and does not establish
        current rewards, claim eligibility, ownership or profit.
      </p>
      <button
        type="button"
        className="portfolio-secondary-button mt-4"
        onClick={read}
        disabled={status === "loading"}
      >
        {status === "loading"
          ? "Reading public record…"
          : value
            ? "Refresh public PumpSwap record"
            : "Read public PumpSwap record"}
      </button>
      {status === "loading" && (
        <p role="status" className="mt-3 text-sm">
          Reading the wallet-specific public account…
        </p>
      )}
      {status === "error" && (
        <p role="alert" className="mt-3 text-sm">
          The public PumpSwap record is unavailable or unsupported. No previous,
          zero or estimated record was substituted. Try again.
        </p>
      )}
      {value && (
        <div className="mt-4 min-w-0" data-testid="public-amm-record-result">
          <p className="text-sm leading-6 text-text-secondary">
            Response slot {value.contextSlot} · mainnet-beta · confirmed ·{" "}
            {value.endpointHost} ·{" "}
            <time dateTime={value.observedAt}>{value.observedAt}</time>
          </p>
          <p className="mt-2 break-all text-sm">
            Record address <code>{value.recordPda}</code>
          </p>
          {value.record === null ? (
            <p className="mt-4">
              No PumpSwap record was returned at this PDA. This is not a zero
              reward balance, a complete activity history, or proof of
              ineligibility.
            </p>
          ) : (
            <>
              <dl className="mt-4 grid min-w-0 gap-3 sm:grid-cols-2">
                {AMM_COUNTERS.map(([key, label]) => (
                  <div
                    key={key}
                    className="min-w-0 rounded-lg border border-border-secondary p-3"
                  >
                    <dt className="text-sm text-text-secondary">
                      {label} (raw integer)
                    </dt>
                    <dd className="mt-1 break-all font-mono text-sm">
                      {value.record![key]}
                    </dd>
                  </div>
                ))}
                <div>
                  <dt className="text-sm text-text-secondary">
                    Stored update timestamp (Unix seconds)
                  </dt>
                  <dd className="break-all font-mono text-sm">
                    {value.record.lastUpdateTimestamp}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-text-secondary">
                    Stored needs-claim flag
                  </dt>
                  <dd>{String(value.record.needsClaim)}</dd>
                </div>
                <div>
                  <dt className="text-sm text-text-secondary">
                    Stored has-claimed-counter flag
                  </dt>
                  <dd>{String(value.record.hasTotalClaimedTokens)}</dd>
                </div>
              </dl>
              <p className="mt-4 text-sm leading-6 text-text-secondary">
                These exact stored counters are not calculated entitlements.
                Token units, decimals and a current claim amount are not
                inferred. The SDK’s incentive calculation also uses a separate
                Global record; it is not run here. No claim or signing action is
                enabled.
              </p>
            </>
          )}
          <p className="mt-3 text-sm leading-6 text-text-secondary">
            Only this PumpSwap wallet record is inspected. The separate Pump
            record and balance reads may observe different slots. Their counters
            are not summed, and nothing is persisted.
          </p>
        </div>
      )}
    </section>
  );
}
