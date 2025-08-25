import { writable, derived } from 'svelte/store';
// CORRECCIÓN: Se importa el wrapper 'api' para hacer llamadas seguras al backend
import { api } from '../utils/api.js';

// =================================================================================
// STORES PRINCIPALES Y DE ESTADO
// =================================================================================

/** @type {import('svelte/store').Writable<any[]>} */
export const images = writable([]);

/** @type {import('svelte/store').Writable<string[]>} */
export const selectedImageIds = writable([]);

/** Store unificado para todos los filtros */
export const filters = writable({
	validation: 'all', // 'all', 'validated', 'notValidated'
	type: 'all', // 'all' o un tipo específico
	pageNumber: 'all' // 'all', 'with', 'without'
});

/** Store para estadísticas generales */
export const stats = writable({
	total_images: 0,
	validated: 0,
	pending: 0,
	by_type: {}
});


// =================================================================================
// STORES DERIVADOS
// =================================================================================

/** Derivado para obtener los objetos completos de las imágenes seleccionadas */
export const selectedImages = derived(
	[images, selectedImageIds],
	([$images, $selectedImageIds]) => {
		if (!$images || !$selectedImageIds) return [];
		const selectedIdsSet = new Set($selectedImageIds);
		return $images.filter((image) => selectedIdsSet.has(image.id));
	}
);

/** Derivado que filtra las imágenes según el estado del store `filters` */
export const filteredImages = derived([images, filters], ([$images, $filters]) => {
	if (!$images) return [];
	return $images.filter((img) => {
		if ($filters.validation === 'validated' && !img.validated) return false;
		if ($filters.validation === 'notValidated' && img.validated) return false;
		if ($filters.type !== 'all' && img.type !== $filters.type) return false;
		const hasNumber = img.page_number !== null && img.page_number !== undefined && img.page_number !== '';
		if ($filters.pageNumber === 'with' && !hasNumber) return false;
		if ($filters.pageNumber === 'without' && hasNumber) return false;
		return true;
	});
});

/** Derivado para contar el número de imágenes seleccionadas */
export const selectionCount = derived(selectedImageIds, ($selectedImageIds) => $selectedImageIds.length);


// =================================================================================
// LÓGICA DE SELECCIÓN DE IMÁGENES
// =================================================================================

export const imageSelection = {
	selectSingle: (imageId) => {
		selectedImageIds.set([imageId]);
	},
	toggle: (imageId) => {
		selectedImageIds.update((selected) => {
			const selectedSet = new Set(selected);
			if (selectedSet.has(imageId)) {
				selectedSet.delete(imageId);
			} else {
				selectedSet.add(imageId);
			}
			return Array.from(selectedSet);
		});
	},
	selectRange: (startImageId, endImageId, allVisibleImages) => {
		const startIndex = allVisibleImages.findIndex((img) => img.id === startImageId);
		const endIndex = allVisibleImages.findIndex((img) => img.id === endImageId);
		if (startIndex === -1 || endIndex === -1) return;
		const start = Math.min(startIndex, endIndex);
		const end = Math.max(startIndex, endIndex);
		const rangeIds = allVisibleImages.slice(start, end + 1).map((img) => img.id);
		selectedImageIds.update((selected) => [...new Set([...selected, ...rangeIds])]);
	},
	selectAll: (visibleImages) => {
		const visibleIds = visibleImages.map((img) => img.id);
		selectedImageIds.set(visibleIds);
	},
	clear: () => {
		selectedImageIds.set([]);
	}
};

// =================================================================================
// CONFIGURACIÓN Y UTILIDADES
// =================================================================================

export const pageTypes = {
	blanca: { label: 'Página blanca', icon: '📄', color: 'bg-gray-200 text-gray-800' },
	portada: { label: 'Portada', icon: '📖', color: 'bg-red-200 text-red-800' },
	contraportada: { label: 'Contraportada', icon: '📕', color: 'bg-red-300 text-red-900' },
	frontispicio: { label: 'Frontispicio', icon: '🏛️', color: 'bg-yellow-200 text-yellow-800' },
	guardia: { label: 'Guardia', icon: '🛡️', color: 'bg-amber-200 text-amber-800' },
	texto: { label: 'Página con texto', icon: '📝', color: 'bg-blue-200 text-blue-800' },
	ilustracion: { label: 'Ilustración', icon: '🎨', color: 'bg-purple-200 text-purple-800' },
	target: { label: 'Target calibración', icon: '🎯', color: 'bg-green-200 text-green-800' },
	inserto: { label: 'Inserto', icon: '📎', color: 'bg-orange-200 text-orange-800' },
	referencia: { label: 'Referencia', icon: '📏', color: 'bg-indigo-200 text-indigo-800' },
	unknown: { label: 'Desconocido', icon: '❓', color: 'bg-pink-200 text-pink-800' }
};

