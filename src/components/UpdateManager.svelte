<script lang="ts">
  import Icon from '@iconify/svelte';
  import axios from 'axios';
  import { onMount } from 'svelte';

  // Types
  interface UpdateInfo {
    success: boolean;
    has_update: boolean;
    current_version: string;
    latest_version: string;
    latest_version_name: string;
    release_notes: string;
    published_at: string;
    download_url: string;
    download_size: number;
    asset_name: string;
    current_os: string;
    error?: string;
  }

  interface UpdateConfig {
    auto_check: boolean;
    auto_install: boolean;
    check_interval_hours: number;
    last_check: number | null;
  }

  interface Props {
    showSettings?: boolean;
    autoCheck?: boolean;
    inSettings?: boolean;
  }

  // Props
  const { showSettings = false, autoCheck = $bindable(true), inSettings = false }: Props = $props();

  // State
  let updateInfo: UpdateInfo | null = $state(null);
  let updateConfig: UpdateConfig | null = $state(null);
  let isChecking = $state(false);
  let isDownloading = $state(false);
  let isInstalling = $state(false);
  const downloadProgress = $state(0);
  let showUpdateDialog = $state(false);
  let showConfigDialog = $state(false);
  let errorMessage = $state('');
  let successMessage = $state('');

  // Fonctions utilitaires
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Fonctions API
  const checkForUpdates = async (): Promise<void> => {
    isChecking = true;
    errorMessage = '';
    successMessage = '';

    try {
      const response = await axios.get('/api/updates/check');
      updateInfo = response.data;

      if (updateInfo?.success && updateInfo?.has_update) {
        showUpdateDialog = true;
      } else if (updateInfo?.success) {
        successMessage = 'Vous utilisez déjà la dernière version !';
      }
    } catch (error) {
      console.error('Erreur lors de la vérification des mises à jour:', error);
      errorMessage = 'Erreur lors de la vérification des mises à jour';
    } finally {
      isChecking = false;
    }
  };

  const downloadUpdate = async (): Promise<void> => {
    if (!updateInfo?.download_url) return;

    isDownloading = true;
    errorMessage = '';

    try {
      const response = await axios.post('/api/updates/download', {
        download_url: updateInfo.download_url,
        latest_version: updateInfo.latest_version,
      });

      if (response.data.success) {
        successMessage = 'Mise à jour téléchargée avec succès !';

        // Si installation automatique est activée
        if (updateConfig?.auto_install) {
          setTimeout(() => {
            installUpdate(response.data.executable_path);
          }, 1000);
        }
      } else {
        errorMessage = response.data.error || 'Erreur lors du téléchargement';
      }
    } catch (error) {
      console.error('Erreur lors du téléchargement:', error);
      errorMessage = 'Erreur lors du téléchargement de la mise à jour';
    } finally {
      isDownloading = false;
    }
  };

  const installUpdate = async (executablePath?: string): Promise<void> => {
    if (!executablePath && !updateInfo) return;

    isInstalling = true;
    errorMessage = '';

    try {
      const response = await axios.post('/api/updates/install', {
        executable_path: executablePath,
      });

      if (response.data.success) {
        successMessage =
          "Mise à jour installée ! Relancez l'application manuellement.";
        showUpdateDialog = false;

        // Fermer l'application pour permettre la mise à jour
        if (response.data.should_exit) {
          setTimeout(async () => {
            try {
              await axios.post('/api/app/exit');
            } catch (error) {
              console.error('Erreur lors de la fermeture:', error);
            }
          }, 3000);
        }
      } else {
        errorMessage = response.data.error || "Erreur lors de l'installation";
      }
    } catch (error) {
      console.error("Erreur lors de l'installation:", error);
      errorMessage = "Erreur lors de l'installation de la mise à jour";
    } finally {
      isInstalling = false;
    }
  };

  const loadUpdateConfig = async (): Promise<void> => {
    try {
      const response = await axios.get('/api/updates/config');
      if (response.data.success) {
        updateConfig = response.data.config;
      }
    } catch (error) {
      console.error('Erreur lors du chargement de la config:', error);
    }
  };

  const saveUpdateConfig = async (): Promise<void> => {
    if (!updateConfig) return;

    try {
      const response = await axios.post('/api/updates/config', updateConfig);
      if (response.data.success) {
        successMessage = 'Configuration sauvegardée avec succès !';
        showConfigDialog = false;
      } else {
        errorMessage = response.data.error || 'Erreur lors de la sauvegarde';
      }
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
      errorMessage = 'Erreur lors de la sauvegarde de la configuration';
    }
  };

  const shouldAutoCheck = async (): Promise<boolean> => {
    try {
      const response = await axios.get('/api/updates/auto-check');
      return response.data.success && response.data.should_check;
    } catch (error) {
      console.error('Erreur lors de la vérification auto:', error);
      return false;
    }
  };

  // Lifecycle
  onMount(async () => {
    await loadUpdateConfig();

    if (autoCheck) {
      const shouldCheck = await shouldAutoCheck();
      if (shouldCheck) {
        await checkForUpdates();
      }
    }
  });

  // Fonctions de gestion des événements
  const closeUpdateDialog = (): void => {
    showUpdateDialog = false;
    updateInfo = null;
  };

  const closeConfigDialog = (): void => {
    showConfigDialog = false;
  };

  const openConfigDialog = (): void => {
    showConfigDialog = true;
  };

  const clearMessages = (): void => {
    errorMessage = '';
    successMessage = '';
  };
