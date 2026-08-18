import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', height: '100vh', background: '#0a0a1a', color: '#e0e0ff',
          fontFamily: 'system-ui, sans-serif', padding: '20px', textAlign: 'center'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>&#9888;</div>
          <h2 style={{ margin: '0 0 8px', fontSize: '20px' }}>Something went wrong</h2>
          <p style={{ color: 'rgba(224,224,255,0.5)', margin: '0 0 20px', maxWidth: '400px' }}>
            An unexpected error occurred. Please try refreshing the page.
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '10px 24px', background: 'linear-gradient(135deg, #00f0ff, #8b5cf6)',
              color: '#0a0a1a', border: 'none', borderRadius: '8px', fontWeight: 700,
              cursor: 'pointer', fontSize: '14px'
            }}
          >
            Reload Page
          </button>
          <button
            onClick={() => { localStorage.clear(); window.location.href = '/login'; }}
            style={{
              marginTop: '10px', padding: '8px 20px', background: 'transparent',
              color: '#00f0ff', border: '1px solid rgba(0,240,255,0.3)', borderRadius: '8px',
              cursor: 'pointer', fontSize: '13px'
            }}
          >
            Clear Data &amp; Login
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
