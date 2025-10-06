<script lang="ts">
  import Icon from '@iconify/svelte';
  import { _ } from 'svelte-i18n';
  import { Link } from 'svelte5-router';
  import { appSettings } from '../stores/app';

  let isClose = $state(true);

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
  class="bg-gray-800 text-white flex flex-col border-r border-gray-700 justify-between py-4 transition-all duration-500 ease-in-out"
  class:max-w-64={!isClose}
  class:w-16={isClose}
  class:lg:w-64={!isClose}
  class:lg:w-16={isClose}
>
  <div class="flex flex-col gap-1 w-full">
    {#each sections as section}
      {#if section.link !== '/translator' || $appSettings.translatorFeature}
        <Link to={section.link}>
          {#snippet children(active)}
            <div
              class="w-full flex px-4.5 gap-3 items-center justify-start py-3 text-left hover:bg-gray-700 transition-all duration-300 relative {section.color}"
              class:bg-blue-600={active}
              class:hover:bg-blue-700={active}
            >
              <span
                class="text-xl flex"
                class:w-min={!isClose}
                class:w-full={isClose}
              >
                <Icon icon={section.icon} class="w-6 h-6" />
              </span>
              <span 
                class="flex-1 font-bold overflow-hidden"
                class:hidden={isClose}
                class:opacity-0={isClose}
                class:opacity-100={!isClose}
                class:max-w-0={isClose}
                class:max-w-full={!isClose}
                class:lg:block={!isClose}
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
    class="hidden lg:flex mx-auto items-center justify-center transition-all duration-500 ease-in-out bg-slate-700 hover:bg-slate-600 rounded-full p-1"
    class:rotate-180={isClose}
    class:scale-110={isClose}
    class:scale-100={!isClose}
    onclick={() => (isClose = !isClose)}
  >
    <Icon icon="hugeicons:arrow-left-01" class="w-8 h-8" />
  </button>
</nav>
