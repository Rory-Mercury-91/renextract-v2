<script lang="ts">
  import { _ } from 'svelte-i18n';
  import { appActions, appState } from '../stores/app';

  const sections = [
    { link: '/', name: $_('navigation.generator'), icon: '⚡', badge: null },
    { link: '/renextract', name: $_('navigation.renextract'), icon: '📄', badge: 3 },
    { link: '/tools', name: $_('navigation.tools'), icon: '🔧', badge: null },
    { link: '/backup', name: $_('navigation.backup'), icon: '💾', badge: null },
    { link: '/settings', name: $_('navigation.settings'), icon: '⚙️', badge: null }
  ];

  function selectSection(sectionId: string) {
    appActions.setCurrentSection(sectionId);
    activeSection = sectionId;
  }

  $: activeSection = $appState.currentSection;
</script>

<aside class="w-64 bg-gray-800 text-white h-full flex flex-col">
  <!-- Logo plus grand -->
  <div class="p-6 border-b border-gray-700 flex justify-center">
    <img src="/public/assets/logo.webp" alt="Logo RenExtract" class="w-24 h-24 object-contain" />
  </div>

  <nav class="flex-1 py-4">
    {#each sections as section}
      <a
        href={section.link}
        class="w-full flex items-center px-6 py-3 text-left hover:bg-gray-700 transition-colors relative"
        class:bg-blue-600={location.pathname === section.link}
        class:hover:bg-blue-700={location.pathname === section.link}
      >
        <span class="text-xl mr-3">{section.icon}</span>
        <span class="flex-1">{section.name}</span>
        {#if section.badge}
          <span class="bg-red-500 text-white text-xs px-2 py-1 rounded-full min-w-[20px] text-center">
            {section.badge}
          </span>
        {/if}
      </a>
    {/each}
  </nav>
</aside>

<style>
  aside {
    min-height: 100vh;
  }
</style>
