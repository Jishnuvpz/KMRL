/**
 * Document grid component with API integration
 */

import React, { useState } from 'react';
import ApiDocumentCard from './ApiDocumentCard';
import DocumentModal from './DocumentModal';
import ShareModal from './ShareModal';
import { DocumentResponse } from '../services/api';

interface DocumentGridProps {
  documents: DocumentResponse[];
  loading: boolean;
  onRefresh: () => void;
}

const DocumentGrid: React.FC<DocumentGridProps> = ({ documents, loading, onRefresh }) => {
  const [selectedDoc, setSelectedDoc] = useState<DocumentResponse | null>(null);
  const [docToShare, setDocToShare] = useState<DocumentResponse | null>(null);

  if (loading && documents.length === 0) {
    return (
      <div className="document-grid-loading">
        <div className="loading-cards">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="document-card loading">
              <div className="loading-header"></div>
              <div className="loading-content">
                <div className="loading-line"></div>
                <div className="loading-line short"></div>
                <div className="loading-line"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (documents.length === 0 && !loading) {
    return (
      <div className="empty-state">
        <i className="fas fa-inbox"></i>
        <h3>No Documents Found</h3>
        <p>Try adjusting your filters or upload a new document to get started.</p>
      </div>
    );
  }

  return (
    <>
      <div className="document-grid">
        {documents.map((doc) => (
          <ApiDocumentCard
            key={doc.id}
            doc={doc}
            onViewSummary={setSelectedDoc}
            onShareDoc={setDocToShare}
            onRefresh={onRefresh}
          />
        ))}
        
        {loading && (
          <div className="loading-indicator">
            <i className="fas fa-spinner fa-spin"></i>
            <span>Loading more documents...</span>
          </div>
        )}
      </div>

      {selectedDoc && (
        <DocumentModal
          doc={selectedDoc}
          onClose={() => setSelectedDoc(null)}
          onShare={() => {
            setDocToShare(selectedDoc);
            setSelectedDoc(null);
          }}
        />
      )}

      {docToShare && (
        <ShareModal
          doc={docToShare}
          onClose={() => setDocToShare(null)}
          onComplete={() => {
            setDocToShare(null);
            onRefresh();
          }}
        />
      )}
    </>
  );
};

export default DocumentGrid;
