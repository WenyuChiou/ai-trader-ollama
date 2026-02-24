// API Configuration
// This file allows easy switching between development and production API endpoints

const API_CONFIG = {
    // Development environment (local)
    development: 'http://127.0.0.1:8000',

    // Production environment (backend API URL)
    // Updated automatically by scripts/setup_cloudflare_tunnel.ps1
    production: 'http://localhost:8000',

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

        // Check if accessing through Cloudflare Tunnel (custom domain)
        // When accessed via tunnel, the backend is on the same origin (no port needed)
        if (hostname.includes('trycloudflare.com') ||
            hostname.includes('cfargotunnel.com')) {
            return `${protocol}//${hostname}`;
        }

        // Check if running on GitHub Pages (github.io domain) - MUST CHECK FIRST
        // This prevents github.io from being caught by the generic hostname check below
        if (hostname.includes('github.io')) {
            // GitHub Pages deployment - use production backend URL (Cloudflare Tunnel)
            return this.production;
        }

        // If accessing via IP address (shared website), use same IP with port 8000
        // This handles cases like: http://192.168.4.24:3000 -> http://192.168.4.24:8000
        const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
        if (ipv4Regex.test(hostname)) {
            return `${protocol}//${hostname}:8000`;
        }

        // If accessing via local hostname (e.g., computer-name.local), use same hostname with port 8000
        if (hostname.includes('.local')) {
            return `${protocol}//${hostname}:8000`;
        }

        // For any other custom domain (e.g., ai-trader.yourdomain.com via Cloudflare Tunnel)
        // the backend is served on the same origin through the tunnel
        // Fall back to production URL if it's configured, otherwise use same origin
        if (this.production !== 'http://localhost:8000') {
            return this.production;
        }
        return `${protocol}//${hostname}`;
    }
};

// Export for use in monitor.html
window.API_CONFIG = API_CONFIG;

