// frontend/src/types/api.d.ts
export interface CalculationRequest {
  operation: 'add' | 'subtract' | 'multiply' | 'divide';
  a: number;
  b: number;
}

export interface CalculationResponse {
  result: number;
  timestamp: string;
  requestId?: string;
}

export interface ApiErrorDetails {
  message: string;
  field?: string;
  code?: string;
}