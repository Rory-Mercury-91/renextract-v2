// src/stores/coherence.ts
// Store pour gérer l'état de la vérification de cohérence

import { apiService } from '$lib/api';
import { derived, get, writable } from 'svelte/store';
import { appSettings } from './app';

// Interfaces pour la cohérence
export interface CoherenceIssue {
  file: string;
  line_number: number;
  type: string;
  severity: 'error' | 'warning' | 'info';
  message: string;
  old_line: string;
  new_line: string;
}

export interface CoherenceStats {
  files_analyzed: number;
  total_issues: number;
  issues_by_type: Record<string, number>;
  issues_by_severity: Record<string, number>;
}

export interface CoherenceResult {
  rapport_path: string;
  stats: CoherenceStats;
  issues: CoherenceIssue[];
  analysis_time: number;
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
    custom_exclusions: ['OK', 'Menu', 'Continue', 'Yes', 'No']
  } as CoherenceOptions,
  
  // Résultats
  lastResult: null as CoherenceResult | null,
  lastError: null as string | null,
  
  // Statistiques
  totalChecks: 0,
  successfulChecks: 0,
  failedChecks: 0,
  
  // Fichier en cours de vérification
  currentTarget: null as string | null,
  selectionInfo: null as any
};

// Store principal
export const coherenceStore = writable(initialCoherenceState);

