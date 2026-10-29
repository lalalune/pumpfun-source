export type LocalUserSearchRow = {
  address: string;
  userId?: string;
  wallet_label?: string;
  displayName: string;
  identifier: string;
  kind: "person" | "group";
  banned: boolean;
};

/** The local HTTP projection is deliberately smaller than the original user DTO. */
export function isLocalUserSearchRows(
  value: unknown,
): value is LocalUserSearchRow[] {
  return (
    Array.isArray(value) &&
    value.length <= 20 &&
    value.every(
      (row) =>
        row &&
        typeof row === "object" &&
        !Array.isArray(row) &&
        typeof row.address === "string" &&
        (row.userId === undefined || typeof row.userId === "string") &&
        (row.wallet_label === undefined ||
          typeof row.wallet_label === "string") &&
        typeof row.displayName === "string" &&
        row.displayName.length > 0 &&
        typeof row.identifier === "string" &&
        row.identifier.length > 0 &&
        row.identifier.length <= 128 &&
        row.identifier === (row.userId?.trim() || row.address) &&
        (row.kind === "person" || row.kind === "group") &&
        typeof row.banned === "boolean",
    ) &&
    new Set(value.map((row) => row.identifier)).size === value.length
  );
}
