// src/stores/coherence.ts
// Store pour gérer l'état de la vérification de cohérence

import { apiService, type CoherenceResultSvelte } from '$lib/api';
import { derived, writable } from 'svelte/store';

// Interfaces pour la cohérence (utilise celles de l'API)
export type CoherenceIssue = CoherenceResultSvelte['issues_by_file'][string][0];
export type CoherenceStats = CoherenceResultSvelte['stats'];

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

// État initial
const initialCoherenceState = {
  // État de vérification
  isChecking: false,
  checkProgress: '',

  // Options de vérification
  options: {
    check_variables: true,
    check_tags: true,
    check_untranslated: true,
    check_ellipsis: true,
    check_escape_sequences: true,
    check_percentages: true,
    check_quotations: true,
    check_parentheses: true,
    check_syntax: true,
    check_deepl_ellipsis: true,
    check_isolated_percent: true,
    check_french_quotes: true,
    check_line_structure: true,
    custom_exclusions: ['OK', 'Menu', 'Continue', 'Yes', 'No'],
  } as CoherenceOptions,

  // Résultats
  lastResult: null as CoherenceResultSvelte | null,
  lastError: null as string | null,

  // Statistiques
  totalChecks: 0,
  successfulChecks: 0,
  failedChecks: 0,

  // Fichier en cours de vérification
  currentTarget: null as string | null,
  // selectionInfo supprimé car plus utilisé
};

// Store principal
export const coherenceStore = writable(initialCoherenceState);

// Stores dérivés
export const isChecking = derived(coherenceStore, $state => $state.isChecking);
export const checkProgress = derived(
  coherenceStore,
  $state => $state.checkProgress
);
export const coherenceOptions = derived(
  coherenceStore,
  $state => $state.options
);
export const lastCoherenceResult = derived(
  coherenceStore,
  $state => $state.lastResult
);
export const lastCoherenceError = derived(
  coherenceStore,
  $state => $state.lastError
);
export const currentCoherenceTarget = derived(
  coherenceStore,
  $state => $state.currentTarget
);

