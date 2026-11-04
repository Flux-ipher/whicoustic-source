export interface DisbursementRecord {
  id: string;
  payoutDate: string;
  amount: number;
  royaltyStream: string;
  licensee: string;
  paymentMethod: string;
  txHash: string;
  status: 'COMPLETED' | 'PROCESSING' | 'PENDING';
}

export const mockMonthlyRevenue = [
  { month: 'Jun', licensing: 38000, royalties: 22000, total: 60000 },
  { month: 'Jul', licensing: 45000, royalties: 28000, total: 73000 },
  { month: 'Aug', licensing: 52000, royalties: 34000, total: 86000 },
  { month: 'Sep', licensing: 68000, royalties: 41000, total: 109000 },
  { month: 'Oct', licensing: 74000, royalties: 48000, total: 122000 },
  { month: 'Nov', licensing: 81000, royalties: 54000, total: 135000 },
];

export const mockDisbursements: DisbursementRecord[] = [
  {
    id: 'tx_99182',
    payoutDate: '2026-11-01',
    amount: 54200,
    royaltyStream: 'October Global Streaming & Game Royalties',
    licensee: 'Automated Escrow Protocol',
    paymentMethod: 'USDC (Ethereum Vault 0x8F9...21B)',
    txHash: '0x3a9f...892e',
    status: 'COMPLETED',
  },
  {
    id: 'tx_99181',
    payoutDate: '2026-10-01',
    amount: 48150,
    royaltyStream: 'September Syndicate Broadcast Pool',
    licensee: 'Automated Escrow Protocol',
    paymentMethod: 'Fedwire / Direct Deposit (Chase Bank)',
    txHash: 'ACH_99018481',
    status: 'COMPLETED',
  },
  {
    id: 'tx_99180',
    payoutDate: '2026-09-01',
    amount: 41300,
    royaltyStream: 'August Audible & Audiobook Royalty Share',
    licensee: 'Penguin Random House Audio',
    paymentMethod: 'USDC (Ethereum Vault 0x8F9...21B)',
    txHash: '0x7b1c...991a',
    status: 'COMPLETED',
  },
  {
    id: 'tx_99179',
    payoutDate: '2026-08-01',
    amount: 34000,
    royaltyStream: 'July Commercial Broadcast Upfront',
    licensee: 'Bayer Health EMEA',
    paymentMethod: 'Fedwire / Direct Deposit (Chase Bank)',
    txHash: 'ACH_77218944',
    status: 'COMPLETED',
  },
];
