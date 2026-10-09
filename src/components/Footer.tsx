export function Footer() {
  return (
    <footer
      role="contentinfo"
      style={{
        borderTop: '1px solid var(--border-fine)',
        marginTop: '5rem',
        padding: '3.5rem 0 2.5rem',
        position: 'relative',
        zIndex: 2,
        background: 'var(--deep-surface)',
      }}
    >
      <div className="section-container">
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '2.5rem',
            marginBottom: '2.5rem',
          }}
        >
          {/* Brand & Purpose */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <div
                style={{
                  width: 26,
                  height: 26,
                  borderRadius: 'var(--radius-xs)',
                  background: 'var(--signal-teal)',
                  color: 'var(--obsidian-ink)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily: 'var(--font-display)',
                  fontWeight: 800,
                  fontSize: 13,
                }}
              >
                S
              </div>
              <span
                style={{
                  fontFamily: 'var(--font-display)',
                  fontWeight: 700,
                  fontSize: 16,
                  color: 'var(--paper-warm)',
                }}
              >
                Saakshi-Access
              </span>
            </div>
            <p style={{ fontSize: 13, color: 'var(--paper-muted)', lineHeight: 1.7, margin: 0 }}>
              An open civic footpath verification instrument by Team OpenForge.
              Designed for rigorous urban evidence auditing: factual observations, not probabilistic assumptions.
            </p>
          </div>

          {/* Team Credits */}
          <div>
            <h3
              style={{
                fontFamily: 'var(--font-mono)',
                fontWeight: 700,
                fontSize: 11,
                marginBottom: 10,
                color: 'var(--signal-teal)',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
              }}
            >
              Team OpenForge // Bangalore
            </h3>
            <p style={{ fontSize: 13, color: 'var(--paper-muted)', margin: 0, lineHeight: 1.8, fontFamily: 'var(--font-mono)' }}>
              Prakhyath S<br />
              Chiranthan
            </p>
          </div>

          {/* Repository & Stack */}
          <div>
            <h3
              style={{
                fontFamily: 'var(--font-mono)',
                fontWeight: 700,
                fontSize: 11,
                marginBottom: 10,
                color: 'var(--evidence-grey)',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
              }}
            >
              Core Architecture
            </h3>
            <p style={{ fontSize: 12, color: 'var(--paper-muted)', margin: 0, lineHeight: 1.8, fontFamily: 'var(--font-mono)' }}>
              FastAPI Deterministic Verdict Gate<br />
              OpenCV Laplacian Quality Filter<br />
              Gemma 4 Multimodal Spatial Vision<br />
              OpenStreetMap Vector Geometries
            </p>
          </div>
        </div>

        {/* Bottom Bar & Strict Legal Disclaimer */}
        <div
          style={{
            borderTop: '1px solid var(--border-fine)',
            paddingTop: '1.5rem',
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'space-between',
            gap: '1rem',
            fontSize: 12,
            color: 'var(--evidence-grey)',
            alignItems: 'center',
          }}
        >
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>
            Map vector data & tiles ©{' '}
            <a
              href="https://www.openstreetmap.org/copyright"
              target="_blank"
              rel="noreferrer"
              style={{ color: 'var(--signal-teal)', textDecoration: 'none' }}
            >
              OpenStreetMap
            </a>{' '}
            contributors
          </div>

          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>
            Apache 2.0 Licence · Team OpenForge
          </div>

          <div
            role="note"
            style={{
              color: 'var(--evidence-grey)',
              maxWidth: 480,
              lineHeight: 1.5,
              fontSize: 11,
              background: 'rgba(11, 16, 20, 0.4)',
              padding: '6px 10px',
              borderRadius: 'var(--radius-xs)',
              border: '1px solid var(--border-fine)',
            }}
          >
            <strong style={{ color: 'var(--survey-amber)' }}>Civic decision support only:</strong>{' '}
            Not legal advice or pedestrian safety certification. Records conditions strictly at captured image timestamp;
            never predicts dynamic route clearance or individual accessibility.
          </div>
        </div>
      </div>
    </footer>
  );
}
