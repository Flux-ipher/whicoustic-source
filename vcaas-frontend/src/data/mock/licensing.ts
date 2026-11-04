export interface LicensingRequest {
  id: string;
  studioName: string;
  studioLogo?: string;
  voiceId: string;
  voiceName: string;
  projectTitle: string;
  projectType: 'AAA Game' | 'Feature Film' | 'Global TV Commercial' | 'Podcast Series' | 'Audiobook';
  territory: 'Worldwide' | 'North America' | 'EMEA' | 'Asia-Pacific';
  proposedFee: number;
  royaltySplitPct: number;
  durationMonths: number;
  submittedDate: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  forensicWatermarkReq: boolean;
}

export const mockLicensingRequests: LicensingRequest[] = [
  {
    id: 'lic_8801',
    studioName: 'Obsidian Interactive Games',
    voiceId: 'voice_002',
    voiceName: 'Marcus Vance (Iron Vanguard)',
    projectTitle: 'Chronicles of the Void IV',
    projectType: 'AAA Game',
    territory: 'Worldwide',
    proposedFee: 48000,
    royaltySplitPct: 18.5,
    durationMonths: 24,
    submittedDate: '2026-11-03',
    status: 'PENDING',
    forensicWatermarkReq: true,
  },
  {
    id: 'lic_8802',
    studioName: 'A24 Independent Films',
    voiceId: 'voice_001',
    voiceName: 'Elena Rostova (Siren Of The North)',
    projectTitle: 'The Echo of Glass',
    projectType: 'Feature Film',
    territory: 'Worldwide',
    proposedFee: 75000,
    royaltySplitPct: 15.0,
    durationMonths: 36,
    submittedDate: '2026-11-02',
    status: 'PENDING',
    forensicWatermarkReq: true,
  },
  {
    id: 'lic_8803',
    studioName: 'Bayer Global Health',
    voiceId: 'voice_005',
    voiceName: 'Zara Khemir (Atlas Nexus)',
    projectTitle: 'Pan-European AI Health Companion',
    projectType: 'Global TV Commercial',
    territory: 'EMEA',
    proposedFee: 32000,
    royaltySplitPct: 16.0,
    durationMonths: 12,
    submittedDate: '2026-10-29',
    status: 'APPROVED',
    forensicWatermarkReq: true,
  },
  {
    id: 'lic_8804',
    studioName: 'Penguin Random House Audio',
    voiceId: 'voice_004',
    voiceName: 'Julian Sterling (The Royal Chronicler)',
    projectTitle: 'The Byzantine Dynasty Trilogy',
    projectType: 'Audiobook',
    territory: 'Worldwide',
    proposedFee: 21500,
    royaltySplitPct: 12.0,
    durationMonths: 48,
    submittedDate: '2026-10-25',
    status: 'APPROVED',
    forensicWatermarkReq: true,
  },
  {
    id: 'lic_8805',
    studioName: 'Vortex Deepfake Ads (Unregistered)',
    voiceId: 'voice_001',
    voiceName: 'Elena Rostova',
    projectTitle: 'Automated Viral Video Generation',
    projectType: 'Global TV Commercial',
    territory: 'Worldwide',
    proposedFee: 4000,
    royaltySplitPct: 5.0,
    durationMonths: 6,
    submittedDate: '2026-10-20',
    status: 'REJECTED',
    forensicWatermarkReq: false,
  },
];

