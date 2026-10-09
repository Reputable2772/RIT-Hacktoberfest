interface Props {
  active: boolean;
  onCancel: () => void;
}

export function PipelineTracker({ active, onCancel }: Props) {
  if (!active) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label="Evaluation pipeline in progress"
      className="lab-panel"
      style={{
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.875rem',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Presentation Scanline */}
      <div className="scan-line" aria-hidden="true" />

      {/* Header bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontFamily: 'var(--font-mono)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: 'var(--signal-teal)',
              boxShadow: '0 0 8px var(--signal-teal)',
            }}
          />
          <span
            style={{
              fontWeight: 700,
              color: 'var(--signal-teal)',
              fontSize: 12.5,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            DISPATCHING DUAL-WITNESS VERIFICATION
          </span>
        </div>

        <button
          type="button"
          onClick={onCancel}
          aria-label="Cancel pipeline analysis"
          style={{
            background: 'var(--barrier-coral-dim)',
            border: '1px solid var(--border-coral)',
            borderRadius: 'var(--radius-xs)',
            color: 'var(--barrier-coral)',
            cursor: 'pointer',
            padding: '3px 8px',
            fontSize: 11,
            fontWeight: 600,
            fontFamily: 'var(--font-mono)',
            transition: 'background 0.15s',
          }}
        >
          [ Cancel Request ]
        </button>
      </div>

      <div style={{ fontSize: 12.5, color: 'var(--evidence-grey)', lineHeight: 1.55 }}>
        Awaiting single-round atomic response from the verification server:
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '0.625rem',
          fontFamily: 'var(--font-mono)',
        }}
      >
        <div
          style={{
            background: 'var(--raised-surface)',
            border: '1px solid var(--border-fine)',
            borderRadius: 'var(--radius-xs)',
            padding: '8px 10px',
          }}
        >
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text)' }}>
            01 Pre-Gate
          </div>
          <div style={{ fontSize: 10, color: 'var(--evidence-grey)' }}>
            Laplacian blur variance & exposure
          </div>
        </div>

        <div
          style={{
            background: 'var(--raised-surface)',
            border: '1px solid var(--border-fine)',
            borderRadius: 'var(--radius-xs)',
            padding: '8px 10px',
          }}
        >
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text)' }}>
            02 Dual Witnesses
          </div>
          <div style={{ fontSize: 10, color: 'var(--evidence-grey)' }}>
            OpenCV contours + Gemma 4 vision
          </div>
        </div>

        <div
          style={{
            background: 'var(--raised-surface)',
            border: '1px solid var(--border-fine)',
            borderRadius: 'var(--radius-xs)',
            padding: '8px 10px',
          }}
        >
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text)' }}>
            03 Deterministic Gate
          </div>
          <div style={{ fontSize: 10, color: 'var(--evidence-grey)' }}>
            Corroboration & threshold verification
          </div>
        </div>
      </div>

      <div
        style={{
          fontSize: 11,
          color: 'var(--text-dim)',
          fontFamily: 'var(--font-mono)',
          display: 'flex',
          alignItems: 'center',
          gap: 6,
        }}
      >
        <span>⏳ Awaiting HTTP response from /api/analyze…</span>
      </div>
    </div>
  );
}
