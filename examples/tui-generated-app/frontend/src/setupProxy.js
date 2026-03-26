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