<script lang="ts">
  import Icon from '@iconify/svelte';
  import { _ } from 'svelte-i18n';
  import { appSettings } from '../stores/app';
  import CoherenceSettingsModal from './CoherenceSettingsModal.svelte';

  let showCoherenceModal = $state(false);
  let showHelpModal = $state(false);

  // Génération des aperçus de patterns
  function generatePreview(pattern: string): string {
    try {
      // Détection du format et génération de 3 exemples
      if (/\d{3}$/.test(pattern)) {
        // Format avec 3 chiffres (ex: CODE_001)
        const base = pattern.replace(/\d{3}$/, '');
        const num = parseInt(pattern.match(/\d{3}$/)?.[0] || '1');
        return `${pattern} → ${base}${String(num + 1).padStart(3, '0')} → ${base}${String(num + 2).padStart(3, '0')}`;
      } else if (/\(\d+\)$/.test(pattern)) {
        // Format avec parenthèses (ex: (01))
        const match = pattern.match(/\((\d+)\)$/);
        const num = parseInt(match?.[1] || '1');
        const base = pattern.replace(/\(\d+\)$/, '');
        return `${pattern} → ${base}(${String(num + 1).padStart(2, '0')}) → ${base}(${String(num + 2).padStart(2, '0')})`;
      } else {
        // Format simple, ajouter des suffixes
        return `${pattern} → ${pattern}_1 → ${pattern}_2`;
      }
    } catch {
      return $_('settings_extract.help_invalid');
    }
  }

  const codePreview = $derived(
    generatePreview($appSettings.extraction.patterns?.code || 'RENPY_CODE_001')
  );
  const asteriskPreview = $derived(
    generatePreview(
      $appSettings.extraction.patterns?.asterisk || 'RENPY_ASTERISK_001'
    )
  );
  const tildePreview = $derived(
    generatePreview(
      $appSettings.extraction.patterns?.tilde || 'RENPY_TILDE_001'
    )
  );

  function resetPatterns() {
    appSettings.update(settings => ({
      ...settings,
      extraction: {
        ...settings.extraction,
        patterns: {
          code: 'RENPY_CODE_001',
          asterisk: 'RENPY_ASTERISK_001',
          tilde: 'RENPY_TILDE_001',
        },
      },
    }));
  }

  function testPatterns() {
    const patterns = $appSettings.extraction?.patterns || {
      code: 'RENPY_CODE_001',
      asterisk: 'RENPY_ASTERISK_001',
      tilde: 'RENPY_TILDE_001',
    };

    const results = [
      `🔤 Codes/Variables:\n  ${generatePreview(patterns.code)}`,
      `⭐ Astérisques:\n  ${generatePreview(patterns.asterisk)}`,
      `〰️ Tildes:\n  ${generatePreview(patterns.tilde)}`,
    ].join('\n\n');

    window.alert(`Test des patterns\n\n${results}`);
  }

  function validateLineLimit() {
    const limit = $appSettings.extraction?.lineLimit || 1000;
    if (limit < 100) {
      return {
        valid: false,
        message: '⚠️ Valeur très basse (< 100). Recommandé: 500-2000',
      };
    } else if (limit > 10000) {
      return {
        valid: false,
        message: '⚠️ Valeur très haute (> 10000). Recommandé: 500-2000',
      };
    }
    return { valid: true, message: '' };
  }

  const lineLimitValidation = $derived(validateLineLimit());
</script>

<!-- Modal de configuration de cohérence -->
<CoherenceSettingsModal bind:showModal={showCoherenceModal} />

