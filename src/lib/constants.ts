/**
 * Constants and Configuration for RenExtract v2
 * Centralized folder definitions and application constants
 */

// ========================================
// FOLDER DEFINITIONS
// ========================================

export const FOLDERS = {
  TEMPORARY: '01_Temporary',
  REPORTS: '02_Reports', 
  BACKUPS: '03_Backups',
  CONFIGS: '04_Configs'
} as const;

export const WORK_FOLDERS = [
  { 
    id: '01', 
    name: FOLDERS.TEMPORARY, 
    icon: 'hugeicons:folder-02', 
    color: 'bg-yellow-700',
    description: 'Fichiers temporaires et de travail'
  },
  { 
    id: '02', 
    name: FOLDERS.REPORTS, 
    icon: 'hugeicons:analysis-text-link', 
    color: 'bg-blue-600',
    description: 'Rapports d\'extraction et d\'analyse'
  },
  { 
    id: '03', 
    name: FOLDERS.BACKUPS, 
    icon: 'hugeicons:floppy-disk', 
    color: 'bg-purple-600',
    description: 'Sauvegardes automatiques et manuelles'
  },
  { 
    id: '04', 
    name: FOLDERS.CONFIGS, 
    icon: 'hugeicons:settings-02', 
    color: 'bg-gray-600',
    description: 'Fichiers de configuration et paramètres'
  }
] as const;

// ========================================
// BACKUP TYPES
// ========================================

export const BACKUP_TYPES = {
  SECURITY: 'security',
  CLEANUP: 'cleanup',
  RPA_BUILD: 'rpa_build',
  REALTIME_EDIT: 'realtime_edit'
} as const;

export const BACKUP_DESCRIPTIONS = {
  [BACKUP_TYPES.SECURITY]: '🛡️ Sécurité',
  [BACKUP_TYPES.CLEANUP]: '🧹 Nettoyage',
  [BACKUP_TYPES.RPA_BUILD]: '📦 Avant RPA',
  [BACKUP_TYPES.REALTIME_EDIT]: '⚡ Édition temps réel'
} as const;

// ========================================
// APPLICATION CONSTANTS
// ========================================

export const APP_CONFIG = {
  NAME: 'RenExtract',
  VERSION: '2.0.0',
  AUTHOR: 'Rory Mercury91',
  DESCRIPTION: 'Outil d\'extraction et de préparation à la traduction pour les jeux Ren\'Py'
} as const;

// ========================================
// DEFAULT SETTINGS
// ========================================

export const DEFAULT_SETTINGS = {
  language: 'fr',
  theme: 'dark',
  debugActive: false,
  autoOpenings: {
    files: true,
    folders: true,
    reports: false,
    outputField: false
  },
  externalTools: {
    textEditor: 'VS Code',
    translator: ''
  },
  paths: {
    renpySdk: '',
    vscode: '',
    sublime: '',
    notepad: '',
    atom: ''
  },
  folders: {
    temporary: `${FOLDERS.TEMPORARY}/`,
    reports: `${FOLDERS.REPORTS}/`,
    backups: `${FOLDERS.BACKUPS}/`,
    configs: `${FOLDERS.CONFIGS}/`
  },
  extraction: {
    placeholderFormat: 'PLACEHOLDER_{n}',
    encoding: 'UTF-8'
  }
} as const;

// ========================================
// UTILITY FUNCTIONS
// ========================================

export function getFolderPath(folderName: keyof typeof FOLDERS): string {
  return FOLDERS[folderName];
}

export function getWorkFolderById(id: string) {
  return WORK_FOLDERS.find(folder => folder.id === id);
}

export function getAllFolderNames(): string[] {
  return Object.values(FOLDERS);
}

export function validateFolderName(name: string): boolean {
  if (!name || typeof name !== 'string') return false;
  if (name.length > 255 || name.length < 1) return false;
  if (/[<>:"|?*\\/]/.test(name)) return false;
  if (name.startsWith(' ') || name.endsWith(' ') || name.startsWith('.') || name.endsWith('.')) return false;
  return true;
}

// ========================================
// TYPE EXPORTS
// ========================================

export type FolderName = keyof typeof FOLDERS;
export type BackupType = keyof typeof BACKUP_TYPES;
export type WorkFolder = typeof WORK_FOLDERS[number];
