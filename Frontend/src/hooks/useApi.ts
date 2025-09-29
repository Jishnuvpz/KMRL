/**
 * React hooks for API operations with loading states and error handling
 */

import { useState, useEffect, useCallback } from 'react';
import { apiService, ApiResponse } from '../services/api';

export function useApiCall<T>(
  apiCall: () => Promise<ApiResponse<T>>,
  dependencies: any[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiCall();
      if (result.success && result.data) {
        setData(result.data);
      } else {
        setError(result.error?.message || 'Unknown error occurred');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Network error');
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    execute();
  }, [execute]);

  return { data, loading, error, refetch: execute };
}

export function useDocuments() {
  return useApiCall(() => apiService.getDocuments());
}

export function useDocument(id: number) {
  return useApiCall(() => apiService.getDocument(id), [id]);
}

export function useDashboardStats() {
  return useApiCall(() => apiService.getDashboardStats());
}

export function useAsyncOperation<T>() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (operation: () => Promise<ApiResponse<T>>) => {
    setLoading(true);
    setError(null);

    try {
      const result = await operation();
      if (result.success) {
        return result.data;
      } else {
        const errorMessage = result.error?.message || 'Operation failed';
        setError(errorMessage);
        throw new Error(errorMessage);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { execute, loading, error };
}

// Specific operation hooks
export function useLogin() {
  return useAsyncOperation();
}

export function useUploadDocument() {
  return useAsyncOperation();
}

export function useShareDocument() {
  return useAsyncOperation();
}

export function useOCR() {
  return useAsyncOperation();
}

export function useSummarization() {
  return useAsyncOperation();
}
