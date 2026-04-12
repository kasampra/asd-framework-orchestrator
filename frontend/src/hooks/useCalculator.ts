// frontend/src/hooks/useCalculator.ts
import { useState } from 'react';
import apiClient, { ApiError } from '../lib/apiClient';
import type { CalculationRequest, CalculationResponse } from '../types/api';

export const useCalculator = () => {
  const [result, setResult] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const calculate = async (request: CalculationRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      const { data } = await apiClient.post<CalculationResponse>('/api/v1/calculate', request);
      setResult(data.result);
      return data;
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message || 'An error occurred');
      } else {
        setError('Network error. Please try again.');
      }
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return { result, error, isLoading, calculate };
};