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
    textEditor: string;
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
    reports: false,
    outputField: false,
  },
  externalTools: {
    textEditor: 'VS Code',
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
    // Sauvegarde immédiate pour éviter la perte en cas de refresh rapide
    void appSettingsActions._syncNow();
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
    // Attendu: { success: boolean, data: {...} }
    const payload = response as unknown as {
      success?: boolean;
      data?: Partial<AppSettings>;
    };
    if (payload && payload.success && payload.data) {
      const fetched = payload.data;

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

export const editorPath = writable<string>('');
