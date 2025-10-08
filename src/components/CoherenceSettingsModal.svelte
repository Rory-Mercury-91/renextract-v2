<script lang="ts">
  import Icon from '@iconify/svelte';
  import { appSettings } from '../stores/app';

  interface Props {
    showModal: boolean;
  }

  let { showModal = $bindable() }: Props = $props();

  // Copie locale des options de cohérence pour permettre l'annulation
  let localCoherenceOptions = $state({
    checkVariables: $appSettings.coherence?.checkVariables ?? true,
    checkTags: $appSettings.coherence?.checkTags ?? true,
    checkUntranslated: $appSettings.coherence?.checkUntranslated ?? true,
    checkEscapeSequences: $appSettings.coherence?.checkEscapeSequences ?? true,
    checkPercentages: $appSettings.coherence?.checkPercentages ?? true,
    checkQuotations: $appSettings.coherence?.checkQuotations ?? true,
    checkParentheses: $appSettings.coherence?.checkParentheses ?? true,
    checkSyntax: $appSettings.coherence?.checkSyntax ?? true,
    checkDeeplEllipsis: $appSettings.coherence?.checkDeeplEllipsis ?? true,
    checkIsolatedPercent: $appSettings.coherence?.checkIsolatedPercent ?? true,
    checkFrenchQuotes: $appSettings.coherence?.checkFrenchQuotes ?? true,
    checkDoubleDashEllipsis: $appSettings.coherence?.checkDoubleDashEllipsis ?? true,
    checkSpecialCodes: $appSettings.coherence?.checkSpecialCodes ?? false,
    checkLineStructure: $appSettings.coherence?.checkLineStructure ?? true,
    customExclusions: [...($appSettings.coherence?.customExclusions || ['OK', 'Menu', 'Continue', 'Yes', 'No', 'Level', '???', '!!!', '...'])],
  });

  interface CoherenceCheck {
    key: keyof typeof localCoherenceOptions;
    label: string;
    description: string;
    danger: '🔴' | '🟡' | '🟢';
  }

  const criticalChecks: CoherenceCheck[] = [
    {
      key: 'checkVariables',
      label: 'Variables [] incohérentes',
      description: 'Détecte les variables manquantes ou modifiées',
      danger: '🔴',
    },
    {
      key: 'checkTags',
      label: 'Balises {} incohérentes',
      description: 'Vérifie l\'équilibre des balises Ren\'Py',
      danger: '🔴',
    },
    {
      key: 'checkEscapeSequences',
      label: 'Séquences d\'échappement (\\n, \\t, \\r)',
      description: 'Vérifie les séquences d\'échappement',
      danger: '🔴',
    },
    {
      key: 'checkPercentages',
      label: 'Variables de formatage (%s, %d, %f)',
      description: 'Vérifie les variables de formatage Python',
      danger: '🔴',
    },
    {
      key: 'checkQuotations',
      label: 'Guillemets et échappements (")',
      description: 'Vérifie les guillemets échappés',
      danger: '🔴',
    },
    {
      key: 'checkIsolatedPercent',
      label: 'Pourcentages isolés (% → %%)',
      description: 'Détecte les % non doublés',
      danger: '🔴',
    },
    {
      key: 'checkSyntax',
      label: 'Syntaxe Ren\'Py',
      description: 'Vérifie indentation et structure',
      danger: '🔴',
    },
    {
      key: 'checkLineStructure',
      label: 'Structure des lignes old/new',
      description: 'Vérifie la structure des blocs translate',
      danger: '🔴',
    },
  ];

  const qualityChecks: CoherenceCheck[] = [
    {
      key: 'checkUntranslated',
      label: 'Lignes non traduites',
      description: 'Détecte les lignes identiques (oublis)',
      danger: '🟡',
    },
    {
      key: 'checkDeeplEllipsis',
      label: 'Ellipses DeepL ([...])',
      description: 'Détecte les ellipses DeepL',
      danger: '🟡',
    },
    {
      key: 'checkFrenchQuotes',
      label: 'Guillemets français («»)',
      description: 'Détecte les guillemets typographiques',
      danger: '🟡',
    },
    {
      key: 'checkParentheses',
      label: 'Parenthèses et crochets',
      description: 'Vérifie l\'équilibre des délimiteurs',
      danger: '🟡',
    },
  ];

  const minorChecks: CoherenceCheck[] = [
    {
      key: 'checkDoubleDashEllipsis',
      label: 'Ellipses (-- → ...)',
      description: 'Suggestion de style pour ellipses',
      danger: '🟢',
    },
    {
      key: 'checkSpecialCodes',
      label: 'Codes spéciaux',
      description: 'Détecte les patterns inhabituels',
      danger: '🟢',
    },
  ];

  function enableAll() {
    Object.keys(localCoherenceOptions).forEach((key) => {
      if (key !== 'customExclusions') {
        (localCoherenceOptions as any)[key] = true;
      }
    });
  }

  function enableRecommended() {
    // Activer tous sauf les mineurs
    criticalChecks.forEach((check) => {
      (localCoherenceOptions as any)[check.key] = true;
    });
    qualityChecks.forEach((check) => {
      (localCoherenceOptions as any)[check.key] = true;
    });
    // Désactiver les mineurs
    minorChecks.forEach((check) => {
      (localCoherenceOptions as any)[check.key] = false;
    });
  }

  function disableAll() {
    Object.keys(localCoherenceOptions).forEach((key) => {
      if (key !== 'customExclusions') {
        (localCoherenceOptions as any)[key] = false;
      }
    });
  }

  function saveSettings() {
    appSettings.update((settings) => ({
      ...settings,
      coherence: {
        ...localCoherenceOptions,
      },
    }));
    showModal = false;
  }

  function cancel() {
    // Réinitialiser les valeurs locales
    localCoherenceOptions = {
      checkVariables: $appSettings.coherence?.checkVariables ?? true,
      checkTags: $appSettings.coherence?.checkTags ?? true,
      checkUntranslated: $appSettings.coherence?.checkUntranslated ?? true,
      checkEscapeSequences: $appSettings.coherence?.checkEscapeSequences ?? true,
      checkPercentages: $appSettings.coherence?.checkPercentages ?? true,
      checkQuotations: $appSettings.coherence?.checkQuotations ?? true,
      checkParentheses: $appSettings.coherence?.checkParentheses ?? true,
      checkSyntax: $appSettings.coherence?.checkSyntax ?? true,
      checkDeeplEllipsis: $appSettings.coherence?.checkDeeplEllipsis ?? true,
      checkIsolatedPercent: $appSettings.coherence?.checkIsolatedPercent ?? true,
      checkFrenchQuotes: $appSettings.coherence?.checkFrenchQuotes ?? true,
      checkDoubleDashEllipsis: $appSettings.coherence?.checkDoubleDashEllipsis ?? true,
      checkSpecialCodes: $appSettings.coherence?.checkSpecialCodes ?? false,
      checkLineStructure: $appSettings.coherence?.checkLineStructure ?? true,
      customExclusions: [...($appSettings.coherence?.customExclusions || ['OK', 'Menu', 'Continue', 'Yes', 'No', 'Level', '???', '!!!', '...'])],
    };
    showModal = false;
  }

  // Gestion des exclusions personnalisées
  let exclusionsText = $state(($appSettings.coherence?.customExclusions || ['OK', 'Menu', 'Continue', 'Yes', 'No', 'Level', '???', '!!!', '...']).join(', '));
  
  function updateExclusions() {
    localCoherenceOptions.customExclusions = exclusionsText
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
  }
  
  // Mettre à jour exclusionsText quand la modal s'ouvre
  $effect(() => {
    if (showModal) {
      exclusionsText = localCoherenceOptions.customExclusions.join(', ');
    }
  });
