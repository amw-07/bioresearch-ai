# Biotech Lead Generator - Frontend

A modern, production-ready Next.js frontend for the Biotech Lead Generator platform.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ installed
- Backend API running on `http://localhost:8000/api/v1`
- npm or yarn package manager

### Installation

1. **Navigate to the frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies** (already done)
   ```bash
   npm install
   ```

3. **Configure environment variables**
   Copy `.env.example` to `.env.local`, then fill in your local values:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   NEXT_PUBLIC_APP_NAME=Biotech Lead Generator
   NEXT_PUBLIC_APP_URL=http://localhost:3000
   NEXT_PUBLIC_ENABLE_ANALYTICS=false
   NEXT_PUBLIC_ENABLE_DARK_MODE=true
   NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_replace_me
   NEXT_PUBLIC_STRIPE_PRO_PRICE_ID=price_replace_me_pro
   NEXT_PUBLIC_STRIPE_TEAM_PRICE_ID=price_replace_me_team
   ```

### Running the Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### Building for Production

```bash
npm run build
npm start
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/                          # Next.js App Router pages
│   │   ├── globals.css              # Global styles
│   │   ├── layout.tsx               # Root layout
│   │   └── page.tsx                 # Home/landing page
│   ├── components/
│   │   ├── ui/                      # Base UI components (Button, Card, etc.)
│   │   ├── auth/                    # Authentication components
│   │   ├── dashboard/               # Dashboard components
│   │   ├── leads/                   # Lead management components
│   │   ├── charts/                  # Chart components
│   │   └── layout/                  # Layout components (Sidebar, Header)
│   ├── lib/
│   │   ├── api/                     # API client and endpoints
│   │   ├── auth/                    # Authentication utilities
│   │   ├── utils.ts                 # Utility functions
│   │   └── constants.ts             # App constants
│   ├── hooks/                       # Custom React hooks
│   ├── stores/                      # Zustand stores for state management
│   ├── types/                       # TypeScript type definitions
│   └── styles/                      # Additional stylesheets
├── public/                          # Static assets
├── .env.local                       # Environment variables
├── next.config.js                   # Next.js configuration
├── tailwind.config.ts               # Tailwind CSS configuration
├── tsconfig.json                    # TypeScript configuration
└── package.json                     # Project dependencies
```

## 🛠️ Technology Stack

### Core
- **Next.js 14** - React framework with Server Components
- **React 18** - UI library
- **TypeScript 5** - Type safety

### Styling & UI
- **Tailwind CSS 3** - Utility-first CSS framework
- **shadcn/ui components** - High-quality, accessible components
- **Lucide Icons** - Beautiful icon library

### State Management
- **Zustand** - Lightweight client state management
- **TanStack React Query** - Server state management
- **Axios** - HTTP client with interceptors

### Forms & Validation
- **React Hook Form** - Efficient form handling
- **Zod** - Runtime schema validation

### Charting & Data Visualization
- **Recharts** - Composable charting library
- **date-fns** - Modern date utility library

## 📡 API Integration

The frontend is configured to connect to the backend API at `http://localhost:8000/api/v1`.

### Key API Endpoints Used:
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/me` - Get current user
- `GET /dashboard/stats` - Dashboard statistics
- `GET /leads` - Get leads list
- `POST /leads` - Create new lead
- `PATCH /leads/{id}` - Update lead
- `DELETE /leads/{id}` - Delete lead
- `POST /exports` - Export data

## 🔐 Authentication

The app uses JWT token-based authentication:

1. Tokens are stored in `localStorage` as `access_token`
2. Automatically included in all API requests via axios interceptors
3. 401 responses redirect to login
4. User context available via `useAuth()` hook

## 🎨 Styling

### Tailwind CSS
- Configured with custom color variables in CSS (supports dark mode)
- Utility-first approach for rapid development
- Custom components in `src/components/ui/`

### Dark Mode
- Implemented via CSS variables
- Toggle in settings page (to be implemented)

## 📦 Available Scripts

```bash
# Development
npm run dev              # Start dev server (port 3000)

# Production
npm run build           # Create optimized build
npm start              # Start production server

# Code Quality
npm run lint           # Run ESLint
npm run format         # Format code with Prettier
npm run type-check     # Type check with TypeScript
```

## 🚀 Deployment Options

### Netlify (Recommended)
```bash
# Option A — Netlify CLI
npm i -g netlify-cli
netlify deploy --prod --dir .next

# Option B — connect GitHub repo at app.netlify.com
# Base directory: frontend
# Build command: npm run build
# Publish directory: .next
# Set env var: NEXT_PUBLIC_API_URL=https://<your-render-url>/api/v1
```

### Docker
```bash
docker build -t lead-generator-frontend .
docker run -p 3000:3000 lead-generator-frontend
```

### Traditional VPS
```bash
npm run build
npm start
```

## 🐛 Troubleshooting

### Dev server won't start
```bash
# Clear Next.js cache
rm -rf .next
npm run dev
```

### Port already in use
```bash
# Use different port
npm run dev -- -p 3001
```

### API connection errors
- Verify backend is running on `http://localhost:8000`
- Check `.env.local` has correct `NEXT_PUBLIC_API_URL`
- Check browser console for CORS errors
- The billing page currently lives at `/settings/billing`
- Stripe test webhooks should be forwarded to `/api/v1/webhooks/stripe`

### TypeScript errors
```bash
npm run type-check  # See detailed errors
```

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [React Query Docs](https://tanstack.com/query/latest)
- [Zustand Documentation](https://github.com/pmndrs/zustand)

## ✅ Implementation Status

### Week 3 (Days 15-20)
- [x] Day 15: Project setup & configuration
- [ ] Day 16: API client & authentication
- [ ] Day 17: Layout components (Sidebar, Header)
- [ ] Day 18: Dashboard structure
- [ ] Day 19: Dashboard charts
- [ ] Day 20: Dashboard polish

### Week 4 (Days 21-28)
- [ ] Day 21: Lead list basics
- [ ] Day 22: Advanced filters
- [ ] Day 23: Lead detail modal
- [ ] Day 24: Export features
- [ ] Day 25: Polish & UX
- [ ] Day 26: Dark mode + mobile
- [ ] Day 27: Testing
- [ ] Day 28: Deployment

## 📝 Next Steps

1. **Start development server**: `npm run dev`
2. **Visit homepage**: `http://localhost:3000`
3. **Begin implementing Day 16** (API client & auth)
4. **Check documentation** in `files/` folder for detailed guides

## 📧 Support

For issues or questions, refer to the backend documentation and API specs at:
- [Backend API Documentation](../backend/docs/API.md)
- [Development Guide](../backend/docs/DEVELOPMENT.md)

---

**Frontend Ready** ✅ 
Proceed to implement features from Day 16 onwards using the guides in `files/` folder.
