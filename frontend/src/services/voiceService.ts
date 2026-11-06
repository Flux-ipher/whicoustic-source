/**
 * Whicoustic Voice Service
 * Connects to real backend endpoints:
 * - GET /api/v1/voices/
 * - GET /api/v1/voices/{id}
 * - POST /api/v1/voices/upload
 * - DELETE /api/v1/voices/{id}
 * - GET /api/v1/voices/{id}/stream
 */

import { apiClient } from './apiClient';

export interface VoiceResponse {
  id: string;
  name: string;
  description?: string | null;
  status: string;
  duration: number;
  quality_score?: number | null;
  sample_rate?: number | null;
  file_size?: number | null;
  created_at: string;
  updated_at: string;
}

export interface VoiceUploadResponse {
  voice_id: string;
  name: string;
  status: string;
  duration: number;
  quality_score: number;
  upload_time: string;
  next_steps: string;
}

export const voiceService = {
  /**
   * Fetch all voices for the authenticated user
   */
  async getVoices(): Promise<VoiceResponse[]> {
    return apiClient.get<VoiceResponse[]>('/api/v1/voices/');
  },

  /**
   * Fetch a single voice by ID
   */
  async getVoice(voiceId: string): Promise<VoiceResponse> {
    return apiClient.get<VoiceResponse>(`/api/v1/voices/${voiceId}`);
  },

  /**
   * Upload raw vocal WAV/audio file to create a voice persona
   */
  async uploadVoice(
    file: Blob | File,
    name: string,
    description?: string
  ): Promise<VoiceUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    if (description) {
      formData.append('description', description);
    }
    return apiClient.upload<VoiceUploadResponse>('/api/v1/voices/upload', formData);
  },

  /**
   * Delete a voice model by ID
   */
  async deleteVoice(voiceId: string): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>(`/api/v1/voices/${voiceId}`);
  },

  /**
   * Get direct streaming URL for proxy audio stream
   */
  getStreamUrl(voiceId: string): string {
    return apiClient.buildUrl(`/api/v1/voices/${voiceId}/stream`);
  },

  /**
   * Get preview audio URL
   */
  getPreviewUrl(voiceId: string): string {
    return apiClient.buildUrl(`/api/v1/voices/${voiceId}/preview`);
  },
};
