<script lang="ts">
  /* eslint-env browser */
  import { apiService } from '$lib/api';
  import Icon from '@iconify/svelte';
  import { WORK_FOLDERS } from '../lib/constants';
  import { appSettings } from '../stores/app';

  const outputFolder = '';

  async function selectFolder(folderId: string) {
    try {
      // Trouver le dossier correspondant
      const folder = WORK_FOLDERS.find(f => f.id === folderId);
      if (!folder) {
        console.error('Dossier non trouvé:', folderId);
        return;
      }

      // Ouvrir le dossier via l'API
      const response = await apiService.openExtractionFolder(folder.name);
      
      if (response.success) {
        console.log('✅ Dossier ouvert:', folder.name);
      } else {
        console.error('❌ Erreur ouverture dossier:', response.error);
      }
    } catch (error) {
      console.error('❌ Erreur exceptionnelle:', error);
    }
  }

  function selectOutputFolder() {
    // eslint-disable-next-line no-console
    console.log('Select output folder');
  }
</script>

<div class="my-2 flex flex-col gap-2 bg-gray-800 px-4">
  <h3 class="text-lg font-semibold text-blue-400">Dossiers de travail</h3>

  <div class="grid grid-cols-4 gap-4">
    {#each WORK_FOLDERS as { name, icon, color, id, description }}
      <button
        onclick={() => selectFolder(id)}
        class="flex items-center gap-3 rounded-lg bg-gray-700 p-3 text-left transition-colors hover:bg-gray-600"
        title={description}
      >
        <div
          class="h-6 w-6 {color} flex items-center justify-center rounded-lg text-white"
        >
          <Icon {icon} class="h-4 w-4" />
        </div>
        <div class="font-medium text-white">{name}</div>
      </button>
    {/each}
  </div>

  {#if $appSettings.autoOpenings.outputField}
    <div>
      <h3 class="mb-2 font-semibold text-blue-400">Dossier de sortie</h3>
      <div class="flex items-center gap-3">
        <button
          onclick={selectOutputFolder}
          class="flex flex-1 items-center justify-between rounded-lg bg-gray-700 px-3 py-2 transition-colors hover:bg-gray-600"
        >
          <span class="text-gray-300">{outputFolder || 'Non défini'}</span>
          <span class="text-blue-400">🏠</span>
        </button>
      </div>
    </div>
  {/if}
</div>
