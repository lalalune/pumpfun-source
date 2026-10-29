"use client";

import {
  useEffect,
  useId,
  useRef,
  useState,
  type MouseEvent,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";
import { lockBodyScroll } from "@/lib/body-scroll-lock";
import { getDevicePrivacyPreference } from "@/components/settings/privacy-setting-control";
import {
  outboundConfirmation,
  preferenceKey,
  normalizeOutboundUrl,
} from "../../../../../reconstruction/privacy-external-links/client.mjs";
import styles from "./footer-outbound-links.module.css";

type Controller = ReturnType<typeof outboundConfirmation>;
type Snapshot = ReturnType<Controller["getSnapshot"]>;

/** Normal footer clicks use the existing device policy; native anchors remain intact. */
export function FooterOutboundLinks({ children }: { children: ReactNode }) {
  const controller = useRef<Controller | null>(null);
  const unsubscribe = useRef<(() => boolean) | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const cancel = useRef<HTMLButtonElement>(null);
  const returnFocus = useRef<HTMLElement | null>(null);
  const backdropDown = useRef(false);
  const [mounted, setMounted] = useState(false);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [failureUrl, setFailureUrl] = useState<string | null>(null);
  const [storageUnconfirmed, setStorageUnconfirmed] = useState(false);
  const titleId = useId();
  const descriptionId = useId();
  const visible = Boolean(snapshot?.open || failureUrl);
  const destination = snapshot?.pendingUrl ?? failureUrl;

  useEffect(() => {
    setMounted(true);
    return () => {
      unsubscribe.current?.();
      controller.current?.dispose();
      controller.current = null;
    };
  }, []);

  function currentController() {
    if (!controller.current) {
      const current = outboundConfirmation({
        preference: getDevicePrivacyPreference(),
        // The local shell exposes this setting, as in CreateDraftLinks. This
        // does not establish the original WEB_SETTINGS_HUB rollout.
        settingsHubEnabled: true,
        openWindow: (url, target, features) =>
          window.open(url, target, features),
      });
      controller.current = current;
      unsubscribe.current = current.subscribe(() =>
        setSnapshot(current.getSnapshot()),
      );
    }
    return controller.current;
  }

  function dismiss() {
    controller.current?.cancel();
    setFailureUrl(null);
  }

  useEffect(() => {
    const element = dialog.current;
    if (!mounted || !visible || !element) return;
    element.showModal();
    cancel.current?.focus();
    const unlock = lockBodyScroll();
    return () => {
      element.close();
      unlock();
      const target = returnFocus.current;
      if (
        target?.isConnected &&
        target.getClientRects().length &&
        !target.closest("[inert]")
      )
        target.focus({ preventScroll: true });
      else
        document.getElementById("main-content")?.focus({ preventScroll: true });
    };
  }, [mounted, visible]);

  function follow(event: MouseEvent<HTMLDivElement>) {
    if (event.defaultPrevented || !(event.target instanceof Element)) return;
    const anchor = event.target.closest("a");
    if (!(anchor instanceof HTMLAnchorElement) || anchor.target !== "_blank")
      return;
    const href = anchor.getAttribute("href");
    // A portal menu bubbles through its React footer ancestor. Keep its stable
    // trigger for focus restoration after the selected menu item unmounts.
    const menu = anchor.closest('[role="menu"]');
    const trigger = menu?.id
      ? Array.from(
          document.querySelectorAll<HTMLElement>("[aria-controls]"),
        ).find((element) => element.getAttribute("aria-controls") === menu.id)
      : null;
    returnFocus.current = trigger ?? anchor;
    setFailureUrl(null);
    setStorageUnconfirmed(false);
    try {
      currentController().handleLinkClick(event, { href });
    } catch {
      // The captured controller keeps a pending request when opening throws.
      // Provide local recovery without fabricating a successful new tab.
      setFailureUrl(normalizeOutboundUrl(href));
    }
  }

  function confirm() {
    const current = currentController();
    const before = current.getSnapshot();
    const url = before.pendingUrl ?? failureUrl;
    if (!url) return;
    setFailureUrl(null);
    try {
      if (before.open) current.confirm();
      else current.requestNavigation(url);
    } catch {
      setFailureUrl(url);
    } finally {
      // The source writer swallows storage failures and may use a page fallback.
      // Read-back feedback reports persistence honestly without changing it.
      if (before.open && before.dontAskAgain) {
        try {
          setStorageUnconfirmed(
            window.localStorage.getItem(preferenceKey) !== "false",
          );
        } catch {
          setStorageUnconfirmed(true);
        }
      }
    }
  }

  return (
    <>
      <div style={{ display: "contents" }} onClick={follow}>
        {children}
      </div>
      {storageUnconfirmed && (
        <p className={styles.warning} role="status">
          The choice changed for this page, but browser storage could not be
          confirmed. Reloading may restore the previous choice.
        </p>
      )}
      {mounted &&
        createPortal(
          <dialog
            ref={dialog}
            className={styles.dialog}
            aria-labelledby={titleId}
            aria-describedby={descriptionId}
            data-testid="footer-link-confirmation"
            onCancel={(event) => {
              event.preventDefault();
              dismiss();
            }}
            onKeyDown={(event) => {
              if (event.key === "Escape") event.stopPropagation();
            }}
            onPointerDown={(event) => {
              backdropDown.current = event.target === event.currentTarget;
            }}
            onClick={(event) => {
              if (backdropDown.current && event.target === event.currentTarget)
                dismiss();
            }}
          >
            <div className={styles.content}>
              <h2 id={titleId}>Open external link?</h2>
              <p id={descriptionId}>
                This link opens another website in a new tab.
              </p>
              <p className={styles.url}>{destination}</p>
              {failureUrl && (
                <div className={styles.failure} role="alert">
                  <p>
                    The browser could not open this link. Retry or use the
                    browser link below.
                  </p>
                  <a
                    href={failureUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={dismiss}
                  >
                    Use browser link
                  </a>
                </div>
              )}
              {snapshot?.open && (
                <label className={styles.choice}>
                  <input
                    type="checkbox"
                    checked={snapshot.dontAskAgain}
                    onChange={(event) =>
                      controller.current?.setDontAskAgain(event.target.checked)
                    }
                  />
                  Do not ask again on this browser
                </label>
              )}
              <div className={styles.actions}>
                <button type="button" ref={cancel} onClick={dismiss}>
                  Cancel
                </button>
                <button type="button" onClick={confirm}>
                  {failureUrl ? "Retry new tab" : "Open link"}
                </button>
              </div>
            </div>
          </dialog>,
          document.body,
        )}
    </>
  );
}
