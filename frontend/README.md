# MetricMind Frontend

This is the Next.js 16 frontend for MetricMind — an Agentic Business Intelligence Platform.

## Tech Stack

- Next.js 16 (App Router)
- React 19
- TypeScript
- Tailwind CSS
- Tremor UI
- Apache ECharts
- TanStack Query (React Query)
- Axios

## Getting Started

### Prerequisites

Ensure the backend is running at http://localhost:8000

### Installation

```bash
npm install
```

### Environment Variables

Create a `.env.local` file in the frontend directory with:
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Project Structure

```
src/
├── app/
│   ├── dashboard/page.tsx  # Main dashboard with KPI cards
│   ├── chat/page.tsx       # AI chat interface
│   ├── analytics/page.tsx  # Charts and analytics
│   ├── history/page.tsx    # Query history
│   ├── layout.tsx          # Root layout with sidebar/navbar
│   └── page.tsx            # Home (redirects to dashboard)
├── components/
│   ├── Sidebar.tsx         # Sidebar navigation
│   ├── Navbar.tsx          # Top navbar
│   ├── StatCard.tsx        # KPI cards
│   ├── ChatBox.tsx         # Chat interface
│   ├── AnalyticsChart.tsx  # ECharts wrapper
│   ├── HistoryTable.tsx    # History table
│   └── Loading.tsx         # Loading indicator
├── lib/
│   ├── api.ts              # Axios API client
│   └── hooks.ts            # TanStack Query hooks
├── types/
│   └── api.ts              # TypeScript API types
└── providers.tsx           # TanStack Query provider
```

## Available Scripts

- `npm run dev`: Start development server
- `npm run build`: Build for production
- `npm start`: Start production server
- `npm run lint`: Run ESLint
