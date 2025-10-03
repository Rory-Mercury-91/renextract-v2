import type { Language, Theme } from '$lib/i18n';
import { writable } from 'svelte/store';

interface AppState {
  currentSection: string;
  currentLanguage: Language;
  currentTheme: Theme;
  debugLevel: number;
  isLoading: boolean;
  error: string | null;
}

const initialState: AppState = {
  currentSection: 'settings', // On commence par Paramètres comme demandé
  currentLanguage: 'fr',
  currentTheme: 'dark',
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

  setLanguage: (lang: Language) => {
    appState.update(state => ({ ...state, currentLanguage: lang }));
  },

  setTheme: (theme: Theme) => {
    appState.update(state => ({ ...state, currentTheme: theme }));
  },

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