<!-- Modal d'aide -->
{#if showHelpModal}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    onclick={() => (showHelpModal = false)}
    onkeydown={e => e.key === 'Escape' && (showHelpModal = false)}
    role="presentation"
    tabindex="-1"
  >
    <div
      class="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-lg bg-gray-800 p-6 shadow-xl"
      onclick={e => e.stopPropagation()}
      onkeydown={e => e.key === 'Escape' && (showHelpModal = false)}
      role="dialog"
      tabindex="0"
    >
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-2xl font-bold text-white">
          🛡️ Protection Automatique du Contenu
        </h2>
        <button
          onclick={() => (showHelpModal = false)}
          class="rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-700 hover:text-white"
        >
          <Icon icon="hugeicons:cancel-01" class="h-6 w-6" />
        </button>
      </div>

      <div class="space-y-4 text-gray-300">
        <p>Lors de l'extraction, RenExtract protège automatiquement :</p>

        <div class="space-y-3">
          <div class="rounded-lg bg-gray-700/50 p-3">
            <h3 class="font-semibold text-blue-400">1️⃣ Codes Ren'Py</h3>
            <p class="text-sm">
              {'{i}'}, {'{b}'}, {'{color=...}'}, etc.<br />
              → Remplacés par des placeholders (ex: (01), (02), ...)<br />
              → Évite que DeepL ne les supprime ou modifie
            </p>
          </div>

          <div class="rounded-lg bg-gray-700/50 p-3">
            <h3 class="font-semibold text-blue-400">2️⃣ Variables</h3>
            <p class="text-sm">
              [player_name], [girl_name], etc.<br />
              → Protégées pour préserver la fonctionnalité du jeu
            </p>
          </div>

          <div class="rounded-lg bg-gray-700/50 p-3">
            <h3 class="font-semibold text-blue-400">3️⃣ Astérisques (*)</h3>
            <p class="text-sm">
              Lignes spéciales marquées par *<br />
              → Extraites dans un fichier séparé (_asterix.txt)
            </p>
          </div>

          <div class="rounded-lg bg-gray-700/50 p-3">
            <h3 class="font-semibold text-blue-400">4️⃣ Tildes (~)</h3>
            <p class="text-sm">
              Lignes spéciales marquées par ~<br />
              → Extraites dans le fichier astérisques
            </p>
          </div>
        </div>

        <div class="rounded-lg bg-blue-900/30 p-4">
          <h3 class="mb-2 font-semibold text-blue-400">🎯 POURQUOI ?</h3>
          <p class="text-sm">
            DeepL et autres traducteurs peuvent :<br />
            • Supprimer les balises qu'ils ne reconnaissent pas<br />
            • Modifier les variables<br />
            • Corriger la "syntaxe" en cassant le code Ren'Py<br /><br />
            La protection garantit que seul le TEXTE est traduit, pas la STRUCTURE
            du code !
          </p>
        </div>

        <div class="rounded-lg bg-purple-900/30 p-4">
          <h3 class="mb-2 font-semibold text-purple-400">
            📝 PERSONNALISATION
          </h3>
          <p class="text-sm">
            Vous pouvez modifier les patterns de protection :<br />
            • (01), (02), (03)... → Court, lisible<br />
            • RENPY_CODE_001, RENPY_CODE_002... → Descriptif, explicite<br />
            • Votre propre format !<br /><br />
            L'aperçu vous montre comment ils s'incrémentent.
          </p>
        </div>
      </div>

      <div class="mt-6 flex justify-end">
        <button
          onclick={() => (showHelpModal = false)}
          class="rounded-lg bg-blue-600 px-6 py-2 text-white transition-colors hover:bg-blue-700"
        >
          Compris !
        </button>
      </div>
    </div>
  </div>
{/if}

{#if $appSettings.extraction?.patterns && $appSettings.coherence}
  <div class="space-y-8">
    <!-- Header with help button -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-xl font-semibold text-white">
          {$_('settings_extract.title')}
        </h3>
        <p class="text-sm text-gray-400">
          {$_('settings_extract.description')}
        </p>
      </div>
      <button
        onclick={() => (showHelpModal = true)}
        class="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700"
      >
        <Icon icon="hugeicons:question" class="h-5 w-5" />
        <span>{$_('coherence.what_is_this')}</span>
      </button>
    </div>

    <!-- Options de protection -->
    <div class="space-y-4">
      <h4 class="text-lg font-semibold text-blue-400">
        🔧 {$_('settings_extract.protection_options')}
      </h4>

      <div class="flex flex-wrap gap-6">
        <label class="flex items-center gap-3">
          <input
            type="checkbox"
            bind:checked={$appSettings.extraction.detectDuplicates}
            class="h-5 w-5 rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-2 focus:ring-blue-500"
          />
          <span class="text-white">{$_('settings_extract.detect_duplicates')}</span>
        </label>

        <label class="flex items-center gap-3">
          <input
            type="checkbox"
            bind:checked={$appSettings.extraction.projectProgressTracking}
            class="h-5 w-5 rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-2 focus:ring-blue-500"
          />
          <span class="text-white">📊 {$_('settings_extract.project_progress')}</span>
        </label>
      </div>
    </div>

    <!-- Contrôles et limite -->
    <div class="flex flex-wrap items-end gap-6">
      <div>
        <button
          onclick={() => (showCoherenceModal = true)}
          class="flex items-center gap-2 rounded-lg bg-gray-600 px-4 py-2 text-white transition-colors hover:bg-gray-700"
        >
          <Icon icon="hugeicons:settings-01" class="h-5 w-5" />
          <span>{$_('settings_extract.configure_controls')}</span>
        </button>
      </div>

      <div class="flex items-center gap-3">
        <label for="line-limit" class="text-white"
          >{$_('settings_extract.file_limit')}</label
        >
        <input
          id="line-limit"
          type="number"
          bind:value={$appSettings.extraction.lineLimit}
          min="100"
          max="100000"
          class="w-24 rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
          class:border-red-500={!lineLimitValidation.valid &&
            $appSettings.extraction.lineLimit < 100}
          class:border-yellow-500={!lineLimitValidation.valid &&
            $appSettings.extraction.lineLimit > 10000}
        />
        <span class="text-white">{$_('settings_extract.lines')}</span>
      </div>
    </div>

    {#if !lineLimitValidation.valid}
      <p
        class="text-sm"
        class:text-red-400={$appSettings.extraction.lineLimit < 100}
        class:text-yellow-400={$appSettings.extraction.lineLimit > 10000}
      >
        {lineLimitValidation.message}
      </p>
    {/if}

    <!-- Mode de sauvegarde -->
    <div class="flex items-center gap-4">
      <label for="save-mode" class="text-white"
        >{$_('settings_extract.save_mode_default')}</label
      >
      <select
        id="save-mode"
        bind:value={$appSettings.extraction.defaultSaveMode}
        class="rounded-lg border border-gray-600 bg-gray-800 px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
      >
        <option value="new_file">{$_('settings_extract.create_new_file')}</option>
        <option value="overwrite">{$_('settings_extract.overwrite_original')}</option>
      </select>
    </div>

    <!-- Patterns de protection -->
    <div class="space-y-6">
      <h4 class="text-lg font-semibold text-blue-400">
        {$_('settings_extract.custom_patterns')}
      </h4>

      <!-- Codes/Variables -->
      <div class="space-y-2">
        <label for="code-pattern" class="block font-medium text-white"
          >{$_('settings_extract.codes_variables')}</label
        >
        <div class="flex items-center gap-4">
          <input
            id="code-pattern"
            type="text"
            bind:value={$appSettings.extraction.patterns.code}
            placeholder="RENPY_CODE_001"
            class="w-64 rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-center font-mono text-white focus:border-blue-500 focus:outline-none"
          />
          <div
            class="flex-1 rounded-lg bg-gray-700/50 px-4 py-2 font-mono text-sm text-gray-300"
          >
            {$_('settings_extract.preview')} {codePreview}
          </div>
        </div>
      </div>

      <!-- Astérisques -->
      <div class="space-y-2">
        <label for="asterisk-pattern" class="block font-medium text-white"
          >{$_('settings_extract.asterisks')}</label
        >
        <div class="flex items-center gap-4">
          <input
            id="asterisk-pattern"
            type="text"
            bind:value={$appSettings.extraction.patterns.asterisk}
            placeholder="RENPY_ASTERISK_001"
            class="w-64 rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-center font-mono text-white focus:border-blue-500 focus:outline-none"
          />
          <div
            class="flex-1 rounded-lg bg-gray-700/50 px-4 py-2 font-mono text-sm text-gray-300"
          >
            {$_('settings_extract.preview')} {asteriskPreview}
          </div>
        </div>
      </div>

      <!-- Tildes -->
      <div class="space-y-2">
        <label for="tilde-pattern" class="block font-medium text-white"
          >{$_('settings_extract.tildes')}</label
        >
        <div class="flex items-center gap-4">
          <input
            id="tilde-pattern"
            type="text"
            bind:value={$appSettings.extraction.patterns.tilde}
            placeholder="RENPY_TILDE_001"
            class="w-64 rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-center font-mono text-white focus:border-blue-500 focus:outline-none"
          />
          <div
            class="flex-1 rounded-lg bg-gray-700/50 px-4 py-2 font-mono text-sm text-gray-300"
          >
            {$_('settings_extract.preview')} {tildePreview}
          </div>
        </div>
      </div>

      <!-- Boutons d'action -->
      <div class="flex gap-3">
        <button
          onclick={resetPatterns}
          class="flex items-center gap-2 rounded-lg bg-gray-600 px-4 py-2 text-white transition-colors hover:bg-gray-700"
        >
          <Icon icon="hugeicons:refresh" class="h-5 w-5" />
          <span>{$_('settings_extract.reset_patterns')}</span>
        </button>
        <button
          onclick={testPatterns}
          class="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700"
        >
          <Icon icon="hugeicons:test-tube" class="h-5 w-5" />
          <span>{$_('settings_extract.test_patterns')}</span>
        </button>
      </div>
    </div>
  </div>
{:else}
  <div class="flex h-64 items-center justify-center">
    <div class="text-center">
      <p class="text-gray-400">Chargement des paramètres...</p>
    </div>
  </div>
{/if}
