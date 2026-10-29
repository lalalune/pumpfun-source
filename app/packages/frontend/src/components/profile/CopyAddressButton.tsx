"use client";

import { useRef, useState } from "react";

export function CopyAddressButton({ address }: { address: string }) {
  const [outcome, setOutcome] = useState<{
    address: string;
    status: "copied" | "failed";
  } | null>(null);
  const request = useRef(0);
  const status = outcome?.address === address ? outcome.status : "idle";

  async function copyAddress() {
    const ticket = ++request.current;
    setOutcome(null);
    try {
      await navigator.clipboard.writeText(address);
      if (ticket === request.current) setOutcome({ address, status: "copied" });
    } catch {
      if (ticket === request.current) setOutcome({ address, status: "failed" });
    }
  }

  return (
    <span className="profile-copy-control">
      <button
        type="button"
        onClick={copyAddress}
        aria-label="Copy wallet address"
      >
        Copy address
      </button>
      <span className="sr-only" aria-live="polite">
        {status === "copied"
          ? "Wallet address copied"
          : status === "failed"
            ? "Wallet address could not be copied"
            : ""}
      </span>
    </span>
  );
}
