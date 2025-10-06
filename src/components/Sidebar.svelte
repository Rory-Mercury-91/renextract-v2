<script lang="ts">
  import Icon from '@iconify/svelte';
  import { _ } from 'svelte-i18n';
  import { Link } from 'svelte5-router';
  import { appSettings } from '../stores/app';

  let isOpen = $state(false);

  interface Section {
    link: string;
    name: string;
    icon: string;
    color: string;
  }

  const sections: Section[] = [
    {
      link: '/',
      name: $_('navigation.generator'),
      icon: 'hugeicons:magic-wand-04',
      color: 'text-yellow-300',
    },
    {
      link: '/extract',
      name: $_('navigation.extract'),
      icon: 'hugeicons:injection',
      color: 'text-blue-300',
    },
    {
      link: '/translator',
      name: $_('navigation.translator'),
      icon: 'hugeicons:translate',
      color: 'text-red-300',
    },
    {
      link: '/tools',
      name: $_('navigation.tools'),
      icon: 'hugeicons:tools',
      color: 'text-green-300',
    },
    {
      link: '/backups',
      name: $_('navigation.backup'),
      icon: 'hugeicons:floppy-disk',
      color: 'text-purple-300',
    },
    {
      link: '/settings',
      name: $_('navigation.settings'),
      icon: 'hugeicons:settings-01',
      color: 'text-gray-300',
    },
  ];
</script>

<nav
  class="max-w-64 bg-gray-800 text-white flex flex-col border-r border-gray-700 justify-between py-4"
  class:lg:w-64={!isOpen}
>
  <div class="flex flex-col gap-1">
    {#each sections as section}
      {#if section.link !== '/translator' || $appSettings.translatorFeature}
        <Link to={section.link}>
          {#snippet children(active)}
            <div
              class="w-full flex gap-3 items-center px-6 py-3 text-left hover:bg-gray-700 transition-colors relative {section.color}"
              class:bg-blue-600={active}
              class:hover:bg-blue-700={active}
            >
              <span class="text-xl">
                <Icon icon={section.icon} class="w-6 h-6" />
              </span>
              {#if !isOpen}
                <span class="flex-1 hidden lg:block font-bold"
                  >{section.name}</span
                >
              {/if}
            </div>
          {/snippet}
        </Link>
      {/if}
    {/each}
  </div>

  <button
    class="hidden lg:flex mx-auto items-center justify-center transition-all duration-400 bg-slate-700 hover:bg-slate-600 rounded-full p-1"
    class:rotate-180={isOpen}
    onclick={() => (isOpen = !isOpen)}
  >
    <Icon icon="hugeicons:arrow-left-01" class="w-8 h-8" />
  </button>
</nav>
