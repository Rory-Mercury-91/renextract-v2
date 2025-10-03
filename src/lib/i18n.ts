import common from '../locales/common.json';
import settings from '../locales/settings.json';

export type Language = 'fr' | 'en' | 'de';
export type Theme = 'dark' | 'light' | 'auto';

interface Translations {
  app: typeof common.app;
  navigation: typeof common.navigation;
  languages: typeof common.languages;
  themes: typeof common.themes;
  actions: typeof common.actions;
  settings?: typeof settings;
}

class I18nManager {
  private currentLanguage: Language = 'fr';
  private translations: Translations = common as Translations;

  constructor() {
    this.setLanguage('fr');
  }

  setLanguage(lang: Language): void {
    this.currentLanguage = lang;
    // Pour l'instant on utilise les traductions françaises
    // TODO: Charger les bonnes traductions selon la langue
    this.translations = {...common as Translations, settings};
  }

  getCurrentLanguage(): Language {
    return this.currentLanguage;
  }

  t(key: string): string {
    const keys = key.split('.');
    let value: any = this.translations;
    
    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        return key; // Retourner la clé si pas trouvée
      }
    }
    
    return typeof value === 'string' ? value : key;
  }

  // Shortcuts courants
  get app() { return this.translations.app; }
  get navigation() { return this.translations.navigation; }
  get actions() { return this.translations.actions; }
  get settings() { return this.translations.settings; }
}

export const i18n = new I18nManager();
