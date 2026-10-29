"use client";

import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { lockBodyScroll } from "@/lib/body-scroll-lock";
import type { CompetitionSummary } from "./types";
import {
  competitionRules,
  competitionRulesCopy as copy,
  COMPETITION_TERMS_URL,
} from "./competition-rules-model";
import styles from "./competition-rules.module.css";

/** Mounted only for a selected, admitted competition; no request or auth adapter. */
export function CompetitionRules({
  competition,
}: {
  competition: CompetitionSummary;
}) {
  const [host, setHost] = useState<HTMLElement | null>(null);
  const [open, setOpen] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  const launcher = useRef<HTMLButtonElement>(null);
  const titleId = useId();
  const boundaryId = useId();
  const model = competitionRules(competition);

  useEffect(() => {
    setHost(document.body);
  }, []);

  useEffect(() => {
    const element = dialog.current;
    return () => {
      if (element?.open) element.close();
    };
  }, [host]);

  useEffect(() => {
    if (!open) return;
    return lockBodyScroll();
  }, [open]);

  return (
    <>
      <button
        className={styles.launcher}
        type="button"
        ref={launcher}
        aria-haspopup="dialog"
        aria-expanded={open}
        disabled={!host}
        onClick={() => {
          const element = dialog.current;
          if (
            !element ||
            element.open ||
            document.querySelector("dialog[open]")
          )
            return;
          element.showModal();
          setOpen(true);
        }}
      >
        {copy.open}
      </button>
      {host &&
        createPortal(
          <dialog
            ref={dialog}
            className={styles.dialog}
            aria-labelledby={titleId}
            aria-describedby={boundaryId}
            data-testid="cup-rules-dialog"
            onKeyDown={(event) => {
              // This modal owns Escape; preserve native cancel/close, not shell shortcuts.
              if (event.key === "Escape") event.stopPropagation();
              if (event.key !== "Tab") return;
              const controls = Array.from(
                event.currentTarget.querySelectorAll<HTMLElement>(
                  'button:not([disabled]), a[href], [tabindex="0"]',
                ),
              ).filter(
                (control) =>
                  control.tabIndex >= 0 && control.getClientRects().length > 0,
              );
              const first = controls[0];
              const last = controls.at(-1);
              // Native modal inertness does not stop Tab from reaching browser chrome.
              if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last?.focus();
              } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first?.focus();
              }
            }}
            onClose={() => {
              setOpen(false);
              if (
                launcher.current?.isConnected &&
                !document.querySelector("dialog[open]")
              )
                launcher.current.focus();
            }}
          >
            <header className={styles.header}>
              <h2 id={titleId}>{copy.title}</h2>
              <button
                type="button"
                autoFocus
                onClick={() => dialog.current?.close()}
              >
                {copy.close}
              </button>
            </header>
            <div className={styles.content}>
              <p className={styles.boundary} id={boundaryId}>
                Read-only reconstruction of captured competition rules. Times
                shown in UTC. Registration, eligibility checks and prize claims
                are not available here.
              </p>
              <p className={styles.title}>{model.title}</p>
              <section>
                <h3>{copy.schedule}</h3>
                <dl>
                  {model.schedule.map((row) => (
                    <div className={styles.row} key={row.label}>
                      <dt>{row.label}</dt>
                      <dd>{row.range}</dd>
                    </div>
                  ))}
                </dl>
              </section>
              <section>
                <h3>{copy.scoring}</h3>
                <p>{model.scoring}</p>
              </section>
              <section>
                <h3>{copy.entry}</h3>
                <p>{model.entry}</p>
                {model.entryCap && <p>{model.entryCap}</p>}
              </section>
              {model.prizes.length > 0 && (
                <section>
                  <h3>{copy.prize_breakdown}</h3>
                  {model.prizeCopy && <p>{model.prizeCopy}</p>}
                  <dl>
                    {model.prizes.map((prize, index) => (
                      <div className={styles.row} key={index}>
                        <dt>{prize.label}</dt>
                        <dd>{prize.amount}</dd>
                      </div>
                    ))}
                  </dl>
                  {model.paidRanks && <p>{model.paidRanks}</p>}
                </section>
              )}
              <section>
                <h3>{copy.list}</h3>
                <ol data-testid="cup-rules-list">
                  {model.rules.map((rule, index) => (
                    <li key={index}>{rule}</li>
                  ))}
                </ol>
              </section>
              <a
                href={COMPETITION_TERMS_URL}
                target="_blank"
                rel="noopener noreferrer"
                data-testid="cup-rules-terms"
              >
                {copy.terms_link}
              </a>
            </div>
          </dialog>,
          host,
        )}
    </>
  );
}
