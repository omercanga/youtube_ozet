import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import AnalyzeForm from './components/AnalyzeForm';
import ManualAnalyzeForm from './components/ManualAnalyzeForm';
import PlaylistForm from './components/PlaylistForm';
import ResultDisplay from './components/ResultDisplay';
import HistoryList from './components/HistoryList';
import { analyzeVideo, analyzeManual, getAnalysisDetail } from './services/api';
import RateLimitBadge from './components/RateLimitBadge';
import './i18n';
import './index.css';

function App() {
  const { t, i18n } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [refreshHistory, setRefreshHistory] = useState(0);
  const [rateLimitRefresh, setRateLimitRefresh] = useState(0);
  const [activeTab, setActiveTab] = useState('youtube');

  const handleAnalyze = async (url) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await analyzeVideo(url);
      setResult(data);
      setRefreshHistory((prev) => prev + 1);
      setRateLimitRefresh((prev) => prev + 1);
    } catch (err) {
      setRateLimitRefresh((prev) => prev + 1);
      setError(err.response?.data?.detail || t('analyze.genericError'));
    } finally {
      setLoading(false);
    }
  };

  const handleManualAnalyze = async (title, transcript, sourceUrl) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await analyzeManual(title, transcript, sourceUrl);
      setResult(data);
      setRefreshHistory((prev) => prev + 1);
      setRateLimitRefresh((prev) => prev + 1);
    } catch (err) {
      setRateLimitRefresh((prev) => prev + 1);
      setError(err.response?.data?.detail || t('analyze.genericError'));
    } finally {
      setLoading(false);
    }
  };

  const handlePlaylistResults = (results) => {
    if (results && results.length > 0) {
      setResult(results[0]);
      setRefreshHistory((prev) => prev + 1);
      setRateLimitRefresh((prev) => prev + 1);
    }
  };

  const handleSelectHistory = async (id) => {
    try {
      const data = await getAnalysisDetail(id);
      setResult(data);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      alert(t('history.detailError') + ': ' + err.message);
    }
  };

  const toggleLanguage = () => {
    const nextLang = i18n.language === 'tr' ? 'en' : 'tr';
    i18n.changeLanguage(nextLang);
  };

  const tabs = [
    { key: 'youtube', label: t('app.tabs.youtube') },
    { key: 'manual', label: t('app.tabs.manual') },
    { key: 'playlist', label: t('app.tabs.playlist') },
  ];

  return (
    <div className="app">
      <div className="container">
        {/* Header */}
        <header className="header">
          <div className="header-content">
            <div>
              <h1 className="header-title">{t('app.title')}</h1>
              <p className="header-subtitle">{t('app.subtitle')}</p>
            </div>
            <div className="header-actions">
              <RateLimitBadge refresh={rateLimitRefresh} />
              <button onClick={toggleLanguage} className="lang-switch" title={t('app.language')}>
                {i18n.language === 'tr' ? '🇬🇧 EN' : '🇹🇷 TR'}
              </button>
            </div>
          </div>
        </header>

        {/* Tab Navigation */}
        <nav className="tabs">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`tab ${activeTab === tab.key ? 'tab-active' : ''}`}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Tab Content */}
        {activeTab === 'youtube' && (
          <AnalyzeForm onAnalyze={handleAnalyze} loading={loading} />
        )}
        {activeTab === 'manual' && (
          <ManualAnalyzeForm onAnalyze={handleManualAnalyze} loading={loading} />
        )}
        {activeTab === 'playlist' && (
          <PlaylistForm
            onResults={handlePlaylistResults}
            loading={loading}
            setLoading={setLoading}
          />
        )}

        {/* Error */}
        {error && (
          <div className="alert alert-error">
            <p className="alert-title">{t('analyze.error')}:</p>
            <p>{error}</p>
          </div>
        )}

        {/* Loading */}
        {loading && activeTab !== 'playlist' && (
          <div className="alert alert-info">
            <div className="loading-spinner" />
            <p>{t('analyze.analyzing')}</p>
          </div>
        )}

        {/* Result */}
        <ResultDisplay result={result} />

        {/* History */}
        <HistoryList refresh={refreshHistory} onSelect={handleSelectHistory} />
      </div>
    </div>
  );
}

export default App;
