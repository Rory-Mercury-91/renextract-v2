<script lang="ts">
  import { apiService } from '$lib/api';
  import { onMount } from 'svelte';

  let wslInfo = $state<any>(null);
  let zenityInfo = $state<any>(null);
  let showInfo = $state(false);

  onMount(async () => {
    try {
      const [wslResult, zenityResult] = await Promise.all([
        apiService.getWslInfo(),
        apiService.checkZenity(),
      ]);

      if (wslResult.success && (wslResult.info as any)?.is_wsl) {
        wslInfo = wslResult.info;
        zenityInfo = zenityResult;
        showInfo = true;
      }
    } catch (error) {
      console.error('Erreur lors du chargement des infos WSL:', error);
    }
  });

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
</script>

{#if showInfo && wslInfo}
  <div
    class="mb-4 rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-900/20"
  >
    <div class="flex items-start justify-between">
      <div class="flex-1">
        <h3
          class="mb-2 flex items-center text-sm font-semibold text-blue-800 dark:text-blue-200"
        >
          🌐 Environnement WSL détecté
        </h3>

        <div class="mb-3 text-xs text-blue-700 dark:text-blue-300">
          <p><strong>Distribution:</strong> {wslInfo.distro}</p>
          <p><strong>Version:</strong> {wslInfo.version}</p>
        </div>

        {#if zenityInfo?.available}
          <div
            class="mb-2 flex items-center text-xs text-green-700 dark:text-green-300"
          >
            <span class="mr-1">✅</span>
            <span
              >zenity est installé ({zenityInfo.version}) - Dialogues graphiques
              disponibles</span
            >
          </div>
        {:else}
          <div class="mb-3">
            <div
              class="mb-2 flex items-center text-xs text-orange-700 dark:text-orange-300"
            >
              <span class="mr-1">⚠️</span>
              <span
                >zenity n'est pas installé - Dialogues graphiques non
                disponibles</span
              >
            </div>

            <button
              onclick={installZenity}
              class="rounded bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
            >
              📋 Copier la commande d'installation
            </button>
          </div>
        {/if}

        <div class="text-xs text-blue-600 dark:text-blue-400">
          <p class="mb-1"><strong>💡 Conseils pour WSL:</strong></p>
          <ul class="ml-4 list-disc space-y-1">
            <li>
              Les chemins Windows sont accessibles via /mnt/c/, /mnt/d/, etc.
            </li>
            <li>
              Vous pouvez saisir les chemins manuellement si zenity n'est pas
              installé
            </li>
            <li>
              Les dialogues de fichier fonctionneront avec des prompts texte
            </li>
          </ul>
        </div>
      </div>

      <button
        onclick={() => (showInfo = false)}
        class="ml-2 text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-200"
        title="Masquer cette information"
      >
        ✕
      </button>
    </div>
  </div>
{/if}
