<script lang="ts">
  /* eslint-env browser */
  import RouteHeader from '$components/RouteHeader.svelte';
  import Icon from '@iconify/svelte';
  import { onMount } from 'svelte';
  import { _ } from 'svelte-i18n';
  import { apiService } from '../lib/api';
  import { BACKUP_DESCRIPTIONS } from '../lib/constants';

  // États
  let backups: any[] = [];
  let filteredBackups: any[] = $state([]);
  let loading = $state(true);
  let error: string | null = $state(null);
  let statusMessage = $state('Chargement...');
  let lastScanTime: Date | null = $state(null);

  // Filtres
  let selectedGame = $state('Tous');
  let selectedType = $state('Tous');
  let games: string[] = $state(['Tous']);

  // Statistiques
  let totalBackups = $state(0);
  let totalGames = $state(0);
  let totalSize = $state(0);

  // Tri
  let sortColumn: string | null = $state(null);
  let sortDirection: 'asc' | 'desc' = $state('asc');

  // Backup sélectionné
  const selectedBackup: any = null;

  async function loadBackups() {
    loading = true;
    statusMessage = '📄 Chargement des sauvegardes en cours...';
    error = null;

    try {
      const result = await apiService.getBackups(
        selectedGame !== 'Tous' ? selectedGame : undefined,
        selectedType !== 'Tous' ? selectedType : undefined
      );

      if (result.success) {
        backups = result.backups || [];
        console.log(backups);
        filteredBackups = backups;
        updateStatistics();
        updateGameFilter();
        lastScanTime = new Date();
        statusMessage = `✅ ${backups.length} sauvegardes chargées - Prêt`;
      } else {
        error = result.error || 'Erreur de chargement';
        statusMessage = '❌ Erreur lors du chargement';
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Erreur inconnue';
      statusMessage = '❌ Erreur lors du chargement';
    } finally {
      loading = false;
    }
  }

  function updateStatistics() {
    totalBackups = filteredBackups.length;
    totalGames = new Set(filteredBackups.map(b => b.game_name)).size;
    totalSize = filteredBackups.reduce((sum, b) => sum + (b.size || 0), 0);
  }

  function updateGameFilter() {
    const uniqueGames = new Set(backups.map(b => b.game_name));
    games = ['Tous', ...Array.from(uniqueGames).sort()];
  }

  function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function formatDate(isoString: string): string {
    try {
      const date = new Date(isoString);
      return date.toLocaleString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  }

  // Fonction de rechargement manuel
  async function refreshBackups() {
    statusMessage = '🔄 Rechargement des sauvegardes...';
    await loadBackups();
  }

  // Fonction pour formater l'heure du dernier scan
  function formatLastScanTime(): string {
    if (!lastScanTime) return 'Jamais';
    return lastScanTime.toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  }

  function handleFilterChange() {
    loadBackups();
  }

  async function restoreBackup(backup: any) {
    if (
      !window.confirm(
        `Restaurer la sauvegarde ?\n\n• Fichier : ${backup.source_filename}\n• Jeu : ${backup.game_name}\n• Type : ${BACKUP_DESCRIPTIONS[backup.type as keyof typeof BACKUP_DESCRIPTIONS] || backup.type}\n\nLe fichier actuel sera remplacé !`
      )
    ) {
      return;
    }

    try {
      statusMessage = '🔄 Restauration en cours...';
      const result = await apiService.restoreBackup(backup.id);

      if (result.success) {
        statusMessage = '✅ Restauration terminée avec succès';
        loadBackups(); // Recharger la liste
      } else {
        statusMessage = '❌ Erreur lors de la restauration';
        window.alert(`Erreur : ${result.error}`);
      }
    } catch (err) {
      statusMessage = '❌ Erreur lors de la restauration';
      window.alert(
        `Erreur : ${err instanceof Error ? err.message : 'Erreur inconnue'}`
      );
    }
  }

  async function restoreBackupTo(backup: any) {
    // Préparer le nom de fichier initial
    let originalFilename = backup.source_filename || 'fichier_restaure';

    // S'assurer que le fichier a l'extension .rpy
    if (!originalFilename.endsWith('.rpy')) {
      originalFilename += '.rpy';
    }

    // Ouvrir le dialogue de sauvegarde (équivalent à asksaveasfilename)
    const result = await apiService.openSaveDialog({
      title: 'Restaurer vers...',
      initialfile: originalFilename,
      defaultextension: '.rpy',
      filetypes: [
        ["Fichiers Ren'Py", '*.rpy'],
        ['Tous les fichiers', '*.*'],
      ],
    });

    if (!result.success || !result.path) {
      return;
    }

    const targetPath = result.path;

    // Pas de confirmation - l'utilisateur a déjà choisi l'emplacement
    try {
      statusMessage = '🔄 Restauration vers chemin personnalisé en cours...';
      const restoreResult = await apiService.restoreBackupTo(
        backup.id,
        targetPath
      );

      if (restoreResult.success) {
        statusMessage = '✅ Restauration vers chemin personnalisé terminée';
      } else {
        statusMessage =
          '❌ Erreur lors de la restauration vers chemin personnalisé';
        window.alert(`Erreur : ${restoreResult.error}`);
      }
    } catch (err) {
      statusMessage =
        '❌ Erreur lors de la restauration vers chemin personnalisé';
      window.alert(
        `Erreur : ${err instanceof Error ? err.message : 'Erreur inconnue'}`
      );
    }
  }

  async function deleteBackup(backup: any) {
    if (
      !window.confirm(
        `Supprimer définitivement cette sauvegarde ?\n\n• Fichier : ${backup.source_filename}\n• Jeu : ${backup.game_name}\n• Taille : ${formatSize(backup.size)}\n\nCette action est irréversible !`
      )
    ) {
      return;
    }

    try {
      statusMessage = '🗑️ Suppression en cours...';
      const result = await apiService.deleteBackup(backup.id);

      if (result.success) {
        statusMessage = '✅ Sauvegarde supprimée avec succès';
        loadBackups(); // Recharger la liste
      } else {
        statusMessage = '❌ Erreur lors de la suppression';
        window.alert(`Erreur : ${result.error}`);
      }
    } catch (err) {
      statusMessage = '❌ Erreur lors de la suppression';
      window.alert(
        `Erreur : ${err instanceof Error ? err.message : 'Erreur inconnue'}`
      );
    }
  }

  function sortBy(column: string) {
    if (sortColumn === column) {
      sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      sortColumn = column;
      sortDirection = 'asc';
    }

    filteredBackups = [...filteredBackups].sort((a, b) => {
      let aVal = a[column];
      let bVal = b[column];

      if (column === 'created') {
        aVal = new Date(aVal).getTime();
        bVal = new Date(bVal).getTime();
      } else if (column === 'size') {
        aVal = parseInt(aVal) || 0;
        bVal = parseInt(bVal) || 0;
      }

      if (sortDirection === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });
  }

  onMount(() => {
    loadBackups();
  });
</script>

<div class="flex h-full flex-col text-gray-900 dark:text-white">
  <RouteHeader
    title={$_('navigation.backup')}
    description={$_('navigation.backup_description')}
    icon="hugeicons:floppy-disk"
    color="text-purple-300"
  >
    <div class="mr-6 flex flex-col items-end gap-1 text-right text-sm">
      <button
        class="flex items-center justify-center gap-2 rounded-lg bg-purple-300 px-4 py-1.5 text-sm font-bold text-slate-800 transition-all duration-200 hover:opacity-65"
        onclick={refreshBackups}
        disabled={loading}
        title="Recharger la liste des sauvegardes"
      >
        {#if loading}
          <Icon icon="hugeicons:refresh" class="h-4 w-4 animate-spin" />
        {/if}
        Recharger
      </button>
      <div class="text-gray-600 dark:text-gray-400">
        <span class="text-green-600 dark:text-green-400">●</span> Dernier scan: {formatLastScanTime()}
      </div>
    </div>
  </RouteHeader>

  <!-- Content -->
  <div class="flex-1 overflow-y-auto p-6">
    <!-- Statistiques -->
    <div class="mb-4 rounded-lg p-6">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-semibold text-blue-600 dark:text-blue-400">
          📊 Statistiques des sauvegardes
        </h2>
      </div>
      <div class="grid grid-cols-3 gap-6">
        <div>
          <p class="text-sm text-gray-600 dark:text-gray-400">Sauvegardes totales</p>
          <p class="text-2xl font-bold">{totalBackups}</p>
        </div>
        <div>
          <p class="text-sm text-gray-600 dark:text-gray-400">Jeux concernés</p>
          <p class="text-2xl font-bold">{totalGames}</p>
        </div>
        <div>
          <p class="text-sm text-gray-600 dark:text-gray-400">Taille totale</p>
          <p class="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {formatSize(totalSize)}
          </p>
        </div>
      </div>
    </div>

    <!-- Filtres -->
    <div class="mb-4 rounded-lg p-6">
      <h2 class="mb-4 text-lg font-semibold text-blue-600 dark:text-blue-400">🔍 Filtres</h2>
      <div class="grid grid-cols-2 gap-6">
        <div>
          <label for="game-filter" class="mb-2 block text-sm font-medium"
            >🎮 Filtrer par jeu :</label
          >
          <select
            id="game-filter"
            bind:value={selectedGame}
            onchange={handleFilterChange}
            class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          >
            {#each games as game}
              <option value={game}>{game}</option>
            {/each}
          </select>
        </div>
        <div>
          <label for="type-filter" class="mb-2 block text-sm font-medium"
            >🏷️ Filtrer par type :</label
          >
          <select
            id="type-filter"
            bind:value={selectedType}
            onchange={handleFilterChange}
            class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          >
            <option value="Tous">Tous</option>
            {#each Object.entries(BACKUP_DESCRIPTIONS) as [key, value]}
              <option value={key}>{value}</option>
            {/each}
          </select>
        </div>
      </div>
    </div>

    <!-- Liste des sauvegardes -->
    <div class="rounded-lg p-6">
      <h2 class="mb-4 text-lg font-semibold text-blue-600 dark:text-blue-400">
        📋 Liste des sauvegardes
      </h2>

      {#if loading}
        <div class="flex items-center justify-center py-12">
          <div
            class="h-10 w-10 animate-spin rounded-full border-4 border-gray-300 border-t-blue-500 dark:border-gray-600"
          ></div>
          <p class="ml-4 text-gray-600 dark:text-gray-400">Chargement...</p>
        </div>
      {:else if error}
        <div class="py-12 text-center text-red-600 dark:text-red-400">
          <p>❌ {error}</p>
          <button
            class="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700"
            onclick={loadBackups}
          >
            Réessayer
          </button>
        </div>
      {:else if filteredBackups.length === 0}
        <div class="py-12 text-center text-gray-600 dark:text-gray-400">
          <p>Aucune sauvegarde trouvée</p>
        </div>
      {:else}
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-200 dark:bg-gray-700">
              <tr>
                <th
                  class="cursor-pointer px-4 py-3 text-left hover:bg-gray-300 dark:hover:bg-gray-600"
                  onclick={() => sortBy('game_name')}
                >
                  Jeu {sortColumn === 'game_name'
                    ? sortDirection === 'asc'
                      ? '↑'
                      : '↓'
                    : ''}
                </th>
                <th
                  class="cursor-pointer px-4 py-3 text-left hover:bg-gray-300 dark:hover:bg-gray-600"
                  onclick={() => sortBy('source_filename')}
                >
                  Fichier {sortColumn === 'source_filename'
                    ? sortDirection === 'asc'
                      ? '↑'
                      : '↓'
                    : ''}
                </th>
                <th
                  class="cursor-pointer px-4 py-3 text-left hover:bg-gray-300 dark:hover:bg-gray-600"
                  onclick={() => sortBy('type')}
                >
                  Type {sortColumn === 'type'
                    ? sortDirection === 'asc'
                      ? '↑'
                      : '↓'
                    : ''}
                </th>
                <th
                  class="cursor-pointer px-4 py-3 text-left hover:bg-gray-300 dark:hover:bg-gray-600"
                  onclick={() => sortBy('created')}
                >
                  Date {sortColumn === 'created'
                    ? sortDirection === 'asc'
                      ? '↑'
                      : '↓'
                    : ''}
                </th>
                <th
                  class="cursor-pointer px-4 py-3 text-left hover:bg-gray-300 dark:hover:bg-gray-600"
                  onclick={() => sortBy('size')}
                >
                  Taille {sortColumn === 'size'
                    ? sortDirection === 'asc'
                      ? '↑'
                      : '↓'
                    : ''}
                </th>
                <th class="px-4 py-3 text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {#each filteredBackups as backup}
                <tr
                  class="hover:bg-gray-750 border-t border-gray-700 transition-colors"
                >
                  <td class="px-4 py-3">{backup.game_name}</td>
                  <td class="px-4 py-3">{backup.source_filename}</td>
                  <td class="px-4 py-3"
                    >{(BACKUP_DESCRIPTIONS as any)[backup.type] ||
                      backup.type}</td
                  >
                  <td class="px-4 py-3">{formatDate(backup.created)}</td>
                  <td class="px-4 py-3">{formatSize(backup.size)}</td>
                  <td class="px-4 py-3 text-center">
                    <div class="flex items-center justify-center gap-2">
                      <button
                        class="rounded bg-blue-600 px-3 py-1 text-sm text-white transition-colors hover:bg-blue-700"
                        onclick={() => restoreBackup(backup)}
                        title="Restaurer vers l'emplacement d'origine"
                      >
                        💾 Restaurer
                      </button>
                      <button
                        class="rounded bg-green-600 px-3 py-1 text-sm text-white transition-colors hover:bg-green-700"
                        onclick={() => restoreBackupTo(backup)}
                        title="Restaurer vers un chemin spécifique (comme asksaveasfilename)"
                      >
                        📄 Restaurer vers...
                      </button>
                      <button
                        class="rounded bg-red-600 px-3 py-1 text-sm text-white transition-colors hover:bg-red-700"
                        onclick={() => deleteBackup(backup)}
                        title="Supprimer"
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </div>
  </div>

  <!-- Footer / Status -->
  <div class="border-t border-gray-300 bg-gray-100 p-4 dark:border-gray-700 dark:bg-gray-800">
    <p class="text-sm text-gray-400">📊 État : {statusMessage}</p>
  </div>
</div>
