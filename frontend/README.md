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
│   ├── visualization/          # Day 14 dynamic visualization engine
│   │   ├── IntentClassifier.ts # Keyword-based intent → chart classifier (trend/distribution/comparison/kpi)
│   │   ├── VisualizationEngine.ts # Intent + Cube JSON → VisualizationPayload with demo datasets
│   │   ├── ChartRouter.tsx     # Receives question; selects/renders Line/Bar/Pie/KPIs automatically
│   │   ├── LineChart.tsx       # Memoized ECharts line chart for chat-embedded viz
│   │   ├── BarChart.tsx        # Memoized ECharts bar chart for chat-embedded viz
│   │   ├── PieChart.tsx        # Memoized ECharts pie chart for chat-embedded viz
│   │   ├── KPICards.tsx        # 1–6 card responsive KPI grid for chat-embedded viz
│   │   └── EmptyVisualization.tsx # Fallback when unsupported / empty / error
│   ├── chat/
│   │   └── VisualizationMessage.tsx # Renders ChartRouter (SSR-disabled dynamic) after AI responses
│   ├── filters/
│   │   ├── DateFilter.tsx      # Date range picker with preset shortcuts
│   │   ├── RegionFilter.tsx    # Region dropdown selector
│   │   └── CategoryFilter.tsx  # Product category dropdown selector
│   ├── Sidebar.tsx             # Sidebar navigation
│   ├── Navbar.tsx              # Top navbar
│   ├── StatCard.tsx            # Legacy KPI card
│   ├── ChatWindow.tsx          # Chat interface with message history/streaming + dynamic viz
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
│   ├── visualization.ts        # Re-exports: classifyIntent, buildVisualizationPayload, getChartLabel
│   ├── chartUtils.ts           # Formatting utilities: currency, number, percent, colors
│   └── hooks.ts                # TanStack Query hooks (useMetrics accepts filters)
├── types/
│   ├── api.ts                  # TypeScript API types
│   ├── analytics.ts            # TypeScript analytics types (KPIs, filters, chart data)
│   ├── visualization.ts        # Day 14 types: DetectedIntent, ChartType, VisualizationPayload, + per-chart data
│   └── chat.ts                 # TypeScript chat types (+ relatedQuestion for viz intent)
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

## Dynamic Visualization (Day 14)

The chat interface now includes an intelligent visualization engine that selects and renders
the best chart for every assistant response based on the user's natural language question.

### Pipeline

```
User Question
      |
      v
IntentClassifier (keyword-based)
      |
      v
DetectedIntent (comparisonType + metrics + dimensions + timePeriod + confidence)
      |
      v
VisualizationEngine.build (Cube JSON -> VisualizationPayload)
      |
      v
ChartRouter (renders Line / Bar / Pie / KPI cards)
      |
      v
Appears below every AI answer inside the chat.
```

### Intent-to-Chart Mapping

| Intent | Keywords | Chart | Example Queries |
|---|---|---|---|
| Trend (trend) | trend, growth, over time, monthly, yearly, daily, timeline, compare months/years | **Line Chart** | "Show monthly revenue trend for 2025", "Customer growth over time", "Profit over time" |
| Comparison (comparison) | region, category, product, customer, top, ranking, compare, highest, lowest, best, best-selling | **Bar Chart** | "Sales by region", "Top 10 customers", "Best-selling products", "Profit by category" |
| Distribution (distribution) | share, percentage, distribution, composition, contribution, breakdown, proportion, mix, market share | **Pie Chart** | "Revenue share by category", "Profit distribution", "Market share" |
| KPI (kpi) | total revenue, total profit, total orders, customers, average order value, aov, margin, kpi, totals | **KPI Cards** | "Total profit", "How many customers do we have?", "Show me the totals", "Average order value" |

### Core Files

- `components/visualization/IntentClassifier.ts`
  - Exports `classifyIntent(question) -> DetectedIntent`.
  - Keyword scoring across 4 buckets: trend, comparison, distribution, kpi.
  - Extracts metrics, dimensions, and timePeriod via regex patterns.
  - Returns `confidence` plus the highest-scoring chart type.
  - Supports future chart types: add a new keyword list, then map it inside `buildVisualizationPayload`.
- `components/visualization/VisualizationEngine.ts`
  - Exports `buildVisualizationPayload(question, cubeResponse, fallbackDemo)`.
  - Selects demo datasets (region/category/product/customer/kpi subsets) based on the detected intent.
  - Pluggable: swap demo datasets for live Cube JSON payloads without touching the classifier.
- `components/visualization/ChartRouter.tsx`
  - `useMemo` over (question + cubeResponse) -> VisualizationPayload.
  - Shows a route badge (Line/Bar/Pie/KPI) with confidence %, extracted metrics/dims, and time period.
  - Switches render path based on `payload.chartType`.
  - Falls back to `EmptyVisualization` with a friendly reason when the intent is unsupported.
- `components/chat/VisualizationMessage.tsx`
  - Uses `next/dynamic` with `ssr: false` because ECharts is browser-only (no window on server).
  - Mounted from ChatWindow for every assistant message that carries a `relatedQuestion`.
- `lib/visualization.ts`
  - Public barrel: re-exports `classifyIntent`, `buildVisualizationPayload`, `getChartLabel`, and the core visualization types.

### Chat Integration Flow

1. `types/chat.ts` - `ChatMessage.relatedQuestion` optional field added.
2. `hooks/useChat.ts` - `sendMessage()` stores the user's trimmed question into the assistant message as `relatedQuestion` when it's persisted. Hydration (localStorage roundtrip) also preserves `relatedQuestion`.
3. `components/ChatWindow.tsx` - After each `ChatMessage` for `role: 'assistant'` with a `relatedQuestion`, a `VisualizationMessage` is rendered immediately below the AI response.

### Supported Queries Verified

All example queries from the spec produce the correct routing:

1. "Show monthly revenue trend for 2025" -> Line Chart
2. "Sales by region" -> Bar Chart
3. "Revenue share by category" -> Pie Chart
4. "Total profit" -> KPI Cards
5. "Top 10 customers" -> Bar Chart
6. "Profit distribution" -> Pie Chart
7. "Customer growth over time" -> Line Chart

### API Flow

Backend endpoints remain unchanged: `/ask`, `/semantic-search`, `/api/v1/metrics`, `/api/v1/sales`. The visualization engine currently uses the user's question (`relatedQuestion`) for intent routing along with any Cube JSON returned by `/ask` or `/semantic-search`, with representative demo fallback datasets for consistent visualization output.

### Error Handling & Performance

- Empty / unsupported question -> EmptyVisualization (dashed border + descriptive fallback message).
- Invalid JSON / missing chart data -> caught by the engine -> EmptyVisualization with a `reason` explaining the issue.
- Network / backend unavailable -> surfaces via `useChat.error` as before; viz never crashes.
- Lazy loading: `next/dynamic` with `ssr: false` defers ECharts bundle to browser runtime.
- Memoized chart option objects + `notMerge={true}` + `lazyUpdate={true}` on echarts-for-react for minimal re-renders.
- Responsive: Tailwind grid breakpoints on KPICards + percentage-width chart containers.

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
