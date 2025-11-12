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
        const hostname = window.location.hostname;
        const protocol = window.location.protocol;
        
        // Check if running on localhost
        if (hostname === 'localhost' || 
            hostname === '127.0.0.1' ||
            hostname === '') {
            return this.development;
        }
        
        // If accessing via IP address (shared website), use same IP with port 8000
        // This handles cases like: http://192.168.4.24:3000 -> http://192.168.4.24:8000
        const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
        if (ipv4Regex.test(hostname)) {
            // Use same protocol and IP, but port 8000 for backend
            return `${protocol}//${hostname}:8000`;
        }
        
        // If accessing via hostname (e.g., computer-name.local), use same hostname with port 8000
        // This handles cases like: http://computer-name.local:3000 -> http://computer-name.local:8000
        if (hostname.includes('.local') || hostname.includes('.')) {
            // For local network sharing, assume backend is on same host with port 8000
            return `${protocol}//${hostname}:8000`;
        }
        
        // Check if running on GitHub Pages (github.io domain)
        if (hostname.includes('github.io')) {
            // GitHub Pages deployment - use production backend URL
            // User needs to update 'production' URL in this file
            return this.production;
        }
        
        // Otherwise use production URL (for deployed environments)
        return this.production;
    }
};

// Export for use in monitor.html
window.API_CONFIG = API_CONFIG;

