"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { PublicWalletController } from "./controller";
import { PublicWalletBalanceOverview } from "./balance-overview";
import styles from "./public-wallet.module.css";

/** A separate local connection boundary; never changes the application's auth state. */
export function PublicWalletPanel() {
  const [controller, setController] = useState<PublicWalletController | null>(
    null,
  );
  useEffect(() => {
    const instance = new PublicWalletController(window);
    setController(instance);
    return () => instance.dispose();
  }, []);
  return controller ? <WalletChoices controller={controller} /> : null;
}

function WalletChoices({ controller }: { controller: PublicWalletController }) {
  const state = useSyncExternalStore(
    controller.subscribe,
    controller.getSnapshot,
    controller.getSnapshot,
  );
  if (state.status === "idle")
    return (
      <button
        className={styles.action}
        type="button"
        onClick={controller.discover}
      >
        Connect a public wallet
      </button>
    );
  return (
    <section
      className={styles.panel}
      aria-label="Public wallet connection"
      data-testid="public-wallet-panel"
    >
      <h3>Public wallet connection</h3>
      <p>
        Share a public Solana address with this page. This does not sign you in
        or request a signature. The address is forgotten when this dialog
        closes.
      </p>
      {state.address ? (
        <>
          <p role="status">Connected public address — ownership unverified</p>
          <code className={styles.address} data-testid="public-wallet-address">
            {state.address}
          </code>
          <button
            className={styles.action}
            type="button"
            onClick={() => void controller.disconnect()}
          >
            Disconnect and forget address
          </button>
          <PublicWalletBalanceOverview
            key={state.address}
            address={state.address}
          />
        </>
      ) : (
        <>
          {state.wallets.length === 0 && (
            <p role="status">
              No supported Solana wallet has registered. Open an installed
              Wallet Standard wallet, then try again.
            </p>
          )}
          <div className={styles.wallets}>
            {state.wallets.map((wallet) => (
              <button
                className={styles.action}
                type="button"
                key={wallet.id}
                disabled={
                  state.status === "connecting" ||
                  state.status === "disconnecting"
                }
                onClick={() => void controller.connect(wallet.id)}
              >
                Connect {wallet.name}
              </button>
            ))}
          </div>
        </>
      )}
      {state.status === "connecting" && (
        <>
          <p role="status">Waiting for wallet approval…</p>
          <button
            className={styles.action}
            type="button"
            onClick={controller.forget}
          >
            Cancel connection
          </button>
        </>
      )}
      {state.status === "disconnecting" && (
        <p role="status">Address forgotten. Disconnecting wallet…</p>
      )}
      {state.message && <p role="alert">{state.message}</p>}
    </section>
  );
}
