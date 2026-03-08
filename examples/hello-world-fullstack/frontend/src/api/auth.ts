// frontend/src/api/auth.ts
import { apiClient } from './client';

export interface LoginRequest {
  organisation_id: string;
}

export interface LoginResponse {
  token: string;
}

/**
 * Simulates login by returning a JWT for demo purposes.
 * In production, this would call `/auth/login` and validate credentials.
 */
export const simulateLogin = async ({ organisation_id }: LoginRequest): Promise<LoginResponse> => {
  // For MVP: generate a dummy JWT with org ID
  // Real implementation should POST to backend auth endpoint
  const response = await apiClient.post<LoginResponse>('/auth/login', { organisation_id });
  return response.data;
};

/**
 * Store the token securely (⚠️ for demo only — use httpOnly cookies in prod)
 */
export const setAuthToken = (token: string): void => {
  localStorage.setItem('auth_token', token);
};

export const getAuthToken = (): string | null => {
  return localStorage.getItem('auth_token');
};

export const clearAuthToken = (): void => {
  localStorage.removeItem('auth_token');
};