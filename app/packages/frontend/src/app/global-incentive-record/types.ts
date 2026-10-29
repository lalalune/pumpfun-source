export type StoredIncentiveSchedule = {
  startTime: string;
  endTime: string;
  secondsInADay: string;
  mint: string;
  totalTokenSupply: string[];
  solVolumes: string[];
};

export type GlobalIncentiveRecord = {
  ok: true;
  programId: string;
  recordPda: string;
  cluster: "mainnet-beta";
  commitment: "confirmed";
  contextSlot: number;
  endpointHost: string;
  observedAt: string;
  dataBytes: number | null;
  record: StoredIncentiveSchedule | null;
};
