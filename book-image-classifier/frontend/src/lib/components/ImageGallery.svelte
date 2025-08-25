<script>
	import { onMount } from 'svelte';
	import { getImageUrl } from '../utils/api.js';
	import {
		filteredImages,
		selectedImageIds,
		selectionCount,
		imageSelection,
		imageActions,
		getPageTypeConfig // Conservamos esto para los badges
	} from '../stores/imageStore.js';

	// Variables de estado para la carga de datos
	let loading = true;
	let error = null;
	let lastClickedImageId = null;

	// Props para hacer el componente más configurable
	export let allowMultiSelect = true;
	export let showSelectionTools = true;
	export let showImageDetails = true;

	// Cargar imágenes al montar el componente
	onMount(async () => {
		await loadImages();
	});

	async function loadImages() {
		try {
			loading = true;
			error = null;
			await imageActions.loadImages();
		} catch (err) {
			error = err.message || 'Ocurrió un error desconocido.';
		} finally {
			loading = false;
		}
	}

	// Maneja toda la lógica de click para selección simple y múltiple
	function handleImageClick(image, event) {
		if (!allowMultiSelect) {
			imageSelection.selectSingle(image.id);
			lastClickedImageId = image.id;
			return;
		}

		if (event.ctrlKey || event.metaKey) {
			// Ctrl/Cmd + Click: alterna la selección
			imageSelection.toggle(image.id);
			lastClickedImageId = image.id;
		} else if (event.shiftKey && lastClickedImageId) {
			// Shift + Click: selección de rango
			imageSelection.selectRange(lastClickedImageId, image.id, $filteredImages);
		} else {
			// Click normal: selección única
			imageSelection.selectSingle(image.id);
			lastClickedImageId = image.id;
		}
	}
</script>

<div class="w-full">
	{#if showSelectionTools && allowMultiSelect}
		<div class="mb-4 p-3 bg-gray-50 rounded-lg flex items-center justify-between border">
			<div class="flex items-center gap-2">
				<button
					on:click={() => imageSelection.selectAll($filteredImages)}
					class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-300"
					disabled={$filteredImages.length === 0}
				>
					Seleccionar Todo
				</button>
				<button
					on:click={() => imageSelection.clear()}
					class="px-3 py-1.5 text-sm bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors disabled:opacity-50"
					disabled={$selectionCount === 0}
				>
					Limpiar
				</button>
			</div>

			<div class="text-sm text-gray-600">
				{#if $selectionCount > 0}
					<span class="font-medium text-blue-700">
						{$selectionCount} imagen{$selectionCount !== 1 ? 'es' : ''} seleccionada{$selectionCount !== 1 ? 's' : ''}
					</span>
				{:else}
					<span class="hidden md:inline">
						Click para seleccionar • Ctrl+Click para múltiple • Shift+Click para rango
					</span>
				{/if}
			</div>
		</div>
	{/if}

	{#if loading}
		<div class="text-center py-12 text-gray-500">Cargando imágenes...</div>
	{:else if error}
		<div class="bg-red-50 text-red-700 p-4 rounded-md border border-red-200">
			<p><strong>Error:</strong> {error}</p>
			<button on:click={loadImages} class="mt-2 px-3 py-1.5 text-sm bg-red-600 text-white rounded-md hover:bg-red-700">
				Reintentar
			</button>
		</div>
	{:else if $filteredImages.length === 0}
		<div class="p-4 text-center text-sm text-gray-500 border-2 border-dashed rounded-lg mt-4">
			No hay imágenes que coincidan con los filtros.
		</div>
	{:else}
		<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
			{#each $filteredImages as image (image.id)}
				{@const typeConfig = getPageTypeConfig(image.type)}
				<div
					class="relative group cursor-pointer border-2 rounded-lg overflow-hidden transition-all duration-200"
					class:selected={$selectedImageIds.includes(image.id)}
					on:click={(e) => handleImageClick(image, e)}
					role="button"
					tabindex="0"
					on:keydown|preventDefault={(e) => (e.key === 'Enter' || e.key === ' ') && handleImageClick(image, e)}
				>
					<img
						src={getImageUrl(image.id, 'thumbnail')}
						alt={image.original_filename}
						loading="lazy"
						class="aspect-square w-full h-full object-cover bg-gray-200"
					/>

					{#if showImageDetails}
						<div class="absolute bottom-0 left-0 right-0 p-2 bg-white/80 backdrop-blur-sm">
							<span class="block text-xs font-medium text-gray-900 truncate" title={image.original_filename}>
								{image.original_filename}
							</span>
							<div class="mt-1 flex gap-1 flex-wrap">
								<span class="badge {typeConfig.color}">{typeConfig.icon} {typeConfig.label}</span>
								{#if image.validated}
									<span class="badge bg-green-200 text-green-800">✓ Validado</span>
								{/if}
							</div>
						</div>
					{/if}

					<div class="checkbox" class:checked={$selectedImageIds.includes(image.id)}>
						{#if $selectedImageIds.includes(image.id)}
							<svg class="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
							</svg>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.selected {
		border-color: #3b82f6;
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
	}
	.badge {
		padding: 0.1rem 0.5rem;
		border-radius: 999px;
		font-size: 0.7rem;
		font-weight: 500;
		white-space: nowrap;
	}
	.checkbox {
		position: absolute;
		top: 0.5rem;
		left: 0.5rem;
		width: 1.25rem;
		height: 1.25rem;
		border-radius: 0.25rem;
		border: 2px solid white;
		background-color: rgba(0, 0, 0, 0.3);
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
	}
	.checkbox.checked {
		background-color: #3b82f6;
		border-color: #3b82f6;
	}
	/* Mejora de accesibilidad para el foco */
	[role='button']:focus-visible {
		outline: 2px solid #3b82f6;
		outline-offset: 2px;
	}
</style>