import { apiService } from '$lib/api';
import { derived, get, writable } from 'svelte/store';
import { appSettings, appSettingsActions } from './app';

// Types pour le projet
export interface LanguageInfo {
  name: string;
  file_count: number;
  path: string;
}

export interface FileInfo {
  name: string;
  path: string;
  size: number;
  relative_path: string;
}

export interface ProjectSummary {
  project_name: string;
  rpa_count: number;
  rpy_count: number;
  languages: LanguageInfo[];
  summary: string;
}

export interface ProjectState {
  mode: 'project' | 'single_file';
  projectPath: string | null;
  language: string | null;
  currentFile: string | null;
  fileContent: string[];
  availableLanguages: LanguageInfo[];
  availableFiles: FileInfo[];
  projectSummary: ProjectSummary | null;
  isLoading: boolean;
  error: string | null;
}

// État initial
const initialState: ProjectState = {
  mode: 'project',
  projectPath: null,
  language: null,
  currentFile: null,
  fileContent: [],
  availableLanguages: [],
  availableFiles: [],
  projectSummary: null,
  isLoading: false,
  error: null,
};

// Store principal
export const projectStore = writable<ProjectState>(initialState);

// Stores dérivés pour un accès facile
export const currentProject = derived(
  projectStore,
  $store => $store.projectPath
);

export const currentLanguage = derived(projectStore, $store => $store.language);

export const currentFile = derived(projectStore, $store => $store.currentFile);

export const availableLanguages = derived(
  projectStore,
  $store => $store.availableLanguages
);

export const availableFiles = derived(
  projectStore,
  $store => $store.availableFiles
);

