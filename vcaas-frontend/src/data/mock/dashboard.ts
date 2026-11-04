export interface OperationsMetric {
  title: string;
  value: string;
  change: string;
  trend: 'up' | 'down' | 'neutral';
  caption: string;
}

export const mockDashboardMetrics: OperationsMetric[] = [
  {
    title: 'Active Voice Clones',
    value: '42 Models',
    change: '+14% MoM',
    trend: 'up',
    caption: 'All models verified SHA-256',
  },
  {
    title: 'Active Studio Licenses',
    value: '188 Contracts',
    change: '+22 Contracts',
    trend: 'up',
    caption: '12 awaiting counter-signature',
  },
  {
    title: 'Monthly Recurring Royalty',
    value: '$124,850',
    change: '+18.4%',
    trend: 'up',
    caption: 'Next payout in 6 days',
  },
  {
    title: 'Synthesis API Volume',
    value: '4.8M Secs',
    change: '-2.1%',
    trend: 'down',
    caption: 'Avg Latency: 42ms TTFT',
  },
];

export const mockThroughputData = [
  { time: '00:00', requests: 120, latency: 45 },
  { time: '04:00', requests: 80, latency: 38 },
  { time: '08:00', requests: 340, latency: 42 },
  { time: '12:00', requests: 590, latency: 51 },
  { time: '16:00', requests: 840, latency: 44 },
  { time: '20:00', requests: 620, latency: 41 },
  { time: '23:59', requests: 410, latency: 39 },
];

export const mockRecentActivity = [
  {
    id: 'act_01',
    event: 'Acoustic Anchor Stamped',
    target: 'Elena Rostova (Siren Of The North)',
    time: '4 minutes ago',
    badge: 'WATERMARK',
    badgeVariant: 'amber' as const,
  },
  {
    id: 'act_02',
    event: 'Enterprise License Approved',
    target: 'Cyberpunk Odyssey (CD Projekt Red Studio)',
    time: '28 minutes ago',
    badge: 'LICENSED',
    badgeVariant: 'success' as const,
  },
  {
    id: 'act_03',
    event: 'Royalty Escrow Disbursed',
    target: '$14,250 to Vault 0x8F9...21B',
    time: '1 hour ago',
    badge: 'PAYOUT',
    badgeVariant: 'neutral' as const,
  },
  {
    id: 'act_04',
    event: 'New Biometric Onboarding',
    target: 'Kaelen Thorne Voice Persona',
    time: '3 hours ago',
    badge: 'ONBOARDING',
    badgeVariant: 'amber' as const,
  },
];

