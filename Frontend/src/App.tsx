/**
 * Main App component with integrated backend support
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from './contexts/AuthContext';
import ApiLoginPage from './components/ApiLoginPage';
import Dashboard from './components/Dashboard';
import LoadingSpinner from './components/LoadingSpinner';

const App: React.FC = () => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="app">
      {user ? <Dashboard /> : <ApiLoginPage />}
    </div>
  );
};

export default App;
