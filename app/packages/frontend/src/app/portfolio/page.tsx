import type { Metadata } from "next";
import PortfolioClient from "./portfolio-client";

export const metadata: Metadata = {
  title: "Live Solana portfolio",
  description: "Read-only Solana mainnet balances from a configured RPC",
};

export default async function PortfolioPage({
  searchParams,
}: {
  searchParams: Promise<{ address?: string | string[] }>;
}) {
  const rawAddress = (await searchParams).address;
  const address = Array.isArray(rawAddress) ? rawAddress[0] : rawAddress;
  return (
    <div className="portfolio-page">
      <div className="portfolio-heading">
        <div>
          <p className="eyebrow">Public mainnet read</p>
          <h1>Solana portfolio</h1>
          <p className="description">
            Inspect SOL, SPL Token and Token-2022 accounts directly from a
            configured Solana mainnet RPC. No wallet connection or signing is
            required.
          </p>
        </div>
        <span className="read-only-badge">Read only</span>
      </div>
      <PortfolioClient initialAddress={address ?? ""} />
    </div>
  );
}
