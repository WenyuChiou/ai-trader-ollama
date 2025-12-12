// API Configuration
// This file allows easy switching between development and production API endpoints

const API_CONFIG = {
    // Development environment (local)
    development: 'http://127.0.0.1:8000',
    
    // Production environment (backend API URL)
    // This URL is automatically used when accessing via GitHub Pages
    // TODO: Update this to your Vercel deployment URL after deploying to Vercel
    // Example: 'https://ai-trader-ollama.vercel.app'
    // See docs/RAILWAY_TO_VERCEL_MIGRATION.md for deployment instructions
    production: 'https://your-app.vercel.app',  // Update with your Vercel URL
    
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
        
        // Check if running on GitHub Pages (github.io domain) - MUST CHECK FIRST
        // This prevents github.io from being caught by the generic hostname check below
        if (hostname.includes('github.io')) {
            // GitHub Pages deployment - use production backend URL
            // User needs to update 'production' URL in this file
            return this.production;
        }
        
        // If accessing via IP address (shared website), use same IP with port 8000
        // This handles cases like: http://192.168.4.24:3000 -> http://192.168.4.24:8000
        const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
        if (ipv4Regex.test(hostname)) {
            // Use same protocol and IP, but port 8000 for backend
            return `${protocol}//${hostname}:8000`;
        }
        
        // If accessing via local hostname (e.g., computer-name.local), use same hostname with port 8000
        // This handles cases like: http://computer-name.local:3000 -> http://computer-name.local:8000
        // NOTE: Only check .local, not generic '.' to avoid matching github.io
        if (hostname.includes('.local')) {
            // For local network sharing, assume backend is on same host with port 8000
            return `${protocol}//${hostname}:8000`;
        }
        
        // Otherwise use production URL (for deployed environments)
        return this.production;
    }
};

// Export for use in monitor.html
window.API_CONFIG = API_CONFIG;

