import type { Verdict } from '../api/types';
import { verdictMeta } from '../utils/display';

interface Props {
  verdict: Verdict;
  size?: 'normal' | 'large';
}

export function VerdictBadge({ verdict, size = 'normal' }: Props) {
  const meta = verdictMeta(verdict);
  const isLarge = size === 'large';

  return (
    <div
      className={meta.colorClass}
      role="status"
      aria-label={`Audit Verdict: ${meta.label}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: isLarge ? '0.625rem' : '0.4rem',
        padding: isLarge ? '0.5rem 1rem' : '0.25rem 0.625rem',
        borderRadius: 'var(--radius-xs)',
        fontFamily: 'var(--font-mono)',
        fontWeight: 700,
        fontSize: isLarge ? '1rem' : '0.8rem',
        letterSpacing: '0.05em',
        textTransform: 'uppercase',
        width: 'fit-content',
      }}
    >
      <span aria-hidden="true" style={{ fontSize: isLarge ? '1.1em' : '0.9em' }}>
        {meta.icon}
      </span>
      <span>{meta.label}</span>
    </div>
  );
}
