import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { useBenchmark } from '../hooks/useBenchmark';

const IS_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

function useCountUp(target: number | null, duration = 1200) {
  const [val, setVal] = useState(0);
  const raf = useRef<number | null>(null);

  useEffect(() => {
    if (target === null) return;
    const start = performance.now();
    const animate = (now: number) => {
      const p = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setVal(Math.round(target * eased));
      if (p < 1) raf.current = requestAnimationFrame(animate);
    };
    raf.current = requestAnimationFrame(animate);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
  }, [target, duration]);

  return val;
}

function StatCard({
  label,
  value,
  subtext,
  color,
}: {
  label: string;
  value: number | null;
  subtext: string;
  color: string;
}) {
  const hasRealData = !IS_MOCK && value !== null && value > 0;
  const count = useCountUp(hasRealData ? value : null);

  return (
    <div
      style={{
        background: 'var(--deep-surface)',
        border: '1px solid var(--border-fine)',
        borderRadius: 'var(--radius)',
        padding: '0.875rem 1.125rem',
        minWidth: 130,
        flex: 1,
      }}
    >
      <div
        style={{
          fontSize: 10,
          color: 'var(--evidence-grey)',
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
          marginBottom: 4,
          fontFamily: 'var(--font-mono)',
        }}
      >
        {label}
      </div>
      <div
        className="count-num"
        style={{
          fontSize: '1.75rem',
          fontWeight: 700,
          color: hasRealData ? color : 'var(--text-dim)',
          lineHeight: 1.1,
          fontFamily: 'var(--font-mono)',
        }}
      >
        {hasRealData ? count.toLocaleString() : '—'}
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>
        {hasRealData ? subtext : 'Awaiting benchmark run'}
      </div>
    </div>
  );
}

