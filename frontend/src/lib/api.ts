/**
 * API client for FastAPI backend communication
 */

import axios from 'axios';
import type { 
  CanvasRequest, 
  SuggestionResponse, 
  HealthResponse, 
  ProvidersResponse,
  APIError 
} from '@/types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      const apiError: APIError = {
        error: error.response.data?.error || `HTTP ${error.response.status}`,
        details: error.response.data?.details || error.message,
      };
      throw apiError;
    } else if (error.request) {
      // Network error
      throw {
        error: 'Network Error',
        details: 'Could not connect to backend server. Make sure it\'s running on port 8000.',
      } as APIError;
    } else {
      // Other error
      throw {
        error: 'Request Error',
        details: error.message,
      } as APIError;
    }
  }
);

export class AIDesignAPI {
  /**
   * Check backend health status
   */
  static async checkHealth(): Promise<HealthResponse> {
    try {
      const response = await apiClient.get<HealthResponse>('/health');
      return response.data;
    } catch (error) {
      throw error as APIError;
    }
  }

  /**
   * Check suggestion service health
   */
  static async checkSuggestionHealth(): Promise<HealthResponse> {
    try {
      const response = await apiClient.get<HealthResponse>('/api/v1/health');
      return response.data;
    } catch (error) {
      throw error as APIError;
    }
  }

  /**
   * Get AI suggestions for canvas state
   */
  static async getSuggestion(request: CanvasRequest): Promise<SuggestionResponse> {
    try {
      const response = await apiClient.post<SuggestionResponse>('/api/v1/suggest', request);
      return response.data;
    } catch (error) {
      throw error as APIError;
    }
  }

  /**
   * Get available LLM providers and their status
   */
  static async getProviders(): Promise<ProvidersResponse> {
    try {
      const response = await apiClient.get<ProvidersResponse>('/api/v1/providers');
      return response.data;
    } catch (error) {
      throw error as APIError;
    }
  }

  /**
   * Switch the active LLM provider
   */
  static async switchProvider(provider: string): Promise<any> {
    try {
      const response = await apiClient.post('/api/v1/providers/switch', { provider });
      return response.data;
    } catch (error) {
      throw error as APIError;
    }
  }

  /**
   * Convert Excalidraw elements to API format
   * Extracts relevant information for pattern analysis
   */
  static formatCanvasElements(elements: any[]): any[] {
    return elements.map(element => ({
      id: element.id,
      type: element.type,
      text: element.text || '',
      x: element.x,
      y: element.y,
      width: element.width,
      height: element.height,
      // Include other relevant properties for analysis
      ...element
    }));
  }

  /**
   * Check if there are significant changes between canvas states
   */
  static hasSignificantChanges(oldElements: any[], newElements: any[]): boolean {
    if (oldElements.length !== newElements.length) {
      return true;
    }
    
    // Check for meaningful changes in elements
    for (const newEl of newElements) {
      const oldEl = oldElements.find(old => old.id === newEl.id);
      
      if (!oldEl) {
        return true; // New element
      }
      
      // Check for significant text changes (labels are important for AI analysis)
      if ((oldEl.text || '').trim() !== (newEl.text || '').trim()) {
        return true;
      }
      
      // Check for significant position changes (>50px movement)
      const positionThreshold = 50;
      if (Math.abs((oldEl.x || 0) - (newEl.x || 0)) > positionThreshold ||
          Math.abs((oldEl.y || 0) - (newEl.y || 0)) > positionThreshold) {
        return true;
      }
      
      // Check for significant size changes (>20px)
      const sizeThreshold = 20;
      if (Math.abs((oldEl.width || 0) - (newEl.width || 0)) > sizeThreshold ||
          Math.abs((oldEl.height || 0) - (newEl.height || 0)) > sizeThreshold) {
        return true;
      }
    }
    
    return false;
  }

  /**
   * Detect specific changes in canvas elements
   */
  static detectChanges(oldElements: any[], newElements: any[]): any[] {
    const changes: any[] = [];
    
    // Find new elements
    newElements.forEach(newEl => {
      const oldEl = oldElements.find(oldEl => oldEl.id === newEl.id);
      if (!oldEl) {
        changes.push({
          action: 'add',
          element_id: newEl.id,
          element: {
            id: newEl.id,
            type: newEl.type,
            text: newEl.text || '',
            x: newEl.x,
            y: newEl.y
          },
          timestamp: new Date().toISOString()
        });
      } else {
        // Check for modifications
        const hasTextChange = (oldEl.text || '').trim() !== (newEl.text || '').trim();
        const hasPositionChange = Math.abs((oldEl.x || 0) - (newEl.x || 0)) > 50 ||
                                 Math.abs((oldEl.y || 0) - (newEl.y || 0)) > 50;
        
        if (hasTextChange || hasPositionChange) {
          changes.push({
            action: 'modify',
            element_id: newEl.id,
            changes: {
              text: hasTextChange ? { old: oldEl.text, new: newEl.text } : undefined,
              position: hasPositionChange ? { 
                old: { x: oldEl.x, y: oldEl.y }, 
                new: { x: newEl.x, y: newEl.y } 
              } : undefined
            },
            timestamp: new Date().toISOString()
          });
        }
      }
    });
    
    // Find removed elements
    oldElements.forEach(oldEl => {
      const newEl = newElements.find(newEl => newEl.id === oldEl.id);
      if (!newEl) {
        changes.push({
          action: 'remove',
          element_id: oldEl.id,
          timestamp: new Date().toISOString()
        });
      }
    });
    
    return changes;
  }
}

export default AIDesignAPI;