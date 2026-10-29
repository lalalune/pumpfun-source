"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { lockBodyScroll } from "@/lib/body-scroll-lock";
import {
  Suspense,
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import { createPortal } from "react-dom";
import type { NotificationAdapter } from "../../lib/notification-controller";
import {
  NotificationSettingsProvider,
  NotificationSettingsModeLabel,
  NotificationSettingsStatus,
  NotificationSettingControl,
} from "./notification-settings";
import {
  SETTINGS_DEFINITIONS,
  SETTINGS_SECTIONS,
  findSettings,
  readSettingsLocation,
  settingsHref,
  type SettingDefinition,
  type SettingsSection,
} from "./settings-model";
import styles from "./settings.module.css";
import { PrivacySettingControl } from "./privacy-setting-control";

export type SettingsControlProps = {
  /** Explicit client-side local/test injection only; no runtime adapter is supplied. */
  notificationAdapter?: NotificationAdapter;
  /** Local ownership token, not authentication or account discovery. */
  notificationSessionKey?: string;
  /** Presentation only: lets the host shell style the launcher as its own footer entry. */
  launcherClassName?: string;
};

function SettingsIcon() {
  return (
    <svg
      aria-hidden="true"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d="m9 3-.6 2.4-2 .9L4 5.8 2 9.2l1.8 1.7v2.2L2 14.8l2 3.4 2.4-.5 2 .9L9 21h4l.6-2.4 2-.9 2.4.5 2-3.4-1.8-1.7v-2.2L20 9.2l-2-3.4-2.4.5-2-.9L13 3Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <circle cx="11" cy="12" r="3" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

function SettingRow({ setting }: { setting: SettingDefinition }) {
  return (
    <div className={styles.setting} data-setting-id={setting.id} tabIndex={-1}>
      <div>
        <h4>{setting.label}</h4>
        <p>{setting.description}</p>
      </div>
      <NotificationSettingControl
        settingId={setting.id}
        label={setting.label}
        fallback={
          setting.id === "privacy.confirmExternalLinks" ? (
            <PrivacySettingControl label={setting.label} />
          ) : (
            <span className={styles.unavailable}>Unavailable</span>
          )
        }
      />
    </div>
  );
}

function SettingGroups({
  settings,
  search = false,
}: {
  settings: readonly SettingDefinition[];
  search?: boolean;
}) {
  const groups = new Map<string, SettingDefinition[]>();
  for (const setting of settings) {
    const section = SETTINGS_SECTIONS.find(
      (item) => item.id === setting.section,
    )?.label;
    const group = search ? `${section} / ${setting.group}` : setting.group;
    const rows = groups.get(group) ?? [];
    rows.push(setting);
    groups.set(group, rows);
  }
  return Array.from(groups, ([group, rows]) => (
    <section className={styles.group} key={group} aria-label={group}>
      <h3>{group}</h3>
      {rows.map((setting) => (
        <SettingRow setting={setting} key={setting.id} />
      ))}
    </section>
  ));
}

function SettingsControlContent({
  notificationAdapter,
  notificationSessionKey,
  launcherClassName,
}: SettingsControlProps) {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { section, settingId } = readSettingsLocation(
    new URLSearchParams(searchParams.toString()),
  );
  const open = section !== null;
  const dialog = useRef<HTMLDialogElement>(null);
  const searchInput = useRef<HTMLInputElement>(null);
  const scrollArea = useRef<HTMLDivElement>(null);
  const launcher = useRef<HTMLButtonElement>(null);
  const tabButtons = useRef(new Map<SettingsSection, HTMLButtonElement>());
  const searchIdentity = JSON.stringify([pathname, section, settingId]);
  const [search, setSearch] = useState({ identity: searchIdentity, value: "" });
  // A new deep link must not retain a filter that hides its focus target.
  const query = search.identity === searchIdentity ? search.value : "";
  function setQuery(value: string) {
    setSearch({ identity: searchIdentity, value });
  }
  const [mounted, setMounted] = useState(false);
  const id = useId();
  const searching = query.trim().length > 0;
  const definitions = searching
    ? findSettings(query)
    : SETTINGS_DEFINITIONS.filter((setting) => setting.section === section);

  function select(next: SettingsSection | null) {
    // Read current browser URL to avoid clobbering a newer query/hash after a
    // rapid repeated click while a router transition is still pending.
    const current = new URL(window.location.href);
    router.replace(
      settingsHref(current.pathname, current.searchParams, next, current.hash),
      { scroll: false },
    );
    setQuery("");
  }

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    setSearch((previous) =>
      previous.identity === searchIdentity
        ? previous
        : { identity: searchIdentity, value: "" },
    );
  }, [searchIdentity]);

  useEffect(() => {
    const node = dialog.current;
    if (!node) return;
    if (open && !node.open) node.showModal();
    if (!open && node.open) {
      node.close();
      setQuery("");
      // A deep link has no previous launcher focus for the browser to restore.
      const target = launcher.current;
      if (
        target &&
        target.getClientRects().length &&
        !target.closest("[inert]")
      ) {
        target.focus({ preventScroll: true });
      } else {
        document.getElementById("main-content")?.focus({ preventScroll: true });
      }
    }
  }, [open, mounted]);

  useEffect(() => {
    scrollArea.current?.scrollTo({ top: 0 });
    if (!open || !settingId) return;
    const target = Array.from(
      dialog.current?.querySelectorAll<HTMLElement>("[data-setting-id]") ?? [],
    ).find((element) => element.dataset.settingId === settingId);
    target?.focus({ preventScroll: true });
    target?.scrollIntoView({ block: "nearest" });
  }, [open, section, settingId, pathname, mounted]);

  useEffect(() => {
    const node = dialog.current;
    return () => {
      if (node?.open) node.close();
    };
  }, [mounted]);

  useEffect(() => {
    if (!open || !mounted) return;
    return lockBodyScroll();
  }, [open, mounted]);

  function trapFocus(event: KeyboardEvent<HTMLDialogElement>) {
    if (event.key === "Escape") {
      // Search inputs can consume Escape to clear their value instead of
      // dispatching the dialog's native cancel event. Own dismissal here and
      // keep the same key from reaching the shell or Live window listeners.
      event.preventDefault();
      event.stopPropagation();
      select(null);
      return;
    }
    if (event.key !== "Tab") return;
    const controls = Array.from(
      dialog.current?.querySelectorAll<HTMLElement>(
        'button:not([disabled]):not([tabindex="-1"]), input:not([disabled]), [tabindex="0"]',
      ) ?? [],
    ).filter((element) => element.getClientRects().length > 0);
    const first = controls[0];
    const last = controls.at(-1);
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last?.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first?.focus();
    }
  }

  function navigateTabs(
    event: KeyboardEvent<HTMLButtonElement>,
    current: SettingsSection,
  ) {
    const index = SETTINGS_SECTIONS.findIndex((item) => item.id === current);
    let next: number;
    if (event.key === "ArrowRight")
      next = (index + 1) % SETTINGS_SECTIONS.length;
    else if (event.key === "ArrowLeft")
      next = (index - 1 + SETTINGS_SECTIONS.length) % SETTINGS_SECTIONS.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = SETTINGS_SECTIONS.length - 1;
    else return;
    event.preventDefault();
    const target = SETTINGS_SECTIONS[next].id;
    select(target);
    tabButtons.current.get(target)?.focus();
  }

  return (
    <NotificationSettingsProvider
      adapter={notificationAdapter}
      open={open}
      sessionKey={notificationSessionKey}
    >
      <button
        className={launcherClassName ?? styles.launcher}
        type="button"
        ref={launcher}
        aria-label="Open settings"
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={`${id}-dialog`}
        onClick={() => select("notifications")}
      >
        <SettingsIcon />
        <span>Settings</span>
      </button>
      {mounted
        ? createPortal(
            <dialog
              ref={dialog}
              id={`${id}-dialog`}
              className={styles.dialog}
              aria-labelledby={`${id}-title`}
              aria-describedby={`${id}-description`}
              onKeyDown={trapFocus}
              onCancel={(event) => {
                event.preventDefault();
                select(null);
              }}
              onClick={(event) => {
                if (event.target === event.currentTarget) select(null);
              }}
            >
              <div className={styles.frame}>
                <header className={styles.header}>
                  <div className={styles.heading}>
                    <div>
                      <h2 id={`${id}-title`}>Settings</h2>
                      <span className={styles.badge}>
                        <NotificationSettingsModeLabel fallback="Device privacy preference" />
                      </span>
                    </div>
                    <button
                      type="button"
                      className={styles.close}
                      aria-label="Close settings"
                      autoFocus
                      onClick={() => select(null)}
                    >
                      ×
                    </button>
                  </div>
                  <div
                    className={styles.tabs}
                    role="tablist"
                    aria-label="Settings sections"
                  >
                    {SETTINGS_SECTIONS.map((item) => (
                      <button
                        type="button"
                        role="tab"
                        key={item.id}
                        ref={(node) => {
                          if (node) tabButtons.current.set(item.id, node);
                          else tabButtons.current.delete(item.id);
                        }}
                        id={`${id}-tab-${item.id}`}
                        aria-controls={`${id}-panel`}
                        aria-selected={section === item.id}
                        tabIndex={section === item.id ? 0 : -1}
                        onClick={() => select(item.id)}
                        onKeyDown={(event) => navigateTabs(event, item.id)}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>
                  <div className={styles.search}>
                    <label className="sr-only" htmlFor={`${id}-search`}>
                      Search settings
                    </label>
                    <input
                      ref={searchInput}
                      id={`${id}-search`}
                      type="search"
                      placeholder="Search settings"
                      autoComplete="off"
                      spellCheck={false}
                      maxLength={200}
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                    />
                    {query && (
                      <button
                        type="button"
                        aria-label="Clear settings search"
                        onClick={() => {
                          setQuery("");
                          searchInput.current?.focus();
                        }}
                      >
                        Clear
                      </button>
                    )}
                  </div>
                </header>
                <div ref={scrollArea} className={styles.content}>
                  <NotificationSettingsStatus
                    descriptionId={`${id}-description`}
                    fallback={
                      <p className={styles.notice} id={`${id}-description`}>
                        These settings are mapped from captured client code.
                        Account values are unavailable, not off. The
                        external-link choice is stored on this browser and applies
                        to Create draft preview links only. No browser permission
                        is requested.
                      </p>
                    }
                  />
                  <div
                    role="tabpanel"
                    id={`${id}-panel`}
                    aria-labelledby={
                      section ? `${id}-tab-${section}` : undefined
                    }
                    tabIndex={0}
                  >
                    {searching ? (
                      <section aria-label="Settings search results">
                        <p className={styles.resultCount} role="status">
                          {definitions.length}{" "}
                          {definitions.length === 1 ? "setting" : "settings"}{" "}
                          found
                        </p>
                        {definitions.length ? (
                          <SettingGroups settings={definitions} search />
                        ) : (
                          <div className={styles.empty}>
                            <h3>No matching settings</h3>
                            <p>
                              Try a term such as messages, language or privacy.
                              Only the mapped settings are searchable.
                            </p>
                          </div>
                        )}
                      </section>
                    ) : (
                      <>
                        {definitions.length ? (
                          <SettingGroups settings={definitions} />
                        ) : (
                          <div className={styles.empty}>
                            <h3>This section is not reconstructed</h3>
                            <p>
                              The section name is captured, but its controls and
                              preference adapters are not implemented in this
                              local interface.
                            </p>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
                <footer className={styles.footer}>
                  <p>
                    Device privacy choice only · account settings unavailable
                  </p>
                  <button type="button" onClick={() => select(null)}>
                    Done
                  </button>
                </footer>
              </div>
            </dialog>,
            document.body,
          )
        : null}
    </NotificationSettingsProvider>
  );
}

/** Mount once in the shared shell. Its own Suspense boundary contains URL hooks. */
export default function SettingsControl(props: SettingsControlProps = {}) {
  return (
    <Suspense
      fallback={
        <button
          type="button"
          className={props.launcherClassName ?? styles.launcher}
          aria-label="Open settings"
          disabled
        >
          <SettingsIcon />
          <span>Settings</span>
        </button>
      }
    >
      <SettingsControlContent {...props} />
    </Suspense>
  );
}
