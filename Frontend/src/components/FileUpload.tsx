/**
 * File Upload component with drag-and-drop and backend integration
 */

import React, { useState, useRef, DragEvent } from 'react';
import { useUploadDocument, useOCR } from '../hooks/useApi';
import { UploadDocumentRequest } from '../services/api';

interface FileUploadProps {
  onUploadComplete: (document: any) => void;
  onClose: () => void;
}

const allowedFileTypes = [
  'application/pdf',
  'image/jpeg',
  'image/png',
  'image/tiff',
  'text/plain',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
];

const departments = ['Operations', 'HR', 'Finance', 'Legal', 'IT', 'Safety', 'Engineering', 'Maintenance'];
const priorities = ['Low', 'Medium', 'High'];
const docTypes = ['Schedule', 'Policy', 'Report', 'Contract', 'Notice', 'Audit', 'Claim', 'Research'];
const sources = ['Email', 'SharePoint', 'Scanned', 'Maximo', 'Web Dashboard'];

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadComplete, onClose }) => {
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [ocrText, setOcrText] = useState('');
  const [metadata, setMetadata] = useState<UploadDocumentRequest>({
    subject: '',
    sender: '',
    body: '',
    departments: ['Operations'],
    priority: 'Medium',
    docType: 'Report',
    source: 'Web Dashboard',
  });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const { execute: uploadDocument, loading: uploadLoading, error: uploadError } = useUploadDocument();
  const { execute: performOCR, loading: ocrLoading, error: ocrError } = useOCR();

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
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = async (selectedFile: File) => {
    if (!allowedFileTypes.includes(selectedFile.type)) {
      alert('Unsupported file type. Please upload PDF, images, or text documents.');
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) { // 10MB limit
      alert('File size too large. Please upload files smaller than 10MB.');
      return;
    }

    setFile(selectedFile);
    
    // Auto-fill subject from filename
    const nameWithoutExt = selectedFile.name.replace(/\.[^/.]+$/, "");
    setMetadata(prev => ({ ...prev, subject: nameWithoutExt }));

    // Perform OCR if it's an image or PDF
    if (selectedFile.type.startsWith('image/') || selectedFile.type === 'application/pdf') {
      try {
        const result = await performOCR(async () => {
          const { apiService } = await import('../services/api');
          return apiService.performOCR(selectedFile);
        });
        
        if (result && result.text) {
          setOcrText(result.text);
          setMetadata(prev => ({ ...prev, body: result.text }));
        }
      } catch (error) {
        console.error('OCR failed:', error);
      }
    } else if (selectedFile.type === 'text/plain') {
      // Read text file content
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        setOcrText(content);
        setMetadata(prev => ({ ...prev, body: content }));
      };
      reader.readAsText(selectedFile);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file || !metadata.subject.trim() || !metadata.sender.trim()) {
      alert('Please fill in all required fields.');
      return;
    }

    try {
      const result = await uploadDocument(async () => {
        const { apiService } = await import('../services/api');
        return apiService.uploadDocument(file, metadata);
      });
      
      if (result) {
        onUploadComplete(result);
      }
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  const isLoading = uploadLoading || ocrLoading;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content large" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2><i className="fas fa-cloud-upload-alt"></i> Upload Document</h2>
          <button className="close-btn" onClick={onClose}>
            <i className="fas fa-times"></i>
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {/* File Upload Area */}
            <div 
              className={`file-upload-area ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.tiff,.txt,.doc,.docx"
                onChange={handleFileInputChange}
                style={{ display: 'none' }}
              />
              
              {file ? (
                <div className="file-info">
                  <i className="fas fa-file-alt"></i>
                  <div>
                    <strong>{file.name}</strong>
                    <p>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    {ocrLoading && <p><i className="fas fa-spinner fa-spin"></i> Processing...</p>}
                  </div>
                </div>
              ) : (
                <div className="upload-prompt">
                  <i className="fas fa-cloud-upload-alt"></i>
                  <p>Drag and drop your document here, or click to browse</p>
                  <p className="file-types">Supports: PDF, Images, Text, Word documents</p>
                </div>
              )}
            </div>

            {(uploadError || ocrError) && (
              <div className="error-message">
                <i className="fas fa-exclamation-triangle"></i>
                {uploadError || ocrError}
              </div>
            )}

            {/* Document Metadata */}
            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="subject">Subject *</label>
                <input
                  id="subject"
                  type="text"
                  value={metadata.subject}
                  onChange={(e) => setMetadata(prev => ({ ...prev, subject: e.target.value }))}
                  placeholder="Document title or subject"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="sender">Sender *</label>
                <input
                  id="sender"
                  type="email"
                  value={metadata.sender}
                  onChange={(e) => setMetadata(prev => ({ ...prev, sender: e.target.value }))}
                  placeholder="sender@example.com"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="departments">Departments</label>
                <select
                  id="departments"
                  value={metadata.departments[0]}
                  onChange={(e) => setMetadata(prev => ({ ...prev, departments: [e.target.value] }))}
                >
                  {departments.map(dept => (
                    <option key={dept} value={dept}>{dept}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="priority">Priority</label>
                <select
                  id="priority"
                  value={metadata.priority}
                  onChange={(e) => setMetadata(prev => ({ ...prev, priority: e.target.value }))}
                >
                  {priorities.map(priority => (
                    <option key={priority} value={priority}>{priority}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="docType">Document Type</label>
                <select
                  id="docType"
                  value={metadata.docType}
                  onChange={(e) => setMetadata(prev => ({ ...prev, docType: e.target.value }))}
                >
                  {docTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="source">Source</label>
                <select
                  id="source"
                  value={metadata.source}
                  onChange={(e) => setMetadata(prev => ({ ...prev, source: e.target.value }))}
                >
                  {sources.map(source => (
                    <option key={source} value={source}>{source}</option>
                  ))}
                </select>
              </div>

              <div className="form-group full-width">
                <label htmlFor="dueDate">Due Date (Optional)</label>
                <input
                  id="dueDate"
                  type="date"
                  value={metadata.dueDate || ''}
                  onChange={(e) => setMetadata(prev => ({ ...prev, dueDate: e.target.value || undefined }))}
                />
              </div>
            </div>

            {/* Extracted Text */}
            {ocrText && (
              <div className="form-group">
                <label htmlFor="extractedText">Extracted Text</label>
                <textarea
                  id="extractedText"
                  value={metadata.body}
                  onChange={(e) => setMetadata(prev => ({ ...prev, body: e.target.value }))}
                  placeholder="Document content will appear here after OCR processing..."
                  rows={6}
                />
              </div>
            )}
          </div>

          <div className="modal-footer">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={isLoading}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={isLoading || !file}>
              {isLoading ? (
                <>
                  <i className="fas fa-spinner fa-spin"></i> 
                  {ocrLoading ? 'Processing...' : 'Uploading...'}
                </>
              ) : (
                <>
                  <i className="fas fa-upload"></i> Upload Document
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default FileUpload;
