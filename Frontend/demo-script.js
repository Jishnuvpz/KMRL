// Document Management System - Demo JavaScript

class DocumentManagementAPI {
    constructor() {
        this.API_BASE = 'http://localhost:8000';  // Actual FAISS backend
        this.token = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
        this.currentUser = JSON.parse(localStorage.getItem('current_user') || 'null');
    }

    // Authentication methods
    async login(username, password, rememberMe = false) {
        try {
            const response = await fetch(`${this.API_BASE}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: username,  // Backend expects email field
                    password,
                    remember_me: rememberMe
                })
            });

            const data = await response.json();
            
            if (response.ok && data.access_token) {
                this.token = data.access_token;
                this.refreshToken = data.refresh_token;
                this.currentUser = data.user || { username };

                // Store tokens
                localStorage.setItem('access_token', this.token);
                localStorage.setItem('refresh_token', this.refreshToken);
                localStorage.setItem('current_user', JSON.stringify(this.currentUser));

                return { success: true, data };
            } else {
                return { success: false, error: data.detail || 'Login failed' };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async logout() {
        try {
            if (this.token) {
                await fetch(`${this.API_BASE}/api/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.token}`,
                        'Content-Type': 'application/json'
                    }
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Clear local storage
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('current_user');
            this.token = null;
            this.refreshToken = null;
            this.currentUser = null;
        }
    }

    // Helper method for authenticated requests
    async authenticatedRequest(url, options = {}) {
        const headers = {
            'Authorization': `Bearer ${this.token}`,
            ...options.headers
        };

        const response = await fetch(`${this.API_BASE}${url}`, {
            ...options,
            headers
        });

        if (response.status === 401) {
            // Token expired or invalid - redirect to login
            console.warn('Authentication failed - redirecting to login');
            this.logout();
            window.location.reload();
            return null;
        }

        return response;
    }

    // System status check
    async checkBackendStatus() {
        try {
            const response = await fetch(`${this.API_BASE}/`);
            if (response.ok) {
                const data = await response.json();
                return { success: true, data };
            } else {
                return { success: false, error: 'Backend not responding' };
            }
        } catch (error) {
            return { success: false, error: 'Connection failed' };
        }
    }

    // Document management methods (simplified - no backend support for listing)
    async uploadDocument(formData) {
        try {
            const response = await this.authenticatedRequest('/api/documents/upload', {
                method: 'POST',
                body: formData
            });

            if (response && response.ok) {
                const data = await response.json();
                return { success: true, data };
            } else {
                const errorData = await response?.json();
                return { success: false, error: errorData?.detail || 'Upload failed' };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Note: Backend doesn't support document listing yet
    async getDocuments(category = null, limit = 50) {
        // Mock response since backend doesn't have this endpoint
        console.warn('Document listing not implemented in backend');
        return { 
            success: true, 
            data: [] // Empty array - will show "upload your first document" message
        };
    }

    // Note: Backend doesn't support basic document search yet
    async searchDocuments(query) {
        console.warn('Basic document search not implemented - use semantic search instead');
        return { success: false, error: 'Use semantic search instead' };
    }

    // Semantic search methods
    async semanticSearch(query, searchType = 'hybrid', topK = 10, minScore = 0.0) {
        try {
            const response = await this.authenticatedRequest('/api/semantic-search/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query,
                    search_type: searchType,
                    top_k: parseInt(topK),
                    min_score: parseFloat(minScore),
                    include_chunks: true
                })
            });

            if (response && response.ok) {
                const data = await response.json();
                return { success: true, data };
            } else {
                const errorData = await response?.json();
                return { success: false, error: errorData?.detail || 'Semantic search failed' };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async getSemanticSearchAnalytics() {
        try {
            const response = await this.authenticatedRequest('/api/semantic-search/analytics');
            
            if (response && response.ok) {
                const data = await response.json();
                return { success: true, data };
            } else {
                console.warn('Analytics endpoint not fully implemented');
                return { 
                    success: true, 
                    data: {
                        total_queries: 0,
                        avg_response_time_ms: 0,
                        popular_queries: [],
                        search_types_distribution: {},
                        recent_activity: []
                    }
                };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async getSemanticSearchStatus() {
        try {
            const response = await this.authenticatedRequest('/api/semantic-search/status');
            
            if (response && response.ok) {
                const data = await response.json();
                return { success: true, data };
            } else {
                console.warn('Status endpoint not fully implemented');
                return { 
                    success: true, 
                    data: { status: 'unknown' }
                };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
}

// UI Controller
class DocumentManagementUI {
    constructor() {
        this.api = new DocumentManagementAPI();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkAuthState();
        this.checkBackendStatus();
    }

    setupEventListeners() {
        // Login form
        document.getElementById('login-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        // Logout button
        document.getElementById('logout-btn').addEventListener('click', () => {
            this.handleLogout();
        });

        // Tab navigation
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Upload form
        document.getElementById('upload-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFileUpload();
        });

        // File drag and drop
        const fileUploadArea = document.getElementById('file-upload-area');
        fileUploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileUploadArea.classList.add('dragover');
        });

        fileUploadArea.addEventListener('dragleave', () => {
            fileUploadArea.classList.remove('dragover');
        });

        fileUploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            fileUploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            document.getElementById('file-input').files = files;
            this.updateFileInput();
        });

        // File input change
        document.getElementById('file-input').addEventListener('change', () => {
            this.updateFileInput();
        });

        // Refresh documents
        document.getElementById('refresh-docs').addEventListener('click', () => {
            this.loadDocuments();
        });

        // Document filters
        document.getElementById('doc-filter').addEventListener('input', () => {
            this.filterDocuments();
        });

        document.getElementById('category-filter').addEventListener('change', () => {
            this.filterDocuments();
        });

        // Search form
        document.getElementById('search-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSemanticSearch();
        });

        // Example queries
        document.querySelectorAll('.example-query').forEach(query => {
            query.addEventListener('click', (e) => {
                document.getElementById('search-query').value = e.target.textContent;
                this.handleSemanticSearch();
            });
        });
    }

    checkAuthState() {
        if (this.api.token && this.api.currentUser) {
            this.showDashboard();
        } else {
            this.showLogin();
        }
    }

    async checkBackendStatus() {
        const statusElement = document.getElementById('backend-status');
        
        try {
            const response = await fetch(`${this.api.API_BASE}/`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                mode: 'cors'  // Explicitly enable CORS
            });
            
            if (response.ok) {
                const data = await response.json();
                statusElement.textContent = 'Connected';
                statusElement.style.color = '#28a745';
                console.log('✅ Backend connected:', data);
            } else {
                statusElement.textContent = `Error ${response.status}`;
                statusElement.style.color = '#dc3545';
                this.showToast(`Backend error: ${response.status}`, 'error');
            }
        } catch (error) {
            console.error('Backend connection error:', error);
            statusElement.textContent = 'Disconnected';
            statusElement.style.color = '#dc3545';
            
            // More specific error messages
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                this.showToast('Backend connection failed - Server may not be running on port 8000', 'error');
            } else if (error.name === 'TypeError' && error.message.includes('CORS')) {
                this.showToast('CORS error - Check backend CORS configuration', 'error');
            } else {
                this.showToast(`Connection error: ${error.message}`, 'error');
            }
        }
    }

    async handleLogin() {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const rememberMe = document.getElementById('remember_me').checked;

        this.showLoading(true);

        const result = await this.api.login(username, password, rememberMe);

        this.showLoading(false);

        if (result.success) {
            this.showToast('Login successful!', 'success');
            this.showDashboard();
        } else {
            this.showToast(result.error, 'error');
        }
    }

    async handleLogout() {
        await this.api.logout();
        this.showToast('Logged out successfully', 'success');
        this.showLogin();
    }

    showLogin() {
        document.getElementById('login-section').classList.remove('hidden');
        document.getElementById('dashboard-section').classList.add('hidden');
    }

    showDashboard() {
        document.getElementById('login-section').classList.add('hidden');
        document.getElementById('dashboard-section').classList.remove('hidden');
        
        // Update user info
        const userElement = document.getElementById('current-user');
        userElement.textContent = this.api.currentUser?.username || 'Unknown';

        // Load initial data
        this.loadDocuments();
        this.loadAnalytics();
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');

        // Load tab-specific data
        if (tabName === 'documents') {
            this.loadDocuments();
        } else if (tabName === 'analytics') {
            this.loadAnalytics();
        }
    }

    updateFileInput() {
        const fileInput = document.getElementById('file-input');
        const uploadText = document.querySelector('.upload-text p');
        
        if (fileInput.files.length > 0) {
            const fileNames = Array.from(fileInput.files).map(f => f.name).join(', ');
            uploadText.innerHTML = `Selected: ${fileNames}`;
            
            // Auto-fill title from first file
            const titleInput = document.getElementById('doc-title');
            if (!titleInput.value && fileInput.files[0]) {
                const fileName = fileInput.files[0].name;
                titleInput.value = fileName.substring(0, fileName.lastIndexOf('.')) || fileName;
            }
        } else {
            uploadText.innerHTML = 'Drag & drop files here or <span>browse</span>';
        }
    }

    async handleFileUpload() {
        const fileInput = document.getElementById('file-input');
        const title = document.getElementById('doc-title').value;
        const category = document.getElementById('doc-category').value;
        const tags = document.getElementById('doc-tags').value;
        const enableSemantic = document.getElementById('enable-semantic').checked;

        if (!fileInput.files.length) {
            this.showToast('Please select a file', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('title', title);
        formData.append('category', category);
        formData.append('tags', tags);
        formData.append('enable_semantic_search', enableSemantic);

        this.showUploadProgress(true);

        const result = await this.api.uploadDocument(formData);

        this.showUploadProgress(false);

        if (result.success) {
            this.showToast('Document uploaded successfully!', 'success');
            
            // Reset form
            document.getElementById('upload-form').reset();
            this.updateFileInput();
            
            // Refresh documents if on documents tab
            const activeTab = document.querySelector('.tab-pane.active');
            if (activeTab && activeTab.id === 'documents-tab') {
                this.loadDocuments();
            }
        } else {
            this.showToast(result.error, 'error');
        }
    }

    showUploadProgress(show) {
        const progressElement = document.getElementById('upload-progress');
        
        if (show) {
            progressElement.classList.remove('hidden');
            // Simulate progress
            let progress = 0;
            const interval = setInterval(() => {
                progress += Math.random() * 20;
                if (progress >= 90) {
                    progress = 90;
                    clearInterval(interval);
                }
                document.getElementById('progress-fill').style.width = `${progress}%`;
                document.getElementById('progress-text').textContent = `Uploading... ${Math.round(progress)}%`;
            }, 200);
        } else {
            // Complete progress
            document.getElementById('progress-fill').style.width = '100%';
            document.getElementById('progress-text').textContent = 'Upload complete!';
            
            setTimeout(() => {
                progressElement.classList.add('hidden');
                document.getElementById('progress-fill').style.width = '0%';
            }, 1000);
        }
    }

    async loadDocuments() {
        const documentsList = document.getElementById('documents-list');
        documentsList.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading documents...</div>';

        const result = await this.api.getDocuments();

        if (result.success) {
            this.renderDocuments(result.data);
        } else {
            documentsList.innerHTML = `<div class="error">Failed to load documents: ${result.error}</div>`;
        }
    }

    renderDocuments(documents) {
        const documentsList = document.getElementById('documents-list');
        
        if (!documents.length) {
            documentsList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <h3>No documents yet</h3>
                    <p>Upload your first document to get started with FAISS semantic search!</p>
                    <button class="btn btn-primary" onclick="document.querySelector('[data-tab=upload]').click()">
                        <i class="fas fa-plus"></i> Upload Document
                    </button>
                </div>
            `;
            return;
        }

        const documentsHTML = documents.map(doc => `
            <div class="document-item" data-category="${doc.category || ''}" data-title="${doc.title || ''}">
                <div class="document-info">
                    <h4>${doc.title || 'Untitled'}</h4>
                    <div class="document-meta">
                        <span><i class="fas fa-folder"></i> ${doc.category || 'Uncategorized'}</span>
                        <span><i class="fas fa-calendar"></i> ${this.formatDate(doc.created_at)}</span>
                        <span><i class="fas fa-file"></i> ${doc.file_type || 'Unknown'}</span>
                        ${doc.tags && doc.tags.length ? `<span><i class="fas fa-tags"></i> ${doc.tags.join(', ')}</span>` : ''}
                    </div>
                </div>
                <div class="document-actions">
                    <button class="btn btn-secondary" ${doc.download_url ? `onclick="window.open('${doc.download_url}', '_blank')"` : 'disabled'}>
                        <i class="fas fa-download"></i> ${doc.download_url ? 'Download' : 'Not Available'}
                    </button>
                </div>
            </div>
        `).join('');

        documentsList.innerHTML = documentsHTML;
    }

