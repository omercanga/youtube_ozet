import { useState } from 'react';
import { useTranslation } from 'react-i18next';

export default function ManualAnalyzeForm({ onAnalyze, loading }) {
  const { t } = useTranslation();
  const [title, setTitle] = useState('');
  const [transcript, setTranscript] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (title.trim() && transcript.trim()) {
      onAnalyze(title.trim(), transcript.trim(), sourceUrl.trim() || null);
    }
  };

  const characterCount = transcript.length;
  const isValid = title.trim().length > 0 && transcript.trim().length >= 50;

  return (
    <div className="card">
      <h2 className="card-title">{t('manual.title')}</h2>
      <p className="card-description">{t('manual.description')}</p>

      <form onSubmit={handleSubmit} className="form-group">
        <div>
          <label htmlFor="title" className="form-label">
            {t('manual.titleLabel')} *
          </label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={t('manual.titlePlaceholder')}
            className="form-input"
            disabled={loading}
            required
          />
        </div>

        <div>
          <label htmlFor="sourceUrl" className="form-label">
            {t('manual.sourceUrlLabel')}
          </label>
          <input
            type="url"
            id="sourceUrl"
            value={sourceUrl}
            onChange={(e) => setSourceUrl(e.target.value)}
            placeholder={t('manual.sourceUrlPlaceholder')}
            className="form-input"
            disabled={loading}
          />
        </div>

        <div>
          <label htmlFor="transcript" className="form-label">
            {t('manual.transcriptLabel')}
          </label>
          <textarea
            id="transcript"
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder={t('manual.transcriptPlaceholder')}
            rows="10"
            className="form-input form-textarea"
            disabled={loading}
            required
          />
          <div className="char-counter">
            <span className={characterCount >= 50 ? 'char-ok' : 'char-pending'}>
              {t('manual.charCount', { count: characterCount })}{' '}
              {characterCount >= 50
                ? t('manual.charOk')
                : t('manual.charNeeded', { count: 50 - characterCount })}
            </span>
            {characterCount > 0 && (
              <button
                type="button"
                onClick={() => setTranscript('')}
                className="btn-text btn-text-danger"
                disabled={loading}
              >
                {t('manual.clear')}
              </button>
            )}
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !isValid}
          className="btn btn-primary"
        >
          {loading ? t('analyze.analyzing') : t('analyze.button')}
        </button>
      </form>

      <div className="tips-box">
        <h3 className="tips-title">{t('manual.tips.title')}</h3>
        <ul className="tips-list">
          <li>{t('manual.tips.tip1')}</li>
          <li>{t('manual.tips.tip2')}</li>
          <li>{t('manual.tips.tip3')}</li>
        </ul>
      </div>
    </div>
  );
}
