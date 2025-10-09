<script lang="ts">
  import Header from '$components/Header.svelte';
  import Sidebar from '$components/Sidebar.svelte';
  import { apiService } from '$lib/api';
  import Backups from '$routes/Backups.svelte';
  import Extractor from '$routes/Extractor.svelte';
  import Generator from '$routes/Generator.svelte';
  import NotFound from '$routes/NotFound.svelte';
  import Settings from '$routes/Settings.svelte';
  import Tools from '$routes/Tools.svelte';
  import Translator from '$routes/Translator.svelte';
  import { onMount } from 'svelte';
  import { _, waitLocale } from 'svelte-i18n';
  import { Route, Router } from 'svelte5-router';
  import { appSettings } from './stores/app';

  let isLoading = $state(true);
  let error: string | null = $state(null);

  const url = $state(window.location.pathname);

  // Gestion du thème dark/light/auto
  const applyTheme = (theme: 'light' | 'dark' | 'auto') => {
    const root = document.documentElement;
    
    if (theme === 'dark') {
      root.setAttribute('data-theme', 'dark');
    } else if (theme === 'light') {
      root.setAttribute('data-theme', 'light');
    } else if (theme === 'auto') {
      // Mode automatique : détecter la préférence système
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      root.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    }
  };

  onMount(async () => {
    try {
      // Check API connection
      await apiService.healthCheck();
      await waitLocale();
      isLoading = false;
    } catch (err) {
      error = 'Unable to connect to Python backend';
      isLoading = true;
    }

    // Appliquer le thème initial
    applyTheme($appSettings.theme);
  });

  // Écouter les changements de préférence système en mode auto
  onMount(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleMediaChange = () => {
      if ($appSettings.theme === 'auto') {
        applyTheme('auto');
      }
    };
    
    mediaQuery.addEventListener('change', handleMediaChange);
    
    return () => {
      mediaQuery.removeEventListener('change', handleMediaChange);
    };
  });

  // Écouter les changements du paramètre theme
  $effect(() => {
    applyTheme($appSettings.theme);
  });
</script>

<Router {url}>
  {#if isLoading}
    <div class="flex flex-1 flex-col items-center justify-center gap-5">
      <div
        class="h-10 w-10 animate-spin rounded-full border-4 border-gray-300 border-t-blue-500 dark:border-gray-600"
      ></div>
      <p class="text-gray-600 dark:text-gray-400">
        {$_('app.loading') || 'Loading application...'}
      </p>
    </div>
  {:else if error}
    <div class="flex flex-1 items-center justify-center">
      <div
        class="max-w-md rounded-lg border border-red-300 bg-red-50 p-10 text-center text-red-700 dark:border-red-700 dark:bg-red-900 dark:text-red-300"
      >
        <h2 class="mb-2 text-xl font-semibold">
          {$_('app.connection_error') || 'Connection error'}
        </h2>
        <p class="mb-4">{error}</p>
        <button
          class="cursor-pointer rounded border-0 bg-red-600 px-5 py-2.5 text-white transition-colors hover:bg-red-700"
          onclick={() => window.location.reload()}
        >
          {$_('app.retry') || 'Retry'}
        </button>
      </div>
    </div>
  {:else}
    <div
      class="relative grid h-screen max-h-screen min-h-screen grid-rows-[5rem_1fr]"
    >
      <Header />

      <div class="relative flex h-[calc(100vh-5rem)]">
        <Sidebar />

        <div class="h-full max-h-full w-full overflow-y-auto">
          <Route path="/" component={Generator} />
          <Route path="/extract" component={Extractor} />
          {#if $appSettings.translatorFeature}
            <Route path="/translator" component={Translator} />
          {/if}
          <Route path="/tools" component={Tools} />
          <Route path="/backups" component={Backups} />
          <Route path="/settings" component={Settings} />
          <Route path="*" component={NotFound} />
        </div>
      </div>
    </div>
  {/if}
</Router>