    filterDocuments() {
        const filterText = document.getElementById('doc-filter').value.toLowerCase();
        const categoryFilter = document.getElementById('category-filter').value;
        
        document.querySelectorAll('.document-item').forEach(item => {
            const title = item.dataset.title.toLowerCase();
            const category = item.dataset.category;
            
            const matchesText = title.includes(filterText);
            const matchesCategory = !categoryFilter || category === categoryFilter;
            
            if (matchesText && matchesCategory) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    }

    async handleSemanticSearch() {
        const query = document.getElementById('search-query').value;
        const searchType = document.getElementById('search-type').value;
        const topK = document.getElementById('top-k').value;
        const minScore = document.getElementById('min-score').value;

        if (!query.trim()) {
            this.showToast('Please enter a search query', 'error');
            return;
        }

        const resultsContainer = document.getElementById('search-results');
        resultsContainer.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Searching...</div>';

        const result = await this.api.semanticSearch(query, searchType, topK, minScore);

        if (result.success) {
            this.renderSearchResults(result.data);
        } else {
            resultsContainer.innerHTML = `<div class="error">Search failed: ${result.error}</div>`;
        }
    }

    renderSearchResults(searchData) {
        const resultsContainer = document.getElementById('search-results');
        
        if (!searchData.results || !searchData.results.length) {
            resultsContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <p>No results found for "${searchData.query}"</p>
                    <p>Try using different keywords or reducing the minimum similarity threshold.</p>
                </div>
            `;
            return;
        }

        const resultsHTML = `
            <div class="search-info">
                <p>Found ${searchData.total_results} results in ${searchData.search_time_ms}ms</p>
            </div>
            ${searchData.results.map(result => `
                <div class="search-result">
                    <div class="search-result-header">
                        <div class="search-result-title">${result.title}</div>
                        <div class="similarity-score">${Math.round(result.similarity_score * 100)}% match</div>
                    </div>
                    ${result.snippet ? `<div class="search-result-snippet">${result.snippet}</div>` : ''}
                    <div class="search-result-meta">
                        <span><i class="fas fa-file"></i> ${result.file_type}</span>
                        <span><i class="fas fa-calendar"></i> ${this.formatDate(result.created_at)}</span>
                        ${result.author ? `<span><i class="fas fa-user"></i> ${result.author}</span>` : ''}
                        ${result.chunks && result.chunks.length ? `<span><i class="fas fa-puzzle-piece"></i> ${result.chunks.length} chunks</span>` : ''}
                    </div>
                </div>
            `).join('')}
        `;

        resultsContainer.innerHTML = resultsHTML;
    }

    async loadAnalytics() {
        // Simple analytics since backend has limited support
        document.getElementById('total-docs').textContent = '0'; // Backend doesn't provide doc count
        document.getElementById('total-searches').textContent = '0';
        document.getElementById('avg-response').textContent = '0ms';
        document.getElementById('system-health').textContent = 'Unknown';

        // Try to get semantic search analytics
        const analyticsResult = await this.api.getSemanticSearchAnalytics();
        if (analyticsResult.success) {
            const analytics = analyticsResult.data;
            document.getElementById('total-searches').textContent = analytics.total_queries || 0;
            document.getElementById('avg-response').textContent = `${analytics.avg_response_time_ms || 0}ms`;
        }

        // Try to get system status
        const statusResult = await this.api.getSemanticSearchStatus();
        if (statusResult.success) {
            const statusText = statusResult.data.status === 'healthy' ? 'Healthy' : 
                             statusResult.data.status === 'error' ? 'Error' : 'Unknown';
            document.getElementById('system-health').textContent = statusText;
        }

        // Load recent activity
        this.loadRecentActivity();
    }

    loadRecentActivity() {
        const activityContainer = document.getElementById('recent-activity');
        
        // Mock activity data - in a real app, this would come from an API
        const activities = [
            { type: 'upload', description: 'Document uploaded', time: new Date() },
            { type: 'search', description: 'Semantic search performed', time: new Date(Date.now() - 300000) },
            { type: 'login', description: 'User logged in', time: new Date(Date.now() - 600000) }
        ];

        const activityHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon">
                    <i class="fas fa-${this.getActivityIcon(activity.type)}"></i>
                </div>
                <div class="activity-content">
                    <h5>${activity.description}</h5>
                    <p>${this.formatTime(activity.time)}</p>
                </div>
            </div>
        `).join('');

        activityContainer.innerHTML = activityHTML;
    }

    getActivityIcon(type) {
        const icons = {
            upload: 'upload',
            search: 'search',
            login: 'sign-in-alt',
            download: 'download'
        };
        return icons[type] || 'circle';
    }

    formatDate(dateString) {
        if (!dateString) return 'Unknown';
        const date = new Date(dateString);
        return date.toLocaleDateString();
    }

    formatTime(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        
        const days = Math.floor(hours / 24);
        return `${days}d ago`;
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' ? 'check-circle' : 
                    type === 'error' ? 'exclamation-circle' : 
                    type === 'warning' ? 'exclamation-triangle' : 'info-circle';
        
        toast.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <span>${message}</span>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    showLoading(show) {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (show) {
            loadingOverlay.classList.remove('hidden');
        } else {
            loadingOverlay.classList.add('hidden');
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DocumentManagementUI();
});