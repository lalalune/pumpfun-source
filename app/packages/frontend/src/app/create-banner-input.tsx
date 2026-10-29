"use client";

import { useEffect, useRef } from "react";
import {
  BannerDraftSession,
  BANNER_TYPES,
  type BannerState,
} from "./create-banner-preview";
import styles from "./create-banner-input.module.css";

export default function CreateBannerInput({
  state,
  onChange,
}: {
  state: BannerState;
  onChange(state: BannerState): void;
}) {
  const publish = useRef(onChange);
  publish.current = onChange;
  const session = useRef<BannerDraftSession | null>(null);
  useEffect(() => {
    const current = new BannerDraftSession((next) => publish.current(next));
    session.current = current;
    return () => {
      current.dispose();
      session.current = null;
    };
  }, []);
  return (
    <details className={styles.details}>
      <summary>
        Add banner <span>Optional · local only</span>
      </summary>
      <div className={styles.content}>
        <p id="banner-hint" className="create-field-hint">
          Select one JPEG, PNG, GIF or WebP of at most 4.5 MB for this local
          draft. A 3:1 image (1500 × 500 pixels) is recommended, not required.
          Files are not resized, uploaded or published. Rejected files keep the
          previous banner.
        </p>
        <label htmlFor="create-banner">Local banner image</label>
        <input
          id="create-banner"
          type="file"
          accept={BANNER_TYPES.join(",")}
          aria-describedby={`banner-hint${state.error ? " banner-error" : ""}`}
          aria-invalid={Boolean(state.error)}
          onChange={(event) => {
            const file = event.currentTarget.files?.[0];
            event.currentTarget.value = "";
            if (file) void session.current?.choose(file);
          }}
        />
        <p role="status">
          {state.pending ? "Preparing local banner preview…" : ""}
        </p>
        {state.error ? (
          <p role="alert" id="banner-error" className="create-field-error">
            {state.error}
          </p>
        ) : null}
        {state.preview ? (
          <div data-testid="selected-banner">
            <p>
              {state.preview.file.name} · {state.preview.file.type} ·{" "}
              {state.preview.file.size.toLocaleString()} bytes ·{" "}
              {state.preview.width} × {state.preview.height} pixels · not
              uploaded
            </p>
            {/* A local object URL must not invoke a network image optimizer. */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              className={styles.preview}
              src={state.preview.url}
              alt="Local draft banner preview"
            />
            <p className="create-field-hint">
              Preview frame is 3:1; the original file is unchanged.
            </p>
          </div>
        ) : null}
        {state.preview || state.pending || state.error ? (
          <button
            type="button"
            className="reset-button"
            onClick={() => session.current?.clear()}
          >
            Remove banner / cancel preparation
          </button>
        ) : null}
      </div>
    </details>
  );
}
