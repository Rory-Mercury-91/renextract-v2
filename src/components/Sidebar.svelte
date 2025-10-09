<script lang="ts">
  import Icon from '@iconify/svelte';
  import { _ } from 'svelte-i18n';
  import { Link } from 'svelte5-router';
  import { appSettings } from '../stores/app';

  let isClose = $state(false);

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
  class="flex flex-col justify-between border-r border-gray-200 bg-gray-50 py-4 text-gray-900 transition-all duration-500 ease-in-out dark:border-gray-700 dark:bg-gray-800 dark:text-white"
  class:max-w-64={!isClose}
  class:w-16={isClose}
  class:lg:w-64={!isClose}
  class:lg:w-16={isClose}
>
  <div class="flex w-full flex-col gap-1">
    {#each sections as section}
      {#if section.link !== '/translator' || $appSettings.translatorFeature}
        <Link to={section.link}>
          {#snippet children(active)}
            <div
              class="px-4.5 relative flex w-full items-center justify-start gap-3 py-3 text-left transition-all duration-300 hover:bg-gray-200 dark:hover:bg-gray-700 {section.color}"
              class:bg-blue-600={active}
              class:hover:bg-blue-700={active}
            >
              <span
                class="flex text-xl"
                class:w-min={!isClose}
                class:w-full={isClose}
              >
                <Icon icon={section.icon} class="h-6 w-6" />
              </span>
              <span
                class="hidden flex-1 overflow-hidden font-bold"
                class:opacity-0={isClose}
                class:opacity-100={!isClose}
                class:max-w-0={isClose}
                class:max-w-full={!isClose}
                class:lg:block={!isClose}
                title={section.name}
              >
                {section.name}
              </span>
            </div>
          {/snippet}
        </Link>
      {/if}
    {/each}
  </div>

  <button
    class="mx-auto hidden items-center justify-center rounded-full bg-gray-200 p-1 transition-all duration-500 ease-in-out hover:bg-gray-300 dark:bg-slate-700 dark:hover:bg-slate-600 lg:flex"
    class:rotate-180={isClose}
    class:scale-110={isClose}
    class:scale-100={!isClose}
    onclick={() => (isClose = !isClose)}
  >
    <Icon icon="hugeicons:arrow-left-01" class="h-8 w-8" />
  </button>
</nav>
