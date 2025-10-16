<script lang="ts">
  import Icon from '@iconify/svelte';
  import axios from 'axios';
  import { onMount } from 'svelte';
  import { _ } from 'svelte-i18n';
  import Dialog from './Dialog.svelte';
  import DialogActions from './DialogActions.svelte';

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

  // State
  let updateInfo: UpdateInfo | null = $state(null);
  let updateConfig: UpdateConfig | null = $state(null);
  let isChecking = $state(false);
  let isDownloading = $state(false);
  const isInstalling = $state(false);
  let downloadProgress = $state(0);
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
    });
  };

  // Fonctions principales
  const checkForUpdates = async () => {
    isChecking = true;
    errorMessage = '';
    successMessage = '';

    try {
      const response = await axios.get('/api/updates/check');
      updateInfo = response.data;

      if (updateInfo?.success) {
        successMessage = updateInfo.has_update
          ? 'Vérification terminée'
          : 'Application à jour';
      } else {
        errorMessage = updateInfo?.error || 'Erreur lors de la vérification';
      }
    } catch (error) {
      console.error('Erreur lors de la vérification des mises à jour:', error);
      errorMessage = 'Impossible de vérifier les mises à jour';
    } finally {
      isChecking = false;
    }
  };

  const downloadUpdate = async () => {
    if (!updateInfo?.download_url) return;

    isDownloading = true;
    errorMessage = '';
    successMessage = '';

    try {
      const response = await axios.post('/api/updates/download', {
        download_url: updateInfo.download_url,
      });

      if (response.data.success) {
        successMessage = 'Mise à jour téléchargée avec succès !';
        // Simuler le téléchargement pour l'instant
        downloadProgress = 100;
      } else {
        errorMessage = response.data.error || $_('settings_updates.download_error');
      }
    } catch (error) {
      console.error('Erreur lors du téléchargement:', error);
      errorMessage = $_('settings_updates.download_impossible');
    } finally {
      isDownloading = false;
    }
  };

  const loadUpdateConfig = async () => {
    try {
      // Charger depuis localStorage
      const savedConfig = window.localStorage.getItem('updateConfig');
      if (savedConfig) {
        updateConfig = JSON.parse(savedConfig);
      } else {
        // Configuration par défaut
        updateConfig = {
          auto_check: true,
          auto_install: false,
          check_interval_hours: 24,
          last_check: null,
        };
      }
    } catch (error) {
      console.error('Erreur lors du chargement de la configuration:', error);
      // Configuration par défaut en cas d'erreur
      updateConfig = {
        auto_check: true,
        auto_install: false,
        check_interval_hours: 24,
        last_check: null,
      };
    }
  };

  const saveUpdateConfig = async () => {
    if (!updateConfig) return;

    try {
      // Sauvegarde automatique dans localStorage
      window.localStorage.setItem('updateConfig', JSON.stringify(updateConfig));
      successMessage = $_('settings_updates.config_saved');
      showConfigDialog = false;
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
      errorMessage = $_('settings_updates.config_save_error');
    }
  };

  const closeConfigDialog = () => {
    showConfigDialog = false;
    loadUpdateConfig(); // Recharger la config originale
  };

  // Sauvegarde automatique quand les valeurs changent
  const autoSaveConfig = () => {
    if (updateConfig) {
      window.localStorage.setItem('updateConfig', JSON.stringify(updateConfig));
    }
  };

  // Chargement initial
  onMount(() => {
    checkForUpdates();
    loadUpdateConfig();
  });
</script>

