/**
 * Enhanced DocumentCard component that integrates with the backend API
 */

import React, { useState } from 'react';
import { DocumentResponse } from '../services/api';
import { useShareDocument, useOCR, useSummarization } from '../hooks/useApi';

interface ApiDocumentCardProps {
  doc: DocumentResponse;
  onViewSummary: (doc: DocumentResponse) => void;
  onShareDoc: (doc: DocumentResponse) => void;
  onRefresh?: () => void;
}

const departmentColors: Record<string, string> = {
  'Operations': '#007bff', 'HR': '#28a745', 'Finance': '#ffc107',
  'Legal': '#6f42c1', 'IT': '#17a2b8', 'Safety': '#dc3545',
  'Engineering': '#6c757d', 'Maintenance': '#17a2b8', 'All': '#6c757d'
};

const departmentEmojis: Record<string, string> = {
  'Operations': '🚇', 'HR': '👥', 'Finance': '💰', 'Legal': '⚖️',
  'IT': '💻', 'Safety': '🛡️', 'Engineering': '⚙️', 'Maintenance': '🔧', 'All': '🏢'
};

const priorityColors: Record<string, string> = {
  'High': '#dc3545', 'Medium': '#ffc107', 'Low': '#28a745'
};

const sourceIcons: Record<string, string> = {
  'Email': 'fas fa-envelope',
  'SharePoint': 'fab fa-windows',
  'Scanned': 'fas fa-scanner',
  'Maximo': 'fas fa-cogs',
  'Web Dashboard': 'fas fa-desktop',
};

export const ApiDocumentCard: React.FC<ApiDocumentCardProps> = ({
  doc,
  onViewSummary,
  onShareDoc,
  onRefresh
}) => {
  const [summaryLang, setSummaryLang] = useState<'en' | 'ml'>('en');
  const [isProcessing, setIsProcessing] = useState(false);
  
  const { execute: shareDocument, loading: shareLoading } = useShareDocument();
  const { execute: regenerateSummary, loading: summaryLoading } = useSummarization();

  const handleDownload = () => {
    if (doc.attachmentFilename) {
      const blob = new Blob([doc.body], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const txtFilename = doc.attachmentFilename.substring(0, doc.attachmentFilename.lastIndexOf('.')) + '.txt';
      a.download = txtFilename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } else {
      alert('No attachment available for this document.');
    }
  };

  const handleRegenerateSummary = async () => {
    if (!doc.body) return;
    
    setIsProcessing(true);
    try {
      await regenerateSummary(async () => {
        const { apiService } = await import('../services/api');
        return apiService.getSummary(doc.body, summaryLang === 'en' ? 'english' : 'malayalam');
      });
      
      if (onRefresh) {
        onRefresh();
      }
    } catch (error) {
      console.error('Failed to regenerate summary:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const summaryText = summaryLang === 'en' ? doc.summary.en : doc.summary.ml;
  const isLoading = shareLoading || summaryLoading || isProcessing;

  return (
    <div className={`document-card ${doc.critical ? 'alert-card-item' : ''}`}>
      <div className="card-header">
        <div>
          <span 
            className="department-tag" 
            style={{ backgroundColor: departmentColors[doc.departments[0]] || '#6c757d' }}
          >
            <i className={sourceIcons[doc.source] || 'fas fa-file'}></i> 
            {doc.departments.join(', ')}
          </span>
          <span className="doctype-tag">{doc.docType}</span>
        </div>
        <span 
          className="priority-tag" 
          style={{ backgroundColor: priorityColors[doc.priority] || '#6c757d' }}
        >
          {doc.priority}
        </span>
      </div>

      <div className="card-body">
        <h4>{doc.subject}</h4>
        
        <div className="card-meta">
          <span><strong>From:</strong> {doc.sender}</span>
          <span><strong>Date:</strong> {new Date(doc.date).toLocaleDateString()}</span>
          {doc.dueDate && (
            <span><strong>Due:</strong> {new Date(doc.dueDate).toLocaleDateString()}</span>
          )}
        </div>

        <div className="summary-container">
          <div className="summary-controls">
            <div className="language-toggle">
              <button 
                className={summaryLang === 'en' ? 'active' : ''} 
                onClick={() => setSummaryLang('en')}
                disabled={isLoading}
              >
                EN
              </button>
              <button 
                className={summaryLang === 'ml' ? 'active' : ''} 
                onClick={() => setSummaryLang('ml')}
                disabled={isLoading}
              >
                ML
              </button>
            </div>
            
            {doc.body && (
              <button 
                className="regenerate-btn" 
                onClick={handleRegenerateSummary}
                disabled={isLoading}
                title="Regenerate summary with latest AI"
              >
                <i className={`fas fa-sync-alt ${isProcessing ? 'fa-spin' : ''}`}></i>
              </button>
            )}
          </div>

          <p className={`card-summary ${!summaryText ? 'loading' : ''}`}>
            {summaryText || (isProcessing ? "Regenerating summary..." : "No summary available")}
          </p>
        </div>
      </div>

      <div className="card-actions">
        <button 
          className="card-btn" 
          onClick={() => onViewSummary(doc)}
          disabled={isLoading}
        >
          <i className="fas fa-eye"></i> View Details
        </button>
        
        <button 
          className="card-btn" 
          onClick={() => onShareDoc(doc)}
          disabled={isLoading}
        >
          <i className="fas fa-share"></i> Share
          {shareLoading && <i className="fas fa-spinner fa-spin"></i>}
        </button>
        
        {doc.attachmentFilename && (
          <button 
            className="card-btn" 
            onClick={handleDownload}
            disabled={isLoading}
          >
            <i className="fas fa-download"></i> Download
          </button>
        )}
      </div>

      {doc.sharedWith && doc.sharedWith.length > 0 && (
        <div className="shared-indicator">
          <i className="fas fa-users"></i> 
          Shared with {doc.sharedWith.length} user{doc.sharedWith.length > 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
};

export default ApiDocumentCard;
