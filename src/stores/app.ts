import { writable } from 'svelte/store';

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
  setSetting: <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    appSettings.update(setting => ({ ...setting, [key]: value }));
  },

  resetSettings: () => {
    appSettings.set(initialSettings);
  },

  resetSettingsPaths: () => {
    appSettings.set({
      ...initialSettings,
      paths: { ...initialSettings.paths, editor: '', renpySdk: '' },
    });
  },
};

export { appActions, appSettings, appSettingsActions };
