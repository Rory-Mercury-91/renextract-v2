/* eslint-env browser */
import axios from 'axios';

// Configuration de base d'axios
const api = axios.create({
  baseURL: "/api",
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
  backups?: Record<string, unknown>[];
  error?: string;
}

export interface BackupActionResponse {
  success: boolean;
  message?: string;
  error?: string;
}

export type SettingsData = Record<string, unknown>;

// Service API
export const apiService = {
  async openDialog(
    params: {
      path?: string;
      dialog_type: 'file' | 'folder' | 'save';
      title?: string;
      initialdir?: string;
      filetypes?: [string, string][];
      initialfile?: string;
      defaultextension?: string;
      must_exist?: boolean;
      validate?: (path: string) => boolean;
    },
    options?: { setPath?: (path: string) => void }
  ): Promise<{success: boolean, path?: string, error?: string}> {
    try {
      const response = await api.post('/file-dialog/open', params, { timeout: 60000 });
      const result = {
        success: Boolean(response.data.success),
        path: response.data.path as string | undefined
      } as { success: boolean, path?: string };
      if (result.success && result.path && options?.setPath) {
        options.setPath(result.path);
      }
      return result;
    } catch (error) {
      // Si le backend renvoie 400 avec WSL_MODE, gérer le fallback utilisateur
      const anyErr = error as unknown as { response?: { data?: { error?: string } } };
      const isWslMode = anyErr?.response?.data?.error === 'WSL_MODE';
      if (isWslMode && !params.path) {
        const promptText = params.dialog_type === 'folder'
          ? "En mode WSL, le dialogue natif n'est pas disponible.\n\nVeuillez saisir le chemin complet du dossier :\nExemple: C:\\Users\\Public\\Documents"
          : "En mode WSL, le dialogue natif n'est pas disponible.\n\nVeuillez saisir le chemin complet du fichier :\nExemple: C:\\Program Files\\Software\\file.exe";
        const userPath = window.prompt(promptText);
        if (!userPath) {
          return { success: false, error: 'Aucun chemin saisi' };
        }
        const postResp = await api.post('/file-dialog/open', { ...params, path: userPath });
        const result = {
          success: Boolean(postResp.data.success),
          path: postResp.data.path as string | undefined
        } as { success: boolean, path?: string };
        if (result.success && result.path && options?.setPath) {
          options.setPath(result.path);
        }
        return result;
      }
      // eslint-disable-next-line no-console
      console.error('Open Dialog Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },
  async healthCheck(): Promise<HealthResponse> {
    const response = await api.get('/health');
    return response.data as HealthResponse;
  },

  async updateSettings(settings: SettingsData): Promise<SettingsUpdateResponse> {
    const response = await api.post('/settings', settings);
    return response.data as SettingsUpdateResponse;
  },

  async getSettings(): Promise<SettingsData> {
    const response = await api.get('/settings');
    return response.data as SettingsData;
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
        const filetypesStr = (params.filetypes || [])
          .map(([desc, ext]) => `${desc} (${ext})`).join(' | ') || 'Tous les fichiers (*.*)';
        const promptText = `En mode WSL, le dialogue de sauvegarde n'est pas disponible.\n\n` +
                          `Titre: ${params.title || 'Enregistrer sous...'}\n` +
                          `Fichier initial: ${params.initialfile || ''}\n` +
                          `Extension par défaut: ${params.defaultextension || ''}\n` +
                          `Types de fichiers: ${filetypesStr}\n\n` +
                          `Veuillez saisir le chemin complet du fichier de destination :\n` +
                          `Exemple: C:\\Users\\Public\\Documents\\mon_fichier.rpy`;

        const filePath = window.prompt(promptText);

        if (!filePath) {
          return {
            success: false,
            error: 'Aucun chemin saisi'
          };
        }

        // Envoyer le chemin via l'endpoint dédié
        const pathResponse = await api.post('/file-dialog/save-path', { path: filePath });
        return {
          success: Boolean(pathResponse.data.success),
          path: pathResponse.data.path as string | undefined
        };
      }

      return {
        success: Boolean(response.data.success),
        path: response.data.path as string | undefined
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Save Dialog Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async getBackups(gameFilter?: string, typeFilter?: string): Promise<BackupListResponse> {
    try {
      const params = new window.URLSearchParams();
      if (gameFilter) params.append('game', gameFilter);
      if (typeFilter) params.append('type', typeFilter);

      const response = await api.get(`/backups?${params.toString()}`);
      return response.data as BackupListResponse;
    } catch (error) {
      // eslint-disable-next-line no-console
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
      return response.data as BackupActionResponse;
    } catch (error) {
      // eslint-disable-next-line no-console
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
      return response.data as BackupActionResponse;
    } catch (error) {
      // eslint-disable-next-line no-console
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
      return response.data as BackupActionResponse;
    } catch (error) {
      // eslint-disable-next-line no-console
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
      return response.data as {success: boolean, message?: string, error?: string};
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Quit Application Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
};
