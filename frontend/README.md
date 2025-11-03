# AI Trader Frontend

React + TypeScript + Vite frontend for monitoring AI Trader portfolio in real-time.

---

## 🚀 Quick Start

### Prerequisites

```bash
# Node.js 18+ required
node --version

# npm or yarn
npm --version
```

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Frontend will start at `http://localhost:5173`

### Build

```bash
npm run build
```

Output will be in `dist/` directory.

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file (or copy from `.env.example`):

```env
# Backend API base URL
VITE_API_BASE=http://localhost:8000

# Development mode
VITE_DEV_MODE=true
```

**Default**: `http://localhost:8000` (if not set)

---

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── SimpleMonitor.tsx    # Main monitoring dashboard
│   │   └── SimpleMonitor.css    # Dashboard styles
│   ├── utils/
│   │   └── api.ts               # API utility functions
│   ├── App.tsx                  # Main app component
│   └── main.tsx                 # Entry point
├── package.json
├── vite.config.ts              # Vite configuration
└── tsconfig.json               # TypeScript configuration
```

---

## 🔌 API Integration

### Endpoints Used

- `GET /api/portfolio/real-time` - Real-time portfolio snapshot
- `GET /api/portfolio/equity-history` - Historical equity data
- `GET /` - API health check

### API Utility Functions

Located in `src/utils/api.ts`:

- `fetchRealTimePortfolio()` - Get current portfolio data
- `fetchEquityHistory()` - Get historical data for charts
- `checkApiHealth()` - Check if API is available
- `getApiBase()` - Get configured API base URL

---

## 🎨 Features

### Simple Monitor Dashboard

- **Real-time Portfolio Tracking**
  - Total Value, Total P&L (with %)
  - Cash and Equity Value
  - Auto-refresh every 30 seconds

- **Position Details**
  - Symbol, Quantity
  - Average Cost vs Current Price
  - Market Value
  - Unrealized P&L (amount and %)

- **Connection Status**
  - Visual indicator (● = connected, ○ = disconnected)
  - API address display
  - Last update timestamp

---

## 🛠️ Development

### Available Scripts

```bash
# Development server (with hot reload)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run type-check  # if configured
```

### Code Structure

- **Components**: React functional components with hooks
- **Utils**: Shared utility functions (API calls, helpers)
- **Styles**: CSS modules for component styling
- **Types**: TypeScript interfaces for type safety

---

## 🔧 Troubleshooting

### Frontend won't start

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### API connection errors

1. Check backend API is running: `curl http://localhost:8000/`
2. Verify `VITE_API_BASE` in `.env` matches backend address
3. Check browser console for CORS errors

### Build errors

```bash
# Check TypeScript errors
npx tsc --noEmit

# Check for missing dependencies
npm install
```

---

## 📦 Dependencies

**Main:**
- `react` - UI library
- `react-dom` - React DOM renderer

**Dev:**
- `vite` - Build tool
- `typescript` - Type safety
- `@vitejs/plugin-react` - Vite React plugin

**Note**: No external UI libraries (like Material-UI) to keep it lightweight.

---

## 🌐 Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

**Required Features:**
- ES6+ support
- Fetch API
- CSS Grid/Flexbox

---

## 📝 Notes

- Frontend is designed to be simple and lightweight
- No state management library (uses React hooks)
- API calls are centralized in `utils/api.ts`
- All text is in English for consistency