// Actions du store
export const projectActions = {
  /**
   * Valide un chemin de projet
   */
  async validateProject(
    projectPath: string
  ): Promise<{ valid: boolean; message: string }> {
    try {
      const result = await apiService.validateProject(projectPath);
      if (result.success && result.validation) {
        return result.validation;
      }
      return { valid: false, message: result.error || 'Erreur de validation' };
    } catch (error) {
      return {
        valid: false,
        message: error instanceof Error ? error.message : 'Erreur inconnue',
      };
    }
  },

  /**
   * Trouve la racine d'un projet à partir d'un sous-dossier
   */
  async findProjectRoot(subdirPath: string): Promise<string | null> {
    try {
      const result = await apiService.findProjectRoot(subdirPath);
      if (result.success && result.root_path) {
        return result.root_path;
      }
      return null;
    } catch (error) {
      console.error('Error finding project root:', error);
      return null;
    }
  },

  /**
   * Charge un projet complet
   */
  async loadProject(projectPath: string): Promise<boolean> {
    projectStore.update(state => ({ ...state, isLoading: true, error: null }));

    try {
      // 1. Valider le projet
      const validation = await this.validateProject(projectPath);
      if (!validation.valid) {
        // Essayer de trouver la racine
        const rootPath = await this.findProjectRoot(projectPath);
        if (rootPath) {
          projectPath = rootPath;
        } else {
          projectStore.update(state => ({
            ...state,
            isLoading: false,
            error: validation.message,
          }));
          return false;
        }
      }

      // 2. Définir le projet actuel
      await apiService.setCurrentProject(projectPath, 'project');

      // 3. Obtenir le résumé du projet
      const summaryResult = await apiService.getProjectSummary(projectPath);
      const summary = summaryResult.success ? summaryResult.summary : null;

      // 4. Scanner les langues
      const languagesResult =
        await apiService.scanProjectLanguages(projectPath);
      const languages = languagesResult.success
        ? languagesResult.languages
        : [];

      // 5. Mettre à jour l'état
      projectStore.update(state => ({
        ...state,
        mode: 'project',
        projectPath,
        projectSummary: summary || null,
        availableLanguages: languages,
        availableFiles: [],
        language: null,
        currentFile: null,
        fileContent: [],
        isLoading: false,
        error: null,
      }));

      // 6. Sauvegarder le dernier projet
      appSettingsActions.setSetting('lastProject', {
        path: projectPath,
        language: '',
        mode: 'project',
      });

      // 7. Mettre à jour le chemin dans les paramètres seulement si différent
      const currentSettings = get(appSettings);
      if (currentSettings.paths.editor !== projectPath) {
        appSettingsActions.setSetting('paths', {
          ...currentSettings.paths,
          editor: projectPath,
        });
      }

      // 8. Si une seule langue, la sélectionner automatiquement
      if (languages.length === 1) {
        await this.selectLanguage(languages[0].name);
      }

      return true;
    } catch (error) {
      const errorMsg =
        error instanceof Error ? error.message : 'Erreur inconnue';
      projectStore.update(state => ({
        ...state,
        isLoading: false,
        error: errorMsg,
      }));
      return false;
    }
  },

  /**
   * Sélectionne une langue et charge ses fichiers
   */
  async selectLanguage(language: string): Promise<boolean> {
    const state = get(projectStore);

    if (!state.projectPath) {
      console.error('No project loaded');
      return false;
    }

    projectStore.update(s => ({ ...s, isLoading: true }));

    try {
      // Scanner les fichiers de la langue
      const filesResult = await apiService.scanLanguageFiles(
        state.projectPath,
        language,
        []
      );

      const files = filesResult.success ? filesResult.files : [];

      // Mettre à jour l'état
      projectStore.update(s => ({
        ...s,
        language,
        availableFiles: files,
        currentFile: null,
        fileContent: [],
        isLoading: false,
      }));

      // Sauvegarder la langue sélectionnée
      const currentSettings = get(appSettings);
      if (currentSettings.lastProject) {
        appSettingsActions.setSetting('lastProject', {
          ...currentSettings.lastProject,
          language,
        });
      }

      // Si un seul fichier, le sélectionner automatiquement
      if (files.length === 1) {
        await this.selectFile(files[0].path);
      }

      return true;
    } catch (error) {
      console.error('Error selecting language:', error);
      projectStore.update(s => ({ ...s, isLoading: false }));
      return false;
    }
  },

  /**
   * Sélectionne et charge un fichier
   */
  async selectFile(filepath: string): Promise<boolean> {
    projectStore.update(s => ({ ...s, isLoading: true }));

    try {
      const result = await apiService.loadFileContent(filepath);

      if (result.success && result.content) {
        projectStore.update(s => ({
          ...s,
          currentFile: filepath,
          fileContent: result.content || [],
          isLoading: false,
          error: null,
        }));
        return true;
      } else {
        projectStore.update(s => ({
          ...s,
          isLoading: false,
          error: result.error || 'Erreur lors du chargement du fichier',
        }));
        return false;
      }
    } catch (error) {
      const errorMsg =
        error instanceof Error ? error.message : 'Erreur inconnue';
      projectStore.update(s => ({
        ...s,
        isLoading: false,
        error: errorMsg,
      }));
      return false;
    }
  },

  /**
   * Charge un fichier unique (mode single_file)
   */
  async loadSingleFile(filepath: string): Promise<boolean> {
    projectStore.update(s => ({ ...s, isLoading: true, error: null }));

    try {
      // Définir le mode single_file
      await apiService.setCurrentProject(filepath, 'single_file');

      // Charger le contenu
      const result = await apiService.loadFileContent(filepath);

      if (result.success && result.content) {
        projectStore.update(s => ({
          ...s,
          mode: 'single_file',
          projectPath: filepath,
          currentFile: filepath,
          fileContent: result.content || [],
          availableLanguages: [],
          availableFiles: [],
          language: null,
          isLoading: false,
          error: null,
        }));

        // Sauvegarder le dernier fichier unique
        appSettingsActions.setSetting('lastProject', {
          path: filepath,
          language: '',
          mode: 'single_file',
        });

        // Mettre à jour le chemin dans les paramètres seulement si différent
        const currentSettings = get(appSettings);
        if (currentSettings.paths.editor !== filepath) {
          appSettingsActions.setSetting('paths', {
            ...currentSettings.paths,
            editor: filepath,
          });
        }

        return true;
      } else {
        projectStore.update(s => ({
          ...s,
          isLoading: false,
          error: result.error || 'Erreur lors du chargement du fichier',
        }));
        return false;
      }
    } catch (error) {
      const errorMsg =
        error instanceof Error ? error.message : 'Erreur inconnue';
      projectStore.update(s => ({
        ...s,
        isLoading: false,
        error: errorMsg,
      }));
      return false;
    }
  },

  /**
   * Réinitialise l'état du projet
   */
  reset() {
    projectStore.set(initialState);
  },

  /**
   * Met à jour le contenu du fichier (pour l'édition)
   */
  updateFileContent(content: string[]) {
    projectStore.update(s => ({ ...s, fileContent: content }));
  },

  /**
   * Obtient l'état actuel du backend
   */
  async refreshState(): Promise<void> {
    try {
      const result = await apiService.getProjectState();
      if (result.success && result.state) {
        const state = result.state;
        projectStore.update(s => ({
          ...s,
          mode: state.mode || 'project',
          projectPath: state.project_path || null,
          language: state.language || null,
          currentFile: state.current_file || null,
          fileContent: state.file_content || [],
          availableLanguages: state.available_languages || [],
          availableFiles: state.available_files || [],
        }));
      }
    } catch (error) {
      console.error('Error refreshing project state:', error);
    }
  },

  /**
   * Charge automatiquement le dernier projet utilisé
   */
  async loadLastProject(): Promise<void> {
    try {
      // Attendre que les settings soient chargés
      await new Promise(resolve => setTimeout(resolve, 100));

      const settings = get(appSettings);
      const lastProject = settings.lastProject;

      if (!lastProject || !lastProject.path) {
        console.debug('No last project to load');
        return;
      }

      console.info('Loading last project:', lastProject);

      // Charger selon le mode
      if (lastProject.mode === 'single_file') {
        await this.loadSingleFile(lastProject.path);
      } else {
        const success = await this.loadProject(lastProject.path);

        // Si une langue était sélectionnée, la recharger
        if (success && lastProject.language) {
          await this.selectLanguage(lastProject.language);
        }
      }
    } catch (error) {
      console.error('Error loading last project:', error);
    }
  },
};

// Charger le projet initial au démarrage
if (typeof window !== 'undefined') {
  setTimeout(() => {
    const initialSettings = get(appSettings);
    const initialPath = initialSettings.paths.editor;
    if (initialPath && initialPath.trim() !== '') {
      console.info('Loading initial project from settings:', initialPath);
      void projectActions.loadProject(initialPath);
    } else {
      // Sinon charger le dernier projet sauvegardé
      void projectActions.loadLastProject();
    }
  }, 1000);
}
