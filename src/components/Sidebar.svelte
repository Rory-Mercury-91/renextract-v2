<script lang="ts">
  import Icon from '@iconify/svelte';
  import { _ } from 'svelte-i18n';
  import { Link } from 'svelte5-router';

  let isOpen = $state(false);

  interface Section {
    link: string;
    name: string;
    icon: string;
  }

  const sections: Section[] = [
    { link: '/', name: $_('navigation.generator'), icon: '⚡' },
    { link: '/extract', name: $_('navigation.extract'), icon: '📄' },
    { link: '/tools', name: $_('navigation.tools'), icon: '🔧' },
    { link: '/backups', name: $_('navigation.backup'), icon: '💾' },
    { link: '/settings', name: $_('navigation.settings'), icon: '⚙️' },
  ];
</script>

<aside
  class="max-w-64 bg-gray-800 text-white h-full flex flex-col border-r border-gray-700"
  class:lg:w-64={!isOpen}
>
  <nav class="flex flex-col justify-between py-4 h-full">
    <div class="flex flex-col gap-1">
      {#each sections as section}
        <Link to={section.link}>
          {#snippet children(active)}
            <div
              class="w-full flex gap-3 items-center px-6 py-3 text-left hover:bg-gray-700 transition-colors relative"
              class:bg-blue-600={active}
              class:hover:bg-blue-700={active}
            >
              <span class="text-xl">{section.icon}</span>
              {#if !isOpen}
                <span class="flex-1 hidden lg:block">{section.name}</span>
              {/if}
            </div>
          {/snippet}
        </Link>
      {/each}
    </div>

    <button
      class="hidden lg:flex mx-auto items-center justify-center"
      class:rotate-180={isOpen}
      onclick={() => (isOpen = !isOpen)}
    >
      <Icon icon="hugeicons:arrow-left-01" class="w-8 h-8" />
    </button>
  </nav>
</aside>

<style>
  aside {
    min-height: 100vh;
  }
</style>
