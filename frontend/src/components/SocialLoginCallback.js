import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { toast } from 'react-toastify';

export default function SocialLoginCallback() {
  const { provider } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [status, setStatus] = useState('Processing...');

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const error = searchParams.get('error');

      if (error) {
        toast.error(`Authentication failed: ${error}`);
        navigate('/login');
        return;
      }

      if (!code || !state) {
        toast.error('Invalid callback parameters');
        navigate('/login');
        return;
      }

      try {
        setStatus('Verifying with server...');
        const { data } = await api.post(`/auth/${provider}/callback`, { code, state, provider });

        const token = data.access_token || data.token;
        localStorage.setItem('token', token);
        if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token);
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        setUser(data.user);

        toast.success('Successfully signed in!');
        navigate('/dashboard');
      } catch (err) {
        console.error('Callback error:', err);
        toast.error(err.response?.data?.detail || err.response?.data?.message || 'Authentication failed');
        navigate('/login');
      }
    };

    handleCallback();
  }, [provider, searchParams, navigate, setUser]);

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-left">
          <div className="auth-brand">
            <div className="auth-logo">KyU</div>
            <h1>Kirinyaga University</h1>
            <p>Campus Connect</p>
          </div>
        </div>
        <div className="auth-right">
          <div className="auth-form-container" style={{ textAlign: 'center' }}>
            <div className="spinner" style={{ margin: '0 auto 20px' }}></div>
            <h2>Signing you in...</h2>
            <p className="auth-subtitle">{status}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
