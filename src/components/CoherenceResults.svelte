<!-- src/components/CoherenceResults.svelte -->
<script lang="ts">
  import type { CoherenceResultSvelte } from '$lib/api';
  import Icon from '@iconify/svelte';
  import { onMount } from 'svelte';

  // Types
  type CoherenceIssue = CoherenceResultSvelte['issues_by_file'][string][0];

  interface Props {
    result: CoherenceResultSvelte;
    onOpenInEditor?: (filePath: string, lineNumber: number) => void;
    selectedLanguage: string;
  }

  const { result, onOpenInEditor = () => {}, selectedLanguage = 'Inconnue' }: Props = $props();
  
  console.log('🔍 CoherenceResults - Composant monté avec result:', result);

  // État local avec $state (Svelte 5)
  let expandedSections = $state<Set<string>>(new Set());
  let expandedFiles = $state<Set<string>>(new Set());
  let filterType = $state<string>('all');
  let searchTerm = $state<string>('');

  // Calculs simplifiés avec $derived
  const issuesByType = $derived(() => {
    console.log('🔍 Debug CoherenceResults - Début du calcul issuesByType');
    
    // Vérification de sécurité
    if (!result || !result.issues_by_file || typeof result.issues_by_file !== 'object') {
      console.warn('⚠️ issues_by_file is not valid:', result?.issues_by_file);
      return {};
    }
    
    const grouped: Record<string, CoherenceIssue[]> = {};
    const allIssues = Object.values(result.issues_by_file).flat();

    console.log('🔍 Debug CoherenceResults:', {
      totalIssues: result.stats.total_issues,
      issuesByFileKeys: Object.keys(result.issues_by_file),
      allIssuesLength: allIssues.length,
      firstIssue: allIssues[0]
    });

    allIssues.forEach((issue: CoherenceIssue) => {
      if (issue && issue.type) {
        if (!grouped[issue.type]) {
          grouped[issue.type] = [];
        }
        grouped[issue.type].push(issue);
      } else {
        console.warn('⚠️ Issue invalide:', issue);
      }
    });

    console.log('🔍 Grouped issues:', grouped);
    return grouped;
  });

         const filteredIssuesByType = $derived(() => {
           console.log('🔍 Calcul filteredIssuesByType avec filterType:', filterType);
           if (filterType === 'all') {
             return issuesByType();
           } else {
             return Object.fromEntries(
               Object.entries(issuesByType()).filter(([type]) => type === filterType)
             );
           }
         });

         const searchFilteredIssues = $derived(() => {
           console.log('🔍 Calcul searchFilteredIssues avec searchTerm:', searchTerm);
           if (!searchTerm.trim()) {
             return filteredIssuesByType();
           } else {
             const filtered: Record<string, CoherenceIssue[]> = {};
             const searchLower = searchTerm.toLowerCase();

             Object.entries(filteredIssuesByType()).forEach(([type, issues]) => {
               const matchingIssues = issues.filter(
                 (issue: CoherenceIssue) =>
                   issue.message.toLowerCase().includes(searchLower) ||
                   issue.file.toLowerCase().includes(searchLower) ||
                   (issue.old_content &&
                     issue.old_content.toLowerCase().includes(searchLower)) ||
                   (issue.new_content &&
                     issue.new_content.toLowerCase().includes(searchLower))
               );

               if (matchingIssues.length > 0) {
                 filtered[type] = matchingIssues;
               }
             });

             return filtered;
           }
         });

         const searchFilteredEntries = $derived(() => {
           const entries = Object.entries(searchFilteredIssues());
           console.log('🔍 searchFilteredEntries:', entries);
           return entries;
         });

  // Fonctions utilitaires
  function toggleSection(type: string) {
    if (expandedSections.has(type)) {
      expandedSections.delete(type);
    } else {
      expandedSections.add(type);
    }
    expandedSections = new Set(expandedSections);
  }

  function toggleFile(filePath: string) {
    if (expandedFiles.has(filePath)) {
      expandedFiles.delete(filePath);
    } else {
      expandedFiles.add(filePath);
    }
    expandedFiles = new Set(expandedFiles);
  }

  function getIssueTypeColor(type: string): string {
    const colors: Record<string, string> = {
      // Variables
      variable_missing: 'bg-pink-500',
      variable_extra: 'bg-pink-500',
      variable_mismatch: 'bg-pink-500',
      // Tags
      tag_missing: 'bg-orange-500',
      tag_extra: 'bg-orange-500',
      tag_mismatch: 'bg-orange-500',
      tag_count_mismatch: 'bg-orange-500',
      tags_unbalanced: 'bg-orange-500',
      // Placeholders
      placeholder_missing: 'bg-purple-500',
      placeholder_extra: 'bg-purple-500',
      // Non traduit
      untranslated: 'bg-yellow-500',
      // Spéciaux
      deepl_ellipsis: 'bg-red-500',
      french_quotes: 'bg-red-500',
      escape_sequence: 'bg-red-500',
      percentage: 'bg-red-500',
      parentheses: 'bg-red-500',
      // Autres
      line_structure: 'bg-gray-500',
      analysis_error: 'bg-gray-500',
    };
    return colors[type] || 'bg-gray-500';
  }

  function getIssueTypeLabel(type: string): string {
    const labels: Record<string, string> = {
      variable_missing: 'Variables manquantes',
      variable_extra: 'Variables en trop',
      variable_mismatch: 'Variables incohérentes',
      tag_missing: 'Tags manquants',
      tag_extra: 'Tags en trop',
      tag_mismatch: 'Tags incohérents',
      tag_count_mismatch: 'Nombre de tags différent',
      tags_unbalanced: 'Balises déséquilibrées',
      placeholder_missing: 'Placeholders manquants',
      placeholder_extra: 'Placeholders en trop',
      untranslated: 'Lignes non traduites',
      deepl_ellipsis: 'Ellipses DeepL',
      french_quotes: 'Guillemets français',
      escape_sequence: "Séquences d'échappement",
      percentage: 'Problèmes de pourcentage',
      parentheses: 'Parenthèses déséquilibrées',
      line_structure: 'Structure de ligne',
      analysis_error: "Erreur d'analyse",
    };
    return labels[type] || type;
  }

  function formatFilePath(filePath: string): string {
    return filePath.split('/').pop() || filePath;
  }

         // Variables pour forcer l'exécution des $derived
         let debugIssuesByType = $derived(issuesByType());
         let debugFilteredIssuesByType = $derived(filteredIssuesByType());
         let debugSearchFilteredIssues = $derived(searchFilteredIssues());
         let debugSearchFilteredEntries = $derived(searchFilteredEntries());

         // Forcer l'exécution avec $effect
         $effect(() => {
           console.log('🔍 $effect - issuesByType:', issuesByType());
           console.log('🔍 $effect - filteredIssuesByType:', filteredIssuesByType());
           console.log('🔍 $effect - searchFilteredIssues:', searchFilteredIssues());
           console.log('🔍 $effect - searchFilteredEntries:', searchFilteredEntries());
         });

         // Ouvrir automatiquement la première section s'il y a des erreurs
         onMount(() => {
           if (result.stats.total_issues > 0) {
             const firstType = searchFilteredEntries()[0]?.[0];
             if (firstType) {
               expandedSections.add(firstType);
               expandedSections = new Set(expandedSections);
             }
           }
         });
