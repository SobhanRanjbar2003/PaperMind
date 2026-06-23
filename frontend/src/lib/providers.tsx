'use client';

import { QueryCache, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ThemeProvider } from 'next-themes';
import { Toaster } from 'sonner';
import { useState, type PropsWithChildren } from 'react';
import { ApiClientError } from './api';

export function AppProviders({ children }: PropsWithChildren) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: (failureCount, error) => {
              if (error instanceof ApiClientError) {
                if (error.status >= 400 && error.status < 500) return false;
              }
              return failureCount < 2;
            },
            refetchOnWindowFocus: false,
            staleTime: 30_000,
          },
        },
        queryCache: new QueryCache(),
      }),
  );

  return (
    <QueryClientProvider client={client}>
      <ThemeProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange={false}
      >
        {children}
        <Toaster
          richColors
          position="top-center"
          toastOptions={{
            className: 'font-sans',
          }}
        />
      </ThemeProvider>
      {process.env.NODE_ENV === 'development' && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
}
