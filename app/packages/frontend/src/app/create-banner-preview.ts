/** Local browser preview only. These extra allocation/time bounds are LOCAL DESIGN. */
export const BANNER_BYTES = 4_500_000;
export const BANNER_MAX_PIXELS = 16_777_216;
export const BANNER_TIMEOUT_MS = 10_000;
export const BANNER_TYPES = [
  "image/jpeg",
  "image/png",
  "image/gif",
  "image/webp",
] as const;

export function validateBanner(file: File): string | undefined {
  if (!BANNER_TYPES.includes(file.type as (typeof BANNER_TYPES)[number]))
    return "Choose a JPEG, PNG, GIF or WebP banner.";
  if (
    !Number.isSafeInteger(file.size) ||
    file.size <= 0 ||
    file.size > BANNER_BYTES
  )
    return "Choose a non-empty banner of at most 4.5 MB (4,500,000 bytes).";
  return undefined;
}

export type BannerPreview = Readonly<{
  file: File;
  url: string;
  width: number;
  height: number;
  dispose(): void;
}>;
export type BannerState = Readonly<{
  preview: BannerPreview | null;
  pending: boolean;
  error: string;
}>;
export const EMPTY_BANNER: BannerState = {
  preview: null,
  pending: false,
  error: "",
};
export type BannerPlatform = {
  image(): HTMLImageElement;
  url(file: File): string;
  revoke(url: string): void;
};
const browser: BannerPlatform = {
  image: () => new Image(),
  url: (file) => URL.createObjectURL(file),
  revoke: (url) => URL.revokeObjectURL(url),
};
const aborted = () =>
  new DOMException("Banner preview cancelled.", "AbortError");

export async function prepareBanner(
  file: File,
  signal: AbortSignal,
  platform: BannerPlatform = browser,
): Promise<BannerPreview> {
  const invalid = validateBanner(file);
  if (invalid) throw new Error(invalid);
  if (signal.aborted) throw aborted();
  const image = platform.image();
  const url = platform.url(file);
  let disposed = false;
  const dispose = () => {
    if (disposed) return;
    disposed = true;
    try {
      image.removeAttribute("src");
    } finally {
      platform.revoke(url);
    }
  };
  try {
    await new Promise<void>((resolve, reject) => {
      let settled = false;
      const finish = (error?: Error) => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        signal.removeEventListener("abort", cancel);
        image.onload = null;
        image.onerror = null;
        if (error) reject(error);
        else resolve();
      };
      const cancel = () => finish(aborted());
      const timer = setTimeout(
        () => finish(new Error("Banner preview timed out.")),
        BANNER_TIMEOUT_MS,
      );
      signal.addEventListener("abort", cancel, { once: true });
      image.onload = () => finish();
      image.onerror = () =>
        finish(new Error("The browser could not decode this banner file."));
      try {
        image.decoding = "async";
        image.src = url;
      } catch {
        finish(new Error("The browser could not decode this banner file."));
      }
    });
    if (signal.aborted) throw aborted();
    const width = image.naturalWidth,
      height = image.naturalHeight;
    if (
      !Number.isSafeInteger(width) ||
      !Number.isSafeInteger(height) ||
      width <= 0 ||
      height <= 0 ||
      width > BANNER_MAX_PIXELS / height
    )
      throw new Error(
        "Banner dimensions exceed this local preview's 16-megapixel bound.",
      );
    return Object.freeze({ file, url, width, height, dispose });
  } catch (error) {
    dispose();
    throw error;
  }
}

type Prepare = (file: File, signal: AbortSignal) => Promise<BannerPreview>;
/** One owner for accepted URLs; superseded decode completions cannot replace newer state. */
export class BannerDraftSession {
  private current: BannerPreview | null = null;
  private controller: AbortController | null = null;
  private revision = 0;
  private disposed = false;
  private publish: (state: BannerState) => void;
  private prepare: Prepare;
  constructor(
    publish: (state: BannerState) => void,
    prepare: Prepare = prepareBanner,
  ) {
    this.publish = publish;
    this.prepare = prepare;
  }
  async choose(file: File): Promise<void> {
    if (this.disposed) return;
    const revision = ++this.revision;
    this.controller?.abort();
    this.controller = null;
    const error = validateBanner(file);
    if (error) {
      this.publish({ preview: this.current, pending: false, error });
      return;
    }
    const controller = new AbortController();
    this.controller = controller;
    this.publish({ preview: this.current, pending: true, error: "" });
    try {
      const preview = await this.prepare(file, controller.signal);
      if (this.disposed || revision !== this.revision) {
        preview.dispose();
        return;
      }
      const previous = this.current;
      this.current = preview;
      this.controller = null;
      this.publish({ preview, pending: false, error: "" });
      previous?.dispose();
    } catch (reason) {
      if (this.disposed || revision !== this.revision) return;
      this.controller = null;
      this.publish({
        preview: this.current,
        pending: false,
        error:
          reason instanceof Error ? reason.message : "Banner preview failed.",
      });
    }
  }
  clear(): void {
    if (this.disposed) return;
    this.revision++;
    this.controller?.abort();
    this.controller = null;
    this.current?.dispose();
    this.current = null;
    this.publish(EMPTY_BANNER);
  }
  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    this.revision++;
    this.controller?.abort();
    this.controller = null;
    this.current?.dispose();
    this.current = null;
  }
}
