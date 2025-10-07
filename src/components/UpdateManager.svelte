<script lang="ts">
  import Icon from '@iconify/svelte';
  import axios from 'axios';
  import { createEventDispatcher, onMount } from 'svelte';

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
    auto_download: boolean;
    auto_install: boolean;
    check_interval_hours: number;
    last_check: number | null;
  }

  // Props
  export let showSettings = false;
  export let autoCheck = true;

  // State
  let updateInfo: UpdateInfo | null = null;
  let updateConfig: UpdateConfig | null = null;
  let isChecking = false;
  let isDownloading = false;
  let isInstalling = false;
  const downloadProgress = 0;
  let showUpdateDialog = false;
  let showConfigDialog = false;
  let errorMessage = '';
  let successMessage = '';

  // Event dispatcher
  const dispatch = createEventDispatcher();

  // Fonctions utilitaires
  function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  // Fonctions API
  async function checkForUpdates(): Promise<void> {
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
  }

  async function downloadUpdate(): Promise<void> {
    if (!updateInfo?.download_url) return;

    isDownloading = true;
    errorMessage = '';

    try {
      const response = await axios.post('/api/updates/download', {
        download_url: updateInfo.download_url,
      });

      if (response.data.success) {
        successMessage = 'Mise à jour téléchargée avec succès !';
        // Proposer l'installation
        setTimeout(() => {
          installUpdate(response.data.extract_path);
        }, 1000);
      } else {
        errorMessage = response.data.error || 'Erreur lors du téléchargement';
      }
    } catch (error) {
      console.error('Erreur lors du téléchargement:', error);
      errorMessage = 'Erreur lors du téléchargement de la mise à jour';
    } finally {
      isDownloading = false;
    }
  }

  async function installUpdate(extractPath?: string): Promise<void> {
    if (!extractPath && !updateInfo) return;

    isInstalling = true;
    errorMessage = '';

    try {
      const response = await axios.post('/api/updates/install', {
        extract_path: extractPath,
      });

      if (response.data.success) {
        successMessage = "Mise à jour installée ! L'application va redémarrer.";
        showUpdateDialog = false;

        // Redémarrer l'application après un délai
        setTimeout(() => {
          window.location.reload();
        }, 2000);
      } else {
        errorMessage = response.data.error || "Erreur lors de l'installation";
      }
    } catch (error) {
      console.error("Erreur lors de l'installation:", error);
      errorMessage = "Erreur lors de l'installation de la mise à jour";
    } finally {
      isInstalling = false;
    }
  }

  async function loadUpdateConfig(): Promise<void> {
    try {
      const response = await axios.get('/api/updates/config');
      if (response.data.success) {
        updateConfig = response.data.config;
      }
    } catch (error) {
      console.error('Erreur lors du chargement de la config:', error);
    }
  }

  async function saveUpdateConfig(): Promise<void> {
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
  }

  async function shouldAutoCheck(): Promise<boolean> {
    try {
      const response = await axios.get('/api/updates/auto-check');
      return response.data.success && response.data.should_check;
    } catch (error) {
      console.error('Erreur lors de la vérification auto:', error);
      return false;
    }
  }

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
  function closeUpdateDialog(): void {
    showUpdateDialog = false;
    updateInfo = null;
  }

  function closeConfigDialog(): void {
    showConfigDialog = false;
  }

  function openConfigDialog(): void {
    showConfigDialog = true;
  }

  function clearMessages(): void {
    errorMessage = '';
    successMessage = '';
  }
</script>

