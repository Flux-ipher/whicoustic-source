export interface VoiceTalent {
  id: string;
  name: string;
  stageName: string;
  avatar: string;
  category: 'Cinematic' | 'Commercial' | 'Video Game' | 'Audiobook' | 'Corporate' | 'Character';
  gender: 'Female' | 'Male' | 'Non-Binary';
  accent: string;
  language: string;
  sampleAudio: string;
  hourlyRate: number;
  royaltyFloorPct: number;
  sha256Hash: string;
  verified: boolean;
  activeLicenses: number;
  description: string;
  tags: string[];
}

export const mockMarketplaceVoices: VoiceTalent[] = [
  {
    id: 'voice_001',
    name: 'Elena Rostova',
    stageName: 'Siren Of The North',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&auto=format&fit=crop&q=80',
    category: 'Cinematic',
    gender: 'Female',
    accent: 'Slavic-British / Mid-Atlantic',
    language: 'English, Russian, French',
    sampleAudio: '/audio/sample1.mp3',
    hourlyRate: 420,
    royaltyFloorPct: 15.0,
    sha256Hash: '4080c0aea1ea4cc3a63a13901af1baaa',
    verified: true,
    activeLicenses: 34,
    description: 'Dark, resonant cinematic timber with crisp enunciation and dramatic range. Ideal for thriller games and luxury narrative.',
    tags: ['Ethereal', 'Sultry', 'Narrative', 'Forensic Watermarked'],
  },
  {
    id: 'voice_002',
    name: 'Marcus Vance',
    stageName: 'Iron Vanguard',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&auto=format&fit=crop&q=80',
    category: 'Video Game',
    gender: 'Male',
    accent: 'American Deep Baritone',
    language: 'English, Spanish',
    sampleAudio: '/audio/sample2.mp3',
    hourlyRate: 550,
    royaltyFloorPct: 18.5,
    sha256Hash: '76da6e81e2804561b6fff5d5f6d917c0',
    verified: true,
    activeLicenses: 62,
    description: 'Commanding gravel and battle-tested authority. Used in AAA sci-fi franchises and historical war epics.',
    tags: ['Gravelly', 'Authoritative', 'Warrior', 'Battle Cry'],
  },
  {
    id: 'voice_003',
    name: 'Aoi Tanaka',
    stageName: 'Neo Tokyo Synapse',
    avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=200&auto=format&fit=crop&q=80',
    category: 'Commercial',
    gender: 'Female',
    accent: 'Bilingual Tokyo / Silicon Valley',
    language: 'Japanese, English',
    sampleAudio: '/audio/sample3.mp3',
    hourlyRate: 380,
    royaltyFloorPct: 12.0,
    sha256Hash: 'edec6aa60cbb428a9230b356daf56787',
    verified: true,
    activeLicenses: 89,
    description: 'Youthful, optimistic, and technologically articulate tone designed for next-gen consumer hardware and automotive AI.',
    tags: ['Conversational', 'Tech', 'Upbeat', 'Bilingual'],
  },
  {
    id: 'voice_004',
    name: 'Julian Sterling',
    stageName: 'The Royal Chronicler',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=200&auto=format&fit=crop&q=80',
    category: 'Audiobook',
    gender: 'Male',
    accent: 'Received Pronunciation (British)',
    language: 'English',
    sampleAudio: '/audio/sample4.mp3',
    hourlyRate: 310,
    royaltyFloorPct: 10.0,
    sha256Hash: 'ba4c0179092a41ccba52d6e309828592',
    verified: true,
    activeLicenses: 114,
    description: 'Warm literary cadence with soothing historical depth. Narrator of 40+ bestsellers with zero forensic artifacts.',
    tags: ['Warm', 'Literary', 'Scholarly', 'Documentary'],
  },
  {
    id: 'voice_005',
    name: 'Zara Khemir',
    stageName: 'Atlas Nexus',
    avatar: 'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=200&auto=format&fit=crop&q=80',
    category: 'Corporate',
    gender: 'Female',
    accent: 'Global Neutral / Pan-European',
    language: 'English, Arabic, French',
    sampleAudio: '/audio/sample5.mp3',
    hourlyRate: 460,
    royaltyFloorPct: 16.0,
    sha256Hash: 'd68842c6a74c43bda292ecb90282a191',
    verified: true,
    activeLicenses: 47,
    description: 'Sophisticated, reassuring, and multilingual enterprise communicator for keynote product launches and governance boards.',
    tags: ['Executive', 'Multilingual', 'Polished', 'Fintech'],
  },
  {
    id: 'voice_006',
    name: 'Kaelen Thorne',
    stageName: 'Shadow Walker',
    avatar: 'https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=200&auto=format&fit=crop&q=80',
    category: 'Character',
    gender: 'Non-Binary',
    accent: 'Celtic / Nordic Fantasy',
    language: 'English, Gaelic',
    sampleAudio: '/audio/sample6.mp3',
    hourlyRate: 390,
    royaltyFloorPct: 14.5,
    sha256Hash: 'c3e8bff43d0d42acbb0027d1e3b7539d',
    verified: true,
    activeLicenses: 28,
    description: 'Whispered rasps, uncanny shapeshifter inflections, and mystical timbre for dark fantasy RPGs.',
    tags: ['Fantasy', 'Raspy', 'Shapeshifter', 'Mystic'],
  },
];

