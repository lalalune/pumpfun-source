export interface SearchIdentityRow {
  address: string;
  userId?: string | null;
  wallet_label?: unknown;
}
export interface UserSearchRequestOptions {
  query: {
    offset: number;
    limit: number;
    includeLabelledWallets: true;
    searchTerm?: string;
  };
  signal: AbortSignal;
  credentials: "include";
  headers: { "Content-Type": string };
  throwHttpErrors: false;
  hooks: {
    afterResponse: Array<
      (request: unknown, options: unknown, response: Response) => void
    >;
  };
}
export function createUserSearchQuery<Row extends SearchIdentityRow>(
  input: {
    searchTerm?: string;
    enabled?: boolean;
    pageSize?: number;
    debouncedTerm: string;
  },
  getContractClient: () => (
    operation: string,
    options: UserSearchRequestOptions,
  ) => Promise<Row[]>,
): {
  queryOptions: {
    queryKey: [string, string, string, number];
    queryFn(context: {
      pageParam: number;
      signal: AbortSignal;
    }): Promise<Row[]>;
    initialPageParam: number;
    getNextPageParam(lastPage: Row[], pages: Row[][]): number | undefined;
    select(data: { pages: Row[][] }): Row[];
    enabled: boolean;
    staleTime: number;
    refetchOnWindowFocus: false;
  };
  trimmedTerm: string;
  isSearchTermTooShort: boolean;
  isDebouncing: boolean;
  minSearchTermLength: number;
  debounceMs: number;
};
export function selectUserSearchPages<Row extends SearchIdentityRow>(data: {
  pages: Row[][];
}): Row[];
export function userSearchIdentity(row: SearchIdentityRow): string;
export function isLabelledWallet(row: SearchIdentityRow): boolean;
