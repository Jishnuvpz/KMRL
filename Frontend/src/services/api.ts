/**
 * API Service for Document Management System
 * Handles all communication with the FastAPI backend
 */

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    message: string;
    code: string;
    details?: any;
  };
  message?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    username: string;
    role: string;
    department: string;
  };
}

export interface DocumentResponse {
  id: number;
  sender: string;
  subject: string;
  body: string;
  date: string;
  departments: string[];
  language: string;
  critical: boolean;
  priority: string;
  docType: string;
  source: string;
  summary: {
    en: string;
    ml: string;
  };
  roleSpecificSummaries?: {
    Staff: string;
    Manager: string;
    Director: string;
  };
  sharedWith?: string[];
  attachmentFilename?: string;
  dueDate?: string;
}

export interface UploadDocumentRequest {
  subject: string;
  sender: string;
  body: string;
  departments: string[];
  priority: string;
  docType: string;
  source: string;
  dueDate?: string;
}

class ApiService {
  private baseURL: string;
  private token: string | null = null;

  constructor() {
    this.baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    this.token = localStorage.getItem('access_token');
  }

  private getAuthHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    
    return headers;
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        ...options,
        headers: {
          ...this.getAuthHeaders(),
          ...options.headers,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: {
            message: data.error?.message || 'Request failed',
            code: data.error?.code || 'UNKNOWN_ERROR',
            details: data.error?.details
          }
        };
      }

      return data;
    } catch (error) {
      return {
        success: false,
        error: {
          message: error instanceof Error ? error.message : 'Network error',
          code: 'NETWORK_ERROR'
        }
      };
    }
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const result = await this.request<LoginResponse>('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (result.success && result.data?.access_token) {
      this.token = result.data.access_token;
      localStorage.setItem('access_token', this.token);
    }

    return result;
  }

  async logout(): Promise<void> {
    this.token = null;
    localStorage.removeItem('access_token');
  }

  // Documents
  async getDocuments(): Promise<ApiResponse<DocumentResponse[]>> {
    return this.request<DocumentResponse[]>('/api/documents/');
  }

  async getDocument(id: number): Promise<ApiResponse<DocumentResponse>> {
    return this.request<DocumentResponse>(`/api/documents/${id}`);
  }

  async uploadDocument(
    file: File, 
    metadata: UploadDocumentRequest
  ): Promise<ApiResponse<DocumentResponse>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify(metadata));

    return this.request<DocumentResponse>('/api/documents/upload', {
      method: 'POST',
      headers: {
        ...this.getAuthHeaders(),
        // Remove Content-Type to let browser set multipart boundary
        'Content-Type': undefined,
      } as any,
      body: formData,
    });
  }

  async processDocument(id: number): Promise<ApiResponse<any>> {
    return this.request(`/api/documents/${id}/process`, {
      method: 'POST',
    });
  }

  async shareDocument(
    id: number, 
    usernames: string[]
  ): Promise<ApiResponse<any>> {
    return this.request(`/api/documents/${id}/share`, {
      method: 'POST',
      body: JSON.stringify({ shared_with: usernames }),
    });
  }

  // OCR Services
  async performOCR(file: File): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request('/api/ocr/process', {
      method: 'POST',
      headers: {
        ...this.getAuthHeaders(),
        'Content-Type': undefined,
      } as any,
      body: formData,
    });
  }

  // Summarization
  async getSummary(
    text: string, 
    language: 'english' | 'malayalam' = 'english'
  ): Promise<ApiResponse<any>> {
    return this.request('/api/summarization/summarize', {
      method: 'POST',
      body: JSON.stringify({ text, language }),
    });
  }

  // Health Check
  async getHealth(): Promise<ApiResponse<any>> {
    return this.request('/health');
  }

  // Dashboard Stats
  async getDashboardStats(): Promise<ApiResponse<any>> {
    return this.request('/api/dashboard/stats');
  }

  // Search
  async searchDocuments(query: string): Promise<ApiResponse<DocumentResponse[]>> {
    return this.request<DocumentResponse[]>(`/api/documents/search?q=${encodeURIComponent(query)}`);
  }

  // User Management (Admin only)
  async getUsers(): Promise<ApiResponse<any[]>> {
    return this.request('/api/auth/users');
  }

  async updateUserRole(username: string, role: string): Promise<ApiResponse<any>> {
    return this.request('/api/auth/users/role', {
      method: 'PUT',
      body: JSON.stringify({ username, role }),
    });
  }
}

export const apiService = new ApiService();
export default apiService;
