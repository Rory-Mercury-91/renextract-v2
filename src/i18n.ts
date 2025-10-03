import { addMessages, getLocaleFromNavigator, init } from 'svelte-i18n';

import en from './locales/en.json';
import fr from './locales/fr.json';

addMessages('fr', fr);
addMessages('en',en);

init({
  fallbackLocale: 'en',
  initialLocale: getLocaleFromNavigator(),
});
