<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    align?: 'left' | 'center' | 'right';
    children?: Snippet;
  }

  const { align = 'right', children }: Props = $props();

  const alignClasses = {
    left: 'justify-start',
    center: 'justify-center',
    right: 'justify-end',
  };
</script>

<div class="mt-6 flex gap-3 {alignClasses[align]}">
  {@render children?.()}
</div>
