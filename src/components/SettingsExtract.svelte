<script lang="ts">
  import { appSettings } from '../stores/app';
</script>

<div class="space-y-8">
  <div>
    <h3 class="text-xl font-semibold mb-4">Extraction & Protection</h3>
    <p class="text-gray-400">
      Configuration des paramètres d'extraction et de protection des données.
    </p>

    <div class="space-y-6">
      <!-- Configuration des placeholders -->
      <div>
        <h3 class="text-lg font-semibold mb-4">
          🔧 Configuration des placeholders
        </h3>
        <div class="space-y-4">
          <div>
            <label
              for="placeholder-format"
              class="block text-sm font-medium mb-2"
              >Format des placeholders :</label
            >
            <input
              id="placeholder-format"
              type="text"
              bind:value={$appSettings.extraction.placeholderFormat}
              placeholder="Ex: PLACEHOLDER_N"
              class="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
            />
            <p class="text-sm text-gray-400 mt-1">
              Format utilisé pour marquer les éléments à traduire
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