</script>

<!-- Composant principal -->
<div class="relative flex items-center gap-2">
  <!-- Bouton de vérification des mises à jour -->
  <button
    class="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-all duration-200 hover:-translate-y-0.5 hover:transform hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
    class:animate-pulse={isChecking}
    onclick={checkForUpdates}
    disabled={isChecking || isDownloading || isInstalling}
    title="Vérifier les mises à jour"
  >
    {#if isChecking}
      <Icon
        icon="hugeicons:refresh-01"
        class="animate-spin"
        width="16"
        height="16"
      />
    {:else}
      <Icon icon="hugeicons:refresh-01" width="16" height="16" />
    {/if}
    <span>Vérifier les mises à jour</span>
  </button>

  <!-- Bouton de configuration -->
  {#if showSettings}
    <button
      class="flex h-10 w-10 items-center justify-center rounded-lg border border-gray-300 bg-gray-100 transition-all duration-200 hover:bg-gray-200 dark:border-gray-600 dark:bg-gray-600 dark:hover:bg-gray-500"
      onclick={openConfigDialog}
      title="Configuration des mises à jour"
    >
      <Icon icon="hugeicons:settings-01" width="16" height="16" />
    </button>
  {/if}

  <!-- Messages d'état -->
  {#if errorMessage}
    <button
      class="animate-slide-down absolute left-0 right-0 top-full z-50 mt-2 flex cursor-pointer items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-700 dark:border-red-700 dark:bg-red-900 dark:text-red-200"
      onclick={clearMessages}
    >
      <Icon icon="hugeicons:alert-circle" width="16" height="16" />
      <span>{errorMessage}</span>
      <Icon
        icon="hugeicons:close-01"
        width="16"
        height="16"
        class="ml-auto opacity-70 hover:opacity-100"
      />
    </button>
  {/if}

  {#if successMessage}
    <button
      class="animate-slide-down absolute left-0 right-0 top-full z-50 mt-2 flex cursor-pointer items-center gap-2 rounded-lg border border-green-200 bg-green-50 p-3 text-sm font-medium text-green-700 dark:border-green-700 dark:bg-green-900 dark:text-green-200"
      onclick={clearMessages}
    >
      <Icon icon="hugeicons:check-circle" width="16" height="16" />
      <span>{successMessage}</span>
      <Icon
        icon="hugeicons:close-01"
        width="16"
        height="16"
        class="ml-auto opacity-70 hover:opacity-100"
      />
    </button>
  {/if}
</div>

<!-- Dialog de mise à jour disponible -->
{#if showUpdateDialog && updateInfo}
  <div
    class="animate-fade-in fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
  >
    <div
      class="animate-slide-up mx-4 max-h-[80vh] w-full max-w-2xl overflow-hidden rounded-lg bg-white shadow-2xl dark:bg-gray-800 dark:text-gray-50"
    >
      <div
        class="flex items-center justify-between border-b border-gray-200 p-6 dark:border-gray-700"
      >
        <h3 class="text-xl font-semibold text-gray-900 dark:text-gray-50">
          Mise à jour disponible
        </h3>
        <button
          class="rounded-md p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-600"
          onclick={closeUpdateDialog}
        >
          <Icon icon="hugeicons:close-01" width="20" height="20" />
        </button>
      </div>

      <div class="max-h-[60vh] overflow-y-auto p-6">
        <div class="space-y-4">
          <div class="space-y-2">
            <div class="flex items-center gap-2">
              <span class="font-medium text-gray-600 dark:text-gray-400"
                >Version actuelle :</span
              >
              <span
                class="rounded bg-gray-100 px-2 py-1 font-mono text-sm font-semibold dark:bg-gray-600"
                >{updateInfo.current_version}</span
              >
            </div>
            <div class="flex items-center gap-2">
              <span class="font-medium text-gray-600 dark:text-gray-400"
                >Nouvelle version :</span
              >
              <span
                class="rounded bg-green-100 px-2 py-1 font-mono text-sm font-semibold text-green-800 dark:bg-green-900 dark:text-green-200"
                >{updateInfo.latest_version}</span
              >
            </div>
          </div>

          {#if updateInfo.latest_version_name}
            <div class="text-lg font-semibold text-gray-900 dark:text-gray-50">
              {updateInfo.latest_version_name}
            </div>
          {/if}

          {#if updateInfo.download_size > 0}
            <div class="flex items-center gap-2 text-sm">
              <span class="font-medium text-gray-600 dark:text-gray-400"
                >Taille :</span
              >
              <span>{formatFileSize(updateInfo.download_size)}</span>
            </div>
          {/if}

          {#if updateInfo.published_at}
            <div class="flex items-center gap-2 text-sm">
              <span class="font-medium text-gray-600 dark:text-gray-400"
                >Publié le :</span
              >
              <span>{formatDate(updateInfo.published_at)}</span>
            </div>
          {/if}

          {#if updateInfo.release_notes}
            <div>
              <h4 class="mb-2 font-semibold text-gray-900 dark:text-gray-50">
                Notes de version :
              </h4>
              <div
                class="rounded-lg bg-gray-50 p-4 text-sm leading-relaxed text-gray-700 dark:bg-gray-700 dark:text-gray-300"
                style:white-space="pre-line"
              >
                {updateInfo.release_notes}
              </div>
            </div>
          {/if}
        </div>
      </div>

      <div
        class="flex justify-end gap-3 border-t border-gray-200 p-6 dark:border-gray-700"
      >
        <button
          class="rounded-lg bg-gray-100 px-6 py-2 font-medium text-gray-700 transition-colors hover:bg-gray-200 disabled:opacity-60 dark:bg-gray-600 dark:text-gray-200 dark:hover:bg-gray-500 dark:disabled:bg-gray-700 dark:disabled:text-gray-400"
          onclick={closeUpdateDialog}
          disabled={isDownloading || isInstalling}
        >
          Plus tard
        </button>
        <button
          class="flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2 font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-60"
          class:animate-pulse={isDownloading || isInstalling}
          onclick={downloadUpdate}
          disabled={isDownloading || isInstalling}
        >
          {#if isDownloading}
            <Icon
              icon="hugeicons:refresh-01"
              class="animate-spin"
              width="16"
              height="16"
            />
            <span>Téléchargement...</span>
          {:else if isInstalling}
            <Icon
              icon="hugeicons:refresh-01"
              class="animate-spin"
              width="16"
              height="16"
            />
            <span>Installation...</span>
          {:else}
            <Icon icon="hugeicons:download-01" width="16" height="16" />
            <span>Mettre à jour</span>
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Dialog de configuration -->
{#if showConfigDialog && updateConfig}
  <div
    class="animate-fade-in fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
  >
    <div
      class="animate-slide-up mx-4 max-h-[80vh] w-full max-w-lg overflow-hidden rounded-lg bg-white shadow-2xl dark:bg-gray-800 dark:text-gray-50"
    >
      <div
        class="flex items-center justify-between border-b border-gray-200 p-6 dark:border-gray-700"
      >
        <h3 class="text-xl font-semibold text-gray-900 dark:text-gray-50">
          Configuration des mises à jour
        </h3>
        <button
          class="rounded-md p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-600"
          onclick={closeConfigDialog}
        >
          <Icon icon="hugeicons:close-01" width="20" height="20" />
        </button>
      </div>

      <div class="max-h-[60vh] overflow-y-auto p-6">
        <div class="space-y-4">
          <label class="flex cursor-pointer items-center gap-3">
            <input
              type="checkbox"
              bind:checked={updateConfig.auto_check}
              class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
            />
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300"
              >Vérification automatique des mises à jour</span
            >
          </label>

          <label class="flex cursor-pointer items-center gap-3">
            <input
              type="checkbox"
              bind:checked={updateConfig.auto_install}
              disabled={!updateConfig.auto_check}
              class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700"
            />
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300"
              >Installation automatique après téléchargement</span
            >
          </label>

          <div class="space-y-2">
            <label
              for="check-interval"
              class="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Intervalle de vérification (heures) :
            </label>
            <input
              id="check-interval"
              type="number"
              min="1"
              max="168"
              bind:value={updateConfig.check_interval_hours}
              disabled={!updateConfig.auto_check}
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:disabled:bg-gray-700 dark:disabled:text-gray-400"
            />
          </div>

          {#if updateConfig.last_check}
            <div
              class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400"
            >
              <span class="font-medium">Dernière vérification :</span>
              <span
                >{formatDate(
                  new Date(updateConfig.last_check * 1000).toISOString()
                )}</span
              >
            </div>
          {/if}
        </div>
      </div>

      <div
        class="flex justify-end gap-3 border-t border-gray-200 p-6 dark:border-gray-700"
      >
        <button
          class="rounded-lg bg-gray-100 px-6 py-2 font-medium text-gray-700 transition-colors hover:bg-gray-200 dark:bg-gray-600 dark:text-gray-200 dark:hover:bg-gray-500"
          onclick={closeConfigDialog}
        >
          Annuler
        </button>
        <button
          class="rounded-lg bg-blue-600 px-6 py-2 font-medium text-white transition-colors hover:bg-blue-700"
          onclick={saveUpdateConfig}
        >
          Sauvegarder
        </button>
      </div>
    </div>
  </div>
{/if}
