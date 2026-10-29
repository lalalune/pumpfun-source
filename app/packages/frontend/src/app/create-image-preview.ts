export const IMAGE_PREVIEW_TIMEOUT_MS = 10_000;

/** Called after validateImage by the form. Local decode admission, not MIME authentication or original upload parity.
 * On success the caller owns the returned URL; every other path revokes it.
 */
export function prepareImagePreview(
  file: File,
  signal: AbortSignal,
): Promise<string> {
  return new Promise((resolve, reject) => {
    const cancelled = () =>
      new DOMException("Image preparation cancelled.", "AbortError");
    if (signal.aborted) return reject(cancelled());
    let image: HTMLImageElement | undefined;
    let url: string | undefined;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let settled = false;
    const finish = (error?: Error) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      signal.removeEventListener("abort", cancel);
      if (image) {
        image.onload = null;
        image.onerror = null;
        image.removeAttribute("src");
      }
      if (error) {
        if (url) URL.revokeObjectURL(url);
        reject(error);
      } else resolve(url!);
    };
    const cancel = () => finish(cancelled());
    try {
      image = new Image();
      url = URL.createObjectURL(file);
      image.onload = () => {
        if (!image!.naturalWidth || !image!.naturalHeight)
          finish(new Error("The browser could not decode this image file."));
        else finish();
      };
      image.onerror = () =>
        finish(new Error("The browser could not decode this image file."));
      signal.addEventListener("abort", cancel, { once: true });
      timer = setTimeout(
        () => finish(new Error("Image preparation timed out.")),
        IMAGE_PREVIEW_TIMEOUT_MS,
      );
      image.src = url;
    } catch (error) {
      finish(
        error instanceof Error ? error : new Error("Image preparation failed."),
      );
    }
  });
}
