<script lang="ts">
  import RouteHeader from '$components/RouteHeader.svelte';
  import axios from 'axios';
  import { _ } from 'svelte-i18n';

  let inputFolder = '';
  let recursive = true;
  let modelPath = 'virusf/nllb-renpy-rory-v4';
  let sourceLang = 'auto';
  let targetLang = 'fra_Latn';
  let running = false;
  let logs = '';
  let health: {
    success: boolean;
    exists: boolean;
    gitHead?: string | null;
  } | null = null;

  async function checkHealth() {
    try {
      const res = await axios.get('/api/translator/health');
      health = res.data;
    } catch (e) {
      health = { success: false, exists: false, gitHead: null } as any;
    }
  }

  async function runTranslation() {
    if (!inputFolder) return;
    running = true;
    logs = '';
    try {
      const res = await axios.post('/api/translator/run', {
        inputFolder,
        recursive,
        modelPath,
        sourceLang,
        targetLang,
      });
      logs = (res.data.stdout || '') + '\n' + (res.data.stderr || '');
    } catch (err: any) {
      const data = err?.response?.data;
      logs =
        (data?.stdout || '') +
        '\n' +
        (data?.stderr || '') +
        '\n' +
        (data?.error || err?.message || 'Erreur inconnue');
    } finally {
      running = false;
    }
  }

  checkHealth();
</script>

<section class="min-h-full flex flex-col text-white">
  <RouteHeader
    title={$_('navigation.translator')}
    description={$_('navigation.translator_description')}
    icon="hugeicons:tools"
    color="text-red-300"
  >
    <div class="text-sm text-gray-300 mr-6">
      <div class="flex justify-end">
        <button
          class="px-4 py-2 flex justify-center items-center font-bold bg-purple-400 hover:bg-purple-300 text-slate-800 rounded-lg transition-colors gap-2"
          onclick={checkHealth}
          title="Rafraîchir TranslationToolsIA"
        >
          Recharger
        </button>
      </div>

      <div>
        <span class="font-medium">Status:</span>
        {#if health}
          {#if health.success && health.exists}
            <span class="text-green-400">TranslationToolsIA détecté</span>
            {#if health.gitHead}
              <span class="ml-2 text-xs text-gray-400"
                >(HEAD {health.gitHead})</span
              >
            {/if}
          {:else}
            <span class="text-red-400"
              >Non installé. Exécutez "pnpm run ttia:clone"</span
            >
          {/if}
        {:else}
          <span class="text-gray-400">Vérification…</span>
        {/if}
      </div>
    </div>
  </RouteHeader>
  <div class="p-4 grid gap-4 max-w-3xl">
    <div class="grid gap-2">
      <label class="text-sm" for="inputFolder">Dossier du jeu Ren'Py</label>
      <input
        id="inputFolder"
        class="px-3 py-2 bg-gray-100 text-black rounded outline-none"
        placeholder="/chemin/vers/le/jeu"
        bind:value={inputFolder}
      />
    </div>

    <div class="grid gap-2 md:grid-cols-2">
      <div class="flex items-center gap-2">
        <input id="rec" type="checkbox" bind:checked={recursive} />
        <label for="rec">Inclure les sous-dossiers</label>
      </div>
      <div class="grid gap-2">
        <label class="text-sm" for="modelPath">Modèle</label>
        <input
          id="modelPath"
          class="px-3 py-2 bg-gray-100 text-black rounded outline-none"
          bind:value={modelPath}
        />
      </div>
    </div>

    <div class="grid gap-2 md:grid-cols-2">
      <div class="grid gap-2">
        <label class="text-sm" for="sourceLang"
          >Langue source (NLLB code ou auto)</label
        >
        <input
          id="sourceLang"
          class="px-3 py-2 bg-gray-100 text-black rounded outline-none"
          bind:value={sourceLang}
        />
      </div>
      <div class="grid gap-2">
        <label class="text-sm" for="targetLang">Langue cible (NLLB code)</label>
        <input
          id="targetLang"
          class="px-3 py-2 bg-gray-100 text-black rounded outline-none"
          bind:value={targetLang}
        />
      </div>
    </div>

    <div>
      <button
        class="px-4 py-2 rounded bg-red-500 hover:bg-red-400 disabled:opacity-50"
        disabled={running || !inputFolder}
        onclick={runTranslation}
      >
        {#if running}En cours…{:else}Lancer la traduction{/if}
      </button>
    </div>

    <div class="grid gap-2">
      <label class="text-sm" for="logs">Logs</label>
      <textarea
        id="logs"
        class="min-h-60 px-3 py-2 bg-gray-900 rounded outline-none font-mono text-xs"
        readonly>{logs}</textarea
      >
    </div>
  </div>
</section>
