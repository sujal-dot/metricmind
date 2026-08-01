'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';
import { MobileNavProvider } from '@/providers/MobileNavProvider';
import { AuthProvider } from '@/providers/AuthProvider';

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <MobileNavProvider>{children}</MobileNavProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
