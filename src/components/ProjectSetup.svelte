<script lang="ts">
  import { apiService } from '$lib/api';
  import { projectActions, projectStore } from '$stores/project';
  import Icon from '@iconify/svelte';
  import { onMount } from 'svelte';
  import { _ } from 'svelte-i18n';
  import Dialog from './Dialog.svelte';
  import DialogActions from './DialogActions.svelte';

  let showSetup = $state(false);
  let isDragging = $state(false);
  let zenityInfo = $state<any>(null);
  let wslInfo = $state<any>(null);
  const isLoading = $state(false);

  // Vérifier si le projet est configuré et chargé
  const isProjectConfigured = $derived(
    $projectStore.projectPath && 
    $projectStore.projectPath.trim() !== '' &&
    $projectStore.availableLanguages.length > 0 &&
    !$projectStore.isLoading
  );

  // Debug: surveiller les changements d'état
  $effect(() => {
    console.log('ProjectSetup Debug:', {
      projectPath: $projectStore.projectPath,
      availableLanguages: $projectStore.availableLanguages.length,
      isLoading: $projectStore.isLoading,
      isProjectConfigured: isProjectConfigured,
      showSetup: showSetup
    });
  });

  // Fermer automatiquement le setup quand le projet est configuré
  $effect(() => {
    if (isProjectConfigured && showSetup) {
      console.log('Projet configuré, fermeture du setup');
      showSetup = false;
    }
  });

  onMount(async () => {
    // Charger les informations WSL et zenity
    const [wslResult, zenityResult] = await Promise.all([
      apiService.getWslInfo(),
      apiService.checkZenity(),
    ]);

    if (wslResult.success) {
      wslInfo = wslResult.info;
    }
    if (zenityResult.success) {
      zenityInfo = zenityResult;
    }

    // Attendre un peu pour que le chargement automatique du projet commence
    await new Promise(resolve => setTimeout(resolve, 1500));

    // Afficher le setup si le projet n'est pas configuré
    if (!isProjectConfigured) {
      console.log('Projet non configuré, affichage du setup');
      showSetup = true;
    } else {
      console.log('Projet déjà configuré, pas de setup nécessaire');
    }
  });

  const handleDragOver = (event: Event) => {
    event.preventDefault();
    isDragging = true;
  };

  const handleDragLeave = (event: Event) => {
    event.preventDefault();
    isDragging = false;
  };

  const handleDrop = async (event: Event) => {
    event.preventDefault();
    isDragging = false;

    const files = (event as Event & { dataTransfer?: { files?: FileList } })
      .dataTransfer?.files;
    if (files && files.length > 0) {
      const file = files[0];
      // En mode web, on ne peut pas accéder au chemin complet du fichier
      // On utilise le nom du fichier comme fallback
      const filePath = (file as any).path || file.name;

      // Vérifier si c'est un exécutable
      if (
        filePath.endsWith('.exe') ||
        filePath.endsWith('.app') ||
        !filePath.includes('.')
      ) {
        $projectStore.projectPath = filePath;
        await projectActions.loadProject(filePath);
        showSetup = false;
      } else {
        window.alert($_('project.select_executable'));
      }
    }
  };

  const openFileDialog = async () => {
    try {
      const result = await apiService.openDialog({
        dialog_type: 'folder',
        title: 'Sélectionner le dossier du jeu',
        filetypes: [],
        initialdir: 'C:\\',
        must_exist: true,
      });

      if (result.success && result.path) {
        $projectStore.projectPath = result.path;
        await projectActions.loadProject(result.path);
        showSetup = false;
      }
    } catch (error) {
      console.error($_('project.editor_selection_error'), error);
    }
  };

  const installZenity = () => {
    const command = 'sudo apt install zenity';
    if (window.navigator.clipboard) {
      window.navigator.clipboard.writeText(command).then(() => {
        window.alert(
          'Commande copiée dans le presse-papiers !\n\nCollez-la dans votre terminal WSL et exécutez-la.'
        );
      });
    } else {
      window.alert(
        `Commande à exécuter dans votre terminal WSL:\n\n${command}`
      );
    }
  };

  const skipSetup = () => {
    showSetup = false;
  };
</script>

<Dialog
  isOpen={showSetup}
  title=""
  size="xl"
  showCloseButton={false}
  onClose={skipSetup}
>
  <div class="text-center">
    <Icon
      icon="hugeicons:code-01"
      class="mx-auto mb-4 h-16 w-16 text-blue-600"
    />
    <h2 class="mb-2 text-2xl font-bold text-gray-900 dark:text-white">
      {$_('project.setup_title')}
    </h2>
    <p class="text-gray-600 dark:text-gray-400">
      RenExtract a besoin d'un projet configuré pour fonctionner correctement.
    </p>
  </div>

  <!-- Indicateur de chargement du projet -->
  {#if $projectStore.projectPath && $projectStore.projectPath.trim() !== '' && $projectStore.isLoading}
    <div class="mb-6 rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-900/20">
      <div class="flex items-center gap-3">
        <div class="animate-spin">
          <Icon icon="hugeicons:loading-01" class="h-6 w-6 text-blue-600" />
        </div>
        <div>
          <p class="font-medium text-blue-800 dark:text-blue-200">Chargement du projet...</p>
          <p class="text-sm text-blue-600 dark:text-blue-400">
            Analyse en cours de {$projectStore.projectPath}
          </p>
        </div>
      </div>
    </div>
  {/if}

  <!-- Zone de drag and drop -->
  {#if !($projectStore.projectPath && $projectStore.projectPath.trim() !== '' && $projectStore.isLoading)}
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
    <Icon
      icon="hugeicons:upload-01"
      class="mx-auto mb-4 h-12 w-12 text-gray-400"
    />
    <p class="mb-2 text-lg font-medium text-gray-700 dark:text-gray-300">
      {$_('project.drag_drop_instruction')}
    </p>
    <p class="mb-4 text-sm text-gray-500 dark:text-gray-400">
      {$_('project.or_click_browse')}
    </p>
    <button
      onclick={openFileDialog}
      disabled={isLoading}
      class="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
    >
      {isLoading ? $_('project.loading') : $_('project.select_renpy_game')}
    </button>
  </div>
  {/if}

  <!-- Section WSL/Zenity -->
  {#if wslInfo?.is_wsl && !zenityInfo?.available}
    <div
      class="mb-6 rounded-lg border border-orange-200 bg-orange-50 p-4 dark:border-orange-800 dark:bg-orange-900/20"
    >
      <div class="flex items-start gap-3">
        <Icon
          icon="hugeicons:warning-triangle"
          class="mt-1 h-5 w-5 text-orange-600"
        />
        <div class="flex-1">
          <h3 class="mb-2 font-medium text-orange-800 dark:text-orange-200">
            Environnement WSL
          </h3>
          <p class="mb-3 text-sm text-orange-700 dark:text-orange-300">
            Pour une meilleure expérience avec les dialogues de fichier,
            installez zenity :
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

  <DialogActions align="right">
    <button
      onclick={skipSetup}
      class="rounded border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
    >
      Passer pour l'instant
    </button>
  </DialogActions>
</Dialog>
