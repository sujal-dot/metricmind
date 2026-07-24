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
│   ├── dashboard/page.tsx  # Main dashboard with KPI cards
│   ├── chat/page.tsx       # AI chat interface (ChatGPT-style)
│   ├── analytics/page.tsx  # Charts and analytics
│   ├── history/page.tsx    # Query history
│   ├── layout.tsx          # Root layout with sidebar/navbar
│   └── page.tsx            # Home (redirects to dashboard)
├── components/
│   ├── Sidebar.tsx         # Sidebar navigation
│   ├── Navbar.tsx          # Top navbar
│   ├── StatCard.tsx        # KPI cards
│   ├── ChatWindow.tsx      # Chat interface with message history/streaming
│   ├── ChatMessage.tsx     # Individual chat message with markdown
│   ├── ChatInput.tsx       # Chat text input and send button
│   ├── TypingIndicator.tsx # AI typing indicator
│   ├── SuggestedQuestions.tsx # Suggested questions to ask
│   ├── AnalyticsChart.tsx  # ECharts wrapper
│   ├── HistoryTable.tsx    # History table
│   └── Loading.tsx         # Loading indicator
├── hooks/
│   └── useChat.ts          # Custom chat state/streaming hook
├── lib/
│   ├── api.ts              # Axios API client
│   └── hooks.ts            # TanStack Query hooks
├── types/
│   ├── api.ts              # TypeScript API types
│   └── chat.ts             # TypeScript chat types
└── providers.tsx           # TanStack Query provider
```

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
