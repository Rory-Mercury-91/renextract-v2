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
  }
};

interface AppSettings {
  language: string;
  theme: 'light' | 'dark' | 'auto';
  debugActive: false, // Single debug mode (false=Level 3, true=Level 4)
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
    renpySdk: '',
    vscode: '',
    sublime: '',
    notepad: '',
    atom: '',
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
}

const initialSettings: AppSettings = {
  language: 'fr',
  theme: 'auto',
  debugActive: false, // Single debug mode (false=Level 3, true=Level 4)
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
      renpySdk: '',
      vscode: '',
      sublime: '',
      notepad: '',
      atom: '',
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
  }
}

export { appActions, appSettings, appSettingsActions };
