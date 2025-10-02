<script lang="ts">
  let activeSection = 'RenExtract';

  const sections = [
    { id: 'generator', name: 'Générateur', icon: '⚡', badge: null },
    { id: 'renextract', name: 'RenExtract', icon: '📄', badge: 5 },
    { id: 'tools', name: 'Outils spécialisés', icon: '🔧', badge: null },
    { id: 'backup', name: 'Sauvegarde', icon: '💾', badge: null },
    { id: 'settings', name: 'Paramètres', icon: '⚙️', badge: null }
  ];

  function selectSection(sectionId: string) {
    activeSection = sectionId;
  }
</script>

<aside class="w-64 bg-gray-800 text-white h-full flex flex-col">
  <nav class="flex-1 py-4">
    {#each sections as section}
      <button
        class="w-full flex items-center px-6 py-3 text-left hover:bg-gray-700 transition-colors relative"
        class:bg-blue-600={activeSection === section.id}
        class:hover:bg-blue-700={activeSection === section.id}
        onclick={() => selectSection(section.id)}
      >
        <span class="text-xl mr-3">{section.icon}</span>
        <span class="flex-1">{section.name}</span>
        {#if section.badge}
          <span class="bg-red-500 text-white text-xs px-2 py-1 rounded-full min-w-[20px] text-center">
            {section.badge}
          </span>
        {/if}
      </button>
    {/each}
  </nav>
</aside>

<style>
  aside {
    min-height: 100vh;
  }
</style>