</script>

{#if showModal}
  <!-- Modal backdrop -->
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    onclick={cancel}
    onkeydown={(e) => e.key === 'Escape' && cancel()}
    role="presentation"
    tabindex="-1"
  >
    <!-- Modal content -->
    <div
      class="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-lg bg-gray-800 shadow-xl"
      onclick={(e) => e.stopPropagation()}
      onkeydown={(e) => e.key === 'Escape' && cancel()}
      role="dialog"
      aria-labelledby="modal-title"
      tabindex="0"
    >
      <!-- Header -->
      <div class="sticky top-0 z-10 border-b border-gray-700 bg-gray-800 px-6 py-4">
        <div class="flex items-center justify-between">
          <h2 id="modal-title" class="text-xl font-bold text-white">
            ⚙️ Configuration des contrôles de cohérence
          </h2>
          <button
            onclick={cancel}
            class="rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-700 hover:text-white"
            aria-label="Fermer"
          >
            <Icon icon="hugeicons:cancel-01" class="h-6 w-6" />
          </button>
        </div>
        <p class="mt-2 text-sm text-gray-400">
          ℹ️ Pour les détails de chaque vérification, consultez : <code class="rounded bg-gray-700 px-1">docs/COHERENCE_COMPLETE.md</code>
        </p>
      </div>

      <!-- Content -->
      <div class="space-y-6 p-6">
        <!-- CRITIQUES -->
        <div>
          <h3 class="mb-3 text-lg font-semibold text-red-400">
            🔴 CRITIQUES (empêchent les crashs)
          </h3>
          <div class="space-y-2">
            {#each criticalChecks as check}
              <label class="flex items-start gap-3 rounded-lg bg-gray-700/50 p-3 transition-colors hover:bg-gray-700">
                <input
                  type="checkbox"
                  checked={localCoherenceOptions[check.key] as boolean}
                  onchange={(e) => {
                    const target = e.target as HTMLInputElement;
                    (localCoherenceOptions as any)[check.key] = target.checked;
                  }}
                  class="mt-1 h-5 w-5 rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-2 focus:ring-blue-500"
                />
                <div class="flex-1">
                  <div class="flex items-center gap-2">
                    <span class="text-sm">{check.danger}</span>
                    <span class="font-medium text-white">{check.label}</span>
                  </div>
                  <p class="text-xs text-gray-400">{check.description}</p>
                </div>
              </label>
            {/each}
          </div>
        </div>

        <!-- QUALITÉ -->
        <div>
          <h3 class="mb-3 text-lg font-semibold text-yellow-400">
            🟡 QUALITÉ (améliorent la traduction)
          </h3>
          <div class="space-y-2">
            {#each qualityChecks as check}
              <label class="flex items-start gap-3 rounded-lg bg-gray-700/50 p-3 transition-colors hover:bg-gray-700">
                <input
                  type="checkbox"
                  checked={localCoherenceOptions[check.key] as boolean}
                  onchange={(e) => {
                    const target = e.target as HTMLInputElement;
                    (localCoherenceOptions as any)[check.key] = target.checked;
                  }}
                  class="mt-1 h-5 w-5 rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-2 focus:ring-blue-500"
                />
                <div class="flex-1">
                  <div class="flex items-center gap-2">
                    <span class="text-sm">{check.danger}</span>
                    <span class="font-medium text-white">{check.label}</span>
                  </div>
                  <p class="text-xs text-gray-400">{check.description}</p>
                </div>
              </label>
            {/each}
          </div>
        </div>

        <!-- MINEURS -->
        <div>
          <h3 class="mb-3 text-lg font-semibold text-green-400">
            🟢 MINEURS (optionnels)
          </h3>
          <div class="space-y-2">
            {#each minorChecks as check}
              <label class="flex items-start gap-3 rounded-lg bg-gray-700/50 p-3 transition-colors hover:bg-gray-700">
                <input
                  type="checkbox"
                  checked={localCoherenceOptions[check.key] as boolean}
                  onchange={(e) => {
                    const target = e.target as HTMLInputElement;
                    (localCoherenceOptions as any)[check.key] = target.checked;
                  }}
                  class="mt-1 h-5 w-5 rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-2 focus:ring-blue-500"
                />
                <div class="flex-1">
                  <div class="flex items-center gap-2">
                    <span class="text-sm">{check.danger}</span>
                    <span class="font-medium text-white">{check.label}</span>
                  </div>
                  <p class="text-xs text-gray-400">{check.description}</p>
                </div>
              </label>
            {/each}
          </div>
        </div>

        <!-- Exclusions personnalisées -->
        <div>
          <h3 class="mb-3 text-lg font-semibold text-blue-400">
            📝 Exclusions personnalisées
          </h3>
          <div class="rounded-lg bg-gray-700/50 p-4">
            <label for="exclusions" class="mb-2 block text-sm font-medium text-gray-300">
              Mots à exclure de la détection "Lignes non traduites" (séparés par des virgules)
            </label>
            <input
              id="exclusions"
              type="text"
              bind:value={exclusionsText}
              oninput={updateExclusions}
              placeholder="OK, Menu, Continue, ???, !!!, ..."
              class="w-full rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
            />
            <p class="mt-2 text-xs text-gray-400">
              Exemples : mots internationaux (OK, Menu), patterns de ponctuation (???, !!!, ...)
            </p>
          </div>
        </div>

        <!-- Quick actions -->
        <div class="flex flex-wrap gap-3">
          <button
            onclick={enableAll}
            class="rounded-lg bg-green-600 px-4 py-2 text-white transition-colors hover:bg-green-700"
          >
            ✅ Tout activer
          </button>
          <button
            onclick={enableRecommended}
            class="rounded-lg bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700"
          >
            ⭐ Recommandé
          </button>
          <button
            onclick={disableAll}
            class="rounded-lg bg-gray-600 px-4 py-2 text-white transition-colors hover:bg-gray-700"
          >
            ❌ Tout désactiver
          </button>
        </div>
      </div>

      <!-- Footer -->
      <div class="sticky bottom-0 border-t border-gray-700 bg-gray-800 px-6 py-4">
        <div class="flex justify-end gap-3">
          <button
            onclick={cancel}
            class="rounded-lg bg-gray-600 px-6 py-2 text-white transition-colors hover:bg-gray-700"
          >
            Annuler
          </button>
          <button
            onclick={saveSettings}
            class="rounded-lg bg-blue-600 px-6 py-2 text-white transition-colors hover:bg-blue-700"
          >
            💾 Sauvegarder
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}
