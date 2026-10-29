export const CREATE_LIMITS = {
  name: 32,
  ticker: 10,
  description: 2_000,
  socialUrl: 2_048,
  imageBytes: 4_500_000,
} as const;

// Captured Create uses Blob.size for these limits (UTF-8), not UTF-16 length.
export function utf8ByteLength(value: string): number {
  return new Blob([value]).size;
}

export const ACCEPTED_IMAGE_TYPES = [
  "image/jpeg",
  "image/png",
  "image/gif",
  "image/webp",
] as const;

export type DraftValues = {
  name: string;
  ticker: string;
  description: string;
  website: string;
  twitter: string;
  telegram: string;
};

export type DraftField = keyof DraftValues | "image";
export type DraftErrors = Partial<Record<DraftField, string>>;

const socialHosts = {
  twitter: new Set(["x.com", "www.x.com", "twitter.com", "www.twitter.com"]),
  telegram: new Set(["t.me", "telegram.me"]),
} as const;

function validateUrl(
  value: string,
  field: "website" | "twitter" | "telegram",
): string | undefined {
  if (!value) return undefined;
  if (value.length > CREATE_LIMITS.socialUrl) {
    return `Keep this link at ${CREATE_LIMITS.socialUrl.toLocaleString()} characters or fewer.`;
  }

  let url: URL;
  try {
    url = new URL(value);
  } catch {
    return "Enter a complete HTTPS URL.";
  }
  if (url.protocol !== "https:") return "Use an HTTPS link.";
  if (url.username || url.password)
    return "Links with embedded credentials are not accepted.";
  if (!url.hostname.includes(".") || url.hostname.endsWith(".")) {
    return "Enter a public website hostname.";
  }
  if (field === "twitter" && !socialHosts.twitter.has(url.hostname)) {
    return "Use an x.com or twitter.com profile link.";
  }
  if (field === "telegram" && !socialHosts.telegram.has(url.hostname)) {
    return "Use a t.me or telegram.me link.";
  }
  if ((field === "twitter" || field === "telegram") && url.pathname === "/") {
    return "Include the profile or channel path.";
  }
  return undefined;
}

export function validateDraftField(
  field: keyof DraftValues,
  value: string,
): string | undefined {
  if (field === "name") {
    if (!value.trim()) return "Enter a coin name.";
    if (utf8ByteLength(value) > CREATE_LIMITS.name) {
      return `Use ${CREATE_LIMITS.name} UTF-8 bytes or fewer.`;
    }
  }
  if (field === "ticker") {
    if (!value.trim()) return "Enter a ticker.";
    if (utf8ByteLength(value) > CREATE_LIMITS.ticker) {
      return `Use ${CREATE_LIMITS.ticker} UTF-8 bytes or fewer.`;
    }
  }
  if (field === "description" && value.length > CREATE_LIMITS.description) {
    return `Use ${CREATE_LIMITS.description.toLocaleString()} characters or fewer.`;
  }
  if (field === "website" || field === "twitter" || field === "telegram") {
    return validateUrl(value.trim(), field);
  }
  return undefined;
}

export function validateImage(file: File | null): string | undefined {
  if (!file) return "Select an image for the local preview.";
  if (
    !ACCEPTED_IMAGE_TYPES.includes(
      file.type as (typeof ACCEPTED_IMAGE_TYPES)[number],
    )
  ) {
    return "Choose a JPEG, PNG, GIF or WebP image.";
  }
  if (file.size === 0) return "Choose a non-empty image file.";
  if (file.size > CREATE_LIMITS.imageBytes) {
    return "Choose an image smaller than 4.5 MB.";
  }
  return undefined;
}

export function validateDraft(
  values: DraftValues,
  image: File | null,
): DraftErrors {
  const errors: DraftErrors = {};
  for (const field of Object.keys(values) as (keyof DraftValues)[]) {
    const error = validateDraftField(field, values[field]);
    if (error) errors[field] = error;
  }
  const imageError = validateImage(image);
  if (imageError) errors.image = imageError;
  return errors;
}
