import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'
import * as Sentry from '@sentry/react'
import { initI18n } from './i18n'

const dsn = import.meta.env.VITE_SENTRY_DSN
if (dsn) {
  Sentry.init({ dsn, tracesSampleRate: 0.2, replaysSessionSampleRate: 0.1 })
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 2, refetchOnWindowFocus: false },
    mutations: { retry: 2 }
  }
})

initI18n()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
)