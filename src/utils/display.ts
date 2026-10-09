import type { Verdict } from '../api/types';

/** Returns { label, icon, colorClass, cssVar } for each verdict status */
export function verdictMeta(verdict: Verdict) {
  switch (verdict) {
    case 'BARRIER':
      return {
        label: 'BARRIER',
        icon: '🚧',
        colorClass: 'chip-barrier',
        cssVar: 'var(--barrier-coral)',
      };
    case 'CLEAR_OBSERVED':
      return {
        label: 'CLEAR OBSERVED',
        icon: '✓',
        colorClass: 'chip-clear',
        cssVar: 'var(--signal-teal)',
      };
    case 'INCONCLUSIVE':
      return {
        label: 'INCONCLUSIVE',
        icon: '?',
        colorClass: 'chip-inconclusive',
        cssVar: 'var(--survey-amber)',
      };
    case 'UNVERIFIED':
      return {
        label: 'UNVERIFIED',
        icon: '○',
        colorClass: 'chip-unverified',
        cssVar: 'var(--evidence-grey)',
      };
  }
}

export function formatDate(iso: string | null): string {
  if (!iso) return 'Capture date unknown';
  try {
    return new Date(iso).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return 'Capture date unknown';
  }
}

export function truncateHash(hash: string, len = 16): string {
  if (hash.length <= len) return hash;
  return hash.slice(0, len) + '…';
}
