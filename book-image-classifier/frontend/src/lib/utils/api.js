// Configuración base de la API
const API_BASE_URL = 'http://localhost:5001'; // Base URL for the Flask backend

// --- API Wrapper Object ---
// Provides clean methods like api.get(), api.post(), etc.
async function fetchWithTimeout(resource, options = {}, timeout = 60000) {
    const { signal, ...restOfOptions } = options;
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);

    const response = await fetch(resource, {
        ...restOfOptions,
        signal: controller.signal
    });

    clearTimeout(id);
    return response;
}

async function handleResponse(response) {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'An unknown network error occurred.' }));
        const errorMessage = errorData.error || `HTTP error! Status: ${response.status}`;
        throw new Error(errorMessage);
    }
    return response.json();
}

export const api = {
    get: async (endpoint) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}${endpoint}`);
        return handleResponse(response);
    },
    post: async (endpoint, body, options = {}) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
            ...options,
        });
        return handleResponse(response);
    },
    put: async (endpoint, body) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}${endpoint}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });
        return handleResponse(response);
    }
};

// --- Specialized Functions ---

/**
 * Uploads multiple images using XMLHttpRequest to support progress tracking.
 * @param {FormData} formData - The form data containing the files.
 * @param {(progress: number) => void} onProgress - Callback function to report upload progress.
 * @returns {Promise<any>}
 */
export function uploadImages(formData, onProgress) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `${API_BASE_URL}/api/upload`, true);

        // Progress event
        if (onProgress) {
            xhr.upload.onprogress = (event) => {
                if (event.lengthComputable) {
                    const percentComplete = Math.round((event.loaded / event.total) * 100);
                    onProgress(percentComplete);
                }
            };
        }

        // Completion event
        xhr.onload = () => {
            try {
                const jsonResponse = JSON.parse(xhr.responseText);
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(jsonResponse);
                } else {
                    reject(new Error(jsonResponse.error || 'Upload failed'));
                }
            } catch (e) {
                reject(new Error('Invalid server response.'));
            }
        };

        // Error events
        xhr.onerror = () => reject(new Error('Network error during upload.'));
        xhr.ontimeout = () => reject(new Error('Upload timed out.'));

        xhr.timeout = 120000; // 2 minutes timeout
        xhr.send(formData);
    });
}

/**
 * Gets the direct URL for an image file from the backend.
 * @param {string|number} imageId - The ID of the image.
 * @returns {string}
 */
export function getImageUrl(imageId) {
    return `${API_BASE_URL}/api/images/${imageId}/file`;
}


// --- Formatter Utilities ---
export const formatters = {
    formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
    },

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        try {
            return new Date(dateString).toLocaleString();
        } catch {
            return 'Invalid Date';
        }
    },

    formatConfidence(confidence) {
        if (confidence === null || confidence === undefined) return 'N/A';
        return `${Math.round(confidence * 100)}%`;
    }
};