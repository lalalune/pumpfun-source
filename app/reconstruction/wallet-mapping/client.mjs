// Complete 795663 read/cache/query owner with explicit local capabilities.
// Credited strict-batch and typed single-user readers are reused unchanged.
import { fetchUsersBatch, USER_BATCH_LIMIT } from '../user-batch/client.mjs';
import { fetchUser, isUserMissing } from '../profile-lookup/client.mjs';
export const walletMappingKey = address => ['walletMapping','solToEvm',address];

export function walletMappingClient({request,createClient,getOrigin,now=Date.now}) {
  async function batch({solAddresses,signal}) {
    const addresses=Array.from(new Set(solAddresses)),chunks=[];
    for(let offset=0;offset<addresses.length;offset+=USER_BATCH_LIMIT)
      chunks.push(addresses.slice(offset,offset+USER_BATCH_LIMIT));
    const responses=await Promise.all(chunks.map(userAddresses=>
      fetchUsersBatch(request,{userAddresses,fetchOptions:{signal}})));
    const mappings={};
    for(const address of addresses)mappings[address]=null;
    for(const rows of responses)for(const user of rows)
      if(user?.address && user.address in mappings)mappings[user.address]=user.canonical_evm_wallet??null;
    return mappings;
  }
  async function single({solAddress,signal}) {
    try {return (await fetchUser(createClient,{clientServerUrl:getOrigin(),userIdentifier:solAddress,fetchOptions:{signal}})).canonical_evm_wallet??null;}
    catch(error){if(isUserMissing(error))return null;throw error;}
  }
  async function cached({solAddresses,queryClient,signal}) {
    const mappings={},missing=[],sample=now();
    for(const address of new Set(solAddresses)) {
      const state=queryClient.getQueryState(walletMappingKey(address)),value=state?.data;
      if(typeof value==='string' || (value===null && state!==undefined && sample-state.dataUpdatedAt<300000))mappings[address]=value;
      else missing.push(address);
    }
    if(missing.length){
      const result=await batch({solAddresses:missing,signal});
      for(const address of missing){const value=result[address]??null;mappings[address]=value;queryClient.setQueryData(walletMappingKey(address),value);}
    }
    return mappings;
  }
  function queryOptions({solAddress,enabled,fresh=false}) {
    return {queryKey:walletMappingKey(solAddress??null),enabled:!!solAddress&&(enabled===undefined||enabled),
      staleTime:300000*!fresh,...(fresh?{refetchOnWindowFocus:false}:{}),
      queryFn:({signal})=>single({solAddress:solAddress??'',signal})};
  }
  return {single,batch,cached,queryOptions,
    // Actual query framework and its cache/retry/observer lifetimes stay ports.
    useWalletMapping:(useQuery,input)=>useQuery(queryOptions(input))};
}
