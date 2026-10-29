"use client";

import {
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
  type Ref,
} from "react";
import {
  VideoDraftSession,
  type VideoPreview,
  type VideoSelection,
  type VideoState,
} from "./create-video-preview";
import styles from "./create-video-input.module.css";

export type VideoInputControl = {
  cancelPending(): void;
  chooseFile(file: File): boolean;
};
export default function CreateVideoInput({
  onSelect,
  onRemove,
  controlRef,
}: {
  onSelect(value: VideoSelection): void;
  onRemove(owner: VideoPreview): void;
  controlRef: Ref<VideoInputControl>;
}) {
  const [state, setState] = useState<VideoState>({
    preview: null,
    selected: 0,
    pending: false,
    error: "",
  });
  const callbacks = useRef({ onSelect, onRemove });
  callbacks.current = { onSelect, onRemove };
  const session = useRef<VideoDraftSession | null>(null);
  useImperativeHandle(
    controlRef,
    () => ({
      cancelPending: () => session.current?.cancelPending(),
      chooseFile: (file) => {
        if (!session.current) return false;
        void session.current.choose(file);
        return true;
      },
    }),
    [],
  );
  useEffect(() => {
    const current = new VideoDraftSession(
      setState,
      (value) => callbacks.current.onSelect(value),
      (owner) => callbacks.current.onRemove(owner),
    );
    session.current = current;
    return () => {
      current.dispose();
      session.current = null;
    };
  }, []);
  return (
    <fieldset className="create-fieldset">
      <legend>
        Video and cover <span>Optional · local only</span>
      </legend>
      <p className="fieldset-description" id="video-hint">
        Choose a local MP4 or WebM up to 10 MB. This browser generates three
        JPEG covers; the first becomes the draft image. Nothing is uploaded or
        published. Codec support varies. Rejected videos leave your current
        image unchanged.
      </p>
      <label htmlFor="create-video">Local video</label>
      <input
        id="create-video"
        className={styles.input}
        type="file"
        accept="video/mp4,video/webm,.mp4,.webm"
        aria-describedby={`video-hint${state.error ? " video-error" : ""}`}
        aria-invalid={Boolean(state.error)}
        onChange={(event) => {
          const file = event.currentTarget.files?.[0];
          event.currentTarget.value = "";
          if (file) void session.current?.choose(file);
        }}
      />
      <p role="status">
        {state.pending ? "Preparing local video covers…" : ""}
      </p>
      {state.error ? (
        <p className="create-field-error" id="video-error" role="alert">
          {state.error}
        </p>
      ) : null}
      {state.preview ? (
        <div className={styles.preview}>
          <p>
            {state.preview.file.name} ·{" "}
            {(state.preview.file.size / 1_000).toLocaleString()} KB · not
            uploaded
          </p>
          <video
            src={state.preview.url}
            controls
            muted
            playsInline
            preload="metadata"
            aria-label="Local draft video preview"
          />
          <div
            className={styles.covers}
            role="group"
            aria-label="Video cover choices"
          >
            {state.preview.covers.map((cover, index) => (
              <button
                type="button"
                key={cover.url}
                aria-pressed={state.selected === index}
                onClick={() => session.current?.select(index)}
              >
                {/* Local object URL only; do not use a network image optimizer. */}
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={cover.url}
                  alt={`Cover ${index + 1} at ${cover.seconds.toFixed(2)} seconds`}
                />
                Cover {index + 1}
              </button>
            ))}
          </div>
          <p>
            A selected JPEG is the separate coin image. You can replace it with
            a manual image above.
          </p>
        </div>
      ) : null}
      {state.preview || state.pending ? (
        <button
          className="reset-button"
          type="button"
          onClick={() => session.current?.clear()}
        >
          Remove video / cancel preparation
        </button>
      ) : null}
    </fieldset>
  );
}
