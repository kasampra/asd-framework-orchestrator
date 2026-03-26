# frontend/src/App.tsx
import React from 'react';
import './App.css';

function App() {
  const [message, setMessage] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string | null>(null);

  const fetchHello = async () => {
    setLoading(true);
    setError(null);
    try {
      // Use relative path to avoid CORS issues during development
      const response = await fetch('/api/hello', {
        method: 'GET',
        headers: {
          'Accept': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setMessage(data.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Secure Hello World</h1>
        <p>A sleek, secure frontend for the FastAPI backend.</p>

        <button 
          onClick={fetchHello} 
          disabled={loading}
          style={{
            padding: '10px 20px',
            fontSize: '16px',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.7 : 1
          }}
        >
          {loading ? 'Loading...' : 'Get Hello Message'}
        </button>

        {error && (
          <div style={{ color: 'red', marginTop: '20px' }}>
            Error: {error}
          </div>
        )}

        {message && (
          <div 
            style={{
              marginTop: '20px',
              padding: '15px',
              backgroundColor: '#f0f8ff',
              borderRadius: '8px',
              border: '1px solid #a0c4ff'
            }}
          >
            <strong>Response:</strong> {message}
          </div>
        )}
      </header>
    </div>
  );
}

export default App;