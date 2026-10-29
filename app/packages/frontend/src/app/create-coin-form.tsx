"use client";

import {
  type ChangeEvent,
  type FormEvent,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  ACCEPTED_IMAGE_TYPES,
  CREATE_LIMITS,
  type DraftErrors,
  type DraftValues,
  utf8ByteLength,
  validateDraft,
  validateDraftField,
  validateImage,
} from "./create-coin-validation";
import { CreateDraftLinks } from "./create-draft-links";
import CreateVideoInput, { type VideoInputControl } from "./create-video-input";
import {
  discardVideoCover,
  type VideoPreview,
  type VideoSelection,
} from "./create-video-preview";

const EMPTY_DRAFT: DraftValues = {
  name: "",
  ticker: "",
  description: "",
  website: "",
  twitter: "",
  telegram: "",
};

const TEXT_FIELDS = [
  {
    name: "name",
    label: "Coin name",
    placeholder: "Name your coin",
    required: true,
    maxLength: CREATE_LIMITS.name,
  },
  {
    name: "ticker",
    label: "Ticker",
    placeholder: "Add a coin ticker (e.g. DOGE)",
    required: true,
    maxLength: CREATE_LIMITS.ticker,
  },
] as const;

const SOCIAL_FIELDS = [
  {
    name: "website",
    label: "Website",
    placeholder: "https://example.com",
    hint: "Optional HTTPS website.",
  },
  {
    name: "twitter",
    label: "X / Twitter",
    placeholder: "https://x.com/username",
    hint: "Optional x.com or twitter.com profile.",
  },
  {
    name: "telegram",
    label: "Telegram",
    placeholder: "https://t.me/channel",
    hint: "Optional t.me or telegram.me link.",
  },
] as const;

function FieldError({ field, error }: { field: string; error?: string }) {
  if (!error) return null;
  return (
    <p className="create-field-error" id={`${field}-error`}>
      {error}
    </p>
  );
}

function validPreviewLink(
  field: "website" | "twitter" | "telegram",
  value: string,
) {
  return value && !validateDraftField(field, value) ? value.trim() : null;
}

