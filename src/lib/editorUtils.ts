/**
 * Utilitaires pour l'ouverture de fichiers dans l'éditeur externe
 * 
 * @example
 * ```typescript
 * // Ouvrir un fichier simple
 * await openFile('/path/to/file.rpy');
 * 
 * // Ouvrir un fichier avec numéro de ligne
 * await openFileAtLine('/path/to/file.rpy', 42);
 * 
 * // Ouvrir plusieurs fichiers
 * await openMultipleFiles([
 *   { filePath: '/path/to/file1.rpy' },
 *   { filePath: '/path/to/file2.rpy', lineNumber: 10 }
 * ]);
 * 
 * // Ouvrir avec options personnalisées
 * await openInEditor({
 *   filePath: '/path/to/file.rpy',
 *   lineNumber: 42,
 *   successMessage: 'Fichier ouvert avec succès !'
 * });
 * ```
 */

import { apiService } from './api';

export interface OpenInEditorOptions {
  /** Chemin du fichier à ouvrir */
  filePath: string;
  /** Numéro de ligne (optionnel) */
  lineNumber?: number;
  /** Message de succès personnalisé (optionnel) */
  successMessage?: string;
  /** Message d'erreur personnalisé (optionnel) */
  errorMessage?: string;
}

export interface OpenInEditorResult {
  success: boolean;
  message?: string;
  error?: string;
}

/**
 * Ouvre un fichier dans l'éditeur externe configuré
 * @param options Options d'ouverture
 * @returns Résultat de l'opération
 */
export async function openInEditor(options: OpenInEditorOptions): Promise<OpenInEditorResult> {
  const { filePath, lineNumber, successMessage, errorMessage } = options;

  try {
    console.info("📂 Ouverture dans l'éditeur:", filePath, lineNumber ? `ligne ${lineNumber}` : '');
    
    const response = await apiService.openExtractionFile(filePath, lineNumber);
    
    if (response.success) {
      const message = successMessage || response.message || "Fichier ouvert avec succès";
      console.info("✅", message);
      return {
        success: true,
        message
      };
    } else {
      const error = errorMessage || response.error || "Erreur lors de l'ouverture du fichier";
      console.error("❌", error);
      return {
        success: false,
        error
      };
    }
  } catch (error) {
    const errorMsg = errorMessage || `Erreur lors de l'ouverture du fichier: ${error instanceof Error ? error.message : 'Erreur inconnue'}`;
    console.error("❌", errorMsg);
    return {
      success: false,
      error: errorMsg
    };
  }
}

/**
 * Ouvre un fichier simple (sans numéro de ligne)
 * @param filePath Chemin du fichier
 * @returns Résultat de l'opération
 */
export async function openFile(filePath: string): Promise<OpenInEditorResult> {
  return openInEditor({ filePath });
}

/**
 * Ouvre un fichier avec numéro de ligne
 * @param filePath Chemin du fichier
 * @param lineNumber Numéro de ligne
 * @returns Résultat de l'opération
 */
export async function openFileAtLine(filePath: string, lineNumber: number): Promise<OpenInEditorResult> {
  return openInEditor({ 
    filePath, 
    lineNumber,
    successMessage: `Fichier ouvert à la ligne ${lineNumber}`
  });
}

/**
 * Ouvre plusieurs fichiers en séquence
 * @param files Liste des fichiers à ouvrir
 * @param delay Délai entre les ouvertures en ms (défaut: 150ms)
 * @returns Résultats de toutes les opérations
 */
export async function openMultipleFiles(
  files: Array<{ filePath: string; lineNumber?: number }>,
  delay: number = 150
): Promise<OpenInEditorResult[]> {
  const results: OpenInEditorResult[] = [];
  
  for (const file of files) {
    const result = await openInEditor({
      filePath: file.filePath,
      lineNumber: file.lineNumber
    });
    results.push(result);
    
    // Délai entre les ouvertures pour éviter de surcharger le système
    if (delay > 0) {
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  return results;
}
