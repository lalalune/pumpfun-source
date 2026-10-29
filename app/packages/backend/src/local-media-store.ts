import { createHash, randomUUID } from "node:crypto";
import { constants } from "node:fs";
import { lstat, mkdir, open, rename, unlink } from "node:fs/promises";
import type { FileHandle } from "node:fs/promises";
import { join, resolve } from "node:path";

// LOCAL DESIGN: none of these URLs, errors, quotas or persistence rules model IPFS.
export const LOCAL_MEDIA_PREFIX = "/__reconstruction/media";
export const MAX_IMAGE_BYTES = 4_500_000;
export const IMAGE_TYPES = [
  "image/png",
  "image/jpeg",
  "image/gif",
  "image/webp",
] as const;
export type ImageType = (typeof IMAGE_TYPES)[number];
const ID = /^[a-f0-9]{64}$/;
const CREATED_ON = "urn:pump-reconstruction:local-media";
const TEXT_LIMITS = { name: 32, symbol: 10, description: 2000, social: 2048 };

export class LocalMediaError extends Error {
  constructor(
    public readonly code: string,
    public readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

type ImageRecord = { id: string; mime: ImageType; data: string };
export type LocalMetadata = {
  name: string;
  symbol: string;
  description: string;
  image: string;
  showName: boolean;
  createdOn: string;
  twitter?: string;
  telegram?: string;
  website?: string;
};
type MetadataRecord = { id: string; imageId: string; value: LocalMetadata };
type Snapshot = {
  version: 1;
  images: ImageRecord[];
  metadata: MetadataRecord[];
};
export type LocalMediaLimits = {
  maxBytes?: number;
  maxImages?: number;
  maxMetadata?: number;
};

function fail(code: string, message: string, status = 400): never {
  throw new LocalMediaError(code, status, message);
}
function hash(bytes: Uint8Array | string) {
  return createHash("sha256").update(bytes).digest("hex");
}
function object(value: unknown): Record<string, unknown> {
  if (
    !value ||
    typeof value !== "object" ||
    Array.isArray(value) ||
    Object.getPrototypeOf(value) !== Object.prototype
  )
    fail("LOCAL_MEDIA_INVALID", "Expected a plain object.");
  return value as Record<string, unknown>;
}
function keys(value: Record<string, unknown>, allowed: string[]) {
  if (Object.keys(value).some((key) => !allowed.includes(key)))
    fail("LOCAL_MEDIA_INVALID", "Unexpected field.");
}
function identifier(value: unknown): string {
  if (typeof value !== "string" || !ID.test(value))
    fail("LOCAL_MEDIA_INVALID_ID", "Expected a SHA-256 identifier.");
  return value;
}
function text(value: unknown, max: number, required: boolean): string {
  if (
    typeof value !== "string" ||
    value.length > max ||
    (required && !value.trim())
  ) {
    fail(
      "LOCAL_MEDIA_INVALID",
      `Expected ${required ? "nonempty " : ""}text of at most ${max} code units.`,
    );
  }
  // JSON would otherwise silently retain strings that cannot round-trip via URI encoding.
  try {
    encodeURIComponent(value);
  } catch {
    fail("LOCAL_MEDIA_INVALID", "Invalid Unicode.");
  }
  return value;
}
function social(value: unknown, field: "website" | "twitter" | "telegram") {
  if (value === undefined) return undefined;
  const result = text(value, TEXT_LIMITS.social, true).trim();
  let url: URL;
  try {
    url = new URL(result);
  } catch {
    return fail("LOCAL_MEDIA_INVALID", "Expected an HTTPS link.");
  }
  if (url.protocol !== "https:" || url.username || url.password)
    fail("LOCAL_MEDIA_INVALID", "Expected an HTTPS link without credentials.");
  if (
    field === "twitter" &&
    !["x.com", "www.x.com", "twitter.com", "www.twitter.com"].includes(
      url.hostname,
    )
  ) {
    fail("LOCAL_MEDIA_INVALID", "Expected an X/Twitter link.");
  }
  if (field === "telegram" && !["t.me", "telegram.me"].includes(url.hostname))
    fail("LOCAL_MEDIA_INVALID", "Expected a Telegram link.");
  if (field !== "website" && url.pathname === "/")
    fail("LOCAL_MEDIA_INVALID", "Include a profile or channel path.");
  return result;
}

function metadata(input: unknown): { imageId: string; value: LocalMetadata } {
  const item = object(input);
  keys(item, [
    "imageId",
    "name",
    "symbol",
    "description",
    "showName",
    "twitter",
    "telegram",
    "website",
  ]);
  const imageId = identifier(item.imageId);
  if (typeof item.showName !== "boolean")
    fail("LOCAL_MEDIA_INVALID", "showName must be a boolean.");
  const value: LocalMetadata = {
    name: text(item.name, TEXT_LIMITS.name, true),
    symbol: text(item.symbol, TEXT_LIMITS.symbol, true),
    description: text(item.description, TEXT_LIMITS.description, false),
    image: `${LOCAL_MEDIA_PREFIX}/images/${imageId}/content`,
    showName: item.showName,
    createdOn: CREATED_ON,
  };
  for (const field of ["twitter", "telegram", "website"] as const) {
    const link = social(item[field], field);
    if (link !== undefined) value[field] = link;
  }
  return { imageId, value };
}

// Signatures reject obvious MIME spoofing; this is NOT a decoder, scanner or sanitizer.
function imageType(bytes: Buffer): ImageType | undefined {
  if (
    bytes.length >= 24 &&
    bytes.subarray(0, 8).equals(Buffer.from("89504e470d0a1a0a", "hex")) &&
    bytes.subarray(12, 16).toString("ascii") === "IHDR" &&
    bytes.readUInt32BE(16) > 0 &&
    bytes.readUInt32BE(20) > 0
  )
    return "image/png";
  if (
    bytes.length >= 4 &&
    bytes[0] === 0xff &&
    bytes[1] === 0xd8 &&
    bytes[2] === 0xff
  )
    return "image/jpeg";
  if (
    bytes.length >= 10 &&
    ["GIF87a", "GIF89a"].includes(bytes.subarray(0, 6).toString("ascii")) &&
    bytes.readUInt16LE(6) > 0 &&
    bytes.readUInt16LE(8) > 0
  )
    return "image/gif";
  if (
    bytes.length >= 16 &&
    bytes.subarray(0, 4).toString("ascii") === "RIFF" &&
    bytes.subarray(8, 12).toString("ascii") === "WEBP"
  )
    return "image/webp";
  return undefined;
}
function validateImage(bytes: Buffer, mime: unknown): ImageType {
  if (!bytes.length || bytes.length > MAX_IMAGE_BYTES)
    fail(
      "LOCAL_MEDIA_IMAGE_SIZE",
      "Image must contain 1–4,500,000 bytes.",
      413,
    );
  const detected = imageType(bytes);
  if (!detected || detected !== mime)
    fail(
      "LOCAL_MEDIA_IMAGE_TYPE",
      "Image signature and declared MIME type must agree.",
      415,
    );
  return detected;
}

/** Upper bound for every canonical snapshot admitted by the record/byte quotas. */
function snapshotByteLimit(limits: Required<LocalMediaLimits>): number {
  const id = "0".repeat(64);
  const imageEnvelope = Math.max(
    ...IMAGE_TYPES.map((mime) =>
      Buffer.byteLength(JSON.stringify({ id, mime, data: "" })),
    ),
  );
  // A JSON string requires at most six UTF-8 bytes per admitted UTF-16 code unit
  // (for example, a control character serialized as \u0000). Include optional
  // fields and the longer boolean spelling, plus all fixed IDs/URI/key overhead.
  const metadataEnvelope = Buffer.byteLength(
    JSON.stringify({
      id,
      imageId: id,
      value: {
        name: "",
        symbol: "",
        description: "",
        image: `${LOCAL_MEDIA_PREFIX}/images/${id}/content`,
        showName: false,
        createdOn: CREATED_ON,
        twitter: "",
        telegram: "",
        website: "",
      },
    }),
  );
  const metadataBytes =
    metadataEnvelope +
    6 *
      (TEXT_LIMITS.name +
        TEXT_LIMITS.symbol +
        TEXT_LIMITS.description +
        3 * TEXT_LIMITS.social);
  // Every image has at least one byte. Each base64 record has its own padding;
  // rounding only the total byte quota undercounts many short images.
  const images = BigInt(Math.min(limits.maxImages, limits.maxBytes));
  const capacity = images * BigInt(MAX_IMAGE_BYTES);
  const quota = BigInt(limits.maxBytes);
  const bytes = quota < capacity ? quota : capacity;
  const encodedBytes = 4n * ((bytes + 2n * images) / 3n);
  const empty = Buffer.byteLength(
    JSON.stringify({ version: 1, images: [], metadata: [] }),
  );
  // One extra comma per record is conservative, including single-item arrays.
  const maximum =
    BigInt(empty) +
    encodedBytes +
    images * BigInt(imageEnvelope + 1) +
    BigInt(limits.maxMetadata) * BigInt(metadataBytes + 1);
  if (maximum > BigInt(Number.MAX_SAFE_INTEGER))
    throw new Error(
      "Invalid local media quota: serialized snapshot bound is not a safe integer.",
    );
  return Number(maximum);
}

/** One process/store instance per directory. Atomic snapshots; no external providers. */
export class LocalMediaStore {
  private state: Snapshot = { version: 1, images: [], metadata: [] };
  private queue: Promise<unknown> = Promise.resolve();
  private readonly file: string;
  private readonly lockPath: string;
  private lock?: FileHandle;
  private closed = false;
  private closing?: Promise<void>;
  private readonly maxSnapshotBytes: number;
  readonly limits: Readonly<Required<LocalMediaLimits>>;
  private constructor(
    private readonly directory: string,
    limits: LocalMediaLimits,
  ) {
    this.file = join(directory, "media.json");
    this.lockPath = join(directory, ".media-owner");
    this.limits = Object.freeze({
      maxBytes: limits.maxBytes ?? 16_000_000,
      maxImages: limits.maxImages ?? 128,
      maxMetadata: limits.maxMetadata ?? 128,
    });
    for (const n of Object.values(this.limits))
      if (!Number.isSafeInteger(n) || n <= 0)
        throw new Error("Invalid local media quota.");
    this.maxSnapshotBytes = snapshotByteLimit(this.limits);
  }

  static async open(directory: string, limits: LocalMediaLimits = {}) {
    const root = resolve(directory);
    await mkdir(root, { recursive: true, mode: 0o700 });
    const stat = await lstat(root);
    if (!stat.isDirectory() || stat.isSymbolicLink())
      throw new Error("Local media directory must be a real directory.");
    const store = new LocalMediaStore(root, limits);
    // Exclusive filesystem ownership also prevents a second process from losing updates.
    // A crashed owner's stale lock is deliberately not auto-stolen.
    store.lock = await open(
      store.lockPath,
      constants.O_WRONLY |
        constants.O_CREAT |
        constants.O_EXCL |
        constants.O_NOFOLLOW,
      0o600,
    );
    let file;
    try {
      await store.lock.writeFile(`pid=${process.pid}\n`);
      try {
        file = await open(
          store.file,
          constants.O_RDONLY | constants.O_NOFOLLOW,
        );
      } catch (error) {
        if ((error as NodeJS.ErrnoException).code === "ENOENT") return store;
        throw error;
      }
      try {
        const stat = await file.stat();
        if (
          !stat.isFile() ||
          !Number.isSafeInteger(stat.size) ||
          stat.size > store.maxSnapshotBytes
        )
          throw new Error("Invalid local media snapshot size/type.");
        store.state = store.validateSnapshot(
          JSON.parse(await file.readFile("utf8")),
        );
      } finally {
        await file.close();
      }
    } catch (error) {
      await store.close();
      throw error;
    }
    return store;
  }

  private assertOpen() {
    if (this.closed)
      fail("LOCAL_MEDIA_CLOSED", "Local media store is closed.", 503);
  }

  close(): Promise<void> {
    if (!this.closing) {
      this.closed = true;
      this.closing = this.queue.then(async () => {
        if (!this.lock) return;
        const owned = await this.lock.stat();
        try {
          const current = await lstat(this.lockPath);
          if (
            !current.isFile() ||
            current.dev !== owned.dev ||
            current.ino !== owned.ino
          )
            throw new Error("Local media owner file changed.");
          await unlink(this.lockPath);
        } finally {
          await this.lock.close();
          this.lock = undefined;
        }
      });
    }
    return this.closing;
  }

  private validateSnapshot(input: unknown): Snapshot {
    const data = object(input);
    keys(data, ["version", "images", "metadata"]);
    if (
      data.version !== 1 ||
      !Array.isArray(data.images) ||
      !Array.isArray(data.metadata)
    )
      throw new Error("Invalid local media snapshot.");
    const images: ImageRecord[] = [];
    const records: MetadataRecord[] = [];
    const imageIds = new Set<string>();
    const metadataIds = new Set<string>();
    for (const candidate of data.images) {
      const item = object(candidate);
      keys(item, ["id", "mime", "data"]);
      const id = identifier(item.id);
      if (
        typeof item.data !== "string" ||
        item.data.length > (MAX_IMAGE_BYTES * 4) / 3 + 4
      )
        throw new Error("Invalid stored image.");
      const bytes = Buffer.from(item.data, "base64");
      const mime = validateImage(bytes, item.mime);
      if (
        bytes.toString("base64") !== item.data ||
        hash(bytes) !== id ||
        imageIds.has(id)
      )
        throw new Error("Stored image integrity failure.");
      imageIds.add(id);
      images.push({ id, mime, data: item.data });
    }
    for (const candidate of data.metadata) {
      const item = object(candidate);
      keys(item, ["id", "imageId", "value"]);
      const value = object(item.value);
      keys(value, [
        "name",
        "symbol",
        "description",
        "image",
        "showName",
        "createdOn",
        "twitter",
        "telegram",
        "website",
      ]);
      const { image, createdOn, ...fields } = value;
      const normalized = metadata({ ...fields, imageId: item.imageId });
      const id = identifier(item.id);
      if (
        image !== normalized.value.image ||
        createdOn !== CREATED_ON ||
        hash(JSON.stringify(normalized.value)) !== id ||
        !imageIds.has(normalized.imageId) ||
        metadataIds.has(id)
      )
        throw new Error("Stored metadata integrity failure.");
      metadataIds.add(id);
      records.push({ id, ...normalized });
    }
    const snapshot: Snapshot = { version: 1, images, metadata: records };
    this.checkQuota(snapshot);
    return snapshot;
  }

  private checkQuota(state: Snapshot) {
    const bytes = state.images.reduce(
      (sum, image) => sum + Buffer.byteLength(image.data, "base64"),
      0,
    );
    if (
      bytes > this.limits.maxBytes ||
      state.images.length > this.limits.maxImages ||
      state.metadata.length > this.limits.maxMetadata
    ) {
      fail("LOCAL_MEDIA_QUOTA", "Local media storage quota exceeded.", 507);
    }
  }

  private change<T>(edit: (next: Snapshot) => T): Promise<T> {
    this.assertOpen();
    const operation = this.queue.then(async () => {
      const next = structuredClone(this.state);
      const result = edit(next);
      this.checkQuota(next);
      const serialized = JSON.stringify(next);
      // Keep publication and reopening on the same bound. The bound covers all
      // admitted fields, unlike the independent HTTP request body limit.
      if (Buffer.byteLength(serialized) > this.maxSnapshotBytes)
        throw new Error("Invalid local media snapshot size/type.");
      // Write completely before replacing the prior snapshot; failed writes leave memory unchanged.
      const temporary = join(this.directory, `.media-${randomUUID()}.tmp`);
      try {
        const file = await open(temporary, "wx", 0o600);
        try {
          await file.writeFile(serialized);
          await file.sync();
        } finally {
          await file.close();
        }
        await rename(temporary, this.file);
        this.state = next;
      } catch (error) {
        await unlink(temporary).catch(() => {});
        throw error;
      }
      return result;
    });
    this.queue = operation.catch(() => {});
    return operation;
  }

  async putImage(bytes: Buffer, mime: string) {
    // Copy caller-owned bytes before entering the asynchronous write queue.
    const copy = Buffer.from(bytes);
    const type = validateImage(copy, mime);
    const id = hash(copy);
    return this.change((next) => {
      const exists = next.images.some((item) => item.id === id);
      if (!exists)
        next.images.push({ id, mime: type, data: copy.toString("base64") });
      return {
        ...this.describeImage({
          id,
          mime: type,
          data: copy.toString("base64"),
        }),
        created: !exists,
      };
    });
  }
  private describeImage(item: ImageRecord) {
    return {
      mode: "local-only" as const,
      id: item.id,
      mime: item.mime,
      bytes: Buffer.byteLength(item.data, "base64"),
      contentUri: `${LOCAL_MEDIA_PREFIX}/images/${item.id}/content`,
    };
  }
  getImage(id: string) {
    this.assertOpen();
    identifier(id);
    const item = this.state.images.find((item) => item.id === id);
    if (!item) fail("LOCAL_MEDIA_NOT_FOUND", "Local image not found.", 404);
    return {
      descriptor: this.describeImage(item),
      content: Buffer.from(item.data, "base64"),
    };
  }
  async putMetadata(input: unknown) {
    const record = metadata(input);
    const id = hash(JSON.stringify(record.value));
    return this.change((next) => {
      if (!next.images.some((item) => item.id === record.imageId))
        fail("LOCAL_MEDIA_NOT_FOUND", "Upload the local image first.", 404);
      const exists = next.metadata.some((item) => item.id === id);
      if (!exists) next.metadata.push({ id, ...record });
      return { ...this.describeMetadata({ id, ...record }), created: !exists };
    });
  }
  private describeMetadata(item: MetadataRecord) {
    return {
      mode: "local-only" as const,
      id: item.id,
      imageId: item.imageId,
      metadataUri: `${LOCAL_MEDIA_PREFIX}/metadata/${item.id}/content`,
      metadata: structuredClone(item.value),
    };
  }
  getMetadata(id: string) {
    this.assertOpen();
    identifier(id);
    const item = this.state.metadata.find((item) => item.id === id);
    if (!item) fail("LOCAL_MEDIA_NOT_FOUND", "Local metadata not found.", 404);
    return this.describeMetadata(item);
  }
  async deleteMetadata(id: string) {
    identifier(id);
    return this.change((next) => {
      if (!next.metadata.some((item) => item.id === id))
        fail("LOCAL_MEDIA_NOT_FOUND", "Local metadata not found.", 404);
      next.metadata = next.metadata.filter((item) => item.id !== id);
    });
  }
  async deleteImage(id: string) {
    identifier(id);
    return this.change((next) => {
      if (!next.images.some((item) => item.id === id))
        fail("LOCAL_MEDIA_NOT_FOUND", "Local image not found.", 404);
      if (next.metadata.some((item) => item.imageId === id))
        fail(
          "LOCAL_MEDIA_IN_USE",
          "Delete referencing metadata before its image.",
          409,
        );
      next.images = next.images.filter((item) => item.id !== id);
    });
  }
}