export default function CreateCoinForm() {
  const [draft, setDraft] = useState<DraftValues>(EMPTY_DRAFT);
  const [errors, setErrors] = useState<DraftErrors>({});
  const [status, setStatus] = useState("");
  const [selectedImage, setSelectedImage] = useState<{
    file: File;
    url: string;
    videoOwner?: VideoPreview;
  } | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<{
    file: File;
    owner: VideoPreview;
  } | null>(null);
  const [videoReset, setVideoReset] = useState(0);
  const formRef = useRef<HTMLFormElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoControlRef = useRef<VideoInputControl>(null);

  useEffect(() => {
    if (!selectedImage) return;
    const objectUrl = selectedImage.url;
    return () => URL.revokeObjectURL(objectUrl);
  }, [selectedImage]);

  function updateField(
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) {
    const field = event.target.name as keyof DraftValues;
    const value = event.target.value;
    setDraft((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
    setStatus("");
  }

  function checkField(field: keyof DraftValues) {
    const error = validateDraftField(field, draft[field]);
    setErrors((current) => ({ ...current, [field]: error }));
  }

  function previewDraft(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validateDraft(draft, selectedImage?.file ?? null);
    setErrors(nextErrors);
    const firstError = Object.keys(nextErrors)[0];
    if (firstError) {
      setStatus("Correct the highlighted fields to preview this draft.");
      requestAnimationFrame(() => {
        if (firstError === "image") fileInputRef.current?.focus();
        else
          formRef.current
            ?.querySelector<HTMLElement>(`[name="${firstError}"]`)
            ?.focus();
      });
      return;
    }
    setStatus("Local draft is ready to review. Nothing has been uploaded.");
  }

  function resetDraft() {
    setDraft(EMPTY_DRAFT);
    setErrors({});
    setSelectedImage(null);
    setSelectedVideo(null);
    setVideoReset((value) => value + 1);
    if (fileInputRef.current) fileInputRef.current.value = "";
    setStatus("Draft cleared.");
  }

  function chooseImage(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    if (!file) return;
    const error = validateImage(file);
    if (error) {
      setErrors((current) => ({ ...current, image: error }));
      event.target.value = "";
      return;
    }
    videoControlRef.current?.cancelPending();
    setSelectedImage({ file, url: URL.createObjectURL(file) });
    setErrors((current) => ({ ...current, image: undefined }));
    setStatus("");
  }

  function removeImage(error?: string) {
    videoControlRef.current?.cancelPending();
    setSelectedImage(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    setErrors((current) => ({ ...current, image: error }));
    setStatus("");
  }

  function chooseVideoCover({ video, cover, owner }: VideoSelection) {
    const error = validateImage(cover);
    if (error) {
      setErrors((current) => ({ ...current, image: error }));
      return;
    }
    setSelectedImage({
      file: cover,
      url: URL.createObjectURL(cover),
      videoOwner: owner,
    });
    setSelectedVideo({ file: video, owner });
    if (fileInputRef.current) fileInputRef.current.value = "";
    setErrors((current) => ({ ...current, image: undefined }));
    setStatus("");
  }

  function removeVideo(owner: VideoPreview) {
    setSelectedVideo((current) => (current?.owner === owner ? null : current));
    // Do not erase a manually chosen replacement image or another video's cover.
    setSelectedImage((current) => discardVideoCover(current, owner));
    setStatus("");
  }

  const metadataPreview = {
    name: draft.name,
    symbol: draft.ticker,
    description: draft.description,
    image: selectedImage
      ? {
          localFileName: selectedImage.file.name,
          mediaType: selectedImage.file.type,
          bytes: selectedImage.file.size,
          uploadStatus: "not uploaded",
        }
      : null,
    ...(selectedVideo && {
      video: {
        localFileName: selectedVideo.file.name,
        mediaType: selectedVideo.file.type || null,
        bytes: selectedVideo.file.size,
        uploadStatus: "not uploaded",
      },
    }),
    ...(draft.twitter && { twitter: draft.twitter }),
    ...(draft.telegram && { telegram: draft.telegram }),
    ...(draft.website && { website: draft.website }),
  };

  const previewLinks = SOCIAL_FIELDS.flatMap((field) => {
    const href = validPreviewLink(field.name, draft[field.name]);
    return href ? [{ label: field.label, href }] : [];
  });

  return (
    <div className="create-workspace">
      <form
        className="create-form create-panel"
        ref={formRef}
        aria-label="Create coin metadata draft"
        onSubmit={previewDraft}
        noValidate
      >
        <div className="create-section-heading">
          <div>
            <h2>Coin details</h2>
            <p>Draft metadata locally. Required fields are marked.</p>
          </div>
          <span className="offline-badge">Offline only</span>
        </div>

        <div className="create-field-row">
          {TEXT_FIELDS.map((field) => (
            <div className="create-field" key={field.name}>
              <label htmlFor={`create-${field.name}`}>
                {field.label} <span aria-hidden="true">*</span>
              </label>
              <input
                id={`create-${field.name}`}
                name={field.name}
                type="text"
                autoComplete="off"
                placeholder={field.placeholder}
                value={draft[field.name]}
                maxLength={field.maxLength}
                required={field.required}
                aria-invalid={Boolean(errors[field.name])}
                aria-describedby={`${field.name}-hint${errors[field.name] ? ` ${field.name}-error` : ""}`}
                onChange={updateField}
                onBlur={() => checkField(field.name)}
              />
              <div className="create-field-meta" id={`${field.name}-hint`}>
                <span>
                  {field.required ? "Required" : "Optional"} · UTF-8 bytes
                </span>
                <span>
                  {utf8ByteLength(draft[field.name])}/{field.maxLength}
                </span>
              </div>
              <FieldError field={field.name} error={errors[field.name]} />
            </div>
          ))}
        </div>

        <div className="create-field">
          <label htmlFor="create-description">
            Description <span className="optional-label">Optional</span>
          </label>
          <textarea
            id="create-description"
            name="description"
            rows={5}
            placeholder="Write a short description"
            value={draft.description}
            maxLength={CREATE_LIMITS.description}
            aria-invalid={Boolean(errors.description)}
            aria-describedby={`description-hint${errors.description ? " description-error" : ""}`}
            onChange={updateField}
            onBlur={() => checkField("description")}
          />
          <div className="create-field-meta" id="description-hint">
            <span>Multiline text is supported.</span>
            <span>
              {draft.description.length}/
              {CREATE_LIMITS.description.toLocaleString()}
            </span>
          </div>
          <FieldError field="description" error={errors.description} />
        </div>

        <div className="create-field media-field">
          <label htmlFor="create-image">
            Coin image <span aria-hidden="true">*</span>
          </label>
          <p className="create-field-hint" id="image-hint">
            Select one local JPEG, PNG, GIF or WebP under 4.5 MB. It stays in
            this browser tab and is never uploaded.
          </p>
          <input
            id="create-image"
            name="image"
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_IMAGE_TYPES.join(",")}
            aria-invalid={Boolean(errors.image)}
            aria-describedby={`image-hint${errors.image ? " image-error" : ""}`}
            onChange={chooseImage}
          />
          {selectedImage ? (
            <div className="selected-file" data-testid="selected-image">
              <div>
                <strong>{selectedImage.file.name}</strong>
                <span>
                  {selectedImage.file.type} ·{" "}
                  {(selectedImage.file.size / 1_000).toLocaleString(undefined, {
                    maximumFractionDigits: 1,
                  })}{" "}
                  KB
                </span>
              </div>
              <button type="button" onClick={() => removeImage()}>
                Remove image
              </button>
            </div>
          ) : null}
          <FieldError field="image" error={errors.image} />
        </div>

        <CreateVideoInput
          key={videoReset}
          controlRef={videoControlRef}
          onSelect={chooseVideoCover}
          onRemove={removeVideo}
        />

        <fieldset className="create-fieldset">
          <legend>
            Social links <span>Optional</span>
          </legend>
          <p className="fieldset-description">
            Only valid HTTPS links are shown as clickable preview links.
          </p>
          <div className="social-grid">
            {SOCIAL_FIELDS.map((field) => (
              <div className="create-field" key={field.name}>
                <label htmlFor={`create-${field.name}`}>{field.label}</label>
                <input
                  id={`create-${field.name}`}
                  name={field.name}
                  type="url"
                  inputMode="url"
                  autoComplete="url"
                  placeholder={field.placeholder}
                  value={draft[field.name]}
                  maxLength={CREATE_LIMITS.socialUrl}
                  aria-invalid={Boolean(errors[field.name])}
                  aria-describedby={`${field.name}-hint${errors[field.name] ? ` ${field.name}-error` : ""}`}
                  onChange={updateField}
                  onBlur={() => checkField(field.name)}
                />
                <p className="create-field-hint" id={`${field.name}-hint`}>
                  {field.hint}
                </p>
                <FieldError field={field.name} error={errors[field.name]} />
              </div>
            ))}
          </div>
        </fieldset>

        <div className="create-actions">
          <button className="draft-button" type="submit">
            Preview draft
          </button>
          <button className="reset-button" type="button" onClick={resetDraft}>
            Reset draft
          </button>
        </div>
        <p className="form-status" aria-live="polite">
          {status}
        </p>

        <div className="launch-boundary">
          <button type="button" disabled>
            Launch unavailable in local reconstruction
          </button>
          <p>
            Wallet signing, metadata upload and token creation have not been
            reconstructed or qualified.
          </p>
        </div>
      </form>

      <aside
        className="create-preview create-panel"
        aria-labelledby="preview-title"
      >
        <div className="create-section-heading">
          <div>
            <p className="preview-kicker">Local draft preview</p>
            <h2 id="preview-title">{draft.name || "Your coin name"}</h2>
          </div>
          <span className="ticker-preview">{draft.ticker || "TICKER"}</span>
        </div>
        {selectedImage ? (
          // Captured media is local-only, so image optimization must not turn
          // the object URL into a network request.
          // eslint-disable-next-line @next/next/no-img-element
          <img
            className="preview-image"
            src={selectedImage.url}
            alt={`Local preview of ${draft.name || selectedImage.file.name}`}
            onError={() =>
              removeImage("The browser could not decode this image file.")
            }
          />
        ) : (
          <div
            className="preview-media-placeholder"
            aria-label="No local image selected"
          >
            <span aria-hidden="true">P</span>
            <p>Local image preview will appear here.</p>
          </div>
        )}
        <p className="preview-description">
          {draft.description ||
            "Your optional coin description will appear here."}
        </p>
        {previewLinks.length ? (
          <CreateDraftLinks links={previewLinks} />
        ) : (
          <p className="preview-empty-links">
            No valid social links in this draft.
          </p>
        )}
        <details className="metadata-json">
          <summary>Inspect draft JSON</summary>
          <p>This is local descriptive output, not a production API payload.</p>
          <pre>{JSON.stringify(metadataPreview, null, 2)}</pre>
        </details>
        <div className="preview-disclaimer">
          No mint address, metadata URI, transaction or launch status exists.
        </div>
      </aside>
    </div>
  );
}
