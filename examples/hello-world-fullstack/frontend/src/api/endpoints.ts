// frontend/src/api/endpoints.ts
import { apiClient } from './client';

export interface HealthResponse {
  status: string;
  timestamp: string;
}

export const getHealth = async (): Promise<HealthResponse> => {
  const response = await apiClient.get<HealthResponse>('/health');
  return response.data;
};

export interface HelloRequest {
  name?: string;
}

export interface HelloResponse {
  message: string;
}

export const postHello = async ({ name = 'World' }: HelloRequest = {}): Promise<HelloResponse> => {
  const response = await apiClient.post<HelloResponse>('/hello', { name });
  return response.data;
};