export function Hero() {
  const { data } = useBenchmark();

  return (
    <section
      id="hero"
      aria-label="Hero section"
      style={{
        paddingTop: '6.5rem',
        paddingBottom: '4.5rem',
        position: 'relative',
        zIndex: 2,
      }}
    >
      <div className="section-container">
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 460px), 1fr))',
            gap: '2.5rem',
            alignItems: 'center',
          }}
        >
          {/* Left Column: Context, Problem Statement, & CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
          >
            {/* Context Badge */}
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '4px 10px',
                borderRadius: 'var(--radius-xs)',
                background: 'var(--signal-teal-dim)',
                border: '1px solid var(--border-teal)',
                color: 'var(--signal-teal)',
                fontSize: 11,
                fontWeight: 600,
                letterSpacing: '0.04em',
                marginBottom: '1.25rem',
                fontFamily: 'var(--font-mono)',
                textTransform: 'uppercase',
              }}
            >
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--signal-teal)' }} />
              URBAN WALKABILITY AUDIT & EVIDENCE VERIFICATION
            </div>

            <h1
              style={{
                fontSize: 'clamp(2.4rem, 5vw, 3.6rem)',
                fontWeight: 700,
                lineHeight: 1.1,
                letterSpacing: '-0.03em',
                marginBottom: '1.25rem',
                color: 'var(--paper-warm)',
                fontFamily: 'var(--font-display)',
              }}
            >
              Evidence,<br />
              <span style={{ color: 'var(--signal-teal)' }}>not assumptions.</span>
            </h1>

            <p
              style={{
                color: 'var(--paper-muted)',
                fontSize: '1.05rem',
                lineHeight: 1.65,
                maxWidth: 540,
                marginBottom: '1.75rem',
              }}
            >
              Saakshi verifies physical conditions from captured street imagery using dual
              independent vision witnesses and a strict deterministic gate.
              It logs whether a barrier was observed at a specific moment in time—
              <strong>it never predicts route suitability, guarantees accessibility, or pronounces a path "safe."</strong>
            </p>

            {/* Primary & Secondary Actions */}
            <div
              style={{
                display: 'flex',
                gap: '0.875rem',
                flexWrap: 'wrap',
                alignItems: 'center',
                marginBottom: '2.25rem',
              }}
            >
              <a
                href="#analyze"
                id="hero-analyze-btn"
                style={{
                  background: 'var(--signal-teal)',
                  color: 'var(--obsidian-ink)',
                  padding: '0.75rem 1.5rem',
                  borderRadius: 'var(--radius-xs)',
                  textDecoration: 'none',
                  fontWeight: 700,
                  fontSize: 14,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                  boxShadow: '0 4px 16px var(--signal-teal-dim)',
                  transition: 'opacity 0.15s, transform 0.15s',
                  fontFamily: 'var(--font-mono)',
                  letterSpacing: '0.02em',
                }}
                onMouseOver={e => {
                  (e.currentTarget as HTMLElement).style.opacity = '0.92';
                  (e.currentTarget as HTMLElement).style.transform = 'translateY(-1px)';
                }}
                onMouseOut={e => {
                  (e.currentTarget as HTMLElement).style.opacity = '1';
                  (e.currentTarget as HTMLElement).style.transform = 'none';
                }}
              >
                <span>🔍</span>
                <span>INSPECT IMAGE EVIDENCE</span>
              </a>

              <a
                href="#corridors"
                id="hero-corridors-btn"
                style={{
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--border-fine)',
                  color: 'var(--paper-warm)',
                  padding: '0.75rem 1.5rem',
                  borderRadius: 'var(--radius-xs)',
                  textDecoration: 'none',
                  fontWeight: 600,
                  fontSize: 14,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                  transition: 'border-color 0.15s, color 0.15s, background 0.15s',
                  fontFamily: 'var(--font-mono)',
                  letterSpacing: '0.02em',
                }}
                onMouseOver={e => {
                  (e.currentTarget as HTMLElement).style.borderColor = 'var(--signal-teal)';
                  (e.currentTarget as HTMLElement).style.color = 'var(--signal-teal)';
                  (e.currentTarget as HTMLElement).style.background = 'var(--signal-teal-dim)';
                }}
                onMouseOut={e => {
                  (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-fine)';
                  (e.currentTarget as HTMLElement).style.color = 'var(--paper-warm)';
                  (e.currentTarget as HTMLElement).style.background = 'rgba(255, 255, 255, 0.03)';
                }}
              >
                <span>🚆</span>
                <span>TRANSIT CORRIDORS</span>
              </a>
            </div>

            {/* Benchmark Summary Telemetry Strip */}
            <div>
              <div
                style={{
                  fontSize: 10,
                  color: 'var(--evidence-grey)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  marginBottom: '0.625rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  fontFamily: 'var(--font-mono)',
                }}
              >
                <span>PILOT EVALUATION TELEMETRY</span>
                <span style={{ height: 1, flex: 1, background: 'var(--border-fine)' }} />
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                <StatCard
                  label="Evaluated"
                  value={data?.n ?? null}
                  subtext="Ground-truth cases"
                  color="var(--signal-teal)"
                />
                <StatCard
                  label="False Reassurance"
                  value={data?.false_reassurance_count ?? null}
                  subtext="Critical error count"
                  color="var(--barrier-coral)"
                />
                <StatCard
                  label="Gate Refusals"
                  value={data?.inconclusive_count ?? null}
                  subtext="Safely refused"
                  color="var(--survey-amber)"
                />
              </div>
            </div>
          </motion.div>

          {/* Right Column: Editorial Photographic Evidence Composition */}
          <motion.div
            initial={{ opacity: 0, scale: 0.99 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            style={{ position: 'relative' }}
          >
            <div
              style={{
                position: 'relative',
                borderRadius: 'var(--radius)',
                overflow: 'hidden',
                border: '1px solid var(--border-fine)',
                background: 'var(--obsidian-ink)',
                boxShadow: '0 20px 48px rgba(0, 0, 0, 0.55)',
              }}
            >
              {/* Evidence Photograph */}
              <img
                src="/images/hero_footpath.jpg"
                alt="Documentary street-level photograph of an urban pedestrian sidewalk with pavement slabs, curb edges, and civic infrastructure"
                style={{
                  width: '100%',
                  height: 'auto',
                  aspectRatio: '16 / 10',
                  objectFit: 'cover',
                  display: 'block',
                }}
              />

              {/* Optical corner reticles */}
              <div style={{ position: 'absolute', top: 6, left: 6, fontFamily: 'var(--font-mono)', color: 'var(--signal-teal)', fontSize: 12 }}>
                ⌜
              </div>
              <div style={{ position: 'absolute', top: 6, right: 6, fontFamily: 'var(--font-mono)', color: 'var(--signal-teal)', fontSize: 12 }}>
                ⌝
              </div>
              <div style={{ position: 'absolute', bottom: 6, left: 6, fontFamily: 'var(--font-mono)', color: 'var(--signal-teal)', fontSize: 12 }}>
                ⌞
              </div>
              <div style={{ position: 'absolute', bottom: 6, right: 6, fontFamily: 'var(--font-mono)', color: 'var(--signal-teal)', fontSize: 12 }}>
                ⌟
              </div>

              {/* Top Evidence Header Strip */}
              <div
                style={{
                  position: 'absolute',
                  top: '0.875rem',
                  left: '0.875rem',
                  right: '0.875rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div
                  style={{
                    background: 'rgba(11, 16, 20, 0.90)',
                    backdropFilter: 'blur(8px)',
                    border: '1px solid var(--border-teal)',
                    borderRadius: 'var(--radius-xs)',
                    padding: '3px 8px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 10,
                    color: 'var(--signal-teal)',
                    letterSpacing: '0.04em',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <span
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      background: 'var(--signal-teal)',
                      boxShadow: '0 0 6px var(--signal-teal)',
                    }}
                  />
                  <span>AUDIT_SPEC // BLR_CORRIDOR_CANONICAL_V1</span>
                </div>

                <div
                  style={{
                    background: 'rgba(11, 16, 20, 0.90)',
                    backdropFilter: 'blur(8px)',
                    border: '1px solid var(--border-fine)',
                    borderRadius: 'var(--radius-xs)',
                    padding: '3px 8px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 10,
                    color: 'var(--evidence-grey)',
                  }}
                >
                  12.9757°N, 77.6074°E
                </div>
              </div>

              {/* Bottom Inspection Card */}
              <div
                style={{
                  position: 'absolute',
                  bottom: '0.875rem',
                  left: '0.875rem',
                  right: '0.875rem',
                  background: 'rgba(11, 16, 20, 0.94)',
                  backdropFilter: 'blur(12px)',
                  border: '1px solid var(--border-fine)',
                  borderRadius: 'var(--radius-xs)',
                  padding: '0.875rem 1rem',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: 4,
                  }}
                >
                  <span
                    style={{
                      fontFamily: 'var(--font-display)',
                      fontWeight: 600,
                      fontSize: 13,
                      color: 'var(--paper-warm)',
                    }}
                  >
                    Visual Verification Pipeline
                  </span>
                  <span
                    style={{
                      fontSize: 10,
                      fontWeight: 700,
                      color: 'var(--signal-teal)',
                      background: 'var(--signal-teal-dim)',
                      border: '1px solid var(--border-teal)',
                      padding: '2px 6px',
                      borderRadius: 'var(--radius-xs)',
                      fontFamily: 'var(--font-mono)',
                    }}
                  >
                    DETERMINISTIC GATE ACTIVE
                  </span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--paper-muted)', lineHeight: 1.5 }}>
                  Continuous edge inspection · Usable clear-width evaluation ·
                  Dual-witness cross-verification against physical blockage.
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
