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
  },

  // ==================== PROJECT MANAGEMENT ====================

  async validateProject(projectPath: string): Promise<{
    success: boolean;
    validation?: { valid: boolean; message: string };
    error?: string;
  }> {
    try {
      const response = await api.post('/project/validate', { project_path: projectPath });
      return response.data as {
        success: boolean;
        validation?: { valid: boolean; message: string };
        error?: string;
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Validate Project Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async findProjectRoot(subdirPath: string, maxLevels = 10): Promise<{
    success: boolean;
    root_path?: string;
    error?: string;
  }> {
    try {
      const response = await api.post('/project/find-root', {
        subdir_path: subdirPath,
        max_levels: maxLevels
      });
      return response.data as {
        success: boolean;
        root_path?: string;
        error?: string;
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Find Project Root Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async scanProjectLanguages(projectPath: string): Promise<{
    success: boolean;
    languages: Array<{ name: string; file_count: number; path: string }>;
    error?: string;
  }> {
    try {
      const response = await api.post('/project/languages', { project_path: projectPath });
      return response.data as {
        success: boolean;
        languages: Array<{ name: string; file_count: number; path: string }>;
        error?: string;
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Scan Project Languages Error:', error);
      return {
        success: false,
        languages: [],
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async scanLanguageFiles(
    projectPath: string,
    language: string,
    exclusions: string[] = []
  ): Promise<{
    success: boolean;
    files: Array<{ name: string; path: string; size: number; relative_path: string }>;
    error?: string;
  }> {
    try {
      const response = await api.post('/project/files', {
        project_path: projectPath,
        language,
        exclusions
      });
      return response.data as {
        success: boolean;
        files: Array<{ name: string; path: string; size: number; relative_path: string }>;
        error?: string;
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Scan Language Files Error:', error);
      return {
        success: false,
        files: [],
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async loadFileContent(filepath: string): Promise<{
    success: boolean;
    content?: string[];
    line_count?: number;
    filepath?: string;
    error?: string;
  }> {
    try {
      const response = await api.post('/project/load-file', { filepath });
      return response.data as {
        success: boolean;
        content?: string[];
        line_count?: number;
        filepath?: string;
        error?: string;
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Load File Content Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async getProjectSummary(projectPath: string): Promise<{
    success: boolean;
    summary?: {
      project_name: string;
      rpa_count: number;
      rpy_count: number;
      languages: Array<{ name: string; file_count: number; path: string }>;
      summary: string;
    };
    error?: string;
  }> {
    try {
      const response = await api.post('/project/summary', { project_path: projectPath });
      return response.data as {
        success: boolean;
        summary?: {
          project_name: string;
          rpa_count: number;
          rpy_count: number;
          languages: Array<{ name: string; file_count: number; path: string }>;
          summary: string;
        };
        error?: string;
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Get Project Summary Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async setCurrentProject(projectPath: string, mode: 'project' | 'single_file' = 'project'): Promise<{
    success: boolean;
    project_path?: string;
    mode?: string;
    error?: string;
  }> {
    try {
      const response = await api.post('/project/set-current', {
        project_path: projectPath,
        mode
      });
      return response.data as {
        success: boolean;
        project_path?: string;
        mode?: string;
        error?: string;
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Set Current Project Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async getProjectState(): Promise<{
    success: boolean;
    state?: {
      mode: string;
      project_path: string | null;
      language: string | null;
      current_file: string | null;
      file_content: string[];
      available_languages: Array<{ name: string; file_count: number; path: string }>;
      available_files: Array<{ name: string; path: string; size: number; relative_path: string }>;
    };
    error?: string;
  }> {
    try {
      const response = await api.get('/project/state');
      return response.data as {
        success: boolean;
        state?: {
          mode: string;
          project_path: string | null;
          language: string | null;
          current_file: string | null;
          file_content: string[];
          available_languages: Array<{ name: string; file_count: number; path: string }>;
          available_files: Array<{ name: string; path: string; size: number; relative_path: string }>;
        };
        error?: string;
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Get Project State Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  // ==================== BACKUPS ====================

  async createBackup(sourcePath: string, backupType: string = 'security', description: string = ''): Promise<{
    success: boolean;
    backup_id?: string;
    backup_path?: string;
    message?: string;
    error?: string;
  }> {
    try {
      const response = await api.post('/backups/create', {
        source_path: sourcePath,
        backup_type: backupType,
        description: description
      });
      return response.data as {
        success: boolean;
        backup_id?: string;
        backup_path?: string;
        message?: string;
        error?: string;
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Create Backup Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  // ==================== EXTRACTION ====================

  async extractTexts(fileContent: string[], filepath: string, detectDuplicates: boolean = true): Promise<{
    success: boolean;
    result?: {
      dialogue_file: string;
      doublons_file?: string;
      asterix_file?: string;
      positions_file: string;
      output_folder: string;
      extracted_count: number;
      asterix_count: number;
      tilde_count: number;
      empty_count: number;
      duplicate_count: number;
    };
    extraction_time?: number;
    error?: string;
  }> {
    try {
      const response = await api.post('/extraction/extract', {
        file_content: fileContent,
        filepath: filepath,
        detect_duplicates: detectDuplicates
      });
      return response.data as {
        success: boolean;
        result?: {
          dialogue_file: string;
          doublons_file?: string;
          asterix_file?: string;
          positions_file: string;
          output_folder: string;
          extracted_count: number;
          asterix_count: number;
          tilde_count: number;
          empty_count: number;
          duplicate_count: number;
        };
        extraction_time?: number;
        error?: string;
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Extract Texts Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async validateExtractionFile(filepath: string): Promise<{
    success: boolean;
    validation?: {
      valid: boolean;
      message: string;
      size?: number;
      filename?: string;
    };
    error?: string;
  }> {
    try {
      const response = await api.post('/extraction/validate-file', {
        filepath: filepath
      });
      return response.data as {
        success: boolean;
        validation?: {
          valid: boolean;
          message: string;
          size?: number;
          filename?: string;
        };
        error?: string;
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Validate Extraction File Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async getExtractionSettings(): Promise<{
    success: boolean;
    settings?: {
      detect_duplicates: boolean;
      code_prefix: string;
      asterisk_prefix: string;
      tilde_prefix: string;
      empty_prefix: string;
    };
    error?: string;
  }> {
    try {
      const response = await api.get('/extraction/get-settings');
      return response.data as {
        success: boolean;
        settings?: {
          detect_duplicates: boolean;
          code_prefix: string;
          asterisk_prefix: string;
          tilde_prefix: string;
          empty_prefix: string;
        };
        error?: string;
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Get Extraction Settings Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async setExtractionSettings(settings: {
    detect_duplicates?: boolean;
    code_prefix?: string;
    asterisk_prefix?: string;
    tilde_prefix?: string;
    empty_prefix?: string;
  }): Promise<{
    success: boolean;
    message?: string;
    error?: string;
  }> {
    try {
      const response = await api.post('/extraction/set-settings', settings);
      return response.data as {
        success: boolean;
        message?: string;
        error?: string;
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Set Extraction Settings Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async openExtractionFile(filepath: string): Promise<{
    success: boolean;
    message?: string;
    error?: string;
  }> {
    try {
      const response = await api.post('/extraction/open-file', {
        filepath: filepath
      });
      return response.data as {
        success: boolean;
        message?: string;
        error?: string;
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Open Extraction File Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async openExtractionFolder(folderpath: string): Promise<{
    success: boolean;
    message?: string;
    error?: string;
  }> {
    try {
      const response = await api.post('/extraction/open-folder', {
        folderpath: folderpath
      });
      return response.data as {
        success: boolean;
        message?: string;
        error?: string;
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Open Extraction Folder Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  // ==================== RECONSTRUCTION ====================

  async validateReconstructionFiles(
    filepath: string,
    extractedCount: number,
    asterixCount: number = 0,
    tildeCount: number = 0
  ): Promise<{
    success: boolean;
    validation?: {
      overall_valid: boolean;
      files_validated: Record<string, any>;
      summary: {
        total_expected: number;
        total_found: number;
        errors: string[];
      };
    };
    error?: string;
  }> {
    try {
      const response = await api.post('/reconstruction/validate', {
        filepath: filepath,
        extracted_count: extractedCount,
        asterix_count: asterixCount,
        tilde_count: tildeCount
      });
      return response.data as {
        success: boolean;
        validation?: {
          overall_valid: boolean;
          files_validated: Record<string, any>;
          summary: {
            total_expected: number;
            total_found: number;
            errors: string[];
          };
        };
        error?: string;
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Validate Reconstruction Files Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async fixTranslationErrors(filepath: string): Promise<{
    success: boolean;
    corrections?: number;
    message?: string;
    error?: string;
  }> {
    try {
      const response = await api.post('/reconstruction/fix-quotes', {
        filepath: filepath
      });
      return response.data as {
        success: boolean;
        corrections?: number;
        message?: string;
        error?: string;
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Fix Translation Errors Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async reconstructFile(
    fileContent: string[],
    filepath: string,
    saveMode: 'overwrite' | 'new_file' = 'new_file'
  ): Promise<{
    success: boolean;
    save_path?: string;
    save_mode?: string;
    reconstruction_time?: number;
    error?: string;
  }> {
    try {
      const response = await api.post('/reconstruction/reconstruct', {
        file_content: fileContent,
        filepath: filepath,
        save_mode: saveMode
      });
      return response.data as {
        success: boolean;
        save_path?: string;
        save_mode?: string;
        reconstruction_time?: number;
        error?: string;
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Reconstruct File Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  // ==================== COHÉRENCE ====================
  
  async checkCoherence(
    targetPath: string,
    returnDetails: boolean = true,
    selectionInfo?: any
  ): Promise<{ success: boolean; result?: any; error?: string; }> {
    try {
      const response = await api.post('/coherence/check', {
        target_path: targetPath,
        return_details: returnDetails,
        selection_info: selectionInfo
      });
      return response.data as { success: boolean; result?: any; error?: string; };
    } catch (error) {
      console.error('Check Coherence Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async getCoherenceOptions(): Promise<{ success: boolean; options?: any; error?: string; }> {
    try {
      const response = await api.get('/coherence/options');
      return response.data as { success: boolean; options?: any; error?: string; };
    } catch (error) {
      console.error('Get Coherence Options Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async setCoherenceOptions(options: any): Promise<{ success: boolean; message?: string; error?: string; }> {
    try {
      const response = await api.post('/coherence/options', { options });
      return response.data as { success: boolean; message?: string; error?: string; };
    } catch (error) {
      console.error('Set Coherence Options Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async openCoherenceReport(reportPath: string): Promise<{ success: boolean; message?: string; error?: string; }> {
    try {
      const response = await api.post('/coherence/open-report', { report_path: reportPath });
      return response.data as { success: boolean; message?: string; error?: string; };
    } catch (error) {
      console.error('Open Coherence Report Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async openCoherenceFolder(): Promise<{ success: boolean; message?: string; error?: string; }> {
    try {
      const response = await api.post('/coherence/open-folder');
      return response.data as { success: boolean; message?: string; error?: string; };
    } catch (error) {
      console.error('Open Coherence Folder Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
};
