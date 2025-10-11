import { apiService } from '$lib/api';
import { get, writable } from 'svelte/store';

interface AppState {
  // currentTheme: Theme;
  debugLevel: number;
  isLoading: boolean;
  error: string | null;
}

const initialState: AppState = {
  // currentTheme: 'dark',
  debugLevel: 4, // DEBUG complet par défaut
  isLoading: false,
  error: null,
};

export const appState = writable<AppState>(initialState);

const appActions = {
  setState: <K extends keyof AppState>(key: K, value: AppState[K]) => {
    appState.update(state => ({ ...state, [key]: value }));
  },
};

interface AppSettings {
  language: string;
  theme: 'light' | 'dark' | 'auto';
  debugActive: boolean; // Single debug mode (false=Level 3, true=Level 4)
  translatorFeature: boolean;
  autoOpenings: {
    files: boolean;
    folders: boolean;
    reports: boolean;
    outputField: boolean;
  };
  externalTools: {
    translator: string;
  };
  paths: {
    editor: string;
    renpySdk: string;
  };
  folders: {
    temporary: string;
    reports: string;
    backups: string;
    configs: string;
  };
  extraction: {
    placeholderFormat: string;
    encoding: string;
    detectDuplicates: boolean;
    projectProgressTracking: boolean;
    lineLimit: number;
    defaultSaveMode: 'overwrite' | 'new_file';
    patterns: {
      code: string;
      asterisk: string;
      tilde: string;
    };
  };
  reconstruction: {
    saveMode: 'overwrite' | 'new_file';
  };
  coherence: {
    checkVariables: boolean;
    checkTags: boolean;
    checkUntranslated: boolean;
    checkEscapeSequences: boolean;
    checkPercentages: boolean;
    checkQuotations: boolean;
    checkParentheses: boolean;
    checkSyntax: boolean;
    checkDeeplEllipsis: boolean;
    checkIsolatedPercent: boolean;
    checkFrenchQuotes: boolean;
    checkDoubleDashEllipsis: boolean;
    checkSpecialCodes: boolean;
    checkLineStructure: boolean;
    customExclusions: string[];
  };
  lastProject: {
    path: string;
    language: string;
    mode: 'project' | 'single_file';
  };
}

const initialSettings: AppSettings = {
  language: 'fr',
  theme: 'auto',
  debugActive: false, // Single debug mode (false=Level 3, true=Level 4)
  translatorFeature: false,
  autoOpenings: {
    files: true,
    folders: true,
    reports: true,
    outputField: false,
  },
  externalTools: {
    translator: '',
  },
  paths: {
    editor: '',
    renpySdk: '',
  },
  folders: {
    temporary: '01_Temporary/',
    reports: '02_Reports/',
    backups: '03_Backups/',
    configs: '04_Configs/',
  },
  extraction: {
    placeholderFormat: 'PLACEHOLDER_{n}',
    encoding: 'UTF-8',
    detectDuplicates: true,
    projectProgressTracking: false,
    lineLimit: 1000,
    defaultSaveMode: 'new_file',
    patterns: {
      code: 'RENPY_CODE_001',
      asterisk: 'RENPY_ASTERISK_001',
      tilde: 'RENPY_TILDE_001',
    },
  },
  reconstruction: {
    saveMode: 'new_file',
  },
  coherence: {
    checkVariables: true,
    checkTags: true,
    checkUntranslated: true,
    checkEscapeSequences: true,
    checkPercentages: true,
    checkQuotations: true,
    checkParentheses: true,
    checkSyntax: true,
    checkDeeplEllipsis: true,
    checkIsolatedPercent: true,
    checkFrenchQuotes: true,
    checkDoubleDashEllipsis: true,
    checkSpecialCodes: false,
    checkLineStructure: true,
    customExclusions: [
      'OK',
      'Menu',
      'Continue',
      'Yes',
      'No',
      'Level',
      '???',
      '!!!',
      '...',
    ],
  },
  lastProject: {
    path: '',
    language: '',
    mode: 'project',
  },
};

const appSettings = writable<AppSettings>(initialSettings);

const appSettingsActions = {
  _settingsLoaded: false as boolean,
  _syncTimer: null as ReturnType<typeof setTimeout> | null,
  async _syncNow() {
    if (!this._settingsLoaded) return;
    try {
      const current = get(appSettings) as unknown as Record<string, unknown>;
      await apiService.updateSettings(current);
    } catch {
      // Ignorer silencieusement
    }
  },
  _scheduleSync() {
    if (!this._settingsLoaded) return;
    if (this._syncTimer) clearTimeout(this._syncTimer);
    this._syncTimer = setTimeout(async () => {
      await appSettingsActions._syncNow();
    }, 500);
  },
  setSetting: <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    appSettings.update(setting => ({ ...setting, [key]: value }));
    // Utiliser la synchronisation différée pour éviter les appels trop fréquents
    appSettingsActions._scheduleSync();
  },

  resetSettings: () => {
    appSettings.set(initialSettings);
    void appSettingsActions._syncNow();
  },

  resetSettingsPaths: () => {
    appSettings.set({
      ...initialSettings,
      paths: { ...initialSettings.paths, editor: '', renpySdk: '' },
    });
    void appSettingsActions._syncNow();
  },

  loadSettings: async () => {
    const response = await apiService.getSettings();
    // Attendu: { success: boolean, settings: {...} }
    const payload = response as unknown as {
      success?: boolean;
      settings?: Partial<AppSettings>;
    };
    if (payload && payload.success && payload.settings) {
      const fetched = payload.settings;

      const nextSettings = {
        ...initialSettings,
        ...fetched,
      } as AppSettings;
      appSettings.set(nextSettings);
      appSettingsActions._settingsLoaded = true;
    }
  },

  refreshAppSettings: async () => {
    await appSettingsActions.loadSettings();
  },
};

export { appActions, appSettings, appSettingsActions };

// Démarrer immédiatement le chargement
void appSettingsActions.loadSettings();

// Synchronisation automatique même pour les modifications directes via bindings
appSettings.subscribe(() => {
  if (appSettingsActions._settingsLoaded) {
    appSettingsActions._scheduleSync();
  }
});
