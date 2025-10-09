// src/stores/extraction.ts
// Store pour gérer l'état de l'extraction des textes

import { apiService } from '$lib/api';
import { derived, get, writable } from 'svelte/store';
import { appSettings } from './app';

// Interfaces pour l'extraction
export interface ExtractionSettings {
  detect_duplicates: boolean;
  code_prefix: string;
  asterisk_prefix: string;
  tilde_prefix: string;
  empty_prefix: string;
}

export interface ExtractionResult {
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
}

export interface ExtractionState {
  // État de l'extraction
  isExtracting: boolean;
  extractionProgress: string;
  extractionTime: number;

  // Résultats de l'extraction
  lastResult: ExtractionResult | null;
  lastError: string | null;

  // Paramètres d'extraction
  settings: ExtractionSettings;

  // Statistiques
  totalExtractions: number;
  successfulExtractions: number;
  failedExtractions: number;
}

// État initial
const initialState: ExtractionState = {
  isExtracting: false,
  extractionProgress: '',
  extractionTime: 0,
  lastResult: null,
  lastError: null,
  settings: {
    detect_duplicates: true,
    code_prefix: 'RENPY_CODE_001',
    asterisk_prefix: 'RENPY_ASTERISK_001',
    tilde_prefix: 'RENPY_TILDE_001',
    empty_prefix: 'RENPY_EMPTY',
  },
  totalExtractions: 0,
  successfulExtractions: 0,
  failedExtractions: 0,
};

// Store principal
export const extractionStore = writable<ExtractionState>(initialState);

// Stores dérivés pour faciliter l'accès
export const isExtracting = derived(
  extractionStore,
  $store => $store.isExtracting
);
export const extractionProgress = derived(
  extractionStore,
  $store => $store.extractionProgress
);
export const lastExtractionResult = derived(
  extractionStore,
  $store => $store.lastResult
);
export const lastExtractionError = derived(
  extractionStore,
  $store => $store.lastError
);
export const extractionSettings = derived(
  extractionStore,
  $store => $store.settings
);
export const extractionStats = derived(extractionStore, $store => ({
  total: $store.totalExtractions,
  successful: $store.successfulExtractions,
  failed: $store.failedExtractions,
  successRate:
    $store.totalExtractions > 0
      ? ($store.successfulExtractions / $store.totalExtractions) * 100
      : 0,
}));

