import React, { Component, ErrorInfo, ReactNode } from 'react';
import { ErrorState } from './ErrorState';
import { ConnectionLostIllustration } from './Illustrations';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error caught by Whicoustic ErrorBoundary:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  public handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-[500px] flex items-center justify-center p-6 bg-background">
          <ErrorState
            illustration={<ConnectionLostIllustration size={180} />}
            title="Something encountered an unexpected pause"
            description="Our telemetry system caught an interface interruption. Your audio vaults and cryptographic keys remain fully secure."
            solutionSteps={[
              'Click "Reload Platform" below to re-initialize your workspace.',
              'Verify that your network connection is stable.',
              'If the issue persists, return to the home screen or contact support.',
            ]}
            retryLabel="Reload Platform"
            onRetry={this.handleReset}
            secondaryLabel="Return to Homepage"
            secondaryHref="/"
            technicalError={
              this.state.error
                ? `${this.state.error.name}: ${this.state.error.message}\n${this.state.errorInfo?.componentStack || ''}`
                : undefined
            }
          />
        </div>
      );
    }

    return this.props.children;
  }
}

