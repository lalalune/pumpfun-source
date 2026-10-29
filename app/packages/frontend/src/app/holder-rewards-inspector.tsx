"use client";

import { type FormEvent, useRef, useState } from "react";
import { HolderConfigurationPanel } from "./holder-rewards-config/panel";
import { HolderRewardsPublicBalances } from "./holder-rewards/public-balances";
import { RewardSummary } from "../components/rewards/RewardSummary";
import {
  deriveHolderRewardsAddress,
  type HolderRewardsDerivation,
} from "./holder-rewards-derivation";

const UNKNOWN_REWARDS = [
  {
    label: "Accrued rewards",
    amount: null,
    explanation: "Requires authenticated on-chain or service data.",
  },
  {
    label: "Claimed rewards",
    amount: null,
    explanation: "No payout history is loaded in this inspector.",
  },
  {
    label: "Claimable rewards",
    amount: null,
    explanation: "A derived PDA does not establish eligibility or balance.",
  },
] as const;

function AddressResult({
  label,
  value,
  onCopy,
}: {
  label: string;
  value: string;
  onCopy: (label: string, value: string) => void;
}) {
  return (
    <div className="min-w-0 rounded-xl border border-border-secondary bg-bg-primary p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.08em] text-text-tertiary">
        {label}
      </p>
      <div className="mt-2 flex min-w-0 flex-col gap-3 sm:flex-row sm:items-center">
        <output className="min-w-0 flex-1 break-all font-mono text-sm leading-6 text-text-primary">
          {value}
        </output>
        <button
          className="min-h-11 shrink-0 rounded-lg border border-border-tertiary px-4 text-sm font-semibold text-text-primary transition-colors hover:bg-bg-tertiary"
          type="button"
          onClick={() => onCopy(label, value)}
          aria-label={`Copy ${label.toLowerCase()}`}
        >
          Copy
        </button>
      </div>
    </div>
  );
}

