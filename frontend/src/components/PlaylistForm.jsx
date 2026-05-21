import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { getPlaylistInfo, analyzePlaylist } from '../services/api';

export default function PlaylistForm({ onResults, loading, setLoading }) {
  const { t } = useTranslation();
  const [url, setUrl] = useState('');
  const [playlistInfo, setPlaylistInfo] = useState(null);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [mode, setMode] = useState('individual');
  const [fetchLoading, setFetchLoading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(null);

  const handleFetchPlaylist = async () => {
    if (!url.trim()) return;
    setFetchLoading(true);
    setError(null);
    setPlaylistInfo(null);
    setSelectedIds(new Set());

    try {
      const data = await getPlaylistInfo(url);
      setPlaylistInfo(data);
      // Auto-select first 10
      const initialSet = new Set(data.videos.slice(0, 10).map((v) => v.video_id));
      setSelectedIds(initialSet);
    } catch (err) {
      setError(err.response?.data?.detail || t('analyze.genericError'));
    } finally {
      setFetchLoading(false);
    }
  };

  const toggleVideo = (videoId) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(videoId)) {
        next.delete(videoId);
      } else {
        if (next.size >= 15) return prev;
        next.add(videoId);
      }
      return next;
    });
  };

  const selectAll = () => {
    if (!playlistInfo) return;
    const all = new Set(playlistInfo.videos.slice(0, 15).map((v) => v.video_id));
    setSelectedIds(all);
  };

  const deselectAll = () => {
    setSelectedIds(new Set());
  };

  const handleAnalyze = async () => {
    if (selectedIds.size === 0) return;
    setLoading(true);
    setError(null);
    setProgress({ current: 0, total: selectedIds.size });

    try {
      const results = await analyzePlaylist(url, Array.from(selectedIds), mode);
      onResults(results);
    } catch (err) {
      setError(err.response?.data?.detail || t('analyze.genericError'));
    } finally {
      setLoading(false);
      setProgress(null);
    }
  };

  return (
    <div className="card">
      <h2 className="card-title">{t('playlist.title')}</h2>
      <p className="card-description">{t('playlist.description')}</p>

      {/* URL input */}
      <div className="form-group">
        <label htmlFor="playlistUrl" className="form-label">
          {t('playlist.urlLabel')}
        </label>
        <div className="input-group">
          <input
            type="text"
            id="playlistUrl"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder={t('playlist.urlPlaceholder')}
            className="form-input"
            disabled={fetchLoading || loading}
          />
          <button
            onClick={handleFetchPlaylist}
            disabled={fetchLoading || loading || !url.trim()}
            className="btn btn-secondary"
          >
            {fetchLoading ? t('playlist.fetching') : t('playlist.fetchButton')}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="alert alert-error">
          <p className="alert-title">{t('analyze.error')}</p>
          <p>{error}</p>
        </div>
      )}

      {/* Video list */}
      {playlistInfo && (
        <>
          <div className="playlist-header">
            <div>
              <h3 className="playlist-name">
                {playlistInfo.playlist_title}
              </h3>
              <span className="text-muted">
                {t('playlist.selectedCount', { count: selectedIds.size })} / {playlistInfo.video_count}
              </span>
            </div>
            <div className="playlist-actions">
              <button onClick={selectAll} className="btn-text">
                {t('playlist.selectAll')}
              </button>
              <button onClick={deselectAll} className="btn-text">
                {t('playlist.deselectAll')}
              </button>
            </div>
          </div>

          <div className="video-list">
            {playlistInfo.videos.map((video, index) => (
              <label
                key={video.video_id}
                className={`video-item ${selectedIds.has(video.video_id) ? 'video-item-selected' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={selectedIds.has(video.video_id)}
                  onChange={() => toggleVideo(video.video_id)}
                  className="video-checkbox"
                  disabled={loading}
                />
                <span className="video-index">{index + 1}</span>
                {video.thumbnail && (
                  <img
                    src={video.thumbnail}
                    alt=""
                    className="video-thumb"
                    loading="lazy"
                  />
                )}
                <div className="video-info">
                  <span className="video-title">{video.title}</span>
                  {video.duration && (
                    <span className="video-duration">{video.duration}</span>
                  )}
                </div>
              </label>
            ))}
          </div>

          {selectedIds.size > 15 && (
            <p className="text-warning">{t('playlist.maxWarning')}</p>
          )}

          {/* Mode selector */}
          <div className="mode-selector">
            <p className="form-label">{t('playlist.mode.label')}</p>
            <div className="mode-options">
              <label className={`mode-option ${mode === 'individual' ? 'mode-option-active' : ''}`}>
                <input
                  type="radio"
                  name="mode"
                  value="individual"
                  checked={mode === 'individual'}
                  onChange={() => setMode('individual')}
                  className="mode-radio"
                />
                <div>
                  <span className="mode-title">{t('playlist.mode.individual')}</span>
                  <span className="mode-desc">{t('playlist.mode.individualDesc')}</span>
                </div>
              </label>
              <label className={`mode-option ${mode === 'combined' ? 'mode-option-active' : ''}`}>
                <input
                  type="radio"
                  name="mode"
                  value="combined"
                  checked={mode === 'combined'}
                  onChange={() => setMode('combined')}
                  className="mode-radio"
                />
                <div>
                  <span className="mode-title">{t('playlist.mode.combined')}</span>
                  <span className="mode-desc">{t('playlist.mode.combinedDesc')}</span>
                </div>
              </label>
            </div>
          </div>

          {/* Analyze button */}
          <button
            onClick={handleAnalyze}
            disabled={loading || selectedIds.size === 0}
            className="btn btn-primary"
          >
            {loading && progress
              ? t('playlist.analyzing', { current: progress.current, total: progress.total })
              : t('playlist.analyzeButton')
            }
          </button>
        </>
      )}
    </div>
  );
}
