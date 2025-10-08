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

<div class="bg-gray-800 flex flex-col gap-2 px-4 my-2">
  <h3 class="text-blue-400 text-lg font-semibold">Dossiers de travail</h3>

  <div class="grid grid-cols-4 gap-4">
    {#each WORK_FOLDERS as { name, icon, color, id, description }}
      <button
        onclick={() => selectFolder(id)}
        class="flex items-center gap-3 p-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors text-left"
        title={description}
      >
        <div
          class="w-6 h-6 {color} rounded-lg flex items-center justify-center text-white"
        >
          <Icon {icon} class="w-4 h-4" />
        </div>
        <div class="text-white font-medium">{name}</div>
      </button>
    {/each}
  </div>

  {#if $appSettings.autoOpenings.outputField}
    <div>
      <h3 class="text-blue-400 font-semibold mb-2">Dossier de sortie</h3>
      <div class="flex items-center gap-3">
        <button
          onclick={selectOutputFolder}
          class="flex-1 flex items-center justify-between py-2 px-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
        >
          <span class="text-gray-300">{outputFolder || 'Non défini'}</span>
          <span class="text-blue-400">🏠</span>
        </button>
      </div>
    </div>
  {/if}
</div>
