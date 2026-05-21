import { useState } from 'react';
import { useTranslation } from 'react-i18next';

const RESULT_TABS = ['overview', 'fullSummary', 'keywords', 'prompts', 'details'];

export default function ResultDisplay({ result }) {
  const { t } = useTranslation();
  const [copiedField, setCopiedField] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  if (!result) return null;

  const handleCopy = async (text, field) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const CopyButton = ({ text, field }) => (
    <button onClick={() => handleCopy(text, field)} className="btn-copy" title={t('result.copy')}>
      {copiedField === field ? t('result.copied') : t('result.copy')}
    </button>
  );

  const rawKeywords = result.keywords
    ? result.keywords.split(',').map((k) => k.trim()).filter(Boolean)
    : [];

  // Parse keyword_summary: lines like "**kelime**: açıklama"
  const keywordSummaryItems = result.keyword_summary
    ? result.keyword_summary
        .split('\n')
        .map((line) => {
          const m = line.match(/^\*\*(.+?)\*\*:\s*(.+)/);
          return m ? { word: m[1], desc: m[2] } : null;
        })
        .filter(Boolean)
    : [];

  let keyQuotes = [];
  if (result.key_quotes) {
    try {
      keyQuotes = JSON.parse(result.key_quotes);
      if (!Array.isArray(keyQuotes)) keyQuotes = [String(keyQuotes)];
    } catch {
      keyQuotes = [result.key_quotes];
    }
  }

  const actionItems = result.action_items
    ? result.action_items.split('\n').map((s) => s.replace(/^[-•]\s*/, '').trim()).filter(Boolean)
    : [];

  // Parse video_summary markdown headings (## Başlık)
  const parseSummaryBlocks = (text) => {
    if (!text) return [];
    const lines = text.split('\n');
    const blocks = [];
    let current = null;
    for (const line of lines) {
      const heading = line.match(/^##\s+(.+)/);
      if (heading) {
        if (current) blocks.push(current);
        current = { title: heading[1], body: '' };
      } else if (current) {
        current.body += (current.body ? '\n' : '') + line;
      } else {
        // Text before first heading
        if (!blocks.length && line.trim()) {
          blocks.push({ title: null, body: line });
        } else if (blocks.length && blocks[blocks.length - 1].title === null) {
          blocks[blocks.length - 1].body += '\n' + line;
        }
      }
    }
    if (current) blocks.push(current);
    return blocks.filter((b) => b.body.trim());
  };

  const summaryBlocks = parseSummaryBlocks(result.video_summary);

  const sentimentClass = () => {
    if (!result.sentiment) return 'chip-neutral';
    const s = result.sentiment.toLowerCase();
    if (s.startsWith('pozitif') || s.startsWith('positive')) return 'chip-positive';
    if (s.startsWith('negatif') || s.startsWith('negative')) return 'chip-negative';
    return 'chip-neutral';
  };

  return (
    <div className="card result-card">
      {/* Card header */}
      <div className="result-card-header">
        <div>
          <h2 className="card-title">{t('result.title')}</h2>
          {result.playlist_id && (
            <span className="badge badge-playlist">{t('result.playlistBadge')}</span>
          )}
        </div>
      </div>

      {/* Video link */}
      <div className="result-section">
        <a href={result.video_url} target="_blank" rel="noopener noreferrer" className="result-link result-video-title">
          {result.video_title || result.video_url}
        </a>
      </div>

      {/* One-liner */}
      {result.one_liner && (
        <div className="one-liner-box">
          <span className="one-liner-icon">✨</span>
          <span>{result.one_liner}</span>
          <CopyButton text={result.one_liner} field="one_liner" />
        </div>
      )}

      {/* Result tabs */}
      <div className="result-tabs">
        {RESULT_TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`result-tab ${activeTab === tab ? 'result-tab-active' : ''}`}
          >
            {t(`result.tabs.${tab}`)}
          </button>
        ))}
      </div>

      {/* TAB: Genel Bakış */}
      {activeTab === 'overview' && (
        <div className="tab-content">
          {/* Meta chips */}
          {(result.content_type || result.target_audience || result.difficulty_level || result.sentiment) && (
            <div className="meta-chips">
              {result.content_type && (
                <div className="chip chip-type"><span className="chip-icon">📂</span>{result.content_type}</div>
              )}
              {result.difficulty_level && (
                <div className="chip chip-difficulty"><span className="chip-icon">📊</span>{result.difficulty_level}</div>
              )}
              {result.sentiment && (
                <div className={`chip ${sentimentClass()}`}><span className="chip-icon">💬</span>{result.sentiment}</div>
              )}
              {result.target_audience && (
                <div className="chip chip-audience"><span className="chip-icon">👥</span>{result.target_audience}</div>
              )}
            </div>
          )}

          {/* Keyword tags */}
          {rawKeywords.length > 0 && (
            <div className="result-section">
              <h3 className="result-label">{t('result.keywords')}</h3>
              <div className="keywords-container">
                {rawKeywords.map((kw, i) => (
                  <span key={i} className="keyword-tag">{kw}</span>
                ))}
              </div>
            </div>
          )}

          {/* Short summary */}
          <div className="result-section">
            <div className="result-header">
              <h3 className="result-label">{t('result.summary')}</h3>
              <CopyButton text={result.summary} field="summary" />
            </div>
            <p className="result-text">{result.summary}</p>
          </div>

          {/* Footer */}
          <div className="result-footer">
            {result.language && <span>{t('result.language')}: {result.language.toUpperCase()}</span>}
            <span>•</span>
            <span>{new Date(result.created_at).toLocaleString()}</span>
          </div>
        </div>
      )}

      {/* TAB: Kapsamlı Özet */}
      {activeTab === 'fullSummary' && (
        <div className="tab-content">
          <div className="result-header" style={{ marginBottom: '1rem' }}>
            <h3 className="result-label">{t('result.videoSummary')}</h3>
            <CopyButton text={result.video_summary || ''} field="video_summary" />
          </div>
          {summaryBlocks.length > 0 ? (
            summaryBlocks.map((block, i) => (
              <div key={i} className="summary-block">
                {block.title && <h4 className="summary-block-title">{block.title}</h4>}
                <p className="result-text result-text-pre">{block.body.trim()}</p>
              </div>
            ))
          ) : (
            <p className="result-text result-text-pre">{result.video_summary}</p>
          )}
        </div>
      )}

      {/* TAB: Anahtar Kelimeler */}
      {activeTab === 'keywords' && (
        <div className="tab-content">
          {/* Keyword tags */}
          {rawKeywords.length > 0 && (
            <div className="result-section">
              <h3 className="result-label">{t('result.keywords')}</h3>
              <div className="keywords-container">
                {rawKeywords.map((kw, i) => (
                  <span key={i} className="keyword-tag">{kw}</span>
                ))}
              </div>
            </div>
          )}

          {/* Keyword explanations */}
          {keywordSummaryItems.length > 0 ? (
            <div className="result-section">
              <div className="result-header">
                <h3 className="result-label">{t('result.keywordSummary')}</h3>
                <CopyButton text={result.keyword_summary || ''} field="keyword_summary" />
              </div>
              <div className="keyword-summary-list">
                {keywordSummaryItems.map((item, i) => (
                  <div key={i} className="keyword-summary-item">
                    <span className="keyword-summary-word">{item.word}</span>
                    <span className="keyword-summary-desc">{item.desc}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : result.keyword_summary ? (
            <div className="result-section">
              <div className="result-header">
                <h3 className="result-label">{t('result.keywordSummary')}</h3>
                <CopyButton text={result.keyword_summary} field="keyword_summary" />
              </div>
              <p className="result-text result-text-pre">{result.keyword_summary}</p>
            </div>
          ) : null}
        </div>
      )}

      {/* TAB: AI Prompts */}
      {activeTab === 'prompts' && (
        <div className="tab-content">
          <div className="result-section">
            <div className="result-header">
              <h3 className="result-label">{t('result.prompt')}</h3>
              <CopyButton text={result.generated_prompt} field="prompt" />
            </div>
            <div className="prompt-box">{result.generated_prompt}</div>
          </div>
          {result.detailed_prompt && (
            <div className="result-section">
              <div className="result-header">
                <h3 className="result-label">{t('result.detailedPrompt')}</h3>
                <CopyButton text={result.detailed_prompt} field="detailed_prompt" />
              </div>
              <div className="prompt-box prompt-box-detailed">{result.detailed_prompt}</div>
            </div>
          )}
        </div>
      )}

      {/* TAB: Detaylar */}
      {activeTab === 'details' && (
        <div className="tab-content">
          {keyQuotes.length > 0 && (
            <div className="result-section">
              <h3 className="result-label">{t('result.keyQuotes')}</h3>
              <ul className="quotes-list">
                {keyQuotes.map((q, i) => (
                  <li key={i} className="quote-item">"{q}"</li>
                ))}
              </ul>
            </div>
          )}
          {actionItems.length > 0 && (
            <div className="result-section">
              <h3 className="result-label">{t('result.actionItems')}</h3>
              <ul className="action-list">
                {actionItems.map((item, i) => (
                  <li key={i} className="action-item">
                    <span className="action-bullet">→</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {(!keyQuotes.length && !actionItems.length) && (
            <p className="result-text" style={{ color: 'var(--color-text-muted)' }}>
              Bu analiz için alıntı veya aksiyon maddesi bulunamadı.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
