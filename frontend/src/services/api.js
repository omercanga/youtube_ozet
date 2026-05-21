import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- Single Video ---

export const analyzeVideo = async (videoUrl) => {
  const response = await api.post('/api/analyze', { video_url: videoUrl });
  return response.data;
};

export const analyzeManual = async (title, transcriptText, sourceUrl = null) => {
  const response = await api.post('/api/analyze-manual', {
    title,
    transcript_text: transcriptText,
    source_url: sourceUrl,
  });
  return response.data;
};

// --- Playlist ---

export const getPlaylistInfo = async (url) => {
  const response = await api.get('/api/playlist/info', { params: { url } });
  return response.data;
};

export const analyzePlaylist = async (playlistUrl, videoIds, mode = 'individual') => {
  const response = await api.post('/api/playlist/analyze', {
    playlist_url: playlistUrl,
    video_ids: videoIds,
    mode,
  });
  return response.data;
};

// --- History ---

export const getHistory = async () => {
  const response = await api.get('/api/history');
  return response.data;
};

export const getAnalysisDetail = async (id) => {
  const response = await api.get(`/api/history/${id}`);
  return response.data;
};

export const deleteAnalysis = async (id) => {
  const response = await api.delete(`/api/history/${id}`);
  return response.data;
};

export default api;
