import axios from 'axios';

// Configuration de base d'axios
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types TypeScript pour les réponses API
export interface HealthResponse {
  status: string;
  message: string;
  timestamp: number;
}

export interface SettingsUpdateResponse {
  success: boolean;
  message: string;
}

// Service API
export const apiService = {
  async healthCheck(): Promise<HealthResponse> {
    const response = await api.get('/health');
    return response.data;
  },

  async updateSettings(settings: any): Promise<SettingsUpdateResponse> {
    const response = await api.post('/settings', settings);
    return response.data;
  },

  async getSettings(): Promise<any> {
    const response = await api.get('/settings');
    return response.data;
  },

  async openFolderDialog(): Promise<{success: boolean, path?: string, error?: string}> {
    try {
      const response = await api.get('/file-dialog/folder');
      return {
        success: response.data.success,
        path: response.data.path
      };
    } catch (error) {
      console.error('Folder Dialog Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async openFileDialog(): Promise<{success: boolean, path?: string, error?: string}> {
    try {
      const response = await api.get('/file-dialog/file');
      return {
        success: response.data.success,
        path: response.data.path
      };
    } catch (error) {
      console.error('File Dialog Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
};
