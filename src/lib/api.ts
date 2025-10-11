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

// Interfaces pour la validation de reconstruction
export interface FileValidation {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface ValidationSummary {
  total_expected: number;
  total_found: number;
  errors: string[];
}

export interface ReconstructionValidation {
  overall_valid: boolean;
  files_validated: Record<string, FileValidation>;
  summary: ValidationSummary;
}

// Interfaces pour la cohérence

// Nouveau type pour l'interface Svelte
export interface CoherenceResultSvelte {
  stats: {
    total_issues: number;
    files_analyzed: number;
    issues_by_type: Record<string, number>;
  };
  issues_by_file: Record<string, Array<{
    type: string;
    line_number: number;
    message: string;
    old_content?: string;
    new_content?: string;
    file: string;
  }>>;
  target_path: string;
}

export interface CoherenceOptions {
  check_variables: boolean;
  check_tags: boolean;
  check_untranslated: boolean;
  check_ellipsis: boolean;
  check_escape_sequences: boolean;
  check_percentages: boolean;
  check_quotations: boolean;
  check_parentheses: boolean;
  check_syntax: boolean;
  check_deepl_ellipsis: boolean;
  check_isolated_percent: boolean;
  check_french_quotes: boolean;
  check_line_structure: boolean;
  custom_exclusions: string[];
}

// SelectionInfo supprimé car plus utilisé

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
      
      // Vérifier si c'est le mode WSL
      if (!response.data.success && response.data.wsl_mode) {
        return await this.handleWslDialog(params, response.data, options);
      }
      
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
      const anyErr = error as unknown as { response?: { data?: { error?: string, wsl_mode?: boolean } } };
      const isWslMode = anyErr?.response?.data?.wsl_mode || anyErr?.response?.data?.error === 'WSL_MODE';
      if (isWslMode && !params.path && anyErr.response?.data) {
        return await this.handleWslDialog(params, { 
          message: anyErr.response.data.error,
          suggested_path: undefined 
        }, options);
      }
       
