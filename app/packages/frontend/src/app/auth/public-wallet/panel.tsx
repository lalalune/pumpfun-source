"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { PublicWalletController } from "./controller";
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
  const panel = useRef<HTMLElement>(null);
  useEffect(() => {
    const element = panel.current;
    // Replacing a focused wallet control can leave focus on body while the
    // enclosing auth dialog stays ready. Preserve every surviving focus target.
    if (
      element?.closest("dialog")?.open &&
      document.activeElement === document.body
    )
      element.focus();
  }, [state.status, state.wallets]);
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
      ref={panel}
      tabIndex={-1}
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
                onClick={(event) => {
                  // Move focus before this still-mounted button is disabled.
                  // Do not leave focus on a control that cannot keep it.
                  const element = panel.current;
                  if (
                    element?.closest("dialog")?.open &&
                    document.activeElement === event.currentTarget
                  )
                    element.focus();
                  void controller.connect(wallet.id);
                }}
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
