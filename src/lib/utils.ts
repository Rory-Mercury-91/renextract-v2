import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { appSettings, appSettingsActions, editorPath } from '../stores/app';
import { apiService } from './api';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChild<T> = T extends { child?: any } ? Omit<T, 'child'> : T;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChildren<T> = T extends { children?: any } ? Omit<T, 'children'> : T;
export type WithoutChildrenOrChild<T> = WithoutChildren<WithoutChild<T>>;
/* eslint-env browser */
export type WithElementRef<T, U extends globalThis.HTMLElement = globalThis.HTMLElement> = T & { ref?: U | null };


export const showBrowse = async (
    title: string,
    placeholder: string,
    inputId: string,
    currentValue: string = ''
  ) => {
    // Essayer le dialogue Windows natif d'abord
    try {
      let result;
      if (inputId === 'renpy-sdk-path') {
        result = await apiService.openFolderDialog();
      } else {
        result = await apiService.openFileDialog();
      }

      if (result.success && result.path && result.path.trim() !== '') {
        // Mettre à jour directement
        if (!appSettings.subscribe(settings => settings.paths)) appSettingsActions.resetSettingsPaths();

        switch (inputId) {
          case 'renpy-sdk-path':
            appSettings.subscribe(settings => settings.paths.renpySdk = result.path || '');
            break;
          case 'editor-path':
            appSettings.subscribe(settings => settings.paths.editor = result.path || '');
            break;
        }

        // Mettre à jour l'input visuellement
        editorPath.set(result.path || '');

        // eslint-disable-next-line no-console
        console.log(`${inputId} path updated via Windows dialog:`, result.path);
      } else {
        // Fallback vers le modal custom si le dialogue Windows échoue
        // eslint-disable-next-line no-console
        console.log(
          'Windows dialog failed or returned empty, using fallback modal'
        );
      }
    } catch (error) {
      // eslint-disable-next-line no-console
      console.warn('Windows dialog failed, falling back to modal:', error);

      // Vérifier si c'est un timeout
      if (error instanceof Error && error.message.includes('timeout')) {
        // eslint-disable-next-line no-console
        console.warn(
          'Dialog timeout - user took too long to select a file/folder'
        );
      }
    }
  };
