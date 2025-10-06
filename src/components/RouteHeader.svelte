<script lang="ts">
  import Icon from '@iconify/svelte';
  import type { Snippet } from 'svelte';

  interface Props {
    title: string;
    description: string;
    icon: string;
    color: string;
    children?: Snippet;
  }

  const { title, description, icon, color, children }: Props = $props();
</script>

<div class="border-b border-gray-700 bg-gray-900">
  <div class="items-center justify-between" class:flex={title !== 'Paramètres'}>
    <div class="p-6">
      <div class="flex items-center gap-3">
        <Icon {icon} class="w-8 h-8 text-{color}-300" />
        <h1
          class="text-3xl font-bold text-{color}-300 mb-2 flex gap-3 items-center"
        >
          {title}
        </h1>
      </div>
      <p class="text-{color}-200 text-sm">
        {description}
      </p>
    </div>
    {@render children?.()}
  </div>
</div>
