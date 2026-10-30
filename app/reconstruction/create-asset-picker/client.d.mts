/** Local structural signatures of the observed JavaScript ports; not original TypeScript or runtime admission. */
export type Coin = { mint: string; name?: string | null; symbol?: string | null; program?: string;
  raydium_pool?: unknown; depth?: number | null; mayhem_state?: unknown; mayhem?: {state?: unknown} | null;
  is_banned?: unknown; base_decimals?: unknown; quote_mint?: string | null; usd_market_cap?: unknown;
  canonical_pool_liquidity_usd?: unknown; [field: string]: unknown };
export type Stock = { mint: string; symbol: string; ticker: string; assetType?: string;
  marketCapUsd?: unknown; liquidityUsd?: unknown; [field: string]: unknown };
export type PickerProps = { isLoading: boolean; stocks: Stock[]; onSelect(stock: Stock): void;
  onSelectPumpCoin(coin: Coin): void; onClose(): void };
export type SearchOptions = {
  queryKey: ['create', 'pump-quote-coin-search', string, 1, boolean, string];
  enabled: boolean; staleTime: 30000; placeholderData<T>(previous: T): T;
  select(coins: Coin[]): Coin[]; queryFn(context: {signal?: AbortSignal}): Promise<Coin[]>;
};
export type QueryResult = {data?: Coin[]; isError: boolean; isFetching: boolean; error?: unknown; refetch(): unknown};
export type RequestOptions = { query: {searchTerm: string; limit: 20; offset: 0; includeNsfw: boolean;
  sort: 'market_cap'; order: 'DESC'; program: 'pump'; maxDepth: 1}; credentials: 'include'; signal?: AbortSignal;
  hooks: {afterResponse: [(request: unknown, options: unknown, response: {ok: boolean; status: number}) => void]} };
export type Primitive = (props: Record<string, unknown>) => unknown;
export type Ports = {
  React: {useState<T>(initial: T): [T, (next: T) => void]; useEffect(effect: () => void | (() => void), dependencies: unknown[]): void};
  compiler(slots: number): unknown[];
  jsxRuntime: {jsx(type: unknown, props: Record<string, unknown>, key?: unknown): unknown;
    jsxs(type: unknown, props: Record<string, unknown>, key?: unknown): unknown; Fragment: unknown};
  useTranslation(): {t(key: string): string};
  useDebouncedValue(value: string, delay: 250): [string, unknown];
  useIpfsPrefix(): {ipfsPrefix: string}; useIncludeNsfw(): boolean;
  useSupportedMints(): {data?: {mint: string}[] | null}; useQuery(options: SearchOptions): QueryResult;
  getContractClient(): (route: 'GET /coins/search-unrestricted', options: RequestOptions) => Promise<unknown>;
  readCoins(value: unknown): Coin[];
  normalizeCoins(coins: Coin[], ipfsPrefix: string): Coin[];
  reportError(details: {error: unknown; feature: 'coin-creation'; operation: 'pair-search'; context: {mint: string | undefined}}): void;
  formatUsd(value: unknown): unknown; classes(...values: unknown[]): string;
  CategorySelector: Primitive; StockArt: Primitive; CoinAvatar: Primitive; CoinName: Primitive;
  LoadError: Primitive; Skeleton: Primitive; CloseIcon: Primitive; SearchIcon: Primitive;
};
export function createQuoteAssetPicker(ports: Ports): {Picker(props: PickerProps): unknown};
