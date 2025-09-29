/**
 * Interdepartment File Sharing Component
 * Advanced sharing system with permissions, notifications, and tracking
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { DocumentResponse } from '../services/api';
import { useShareDocument } from '../hooks/useApi';

interface InterdepartmentSharingProps {
  documents: DocumentResponse[];
  onClose: () => void;
  onShareComplete: () => void;
}

interface ShareRequest {
  id: string;
  documentIds: number[];
  targetDepartments: string[];
  shareType: 'view' | 'edit' | 'comment';
  expiryDate?: string;
  message: string;
  urgent: boolean;
  requiresApproval: boolean;
}

interface DepartmentUser {
  email: string;
  role: string;
  department: string;
  name: string;
  active: boolean;
}

const departmentUsers: Record<string, DepartmentUser[]> = {
  'Operations': [
    { email: 'director.ops@kmrl.co.in', role: 'Director', department: 'Operations', name: 'Operations Director', active: true },
    { email: 'manager.ops@kmrl.co.in', role: 'Manager', department: 'Operations', name: 'Operations Manager', active: true },
    { email: 'staff.ops1@kmrl.co.in', role: 'Staff', department: 'Operations', name: 'Operations Staff 1', active: true },
    { email: 'staff.ops2@kmrl.co.in', role: 'Staff', department: 'Operations', name: 'Operations Staff 2', active: true },
  ],
  'HR': [
    { email: 'director.hr@kmrl.co.in', role: 'Director', department: 'HR', name: 'HR Director', active: true },
    { email: 'manager.hr@kmrl.co.in', role: 'Manager', department: 'HR', name: 'HR Manager', active: true },
    { email: 'staff.hr@kmrl.co.in', role: 'Staff', department: 'HR', name: 'HR Staff', active: true },
  ],
  'Finance': [
    { email: 'manager.fin@kmrl.co.in', role: 'Manager', department: 'Finance', name: 'Finance Manager', active: true },
    { email: 'staff.fin@kmrl.co.in', role: 'Staff', department: 'Finance', name: 'Finance Staff', active: true },
    { email: 'accountant@kmrl.co.in', role: 'Staff', department: 'Finance', name: 'Accountant', active: true },
  ],
  'Legal': [
    { email: 'staff.legal@kmrl.co.in', role: 'Staff', department: 'Legal', name: 'Legal Officer', active: true },
    { email: 'counsel@kmrl.co.in', role: 'Staff', department: 'Legal', name: 'Legal Counsel', active: true },
  ],
  'IT': [
    { email: 'it.head@kmrl.co.in', role: 'Manager', department: 'IT', name: 'IT Head', active: true },
    { email: 'it.support@kmrl.co.in', role: 'Staff', department: 'IT', name: 'IT Support', active: true },
    { email: 'system.admin@kmrl.co.in', role: 'Staff', department: 'IT', name: 'System Administrator', active: true },
  ],
  'Safety': [
    { email: 'staff.safety@kmrl.co.in', role: 'Staff', department: 'Safety', name: 'Safety Officer', active: true },
    { email: 'safety.inspector@kmrl.co.in', role: 'Staff', department: 'Safety', name: 'Safety Inspector', active: true },
  ],
  'Engineering': [
    { email: 'chief.engineer@kmrl.co.in', role: 'Director', department: 'Engineering', name: 'Chief Engineer', active: true },
    { email: 'project.engineer@kmrl.co.in', role: 'Manager', department: 'Engineering', name: 'Project Engineer', active: true },
  ],
  'Maintenance': [
    { email: 'maintenance.head@kmrl.co.in', role: 'Manager', department: 'Maintenance', name: 'Maintenance Head', active: true },
    { email: 'technician@kmrl.co.in', role: 'Staff', department: 'Maintenance', name: 'Technician', active: true },
  ]
};

const departments = Object.keys(departmentUsers);

export const InterdepartmentSharing: React.FC<InterdepartmentSharingProps> = ({
  documents,
  onClose,
  onShareComplete
}) => {
  const { user } = useAuth();
  const [selectedDocuments, setSelectedDocuments] = useState<number[]>([]);
  const [shareRequest, setShareRequest] = useState<ShareRequest>({
    id: `share-${Date.now()}`,
    documentIds: [],
    targetDepartments: [],
    shareType: 'view',
    message: '',
    urgent: false,
    requiresApproval: false
  });
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [currentStep, setCurrentStep] = useState<'select' | 'configure' | 'users' | 'review' | 'complete'>('select');
  const [shareResults, setShareResults] = useState<any[]>([]);
  const { execute: shareDocument, loading: shareLoading } = useShareDocument();

  // Filter documents user can share
  const shareableDocuments = documents.filter(doc => {
    if (user?.role === 'Admin' || user?.role === 'Board Member') return true;
    if (user?.role === 'Director') return true;
    if (user?.role === 'Manager') return doc.departments.includes(user.department);
    return false; // Staff can't share by default
  });

  // Get available departments for current user
  const availableDepartments = departments.filter(dept => {
    if (user?.role === 'Admin' || user?.role === 'Board Member') return true;
    return dept !== user?.department; // Can't share with own department
  });

  const handleDocumentSelection = (docId: number, selected: boolean) => {
    if (selected) {
      setSelectedDocuments(prev => [...prev, docId]);
    } else {
      setSelectedDocuments(prev => prev.filter(id => id !== docId));
    }
  };

  const handleDepartmentSelection = (dept: string, selected: boolean) => {
    if (selected) {
      setShareRequest(prev => ({
        ...prev,
        targetDepartments: [...prev.targetDepartments, dept]
      }));
    } else {
      setShareRequest(prev => ({
        ...prev,
        targetDepartments: prev.targetDepartments.filter(d => d !== dept)
      }));
      // Remove users from deselected department
      const deptUsers = departmentUsers[dept]?.map(u => u.email) || [];
      setSelectedUsers(prev => prev.filter(email => !deptUsers.includes(email)));
    }
  };

  const handleUserSelection = (userEmail: string, selected: boolean) => {
    if (selected) {
      setSelectedUsers(prev => [...prev, userEmail]);
    } else {
      setSelectedUsers(prev => prev.filter(email => email !== userEmail));
    }
  };

  const processSharing = async () => {
    setCurrentStep('complete');
    const results: any[] = [];

    for (const docId of selectedDocuments) {
      try {
        const result = await shareDocument(async () => {
          const { apiService } = await import('../services/api');
          return apiService.shareDocument(docId, selectedUsers);
        });

        results.push({
          documentId: docId,
          document: documents.find(d => d.id === docId),
          status: 'success',
          sharedWith: selectedUsers.length,
          departments: shareRequest.targetDepartments
        });
      } catch (error) {
        results.push({
          documentId: docId,
          document: documents.find(d => d.id === docId),
          status: 'failed',
          error: error instanceof Error ? error.message : 'Sharing failed'
        });
      }
    }

    setShareResults(results);
  };

  const renderDocumentSelection = () => (
    <div className="sharing-step">
      <h3><i className="fas fa-file-alt"></i> Select Documents to Share</h3>
      <p>Choose documents you want to share with other departments</p>

      {shareableDocuments.length === 0 ? (
        <div className="no-documents">
          <i className="fas fa-info-circle"></i>
          <p>No documents available for sharing. You may need higher permissions.</p>
        </div>
      ) : (
        <div className="document-selection">
          <div className="selection-header">
            <label className="select-all">
              <input
                type="checkbox"
                checked={selectedDocuments.length === shareableDocuments.length}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedDocuments(shareableDocuments.map(d => d.id));
                  } else {
                    setSelectedDocuments([]);
                  }
                }}
              />
              Select All ({shareableDocuments.length} documents)
            </label>
          </div>

          <div className="document-list">
            {shareableDocuments.map(doc => (
              <div key={doc.id} className={`document-item ${selectedDocuments.includes(doc.id) ? 'selected' : ''}`}>
                <label className="document-checkbox">
                  <input
                    type="checkbox"
                    checked={selectedDocuments.includes(doc.id)}
                    onChange={(e) => handleDocumentSelection(doc.id, e.target.checked)}
                  />
                  <div className="document-info">
                    <div className="document-header">
                      <h4>{doc.subject}</h4>
                      <div className="document-meta">
                        <span className="priority" style={{ backgroundColor: 
                          doc.priority === 'High' ? '#dc3545' : 
                          doc.priority === 'Medium' ? '#ffc107' : '#28a745' 
                        }}>
                          {doc.priority}
                        </span>
                        <span className="department" style={{ backgroundColor: 
                          doc.departments[0] === 'Operations' ? '#007bff' :
                          doc.departments[0] === 'HR' ? '#28a745' :
                          doc.departments[0] === 'Finance' ? '#ffc107' :
                          doc.departments[0] === 'Legal' ? '#6f42c1' :
                          doc.departments[0] === 'IT' ? '#17a2b8' :
                          doc.departments[0] === 'Safety' ? '#dc3545' :
                          '#6c757d'
                        }}>
                          {doc.departments[0]}
                        </span>
                      </div>
                    </div>
                    <div className="document-details">
                      <span>From: {doc.sender}</span>
                      <span>Date: {new Date(doc.date).toLocaleDateString()}</span>
                      <span>Type: {doc.docType}</span>
                      {doc.dueDate && (
                        <span className="due-date">Due: {new Date(doc.dueDate).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                </label>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="step-actions">
        <button className="btn-secondary" onClick={onClose}>
          <i className="fas fa-times"></i> Cancel
        </button>
        <button 
          className="btn-primary" 
          onClick={() => {
            setShareRequest(prev => ({ ...prev, documentIds: selectedDocuments }));
            setCurrentStep('configure');
          }}
          disabled={selectedDocuments.length === 0}
        >
          <i className="fas fa-arrow-right"></i> 
          Configure Sharing ({selectedDocuments.length} selected)
        </button>
      </div>
    </div>
  );

  const renderShareConfiguration = () => (
    <div className="sharing-step">
      <h3><i className="fas fa-cog"></i> Configure Sharing Settings</h3>
      <p>Set permissions and access levels for the shared documents</p>

      <div className="config-form">
        <div className="form-group">
          <label>Share Type</label>
          <div className="radio-group">
            <label>
              <input
                type="radio"
                value="view"
                checked={shareRequest.shareType === 'view'}
                onChange={(e) => setShareRequest(prev => ({ ...prev, shareType: e.target.value as any }))}
              />
              <i className="fas fa-eye"></i> View Only
              <span className="description">Recipients can view and download</span>
            </label>
            <label>
              <input
                type="radio"
                value="comment"
                checked={shareRequest.shareType === 'comment'}
                onChange={(e) => setShareRequest(prev => ({ ...prev, shareType: e.target.value as any }))}
              />
              <i className="fas fa-comment"></i> View & Comment
              <span className="description">Recipients can view and add comments</span>
            </label>
            <label>
              <input
                type="radio"
                value="edit"
                checked={shareRequest.shareType === 'edit'}
                onChange={(e) => setShareRequest(prev => ({ ...prev, shareType: e.target.value as any }))}
              />
              <i className="fas fa-edit"></i> Full Access
              <span className="description">Recipients can view, comment, and edit</span>
            </label>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="share-message">Message to Recipients</label>
          <textarea
            id="share-message"
            value={shareRequest.message}
            onChange={(e) => setShareRequest(prev => ({ ...prev, message: e.target.value }))}
            placeholder="Add a message explaining why you're sharing these documents..."
            rows={3}
          />
        </div>

        <div className="form-group">
          <label htmlFor="expiry-date">Access Expires (Optional)</label>
          <input
            id="expiry-date"
            type="date"
            value={shareRequest.expiryDate || ''}
            onChange={(e) => setShareRequest(prev => ({ ...prev, expiryDate: e.target.value || undefined }))}
            min={new Date().toISOString().split('T')[0]}
          />
        </div>

        <div className="form-options">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={shareRequest.urgent}
              onChange={(e) => setShareRequest(prev => ({ ...prev, urgent: e.target.checked }))}
            />
            <i className="fas fa-exclamation-triangle"></i>
            Mark as Urgent
          </label>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={shareRequest.requiresApproval}
              onChange={(e) => setShareRequest(prev => ({ ...prev, requiresApproval: e.target.checked }))}
            />
            <i className="fas fa-check-circle"></i>
            Require Approval from Recipients
          </label>
        </div>
      </div>

      <div className="step-actions">
        <button className="btn-secondary" onClick={() => setCurrentStep('select')}>
          <i className="fas fa-arrow-left"></i> Back
        </button>
        <button className="btn-primary" onClick={() => setCurrentStep('users')}>
          <i className="fas fa-arrow-right"></i> Select Recipients
        </button>
      </div>
    </div>
  );

  const renderUserSelection = () => (
    <div className="sharing-step">
      <h3><i className="fas fa-users"></i> Select Recipients</h3>
      <p>Choose specific users from departments who will receive access</p>

      <div className="department-user-selection">
        {availableDepartments.map(dept => (
          <div key={dept} className="department-section">
            <div className="department-header">
              <label className="department-checkbox">
                <input
                  type="checkbox"
                  checked={shareRequest.targetDepartments.includes(dept)}
                  onChange={(e) => handleDepartmentSelection(dept, e.target.checked)}
                />
                <span className="dept-name">
                  <span className="dept-color-tag" style={{ backgroundColor: 
                    dept === 'Operations' ? '#007bff' :
                    dept === 'HR' ? '#28a745' :
                    dept === 'Finance' ? '#ffc107' :
                    dept === 'Legal' ? '#6f42c1' :
                    dept === 'IT' ? '#17a2b8' :
                    dept === 'Safety' ? '#dc3545' :
                    '#6c757d'
                  }}></span>
                  {dept} Department
                </span>
              </label>
            </div>

            {shareRequest.targetDepartments.includes(dept) && (
              <div className="user-list">
                {departmentUsers[dept]?.map(user => (
                  <label key={user.email} className="user-checkbox">
                    <input
                      type="checkbox"
                      checked={selectedUsers.includes(user.email)}
                      onChange={(e) => handleUserSelection(user.email, e.target.checked)}
                    />
                    <div className="user-info">
                      <div className="user-name">{user.name}</div>
                      <div className="user-details">
                        <span className="user-role">{user.role}</span>
                        <span className="user-email">{user.email}</span>
                        <span className={`user-status ${user.active ? 'active' : 'inactive'}`}>
                          <i className={`fas fa-circle ${user.active ? 'active' : 'inactive'}`}></i>
                          {user.active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    </div>
                  </label>
                )) || <p className="no-users">No users available</p>}
              </div>
            )}
          </div>
        ))}
      </div>

      {selectedUsers.length > 0 && (
        <div className="selection-summary">
          <h4>Selected Recipients ({selectedUsers.length})</h4>
          <div className="selected-users">
            {selectedUsers.map(email => {
              const user = Object.values(departmentUsers).flat().find(u => u.email === email);
              return user ? (
                <div key={email} className="selected-user">
                  <span>{user.name}</span>
                  <span className="user-dept">{user.department}</span>
                  <button onClick={() => handleUserSelection(email, false)}>
                    <i className="fas fa-times"></i>
                  </button>
                </div>
              ) : null;
            })}
          </div>
        </div>
      )}

      <div className="step-actions">
        <button className="btn-secondary" onClick={() => setCurrentStep('configure')}>
          <i className="fas fa-arrow-left"></i> Back
        </button>
        <button 
          className="btn-primary" 
          onClick={() => setCurrentStep('review')}
          disabled={selectedUsers.length === 0}
        >
          <i className="fas fa-arrow-right"></i> Review & Share
        </button>
      </div>
    </div>
  );

  const renderReview = () => (
    <div className="sharing-step">
      <h3><i className="fas fa-eye"></i> Review Sharing Request</h3>
      <p>Confirm the details before sharing documents</p>

      <div className="review-summary">
        <div className="summary-section">
          <h4><i className="fas fa-file-alt"></i> Documents ({selectedDocuments.length})</h4>
          <div className="document-summary">
            {selectedDocuments.map(docId => {
              const doc = documents.find(d => d.id === docId);
              return doc ? (
                <div key={docId} className="summary-item">
                  <span className="doc-title">{doc.subject}</span>
                  <span className="doc-meta">{doc.docType} • {doc.priority}</span>
                </div>
              ) : null;
            })}
          </div>
        </div>

        <div className="summary-section">
          <h4><i className="fas fa-users"></i> Recipients ({selectedUsers.length})</h4>
          <div className="recipient-summary">
            {shareRequest.targetDepartments.map(dept => (
              <div key={dept} className="dept-summary">
                <strong>{dept}:</strong>
                <div className="dept-users">
                  {selectedUsers
                    .filter(email => departmentUsers[dept]?.find(u => u.email === email))
                    .map(email => {
                      const user = departmentUsers[dept]?.find(u => u.email === email);
                      return user ? (
                        <span key={email} className="recipient-name">{user.name} ({user.role})</span>
                      ) : null;
                    })
                  }
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="summary-section">
          <h4><i className="fas fa-cog"></i> Sharing Settings</h4>
          <div className="settings-summary">
            <div className="setting-item">
              <span>Access Type:</span>
              <strong>
                <i className={`fas ${
                  shareRequest.shareType === 'view' ? 'fa-eye' :
                  shareRequest.shareType === 'comment' ? 'fa-comment' :
                  'fa-edit'
                }`}></i>
                {shareRequest.shareType === 'view' ? 'View Only' :
                 shareRequest.shareType === 'comment' ? 'View & Comment' :
                 'Full Access'}
              </strong>
            </div>
            
            {shareRequest.expiryDate && (
              <div className="setting-item">
                <span>Expires:</span>
                <strong>{new Date(shareRequest.expiryDate).toLocaleDateString()}</strong>
              </div>
            )}
            
            {shareRequest.urgent && (
              <div className="setting-item urgent">
                <i className="fas fa-exclamation-triangle"></i>
                <strong>Marked as Urgent</strong>
              </div>
            )}
          </div>
        </div>

        {shareRequest.message && (
          <div className="summary-section">
            <h4><i className="fas fa-envelope"></i> Message</h4>
            <div className="message-preview">
              "{shareRequest.message}"
            </div>
          </div>
        )}
      </div>

      <div className="step-actions">
        <button className="btn-secondary" onClick={() => setCurrentStep('users')}>
          <i className="fas fa-arrow-left"></i> Back
        </button>
        <button 
          className="btn-primary" 
          onClick={processSharing}
          disabled={shareLoading}
        >
          {shareLoading ? (
            <>
              <i className="fas fa-spinner fa-spin"></i> Sharing...
            </>
          ) : (
            <>
              <i className="fas fa-share"></i> Share Documents
            </>
          )}
        </button>
      </div>
    </div>
  );

  const renderComplete = () => (
    <div className="sharing-step">
      <h3><i className="fas fa-check-circle"></i> Sharing Complete</h3>
      <p>Documents have been shared with selected recipients</p>

      <div className="share-results">
        {shareResults.map((result, index) => (
          <div key={index} className={`result-item ${result.status}`}>
            <div className="result-icon">
              <i className={`fas ${result.status === 'success' ? 'fa-check' : 'fa-times'}`}></i>
            </div>
            <div className="result-info">
              <strong>{result.document?.subject}</strong>
              {result.status === 'success' ? (
                <div className="success-details">
                  <span>✓ Shared with {result.sharedWith} users</span>
                  <span>✓ Departments: {result.departments.join(', ')}</span>
                  <span>✓ Notifications sent</span>
                </div>
              ) : (
                <div className="error-details">
                  <span>✗ Failed: {result.error}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="completion-summary">
        <div className="summary-stat success">
          <i className="fas fa-check"></i>
          <span>{shareResults.filter(r => r.status === 'success').length} documents shared successfully</span>
        </div>
        {shareResults.some(r => r.status === 'failed') && (
          <div className="summary-stat error">
            <i className="fas fa-times"></i>
            <span>{shareResults.filter(r => r.status === 'failed').length} documents failed to share</span>
          </div>
        )}
      </div>

      <div className="step-actions">
        <button className="btn-secondary" onClick={() => {
          setCurrentStep('select');
          setSelectedDocuments([]);
          setSelectedUsers([]);
          setShareResults([]);
        }}>
          <i className="fas fa-plus"></i> Share More Documents
        </button>
        <button className="btn-primary" onClick={() => {
          onShareComplete();
          onClose();
        }}>
          <i className="fas fa-check"></i> Complete
        </button>
      </div>
    </div>
  );

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content sharing-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>
            <i className="fas fa-share-alt"></i>
            Interdepartment Document Sharing
          </h2>
          <button className="close-btn" onClick={onClose}>
            <i className="fas fa-times"></i>
          </button>
        </div>

        <div className="sharing-stepper">
          <div className={`step ${currentStep === 'select' ? 'active' : ['configure', 'users', 'review', 'complete'].includes(currentStep) ? 'completed' : ''}`}>
            <div className="step-number">1</div>
            <span>Select</span>
          </div>
          <div className={`step ${currentStep === 'configure' ? 'active' : ['users', 'review', 'complete'].includes(currentStep) ? 'completed' : ''}`}>
            <div className="step-number">2</div>
            <span>Configure</span>
          </div>
          <div className={`step ${currentStep === 'users' ? 'active' : ['review', 'complete'].includes(currentStep) ? 'completed' : ''}`}>
            <div className="step-number">3</div>
            <span>Recipients</span>
          </div>
          <div className={`step ${currentStep === 'review' ? 'active' : currentStep === 'complete' ? 'completed' : ''}`}>
            <div className="step-number">4</div>
            <span>Review</span>
          </div>
          <div className={`step ${currentStep === 'complete' ? 'active' : ''}`}>
            <div className="step-number">5</div>
            <span>Complete</span>
          </div>
        </div>

        <div className="modal-body">
          {currentStep === 'select' && renderDocumentSelection()}
          {currentStep === 'configure' && renderShareConfiguration()}
          {currentStep === 'users' && renderUserSelection()}
          {currentStep === 'review' && renderReview()}
          {currentStep === 'complete' && renderComplete()}
        </div>
      </div>
    </div>
  );
};

export default InterdepartmentSharing;
