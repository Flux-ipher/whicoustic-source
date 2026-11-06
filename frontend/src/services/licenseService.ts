/**
 * Whicoustic License Service
 * Connects to real backend endpoints:
 * - GET /api/v1/licenses/marketplace/browse
 * - GET /api/v1/licenses/
 * - GET /api/v1/licenses/{id}
 * - PUT /api/v1/licenses/{id}
 * - GET /api/v1/licenses/{id}/stats
 * - GET /api/v1/licenses/{id}/disbursements
 */

import { apiClient } from './apiClient';

export interface MarketplaceLicenseItem {
  id: string;
  voice_id: string;
  name: string;
  description?: string | null;
  license_type: string;
  price: number;
  currency: string;
  territory?: string[] | null;
  allowed_use_cases?: string[] | null;
  duration_days?: number | null;
  usage_limit?: number | null;
  creator_name?: string;
  voice_preview_url?: string;
}

export interface LicenseResponse {
  id: string;
  voice_id: string;
  name: string;
  description?: string | null;
  license_type: string;
  price?: number | null;
  currency: string;
  duration_days?: number | null;
  usage_limit?: number | null;
  territory?: string[] | null;
  allowed_use_cases?: string[] | null;
  restrictions?: Record<string, unknown> | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EscrowDisbursement {
  id: string;
  royalty_stream: string;
  licensee: string;
  gross_amount: number;
  platform_fee: number;
  net_amount: number;
  status: string;
  disbursed_at: string;
}

export interface EscrowDisbursementResponse {
  license_id: string;
  gross_escrow: number;
  platform_fee: number;
  net_disbursement: number;
  currency: string;
  disbursements: EscrowDisbursement[];
}

export interface LicenseStats {
  license_id: string;
  license_name: string;
  total_uses: number;
  usage_limit?: number | null;
  usage_remaining?: number | null;
  unique_users: number;
  total_text_length: number;
  total_audio_duration: number;
  total_revenue: number;
  currency: string;
  last_used?: string | null;
  created_at: string;
}

export const licenseService = {
  /**
   * Browse available public licenses in the marketplace
   */
  async browseMarketplace(params?: {
    license_type?: string;
    min_price?: number;
    max_price?: number;
    territory?: string;
    limit?: number;
  }): Promise<MarketplaceLicenseItem[]> {
    const query = new URLSearchParams();
    if (params?.license_type && params.license_type !== 'All') {
      query.set('license_type', params.license_type);
    }
    if (params?.min_price !== undefined) query.set('min_price', String(params.min_price));
    if (params?.max_price !== undefined) query.set('max_price', String(params.max_price));
    if (params?.territory) query.set('territory', params.territory);
    if (params?.limit) query.set('limit', String(params.limit));

    const qs = query.toString();
    const endpoint = `/api/v1/licenses/marketplace/browse${qs ? `?${qs}` : ''}`;
    return apiClient.get<MarketplaceLicenseItem[]>(endpoint);
  },

  /**
   * List licenses created by the current user
   */
  async getUserLicenses(params?: {
    voice_id?: string;
    license_type?: string;
    is_active?: boolean;
  }): Promise<LicenseResponse[]> {
    const query = new URLSearchParams();
    if (params?.voice_id) query.set('voice_id', params.voice_id);
    if (params?.license_type && params.license_type !== 'ALL') query.set('license_type', params.license_type);
    if (params?.is_active !== undefined) query.set('is_active', String(params.is_active));

    const qs = query.toString();
    const endpoint = `/api/v1/licenses/${qs ? `?${qs}` : ''}`;
    return apiClient.get<LicenseResponse[]>(endpoint);
  },

  /**
   * Get single license by ID
   */
  async getLicense(licenseId: string): Promise<LicenseResponse> {
    return apiClient.get<LicenseResponse>(`/api/v1/licenses/${licenseId}`);
  },

  /**
   * Update license fields
   */
  async updateLicense(
    licenseId: string,
    updates: Partial<LicenseResponse>
  ): Promise<LicenseResponse> {
    return apiClient.put<LicenseResponse>(`/api/v1/licenses/${licenseId}`, updates);
  },

  /**
   * Get usage statistics for a license
   */
  async getLicenseStats(licenseId: string): Promise<LicenseStats> {
    return apiClient.get<LicenseStats>(`/api/v1/licenses/${licenseId}/stats`);
  },

  /**
   * Get disbursements for a license or aggregated user disbursements
   */
  async getDisbursements(licenseId?: string): Promise<EscrowDisbursementResponse | null> {
    if (licenseId) {
      try {
        return await apiClient.get<EscrowDisbursementResponse>(
          `/api/v1/licenses/${licenseId}/disbursements`
        );
      } catch {
        // If 404, return empty disbursement
        return {
          license_id: licenseId,
          gross_escrow: 0,
          platform_fee: 0,
          net_disbursement: 0,
          currency: 'USD',
          disbursements: [],
        };
      }
    }

    // If no specific licenseId provided, check user licenses
    try {
      const licenses = await this.getUserLicenses();
      if (!licenses || licenses.length === 0) {
        return {
          license_id: '',
          gross_escrow: 0,
          platform_fee: 0,
          net_disbursement: 0,
          currency: 'USD',
          disbursements: [],
        };
      }

      // Fetch disbursements for first license if exists
      const first = licenses[0];
      return await this.getDisbursements(first.id);
    } catch {
      return {
        license_id: '',
        gross_escrow: 0,
        platform_fee: 0,
        net_disbursement: 0,
        currency: 'USD',
        disbursements: [],
      };
    }
  },
};
