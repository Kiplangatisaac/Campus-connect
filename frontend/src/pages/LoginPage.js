import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { toast } from 'react-toastify';
import SocialLoginButtons from '../components/SocialLoginButtons';
import './LoginPage.css';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim()) {
      toast.error('Registration Number is required');
      return;
    }
    if (!password) {
      toast.error('Password is required');
      return;
    }
    setLoading(true);
    try {
      const email = username.includes('@') ? username : `${username.trim()}@students.kyu.ac.ke`;
      await login(email, password);
      toast.success('Welcome back!');
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login failed. Check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ku-login-page">
      <div className="ku-login-bg" />
      <div className="ku-login-container">
        <div className="ku-login-header">
          <img src="/images/kyu-logo.png" alt="KyU Logo" className="ku-login-logo" />
          <h1>KyU Campus Connect</h1>
        </div>
        <div className="ku-login-body">
          <form onSubmit={handleSubmit} className="ku-login-form">
            <div className="ku-form-group">
              <label htmlFor="username">Registration No:</label>
              <input
                id="username"
                type="text"
                placeholder="e.g CT101/G/25159/24"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
              />
            </div>
            <div className="ku-form-group">
              <label htmlFor="password">Password:</label>
              <div className="ku-password-wrapper">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="ku-toggle-password"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                >
                  {showPassword ? '🙈' : '👁️'}
                </button>
              </div>
            </div>
            <div className="ku-form-actions">
              <Link to="/forgot-password" className="ku-btn-forgot">Forgot Password</Link>
              <button type="submit" className="ku-btn-signin" disabled={loading}>
                {loading ? 'Signing In...' : 'Sign In'}
              </button>
            </div>
          </form>
          <div className="ku-social-section">
            <div className="ku-social-divider"><span>or sign in with</span></div>
            <SocialLoginButtons mode="login" />
          </div>
          <div className="ku-login-footer">
            <p>New to Campus Connect? <Link to="/register">Create Account</Link></p>
          </div>
        </div>
      </div>
      <div className="ku-login-info">
        <p>Innovative Technology for a Dynamic World</p>
        <p className="ku-iso">Kirinyaga University is ISO 9001:2015 Certified</p>
      </div>
    </div>
  );
}
