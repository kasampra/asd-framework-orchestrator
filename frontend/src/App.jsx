// frontend/src/App.jsx
import { useState, useEffect } from 'react';

function App() {
  const [status, setStatus] = useState('Loading...');

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => setStatus(JSON.stringify(data)))
      .catch(err => setStatus(`Error: ${err.message}`));
  }, []);

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>Health Check</h1>
      <p>Status: {status}</p>
    </div>
  );
}

export default App;