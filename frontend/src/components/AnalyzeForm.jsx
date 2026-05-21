import { useState } from 'react';
import { useTranslation } from 'react-i18next';

export default function AnalyzeForm({ onAnalyze, loading }) {
  const { t } = useTranslation();
  const [url, setUrl] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (url.trim()) {
      onAnalyze(url);
    }
  };

  return (
    <div className="card">
      <h2 className="card-title">{t('analyze.title')}</h2>
      <form onSubmit={handleSubmit} className="form-group">
        <div>
          <label htmlFor="url" className="form-label">
            {t('analyze.urlLabel')}
          </label>
          <input
            type="text"
            id="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder={t('analyze.urlPlaceholder')}
            className="form-input"
            disabled={loading}
          />
        </div>
        <button
          type="submit"
          disabled={loading || !url.trim()}
          className="btn btn-primary"
        >
          {loading ? t('analyze.analyzing') : t('analyze.button')}
        </button>
      </form>
    </div>
  );
}