</script>

<div class="flex flex-col gap-6">
  <!-- Header avec informations du projet -->
  <div class="rounded-lg border border-gray-700 bg-gray-800 p-6">
    <div class="mb-4 flex items-center justify-between">
      <h2 class="flex items-center gap-2 text-xl font-bold text-white">
        <Icon icon="hugeicons:chart-bar" class="h-6 w-6" />
        Rapport de Cohérence
      </h2>
    </div>

    <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
      <div class="flex items-center gap-2 text-sm text-gray-300">
        <Icon icon="hugeicons:folder" class="h-4 w-4" />
        <span>Projet: {result.target_path.split('/').pop() || 'Inconnu'}</span>
      </div>
      <div class="flex items-center gap-2 text-sm text-gray-300">
        <Icon icon="hugeicons:globe" class="h-4 w-4" />
        <span>Langue: {selectedLanguage}</span>
      </div>
      <div class="flex items-center gap-2 text-sm text-gray-300">
        <Icon icon="hugeicons:calendar" class="h-4 w-4" />
        <span>Généré: {new Date().toLocaleString('fr-FR')}</span>
      </div>
    </div>
  </div>

  <!-- Statistiques générales -->
  <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
    <div class="rounded-lg border border-gray-700 bg-gray-800 p-6">
      <div class="flex items-center gap-2 text-gray-300">
        <Icon icon="hugeicons:alert-triangle" class="h-5 w-5" />
        <span class="text-sm">Problèmes totaux</span>
      </div>
      <div class="mt-2 text-2xl font-bold text-white">
        {result.stats.total_issues}
      </div>
    </div>

    <div class="rounded-lg border border-gray-700 bg-gray-800 p-6">
      <div class="flex items-center gap-2 text-gray-300">
        <Icon icon="hugeicons:file-document" class="h-5 w-5" />
        <span class="text-sm">Fichiers analysés</span>
      </div>
      <div class="mt-2 text-2xl font-bold text-white">
        {result.stats.files_analyzed}
      </div>
    </div>

    <div class="rounded-lg border border-gray-700 bg-gray-800 p-6">
      <div class="flex items-center gap-2 text-gray-300">
        <Icon icon="hugeicons:tag" class="h-5 w-5" />
        <span class="text-sm">Types d'erreurs</span>
      </div>
      <div class="mt-2 text-2xl font-bold text-white">
        {Object.keys(result.stats.issues_by_type).length}
      </div>
    </div>
  </div>

  <!-- Message de succès si aucun problème -->
  {#if result.stats.total_issues === 0}
    <div
      class="rounded-lg border border-green-600 bg-green-900/20 p-8 text-center"
    >
      <Icon
        icon="hugeicons:checkmark-circle"
        class="mx-auto h-16 w-16 text-green-500"
      />
      <h3 class="mt-4 text-xl font-bold text-green-400">
        🎉 Aucun problème détecté !
      </h3>
      <p class="mt-2 text-green-300">Votre traduction est parfaite !</p>
    </div>
  {:else}
    <!-- Filtres et recherche -->
    <div class="rounded-lg border border-gray-700 bg-gray-800 p-4">
      <div class="flex flex-col gap-4 md:flex-row md:items-center">
        <div class="flex-1">
          <input
            bind:value={searchTerm}
            type="text"
            placeholder="Rechercher dans les problèmes..."
            class="w-full rounded-lg border border-gray-600 bg-gray-700 px-4 py-2 text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none"
          />
        </div>
        <div class="flex gap-2">
          <select
            bind:value={filterType}
            class="rounded-lg border border-gray-600 bg-gray-700 px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
          >
            <option value="all">Tous les types</option>
            {#each Object.keys(result.stats.issues_by_type) as type}
              <option value={type}>{getIssueTypeLabel(type)}</option>
            {/each}
          </select>
        </div>
      </div>
    </div>


           <!-- Debug pour forcer l'exécution des $derived -->
           {console.log('🔍 Template - debugIssuesByType:', debugIssuesByType)}
           {console.log('🔍 Template - debugFilteredIssuesByType:', debugFilteredIssuesByType)}
           {console.log('🔍 Template - debugSearchFilteredIssues:', debugSearchFilteredIssues)}
           {console.log('🔍 Template - debugSearchFilteredEntries:', debugSearchFilteredEntries)}
    
    <!-- Sections par type d'erreur -->
    {#each debugSearchFilteredEntries as [type, issues]}
      {@const isExpanded = expandedSections.has(type)}
      {@const typeCount = issues.length}
      {@const percentage = (typeCount / result.stats.total_issues) * 100}

      <div
        class="overflow-hidden rounded-lg border border-gray-700 bg-gray-800"
      >
        <button
          onclick={() => toggleSection(type)}
          class="w-full bg-gray-700 p-4 text-left transition-colors hover:bg-gray-600"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <span
                class="rounded-full px-3 py-1 text-xs font-bold text-white {getIssueTypeColor(
                  type
                )}"
              >
                {typeCount}
              </span>
              <span class="font-semibold text-white">
                {getIssueTypeLabel(type)}
              </span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-400">
                {percentage.toFixed(1)}% du total
              </span>
              <Icon
                icon="hugeicons:arrow-down"
                class="h-4 w-4 text-gray-400 transition-transform {isExpanded
                  ? 'rotate-180'
                  : ''}"
              />
            </div>
          </div>
        </button>

        {#if isExpanded}
          <div class="border-t border-gray-700">
            {#each Object.entries(issues.reduce((acc: Record<string, CoherenceIssue[]>, issue: CoherenceIssue) => {
                if (!acc[issue.file]) acc[issue.file] = [];
                acc[issue.file].push(issue);
                return acc;
              }, {} as Record<string, CoherenceIssue[]>)) as [filePath, fileIssues]}
              {@const isFileExpanded = expandedFiles.has(filePath)}

              <div class="border-b border-gray-700 last:border-b-0">
                <button
                  onclick={() => toggleFile(filePath)}
                  class="bg-gray-750 hover:bg-gray-650 w-full p-3 text-left transition-colors"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <Icon
                        icon="hugeicons:file-document"
                        class="h-4 w-4 text-gray-400"
                      />
                      <span class="font-medium text-gray-200">
                        {formatFilePath(filePath)}
                      </span>
                      <span
                        class="rounded-full bg-gray-600 px-2 py-1 text-xs text-gray-300"
                      >
                        {(fileIssues as CoherenceIssue[]).length} problème{(
                          fileIssues as CoherenceIssue[]
                        ).length > 1
                          ? 's'
                          : ''}
                      </span>
                    </div>
                    <Icon
                      icon="hugeicons:arrow-down"
                      class="h-4 w-4 text-gray-400 transition-transform {isFileExpanded
                        ? 'rotate-180'
                        : ''}"
                    />
                  </div>
                </button>

                {#if isFileExpanded}
                  <div class="bg-gray-900">
                    {#each fileIssues as CoherenceIssue[] as issue}
                      <div class="border-b border-gray-800 p-4 last:border-b-0">
                        <div class="mb-3 flex items-center justify-between">
                          <h4 class="font-semibold text-yellow-400">
                            Ligne {issue.line_number}
                          </h4>
                          <button
                            onclick={() =>
                              onOpenInEditor(issue.file, issue.line_number)}
                            class="flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-1 text-xs text-white transition-colors hover:bg-blue-700"
                          >
                            <Icon
                              icon="hugeicons:external-link"
                              class="h-3 w-3"
                            />
                            Ouvrir dans l'éditeur
                          </button>
                        </div>

                        <p class="mb-3 text-gray-300">
                          {issue.message}
                        </p>

                        {#if issue.old_content || issue.new_content}
                          <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
                            {#if issue.old_content}
                              <div
                                class="rounded-lg border-l-4 border-red-500 bg-red-900/20 p-3"
                              >
                                <div
                                  class="mb-2 text-xs font-bold uppercase text-red-400"
                                >
                                  Original
                                </div>
                                <div class="font-mono text-sm text-gray-300">
                                  {issue.old_content}
                                </div>
                              </div>
                            {/if}

                            {#if issue.new_content}
                              <div
                                class="rounded-lg border-l-4 border-green-500 bg-green-900/20 p-3"
                              >
                                <div
                                  class="mb-2 text-xs font-bold uppercase text-green-400"
                                >
                                  Traduit
                                </div>
                                <div class="font-mono text-sm text-gray-300">
                                  {issue.new_content}
                                </div>
                              </div>
                            {/if}
                          </div>
                        {/if}
                      </div>
                    {/each}
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/each}
  {/if}
</div>

<style>
  .bg-gray-750 {
    background-color: rgb(55 65 81);
  }
  .bg-gray-650 {
    background-color: rgb(75 85 99);
  }
</style>