// Actions de cohérence
export const coherenceActions = {
  /**
   * Charge les options de cohérence depuis le backend
   */
  async loadOptions(): Promise<void> {
    try {
      const response = await apiService.getCoherenceOptions();
      if (response.success && response.options) {
        coherenceStore.update(state => ({
          ...state,
          options: { ...state.options, ...response.options },
        }));
        console.info('✅ Options de cohérence chargées');
      }
    } catch (error) {
      console.error('Erreur chargement options cohérence:', error);
    }
  },

  /**
   * Sauvegarde les options de cohérence
   */
  async saveOptions(options: Partial<CoherenceOptions>): Promise<boolean> {
    try {
      coherenceStore.update(state => ({
        ...state,
        options: { ...state.options, ...options },
      }));

      const response = await apiService.setCoherenceOptions(options);
      if (response.success) {
        console.info('✅ Options de cohérence sauvegardées');
        return true;
      } else {
        console.error('❌ Erreur sauvegarde options:', response.error);
        return false;
      }
    } catch (error) {
      console.error('Erreur sauvegarde options cohérence:', error);
      return false;
    }
  },

  /**
   * Vérifie la cohérence d'un fichier ou dossier (bouton Revérifier)
   */
  async quickCheckFile(filePath: string): Promise<boolean> {
    if (!filePath || !filePath.trim()) {
      console.error(
        '❌ Chemin de fichier manquant pour la vérification rapide'
      );
      return false;
    }

    try {
      // Mettre à jour l'état de chargement
      coherenceStore.update(state => ({
        ...state,
        isChecking: true,
        checkProgress: 'Vérification rapide en cours...',
        currentTarget: filePath,
        lastError: null,
      }));

      console.debug(`🔍 Vérification rapide: ${filePath}`);

      // Lancer la vérification avec le nouveau système Svelte
      const response = await apiService.checkCoherenceSvelte(filePath);

      if (response.success && response.result) {
        // Succès
        coherenceStore.update(state => ({
          ...state,
          isChecking: false,
          checkProgress: 'Vérification terminée',
          lastResult: response.result || null, // Utilise maintenant le nouveau format Svelte
          lastError: null,
          totalChecks: state.totalChecks + 1,
          successfulChecks: state.successfulChecks + 1,
        }));

        console.info('✅ Vérification rapide réussie');

        // Afficher une notification selon le résultat
        const stats = response.result.stats;
        const totalIssues = stats.total_issues;

        if (totalIssues === 0) {
          console.info('✅ Aucun problème détecté');
        } else {
          const distinctTypes = Object.values(stats.issues_by_type).filter(
            count => typeof count === 'number' && count > 0
          ).length;
          console.warn(
            `⚠️ ${totalIssues} erreur(s) détectée(s) sur ${distinctTypes} type(s)`
          );
        }

        return true;
      } else {
        // Erreur
        coherenceStore.update(state => ({
          ...state,
          isChecking: false,
          checkProgress: 'Erreur lors de la vérification',
          lastError: response.error || 'Erreur inconnue',
          totalChecks: state.totalChecks + 1,
          failedChecks: state.failedChecks + 1,
        }));

        console.error('❌ Erreur vérification rapide:', response.error);
        return false;
      }
    } catch (error) {
      // Erreur exceptionnelle
      const errorMessage =
        error instanceof Error ? error.message : 'Erreur inconnue';
      coherenceStore.update(state => ({
        ...state,
        isChecking: false,
        checkProgress: 'Erreur exceptionnelle',
        lastError: errorMessage,
        totalChecks: state.totalChecks + 1,
        failedChecks: state.failedChecks + 1,
      }));

      console.error('❌ Erreur exceptionnelle vérification:', error);
      return false;
    }
  },

  /**
   * Lance une analyse complète de cohérence (onglet Cohérence)
   */
  async analyzeCoherence(targetPath: string): Promise<boolean> {
    if (!targetPath || !targetPath.trim()) {
      console.error("❌ Chemin cible manquant pour l'analyse");
      return false;
    }

    try {
      // Mettre à jour l'état de chargement
      coherenceStore.update(state => ({
        ...state,
        isChecking: true,
        checkProgress: 'Analyse de cohérence en cours...',
        currentTarget: targetPath,
        lastError: null,
      }));

      console.debug(`🔍 Analyse cohérence: ${targetPath}`);

      // Lancer l'analyse avec la nouvelle API Svelte
      const response = await apiService.checkCoherenceSvelte(targetPath);

      if (response.success && response.result) {
        // Succès
        coherenceStore.update(state => ({
          ...state,
          isChecking: false,
          checkProgress: 'Analyse terminée',
          lastResult: response.result || null,
          lastError: null,
          totalChecks: state.totalChecks + 1,
          successfulChecks: state.successfulChecks + 1,
        }));

        console.info('✅ Analyse de cohérence réussie');

        // Afficher le résumé
        const stats = response.result.stats;
        const totalIssues = stats.total_issues;
        const filesAnalyzed = stats.files_analyzed;

        if (totalIssues === 0) {
          console.info(
            `✅ Analyse terminée - ${filesAnalyzed} fichier(s), aucun problème détecté`
          );
        } else {
          const distinctTypes = Object.values(stats.issues_by_type).filter(
            count => typeof count === 'number' && count > 0
          ).length;
          console.warn(
            `⚠️ Analyse terminée - ${filesAnalyzed} fichier(s), ${totalIssues} problème(s), ${distinctTypes} type(s)`
          );
        }

        return true;
      } else {
        // Erreur
        coherenceStore.update(state => ({
          ...state,
          isChecking: false,
          checkProgress: "Erreur lors de l'analyse",
          lastError: response.error || 'Erreur inconnue',
          totalChecks: state.totalChecks + 1,
          failedChecks: state.failedChecks + 1,
        }));

        console.error('❌ Erreur analyse cohérence:', response.error);
        return false;
      }
    } catch (error) {
      // Erreur exceptionnelle
      const errorMessage =
        error instanceof Error ? error.message : 'Erreur inconnue';
      coherenceStore.update(state => ({
        ...state,
        isChecking: false,
        checkProgress: 'Erreur exceptionnelle',
        lastError: errorMessage,
        totalChecks: state.totalChecks + 1,
        failedChecks: state.failedChecks + 1,
      }));

      console.error('❌ Erreur exceptionnelle analyse:', error);
      return false;
    }
  },

  // Les fonctions openDetailedReport et openReportsFolder ont été supprimées
  // car le nouveau système Svelte affiche les résultats directement dans l'interface

  /**
   * Réinitialise l'état de cohérence
   */
  resetState(): void {
    coherenceStore.update(state => ({
      ...state,
      isChecking: false,
      checkProgress: '',
      lastResult: null,
      lastError: null,
      currentTarget: null,
      selectionInfo: null,
    }));
  },

  /**
   * Met à jour une option spécifique
   */
  updateOption<K extends keyof CoherenceOptions>(
    key: K,
    value: CoherenceOptions[K]
  ): void {
    coherenceStore.update(state => ({
      ...state,
      options: {
        ...state.options,
        [key]: value,
      },
    }));
  },

  /**
   * Sélectionne/désélectionne toutes les options
   */
  toggleAllOptions(enabled: boolean): void {
    coherenceStore.update(state => ({
      ...state,
      options: {
        ...state.options,
        check_variables: enabled,
        check_tags: enabled,
        check_untranslated: enabled,
        check_ellipsis: enabled,
        check_escape_sequences: enabled,
        check_percentages: enabled,
        check_quotations: enabled,
        check_parentheses: enabled,
        check_syntax: enabled,
        check_deepl_ellipsis: enabled,
        check_isolated_percent: enabled,
        check_french_quotes: enabled,
        check_line_structure: enabled,
      },
    }));
  },
};