// Stores dérivés
export const isChecking = derived(coherenceStore, $state => $state.isChecking);
export const checkProgress = derived(coherenceStore, $state => $state.checkProgress);
export const coherenceOptions = derived(coherenceStore, $state => $state.options);
export const lastCoherenceResult = derived(coherenceStore, $state => $state.lastResult);
export const lastCoherenceError = derived(coherenceStore, $state => $state.lastError);
export const currentCoherenceTarget = derived(coherenceStore, $state => $state.currentTarget);

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
          options: { ...state.options, ...response.options }
        }));
        console.log('✅ Options de cohérence chargées');
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
        options: { ...state.options, ...options }
      }));

      const response = await apiService.setCoherenceOptions(options);
      if (response.success) {
        console.log('✅ Options de cohérence sauvegardées');
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
      console.error('❌ Chemin de fichier manquant pour la vérification rapide');
      return false;
    }

    try {
      // Mettre à jour l'état de chargement
      coherenceStore.update(state => ({
        ...state,
        isChecking: true,
        checkProgress: 'Vérification rapide en cours...',
        currentTarget: filePath,
        lastError: null
      }));

      console.log(`🔍 Vérification rapide: ${filePath}`);

      // Lancer la vérification
      const response = await apiService.checkCoherence(filePath, true);

      if (response.success && response.result) {
        // Succès
        coherenceStore.update(state => ({
          ...state,
          isChecking: false,
          checkProgress: 'Vérification terminée',
          lastResult: response.result,
          lastError: null,
          totalChecks: state.totalChecks + 1,
          successfulChecks: state.successfulChecks + 1
        }));

        console.log('✅ Vérification rapide réussie');
        
        // Afficher une notification selon le résultat
        const stats = response.result.stats;
        const totalIssues = stats.total_issues;
        
        if (totalIssues === 0) {
          console.log('✅ Aucun problème détecté');
        } else {
          const distinctTypes = Object.values(stats.issues_by_type).filter(count => count > 0).length;
          console.log(`⚠️ ${totalIssues} erreur(s) détectée(s) sur ${distinctTypes} type(s)`);
        }
        
        // Ouverture automatique du rapport si activée
        const settings = get(appSettings);
        if (settings.autoOpenings.reports && response.result.rapport_path) {
          console.log('📄 Ouverture automatique du rapport de cohérence...');
          await apiService.openCoherenceReport(response.result.rapport_path);
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
          failedChecks: state.failedChecks + 1
        }));

        console.error('❌ Erreur vérification rapide:', response.error);
        return false;
      }
    } catch (error) {
      // Erreur exceptionnelle
      const errorMessage = error instanceof Error ? error.message : 'Erreur inconnue';
      coherenceStore.update(state => ({
        ...state,
        isChecking: false,
        checkProgress: 'Erreur exceptionnelle',
        lastError: errorMessage,
        totalChecks: state.totalChecks + 1,
        failedChecks: state.failedChecks + 1
      }));

      console.error('❌ Erreur exceptionnelle vérification:', error);
      return false;
    }
  },

  /**
   * Lance une analyse complète de cohérence (onglet Cohérence)
   */
  async analyzeCoherence(targetPath: string, selectionInfo?: any): Promise<boolean> {
    if (!targetPath || !targetPath.trim()) {
      console.error('❌ Chemin cible manquant pour l\'analyse');
      return false;
    }

    try {
      // Mettre à jour l'état de chargement
      coherenceStore.update(state => ({
        ...state,
        isChecking: true,
        checkProgress: 'Analyse de cohérence en cours...',
        currentTarget: targetPath,
        selectionInfo,
        lastError: null
      }));

      console.log(`🔍 Analyse cohérence: ${targetPath}`);

      // Lancer l'analyse
      const response = await apiService.checkCoherence(targetPath, true, selectionInfo);

      if (response.success && response.result) {
        // Succès
        coherenceStore.update(state => ({
          ...state,
          isChecking: false,
          checkProgress: 'Analyse terminée',
          lastResult: response.result,
          lastError: null,
          totalChecks: state.totalChecks + 1,
          successfulChecks: state.successfulChecks + 1
        }));

        console.log('✅ Analyse de cohérence réussie');
        
        // Afficher le résumé
        const stats = response.result.stats;
        const totalIssues = stats.total_issues;
        const filesAnalyzed = stats.files_analyzed;
        
        if (totalIssues === 0) {
          console.log(`✅ Analyse terminée - ${filesAnalyzed} fichier(s), aucun problème détecté`);
        } else {
          const distinctTypes = Object.values(stats.issues_by_type).filter(count => count > 0).length;
          console.log(`⚠️ Analyse terminée - ${filesAnalyzed} fichier(s), ${totalIssues} problème(s), ${distinctTypes} type(s)`);
        }
        
        // Ouverture automatique du rapport si activée
        const settings = get(appSettings);
        if (settings.autoOpenings.reports && response.result.rapport_path) {
          console.log('📄 Ouverture automatique du rapport de cohérence...');
          await apiService.openCoherenceReport(response.result.rapport_path);
        }
        
        return true;
      } else {
        // Erreur
        coherenceStore.update(state => ({
          ...state,
          isChecking: false,
          checkProgress: 'Erreur lors de l\'analyse',
          lastError: response.error || 'Erreur inconnue',
          totalChecks: state.totalChecks + 1,
          failedChecks: state.failedChecks + 1
        }));

        console.error('❌ Erreur analyse cohérence:', response.error);
        return false;
      }
    } catch (error) {
      // Erreur exceptionnelle
      const errorMessage = error instanceof Error ? error.message : 'Erreur inconnue';
      coherenceStore.update(state => ({
        ...state,
        isChecking: false,
        checkProgress: 'Erreur exceptionnelle',
        lastError: errorMessage,
        totalChecks: state.totalChecks + 1,
        failedChecks: state.failedChecks + 1
      }));

      console.error('❌ Erreur exceptionnelle analyse:', error);
      return false;
    }
  },

  /**
   * Ouvre le rapport détaillé de cohérence
   */
  async openDetailedReport(): Promise<void> {
    const currentState = get(coherenceStore);
    if (currentState.lastResult?.rapport_path) {
      try {
        const response = await apiService.openCoherenceReport(currentState.lastResult.rapport_path);
        if (response.success) {
          console.log('✅ Rapport détaillé ouvert');
        } else {
          console.error('❌ Erreur ouverture rapport:', response.error);
        }
      } catch (error) {
        console.error('Erreur ouverture rapport:', error);
      }
    }
  },

  /**
   * Ouvre le dossier des rapports
   */
  async openReportsFolder(): Promise<void> {
    try {
      const response = await apiService.openCoherenceFolder();
      if (response.success) {
        console.log('✅ Dossier des rapports ouvert');
      } else {
        console.error('❌ Erreur ouverture dossier:', response.error);
      }
    } catch (error) {
      console.error('Erreur ouverture dossier rapports:', error);
    }
  },

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
      selectionInfo: null
    }));
  },

  /**
   * Met à jour une option spécifique
   */
  updateOption<K extends keyof CoherenceOptions>(key: K, value: CoherenceOptions[K]): void {
    coherenceStore.update(state => ({
      ...state,
      options: {
        ...state.options,
        [key]: value
      }
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
        check_line_structure: enabled
      }
    }));
  }
};