      console.error('Open Dialog Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async handleWslDialog(
    params: {
      dialog_type: 'file' | 'folder' | 'save';
      title?: string;
      initialdir?: string;
      filetypes?: [string, string][];
    },
    wslData: { message?: string; suggested_path?: string },
    options?: { setPath?: (path: string) => void }
  ): Promise<{success: boolean, path?: string, error?: string}> {
    // Créer un message d'aide plus détaillé
    const filetypesStr = (params.filetypes || [])
      .map(([desc, ext]) => `${desc} (${ext})`).join(' | ') || 'Tous les fichiers (*.*)';
    
    const title = params.title || (params.dialog_type === 'folder' ? 'Sélectionner un dossier' : 'Sélectionner un fichier');
    const suggestedPath = wslData.suggested_path || params.initialdir || '';
    
    let promptText = `🌐 Mode WSL détecté\n\n`;
    promptText += `Titre: ${title}\n`;
    promptText += `Type: ${params.dialog_type === 'folder' ? 'Dossier' : 'Fichier'}\n`;
    
    if (params.dialog_type === 'file') {
      promptText += `Types acceptés: ${filetypesStr}\n`;
    }
    
    if (suggestedPath) {
      promptText += `Dossier suggéré: ${suggestedPath}\n`;
    }
    
    promptText += `\n💡 Solutions recommandées:\n`;
    promptText += `1. Installer zenity: sudo apt install zenity\n`;
    promptText += `2. Ou saisir le chemin manuellement ci-dessous\n\n`;
    
    if (params.dialog_type === 'folder') {
      promptText += `Veuillez saisir le chemin complet du dossier:\n`;
      promptText += `Exemple: /mnt/c/Users/Public/Documents`;
    } else {
      promptText += `Veuillez saisir le chemin complet du fichier:\n`;
      promptText += `Exemple: /mnt/c/Users/Public/Documents/mon_fichier.rpy`;
    }
    
    const userPath = window.prompt(promptText);
    if (!userPath) {
      return { success: false, error: 'Aucun chemin saisi' };
    }
    
    // Valider le chemin si une fonction de validation est fournie
    if ('validate' in params && params.validate && !(params.validate as (path: string) => boolean)(userPath)) {
      return { success: false, error: 'Chemin invalide' };
    }
    
    // Retourner le chemin directement (pas besoin de le renvoyer au backend)
    const result = {
      success: true,
      path: userPath
    };
    
    if (result.success && result.path && options?.setPath) {
      options.setPath(result.path);
    }
    
    return result;
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
       
      console.error('Save Dialog Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async checkZenity(): Promise<{success: boolean, available: boolean, version?: string, message: string}> {
    try {
      const response = await api.get('/system/check-zenity');
      return response.data;
    } catch (error) {
      console.error('Check Zenity Error:', error);
      return {
        success: false,
        available: false,
        message: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async getWslInfo(): Promise<{success: boolean, info?: any, error?: string}> {
    try {
      const response = await api.get('/system/wsl-info');
      return response.data;
    } catch (error) {
      console.error('WSL Info Error:', error);
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

      const response = await api.get(`/backup/list?${params.toString()}`);
      return response.data as BackupListResponse;
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
      return response.data as BackupActionResponse;
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
      return response.data as BackupActionResponse;
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
      return response.data as BackupActionResponse;
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
      return response.data as {success: boolean, message?: string, error?: string};
    } catch (error) {
       
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
        file_type: 'languages',
        language,
        exclusions
      });
      return response.data as {
        success: boolean;
        files: Array<{ name: string; path: string; size: number; relative_path: string }>;
        error?: string;
      };
    } catch (error) {
       
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
      mode: 'project' | 'single_file';
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
          mode: 'project' | 'single_file';
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
       
      console.error('Set Extraction Settings Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async openExtractionFile(filepath: string, lineNumber?: number): Promise<{
    success: boolean;
    message?: string;
    error?: string;
  }> {
    try {
      const payload: { filepath: string; line_number?: number } = {
        filepath: filepath
      };
      
      if (lineNumber !== undefined) {
        payload.line_number = lineNumber;
      }
      
      const response = await api.post('/extraction/open-file', payload);
      return response.data as {
        success: boolean;
        message?: string;
        error?: string;
      };
    } catch (error) {
      console.error('Open Extraction File Error:', error);
      
      // Gestion d'erreur améliorée
      let errorMessage = 'Unknown error';
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (typeof error === 'object' && error !== null) {
        // Essayer d'extraire le message d'erreur de la réponse
        const anyError = error as any;
        if (anyError.response?.data?.error) {
          errorMessage = anyError.response.data.error;
        } else if (anyError.response?.statusText) {
          errorMessage = `HTTP ${anyError.response.status}: ${anyError.response.statusText}`;
        } else if (anyError.message) {
          errorMessage = anyError.message;
        }
      }
      
      return {
        success: false,
        error: errorMessage
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
    validation?: ReconstructionValidation; 
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
        validation?: ReconstructionValidation;
        error?: string;
      };
    } catch (error) {
       
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
       
      console.error('Reconstruct File Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  // ==================== COHÉRENCE ====================

  async checkCoherenceSvelte(
    targetPath: string
  ): Promise<{ 
    success: boolean; 
    result?: CoherenceResultSvelte; 
    error?: string; 
  }> {
    try {
      const response = await api.post('/coherence/check-svelte', {
        target_path: targetPath
      });
      return response.data as { 
        success: boolean; 
        result?: CoherenceResultSvelte; 
        error?: string; 
      };
    } catch (error) {
      console.error('Check Coherence Svelte Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async getCoherenceOptions(): Promise<{ success: boolean; options?: CoherenceOptions; error?: string; }> {
    try {
      const response = await api.get('/coherence/options');
      return response.data as { success: boolean; options?: CoherenceOptions; error?: string; };
    } catch (error) {
      console.error('Get Coherence Options Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  },

  async setCoherenceOptions(options: Partial<CoherenceOptions>): Promise<{ success: boolean; message?: string; error?: string; }> {
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
