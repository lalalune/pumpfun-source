"use client";

import { useRef, useState } from "react";
import type { CreateInstructionPreview } from "./create-instruction-preview";

const EMPTY = { mint: "", creator: "", payer: "", metadataUri: "" };
const FIELDS = [
  ["mint", "Proposed mint public key"],
  ["creator", "Creator public key"],
  ["payer", "Payer public key"],
  ["metadataUri", "Existing metadata URI (not fetched)"],
] as const;

export default function CreateInstructionInspector({
  name,
  ticker,
}: {
  name: string;
  ticker: string;
}) {
  const [values, setValues] = useState(EMPTY);
  const [outcome, setOutcome] = useState<{
    input: string;
    preview?: CreateInstructionPreview;
    error?: string;
  } | null>(null);
  const [pending, setPending] = useState(false);
  const revision = useRef(0);
  const input = { name, ticker, ...values };
  const snapshot = JSON.stringify(input);
  const current = outcome?.input === snapshot ? outcome : null;

  async function inspect() {
    const ticket = ++revision.current;
    setPending(true);
    setOutcome(null);
    try {
      const { previewCreateInstruction } = await import(
        "./create-instruction-preview"
      );
      const preview = await previewCreateInstruction(input);
      if (revision.current === ticket) setOutcome({ input: snapshot, preview });
    } catch (error) {
      if (revision.current === ticket)
        setOutcome({
          input: snapshot,
          error:
            error instanceof Error
              ? error.message
              : "Unable to build the local instruction preview.",
        });
    } finally {
      if (revision.current === ticket) setPending(false);
    }
  }

  return (
    <details className="metadata-json">
      <summary>Inspect unsigned SDK create instruction</summary>
      <p>
        Advanced offline inspection using SDK 4.3.1. Uses the name and ticker
        above. Supply public keys only—never private keys or seed phrases.
      </p>
      <p>
        SOL quote; Mayhem, cashback and holder rewards off; no initial buy or
        custom creator fee. The metadata URI is supplied, not uploaded, fetched
        or verified against this draft.
      </p>
      {FIELDS.map(([field, label]) => (
        <div className="create-field" key={field}>
          <label htmlFor={`instruction-${field}`}>{label}</label>
          <input
            id={`instruction-${field}`}
            type="text"
            autoComplete="off"
            spellCheck={false}
            value={values[field]}
            maxLength={field === "metadataUri" ? 2048 : 44}
            onChange={(event) => {
              revision.current++;
              setPending(false);
              setOutcome(null);
              setValues({ ...values, [field]: event.target.value });
            }}
          />
        </div>
      ))}
      <div className="create-actions">
        <button
          className="draft-button"
          type="button"
          disabled={pending}
          onClick={inspect}
        >
          {pending ? "Inspecting…" : "Build unsigned preview"}
        </button>
        <button
          className="reset-button"
          type="button"
          onClick={() => {
            revision.current++;
            setPending(false);
            setValues(EMPTY);
            setOutcome(null);
          }}
        >
          Clear instruction inputs
        </button>
      </div>
      <div aria-live="polite">
        {current?.error ? (
          <p className="create-field-error">{current.error}</p>
        ) : null}
        {current?.preview ? (
          <>
            <p>
              Unsigned instruction only · {current.preview.dataBytes} data bytes
              · {current.preview.accounts.length} ordered accounts. Signer flags
              describe required signatures; none were obtained.
            </p>
            <pre data-testid="create-instruction-json">
              {JSON.stringify(current.preview, null, 2)}
            </pre>
          </>
        ) : null}
      </div>
      <p>
        No transaction, blockhash, wallet connection, RPC, fee estimate, signing
        or submission. This does not validate account existence, ownership,
        funds, mint availability, current program configuration, metadata
        contents or launch eligibility. No token has been created.
      </p>
    </details>
  );
}
