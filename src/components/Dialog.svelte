<script lang="ts">
  import Icon from '@iconify/svelte';
  import type { Snippet } from 'svelte';

  interface Props {
    isOpen: boolean;
    title: string;
    size?: 'sm' | 'md' | 'lg' | 'xl';
    showCloseButton?: boolean;
    onClose: () => void;
    children?: Snippet;
  }

  const {
    isOpen,
    title,
    size = 'md',
    showCloseButton = true,
    onClose,
    children,
  }: Props = $props();

  // Tailles de modal
  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-2xl',
  };

  // Gérer la fermeture avec Escape
  const handleKeydown = (event: Event) => {
    if ((event as Event & { key: string }).key === 'Escape') {
      onClose();
    }
  };

  // Gérer le clic sur l'overlay
  const handleOverlayClick = (event: Event) => {
    if (event.target === event.currentTarget) {
      onClose();
    }
  };
</script>

<svelte:window onkeydown={handleKeydown} />

{#if isOpen}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
    onclick={handleOverlayClick}
    onkeydown={e =>
      (e as Event & { key: string }).key === 'Enter' && handleOverlayClick(e)}
    role="dialog"
    aria-modal="true"
    aria-labelledby="dialog-title"
    tabindex="-1"
  >
    <div
      class="w-full {sizeClasses[
        size
      ]} max-h-[90vh] overflow-y-auto rounded-2xl border border-gray-300 bg-white shadow-xl dark:border-gray-600 dark:bg-gray-800"
    >
      <div class="p-6">
        <!-- Header -->
        <div class="mb-4 flex items-center justify-between">
          <h3
            id="dialog-title"
            class="text-lg font-semibold text-gray-900 dark:text-white"
          >
            {title}
          </h3>
          {#if showCloseButton}
            <button
              class="rounded-lg bg-gray-100 p-2 text-gray-500 hover:bg-gray-200 dark:bg-gray-600 dark:text-gray-400 dark:hover:bg-gray-500"
              onclick={onClose}
              aria-label="Fermer"
            >
              <Icon icon="hugeicons:cancel-01" class="h-5 w-5" />
            </button>
          {/if}
        </div>

        <!-- Content -->
        <div class="space-y-4">
          {@render children?.()}
        </div>
      </div>
    </div>
  </div>
{/if}