<!-- Composant principal -->
<div class="flex items-center gap-2 relative">
  <!-- Bouton de vérification des mises à jour -->
  <button
    class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed hover:transform hover:-translate-y-0.5"
    class:animate-pulse={isChecking}
    onclick={checkForUpdates}
    disabled={isChecking || isDownloading || isInstalling}
    title="Vérifier les mises à jour"
  >
    {#if isChecking}
      <Icon icon="hugeicons:refresh-01" class="animate-spin" width="16" height="16" />
    {:else}
      <Icon icon="hugeicons:refresh-01" width="16" height="16" />
    {/if}
    <span>Vérifier les mises à jour</span>
  </button>

  <!-- Bouton de configuration -->
  {#if showSettings}
    <button
      class="flex items-center justify-center w-10 h-10 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-lg transition-all duration-200"
      onclick={openConfigDialog}
      title="Configuration des mises à jour"
    >
      <Icon icon="hugeicons:settings-01" width="16" height="16" />
    </button>
  {/if}

  <!-- Messages d'état -->
  {#if errorMessage}
    <button class="absolute top-full left-0 right-0 mt-2 flex items-center gap-2 p-3 bg-red-50 text-red-700 border border-red-200 rounded-lg text-sm font-medium cursor-pointer z-50 animate-slide-down" onclick={clearMessages}>
      <Icon icon="hugeicons:alert-circle" width="16" height="16" />
      <span>{errorMessage}</span>
      <Icon icon="hugeicons:close-01" width="16" height="16" class="ml-auto opacity-70 hover:opacity-100" />
    </button>
  {/if}

  {#if successMessage}
    <button class="absolute top-full left-0 right-0 mt-2 flex items-center gap-2 p-3 bg-green-50 text-green-700 border border-green-200 rounded-lg text-sm font-medium cursor-pointer z-50 animate-slide-down" onclick={clearMessages}>
      <Icon icon="hugeicons:check-circle" width="16" height="16" />
      <span>{successMessage}</span>
      <Icon icon="hugeicons:close-01" width="16" height="16" class="ml-auto opacity-70 hover:opacity-100" />
    </button>
  {/if}
</div>

<!-- Dialog de mise à jour disponible -->
{#if showUpdateDialog && updateInfo}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 animate-fade-in">
    <div class="bg-white rounded-lg shadow-2xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden animate-slide-up">
      <div class="flex items-center justify-between p-6 border-b border-gray-200">
        <h3 class="text-xl font-semibold text-gray-900">Mise à jour disponible</h3>
        <button class="p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors" onclick={closeUpdateDialog}>
          <Icon icon="hugeicons:close-01" width="20" height="20" />
        </button>
      </div>

      <div class="p-6 max-h-[60vh] overflow-y-auto">
        <div class="space-y-4">
          <div class="space-y-2">
            <div class="flex items-center gap-2">
              <span class="font-medium text-gray-600">Version actuelle :</span>
              <span class="font-mono font-semibold px-2 py-1 bg-gray-100 rounded text-sm">{updateInfo.current_version}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="font-medium text-gray-600">Nouvelle version :</span>
              <span class="font-mono font-semibold px-2 py-1 bg-green-100 text-green-800 rounded text-sm">{updateInfo.latest_version}</span>
            </div>
          </div>

          {#if updateInfo.latest_version_name}
            <div class="text-lg font-semibold text-gray-900">
              {updateInfo.latest_version_name}
            </div>
          {/if}

          {#if updateInfo.download_size > 0}
            <div class="flex items-center gap-2 text-sm">
              <span class="font-medium text-gray-600">Taille :</span>
              <span>{formatFileSize(updateInfo.download_size)}</span>
            </div>
          {/if}

          {#if updateInfo.published_at}
            <div class="flex items-center gap-2 text-sm">
              <span class="font-medium text-gray-600">Publié le :</span>
              <span>{formatDate(updateInfo.published_at)}</span>
            </div>
          {/if}

          {#if updateInfo.release_notes}
            <div>
              <h4 class="font-semibold text-gray-900 mb-2">Notes de version :</h4>
              <div class="bg-gray-50 p-4 rounded-lg text-sm leading-relaxed text-gray-700">
                {@html updateInfo.release_notes.replace(/\n/g, '<br>')}
              </div>
            </div>
          {/if}
        </div>
      </div>

      <div class="flex justify-end gap-3 p-6 border-t border-gray-200">
        <button
          class="px-6 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-colors disabled:opacity-60"
          onclick={closeUpdateDialog}
          disabled={isDownloading || isInstalling}
        >
          Plus tard
        </button>
        <button
          class="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-60"
          class:animate-pulse={isDownloading || isInstalling}
          onclick={downloadUpdate}
          disabled={isDownloading || isInstalling}
        >
          {#if isDownloading}
            <Icon icon="hugeicons:refresh-01" class="animate-spin" width="16" height="16" />
            <span>Téléchargement...</span>
          {:else if isInstalling}
            <Icon icon="hugeicons:refresh-01" class="animate-spin" width="16" height="16" />
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
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 animate-fade-in">
    <div class="bg-white rounded-lg shadow-2xl max-w-lg w-full mx-4 max-h-[80vh] overflow-hidden animate-slide-up">
      <div class="flex items-center justify-between p-6 border-b border-gray-200">
        <h3 class="text-xl font-semibold text-gray-900">Configuration des mises à jour</h3>
        <button class="p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors" onclick={closeConfigDialog}>
          <Icon icon="hugeicons:close-01" width="20" height="20" />
        </button>
      </div>

      <div class="p-6 max-h-[60vh] overflow-y-auto">
        <div class="space-y-4">
          <label class="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" bind:checked={updateConfig.auto_check} class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500" />
            <span class="text-sm font-medium text-gray-700">Vérification automatique des mises à jour</span>
          </label>

          <label class="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              bind:checked={updateConfig.auto_download}
              disabled={!updateConfig.auto_check}
              class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 disabled:opacity-50"
            />
            <span class="text-sm font-medium text-gray-700">Téléchargement automatique des mises à jour</span>
          </label>

          <label class="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              bind:checked={updateConfig.auto_install}
              disabled={!updateConfig.auto_download}
              class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 disabled:opacity-50"
            />
            <span class="text-sm font-medium text-gray-700">Installation automatique des mises à jour</span>
          </label>

          <div class="space-y-2">
            <label for="check-interval" class="block text-sm font-medium text-gray-700">
              Intervalle de vérification (heures) :
            </label>
            <input
              id="check-interval"
              type="number"
              min="1"
              max="168"
              bind:value={updateConfig.check_interval_hours}
              disabled={!updateConfig.auto_check}
              class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
            />
          </div>

          {#if updateConfig.last_check}
            <div class="flex items-center gap-2 text-sm text-gray-600">
              <span class="font-medium">Dernière vérification :</span>
              <span>{formatDate(new Date(updateConfig.last_check * 1000).toISOString())}</span>
            </div>
          {/if}
        </div>
      </div>

      <div class="flex justify-end gap-3 p-6 border-t border-gray-200">
        <button class="px-6 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-colors" onclick={closeConfigDialog}>
          Annuler
        </button>
        <button class="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors" onclick={saveUpdateConfig}>
          Sauvegarder
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  /* Animations personnalisées pour Tailwind CSS */
  @keyframes fade-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes slide-up {
    from {
      opacity: 0;
      transform: translateY(1rem);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes slide-down {
    from {
      opacity: 0;
      transform: translateY(-0.5rem);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .animate-fade-in {
    animation: fade-in 0.2s ease-out;
  }

  .animate-slide-up {
    animation: slide-up 0.3s ease-out;
  }

  .animate-slide-down {
    animation: slide-down 0.3s ease-out;
  }

  /* Mode sombre */
  :global(.dark) .bg-white {
    background-color: #1f2937;
    color: #f9fafb;
  }

  :global(.dark) .text-gray-900 {
    color: #f9fafb;
  }

  :global(.dark) .text-gray-700 {
    color: #d1d5db;
  }

  :global(.dark) .text-gray-600 {
    color: #9ca3af;
  }

  :global(.dark) .border-gray-200 {
    border-color: #374151;
  }

  :global(.dark) .bg-gray-50 {
    background-color: #374151;
  }

  :global(.dark) .bg-gray-100 {
    background-color: #4b5563;
  }

  :global(.dark) .border-gray-300 {
    border-color: #4b5563;
  }

  :global(.dark) .hover\:bg-gray-100:hover {
    background-color: #4b5563;
  }

  :global(.dark) .hover\:bg-gray-200:hover {
    background-color: #6b7280;
  }

  :global(.dark) .disabled\:bg-gray-100:disabled {
    background-color: #374151;
  }

  :global(.dark) .disabled\:text-gray-500:disabled {
    color: #9ca3af;
  }
</style>
