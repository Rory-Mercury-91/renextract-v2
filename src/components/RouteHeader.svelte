<script lang="ts">
  import { cn } from '$lib/utils';
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
        <Icon {icon} class={cn('w-8 h-8', color)} />
        <h1
          class={cn(
            'text-3xl font-bold',
            'mb-2 flex gap-3 items-center',
            color
          )}
        >
          {title}
        </h1>
      </div>
      <p class={cn('text-sm opacity-65', color)}>
        {description}
      </p>
    </div>
    {@render children?.()}
  </div>
</div>
