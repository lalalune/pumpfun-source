/** Local capability types for the witnessed JavaScript call signatures, not recovered TypeScript. */
export interface CreatorFeeState {
  creatorFeePercent: string;
  setCreatorFeePercent(value: string): void;
}
export interface CreatorFeeStore {
  (): CreatorFeeState;
  <T>(selector: (state: CreatorFeeState) => T): T;
}
export interface QuoteSnapshot { pair: { kind: string } }
export type Translator = (key: string, variables?: { min_percent: number; max_percent: number }) => unknown;
export interface AdvancedFeePorts {
  /** Actual direct initializer => bound-hook form; no original provider acquisition. */
  createBoundStore(initialize: (set: (patch: Partial<CreatorFeeState>) => void) => CreatorFeeState): CreatorFeeStore;
  useQuoteState<T>(selector: (snapshot: QuoteSnapshot) => T): T;
  useTranslation(): { t: Translator };
  compiler(size: number): unknown[];
  jsxRuntime: {
    jsx(type: unknown, props: Record<string, unknown>): unknown;
    jsxs(type: unknown, props: Record<string, unknown>): unknown;
  };
  /** Opaque original component boundary: the local host supplies renderer-compatible primitives. */
  Collapsible: { Y: unknown; v: unknown; C: unknown };
  Input: unknown;
  Chevron: unknown;
}
export function createAdvancedCreatorFeeControl(ports: AdvancedFeePorts): {
  Control(): unknown;
  store: CreatorFeeStore;
};
