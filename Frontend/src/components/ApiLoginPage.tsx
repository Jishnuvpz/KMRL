/**
 * Login page component with backend authentication
 */

import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

export const ApiLoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const { login, loading, error } = useAuth();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!username.trim() || !password.trim()) {
      return;
    }

    try {
      await login({ username: username.trim(), password });
    } catch (err) {
      // Error is already handled by AuthContext
      console.error('Login failed:', err);
    }
  };

  // Demo accounts for quick access
  const demoAccounts = [
    { username: 'admin@kmrl.co.in', role: 'Admin', department: 'All' },
    { username: 'director.ops@kmrl.co.in', role: 'Director', department: 'Operations' },
    { username: 'manager.fin@kmrl.co.in', role: 'Manager', department: 'Finance' },
    { username: 'staff.safety@kmrl.co.in', role: 'Staff', department: 'Safety' },
  ];

  const fillDemoAccount = (demoUsername: string) => {
    setUsername(demoUsername);
    setPassword('password123');
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-branding">
          <div className="login-logo">KMRL</div>
          <h1>Document Intelligence Platform</h1>
          <p>Empowering decisions with intelligent document processing.</p>
        </div>
        
        <div className="login-box">
          <h2>Sign In</h2>
          <p className="login-subtitle">Enter your credentials to access the dashboard.</p>
          
          <form onSubmit={handleLogin}>
            <div className="input-group">
              <i className="fas fa-user"></i>
              <input
                type="text"
                id="username"
                placeholder="e.g., admin@kmrl.co.in"
                value={username}
                onChange={e => setUsername(e.target.value)}
                required
                autoCapitalize="none"
                autoComplete="username"
                disabled={loading}
              />
            </div>
            
            <div className="input-group">
              <i className="fas fa-lock"></i>
              <input
                type={showPassword ? "text" : "password"}
                id="password"
                placeholder="Password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                disabled={loading}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                disabled={loading}
              >
                <i className={`fas fa-eye${showPassword ? '-slash' : ''}`}></i>
              </button>
            </div>

            {error && (
              <div className="login-error">
                <i className="fas fa-exclamation-circle"></i>
                {error}
              </div>
            )}

            <button type="submit" className="login-btn" disabled={loading}>
              {loading ? (
                <>
                  <i className="fas fa-spinner fa-spin"></i> 
                  Signing In...
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <div className="demo-accounts">
            <p>Demo Accounts:</p>
            <div className="demo-buttons">
              {demoAccounts.map((account) => (
                <button
                  key={account.username}
                  type="button"
                  className="demo-btn"
                  onClick={() => fillDemoAccount(account.username)}
                  disabled={loading}
                >
                  <strong>{account.role}</strong>
                  <span>{account.department}</span>
                </button>
              ))}
            </div>
            <p className="demo-note">Default password: password123</p>
          </div>

          <div className="login-features">
            <h4>Platform Features:</h4>
            <ul>
              <li><i className="fas fa-eye"></i> Multi-language OCR Processing</li>
              <li><i className="fas fa-brain"></i> AI-Powered Document Summarization</li>
              <li><i className="fas fa-share"></i> Real-time Document Collaboration</li>
              <li><i className="fas fa-shield-alt"></i> Secure Role-based Access</li>
            </ul>
          </div>

          <div className="forgot-password">
            <a href="#" onClick={(e) => { e.preventDefault(); alert('Contact IT support for password reset.'); }}>
              Forgot Password?
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ApiLoginPage;
