<script lang="ts">
  import Icon from '@iconify/svelte';
  import { appSettings } from '../stores/app';

  const workFolders = [
    {
      id: '01',
      name: '01_Temporary',
      icon: 'hugeicons:folder-02',
      color: 'bg-yellow-700',
    },
    {
      id: '02',
      name: '02_Reports',
      icon: 'hugeicons:analysis-text-link',
      color: 'bg-blue-600',
    },
    {
      id: '03',
      name: '03_Backups',
      icon: 'hugeicons:floppy-disk',
      color: 'bg-purple-600',
    },
    {
      id: '04',
      name: '04_Configs',
      icon: 'hugeicons:settings-02',
      color: 'bg-gray-600',
    },
  ];

  let outputFolder = '';

  function selectFolder(folderId: string) {
    console.log('Selected folder:', folderId);
  }

  function selectOutputFolder() {
    console.log('Select output folder');
  }
</script>

<div class="bg-gray-800 flex flex-col gap-2 px-4 mt-2 mb-2">
  <h3 class="text-blue-400 font-semibold">Dossiers de travail</h3>

  <div class="grid grid-cols-4 gap-4">
    {#each workFolders as { name, icon, color, id }}
      <button
        onclick={() => selectFolder(id)}
        class="flex items-center gap-3 p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors text-left"
      >
        <div class="w-6 h-6 {color} rounded-lg flex items-center justify-center text-white">
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
