import { writable, derived } from 'svelte/store';

// --- Core Stores ---
/** @type {import('svelte/store').Writable<any[]>} */
export const images = writable([]);

/** @type {import('svelte/store').Writable<any|null>} */
export const selectedImage = writable(null);

// --- Filter Stores ---
/** @type {import('svelte/store').Writable<'all' | 'validated' | 'notValidated'>} */
export const validationFilter = writable('all');

/** @type {import('svelte/store').Writable<string>} */
export const typeFilter = writable('all');

/** @type {import('svelte/store').Writable<'all' | 'with' | 'without'>} */
export const pageNumberFilter = writable('all');

// --- Derived Store for Filtered Images ---
// This store automatically updates when the source images or any filter changes.
export const filteredImages = derived(
	[images, validationFilter, typeFilter, pageNumberFilter],
	([$images, $validationFilter, $typeFilter, $pageNumberFilter]) => {
		if (!$images) return [];

		return $images.filter((img) => {
			// Validation status filter
			if ($validationFilter === 'validated' && !img.validated) return false;
			if ($validationFilter === 'notValidated' && img.validated) return false;

			// Page type filter
			if ($typeFilter !== 'all' && img.type !== $typeFilter) return false;

			// Page number filter
			const hasNumber = img.page_number !== null && img.page_number !== undefined && img.page_number !== false && img.page_number !== '';
			if ($pageNumberFilter === 'with' && !hasNumber) return false;
			if ($pageNumberFilter === 'without' && hasNumber) return false;

			return true;
		});
	}
);

// --- Derived Store for Current Image Index ---
// Provides the index of the selected image within the filtered list.
export const currentImageIndex = derived(
	[filteredImages, selectedImage],
	([$filteredImages, $selectedImage]) => {
		if (!$selectedImage || !$filteredImages) return -1;
		return $filteredImages.findIndex((img) => img.id === $selectedImage.id);
	}
);


// --- Page Type Configuration ---
// Centralized configuration for page types, colors, and icons.
export const pageTypes = {
    'blanca': { label: 'Página blanca', icon: '📄', color: 'bg-gray-200 text-gray-800' },
    'portada': { label: 'Portada', icon: '📖', color: 'bg-red-200 text-red-800' },
    'contraportada': { label: 'Contraportada', icon: '📕', color: 'bg-red-300 text-red-900' },
    'frontispicio': { label: 'Frontispicio', icon: '🏛️', color: 'bg-yellow-200 text-yellow-800' },
    'guardia': { label: 'Guardia', icon: '🛡️', color: 'bg-amber-200 text-amber-800' },
    'texto': { label: 'Página con texto', icon: '📝', color: 'bg-blue-200 text-blue-800' },
    'ilustracion': { label: 'Ilustración', icon: '🎨', color: 'bg-purple-200 text-purple-800' },
    'target': { label: 'Target calibración', icon: '🎯', color: 'bg-green-200 text-green-800' },
    'inserto': { label: 'Inserto', icon: '📎', color: 'bg-orange-200 text-orange-800' },
    'referencia': { label: 'Referencia', icon: '📏', color: 'bg-indigo-200 text-indigo-800' },
    'unknown': { label: 'Desconocido', icon: '❓', color: 'bg-pink-200 text-pink-800' }
};

export function getPageTypeConfig(type) {
    return pageTypes[type] || pageTypes['unknown'];
}