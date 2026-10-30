/** Authored structural port types, not original TS or runtime/schema admission. */
export type Node = unknown;
export type Renderer<P> = (props: P) => Node;
export interface Entry {key?: string;userId:string;coinMint:string;createdAt?:number;mediaUrl?:unknown;positionPnl?:unknown;[key:string]:unknown}
export interface Author {walletAddress?:string|null;username?:string|null;avatarUrl?:string|null;[key:string]:unknown}
export interface Callout {coinMint:string;calloutId?:string|number|null;author:Author;createdAtMs?:number;note?:unknown;mediaUrl?:unknown;[key:string]:unknown}
export interface Coin {mint:string;symbol?:string|null;name?:string|null;image_uri?:string|null;chain_id?:string|number|null;[key:string]:unknown}
export interface RowCoin {mint:string;symbol?:string|null;name?:string|null;image?:string|null;chainId?:string|number|null}
export type Row = {type:'callout';key:string;entry:Entry} | {type:'trade';key:string} | {type:'reply'|'quote';key:string;row:{callout?:Callout|null;[key:string]:unknown};coin?:RowCoin|null;xUsername?:string|null} | {type:'repost';key:string;callout:Callout;reposter:{address?:string|null;name?:string|null};coin?:RowCoin|null};
export interface Preview {key:string;coinMint:string}
export interface Feed {rows:Row[];isLoadingHistory:boolean;error:unknown;pendingNewCount:number;pendingPreview:Preview[];showNewCallouts(options:{trigger:'tap'|'auto'}):unknown;hasNextPage:boolean;hasUnseen?:boolean;isFetchingNextPage:boolean;fetchNextPage():unknown}
export interface ListProps {feed:Feed;listAriaLabel:string;errorTitle:string;emptyTitle:string;emptyDescription?:string;applyOpenPositionGate?:boolean;surface?:string;autoLoadMore?:boolean;autoRevealAtTop?:boolean;viewerAddress?:string;isLoggedIn?:boolean;viewerFollowing?:unknown}
export interface SelectionProps {t(key:string):string;tab:'for-you'|'top'|'following';showFollowingSignedOut:boolean;feedByTab:Record<'for-you'|'top'|'following',Feed>;address?:string;isLoggedIn?:boolean;viewerFollowing?:unknown}
export interface RepostProps {row:Extract<Row,{type:'repost'}>;coinSymbol?:string|null;coinName?:string|null;coinImageUri?:string|null;coinChainId?:string|number|null;positionRead?:unknown;testId?:string}
export interface CalloutEntryProps {entry:Entry;coin?:Coin;card:unknown;user?:{address:string;[key:string]:unknown};position:number;mediaPriority:boolean;surface?:string;viewerAddress?:string;isLoggedIn?:boolean;viewerFollowing?:unknown;className:string}
export interface PositionProps {mint:string;authorAddress:string;positionRead?:unknown;symbol?:string|null;name?:string|null;imageUri?:string|null;chainId?:string|number|null}
export interface RootCalloutProps {authorAddress:string;authorName:string;authorAvatarUrl:unknown;createdAt?:number;note?:unknown;mediaUrl?:unknown;nameAdornment:Node;density:'compact';noteSize:'sm';href?:string;testId:string;className:string;children:Node}
export interface Ports {
 React:{memo<T>(component:T):T;useEffect(effect:()=>void|(()=>void),dependencies:unknown[]):void};
 compiler(size:number):unknown[];
 jsxRuntime:{jsx(type:unknown,props:unknown,key?:unknown):Node;jsxs(type:unknown,props:unknown,key?:unknown):Node;Fragment:unknown};
 window:{scrollY:number;scrollTo(options:{top:0;behavior:'smooth'}):void;addEventListener(type:'scroll',listener:()=>void,options:{passive:true}):void;removeEventListener(type:'scroll',listener:()=>void):void};
 useFeatureFlag(key:'webPerps'|'webPacks',fallback:false):boolean;
 usePositionsRead(inputs:{userId?:string;mint?:string}[]):{readFor(author:string,mint:string):unknown};
 useCoins(options:{mints:string[];disabled:boolean}):{coins:(Coin|null)[];loading:boolean};
 usePackCards(mints:string[]):{cardByMint:Map<string,unknown>};
 useUsers(options:{userAddresses:string[]}):{data?:({address:string;[key:string]:unknown}|null)[]};
 isCollectibleEntry(entry:Entry):boolean;isBase58Pubkey(mint:string):boolean;normalizeMintKey(mint:string):string;isPerpRow(row:Row):boolean;
 useOpenPositionGate(options:{mint:string;authorAddress:string;positionPnl?:unknown}):{shouldHide:boolean};
 PendingBanner:Renderer<{count:number;avatars:{key:string;mint:string;imageUrl?:string|null}[];onClick():void}>;
 LoadMore:Renderer<{hasNextPage:boolean;autoLoadHasMore?:boolean;isFetchingNextPage:boolean;onFetchNextPage():unknown;autoLoad:boolean}>;
 CalloutEntry:Renderer<CalloutEntryProps>;
 MainFeedRow:Renderer<{row:Extract<Row,{type:'reply'|'quote'}>['row'];variant:'reply'|'quote';coinSymbol?:string|null;coinName?:string|null;coinImageUri?:string|null;coinChainId?:string|number|null;positionRead?:unknown;xUsername?:string|null}>;
 PositionInsert:Renderer<PositionProps>;RootCallout:Renderer<RootCalloutProps>;
 Link:Renderer<{href:string|null;className:string;children:Node}>;
 profileRoute(address:string):string|null;shortenAddress(address:string,start:number,end:number):string;
 normalizeImage(source?:string|null):unknown;buildImage(options:{sourceUrl:unknown;width:40}):unknown;
 RepostIcon:Renderer<{className:string;'aria-hidden':true}>;EmptyIcon:Renderer<{className:string}>;
 labelText(value:unknown,context:'error-message'):Node;
}
export function createMobileFeedList(ports:Ports):{FeedList:Renderer<ListProps>;selectFeed:Renderer<SelectionProps>;RepostRow:Renderer<RepostProps>;EmptyState:Renderer<{title:string;description?:Node}>;Skeleton:Renderer<Record<string,never>>};
