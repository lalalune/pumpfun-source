/** Offline browser decoding only. No upload, fetch, SDK, wallet or provider API. */
export const VIDEO_BYTES = 10_000_000;
export const VIDEO_TIMEOUT_MS = 30_000;
export const VIDEO_MAX_PIXELS = 16_777_216; // Local allocation policy, not an upstream limit.
export const COVER_MAX_EDGE = 1_280;
export const COVER_MAX_BYTES = 4_500_000;

export function validateVideo(file: File): string | undefined {
  const extension = /\.(mp4|webm)$/i.exec(file.name)?.[1].toLowerCase();
  if (!extension || (file.type && file.type !== `video/${extension}`))
    return "Choose an MP4 or WebM video with a matching media type.";
  if (
    !Number.isSafeInteger(file.size) ||
    file.size <= 0 ||
    file.size > VIDEO_BYTES
  )
    return "Choose a non-empty video of at most 10 MB (10,000,000 bytes).";
  return undefined;
}

export function coverTimes(duration: number): number[] {
  const times = [1, 2, 3].map((n) => (duration / 4) * n);
  if (
    !Number.isFinite(duration) ||
    duration <= 0 ||
    times.some((n) => !Number.isFinite(n) || n <= 0 || n >= duration) ||
    new Set(times).size !== 3
  )
    throw new Error("This video does not have a usable finite duration.");
  return times;
}

export type VideoPlatform = {
  video(): HTMLVideoElement;
  canvas(): HTMLCanvasElement;
  url(blob: Blob): string;
  revoke(url: string): void;
};
export type VideoPreview = {
  readonly file: File;
  readonly url: string;
  readonly covers: readonly {
    readonly file: File;
    readonly url: string;
    readonly seconds: number;
  }[];
  dispose(): void;
};
const browser: VideoPlatform = {
  video: () => document.createElement("video"),
  canvas: () => document.createElement("canvas"),
  url: (blob) => URL.createObjectURL(blob),
  revoke: (url) => URL.revokeObjectURL(url),
};
const aborted = () =>
  new DOMException("Video preparation cancelled.", "AbortError");

export async function prepareVideo(
  file: File,
  signal: AbortSignal,
  platform: VideoPlatform = browser,
  timeoutMs = VIDEO_TIMEOUT_MS,
): Promise<VideoPreview> {
  const error = validateVideo(file);
  if (error) throw new Error(error);
  if (signal.aborted) throw aborted();
  if (
    !Number.isFinite(timeoutMs) ||
    timeoutMs <= 0 ||
    timeoutMs > VIDEO_TIMEOUT_MS
  )
    throw new Error("Invalid local video timeout.");
  const deadline = Date.now() + timeoutMs;
  const video = platform.video();
  const urls: string[] = [];
  let canvas: HTMLCanvasElement | undefined;
  let disposed = false;
  const dispose = () => {
    if (disposed) return;
    disposed = true;
    signal.removeEventListener("abort", dispose);
    for (const url of urls) platform.revoke(url);
  };
  signal.addEventListener("abort", dispose, { once: true });
  const active = () => {
    if (signal.aborted || disposed) throw aborted();
    if (Date.now() >= deadline) throw new Error("Video preparation timed out.");
  };
  function stage<T>(
    start: (done: (value: T) => void, fail: (error: Error) => void) => void,
    cleanup: () => void = () => {},
  ): Promise<T> {
    active();
    return new Promise((resolve, reject) => {
      let settled = false;
      const finish = (error?: Error, result?: T) => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        signal.removeEventListener("abort", cancel);
        cleanup();
        if (error) reject(error);
        else resolve(result as T);
      };
      const cancel = () => finish(aborted());
      const timer = setTimeout(
        () => finish(new Error("Video preparation timed out.")),
        deadline - Date.now(),
      );
      signal.addEventListener("abort", cancel, { once: true });
      try {
        start(
          (value) => finish(undefined, value),
          (error) => finish(error),
        );
      } catch (error) {
        finish(
          error instanceof Error ? error : new Error("Video decoding failed."),
        );
      }
    });
  }
  function event(name: "loadedmetadata" | "seeked", action: () => void) {
    let done: EventListener;
    let failed: EventListener;
    return stage<void>(
      (resolve, reject) => {
        done = () => resolve();
        failed = () =>
          reject(
            new Error("The browser could not decode this video or codec."),
          );
        video.addEventListener(name, done);
        video.addEventListener("error", failed);
        action();
      },
      () => {
        video.removeEventListener(name, done);
        video.removeEventListener("error", failed);
      },
    );
  }
  try {
    video.preload = "metadata";
    video.muted = true;
    video.playsInline = true;
    const url = platform.url(file);
    urls.push(url);
    await event("loadedmetadata", () => {
      video.src = url;
      video.load();
    });
    active();
    const times = coverTimes(video.duration);
    const width = video.videoWidth,
      height = video.videoHeight;
    if (
      !Number.isSafeInteger(width) ||
      !Number.isSafeInteger(height) ||
      width <= 0 ||
      height <= 0 ||
      width > VIDEO_MAX_PIXELS / height
    )
      throw new Error(
        "Video dimensions exceed this local preview's 16-megapixel bound.",
      );
    canvas = platform.canvas();
    const scale = Math.min(1, COVER_MAX_EDGE / Math.max(width, height));
    canvas.width = Math.max(1, Math.round(width * scale));
    canvas.height = Math.max(1, Math.round(height * scale));
    const context = canvas.getContext("2d");
    if (!context)
      throw new Error("The browser cannot create video cover images.");
    const covers: { file: File; url: string; seconds: number }[] = [];
    for (const seconds of times) {
      active();
      await event("seeked", () => {
        video.currentTime = seconds;
      });
      active();
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      const blob = await stage<Blob>((done, fail) =>
        canvas!.toBlob(
          (value) =>
            value
              ? done(value)
              : fail(new Error("The browser could not encode a video cover.")),
          "image/jpeg",
          0.8,
        ),
      );
      active();
      if (
        blob.type !== "image/jpeg" ||
        blob.size <= 0 ||
        blob.size > COVER_MAX_BYTES
      )
        throw new Error(
          "The generated JPEG cover is empty, unsupported or larger than 4.5 MB.",
        );
      const cover = new File([blob], `video-cover-${covers.length + 1}.jpg`, {
        type: "image/jpeg",
      });
      const coverUrl = platform.url(cover);
      urls.push(coverUrl);
      covers.push(Object.freeze({ file: cover, url: coverUrl, seconds }));
    }
    return Object.freeze({ file, url, covers: Object.freeze(covers), dispose });
  } catch (error) {
    dispose();
    throw error;
  } finally {
    // Best-effort decoder teardown must not mask the result or skip URL ownership cleanup.
    try {
      video.pause();
    } catch {}
    try {
      video.removeAttribute("src");
      video.load();
    } catch {}
    if (canvas) {
      canvas.width = 0;
      canvas.height = 0;
    }
  }
}

