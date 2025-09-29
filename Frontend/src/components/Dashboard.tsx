/**
 * Main Dashboard component with backend integration
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useDocuments, useDashboardStats } from '../hooks/useApi';
import Header from './Header';
import Sidebar from './Sidebar';
import DocumentGrid from './DocumentGrid';
import FileUpload from './FileUpload';
import LoadingSpinner from './LoadingSpinner';
import { DocumentResponse } from '../services/api';

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeView, setActiveView] = useState('Dashboard');
  const [activeDept, setActiveDept] = useState<string>('All');
  const [searchTerm, setSearchTerm] = useState('');
  const [showUpload, setShowUpload] = useState(false);
  
  const { data: documents, loading: docsLoading, error: docsError, refetch } = useDocuments();
  const { data: stats, loading: statsLoading } = useDashboardStats();

  const filteredDocuments = useMemo(() => {
    if (!documents) return [];
    
    let filtered = [...documents];
    
    // Filter by department
    if (activeDept !== 'All') {
      filtered = filtered.filter(doc => doc.departments.includes(activeDept));
    }
    
    // Filter by search term
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(doc =>
        doc.subject.toLowerCase().includes(term) ||
        doc.sender.toLowerCase().includes(term) ||
        doc.body.toLowerCase().includes(term) ||
        doc.departments.some(dept => dept.toLowerCase().includes(term))
      );
    }
    
    return filtered;
  }, [documents, activeDept, searchTerm]);

  const notifications = useMemo(() => {
    return documents?.filter(doc => doc.critical) || [];
  }, [documents]);

  const handleUploadComplete = (newDocument: DocumentResponse) => {
    setShowUpload(false);
    refetch(); // Refresh documents list
  };

  const accessibleDepartments = useMemo(() => {
    if (!user) return [];
    if (user.role === 'Admin' || user.role === 'Board Member') {
      return ['Operations', 'HR', 'Finance', 'Legal', 'IT', 'Safety'];
    }
    return [user.department];
  }, [user]);

  if (docsLoading && !documents) {
    return <LoadingSpinner message="Loading dashboard..." />;
  }

  return (
    <div className={`app-layout ${sidebarOpen ? 'sidebar-open' : ''}`}>
      <Sidebar
        isOpen={sidebarOpen}
        activeView={activeView}
        setActiveView={setActiveView}
        activeDept={activeDept}
        setActiveDept={setActiveDept}
        departments={accessibleDepartments}
      />
      
      <div className="main-wrapper">
        <Header
          user={user}
          onLogout={logout}
          onSearch={setSearchTerm}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          notifications={notifications}
        />
        
        <main className="main-content">
          <div className="content-header">
            <h1>
              <i className="fas fa-tachometer-alt"></i>
              Dashboard
            </h1>
            
            <div className="content-actions">
              <button
                className="btn-primary"
                onClick={() => setShowUpload(true)}
              >
                <i className="fas fa-plus"></i> Upload Document
              </button>
              
              <button
                className="btn-secondary"
                onClick={() => refetch()}
                disabled={docsLoading}
              >
                <i className={`fas fa-sync-alt ${docsLoading ? 'fa-spin' : ''}`}></i>
                Refresh
              </button>
            </div>
          </div>

          {/* Dashboard Stats */}
          {stats && (
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">
                  <i className="fas fa-file-alt"></i>
                </div>
                <div className="stat-info">
                  <span className="stat-value">{stats.total_documents || documents?.length || 0}</span>
                  <span className="stat-label">Total Documents</span>
                </div>
              </div>
              
              <div className="stat-card">
                <div className="stat-icon critical">
                  <i className="fas fa-exclamation-triangle"></i>
                </div>
                <div className="stat-info">
                  <span className="stat-value">{notifications.length}</span>
                  <span className="stat-label">Critical Alerts</span>
                </div>
              </div>
              
              <div className="stat-card">
                <div className="stat-icon processing">
                  <i className="fas fa-clock"></i>
                </div>
                <div className="stat-info">
                  <span className="stat-value">{stats.processing_documents || 0}</span>
                  <span className="stat-label">Processing</span>
                </div>
              </div>
            </div>
          )}

          {docsError && (
            <div className="error-message">
              <i className="fas fa-exclamation-triangle"></i>
              Failed to load documents: {docsError}
              <button onClick={() => refetch()} className="retry-btn">
                <i className="fas fa-retry"></i> Retry
              </button>
            </div>
          )}

          <DocumentGrid
            documents={filteredDocuments}
            loading={docsLoading}
            onRefresh={refetch}
          />
        </main>
      </div>

      {showUpload && (
        <FileUpload
          onUploadComplete={handleUploadComplete}
          onClose={() => setShowUpload(false)}
        />
      )}
    </div>
  );
};

export default Dashboard;
