import { usePathname } from "next/navigation";
import { lockBodyScroll } from "@/lib/body-scroll-lock";
import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
import { createPortal } from "react-dom";
import { AuthDialogController } from "./auth-controller";
import { walletChoices, type AuthPresentationAdapter } from "./auth-model";
import copy from "./auth-copy.json";
import styles from "./auth-dialog.module.css";
import { PublicWalletPanel } from "./public-wallet/panel";

type Props = {
  adapter: AuthPresentationAdapter;
  /** Public-address connection only; does not supply authentication. */
  publicWallet?: boolean;
  /** Only the external browser-test fixture passes this; product entrypoint cannot. */
  syntheticTest?: boolean;
  /** Presentation only: lets the host shell match its captured sign-in button. */
  triggerClassName?: string;
};

function Arrow({ back = false }: { back?: boolean }) {
  return (
    <svg
      aria-hidden="true"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d={back ? "m14 6-6 6 6 6" : "m10 6 6 6-6 6"}
        stroke="currentColor"
        strokeWidth="2"
      />
    </svg>
  );
}

/** Internal client component. No auth commands exist on its read-only adapter. */
export function AuthControl({
  adapter,
  publicWallet = false,
  syntheticTest = false,
  triggerClassName,
}: Props) {
  const controller = useMemo(
    () => new AuthDialogController(adapter, { allowSynthetic: syntheticTest }),
    [adapter, syntheticTest],
  );
  const state = useSyncExternalStore(
    controller.subscribe,
    controller.getSnapshot,
    controller.getSnapshot,
  );
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const close = useRef<HTMLButtonElement>(null);
  const back = useRef<HTMLButtonElement>(null);
  const more = useRef<HTMLButtonElement>(null);
  const [mounted, setMounted] = useState(false);
  const pathname = usePathname();
  const titleId = useId();
  const boundaryId = useId();
  const open = state.status !== "closed";
  const expanded = state.status === "ready" && state.expanded;

  useEffect(() => {
    setMounted(true);
    return controller.dispose;
  }, [controller]);

  useEffect(() => {
    controller.close();
  }, [controller, pathname]);
  useEffect(() => {
    window.addEventListener("popstate", controller.close);
    return () => window.removeEventListener("popstate", controller.close);
  }, [controller]);

  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    if (open && !element.open) element.showModal();
    if (!open && element.open) {
      element.close();
      const target = trigger.current;
      if (
        target?.isConnected &&
        !target.closest("[inert]") &&
        target.getClientRects().length
      )
        target.focus();
      else document.getElementById("main-content")?.focus();
    }
  }, [mounted, open]);

  useEffect(() => {
    const element = dialog.current;
    // Retry removes its focused button. Recover only lost focus; preserve
    // any surviving control the user is already interacting with.
    if (element?.open && !element.contains(document.activeElement))
      close.current?.focus();
  }, [mounted, state.status]);

  useEffect(() => {
    if (!open) return;
    return lockBodyScroll();
  }, [open]);

  const expandWallets = () => {
    controller.setExpanded(true);
    requestAnimationFrame(() => back.current?.focus());
  };
  const collapseWallets = () => {
    controller.setExpanded(false);
    requestAnimationFrame(() => more.current?.focus());
  };

  const title =
    state.status === "loading"
      ? copy["web.auth.opening_sign_in"]
      : state.status === "error"
        ? copy["web.auth.sign_in_open_failed_title"]
        : expanded
          ? copy["web.wallet.select_wallet"]
          : copy["web.wallet.welcome_back"];

  return (
    <>
      <button
        ref={trigger}
        type="button"
        className={triggerClassName ?? styles.trigger}
        data-testid="sign-in-button"
        aria-haspopup="dialog"
        aria-expanded={open}
        disabled={!mounted}
        onClick={controller.open}
      >
        {copy["common.sign_in"]}
      </button>
      {mounted &&
        createPortal(
          <dialog
            ref={dialog}
            className={styles.dialog}
            data-testid="auth-dialog"
            data-auth-state={state.status}
            aria-labelledby={titleId}
            aria-describedby={boundaryId}
            aria-modal="true"
            role={state.status === "error" ? "alertdialog" : "dialog"}
            onCancel={(event) => {
              event.preventDefault();
              controller.close();
            }}
            onClose={controller.close}
            onKeyDown={(event) => {
              if (event.key === "Escape") event.stopPropagation();
            }}
            onClick={(event) => {
              if (event.target !== event.currentTarget) return;
              const bounds = event.currentTarget.getBoundingClientRect();
              if (
                event.clientX < bounds.left ||
                event.clientX > bounds.right ||
                event.clientY < bounds.top ||
                event.clientY > bounds.bottom
              )
                controller.close();
            }}
          >
            <div className={styles.panel}>
              <header className={styles.header}>
                {expanded ? (
                  <button
                    ref={back}
                    type="button"
                    className={styles.iconButton}
                    aria-label={copy["common.back"]}
                    onClick={collapseWallets}
                  >
                    <Arrow back />
                  </button>
                ) : (
                  <span className={styles.headerSpacer} />
                )}
                <div className={styles.heading}>
                  {state.status === "ready" && !expanded && (
                    <span className={styles.logo} aria-hidden="true">
                      {/* The shared reconstruction's local asset; no remote image request. */}
                      <img
                        src="/pump-logomark.svg"
                        width="28"
                        height="28"
                        alt=""
                      />
                    </span>
                  )}
                  <h2 id={titleId}>{title}</h2>
                </div>
                <button
                  ref={close}
                  type="button"
                  className={styles.iconButton}
                  autoFocus
                  aria-label={copy["common.close"]}
                  onClick={controller.close}
                >
                  <svg
                    aria-hidden="true"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                  >
                    <path
                      d="m6 6 12 12M18 6 6 18"
                      stroke="currentColor"
                      strokeWidth="2"
                    />
                  </svg>
                </button>
              </header>
              <p className={styles.boundary} id={boundaryId}>
                {syntheticTest
                  ? "Synthetic UI test — not an authenticated account."
                  : "Local reconstruction — sign-in is unavailable."}{" "}
                No authenticated account or email is connected.
              </p>

              {state.status === "loading" && (
                <div
                  className={styles.loading}
                  role="status"
                  aria-live="polite"
                >
                  <span className={styles.spinner} aria-hidden="true" />
                  <p>{copy["web.auth.loading_wallet_options"]}</p>
                </div>
              )}

              {state.status === "error" && (
                <div className={styles.error} data-testid="sign-in-error">
                  <span className={styles.errorIcon} aria-hidden="true">
                    !
                  </span>
                  <p>
                    {
                      copy[
                        state.reason === "timeout"
                          ? "web.auth.sign_in_timeout_description"
                          : "web.auth.sign_in_error_description"
                      ]
                    }
                  </p>
                  <button
                    type="button"
                    className={styles.retry}
                    data-testid="sign-in-retry"
                    onClick={controller.retry}
                  >
                    {copy["web.common.try_again"]}
                  </button>
                  <button
                    type="button"
                    className={styles.secondary}
                    data-testid="sign-in-reload"
                    onClick={() => window.location.reload()}
                  >
                    {copy["web.auth.refresh_the_page"]}
                  </button>
                </div>
              )}

              {state.status === "ready" && (
                <div className={styles.options} data-testid="sign-in-modal">
                  {state.presentation.session === "expired" && (
                    <p className={styles.notice} role="status">
                      {copy["web.auth.session_lapsed_signed_out"]}
                    </p>
                  )}
                  {!expanded && (
                    <>
                      <div
                        className={styles.social}
                        role="group"
                        aria-label={copy["web.auth.continue_with_social"]}
                      >
                        <button
                          type="button"
                          className={styles.google}
                          disabled
                          aria-describedby={boundaryId}
                          data-testid="auth-google-button"
                        >
                          Google
                        </button>
                        <div className={styles.socialRow}>
                          <button
                            type="button"
                            className={styles.apple}
                            disabled
                            aria-describedby={boundaryId}
                            data-testid="auth-apple-button"
                          >
                            Apple
                          </button>
                          <button
                            type="button"
                            className={styles.github}
                            disabled
                            aria-describedby={boundaryId}
                            data-testid="auth-github-button"
                          >
                            {copy["web.auth.continue_with_github"]}
                          </button>
                        </div>
                      </div>
                      {/* Deliberately not an input or form: this reconstruction collects no identifiers or codes. */}
                      <div
                        className={styles.email}
                        aria-disabled="true"
                        aria-describedby={boundaryId}
                        data-testid="auth-email-unavailable"
                      >
                        <span>{copy["web.auth.email_address_label"]}</span>
                        <span className={styles.unavailable}>Unavailable</span>
                      </div>
                      <div className={styles.divider}>
                        <span>{copy["web.wallet.or_connect_wallet"]}</span>
                      </div>
                    </>
                  )}
                  <div
                    className={styles.walletList}
                    data-testid={
                      expanded ? "auth-all-wallets" : "auth-wallet-preview"
                    }
                  >
                    {walletChoices(state.presentation, expanded).map(
                      (wallet) => (
                        <button
                          key={wallet.name}
                          type="button"
                          disabled
                          className={styles.wallet}
                          aria-describedby={boundaryId}
                          data-testid="auth-wallet-option"
                        >
                          <span
                            className={styles.walletIcon}
                            aria-hidden="true"
                          >
                            {wallet.name.slice(0, 1)}
                          </span>
                          <span className={styles.walletName}>
                            {wallet.name}
                          </span>
                          <span className={styles.unavailable}>
                            {state.presentation.source === "synthetic-test" &&
                            wallet.name === state.presentation.recentWallet
                              ? `Test: ${copy["web.wallet.recent"]}`
                              : state.presentation.source ===
                                    "synthetic-test" &&
                                  wallet.readiness === "installed"
                                ? `Test: ${copy["web.wallet.detected"]}`
                                : "Unavailable"}
                          </span>
                        </button>
                      ),
                    )}
                    {walletChoices(state.presentation, expanded).length ===
                      0 && (
                      <p className={styles.empty}>
                        No wallet options are available from this adapter.
                        Wallet extensions have not been checked.
                      </p>
                    )}
                  </div>
                  {!expanded && (
                    <button
                      ref={more}
                      type="button"
                      className={styles.more}
                      data-testid="show-all-wallets-button"
                      onClick={expandWallets}
                    >
                      <span className={styles.walletIcon} aria-hidden="true">
                        ⋯
                      </span>
                      <span>{copy["web.wallet.more_wallets"]}</span>
                      <Arrow />
                    </button>
                  )}
                  <p className={styles.footnote}>
                    Provider login, email codes and signing are disabled.
                  </p>
                  {publicWallet && <PublicWalletPanel />}
                </div>
              )}
            </div>
          </dialog>,
          document.body,
        )}
    </>
  );
}
