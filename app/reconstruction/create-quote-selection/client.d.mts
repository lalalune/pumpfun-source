/** Local structural capability types, not recovered original TypeScript or an API schema. */
export interface StockRecord { mint: string; symbol: string; ticker: string; [key: string]: unknown }
export interface PumpRecord { mint: string; name?: string | null; symbol?: string | null; [key: string]: unknown }
export type QuotePair = { kind: 'sol' | 'usdc' } | { kind: 'stock'; stock?: StockRecord } | { kind: 'pump'; coin?: PumpRecord };
export interface QuoteState {
  pair: QuotePair;
  isQuoteMintEnabled: boolean;
  setPair(pair: QuotePair): void;
  setIsQuoteMintEnabled(enabled: boolean): void;
}
export interface QuoteStore {
  (): QuoteState;
  <T>(selector: (state: QuoteState) => T): T;
}
export interface PickerBodyProps {
  isLoading: boolean;
  stocks: readonly StockRecord[];
  onSelect(stock: StockRecord): void;
  onSelectPumpCoin(coin: PumpRecord): void;
  onClose(): void;
}
export interface QuoteSelectionPorts {
  createBoundStore(initialize: (set: (patch: Partial<QuoteState>) => void) => QuoteState): QuoteStore;
  React: { useState(initial: boolean): [boolean, (value: boolean) => void] };
  compiler(size: number): unknown[];
  jsxRuntime: { jsx(type: unknown, props: Record<string, unknown>, key?: unknown): unknown; jsxs(type: unknown, props: Record<string, unknown>, key?: unknown): unknown; Fragment: unknown };
  useTranslation(): { t(key: string, variables?: Record<string, unknown>): string };
  useStocks(): { data?: readonly StockRecord[] | null; isPending: boolean };
  mayhemState: { getState(): { isMayhemEnabled: boolean; setIsMayhemEnabled(value: boolean): void } };
  feeSharingState: { getState(): { enabled: boolean; setEnabled(value: boolean): void } };
  toast: { info(message: string): unknown };
  classes(...values: string[]): string;
  Image: unknown;
  StockArt: unknown;
  CoinAvatar: unknown;
  Chevron: unknown;
  Dialog: unknown;
  DialogContent: unknown;
  /** Renderer-compatible function with the actual five-field signature; no search implementation supplied here. */
  PickerBody(props: PickerBodyProps): unknown;
}
export function createQuoteSelectionCoordinator(ports: QuoteSelectionPorts): { Control(): unknown; store: QuoteStore };
