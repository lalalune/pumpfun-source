/** Local drop admission only: never read strings, follow URLs or traverse folders. */
export type DroppedFile = { file: File } | { error: string };

export function hasDraggedFile(
  data: Pick<DataTransfer, "items" | "types">,
): boolean {
  for (let index = 0; index < data.items.length; index++) {
    if (data.items[index].kind === "file") return true;
  }
  return Array.from(data.types).includes("Files");
}

export function readDroppedFile(
  data: Pick<DataTransfer, "items" | "files">,
): DroppedFile {
  let item: DataTransferItem | undefined;
  for (let index = 0; index < data.items.length; index++) {
    if (data.items[index].kind !== "file") continue;
    if (item) return { error: "Drop exactly one image or video at a time." };
    item = data.items[index];
  }
  if (data.files.length > 1) {
    return { error: "Drop exactly one image or video at a time." };
  }
  try {
    if (item) {
      // This synchronous directory check does not enumerate or read entries.
      const entry = item.webkitGetAsEntry?.();
      if (entry?.isDirectory) return { error: "Choose a file, not a folder." };
      const file = item.getAsFile();
      return file
        ? { file }
        : {
            error:
              "This dropped file could not be read. Use a file control below.",
          };
    }
    // Older browser ports may expose only FileList. It still must be one file.
    if (data.files.length === 1) return { file: data.files[0] };
  } catch {
    return {
      error: "This dropped file could not be read. Use a file control below.",
    };
  }
  return { error: "Drop a local image or video file, not text or a link." };
}
