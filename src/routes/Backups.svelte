<script lang="ts">
  import { onMount } from 'svelte';
  import { apiService } from '../lib/api';
  import { BACKUP_DESCRIPTIONS } from '../lib/constants';

  // États
  let backups: any[] = [];
  let filteredBackups: any[] = [];
  let loading = true;
  let error: string | null = null;
  let statusMessage = 'Chargement...';
  let lastScanTime: Date | null = null;

  // Filtres
  let selectedGame = 'Tous';
  let selectedType = 'Tous';
  let games: string[] = ['Tous'];

  // Statistiques
  let totalBackups = 0;
  let totalGames = 0;
  let totalSize = 0;

  // Tri
  let sortColumn: string | null = null;
  let sortDirection: 'asc' | 'desc' = 'asc';

  // Backup sélectionné
  let selectedBackup: any = null;

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
        minute: '2-digit'
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
      second: '2-digit'
    });
  }

  function handleFilterChange() {
    loadBackups();
  }

  async function restoreBackup(backup: any) {
    if (!confirm(`Restaurer la sauvegarde ?\n\n• Fichier : ${backup.source_filename}\n• Jeu : ${backup.game_name}\n• Type : ${BACKUP_DESCRIPTIONS[backup.type as keyof typeof BACKUP_DESCRIPTIONS] || backup.type}\n\nLe fichier actuel sera remplacé !`)) {
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
        alert(`Erreur : ${result.error}`);
      }
    } catch (err) {
      statusMessage = '❌ Erreur lors de la restauration';
      alert(`Erreur : ${err instanceof Error ? err.message : 'Erreur inconnue'}`);
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
      title: "Restaurer vers...",
      initialfile: originalFilename,
      defaultextension: ".rpy",
      filetypes: [
        ["Fichiers Ren'Py", "*.rpy"],
        ["Tous les fichiers", "*.*"]
      ]
    });
    
    if (!result.success || !result.path) {
      return;
    }

    const targetPath = result.path;

    // Pas de confirmation - l'utilisateur a déjà choisi l'emplacement
    try {
      statusMessage = '🔄 Restauration vers chemin personnalisé en cours...';
      const restoreResult = await apiService.restoreBackupTo(backup.id, targetPath);
      
      if (restoreResult.success) {
        statusMessage = '✅ Restauration vers chemin personnalisé terminée';
      } else {
        statusMessage = '❌ Erreur lors de la restauration vers chemin personnalisé';
        alert(`Erreur : ${restoreResult.error}`);
      }
    } catch (err) {
      statusMessage = '❌ Erreur lors de la restauration vers chemin personnalisé';
      alert(`Erreur : ${err instanceof Error ? err.message : 'Erreur inconnue'}`);
    }
  }

  async function deleteBackup(backup: any) {
    if (!confirm(`Supprimer définitivement cette sauvegarde ?\n\n• Fichier : ${backup.source_filename}\n• Jeu : ${backup.game_name}\n• Taille : ${formatSize(backup.size)}\n\nCette action est irréversible !`)) {
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
        alert(`Erreur : ${result.error}`);
      }
    } catch (err) {
      statusMessage = '❌ Erreur lors de la suppression';
      alert(`Erreur : ${err instanceof Error ? err.message : 'Erreur inconnue'}`);
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

<div class="h-full bg-gray-900 text-white flex flex-col">
  <!-- Header -->
  <div class="p-6 border-b border-gray-700">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-blue-400 mb-2">🗂️ Gestionnaire de Sauvegardes</h1>
        <p class="text-gray-400 text-sm">Gérez, restaurez et organisez toutes vos sauvegardes de fichiers RenExtract</p>
      </div>
      <button
        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2"
        onclick={refreshBackups}
        disabled={loading}
        title="Recharger la liste des sauvegardes"
      >
        {#if loading}
          <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
        {:else}
          🔄
        {/if}
        Recharger
      </button>
    </div>
  </div>

  <!-- Content -->
  <div class="flex-1 overflow-y-auto p-6">
    <!-- Statistiques -->
    <div class="bg-gray-800 rounded-lg p-6 mb-4">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-blue-400">📊 Statistiques des sauvegardes</h2>
        <div class="text-sm text-gray-400">
          <span class="text-green-400">●</span> Dernier scan: {formatLastScanTime()}
        </div>
      </div>
      <div class="grid grid-cols-3 gap-6">
        <div>
          <p class="text-gray-400 text-sm">Sauvegardes totales</p>
          <p class="text-2xl font-bold">{totalBackups}</p>
        </div>
        <div>
          <p class="text-gray-400 text-sm">Jeux concernés</p>
          <p class="text-2xl font-bold">{totalGames}</p>
        </div>
        <div>
          <p class="text-gray-400 text-sm">Taille totale</p>
          <p class="text-2xl font-bold text-blue-400">{formatSize(totalSize)}</p>
        </div>
      </div>
    </div>

    <!-- Filtres -->
    <div class="bg-gray-800 rounded-lg p-6 mb-4">
      <h2 class="text-lg font-semibold text-blue-400 mb-4">🔍 Filtres</h2>
      <div class="grid grid-cols-2 gap-6">
        <div>
          <label for="game-filter" class="block text-sm font-medium mb-2">🎮 Filtrer par jeu :</label>
          <select
            id="game-filter"
            bind:value={selectedGame}
            onchange={handleFilterChange}
            class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
          >
            {#each games as game}
              <option value={game}>{game}</option>
            {/each}
          </select>
        </div>
        <div>
          <label for="type-filter" class="block text-sm font-medium mb-2">🏷️ Filtrer par type :</label>
          <select
            id="type-filter"
            bind:value={selectedType}
            onchange={handleFilterChange}
            class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
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
    <div class="bg-gray-800 rounded-lg p-6">
      <h2 class="text-lg font-semibold text-blue-400 mb-4">📋 Liste des sauvegardes</h2>
      
      {#if loading}
        <div class="flex items-center justify-center py-12">
          <div class="w-10 h-10 border-4 border-gray-600 border-t-blue-500 rounded-full animate-spin"></div>
          <p class="ml-4 text-gray-400">Chargement...</p>
        </div>
      {:else if error}
        <div class="text-center py-12 text-red-400">
          <p>❌ {error}</p>
          <button
            class="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            onclick={loadBackups}
          >
            Réessayer
          </button>
        </div>
      {:else if filteredBackups.length === 0}
        <div class="text-center py-12 text-gray-400">
          <p>Aucune sauvegarde trouvée</p>
        </div>
      {:else}
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-700">
              <tr>
                <th class="px-4 py-3 text-left cursor-pointer hover:bg-gray-600" onclick={() => sortBy('game_name')}>
                  Jeu {sortColumn === 'game_name' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
                </th>
                <th class="px-4 py-3 text-left cursor-pointer hover:bg-gray-600" onclick={() => sortBy('source_filename')}>
                  Fichier {sortColumn === 'source_filename' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
                </th>
                <th class="px-4 py-3 text-left cursor-pointer hover:bg-gray-600" onclick={() => sortBy('type')}>
                  Type {sortColumn === 'type' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
                </th>
                <th class="px-4 py-3 text-left cursor-pointer hover:bg-gray-600" onclick={() => sortBy('created')}>
                  Date {sortColumn === 'created' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
                </th>
                <th class="px-4 py-3 text-left cursor-pointer hover:bg-gray-600" onclick={() => sortBy('size')}>
                  Taille {sortColumn === 'size' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
                </th>
                <th class="px-4 py-3 text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {#each filteredBackups as backup}
                <tr class="border-t border-gray-700 hover:bg-gray-750 transition-colors">
                  <td class="px-4 py-3">{backup.game_name}</td>
                  <td class="px-4 py-3">{backup.source_filename}</td>
                  <td class="px-4 py-3">{(BACKUP_DESCRIPTIONS as any)[backup.type] || backup.type}</td>
                  <td class="px-4 py-3">{formatDate(backup.created)}</td>
                  <td class="px-4 py-3">{formatSize(backup.size)}</td>
                  <td class="px-4 py-3 text-center">
                    <div class="flex items-center justify-center gap-2">
                      <button
                        class="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
                        onclick={() => restoreBackup(backup)}
                        title="Restaurer vers l'emplacement d'origine"
                      >
                        💾 Restaurer
                      </button>
                      <button
                        class="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition-colors"
                        onclick={() => restoreBackupTo(backup)}
                        title="Restaurer vers un chemin spécifique (comme asksaveasfilename)"
                      >
                        📄 Restaurer vers...
                      </button>
                      <button
                        class="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition-colors"
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
  <div class="p-4 border-t border-gray-700 bg-gray-800">
    <p class="text-sm text-gray-400">📊 État : {statusMessage}</p>
  </div>
</div>
