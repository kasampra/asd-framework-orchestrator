// frontend/src/components/CalculatorForm.tsx
import { useState } from 'react';
import apiClient, { ApiError } from '../lib/apiClient';
import type { CalculationRequest, CalculationResponse } from '../types/api';

const CalculatorForm = () => {
  const [a, setA] = useState<number | ''>('');
  const [b, setB] = useState<number | ''>('');
  const [operation, setOperation] = useState<CalculationRequest['operation']>('add');
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Input validation
    if (a === '' || b === '') {
      setError('Please enter valid numbers');
      return;
    }
    
    if (operation === 'divide' && b === 0) {
      setError('Division by zero is not allowed');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const request: CalculationRequest = {
        operation,
        a: Number(a),
        b: Number(b)
      };

      const { data } = await apiClient.post<CalculationResponse>('/api/v1/calculate', request);
      setResult(`Result: ${data.result}`);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message || 'An error occurred');
      } else {
        setError('Network error. Please check your connection.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="calculator-form">
      <h2>Secure Calculator</h2>
      
      {error && <div className="error">{error}</div>}
      {result && <div className="success">{result}</div>}
      
      <form onSubmit={handleSubmit}>
        <input
          type="number"
          value={a}
          onChange={(e) => setA(e.target.valueAsNumber)}
          placeholder="First number"
          required
        />
        
        <select 
          value={operation} 
          onChange={(e) => setOperation(e.target.value as CalculationRequest['operation'])}
        >
          <option value="add">Add (+)</option>
          <option value="subtract">Subtract (-)</option>
          <option value="multiply">Multiply (×)</option>
          <option value="divide">Divide (÷)</option>
        </select>
        
        <input
          type="number"
          value={b}
          onChange={(e) => setB(e.target.valueAsNumber)}
          placeholder="Second number"
          required
        />
        
        <button 
          type="submit" 
          disabled={isLoading}
        >
          {isLoading ? 'Calculating...' : 'Calculate'}
        </button>
      </form>
    </div>
  );
};

export default CalculatorForm;