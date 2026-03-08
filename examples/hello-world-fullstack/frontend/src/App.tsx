// frontend/src/App.tsx
import React, { useState } from 'react';
import './App.css';

import { simulateLogin, setAuthToken, getAuthToken, clearAuthToken } from './api/auth';
import { getHealth, postHello } from './api/endpoints';

function App() {
  const [organisationId, setOrganisationId] = useState('');
  const [name, setName] = useState('Alice');
  const [token, setToken] = useState<string | null>(getAuthToken());
  const [healthData, setHealthData] = useState<{ status: string; timestamp: string } | null>(null);
  const [helloMessage, setHelloMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const { token } = await simulateLogin({ organisation_id: organisationId });
      setAuthToken(token);
      setToken(token);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    clearAuthToken();
    setToken(null);
    setHealthData(null);
    setHelloMessage('');
  };

  const fetchHealth = async () => {
    try {
      const data = await getHealth();
      setHealthData(data);
    } catch (err: any) {
      setError('Failed to fetch health: ' + err.message);
    }
  };

  const handleSayHello = async () => {
    if (!token) {
      setError('Please log in first.');
      return;
    }

    try {
      const { message } = await postHello({ name });
      setHelloMessage(message);
    } catch (err: any) {
      setError('Failed to say hello: ' + err.message);
    }
  };

  return (
    <div className="app">
      <header>
        <h1>Agentic SDLC Hello World</h1>
      </header>

      {!token ? (
        <section className="login-form">
          <h2>Login (Demo)</h2>
          <form onSubmit={handleLogin}>
            <input
              type="text"
              placeholder="Organisation ID"
              value={organisationId}
              onChange={(e) => setOrganisationId(e.target.value)}
              required
            />
            <button type="submit" disabled={loading}>
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>
          {error && <p className="error">{error}</p>}
        </section>
      ) : (
        <div className="dashboard">
          <div className="user-info">
            <span>Logged in as: <strong>{organisationId}</strong></span>
            <button onClick={handleLogout}>Logout</button>
          </div>

          <section className="api-section">
            <h2>Health Check</h2>
            <button onClick={fetchHealth}>Fetch /health</button>
            {healthData && (
              <pre>{JSON.stringify(healthData, null, 2)}</pre>
            )}
          </section>

          <section className="api-section">
            <h2>Say Hello</h2>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your name"
            />
            <button onClick={handleSayHello}>POST /hello</button>
            {helloMessage && <p><strong>Response:</strong> {helloMessage}</p>}
          </section>

          {error && <p className="error">{error}</p>}
        </div>
      )}
    </div>
  );
}

export default App;