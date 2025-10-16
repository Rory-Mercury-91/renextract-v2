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
  projectPath: string;
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
  projectPath: '',
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
   * Charge un projet complet
   */
  async loadProject(projectPath: string): Promise<boolean> {
    projectStore.update(state => ({ ...state, isLoading: true, error: null }));

    try {
      // 1. Valider le projet
      const validationResult = await apiService.validateProject(projectPath);
      if (!validationResult.success || !validationResult.validation?.valid) {
        // Essayer de trouver la racine
        const rootResult = await apiService.findProjectRoot(projectPath);
        if (rootResult.success && rootResult.root_path) {
          projectPath = rootResult.root_path;
        } else {
          projectStore.update(state => ({
            ...state,
            isLoading: false,
            error: validationResult.validation?.message || validationResult.error || 'Erreur de validation',
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
          projectPath: state.project_path || '',
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

      const success = await this.loadProject(lastProject.path);

      // Si une langue était sélectionnée, la recharger
      if (success && lastProject.language) {
        await this.selectLanguage(lastProject.language);
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
    
    // Vérifier si l'ouverture automatique du dernier projet est activée
    if (!initialSettings.autoOpenings.lastProject) {
      console.info('Auto-opening of last project is disabled');
      return;
    }
    
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
