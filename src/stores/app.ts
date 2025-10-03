import { writable } from 'svelte/store';

interface AppState {
  currentSection: string;
  // currentTheme: Theme;
  debugLevel: number;
  isLoading: boolean;
  error: string | null;
}

const initialState: AppState = {
  currentSection: 'settings', // On commence par Paramètres comme demandé
  // currentTheme: 'dark',
  debugLevel: 4, // DEBUG complet par défaut
  isLoading: false,
  error: null
};

export const appState = writable<AppState>(initialState);

// Actions pour modifier l'état
export const appActions = {
  setCurrentSection: (section: string) => {
    appState.update(state => ({ ...state, currentSection: section }));
  },

  // setTheme: (theme: Theme) => {
  //   appState.update(state => ({ ...state, currentTheme: theme }));
  // },

  setDebugLevel: (level: number) => {
    appState.update(state => ({ ...state, debugLevel: level }));
  },

  setLoading: (loading: boolean) => {
    appState.update(state => ({ ...state, isLoading: loading }));
  },

  setError: (error: string | null) => {
    appState.update(state => ({ ...state, error }));
  }
};
