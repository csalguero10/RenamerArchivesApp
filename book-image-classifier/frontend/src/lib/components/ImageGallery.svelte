<script>
	import { getImageUrl } from '../utils/api.js';
	import { getPageTypeConfig } from '../stores/imageStore.js';

	export let images = [];
	export let selectedImage = null;

	let thumbnailContainer;

	// Scroll to selected image when it changes
	$: if (selectedImage && thumbnailContainer) {
		const el = thumbnailContainer.querySelector(`[data-image-id="${selectedImage.id}"]`);
		if (el) {
			el.scrollIntoView({
				behavior: 'smooth',
				block: 'nearest'
			});
		}
	}
</script>

<div class="image-gallery" bind:this={thumbnailContainer}>
	{#if images.length === 0}
		<div class="p-4 text-center text-sm text-gray-500">No hay imágenes que coincidan con los filtros.</div>
	{:else}
		{#each images as image (image.id)}
			{@const typeConfig = getPageTypeConfig(image.type)}
			<button
				class="gallery-item"
				class:selected={selectedImage?.id === image.id}
				on:click={() => (selectedImage = image)}
				data-image-id={image.id}
			>
				<img src={getImageUrl(image.id)} alt={image.original_filename} loading="lazy" />
				<div class="info">
					<span class="truncate text-xs font-medium">{image.original_filename}</span>
					<div class="badges">
						<span class="badge {typeConfig.color}">{typeConfig.label}</span>
						{#if image.validated}
							<span class="badge bg-green-200 text-green-800">✓</span>
						{/if}
					</div>
				</div>
			</button>
		{/each}
	{/if}
</div>

<style>
	.image-gallery {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		padding: 0.5rem;
	}
	.gallery-item {
		display: flex;
		align-items: center;
		width: 100%;
		padding: 0.5rem;
		border-radius: 0.5rem;
		border: 2px solid transparent;
		gap: 0.75rem;
		cursor: pointer;
		text-align: left;
		background: #f9fafb;
	}
	.gallery-item:hover {
		border-color: #d1d5db;
	}
	.gallery-item.selected {
		border-color: #3b82f6;
		background-color: #eff6ff;
	}
	.gallery-item img {
		width: 4rem;
		height: 5rem;
		object-fit: cover;
		border-radius: 0.25rem;
		flex-shrink: 0;
		background-color: #e5e7eb;
	}
	.info {
		min-width: 0; /* Important for flex truncation */
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}
	.badges {
		display: flex;
		gap: 0.25rem;
		flex-wrap: wrap;
	}
	.badge {
		padding: 0.1rem 0.5rem;
		border-radius: 999px;
		font-size: 0.7rem;
		font-weight: 500;
	}
</style>