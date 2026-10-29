"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { validateImage } from "./create-coin-validation";
import { hasDraggedFile, readDroppedFile } from "./create-media-drop";
import { validateVideo } from "./create-video-preview";
import styles from "./create-media-dropzone.module.css";

export default function CreateMediaDropzone({
  onImage,
  onVideo,
}: {
  onImage(file: File): void;
  onVideo(file: File): boolean;
}) {
  const depth = useRef(0);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");
  const clearDrag = useCallback(() => {
    depth.current = 0;
    setDragging(false);
  }, []);
  useEffect(() => {
    window.addEventListener("blur", clearDrag);
    window.addEventListener("dragend", clearDrag);
    return () => {
      window.removeEventListener("blur", clearDrag);
      window.removeEventListener("dragend", clearDrag);
    };
  }, [clearDrag]);

  return (
    <div
      className={styles.dropzone}
      data-dragging={dragging}
      role="region"
      aria-label="Drop local coin media"
      aria-describedby="media-drop-hint"
      onDragEnter={(event) => {
        event.preventDefault();
        if (hasDraggedFile(event.dataTransfer)) {
          depth.current++;
          setDragging(true);
        }
      }}
      onDragOver={(event) => {
        // Prevent native file/URL navigation only inside this explicit drop surface.
        event.preventDefault();
        event.dataTransfer.dropEffect = hasDraggedFile(event.dataTransfer)
          ? "copy"
          : "none";
      }}
      onDragLeave={(event) => {
        event.preventDefault();
        depth.current = Math.max(0, depth.current - 1);
        if (depth.current === 0) setDragging(false);
      }}
      onDrop={(event) => {
        event.preventDefault();
        event.stopPropagation();
        clearDrag();
        setError("");
        const selection = readDroppedFile(event.dataTransfer);
        if ("error" in selection) {
          setError(selection.error);
          return;
        }
        const file = selection.file;
        if (file.type.startsWith("image/")) {
          const message = validateImage(file);
          if (message) setError(message);
          else onImage(file);
        } else if (
          file.type.startsWith("video/") ||
          /\.(mp4|webm)$/i.test(file.name)
        ) {
          const message = validateVideo(file);
          if (message) setError(message);
          else if (!onVideo(file))
            setError(
              "Video preparation is not ready. Use the video file control below.",
            );
        } else {
          setError("Choose a JPEG, PNG, GIF, WebP, MP4 or WebM file.");
        }
      }}
    >
      <strong>
        {dragging ? "Drop one local file" : "Drag one image or video here"}
      </strong>
      <p id="media-drop-hint">
        Or use the image and video file controls below. Files stay in this tab;
        nothing is uploaded.
      </p>
      {error ? (
        <p className="create-field-error" role="alert">
          Drop rejected: {error}
        </p>
      ) : null}
    </div>
  );
}