export type VideoState = {
  preview: VideoPreview | null;
  selected: number;
  pending: boolean;
  error: string;
};
export type VideoSelection = { video: File; cover: File; owner: VideoPreview };
export function discardVideoCover<T extends { videoOwner?: VideoPreview }>(
  image: T | null,
  owner: VideoPreview,
): T | null {
  return image?.videoOwner === owner ? null : image;
}

/** Owns pending and committed resources separately; failed replacements preserve the draft. */
export class VideoDraftSession {
  private revision = 0;
  private pending?: AbortController;
  private disposed = false;
  private state: VideoState = {
    preview: null,
    selected: 0,
    pending: false,
    error: "",
  };
  private readonly changed: (state: VideoState) => void;
  private readonly selected: (value: VideoSelection) => void;
  private readonly removed: (owner: VideoPreview) => void;
  private readonly prepare: typeof prepareVideo;
  constructor(
    changed: (state: VideoState) => void,
    selected: (value: VideoSelection) => void,
    removed: (owner: VideoPreview) => void,
    prepare = prepareVideo,
  ) {
    this.changed = changed;
    this.selected = selected;
    this.removed = removed;
    this.prepare = prepare;
  }
  private publish(update: Partial<VideoState>) {
    this.state = { ...this.state, ...update };
    if (!this.disposed) this.changed(this.state);
  }
  async choose(file: File) {
    if (this.disposed) return;
    const revision = ++this.revision;
    this.pending?.abort();
    const pending = new AbortController();
    this.pending = pending;
    this.publish({ pending: true, error: "" });
    try {
      const preview = await this.prepare(file, pending.signal);
      if (this.disposed || revision !== this.revision) {
        preview.dispose();
        return;
      }
      const previous = this.state.preview;
      this.publish({ preview, selected: 0, pending: false });
      // Observers may clear or dispose the draft synchronously while publishing.
      if (!this.disposed && this.state.preview === preview) {
        this.selected({
          video: file,
          cover: preview.covers[0].file,
          owner: preview,
        });
      }
      previous?.dispose();
    } catch (error) {
      if (!this.disposed && revision === this.revision)
        this.publish({
          pending: false,
          error:
            error instanceof Error
              ? error.message
              : "Video preparation failed.",
        });
    } finally {
      if (revision === this.revision) this.pending = undefined;
    }
  }
  select(index: number) {
    const preview = this.state.preview;
    if (
      this.disposed ||
      !preview ||
      !Number.isInteger(index) ||
      !preview.covers[index]
    )
      return;
    this.cancelPending();
    this.publish({ selected: index });
    this.selected({
      video: preview.file,
      cover: preview.covers[index].file,
      owner: preview,
    });
  }
  cancelPending() {
    this.cancelPreparation();
  }
  cancelPreparation() {
    if (this.disposed || !this.pending) return;
    ++this.revision;
    this.pending.abort();
    this.pending = undefined;
    this.publish({ pending: false, error: "" });
  }
  clear() {
    if (this.disposed) return;
    ++this.revision;
    this.pending?.abort();
    this.pending = undefined;
    const previous = this.state.preview;
    this.publish({ preview: null, selected: 0, pending: false, error: "" });
    if (previous) {
      this.removed(previous);
      previous.dispose();
    }
  }
  dispose() {
    if (this.disposed) return;
    this.disposed = true;
    ++this.revision;
    this.pending?.abort();
    this.state.preview?.dispose();
  }
}
