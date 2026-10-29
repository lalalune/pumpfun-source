"use client";

import { useId, useState, useSyncExternalStore } from "react";
import {
  preferenceKey,
  privacyPreferenceRuntime,
  type PrivacyPreference,
} from "../../../../../reconstruction/privacy-external-links/client.mjs";
import styles from "./privacy-setting-control.module.css";

// One runtime preserves the captured device setting's module-lifetime fallback.
// Browser APIs are touched only after the client boundary, never during SSR.
let devicePreference: PrivacyPreference | undefined;
export function getDevicePrivacyPreference() {
  devicePreference ??= privacyPreferenceRuntime({
    getStorage: () => window.localStorage,
    events: window,
    createStorageEvent: (type, init) => new StorageEvent(type, init),
  }).preference();
  return devicePreference;
}
const subscribe = (notify: () => void) => getDevicePrivacyPreference().subscribe(notify);
const snapshot = () => getDevicePrivacyPreference().read();
const serverSnapshot = () => true;
const subscribeToHydration = () => () => {};
const clientReady = () => true;
const serverReady = () => false;

/** Device preference shared by the local Create and footer outbound consumers. */
export function PrivacySettingControl({ label }: { label: string }) {
  const enabled = useSyncExternalStore(subscribe, snapshot, serverSnapshot);
  const ready = useSyncExternalStore(
    subscribeToHydration,
    clientReady,
    serverReady,
  );
  const [result, setResult] = useState<"idle" | "saved" | "unconfirmed">(
    "idle",
  );
  const id = useId();

  function change() {
    const next = !enabled;
    getDevicePrivacyPreference().write(next);
    // The captured writer intentionally swallows storage failures. A separate
    // read-back supports truthful UI feedback without changing that behavior.
    try {
      setResult(
        window.localStorage.getItem(preferenceKey) === JSON.stringify(next)
          ? "saved"
          : "unconfirmed",
      );
    } catch {
      setResult("unconfirmed");
    }
  }

  return (
    <div className={styles.control}>
      <button
        type="button"
        role="switch"
        aria-label={label}
        aria-checked={enabled}
        aria-describedby={`${id}-scope ${id}-result`}
        disabled={!ready}
        onClick={change}
        className={styles.switch}
      >
        {ready ? (enabled ? "On" : "Off") : "Loading…"}
      </button>
      <p id={`${id}-scope`} className={styles.scope}>
        Stored on this browser, shared across accounts. Applies to Create draft
        preview and site footer links; other app links are not connected.
      </p>
      <p
        id={`${id}-result`}
        role="status"
        className={result === "unconfirmed" ? styles.warning : styles.result}
      >
        {result === "saved"
          ? "Saved in this browser."
          : result === "unconfirmed"
            ? "Changed for this page, but browser storage could not be confirmed. Reloading may restore the previous choice."
            : ""}
      </p>
    </div>
  );
}
