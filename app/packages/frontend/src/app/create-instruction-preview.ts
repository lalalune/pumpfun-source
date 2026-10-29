import { PublicKey } from "@solana/web3.js";
import { validateDraftField } from "./create-coin-validation";

export type CreateInstructionInput = {
  name: string;
  ticker: string;
  mint: string;
  creator: string;
  payer: string;
  metadataUri: string;
};
export type CreateInstructionPreview = {
  programId: string;
  dataHex: string;
  dataBytes: number;
  accounts: { address: string; isSigner: boolean; isWritable: boolean }[];
};

/** Local inspection only: no wallet, connection, transaction or metadata fetch. */
export async function previewCreateInstruction(
  input: CreateInstructionInput,
): Promise<CreateInstructionPreview> {
  // Refuse silent UTF-8 replacement so displayed text equals encoded text.
  for (const field of ["name", "ticker", "metadataUri"] as const) {
    if (
      new TextDecoder("utf-8", { ignoreBOM: true }).decode(
        new TextEncoder().encode(input[field]),
      ) !== input[field]
    ) {
      throw new Error(
        `${field}: unpaired UTF-16 surrogates cannot be encoded exactly.`,
      );
    }
  }
  for (const field of ["name", "ticker"] as const) {
    const error = validateDraftField(field, input[field]);
    if (error) throw new Error(`${field}: ${error}`);
  }
  const keys = {} as Record<"mint" | "creator" | "payer", PublicKey>;
  for (const field of ["mint", "creator", "payer"] as const) {
    const value = input[field].trim();
    try {
      keys[field] = new PublicKey(value);
      if (keys[field].toBase58() !== value) throw new Error();
    } catch {
      throw new Error(
        `${field}: enter a canonical Base58 public key (32 bytes).`,
      );
    }
  }
  // Local display/input policy, not an assertion about chain or upload limits.
  const uri = input.metadataUri.trim();
  if (!uri || new TextEncoder().encode(uri).length > 2_048 || /\s/.test(uri)) {
    throw new Error(
      "Metadata URI: enter an HTTPS or IPFS URI up to 2,048 UTF-8 bytes without whitespace.",
    );
  }
  let parsed: URL;
  try {
    parsed = new URL(uri);
  } catch {
    throw new Error("Metadata URI: enter an absolute HTTPS or IPFS URI.");
  }
  if (
    !["https:", "ipfs:"].includes(parsed.protocol) ||
    !parsed.hostname ||
    parsed.username ||
    parsed.password
  ) {
    throw new Error(
      "Metadata URI: use HTTPS or IPFS without embedded credentials.",
    );
  }
  // Published SDK uses offline null-connection providers; no OnlinePumpSdk.
  const { PUMP_SDK } = await import("@pump-fun/pump-sdk");
  const instruction = await PUMP_SDK.createV2Instruction({
    name: input.name,
    symbol: input.ticker,
    uri,
    mint: keys.mint,
    creator: keys.creator,
    user: keys.payer,
    mayhemMode: false,
    cashback: false,
    holderReward: false,
    // No quote mint = SOL. No initial buy, fee override or live configuration.
  });
  return {
    programId: instruction.programId.toBase58(),
    dataHex: Array.from(instruction.data, (byte) =>
      byte.toString(16).padStart(2, "0"),
    ).join(""),
    dataBytes: instruction.data.length,
    accounts: instruction.keys.map((key) => ({
      address: key.pubkey.toBase58(),
      isSigner: key.isSigner,
      isWritable: key.isWritable,
    })),
  };
}
