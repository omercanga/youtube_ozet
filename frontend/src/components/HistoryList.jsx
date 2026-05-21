import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { getHistory, deleteAnalysis } from '../services/api';

export default function HistoryList({ refresh, onSelect }) {
  const { t } = useTranslation();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const data = await getHistory();
      setHistory(data);
    } catch (error) {
      console.error('History load error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [refresh]);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (window.confirm(t('history.deleteConfirm'))) {
      try {
        await deleteAnalysis(id);
        loadHistory();
      } catch (error) {
        alert(t('history.deleteError') + ': ' + error.message);
      }
    }
  };

  if (loading) {
    return (
      <div className="card">
        <p className="text-muted">{t('app.loading')}</p>
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="card">
        <h2 className="card-title">{t('history.title')}</h2>
        <p className="text-muted">{t('history.empty')}</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="card-title">{t('history.title')}</h2>
      <div className="history-list">
        {history.map((item) => (
          <div
            key={item.id}
            className="history-item"
            onClick={() => onSelect && onSelect(item.id)}
          >
            <div className="history-item-content">
              <div className="history-item-header">
                <h3 className="history-item-title">
                  {item.video_title || 'Video'}
                </h3>
                {item.playlist_id && (
                  <span className="badge badge-playlist-sm">📋</span>
                )}
              </div>
              <p className="history-item-summary">{item.summary}</p>

              {/* Keywords preview */}
              {item.keywords && (
                <div className="history-item-keywords">
                  {item.keywords
                    .split(',')
                    .slice(0, 3)
                    .map((kw, i) => (
                      <span key={i} className="keyword-tag keyword-tag-sm">
                        {kw.trim()}
                      </span>
                    ))}
                </div>
              )}

              <div className="history-item-footer">
                {item.content_type && (
                  <span className="history-item-type">{item.content_type}</span>
                )}
                <span className="history-item-date">
                  {new Date(item.created_at).toLocaleString()}
                </span>
              </div>
            </div>
            <button
              onClick={(e) => handleDelete(item.id, e)}
              className="btn-text btn-text-danger"
            >
              {t('history.delete')}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
