import { useState, useEffect } from 'react';

const IS_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

const links = [
  { label: 'Analyze', href: '#analyze' },
  { label: 'Transit Corridors', href: '#corridors' },
];


export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-200 ${
        scrolled
          ? 'bg-[var(--deep-surface)]/90 backdrop-blur-md border-b border-[var(--border-fine)]'
          : 'bg-transparent border-b border-transparent'
      }`}
    >
      {/* Integrated Compact Amber Status Strip */}
      {IS_MOCK && (
        <div
          role="status"
          aria-live="polite"
          style={{
            background: 'rgba(255, 180, 84, 0.08)',
            borderBottom: '1px solid var(--border-amber)',
            color: 'var(--survey-amber)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: '4px 16px',
            fontSize: '11px',
            fontWeight: 600,
            fontFamily: 'var(--font-mono)',
            letterSpacing: '0.06em',
            textTransform: 'uppercase',
          }}
        >
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: 'var(--survey-amber)',
              boxShadow: '0 0 6px var(--survey-amber)',
            }}
          />
          <span>SIMULATION MODE // SYNTHETIC AUDIT TELEMETRY ACTIVE — DO NOT USE FOR ROUTING</span>
        </div>
      )}

      <div
        className="section-container"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '1rem',
          padding: '0.75rem 1.5rem',
        }}
      >
        {/* Brand & Instrument Callout */}
        <a
          href="#hero"
          aria-label="Saakshi — Urban Evidence Lab"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.625rem',
            textDecoration: 'none',
          }}
        >
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: 'var(--radius-xs)',
              background: 'var(--signal-teal)',
              color: 'var(--obsidian-ink)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: 'var(--font-display)',
              fontWeight: 800,
              fontSize: 14,
            }}
          >
            S
          </div>

          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span
              style={{
                fontFamily: 'var(--font-display)',
                fontWeight: 700,
                fontSize: 17,
                color: 'var(--text)',
                letterSpacing: '-0.02em',
                lineHeight: 1.1,
              }}
            >
              Saakshi
            </span>
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                color: 'var(--evidence-grey)',
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
              }}
            >
              Urban Evidence Lab
            </span>
          </div>
        </a>

        {/* Civic Project Tags */}
        <span
          style={{
            background: 'var(--signal-teal-dim)',
            border: '1px solid var(--border-teal)',
            color: 'var(--signal-teal)',
            fontSize: 11,
            fontWeight: 600,
            padding: '2px 8px',
            borderRadius: 'var(--radius-xs)',
            fontFamily: 'var(--font-mono)',
            letterSpacing: '0.04em',
            marginLeft: 4,
          }}
        >
          OpenForge
        </span>

        <span
          style={{
            background: 'rgba(166, 176, 187, 0.08)',
            border: '1px solid var(--border-fine)',
            color: 'var(--evidence-grey)',
            fontSize: 11,
            fontWeight: 500,
            padding: '2px 8px',
            borderRadius: 'var(--radius-xs)',
            fontFamily: 'var(--font-mono)',
            letterSpacing: '0.04em',
          }}
          className="hidden-mobile"
        >
          PILOT // BLR-CORE
        </span>

        {/* Navigation links */}
        <nav
          role="navigation"
          aria-label="Main navigation"
          style={{
            display: 'flex',
            gap: '0.5rem',
            marginLeft: 'auto',
            alignItems: 'center',
          }}
          className="hidden-mobile"
        >
          {links.map(l => (
            <a
              key={l.href}
              href={l.href}
              style={{
                color: 'var(--evidence-grey)',
                textDecoration: 'none',
                fontSize: 13,
                fontWeight: 500,
                padding: '6px 12px',
                borderRadius: 'var(--radius-xs)',
                transition: 'color 0.15s, background-color 0.15s',
              }}
              onMouseOver={e => {
                (e.currentTarget as HTMLElement).style.color = 'var(--text)';
                (e.currentTarget as HTMLElement).style.background = 'rgba(255, 255, 255, 0.04)';
              }}
              onMouseOut={e => {
                (e.currentTarget as HTMLElement).style.color = 'var(--evidence-grey)';
                (e.currentTarget as HTMLElement).style.background = 'transparent';
              }}
            >
              {l.label}
            </a>
          ))}
        </nav>

        {/* Mobile menu toggle */}
        <button
          aria-label={open ? 'Close menu' : 'Open menu'}
          aria-expanded={open}
          onClick={() => setOpen(o => !o)}
          style={{
            marginLeft: 'auto',
            background: 'none',
            border: '1px solid var(--border-fine)',
            borderRadius: 'var(--radius-xs)',
            cursor: 'pointer',
            color: 'var(--text)',
            padding: '6px 10px',
            display: 'none',
          }}
          className="show-mobile"
        >
          {open ? '✕' : '☰'}
        </button>
      </div>

      {/* Mobile drawer */}
      {open && (
        <nav
          role="navigation"
          aria-label="Mobile navigation"
          style={{
            background: 'var(--deep-surface)',
            borderTop: '1px solid var(--border-fine)',
            padding: '0.75rem 1.5rem 1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem',
          }}
        >
          {links.map(l => (
            <a
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              style={{
                color: 'var(--text)',
                textDecoration: 'none',
                padding: '8px 12px',
                borderRadius: 'var(--radius-xs)',
                fontSize: 14,
                border: '1px solid var(--border-fine)',
                background: 'rgba(255, 255, 255, 0.02)',
              }}
            >
              {l.label}
            </a>
          ))}
        </nav>
      )}

      <style>{`
        @media (max-width: 640px) {
          .hidden-mobile { display: none !important; }
          .show-mobile   { display: flex !important; }
        }
        @media (min-width: 641px) {
          .show-mobile { display: none !important; }
        }
      `}</style>
    </header>
  );
}
