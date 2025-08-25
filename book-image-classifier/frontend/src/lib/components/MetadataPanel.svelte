<script>
	import { createEventDispatcher } from 'svelte';
	import { pageTypes, getPageTypeConfig } from '../stores/imageStore.js';

	export let image;
	const dispatch = createEventDispatcher();

	function updateField(field, value) {
		if (!image) return;
		// Create a detail object with the imageId and the updates
		const detail = {
			imageId: image.id,
			updates: { [field]: value }
		};
		dispatch('update', detail);
	}

	function validateImage() {
		if (!image) return;
		dispatch('validate', { imageId: image.id });
	}
</script>

{#if image}
	<div class="p-4 space-y-6">
		<h3 class="text-lg font-semibold text-gray-800 border-b pb-2">Metadatos</h3>

		<div>
			<label for="type-select" class="label">Tipo de Página</label>
			<select
				id="type-select"
				class="input"
				value={image.type}
				on:change={(e) => updateField('type', e.target.value)}
			>
				{#each Object.entries(pageTypes) as [type, config]}
					<option value={type}>{config.icon} {config.label}</option>
				{/each}
			</select>
		</div>

		<div>
			<label for="page-number-input" class="label">Número de Página</label>
			<input
				id="page-number-input"
				type="text"
				class="input"
				placeholder="Ej: 15, XV, 15bis"
				value={image.page_number || ''}
				on:change={(e) => updateField('page_number', e.target.value || null)}
			/>
		</div>

		<div>
			<label class="flex items-center space-x-2">
				<input
					type="checkbox"
					class="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
					checked={image.ghost_number || false}
					on:change={(e) => updateField('ghost_number', e.target.checked)}
				/>
				<span class="text-sm text-gray-700">Número fantasma (no impreso)</span>
			</label>
		</div>

		<div class="pt-4 border-t">
			<button
				class="w-full font-bold py-2 px-4 rounded transition-colors duration-200"
				class:bg-green-600={!image.validated}
				class:hover:bg-green-700={!image.validated}
				class:text-white={!image.validated}
				class:bg-gray-300={image.validated}
				class:text-gray-500={image.validated}
				class:cursor-not-allowed={image.validated}
				on:click={validateImage}
				disabled={image.validated}
			>
				{image.validated ? '✓ Validada' : 'Marcar como Validada'}
			</button>
		</div>
	</div>
{/if}

<style>
	.label {
		display: block;
		margin-bottom: 0.25rem;
		font-size: 0.875rem;
		font-weight: 500;
		color: #374151;
	}
	.input {
		width: 100%;
		border-radius: 0.375rem;
		border: 1px solid #d1d5db;
		padding: 0.5rem 0.75rem;
		font-size: 1rem;
	}
	.input:focus {
		border-color: #3b82f6;
		box-shadow: 0 0 0 2px #bfdbfe;
		outline: none;
	}
</style>