export function getPageTypeConfig(type) {
	return pageTypes[type] || pageTypes['unknown'];
}


// =================================================================================
// ACCIONES (INTERACCIÓN CON API) - VERSIÓN CORREGIDA Y COMPLETA
// =================================================================================

export const imageActions = {
	/** Cargar todas las imágenes desde la API */
	loadImages: async () => {
		try {
			const data = await api.get('/api/images');
			images.set(data.images);
		} catch (error) {
			console.error('Error loading images:', error);
			throw error;
		}
	},

	/** Actualizar una única imagen en el servidor y luego en el store */
	updateImage: async (imageId, updates) => {
		try {
			const updatedImage = await api.put(`/api/images/${imageId}`, updates);
			images.update((all) => all.map((img) => (img.id === imageId ? updatedImage : img)));
			return updatedImage;
		} catch (error) {
			console.error(`Error updating image ${imageId}:`, error);
			throw error;
		}
	},

	/** Actualizar un lote de imágenes en el servidor y luego en el store */
	bulkUpdateImages: async (imageIds, updates) => {
		try {
			const body = { image_ids: imageIds, updates: updates };
			const data = await api.put('/api/images/bulk-update', body);
			images.update((all) => {
				const updatedMap = new Map(data.updated_images.map((img) => [img.id, img]));
				return all.map((img) => updatedMap.get(img.id) || img);
			});
			return data;
		} catch (error) {
			console.error('Error bulk updating images:', error);
			throw error;
		}
	},

	/** Aplicar numeración consecutiva a un lote de imágenes */
	applyConsecutiveNumbering: async (imageIds, options = {}) => {
		try {
			const body = {
				image_ids: imageIds,
				start_number: options.startNumber || 1,
				number_type: options.numberType || 'arabic',
				phantom_number: options.phantomNumber || false
			};
			const data = await api.post('/api/images/consecutive-numbering', body);
			images.update((all) => {
				const updatedMap = new Map(data.updated_images.map((img) => [img.id, img]));
				return all.map((img) => updatedMap.get(img.id) || img);
			});
			return data;
		} catch (error) {
			console.error('Error applying consecutive numbering:', error);
			throw error;
		}
	},

	/** Validar un lote de imágenes */
	bulkValidate: async (imageIds) => {
		try {
			const data = await api.post('/api/validate/bulk', { image_ids: imageIds });
			images.update((all) =>
				all.map((img) => (imageIds.includes(img.id) ? { ...img, validated: true } : img))
			);
			return data;
		} catch (error) {
			console.error('Error bulk validating:', error);
			throw error;
		}
	},

	/** Reclasificar un lote de imágenes */
	bulkReclassify: async (imageIds) => {
		try {
			const data = await api.post('/api/classify/bulk', { image_ids: imageIds });
			images.update((all) => {
				const updatedMap = new Map();
				data.results.forEach((result) => {
					if (result.type && !result.error) {
						updatedMap.set(result.id, {
							type: result.type,
							confidence: result.confidence,
							validated: false
						});
					}
				});
				return all.map((img) => {
					const update = updatedMap.get(img.id);
					return update ? { ...img, ...update } : img;
				});
			});
			return data;
		} catch (error) {
			console.error('Error bulk reclassifying:', error);
			throw error;
		}
	},

	/** Cargar las estadísticas globales desde la API */
	loadStats: async () => {
		try {
			const data = await api.get('/api/stats');
			stats.set(data);
		} catch (error) {
			console.error('Error loading stats:', error);
			throw error;
		}
	},

	/** Obtener una vista previa de la exportación */
	getExportPreview: async (imageIds) => {
		try {
			const data = await api.post('/api/export/preview', { image_ids: imageIds });
			return data;
		} catch (error) {
			console.error('Error getting export preview:', error);
			throw error;
		}
	}
};