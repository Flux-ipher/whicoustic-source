export interface CloneJob {
  id: string;
  name: string;
  sourceAudioDurationSec: number;
  qualityScore: number;
  status: 'READY' | 'SYNTHESIZING' | 'TRAINING';
  createdDate: string;
  watermarkSha256: string;
  latencyMs: number;
}

export const mockCloneJobs: CloneJob[] = [
  {
    id: 'clone_v1',
    name: 'Elena Rostova — Intimate Whisper Model',
    sourceAudioDurationSec: 360,
    qualityScore: 99.4,
    status: 'READY',
    createdDate: '2026-10-28',
    watermarkSha256: '4080c0aea1ea4cc3a63a13901af1baaa',
    latencyMs: 38,
  },
  {
    id: 'clone_v2',
    name: 'Elena Rostova — Dynamic Keynote Model',
    sourceAudioDurationSec: 420,
    qualityScore: 98.7,
    status: 'READY',
    createdDate: '2026-10-25',
    watermarkSha256: '76da6e81e2804561b6fff5d5f6d917c0',
    latencyMs: 44,
  },
  {
    id: 'clone_v3',
    name: 'Experimental French Accent Synthesis',
    sourceAudioDurationSec: 180,
    qualityScore: 94.2,
    status: 'SYNTHESIZING',
    createdDate: '2026-11-04',
    watermarkSha256: 'edec6aa60cbb428a9230b356daf56787',
    latencyMs: 52,
  },
];

