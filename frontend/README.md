# MetricMind Frontend

This is the Next.js 16 frontend for MetricMind — an Agentic Business Intelligence Platform.

## Tech Stack

- Next.js 16 (App Router)
- React 19
- TypeScript
- Tailwind CSS
- React Markdown + Remark GFM
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
│   ├── dashboard/page.tsx      # Main dashboard with KPI cards
│   ├── chat/page.tsx           # AI chat interface (ChatGPT-style)
│   ├── analytics/page.tsx      # Interactive analytics dashboard with charts/KPIs
│   ├── history/page.tsx        # Query history
│   ├── layout.tsx              # Root layout with sidebar/navbar
│   └── page.tsx                # Home (redirects to dashboard)
├── components/
│   ├── charts/
│   │   ├── ChartContainer.tsx  # Chart wrapper with title, loading, and error states
│   │   ├── KPICard.tsx         # KPI metric card with skeleton and trend indicator
│   │   ├── KPIGrid.tsx         # Responsive 6-KPI grid with filter-driven refresh
│   │   ├── LineChart.tsx       # ECharts line chart (zoom, legend, gradient area)
│   │   ├── BarChart.tsx        # ECharts bar chart (horizontal/vertical, hover effects)
│   │   └── PieChart.tsx        # ECharts pie chart (interactive legend, percentage labels)
│   ├── filters/
│   │   ├── DateFilter.tsx      # Date range picker with preset shortcuts
│   │   ├── RegionFilter.tsx    # Region dropdown selector
│   │   └── CategoryFilter.tsx  # Product category dropdown selector
│   ├── Sidebar.tsx             # Sidebar navigation
│   ├── Navbar.tsx              # Top navbar
│   ├── StatCard.tsx            # Legacy KPI card
│   ├── ChatWindow.tsx          # Chat interface with message history/streaming
│   ├── ChatMessage.tsx         # Individual chat message with markdown
│   ├── ChatInput.tsx           # Chat text input and send button
│   ├── TypingIndicator.tsx     # AI typing indicator
│   ├── SuggestedQuestions.tsx  # Suggested questions to ask
│   ├── AnalyticsChart.tsx      # Legacy simple ECharts wrapper
│   ├── HistoryTable.tsx        # History table
│   ├── Loading.tsx             # Generic loading indicator
│   └── LoadingCharts.tsx       # KPI + chart skeleton loading placeholder
├── hooks/
│   └── useChat.ts              # Custom chat state/streaming hook
├── lib/
│   ├── api.ts                  # Axios API client (with filter support on /metrics)
│   ├── analyticsApi.ts         # Dedicated analytics API client
│   ├── chartUtils.ts           # Formatting utilities: currency, number, percent, colors
│   └── hooks.ts                # TanStack Query hooks (useMetrics accepts filters)
├── types/
│   ├── api.ts                  # TypeScript API types
│   ├── analytics.ts            # TypeScript analytics types (KPIs, filters, chart data)
│   └── chat.ts                 # TypeScript chat types
└── providers.tsx               # TanStack Query provider
```

## Analytics Dashboard (Day 13)

The `/analytics` route provides a modern, responsive BI dashboard with:

### KPI Cards (`components/charts/`)
- **KPIGrid**: Responsive 1/2/3 column grid of 6 core metrics:
  - Total Revenue, Total Profit, Profit Margin
  - Total Orders, Total Customers, Average Order Value
- **KPICard**: Individual card with loading skeleton, error state, and trend indicator (↑ up / ↓ down / → neutral).
- Data is fetched via `useMetrics(filters)` from `GET /api/v1/metrics` with TanStack Query caching (1 min stale time).

### Chart Components (`components/charts/`)
Each component is memoized via `useMemo` for the ECharts option object and uses `echarts-for-react` in `lazyUpdate` + `notMerge` mode for performance.

- **LineChart**: Zoomable time series with legend, toolbox (dataZoom + restore), smooth lines, and gradient area fill. Used for Monthly Revenue/Profit and Orders trend.
- **BarChart**: Supports vertical and horizontal orientation, rounded corners, hover shadow, and axis value formatters. Used for Sales by Category/Region, Top Products, and Top Customers.
- **PieChart**: Donut-style or full pie with interactive legend, percentage labels, elasticOut animation, and emphasis scale hover. Used for Revenue by Category and Revenue by Region distributions.
- **ChartContainer**: Generic wrapper that provides title + subtitle header, loading skeleton (`animate-pulse`), and user-friendly error state fallback.

### Filter Panel (`components/filters/`)
- **DateFilter**: Dual date inputs (from/to) with preset shortcut pills (Last 7 days / 30 days / 90 days / 12 months) and a Clear button.
- **RegionFilter**: Dropdown with "All Regions" default and common world region presets.
- **CategoryFilter**: Dropdown with "All Categories" default and product category presets.
- All filters flow via React state into an `AnalyticsFilters` memoized object that propagates to `KPIGrid` → `useMetrics(filters)`, triggering automatic cache invalidation and refresh. A "Clear all filters" button appears whenever any filter is active.

### Loading & Error Handling
- `LoadingCharts.tsx`: Full-page skeleton placeholder with 6 animated KPI cards and 4 animated chart panels (used during initial filter transitions).
- Each `KPICard` has an individual inline skeleton; each `ChartContainer` handles its own loading/error state independently.
- Network errors surface as red error messages inline rather than crashing the page.

### Responsive Design
- Mobile: 1 column grids, stacked inputs, scrollable chart containers.
- Tablet (sm/md): 2 column KPI grid, 1 column chart grid.
- Desktop (lg/xl): 3 column KPI grid, 2 column chart grid (Top Products and Top Customers span both columns).

## Chat UI Features

- Markdown rendering for AI responses
- Copy-to-clipboard for AI responses
- Streaming responses (simulated for now, ready for real streaming)
- Suggested questions
- Clear chat
- Sidebar conversation history with local persistence
- Auto-scroll to latest message
- Responsive design
- Loading indicator (typing animation)

## Chat UI Architecture

- `useChat.ts` manages conversations, active chat state, streaming state, errors, and local persistence.
- `ChatWindow.tsx` composes the chat shell, history sidebar, messages, and input area.
- `ChatMessage.tsx` renders markdown responses and includes copy support.
- `EmptyState.tsx` provides the welcome experience and starter prompts.
- `SidebarHistory.tsx` shows recent conversations and lets the user start a fresh chat.

## Streaming Implementation

- The current backend returns a full response from `POST /ask`.
- The frontend simulates token-by-token rendering to provide a streaming chat experience today.
- The UI is structured so the `useChat.ts` hook can later switch to SSE, WebSockets, or streaming HTTP without major component changes.

## API Integration

- `POST /ask` powers the chat interface.
- `GET /api/v1/metrics` powers the dashboard KPI cards.
- `GET /api/v1/sales` is available for future table and chart extensions.
- `POST /semantic-search` remains available for future advanced analytics UX.

## Available Scripts

- `npm run dev`: Start development server
- `npm run build`: Build for production
- `npm start`: Start production server
- `npm run lint`: Run ESLint

## Troubleshooting

- If the chat shows network errors, make sure the backend is running on `http://localhost:8000`.
- If responses do not appear, check `NEXT_PUBLIC_API_BASE_URL` in `.env.local`.
- If Next.js warns about multiple lockfiles, set the Turbopack root in `next.config.ts` or remove the unrelated lockfile outside this project.
