// src/stores/reconstruction.ts
// Store pour gérer l'état de la reconstruction des fichiers traduits

import { apiService } from '$lib/api';
import { derived, get, writable } from 'svelte/store';
import { appSettings } from './app';
import { coherenceActions } from './coherence';
import { extractionStore } from './extraction';

// Interfaces pour la reconstruction
export interface ReconstructionResult {
  save_path: string;
  save_mode: string;
  reconstruction_time: number;
}

export interface FileValidation {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface ValidationResult {
  overall_valid: boolean;
  files_validated: Record<string, FileValidation>;
  summary: {
    total_expected: number;
    total_found: number;
    errors: string[];
  };
}

export interface ReconstructionState {
  // État de la reconstruction
  isReconstructing: boolean;
  reconstructionProgress: string;
  reconstructionTime: number;

  // Résultats de la reconstruction
  lastResult: ReconstructionResult | null;
  lastError: string | null;

  // Validation
  lastValidation: ValidationResult | null;

  // Statistiques
  totalReconstructions: number;
  successfulReconstructions: number;
  failedReconstructions: number;
}

// État initial
const initialState: ReconstructionState = {
  isReconstructing: false,
  reconstructionProgress: '',
  reconstructionTime: 0,
  lastResult: null,
  lastError: null,
  lastValidation: null,
  totalReconstructions: 0,
  successfulReconstructions: 0,
  failedReconstructions: 0,
};

// Store principal
export const reconstructionStore = writable<ReconstructionState>(initialState);

// Stores dérivés pour faciliter l'accès
export const isReconstructing = derived(
  reconstructionStore,
  $store => $store.isReconstructing
);
export const reconstructionProgress = derived(
  reconstructionStore,
  $store => $store.reconstructionProgress
);
export const lastReconstructionResult = derived(
  reconstructionStore,
  $store => $store.lastResult
);
export const lastReconstructionError = derived(
  reconstructionStore,
  $store => $store.lastError
);
export const lastValidation = derived(
  reconstructionStore,
  $store => $store.lastValidation
);
export const reconstructionStats = derived(reconstructionStore, $store => ({
  total: $store.totalReconstructions,
  successful: $store.successfulReconstructions,
  failed: $store.failedReconstructions,
  successRate:
    $store.totalReconstructions > 0
      ? ($store.successfulReconstructions / $store.totalReconstructions) * 100
      : 0,
}));

// Actions pour la reconstruction
export const reconstructionActions = {
  /**
   * Valide les fichiers de traduction avant reconstruction
   */
  async validateFiles(filepath: string): Promise<boolean> {
    try {
      // Récupérer les compteurs depuis l'extraction
      const extractionState = get(extractionStore);
      const lastExtractionResult = extractionState.lastResult;

      if (!lastExtractionResult) {
        console.error('Aucune extraction effectuée');
        return false;
      }

      const extractedCount = lastExtractionResult.extracted_count || 0;
      const asterixCount = lastExtractionResult.asterix_count || 0;
      const tildeCount = lastExtractionResult.tilde_count || 0;

      // Valider les fichiers
      const response = await apiService.validateReconstructionFiles(
        filepath,
        extractedCount,
        asterixCount,
        tildeCount
      );

      if (response.success && response.validation) {
        reconstructionStore.update(state => ({
          ...state,
          lastValidation: response.validation || null,
        }));

        return response.validation.overall_valid;
      } else {
        console.error('Erreur validation:', response.error);
        return false;
      }
    } catch (error) {
      console.error('Erreur validation fichiers:', error);
      return false;
    }
  },

  /**
   * Corrige automatiquement les erreurs courantes dans les fichiers de traduction
   * (ellipses DeepL, guillemets français, chevrons, pourcentages, guillemets non-échappés)
   */
  async fixTranslationErrorsInFiles(filepath: string): Promise<number> {
    try {
      const file_base = filepath.split('/').pop()?.replace('.rpy', '') || '';
      const game_name = filepath.split('/').slice(-3, -2)[0] || '';

      const translate_folder = `01_Temporary/${game_name}/${file_base}/fichiers_a_traduire`;

      const files_to_check = [
        `${translate_folder}/${file_base}_dialogue.txt`,
        `${translate_folder}/${file_base}_doublons.txt`,
        `${translate_folder}/${file_base}_asterix.txt`,
      ];

      let totalCorrections = 0;

      for (const file of files_to_check) {
        const response = await apiService.fixTranslationErrors(file);
        if (response.success && response.corrections) {
          totalCorrections += response.corrections;
        }
      }

      if (totalCorrections > 0) {
        console.info(
          `✅ ${totalCorrections} correction(s) de guillemets appliquée(s)`
        );
      }

      return totalCorrections;
    } catch (error) {
      console.error('Erreur correction guillemets:', error);
      return 0;
    }
  },

  /**
   * Lance la reconstruction du fichier
   */
  async reconstructFile(
    fileContent: string[],
    filepath: string,
    saveMode?: 'overwrite' | 'new_file'
  ): Promise<boolean> {
    try {
      // Récupérer le mode de sauvegarde depuis les paramètres si non spécifié
      const settings = get(appSettings);
      const actualSaveMode = saveMode || settings.reconstruction.saveMode;

      console.debug(`🔧 Mode de sauvegarde: ${actualSaveMode}`);

      // Mettre à jour l'état de chargement
      reconstructionStore.update(state => ({
        ...state,
        isReconstructing: true,
        reconstructionProgress: 'Initialisation de la reconstruction...',
        lastError: null,
      }));

      // ÉTAPE 1: Corriger automatiquement les erreurs courantes (5 types)
      reconstructionStore.update(state => ({
        ...state,
        reconstructionProgress:
          'Correction automatique des erreurs courantes...',
      }));

      await this.fixTranslationErrorsInFiles(filepath);

      // ÉTAPE 2: Valider les fichiers
      reconstructionStore.update(state => ({
        ...state,
        reconstructionProgress: 'Validation des fichiers de traduction...',
      }));

      const isValid = await this.validateFiles(filepath);

      if (!isValid) {
        const validation = get(reconstructionStore).lastValidation;
        const errors = validation?.summary.errors || [
          'Fichiers de traduction invalides',
        ];

        console.warn('⚠️ Validation échouée:', errors);
        // Continuer quand même (selon le flux)
      }

      // ÉTAPE 3: Lancer la reconstruction
      reconstructionStore.update(state => ({
        ...state,
        reconstructionProgress: 'Reconstruction du fichier traduit...',
      }));

      const response = await apiService.reconstructFile(
        fileContent,
        filepath,
        actualSaveMode
      );

      if (response.success && response.save_path) {
        // Succès
        reconstructionStore.update(state => ({
          ...state,
          isReconstructing: false,
          reconstructionProgress: 'Reconstruction terminée avec succès',
          reconstructionTime: response.reconstruction_time || 0,
          lastResult: {
            save_path: response.save_path || '',
            save_mode: response.save_mode || saveMode || '',
            reconstruction_time: response.reconstruction_time || 0,
          },
          lastError: null,
          totalReconstructions: state.totalReconstructions + 1,
          successfulReconstructions: state.successfulReconstructions + 1,
        }));

        console.info('✅ Reconstruction réussie:', response.save_path);

        // Ouverture automatique du fichier reconstruit si activée
        const settings = get(appSettings);
        if (settings.autoOpenings.files) {
          await this.openReconstructedFile();
        }

        // Lancer automatiquement la vérification de cohérence après reconstruction
        console.info(
          '🔍 Lancement de la vérification de cohérence automatique...'
        );
        if (response.save_path) {
          await coherenceActions.quickCheckFile(response.save_path);
        }

        return true;
      } else {
        // Erreur
        reconstructionStore.update(state => ({
          ...state,
          isReconstructing: false,
          reconstructionProgress: 'Erreur lors de la reconstruction',
          lastError: response.error || 'Erreur inconnue',
          totalReconstructions: state.totalReconstructions + 1,
          failedReconstructions: state.failedReconstructions + 1,
        }));

        console.error('❌ Erreur reconstruction:', response.error);
        return false;
      }
    } catch (error) {
      // Erreur exceptionnelle
      const errorMessage =
        error instanceof Error ? error.message : 'Erreur inconnue';

      reconstructionStore.update(state => ({
        ...state,
        isReconstructing: false,
        reconstructionProgress: 'Erreur lors de la reconstruction',
        lastError: errorMessage,
        totalReconstructions: state.totalReconstructions + 1,
        failedReconstructions: state.failedReconstructions + 1,
      }));

      console.error('❌ Erreur exceptionnelle reconstruction:', error);
      return false;
    }
  },

  /**
   * Ouvre le fichier reconstruit
   */
  async openReconstructedFile(): Promise<void> {
    const currentState = get(reconstructionStore);
    if (currentState.lastResult?.save_path) {
      try {
        const response = await apiService.openExtractionFile(
          currentState.lastResult.save_path
        );
        if (!response.success) {
          console.error('Erreur ouverture fichier:', response.error);
        }
      } catch (error) {
        console.error('Erreur ouverture fichier:', error);
      }
    }
  },

  /**
   * Réinitialise l'état de la reconstruction
   */
  reset(): void {
    reconstructionStore.update(state => ({
      ...state,
      isReconstructing: false,
      reconstructionProgress: '',
      lastResult: null,
      lastError: null,
      lastValidation: null,
      reconstructionTime: 0,
    }));
  },

  /**
   * Réinitialise les statistiques
   */
  resetStats(): void {
    reconstructionStore.update(state => ({
      ...state,
      totalReconstructions: 0,
      successfulReconstructions: 0,
      failedReconstructions: 0,
    }));
  },

  /**
   * Formate le temps de reconstruction en texte lisible
   */
  formatReconstructionTime(timeMs: number): string {
    if (timeMs < 1000) {
      return `${Math.round(timeMs)}ms`;
    } else {
      return `${(timeMs / 1000).toFixed(2)}s`;
    }
  },
};
