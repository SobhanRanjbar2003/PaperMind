'use client';

import { Component, type ReactNode } from 'react';
import { ErrorState } from '@/components/ui/error-state';

interface State {
  hasError: boolean;
  message?: string;
}

export class ErrorBoundary extends Component<{ children: ReactNode; fallbackTitle?: string; fallbackBody?: string }, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message };
  }

  override componentDidCatch(error: Error) {
    if (process.env.NODE_ENV !== 'production') {
      // eslint-disable-next-line no-console
      console.error('[ErrorBoundary]', error);
    }
  }

  override render() {
    if (this.state.hasError) {
      return (
        <div className="container py-12">
          <ErrorState
            title={this.props.fallbackTitle ?? 'Something went wrong'}
            description={this.state.message ?? this.props.fallbackBody}
            onRetry={() => this.setState({ hasError: false })}
            retryLabel="Try again"
          />
        </div>
      );
    }
    return this.props.children;
  }
}
