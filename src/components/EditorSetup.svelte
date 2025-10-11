<script lang="ts">
  import { apiService } from '$lib/api';
  import { appSettings, appSettingsActions } from '$stores/app';
  import Icon from '@iconify/svelte';
  import { onMount } from 'svelte';

  let showSetup = $state(false);
  let isDragging = $state(false);
  let zenityInfo = $state<any>(null);
  let wslInfo = $state<any>(null);
  let editorPath = $state('');
  let isLoading = $state(false);

  // Vérifier si l'éditeur est configuré
  const isEditorConfigured = $derived($appSettings.paths.editor && $appSettings.paths.editor.trim() !== '');

  onMount(async () => {
    // Charger les informations WSL et zenity
    const [wslResult, zenityResult] = await Promise.all([
      apiService.getWslInfo(),
      apiService.checkZenity()
    ]);

    if (wslResult.success) {
      wslInfo = wslResult.info;
    }
    if (zenityResult.success) {
      zenityInfo = zenityResult;
    }

    // Afficher le setup si l'éditeur n'est pas configuré
    if (!isEditorConfigured) {
      showSetup = true;
    }
  });

  const handleDragOver = (event: DragEvent) => {
    event.preventDefault();
    isDragging = true;
  };

  const handleDragLeave = (event: DragEvent) => {
    event.preventDefault();
    isDragging = false;
  };

  const handleDrop = async (event: DragEvent) => {
    event.preventDefault();
    isDragging = false;
    
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      const file = files[0];
      // En mode web, on ne peut pas accéder au chemin complet du fichier
      // On utilise le nom du fichier comme fallback
      const filePath = (file as any).path || file.name;
      
      // Vérifier si c'est un exécutable
      if (filePath.endsWith('.exe') || filePath.endsWith('.app') || !filePath.includes('.')) {
        editorPath = filePath;
        await saveEditorPath();
      } else {
        alert('Veuillez sélectionner un exécutable d\'éditeur (fichier .exe, .app ou sans extension)');
      }
    }
  };

  const openFileDialog = async () => {
    try {
      const result = await apiService.openDialog({
        dialog_type: 'file',
        title: 'Sélectionner l\'éditeur',
        filetypes: [
          ['Exécutables', '*.exe'],
          ['Applications', '*.app'],
          ['Tous les fichiers', '*.*']
        ]
      });

      if (result.success && result.path) {
        editorPath = result.path;
        await saveEditorPath();
      }
    } catch (error) {
      console.error('Erreur lors de la sélection de l\'éditeur:', error);
    }
  };

  const saveEditorPath = async () => {
    if (!editorPath.trim()) return;
    
    isLoading = true;
    try {
      appSettingsActions.setSetting('paths', {
        ...$appSettings.paths,
        editor: editorPath
      });
      
      // Attendre un peu pour que la sauvegarde se fasse
      await new Promise(resolve => setTimeout(resolve, 500));
      showSetup = false;
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
      alert('Erreur lors de la sauvegarde du chemin de l\'éditeur');
    } finally {
      isLoading = false;
    }
  };

  const installZenity = () => {
    const command = 'sudo apt install zenity';
    if (navigator.clipboard) {
      navigator.clipboard.writeText(command).then(() => {
        alert('Commande copiée dans le presse-papiers !\n\nCollez-la dans votre terminal WSL et exécutez-la.');
      });
    } else {
      alert(`Commande à exécuter dans votre terminal WSL:\n\n${command}`);
    }
  };

  const skipSetup = () => {
    showSetup = false;
  };
</script>

{#if showSetup}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="mx-4 w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl dark:bg-gray-800">
      <div class="mb-6 text-center">
        <Icon icon="hugeicons:code-01" class="mx-auto mb-4 h-16 w-16 text-blue-600" />
        <h2 class="mb-2 text-2xl font-bold text-gray-900 dark:text-white">
          Configuration de l'éditeur
        </h2>
        <p class="text-gray-600 dark:text-gray-400">
          RenExtract a besoin d'un éditeur configuré pour fonctionner correctement.
        </p>
      </div>

      <!-- Zone de drag and drop -->
      <div
        class="mb-6 rounded-lg border-2 border-dashed p-8 text-center transition-colors {isDragging
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
          : 'border-gray-300 dark:border-gray-600'}"
        role="button"
        tabindex="0"
        ondragover={handleDragOver}
        ondragleave={handleDragLeave}
        ondrop={handleDrop}
      >
        <Icon icon="hugeicons:upload-01" class="mx-auto mb-4 h-12 w-12 text-gray-400" />
        <p class="mb-2 text-lg font-medium text-gray-700 dark:text-gray-300">
          Glissez-déposez votre éditeur ici
        </p>
        <p class="mb-4 text-sm text-gray-500 dark:text-gray-400">
          Ou cliquez sur le bouton ci-dessous pour le sélectionner
        </p>
        <button
          onclick={openFileDialog}
          disabled={isLoading}
          class="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {isLoading ? 'Chargement...' : 'Sélectionner un éditeur'}
        </button>
      </div>

      <!-- Chemin de l'éditeur -->
      {#if editorPath}
        <div class="mb-6 rounded-lg bg-gray-100 p-4 dark:bg-gray-700">
          <label for="editor-path" class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
            Chemin de l'éditeur :
          </label>
          <div class="flex items-center gap-2">
            <input
              id="editor-path"
              type="text"
              bind:value={editorPath}
              class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              placeholder="Chemin vers l'exécutable de l'éditeur"
            />
            <button
              onclick={saveEditorPath}
              disabled={isLoading || !editorPath.trim()}
              class="rounded bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700 disabled:opacity-50"
            >
              {isLoading ? 'Sauvegarde...' : 'Sauvegarder'}
            </button>
          </div>
        </div>
      {/if}

      <!-- Section WSL/Zenity -->
      {#if wslInfo?.is_wsl && !zenityInfo?.available}
        <div class="mb-6 rounded-lg border border-orange-200 bg-orange-50 p-4 dark:border-orange-800 dark:bg-orange-900/20">
          <div class="flex items-start gap-3">
            <Icon icon="hugeicons:warning-triangle" class="mt-1 h-5 w-5 text-orange-600" />
            <div class="flex-1">
              <h3 class="mb-2 font-medium text-orange-800 dark:text-orange-200">
                Environnement WSL détecté
              </h3>
              <p class="mb-3 text-sm text-orange-700 dark:text-orange-300">
                Pour une meilleure expérience avec les dialogues de fichier, installez zenity :
              </p>
              <button
                onclick={installZenity}
                class="rounded bg-orange-600 px-3 py-1 text-sm text-white hover:bg-orange-700"
              >
                📋 Copier la commande d'installation
              </button>
            </div>
          </div>
        </div>
      {/if}

      <!-- Boutons d'action -->
      <div class="flex justify-end gap-3">
        <button
          onclick={skipSetup}
          class="rounded border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
        >
          Passer pour l'instant
        </button>
        {#if editorPath.trim()}
          <button
            onclick={saveEditorPath}
            disabled={isLoading}
            class="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? 'Configuration...' : 'Continuer'}
          </button>
        {/if}
      </div>
    </div>
  </div>
{/if}