// Actions pour l'extraction
export const extractionActions = {
  /**
   * Charge les paramètres d'extraction depuis le backend
   */
  async loadSettings(): Promise<void> {
    try {
      const response = await apiService.getExtractionSettings();
      if (response.success && response.settings) {
        extractionStore.update(state => ({
          ...state,
          settings: response.settings || state.settings,
        }));
      }
    } catch (error) {
      console.error('Erreur chargement paramètres extraction:', error);
    }
  },

  /**
   * Met à jour les paramètres d'extraction
   */
  async updateSettings(
    newSettings: Partial<ExtractionSettings>
  ): Promise<boolean> {
    try {
      const response = await apiService.setExtractionSettings(newSettings);
      if (response.success) {
        extractionStore.update(state => ({
          ...state,
          settings: { ...state.settings, ...newSettings },
        }));
        return true;
      } else {
        console.error('Erreur mise à jour paramètres:', response.error);
        return false;
      }
    } catch (error) {
      console.error('Erreur mise à jour paramètres extraction:', error);
      return false;
    }
  },

  /**
   * Valide un fichier pour l'extraction
   */
  async validateFile(
    filepath: string
  ): Promise<{ valid: boolean; message: string }> {
    try {
      const response = await apiService.validateExtractionFile(filepath);
      if (response.success && response.validation) {
        return {
          valid: response.validation.valid,
          message: response.validation.message,
        };
      } else {
        return {
          valid: false,
          message: response.error || 'Erreur de validation',
        };
      }
    } catch (error) {
      console.error('Erreur validation fichier:', error);
      return {
        valid: false,
        message: 'Erreur de validation',
      };
    }
  },

  /**
   * Lance l'extraction des textes
   */
  async extractTexts(
    fileContent: string[],
    filepath: string,
    detectDuplicates?: boolean
  ): Promise<boolean> {
    const currentSettings = get(extractionStore);
    const useDetectDuplicates =
      detectDuplicates !== undefined
        ? detectDuplicates
        : currentSettings.settings.detect_duplicates;

    try {
      // Mettre à jour l'état de chargement
      extractionStore.update(state => ({
        ...state,
        isExtracting: true,
        extractionProgress: "Initialisation de l'extraction...",
        lastError: null,
      }));

      // ÉTAPE 1: Créer une sauvegarde de sécurité avant extraction
      extractionStore.update(state => ({
        ...state,
        extractionProgress: 'Création de la sauvegarde de sécurité...',
      }));

      const backupResult = await apiService.createBackup(
        filepath,
        'security',
        'Sauvegarde avant extraction'
      );

      if (!backupResult.success) {
        // Warning mais continue quand même (selon le flux)
        console.warn('⚠️ Sauvegarde échouée:', backupResult.error);
      } else {
        console.info('✅ Sauvegarde créée:', backupResult.backup_path);
      }

      // ÉTAPE 2: Lancer l'extraction
      extractionStore.update(state => ({
        ...state,
        extractionProgress: 'Protection des codes et variables...',
      }));

      const response = await apiService.extractTexts(
        fileContent,
        filepath,
        useDetectDuplicates
      );

      if (response.success && response.result) {
        // Succès
        extractionStore.update(state => ({
          ...state,
          isExtracting: false,
          extractionProgress: 'Extraction terminée avec succès',
          extractionTime: response.extraction_time || 0,
          lastResult: response.result || null,
          lastError: null,
          totalExtractions: state.totalExtractions + 1,
          successfulExtractions: state.successfulExtractions + 1,
        }));

        console.info('✅ Extraction réussie:', response.result);

        // Ouverture automatique des fichiers si activée
        const settings = get(appSettings);
        if (settings.autoOpenings.files) {
          await this.openExtractionFiles(response.result);
        }

        return true;
      } else {
        // Erreur
        extractionStore.update(state => ({
          ...state,
          isExtracting: false,
          extractionProgress: "Erreur lors de l'extraction",
          lastError: response.error || 'Erreur inconnue',
          totalExtractions: state.totalExtractions + 1,
          failedExtractions: state.failedExtractions + 1,
        }));

        console.error('❌ Erreur extraction:', response.error);
        return false;
      }
    } catch (error) {
      // Erreur exceptionnelle
      const errorMessage =
        error instanceof Error ? error.message : 'Erreur inconnue';

      extractionStore.update(state => ({
        ...state,
        isExtracting: false,
        extractionProgress: "Erreur lors de l'extraction",
        lastError: errorMessage,
        totalExtractions: state.totalExtractions + 1,
        failedExtractions: state.failedExtractions + 1,
      }));

      console.error('❌ Erreur exceptionnelle extraction:', error);
      return false;
    }
  },

  /**
   * Ouvre automatiquement les fichiers d'extraction
   */
  async openExtractionFiles(result: ExtractionResult): Promise<void> {
    try {
      const filesToOpen: string[] = [];

      // Ajouter les fichiers générés
      if (result.dialogue_file) {
        filesToOpen.push(result.dialogue_file);
      }
      if (result.doublons_file) {
        filesToOpen.push(result.doublons_file);
      }
      if (result.asterix_file) {
        filesToOpen.push(result.asterix_file);
      }

      // Ouvrir les fichiers
      if (filesToOpen.length > 0) {
        console.info('📂 Ouverture automatique des fichiers:', filesToOpen);

        // Utiliser l'API backend pour ouvrir les fichiers
        for (const file of filesToOpen) {
          await apiService.openExtractionFile(file);
          // Petit délai entre les ouvertures pour éviter de surcharger le système
          await new Promise(resolve => setTimeout(resolve, 150));
        }
      }
    } catch (error) {
      console.error('Erreur ouverture automatique des fichiers:', error);
    }
  },

  /**
   * Ouvre le dossier de sortie de la dernière extraction
   */
  async openOutputFolder(): Promise<void> {
    const currentState = get(extractionStore);
    if (currentState.lastResult?.output_folder) {
      try {
        const response = await apiService.openExtractionFolder(
          currentState.lastResult.output_folder
        );
        if (!response.success) {
          console.error('Erreur ouverture dossier:', response.error);
        }
      } catch (error) {
        console.error('Erreur ouverture dossier:', error);
      }
    }
  },

  /**
   * Ouvre un fichier spécifique de l'extraction
   */
  async openExtractionFile(filePath: string): Promise<void> {
    try {
      const response = await apiService.openExtractionFile(filePath);
      if (!response.success) {
        console.error('Erreur ouverture fichier:', response.error);
      }
    } catch (error) {
      console.error('Erreur ouverture fichier:', error);
    }
  },

  /**
   * Réinitialise l'état de l'extraction
   */
  reset(): void {
    extractionStore.update(state => ({
      ...state,
      isExtracting: false,
      extractionProgress: '',
      lastResult: null,
      lastError: null,
      extractionTime: 0,
    }));
  },

  /**
   * Réinitialise les statistiques
   */
  resetStats(): void {
    extractionStore.update(state => ({
      ...state,
      totalExtractions: 0,
      successfulExtractions: 0,
      failedExtractions: 0,
    }));
  },

  /**
   * Formate le temps d'extraction en texte lisible
   */
  formatExtractionTime(timeMs: number): string {
    if (timeMs < 1000) {
      return `${Math.round(timeMs)}ms`;
    } else {
      return `${(timeMs / 1000).toFixed(2)}s`;
    }
  },

  /**
   * Génère un résumé de l'extraction
   */
  getExtractionSummary(result: ExtractionResult): string {
    const parts = [];

    if (result.extracted_count > 0) {
      parts.push(`${result.extracted_count} dialogues`);
    }

    if (result.asterix_count > 0) {
      parts.push(`${result.asterix_count} astérisques`);
    }

    if (result.tilde_count > 0) {
      parts.push(`${result.tilde_count} tildes`);
    }

    if (result.empty_count > 0) {
      parts.push(`${result.empty_count} textes vides`);
    }

    if (result.duplicate_count > 0) {
      parts.push(`${result.duplicate_count} doublons`);
    }

    return parts.join(' | ');
  },
};

// Initialisation automatique des paramètres au démarrage
if (typeof window !== 'undefined') {
  setTimeout(() => {
    extractionActions.loadSettings();
  }, 100);
}
