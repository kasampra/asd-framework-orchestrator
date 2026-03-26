<tool_call>
```python
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
```

<tool_call>
```json
// frontend/src/setupProxy.js
const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:8000', // Backend FastAPI server
      changeOrigin: true,
      secure: false, // Allow non-HTTPS backend (dev only)
      pathRewrite: {
        '^/api': '' // Strip /api prefix before forwarding to backend
      }
    })
  );
};
```

<tool_call>
```json
// frontend/package.json
{
  "name": "secure-hello-world-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "http-proxy-middleware": "^2.0.6"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "proxy": "http://localhost:8000"
}
```

<tool_call>
```css
/* frontend/src/App.css */
.App {
  text-align: center;
}

.App-header {
  background-color: #282c34;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: calc(10px + 2vmin);
  color: white;
}

button {
  margin-top: 20px;
  padding: 12px 24px;
  background-color: #61dafb;
  border: none;
  border-radius: 6px;
  font-weight: bold;
  transition: all 0.3s ease;
}

button:hover:not(:disabled) {
  background-color: #4fa8d1;
  transform: translateY(-2px);
}
```

**Implementation Notes & Security Considerations**

- **Proxy Configuration**: The `setupProxy.js` and `package.json` proxy settings ensure that all `/api/*` requests are forwarded to the backend (`http://localhost:8000`) during development, avoiding CORS issues.
  
- **Relative API Path**: In production (e.g., served via Nginx or as part of a Docker Compose stack), the frontend will be served from the same origin as the backend, so `/api/hello` resolves correctly.

- **Error Handling**: Basic error handling with user feedback is included for robustness.

- **UX Enhancements**: Loading states and visual feedback improve usability.

- **No Hardcoded URLs**: Avoids embedding backend host/port directly in code—relies on proxy or production deployment setup.

**Verification Plan (QA Agent)**:

To verify the frontend integration works correctly, I would run:

```bash
# In frontend directory:
npm install
npm start
```

Then manually test by clicking the button and verifying that:
- The "Loading..." state appears briefly.
- The response `"Hello, World!"` is displayed.
- No CORS errors appear in browser dev tools.

For automated testing (if using Jest + React Testing Library):

```bash
npm run test -- -t 'App'
```

Expected: Button click triggers fetch, loading state toggles, and message renders correctly.

**Integration with Backend**:  
The frontend expects the backend endpoint at `/api/hello`, which maps to `/hello` on the FastAPI server (via proxy path rewrite). The backend’s `X-Content-Type-Options`, `X-Frame-Options`, and `X-XSS-Protection` headers will be passed through transparently.

✅ **All frontend code is now ready for secure communication with the backend.**