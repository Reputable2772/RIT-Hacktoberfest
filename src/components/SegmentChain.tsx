import { useEffect, useRef } from 'react';
import type { Segment } from '../api/types';
import { verdictMeta } from '../utils/display';

interface Props {
  segments: Segment[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  highlightId?: string | null;
}

export function SegmentChain({ segments, selectedId, onSelect, highlightId }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll selected chip into view smoothly
  useEffect(() => {
    if (!selectedId || !containerRef.current) return;
    const el = containerRef.current.querySelector<HTMLElement>(`[data-seg="${selectedId}"]`);
    el?.scrollIntoView({ behavior: 'smooth', inline: 'nearest', block: 'nearest' });
  }, [selectedId]);

  if (!segments.length) return null;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: 'var(--evidence-grey)',
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ color: 'var(--signal-teal)' }}>◆</span>
          CORRIDOR TRAVERSAL CHAIN ({segments.length} SECTORS)
        </span>
        <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>
          CLICK OR USE ARROW KEYS TO INSPECT
        </span>
      </div>

      <div
        ref={containerRef}
        role="tablist"
        aria-label="Surveyed corridor segment chain"
        style={{
          display: 'flex',
          alignItems: 'stretch',
          gap: '0.5rem',
          overflowX: 'auto',
          padding: '0.25rem 0 0.5rem',
          scrollbarWidth: 'thin',
          scrollbarColor: 'var(--border-fine) transparent',
        }}
      >
        {segments.map((seg, idx) => {
          const meta = verdictMeta(seg.status);
          const isSelected = seg.id === selectedId;
          const isHighlighted = seg.id === highlightId;
          const sectorTag = `SEC-${String(idx + 1).padStart(2, '0')}`;

          return (
            <button
              key={seg.id}
              data-seg={seg.id}
              role="tab"
              aria-selected={isSelected}
              aria-label={`Sector ${sectorTag}: ${seg.name}, status ${meta.label}`}
              tabIndex={isSelected ? 0 : -1}
              onClick={() => onSelect(seg.id)}
              onKeyDown={e => {
                if (e.key === 'ArrowRight') {
                  const next = segments[idx + 1] ?? segments[0];
                  onSelect(next.id);
                } else if (e.key === 'ArrowLeft') {
                  const prev = segments[idx - 1] ?? segments[segments.length - 1];
                  onSelect(prev.id);
                }
              }}
              style={{
                flexShrink: 0,
                background: isSelected ? 'var(--deep-surface)' : 'rgba(18, 26, 32, 0.65)',
                border: `1px solid ${
                  isSelected
                    ? 'var(--signal-teal)'
                    : isHighlighted
                    ? 'var(--border-amber)'
                    : 'var(--border-fine)'
                }`,
                borderRadius: 'var(--radius-xs)',
                color: isSelected ? 'var(--paper-warm)' : 'var(--paper-muted)',
                cursor: 'pointer',
                padding: '0.5rem 0.75rem',
                display: 'flex',
                flexDirection: 'column',
                gap: 4,
                textAlign: 'left',
                minWidth: 160,
                maxWidth: 220,
                boxShadow: isSelected
                  ? '0 0 12px var(--signal-teal-dim)'
                  : 'none',
                transition: 'all 0.15s cubic-bezier(0.16, 1, 0.3, 1)',
              }}
            >
              {/* Header row: Sector code & status dot */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  width: '100%',
                }}
              >
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: 10,
                    fontWeight: 700,
                    color: isSelected ? 'var(--signal-teal)' : 'var(--evidence-grey)',
                    letterSpacing: '0.04em',
                  }}
                >
                  {sectorTag}
                </span>

                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 4,
                    fontSize: 10,
                    fontWeight: 700,
                    fontFamily: 'var(--font-mono)',
                    color: meta.cssVar,
                  }}
                >
                  <span
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      background: meta.cssVar,
                      boxShadow: isSelected ? `0 0 6px ${meta.cssVar}` : 'none',
                    }}
                    aria-hidden="true"
                  />
                  <span>{meta.label}</span>
                </span>
              </div>

              {/* Segment Name */}
              <div
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  color: isSelected ? 'var(--paper-warm)' : 'var(--paper-muted)',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  maxWidth: '100%',
                }}
                title={seg.name}
              >
                {seg.name}
              </div>

              {/* Centroid coordinates */}
              <div
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 9,
                  color: 'var(--text-dim)',
                }}
              >
                {seg.lat.toFixed(4)}°N, {seg.lon.toFixed(4)}°E
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
