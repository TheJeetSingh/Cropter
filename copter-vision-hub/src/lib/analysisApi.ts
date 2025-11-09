/**
 * API Client for Agricultural Video Analysis
 * Connects Frontend → Backend → AI Service
 */

import type {
  AnalysisOptions,
  AnalysisMetadata,
  AnalysisResponse,
  UploadProgress,
} from '@/types/analysis';

// Configure your backend URL here
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';

/**
 * Upload and analyze video file
 */
export async function analyzeVideo(
  file: File,
  options?: AnalysisOptions,
  metadata?: AnalysisMetadata,
  onProgress?: (progress: UploadProgress) => void
): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append('video', file);

  // Add options if provided
  if (options) {
    formData.append('options', JSON.stringify(options));
  }

  // Add metadata if provided
  if (metadata) {
    formData.append('metadata', JSON.stringify(metadata));
  }

  try {
    const xhr = new XMLHttpRequest();

    // Track upload progress
    if (onProgress) {
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          onProgress({
            loaded: e.loaded,
            total: e.total,
            percentage: Math.round((e.loaded / e.total) * 100),
          });
        }
      });
    }

    // Make the request
    const response = await new Promise<Response>((resolve, reject) => {
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const blob = new Blob([xhr.response]);
          const headers = new Headers();
          xhr.getAllResponseHeaders()
            .split('\r\n')
            .forEach((line) => {
              const parts = line.split(': ');
              if (parts.length === 2) {
                headers.append(parts[0], parts[1]);
              }
            });
          resolve(
            new Response(blob, {
              status: xhr.status,
              statusText: xhr.statusText,
              headers,
            })
          );
        } else {
          reject(new Error(`HTTP Error: ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Network error'));
      });

      xhr.addEventListener('abort', () => {
        reject(new Error('Upload aborted'));
      });

      xhr.open('POST', `${BACKEND_URL}/api/upload`);
      xhr.send(formData);
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error_message || `HTTP Error: ${response.status}`);
    }

    const result: AnalysisResponse = await response.json();
    return result;
  } catch (error) {
    console.error('Analysis error:', error);
    throw error;
  }
}

/**
 * Check analysis status (for async processing)
 */
export async function checkAnalysisStatus(requestId: string): Promise<AnalysisResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/status/${requestId}`);

    if (!response.ok) {
      throw new Error(`HTTP Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Status check error:', error);
    throw error;
  }
}

/**
 * Download annotated video
 */
export function getVideoUrl(videoPath: string): string {
  // Remove leading slash if present
  const cleanPath = videoPath.startsWith('/') ? videoPath.substring(1) : videoPath;
  return `${BACKEND_URL}/${cleanPath}`;
}

/**
 * Download analysis report JSON
 */
export async function downloadReport(reportPath: string): Promise<Blob> {
  try {
    const url = getVideoUrl(reportPath);
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`HTTP Error: ${response.status}`);
    }

    return await response.blob();
  } catch (error) {
    console.error('Download error:', error);
    throw error;
  }
}

/**
 * Health check endpoint
 */
export async function checkHealth(): Promise<{ status: string; ai_service: string }> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/health`);

    if (!response.ok) {
      throw new Error(`HTTP Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Health check error:', error);
    throw error;
  }
}


