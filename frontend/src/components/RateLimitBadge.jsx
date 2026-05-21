import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { getRateLimitStatus } from '../services/api';

export default function RateLimitBadge({ refresh }) {
  const { t } = useTranslation();
  const [status, setStatus] = useState(null);

  useEffect(() => {
    getRateLimitStatus()
      .then(setStatus)
      .catch(() => setStatus(null));
  }, [refresh]);

  if (!status) return null;

  const { used, limit, remaining } = status;
  const pct = Math.round((used / limit) * 100);
  const isExhausted = remaining === 0;
  const isLow = remaining === 1;

  const badgeClass = isExhausted
    ? 'rate-badge rate-badge-exhausted'
    : isLow
    ? 'rate-badge rate-badge-low'
    : 'rate-badge rate-badge-ok';

  return (
    <div className={badgeClass} title={t('rateLimit.tooltip', { used, limit })}>
      <span className="rate-badge-icon">{isExhausted ? '🚫' : isLow ? '⚠️' : '✅'}</span>
      <span>
        {t('rateLimit.label', { remaining, limit })}
      </span>
      <div className="rate-bar">
        <div className="rate-bar-fill" style={{ width: `${pct}%`, opacity: isExhausted ? 1 : 0.8 }} />
      </div>
    </div>
  );
}