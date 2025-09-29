/**
 * Document Ingestion Component
 * Handles multiple types of document uploads and processing
 */

import React, { useState, useRef, DragEvent } from 'react';
import { useUploadDocument, useOCR } from '../hooks/useApi';
import { UploadDocumentRequest } from '../services/api';

interface DocumentIngestionProps {
  onUploadComplete: (document: any) => void;
  onClose: () => void;
}

const departments = ['Operations', 'HR', 'Finance', 'Legal', 'IT', 'Safety', 'Engineering', 'Maintenance'];
const priorities = ['Low', 'Medium', 'High'];
const docTypes = ['Schedule', 'Policy', 'Report', 'Contract', 'Notice', 'Audit', 'Claim', 'Research', 'Memo', 'Circular'];
const sources = ['Email', 'SharePoint', 'Scanned', 'Maximo', 'Web Dashboard', 'Physical Mail', 'Fax', 'Mobile App'];

interface IngestionStats {
  totalUploaded: number;
  processing: number;
  completed: number;
  failed: number;
}

export const DocumentIngestion: React.FC<DocumentIngestionProps> = ({ onUploadComplete, onClose }) => {
  const [files, setFiles] = useState<File[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [currentStep, setCurrentStep] = useState<'upload' | 'metadata' | 'processing' | 'complete'>('upload');
  const [batchMetadata, setBatchMetadata] = useState<Partial<UploadDocumentRequest>>({
    sender: '',
    departments: ['Operations'],
    priority: 'Medium',
    docType: 'Report',
    source: 'Web Dashboard',
  });
  const [stats, setStats] = useState<IngestionStats>({
    totalUploaded: 0,
    processing: 0,
    completed: 0,
    failed: 0
  });
  const [processedDocs, setProcessedDocs] = useState<any[]>([]);
  const [shareWithDepartments, setShareWithDepartments] = useState<string[]>([]);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { execute: uploadDocument, loading: uploadLoading } = useUploadDocument();
  const { execute: performOCR, loading: ocrLoading } = useOCR();

  const allowedFileTypes = [
    'application/pdf',
    'image/jpeg', 'image/jpg', 'image/png', 'image/tiff', 'image/bmp',
    'text/plain',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  ];

  const handleDrag = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files) {
      const droppedFiles = Array.from(e.dataTransfer.files);
      handleFileSelection(droppedFiles);
    }
  };

  const handleFileSelection = (selectedFiles: File[]) => {
    const validFiles = selectedFiles.filter(file => {
      if (!allowedFileTypes.includes(file.type)) {
        alert(`Unsupported file type: ${file.name}`);
        return false;
      }
      if (file.size > 25 * 1024 * 1024) { // 25MB limit
        alert(`File too large (${file.name}). Maximum size is 25MB.`);
        return false;
      }
      return true;
    });

    setFiles(prev => [...prev, ...validFiles]);
    
    if (validFiles.length > 0) {
      setCurrentStep('metadata');
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      handleFileSelection(selectedFiles);
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const processBatch = async () => {
    setCurrentStep('processing');
    setStats({ totalUploaded: files.length, processing: files.length, completed: 0, failed: 0 });
    
    const results: any[] = [];
    
    for (const file of files) {
      try {
        // Create document metadata
        const docMetadata: UploadDocumentRequest = {
          ...batchMetadata,
          subject: batchMetadata.subject || file.name.replace(/\.[^/.]+$/, ""),
          sender: batchMetadata.sender || 'batch.upload@kmrl.co.in',
        };

        // Upload document
        const uploadResult = await uploadDocument(async () => {
          const { apiService } = await import('../services/api');
          return apiService.uploadDocument(file, docMetadata);
        });

        if (uploadResult) {
          // If sharing is enabled, share with specified departments
          if (shareWithDepartments.length > 0) {
            try {
              const { apiService } = await import('../services/api');
              const shareEmails = shareWithDepartments.map(dept => 
                dept === 'Operations' ? 'director.ops@kmrl.co.in' :
                dept === 'HR' ? 'director.hr@kmrl.co.in' :
                dept === 'Finance' ? 'manager.fin@kmrl.co.in' :
                dept === 'Safety' ? 'staff.safety@kmrl.co.in' :
                `${dept.toLowerCase()}@kmrl.co.in`
              );
              
              await apiService.shareDocument(uploadResult.id, shareEmails);
            } catch (shareError) {
              console.warn('Document shared failed:', shareError);
            }
          }

          results.push({
            file: file.name,
            status: 'success',
            document: uploadResult,
            sharedWith: shareWithDepartments
          });
          
          setStats(prev => ({
            ...prev,
            processing: prev.processing - 1,
            completed: prev.completed + 1
          }));
        }
      } catch (error) {
        results.push({
          file: file.name,
          status: 'failed',
          error: error instanceof Error ? error.message : 'Upload failed'
        });
        
        setStats(prev => ({
          ...prev,
          processing: prev.processing - 1,
          failed: prev.failed + 1
        }));
      }
    }
    
    setProcessedDocs(results);
    setCurrentStep('complete');
  };

  const handleComplete = () => {
    const successfulDocs = processedDocs.filter(doc => doc.status === 'success');
    successfulDocs.forEach(doc => onUploadComplete(doc.document));
    onClose();
  };

  const renderUploadStep = () => (
    <div className="ingestion-step">
      <h3><i className="fas fa-cloud-upload-alt"></i> Document Ingestion</h3>
      <p>Upload multiple documents for batch processing</p>
      
      <div 
        className={`ingestion-drop-zone ${dragActive ? 'drag-active' : ''} ${files.length > 0 ? 'has-files' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.jpg,.jpeg,.png,.tiff,.txt,.doc,.docx,.xls,.xlsx"
          onChange={handleFileInputChange}
          style={{ display: 'none' }}
        />
        
        {files.length === 0 ? (
          <div className="upload-prompt">
            <i className="fas fa-cloud-upload-alt"></i>
            <h4>Drag & Drop Documents Here</h4>
            <p>Or click to browse files</p>
            <div className="supported-formats">
              <span>PDF</span>
              <span>Images</span>
              <span>Word</span>
              <span>Excel</span>
              <span>Text</span>
            </div>
          </div>
        ) : (
          <div className="file-list">
            <h4>{files.length} files selected</h4>
            {files.map((file, index) => (
              <div key={index} className="file-item">
                <div className="file-info">
                  <i className={`fas ${
                    file.type.includes('pdf') ? 'fa-file-pdf' :
                    file.type.includes('image') ? 'fa-file-image' :
                    file.type.includes('word') ? 'fa-file-word' :
                    file.type.includes('excel') ? 'fa-file-excel' :
                    'fa-file-alt'
                  }`}></i>
                  <div>
                    <strong>{file.name}</strong>
                    <span>{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                  </div>
                </div>
                <button 
                  className="remove-file"
                  onClick={(e) => { e.stopPropagation(); removeFile(index); }}
                >
                  <i className="fas fa-times"></i>
                </button>
              </div>
            ))}
            
            <div className="add-more-files" onClick={(e) => e.stopPropagation()}>
              <button onClick={() => fileInputRef.current?.click()}>
                <i className="fas fa-plus"></i> Add More Files
              </button>
            </div>
          </div>
        )}
      </div>
      
      {files.length > 0 && (
        <div className="ingestion-actions">
          <button className="btn-secondary" onClick={() => setFiles([])}>
            <i className="fas fa-trash"></i> Clear All
          </button>
          <button className="btn-primary" onClick={() => setCurrentStep('metadata')}>
            <i className="fas fa-arrow-right"></i> Configure Metadata ({files.length} files)
          </button>
        </div>
      )}
    </div>
  );

  const renderMetadataStep = () => (
    <div className="ingestion-step">
      <h3><i className="fas fa-cog"></i> Batch Metadata Configuration</h3>
      <p>Set common properties for all {files.length} documents</p>
      
      <div className="metadata-form">
        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="batch-sender">Default Sender</label>
            <input
              id="batch-sender"
              type="email"
              value={batchMetadata.sender}
              onChange={(e) => setBatchMetadata(prev => ({ ...prev, sender: e.target.value }))}
              placeholder="sender@department.kmrl.co.in"
            />
          </div>

          <div className="form-group">
            <label htmlFor="batch-department">Primary Department</label>
            <select
              id="batch-department"
              value={batchMetadata.departments?.[0] || 'Operations'}
              onChange={(e) => setBatchMetadata(prev => ({ ...prev, departments: [e.target.value] }))}
            >
              {departments.map(dept => (
                <option key={dept} value={dept}>{dept}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="batch-priority">Priority Level</label>
            <select
              id="batch-priority"
              value={batchMetadata.priority}
              onChange={(e) => setBatchMetadata(prev => ({ ...prev, priority: e.target.value }))}
            >
              {priorities.map(priority => (
                <option key={priority} value={priority}>{priority}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="batch-doctype">Document Type</label>
            <select
              id="batch-doctype"
              value={batchMetadata.docType}
              onChange={(e) => setBatchMetadata(prev => ({ ...prev, docType: e.target.value }))}
            >
              {docTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="batch-source">Document Source</label>
            <select
              id="batch-source"
              value={batchMetadata.source}
              onChange={(e) => setBatchMetadata(prev => ({ ...prev, source: e.target.value }))}
            >
              {sources.map(source => (
                <option key={source} value={source}>{source}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="batch-duedate">Due Date (Optional)</label>
            <input
              id="batch-duedate"
              type="date"
              value={batchMetadata.dueDate || ''}
              onChange={(e) => setBatchMetadata(prev => ({ ...prev, dueDate: e.target.value || undefined }))}
            />
          </div>
        </div>

        {/* Interdepartment Sharing */}
        <div className="sharing-section">
          <h4><i className="fas fa-share-alt"></i> Interdepartment Sharing</h4>
          <p>Share these documents with other departments automatically</p>
          
          <div className="department-checkboxes">
            {departments.filter(dept => dept !== batchMetadata.departments?.[0]).map(dept => (
              <label key={dept} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={shareWithDepartments.includes(dept)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setShareWithDepartments(prev => [...prev, dept]);
                    } else {
                      setShareWithDepartments(prev => prev.filter(d => d !== dept));
                    }
                  }}
                />
                <span className="dept-color-tag" style={{ 
                  backgroundColor: 
                    dept === 'Operations' ? '#007bff' :
                    dept === 'HR' ? '#28a745' :
                    dept === 'Finance' ? '#ffc107' :
                    dept === 'Legal' ? '#6f42c1' :
                    dept === 'IT' ? '#17a2b8' :
                    dept === 'Safety' ? '#dc3545' :
                    '#6c757d'
                }}></span>
                {dept}
              </label>
            ))}
          </div>
          
          {shareWithDepartments.length > 0 && (
            <div className="sharing-preview">
              <i className="fas fa-info-circle"></i>
              Documents will be shared with: <strong>{shareWithDepartments.join(', ')}</strong>
            </div>
          )}
        </div>
      </div>
      
      <div className="ingestion-actions">
        <button className="btn-secondary" onClick={() => setCurrentStep('upload')}>
          <i className="fas fa-arrow-left"></i> Back to Upload
        </button>
        <button 
          className="btn-primary" 
          onClick={processBatch}
          disabled={!batchMetadata.sender?.trim()}
        >
          <i className="fas fa-play"></i> Process {files.length} Documents
        </button>
      </div>
    </div>
  );

  const renderProcessingStep = () => (
    <div className="ingestion-step">
      <h3><i className="fas fa-cog fa-spin"></i> Processing Documents</h3>
      <p>Uploading, processing OCR, and generating summaries...</p>
      
      <div className="processing-stats">
        <div className="stat-card">
          <div className="stat-value">{stats.totalUploaded}</div>
          <div className="stat-label">Total</div>
        </div>
        <div className="stat-card processing">
          <div className="stat-value">{stats.processing}</div>
          <div className="stat-label">Processing</div>
        </div>
        <div className="stat-card success">
          <div className="stat-value">{stats.completed}</div>
          <div className="stat-label">Completed</div>
        </div>
        <div className="stat-card error">
          <div className="stat-value">{stats.failed}</div>
          <div className="stat-label">Failed</div>
        </div>
      </div>
      
      <div className="progress-bar">
        <div 
          className="progress-fill"
          style={{ 
            width: `${((stats.completed + stats.failed) / stats.totalUploaded) * 100}%` 
          }}
        ></div>
      </div>
      
      <div className="processing-details">
        <p>Processing {stats.processing} documents...</p>
        <p>OCR extraction, language detection, and AI summarization in progress</p>
      </div>
    </div>
  );

  const renderCompleteStep = () => (
    <div className="ingestion-step">
      <h3><i className="fas fa-check-circle"></i> Ingestion Complete</h3>
      <p>Document batch processing finished</p>
      
      <div className="completion-stats">
        <div className="stat-summary success">
          <i className="fas fa-check-circle"></i>
          <div>
            <strong>{stats.completed}</strong>
            <span>Successfully processed</span>
          </div>
        </div>
        
        {stats.failed > 0 && (
          <div className="stat-summary error">
            <i className="fas fa-exclamation-circle"></i>
            <div>
              <strong>{stats.failed}</strong>
              <span>Failed to process</span>
            </div>
          </div>
        )}
        
        {shareWithDepartments.length > 0 && (
          <div className="stat-summary shared">
            <i className="fas fa-share-alt"></i>
            <div>
              <strong>{shareWithDepartments.length}</strong>
              <span>Departments shared with</span>
            </div>
          </div>
        )}
      </div>
      
      <div className="processed-documents">
        <h4>Processing Results:</h4>
        {processedDocs.map((doc, index) => (
          <div key={index} className={`processed-doc ${doc.status}`}>
            <i className={`fas ${doc.status === 'success' ? 'fa-check' : 'fa-times'}`}></i>
            <div className="doc-info">
              <strong>{doc.file}</strong>
              {doc.status === 'success' ? (
                <span className="success">Successfully processed and uploaded</span>
              ) : (
                <span className="error">Failed: {doc.error}</span>
              )}
              {doc.sharedWith && doc.sharedWith.length > 0 && (
                <div className="shared-info">
                  <i className="fas fa-share"></i> Shared with {doc.sharedWith.join(', ')}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      
      <div className="ingestion-actions">
        <button className="btn-secondary" onClick={() => {
          setCurrentStep('upload');
          setFiles([]);
          setProcessedDocs([]);
          setShareWithDepartments([]);
        }}>
          <i className="fas fa-plus"></i> Process More Documents
        </button>
        <button className="btn-primary" onClick={handleComplete}>
          <i className="fas fa-check"></i> Complete Ingestion
        </button>
      </div>
    </div>
  );

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content ingestion-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>
            <i className="fas fa-file-import"></i> 
            Document Ingestion & Interdepartment Sharing
          </h2>
          <button className="close-btn" onClick={onClose}>
            <i className="fas fa-times"></i>
          </button>
        </div>

        <div className="ingestion-stepper">
          <div className={`step ${currentStep === 'upload' ? 'active' : currentStep === 'metadata' || currentStep === 'processing' || currentStep === 'complete' ? 'completed' : ''}`}>
            <div className="step-number">1</div>
            <span>Upload</span>
          </div>
          <div className={`step ${currentStep === 'metadata' ? 'active' : currentStep === 'processing' || currentStep === 'complete' ? 'completed' : ''}`}>
            <div className="step-number">2</div>
            <span>Configure</span>
          </div>
          <div className={`step ${currentStep === 'processing' ? 'active' : currentStep === 'complete' ? 'completed' : ''}`}>
            <div className="step-number">3</div>
            <span>Process</span>
          </div>
          <div className={`step ${currentStep === 'complete' ? 'active' : ''}`}>
            <div className="step-number">4</div>
            <span>Complete</span>
          </div>
        </div>

        <div className="modal-body">
          {currentStep === 'upload' && renderUploadStep()}
          {currentStep === 'metadata' && renderMetadataStep()}
          {currentStep === 'processing' && renderProcessingStep()}
          {currentStep === 'complete' && renderCompleteStep()}
        </div>
      </div>
    </div>
  );
};

export default DocumentIngestion;