export default function HolderRewardsInspector() {
  const [mintInput, setMintInput] = useState("");
  const [result, setResult] = useState<HolderRewardsDerivation | null>(null);
  const [copyStatus, setCopyStatus] = useState("");
  const copyGeneration = useRef(0);

  function updateMint(value: string) {
    copyGeneration.current++;
    setMintInput(value);
    setResult(null);
    setCopyStatus("");
  }

  function inspectMint(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    copyGeneration.current++;
    setResult(deriveHolderRewardsAddress(mintInput));
    setCopyStatus("");
  }

  async function copyAddress(label: string, value: string) {
    const generation = ++copyGeneration.current;
    try {
      await navigator.clipboard.writeText(value);
      if (generation === copyGeneration.current) setCopyStatus(`${label} copied.`);
    } catch {
      if (generation === copyGeneration.current)
        setCopyStatus(`Could not copy ${label.toLowerCase()}. Select the address instead.`);
    }
  }

  function clearInspector() {
    copyGeneration.current++;
    setMintInput("");
    setResult(null);
    setCopyStatus("Inspector cleared.");
  }

  const error = result && !result.ok ? result.error : undefined;

  return (
    <div className="mt-8 grid gap-5" data-testid="holder-rewards-inspector">
      <section className="rounded-2xl border border-border-secondary bg-bg-secondary p-5 sm:p-7">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold tracking-tight text-text-primary">
              Inspect a holder-rewards address
            </h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-text-tertiary">
              Enter a Solana mint to compute its deterministic Pump
              holder-rewards PDA. Computation stays in this browser and does
              not query the chain.
            </p>
          </div>
          <span className="w-fit rounded-full border border-border-tertiary bg-bg-tertiary px-3 py-1 text-xs font-semibold text-text-accent">
            Offline SDK computation
          </span>
        </div>

        <form className="mt-6" onSubmit={inspectMint} noValidate>
          <label className="text-sm font-semibold text-text-primary" htmlFor="holder-rewards-mint">
            Solana mint address
          </label>
          <p className="mt-1 text-xs leading-5 text-text-muted" id="holder-rewards-mint-hint">
            Whitespace is trimmed. A syntactically valid address does not prove
            that a mint or rewards account exists.
          </p>
          <div className="mt-3 flex flex-col gap-3 md:flex-row">
            <input
              className="min-h-12 min-w-0 flex-1 rounded-xl border border-border-tertiary bg-bg-primary px-4 font-mono text-sm text-text-primary placeholder:text-text-muted"
              id="holder-rewards-mint"
              name="mint"
              value={mintInput}
              onChange={(event) => updateMint(event.target.value)}
              placeholder="Enter a Base58 public key"
              autoComplete="off"
              spellCheck={false}
              aria-invalid={Boolean(error)}
              aria-describedby={`holder-rewards-mint-hint${error ? " holder-rewards-mint-error" : ""}`}
            />
            <button
              className="min-h-12 rounded-xl bg-bg-accent px-5 text-sm font-bold text-text-on-accent transition-[filter] hover:brightness-90"
              type="submit"
            >
              Derive address
            </button>
            <button
              className="min-h-12 rounded-xl border border-border-tertiary px-5 text-sm font-semibold text-text-secondary transition-colors hover:bg-bg-tertiary disabled:cursor-not-allowed disabled:opacity-50"
              type="button"
              onClick={clearInspector}
              disabled={!mintInput && !result}
            >
              Clear
            </button>
          </div>
          {error ? (
            <p className="mt-3 text-sm text-text-error" id="holder-rewards-mint-error" role="alert">
              {error}
            </p>
          ) : null}
        </form>
      </section>

      {result?.ok ? (
        <section
          className="rounded-2xl border border-border-secondary bg-bg-secondary p-5 sm:p-7"
          aria-labelledby="holder-rewards-result-heading"
          data-testid="holder-rewards-result"
        >
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-xl font-semibold tracking-tight text-text-primary" id="holder-rewards-result-heading">
              Local derivation result
            </h2>
            <span className="text-xs font-semibold text-text-accent">Computed locally</span>
          </div>
          <div className="mt-5 grid gap-3">
            <AddressResult label="Normalized mint" value={result.mint} onCopy={copyAddress} />
            <AddressResult label="Holder-rewards PDA" value={result.holderRewardsPda} onCopy={copyAddress} />
          </div>
          <p className="mt-4 text-sm leading-6 text-text-tertiary">
            SDK derivation: seeds <code className="rounded bg-bg-tertiary px-1.5 py-0.5 text-xs text-text-primary">[&quot;holder-rewards&quot;, mint]</code> under the Pump program ID.
          </p>
        </section>
      ) : (
        <section className="rounded-2xl border border-dashed border-border-tertiary bg-bg-secondary p-5 sm:p-7" data-testid="holder-rewards-no-result">
          <h2 className="text-base font-semibold text-text-primary">No mint inspected</h2>
          <p className="mt-2 text-sm leading-6 text-text-tertiary">
            Enter a mint above to derive an address. No live account or reward
            information is loaded.
          </p>
        </section>
      )}

      {result?.ok && <HolderConfigurationPanel key={result.mint} mint={result.mint} rewardsPda={result.holderRewardsPda} />}
      {result?.ok && <HolderRewardsPublicBalances key={result.holderRewardsPda} address={result.holderRewardsPda} />}

      <section aria-labelledby="holder-rewards-status-heading">
        <div className="mb-3">
          <h2 className="text-xl font-semibold tracking-tight text-text-primary" id="holder-rewards-status-heading">
            Reward status
          </h2>
          <p className="mt-1 text-sm leading-6 text-text-tertiary">
            These values remain unknown without authenticated live data.
          </p>
        </div>
        <RewardSummary items={UNKNOWN_REWARDS} />
      </section>

      <section className="rounded-2xl border border-border-secondary bg-bg-secondary p-5 sm:p-7" aria-labelledby="holder-rewards-boundary-heading">
        <h2 className="text-lg font-semibold text-text-primary" id="holder-rewards-boundary-heading">
          Rewards trust boundary
        </h2>
        <ul className="mt-3 grid gap-2 pl-5 text-sm leading-6 text-text-tertiary marker:text-text-accent">
          <li>Mint existence and Pump-coin status are not checked.</li>
          <li>Rewards configuration, ownership, accrual and eligibility are unknown.</li>
          <li>No wallet is connected and no transaction can be signed or submitted.</li>
        </ul>
        <button className="mt-5 min-h-11 w-full cursor-not-allowed rounded-xl border border-border-tertiary bg-bg-tertiary px-4 text-sm font-semibold text-text-muted sm:w-auto" type="button" disabled>
          Claim unavailable
        </button>
      </section>

      <p className="sr-only" aria-live="polite" role="status">
        {copyStatus}
      </p>
      {copyStatus ? (
        <p className="text-sm text-text-accent" aria-hidden="true">
          {copyStatus}
        </p>
      ) : null}
    </div>
  );
}