<div class="space-y-6">
  <!-- En-tête -->
  <div class="flex items-center justify-between">
    <div>
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
        {$_('settings_updates.update_manager')}
      </h3>
      <p class="text-sm text-gray-600 dark:text-gray-400">
        {$_('settings_updates.update_manager_description')}
      </p>
    </div>
    <button
      class="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
      onclick={checkForUpdates}
      disabled={isChecking}
    >
      <Icon
        icon="hugeicons:refresh-01"
        class="h-4 w-4 {isChecking ? 'animate-spin' : ''}"
      />
      {isChecking ? $_('settings_updates.checking') : $_('settings_updates.check_updates')}
    </button>
  </div>

  <!-- Informations de version -->
  <div
    class="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800"
  >
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <div>
        <label
          for="current-version"
          class="text-sm font-medium text-gray-700 dark:text-gray-300"
          >Version actuelle</label
        >
        <p
          id="current-version"
          class="text-lg font-semibold text-gray-900 dark:text-white"
        >
          {updateInfo?.current_version || 'Chargement...'}
        </p>
      </div>
      <div>
        <label
          for="latest-version"
          class="text-sm font-medium text-gray-700 dark:text-gray-300"
          >Dernière version</label
        >
        <p
          id="latest-version"
          class="text-lg font-semibold text-gray-900 dark:text-white"
        >
          {updateInfo?.latest_version || 'Non vérifiée'}
        </p>
      </div>
    </div>
  </div>

  <!-- Statut de mise à jour -->
  {#if updateInfo}
    {#if updateInfo.has_update}
      <div
        class="rounded-lg border border-orange-200 bg-orange-50 p-4 dark:border-orange-800 dark:bg-orange-900/20"
      >
        <div class="flex items-start gap-3">
          <Icon
            icon="hugeicons:warning-triangle"
            class="mt-1 h-5 w-5 text-orange-600"
          />
          <div class="flex-1">
            <h4 class="font-medium text-orange-800 dark:text-orange-200">
              Mise à jour disponible !
            </h4>
            <p class="mt-1 text-sm text-orange-700 dark:text-orange-300">
              Version {updateInfo.latest_version} ({updateInfo.latest_version_name})
              est disponible. Taille: {formatFileSize(updateInfo.download_size)}
            </p>
            <div class="mt-3 flex gap-2">
              <button
                class="rounded bg-orange-600 px-3 py-1 text-sm text-white hover:bg-orange-700 disabled:opacity-50"
                onclick={downloadUpdate}
                disabled={isDownloading || isInstalling}
              >
                {isDownloading ? 'Téléchargement...' : 'Télécharger'}
              </button>
              <button
                class="rounded border border-orange-300 px-3 py-1 text-sm text-orange-700 hover:bg-orange-100 dark:border-orange-600 dark:text-orange-300 dark:hover:bg-orange-900/30"
                onclick={() => (showUpdateDialog = true)}
              >
                Voir les détails
              </button>
            </div>
          </div>
        </div>
      </div>
    {:else}
      <div
        class="rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/20"
      >
        <div class="flex items-center gap-3">
          <Icon
            icon="hugeicons:checkmark-circle"
            class="h-5 w-5 text-green-600"
          />
          <div>
            <h4 class="font-medium text-green-800 dark:text-green-200">
              Application à jour
            </h4>
            <p class="text-sm text-green-700 dark:text-green-300">
              Vous utilisez la dernière version de RenExtract
            </p>
          </div>
        </div>
      </div>
    {/if}
  {/if}

  <!-- Configuration -->
  <div
    class="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800"
  >
    <div class="flex items-center justify-between">
      <div>
        <h4 class="font-medium text-gray-900 dark:text-white">
          Configuration automatique
        </h4>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Gérer les vérifications automatiques de mises à jour
        </p>
      </div>
      <button
        class="rounded bg-gray-600 px-3 py-1 text-sm text-white hover:bg-gray-700"
        onclick={() => (showConfigDialog = true)}
      >
        Configurer
      </button>
    </div>
  </div>

  <!-- Messages d'erreur/succès -->
  {#if errorMessage}
    <div
      class="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20"
    >
      <div class="flex items-center gap-3">
        <Icon icon="hugeicons:error-circle" class="h-5 w-5 text-red-600" />
        <p class="text-sm text-red-700 dark:text-red-300">{errorMessage}</p>
      </div>
    </div>
  {/if}

  {#if successMessage}
    <div
      class="rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/20"
    >
      <div class="flex items-center gap-3">
        <Icon
          icon="hugeicons:checkmark-circle"
          class="h-5 w-5 text-green-600"
        />
        <p class="text-sm text-green-700 dark:text-green-300">
          {successMessage}
        </p>
      </div>
    </div>
  {/if}
</div>

<!-- Dialog de configuration -->
<Dialog
  isOpen={showConfigDialog && !!updateConfig}
  title="Configuration des mises à jour"
  size="md"
  onClose={closeConfigDialog}
>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <label
        for="auto-check"
        class="text-sm font-medium text-gray-700 dark:text-gray-300"
      >
        Vérification automatique
      </label>
      <input
        id="auto-check"
        type="checkbox"
        checked={updateConfig?.auto_check || false}
        onchange={e => {
          if (updateConfig) {
            updateConfig.auto_check = e.currentTarget.checked;
            autoSaveConfig();
          }
        }}
        class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
      />
    </div>

    <div class="flex items-center justify-between">
      <label
        for="auto-install"
        class="text-sm font-medium text-gray-700 dark:text-gray-300"
      >
        Installation automatique
      </label>
      <input
        id="auto-install"
        type="checkbox"
        checked={updateConfig?.auto_install || false}
        onchange={e => {
          if (updateConfig) {
            updateConfig.auto_install = e.currentTarget.checked;
            autoSaveConfig();
          }
        }}
        class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
      />
    </div>

    <div>
      <label
        for="check-interval"
        class="block text-sm font-medium text-gray-700 dark:text-gray-300"
      >
        Intervalle de vérification (heures)
      </label>
      <input
        id="check-interval"
        type="number"
        value={updateConfig?.check_interval_hours || 24}
        onchange={e => {
          if (updateConfig) {
            updateConfig.check_interval_hours = parseInt(e.currentTarget.value);
            autoSaveConfig();
          }
        }}
        min="1"
        max="168"
        class="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
      />
    </div>
  </div>

  <DialogActions>
    <button
      class="rounded-lg bg-gray-100 px-4 py-2 text-gray-700 hover:bg-gray-200 dark:bg-gray-600 dark:text-gray-200 dark:hover:bg-gray-500"
      onclick={closeConfigDialog}
    >
      Fermer
    </button>
  </DialogActions>
</Dialog>

<!-- Modal de détails de mise à jour -->
<Dialog
  isOpen={showUpdateDialog && !!updateInfo}
  title="Détails de la mise à jour"
  size="xl"
  onClose={() => (showUpdateDialog = false)}
>
  <div class="space-y-4">
    <!-- Informations de version -->
    <div
      class="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800"
    >
      <h4 class="mb-3 font-medium text-gray-900 dark:text-white">
        Informations de version
      </h4>
      <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
        <div>
          <span class="text-sm text-gray-600 dark:text-gray-400"
            >Version actuelle :</span
          >
          <p class="font-medium text-gray-900 dark:text-white">
            {updateInfo?.current_version}
          </p>
        </div>
        <div>
          <span class="text-sm text-gray-600 dark:text-gray-400"
            >Nouvelle version :</span
          >
          <p class="font-medium text-gray-900 dark:text-white">
            {updateInfo?.latest_version}
          </p>
        </div>
        <div>
          <span class="text-sm text-gray-600 dark:text-gray-400"
            >Nom de la version :</span
          >
          <p class="font-medium text-gray-900 dark:text-white">
            {updateInfo?.latest_version_name}
          </p>
        </div>
        <div>
          <span class="text-sm text-gray-600 dark:text-gray-400">Taille :</span>
          <p class="font-medium text-gray-900 dark:text-white">
            {formatFileSize(updateInfo?.download_size || 0)}
          </p>
        </div>
        <div>
          <span class="text-sm text-gray-600 dark:text-gray-400"
            >Date de publication :</span
          >
          <p class="font-medium text-gray-900 dark:text-white">
            {formatDate(updateInfo?.published_at || '')}
          </p>
        </div>
        <div>
          <span class="text-sm text-gray-600 dark:text-gray-400">Fichier :</span
          >
          <p class="font-medium text-gray-900 dark:text-white">
            {updateInfo?.asset_name}
          </p>
        </div>
      </div>
    </div>

    <!-- Notes de version -->
    {#if updateInfo?.release_notes}
      <div
        class="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800"
      >
        <h4 class="mb-3 font-medium text-gray-900 dark:text-white">
          Notes de version
        </h4>
        <div class="prose prose-sm max-w-none text-gray-700 dark:text-gray-300">
          <pre
            class="whitespace-pre-wrap font-sans text-sm">{updateInfo.release_notes}</pre>
        </div>
      </div>
    {/if}
  </div>

  <DialogActions>
    <button
      class="rounded-lg bg-gray-100 px-4 py-2 text-gray-700 hover:bg-gray-200 dark:bg-gray-600 dark:text-gray-200 dark:hover:bg-gray-500"
      onclick={() => (showUpdateDialog = false)}
    >
      Fermer
    </button>
    <button
      class="rounded-lg bg-orange-600 px-4 py-2 text-white hover:bg-orange-700 disabled:opacity-50"
      onclick={() => {
        showUpdateDialog = false;
        downloadUpdate();
      }}
      disabled={isDownloading || isInstalling}
    >
      {isDownloading ? 'Téléchargement...' : 'Télécharger la mise à jour'}
    </button>
  </DialogActions>
</Dialog>
