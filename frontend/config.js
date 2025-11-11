// API Configuration
// This file allows easy switching between development and production API endpoints

const API_CONFIG = {
    // Development environment (local)
    development: 'http://127.0.0.1:8000',
    
    // Production environment (update this with your deployed backend URL)
    // Examples:
    // - Railway: 'https://your-app.railway.app'
    // - Render: 'https://your-app.onrender.com'
    // - Heroku: 'https://your-app.herokuapp.com'
    // - Custom: 'https://api.yourdomain.com'
    production: 'https://your-api-server.com',
    
    // Auto-detect environment
    get apiUrl() {
        // Check if running on localhost
        if (window.location.hostname === 'localhost' || 
            window.location.hostname === '127.0.0.1' ||
            window.location.hostname === '') {
            return this.development;
        }
        // Otherwise use production URL
        return this.production;
    }
};

// Export for use in monitor.html
window.API_CONFIG = API_CONFIG;

