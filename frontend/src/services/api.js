const API_BASE = import.meta.env.VITE_API_BASE || '/api';

/**
 * Send text query to Multilingual RAG assistant
 */
export async function sendChatMessage(query, language = 'auto', conversationHistory = [], filterScheme = null) {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      language,
      conversation_history: conversationHistory,
      filter_scheme: filterScheme,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }

  return response.json();
}

/**
 * Fetch supported Indian regional languages
 */
export async function fetchSupportedLanguages() {
  const response = await fetch(`${API_BASE}/languages`);
  if (!response.ok) {
    throw new Error('Failed to fetch languages');
  }
  return response.json();
}

/**
 * Send recorded audio for Voice Query (STT -> RAG -> TTS)
 */
export async function sendVoiceQuery(audioBlob, language = 'auto') {
  const formData = new FormData();
  formData.append('file', audioBlob, 'voice_query.webm');
  formData.append('preferred_language', language);

  const response = await fetch(`${API_BASE}/voice/query`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Voice processing error: ${response.status}`);
  }

  return response.json();
}

/**
 * Generate Speech Audio for answer reading
 */
export async function requestTTS(text, language = 'en') {
  const response = await fetch(`${API_BASE}/voice/tts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text, language }),
  });

  if (!response.ok) {
    throw new Error('TTS generation failed');
  }

  return response.json();
}

/**
 * List all indexed government policy PDFs
 */
export async function fetchIndexedDocuments() {
  const response = await fetch(`${API_BASE}/docs/list`);
  if (!response.ok) {
    throw new Error('Failed to load documents list');
  }
  return response.json();
}

/**
 * Upload and index a new official policy PDF
 */
export async function uploadPolicyDocument(file, schemeName = '') {
  const formData = new FormData();
  formData.append('file', file);
  if (schemeName) {
    formData.append('scheme_name', schemeName);
  }

  const response = await fetch(`${API_BASE}/docs/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Upload failed');
  }

  return response.json();
}

/**
 * Delete an indexed document
 */
export async function deletePolicyDocument(filename) {
  const response = await fetch(`${API_BASE}/docs/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Delete failed');
  }

  return response.json();
}
