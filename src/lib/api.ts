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

export interface BackupListResponse {
  success: boolean;
  backups?: any[];
  error?: string;
}

export interface BackupActionResponse {
  success: boolean;
  message?: string;
  error?: string;
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
      // Utiliser un timeout plus long pour les dialogues (60 secondes)
      const response = await api.get('/file-dialog/folder', { timeout: 60000 });
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
      // Utiliser un timeout plus long pour les dialogues (60 secondes)
      const response = await api.get('/file-dialog/file', { timeout: 60000 });
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
  },

  async openSaveDialog(params: {
    title?: string;
    initialfile?: string;
    defaultextension?: string;
    filetypes?: [string, string][];
  }): Promise<{success: boolean, path?: string, error?: string}> {
    try {
      const response = await api.post('/file-dialog/save', params);

      // Si c'est le mode WSL, demander le chemin à l'utilisateur
      if (!response.data.success && response.data.error === 'WSL_MODE') {
        const filetypes_str = params.filetypes?.map(([desc, ext]) => `${desc} (${ext})`).join(' | ') || 'Tous les fichiers (*.*)';
        const prompt_text = `En mode WSL, le dialogue de sauvegarde n'est pas disponible.\n\n` +
                          `Titre: ${params.title || 'Enregistrer sous...'}\n` +
                          `Fichier initial: ${params.initialfile || ''}\n` +
                          `Extension par défaut: ${params.defaultextension || ''}\n` +
                          `Types de fichiers: ${filetypes_str}\n\n` +
                          `Veuillez saisir le chemin complet du fichier de destination :\n` +
                          `Exemple: C:\\Users\\Public\\Documents\\mon_fichier.rpy`;

        const filePath = prompt(prompt_text);

        if (!filePath) {
          return {
            success: false,
            error: 'Aucun chemin saisi'
          };
        }

        // Envoyer le chemin via l'endpoint dédié
        const pathResponse = await api.post('/file-dialog/save-path', { path: filePath });
        return {
          success: pathResponse.data.success,
          path: pathResponse.data.path
        };
      }

      return {
        success: response.data.success,
        path: response.data.path
      };
    } catch (error) {
      console.error('Save Dialog Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async getBackups(gameFilter?: string, typeFilter?: string): Promise<BackupListResponse> {
    try {
      const params = new URLSearchParams();
      if (gameFilter) params.append('game', gameFilter);
      if (typeFilter) params.append('type', typeFilter);

      const response = await api.get(`/backups?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Get Backups Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async restoreBackup(backupId: string): Promise<BackupActionResponse> {
    try {
      const response = await api.post(`/backups/${backupId}/restore`);
      return response.data;
    } catch (error) {
      console.error('Restore Backup Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async restoreBackupTo(backupId: string, targetPath: string): Promise<BackupActionResponse> {
    try {
      const response = await api.post(`/backups/${backupId}/restore-to`, {
        target_path: targetPath
      });
      return response.data;
    } catch (error) {
      console.error('Restore Backup To Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async deleteBackup(backupId: string): Promise<BackupActionResponse> {
    try {
      const response = await api.delete(`/backups/${backupId}`);
      return response.data;
    } catch (error) {
      console.error('Delete Backup Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async quitApplication(): Promise<{success: boolean, message?: string, error?: string}> {
    try {
      const response = await api.post('/quit');
      return response.data;
    } catch (error) {
      console.error('Quit Application Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
};
