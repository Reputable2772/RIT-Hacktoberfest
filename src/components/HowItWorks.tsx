import { motion } from 'framer-motion';

interface Stage {
  step: string;
  title: string;
  subtitle: string;
  mechanism: string;
  qualityNote?: string;
  status: 'IMPLEMENTED' | 'PLANNED';
  highlight?: boolean;
}

const STAGES: Stage[] = [
  {
    step: '01',
    title: 'Image Intake & Cryptographic Fingerprinting',
    subtitle: 'Provenance integrity & temporal validation',
    mechanism:
      'Pedestrian photograph ingested with camera EXIF metadata. Generates an immutable SHA-256 hash. Flags missing or unverified timestamps to prevent temporal misrepresentation.',
    status: 'IMPLEMENTED',
  },
  {
    step: '02',
    title: 'Pre-Gate Quality Checks (OpenCV)',
    subtitle: 'Optical viability filtering prior to inference',
    mechanism:
      'Calculates Laplacian blur variance and grayscale exposure histogram dispersion. Rejects motion-blurred or glare-saturated frames before invoking neural networks.',
    qualityNote:
      'CRITICAL AUDIT PRINCIPLE: OpenCV image-quality measurements assess optical viability only. They are NOT independent semantic confirmation of a physical barrier.',
    status: 'IMPLEMENTED',
  },
  {
    step: '03',
    title: 'Semantic Observation (Gemma 4)',
    subtitle: 'Multimodal spatial observation of walkway conditions',
    mechanism:
      'Gemma 4 multimodal model examines physical walkway geometry, evaluating walking line continuity, usable width (>1.2m), vehicular parking encroachment, construction debris, and pavement steps.',
    status: 'IMPLEMENTED',
  },
  {
    step: '04',
    title: 'Deterministic Decision Gate',
    subtitle: 'Hard-coded civic decision gate in Python backend',
    mechanism:
      'A rigid deterministic gate evaluates structured observations against conservative civic thresholds (confidence ≥ 0.75, quality passed). Prevents LLM hallucinations; defaults to INCONCLUSIVE on ambiguity.',
    status: 'IMPLEMENTED',
    highlight: true,
  },
  {
    step: '05',
    title: 'Civic Audit Record & Disclaimers',
    subtitle: 'Immutable record generation with strict legal boundary',
    mechanism:
      'Yields BARRIER, CLEAR_OBSERVED, INCONCLUSIVE, or UNVERIFIED. Enforces the strict rule: NEVER labels a path "safe" or "accessible." The record is strictly valid for the moment of camera capture.',
    status: 'IMPLEMENTED',
  },
];

const CAPABILITIES = [
  {
    category: 'ACTIVE IN PILOT',
    statusTag: 'VERIFIED IMPLEMENTATION',
    isImplemented: true,
    items: [
      'Single-frame photographic intake with SHA-256 fingerprinting',
      'OpenCV Laplacian blur variance and exposure histogram pre-filter',
      'Gemma 4 multimodal spatial observation extraction',
      'Deterministic refusal gate preventing false reassurance',
      'Corridor segment mapping on OpenStreetMap basemap',
    ],
  },
  {
    category: 'PLANNED / EXCLUDED BY DESIGN',
    statusTag: 'OUT OF SCOPE OR PHASE 2',
    isImplemented: false,
    items: [
      'Multi-frame LiDAR / Stereo depth point clouds (Planned Phase 2)',
      'Automated BBMP civic grievance ticket generation (Planned API v2)',
      'Real-time BMTC bus & BMRCL metro timetable overlays (Uncoupled from pilot)',
      'Pedestrian turn-by-turn routing (Intentionally excluded: Saakshi is an audit instrument, not a navigator)',
    ],
  },
];

export function HowItWorks() {
  return (
    <section
      id="how-it-works"
      aria-label="Verification Pipeline Architecture and Scientific Methodology"
      className="section-paper"
      style={{
        padding: '6rem 0 5.5rem',
        position: 'relative',
        zIndex: 2,
      }}
    >
      <div className="section-container">
        {/* Editorial Section Header */}
        <div style={{ marginBottom: '3.5rem' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              fontWeight: 600,
              color: 'var(--paper-text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              marginBottom: '0.75rem',
            }}
          >
            <span>METHODOLOGY SPECIFICATION</span>
            <span style={{ color: 'var(--paper-text-dark)' }}>//</span>
            <span>EVIDENCE INVESTIGATION PIPELINE</span>
          </div>

          <h2
            style={{
              fontSize: 'clamp(2rem, 4vw, 2.75rem)',
              fontWeight: 700,
              margin: '0 0 0.75rem',
              color: 'var(--paper-text-dark)',
              lineHeight: 1.15,
            }}
          >
            An Evidence Investigation
          </h2>
          <p
            style={{
              color: 'var(--paper-text-muted)',
              margin: 0,
              maxWidth: 720,
              fontSize: '1.05rem',
              lineHeight: 1.6,
            }}
          >
            Footpath verification is structured as a sequential forensic investigation. Each piece of evidence
            passes through strict pre-gate filtering, semantic inspection, and deterministic decision gates.
          </p>
        </div>

        {/* Connected Sequential Timeline */}
        <div
          role="list"
          aria-label="5-stage evidence verification sequence"
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '1.5rem',
            position: 'relative',
            marginBottom: '4rem',
          }}
        >
          {/* Subtle vertical connector spine */}
          <div
            style={{
              position: 'absolute',
              left: 24,
              top: 24,
              bottom: 24,
              width: 2,
              background: 'linear-gradient(180deg, rgba(11, 16, 20, 0.4), rgba(11, 16, 20, 0.15))',
              display: 'none', // Shown on desktop via media query or inline flex
            }}
            className="hidden md:block"
            aria-hidden="true"
          />

          {STAGES.map((stage, idx) => (
            <motion.div
              key={stage.step}
              role="listitem"
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-40px' }}
              transition={{ delay: idx * 0.08, duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
              style={{
                background: stage.highlight ? '#FFFFFF' : 'rgba(255, 255, 255, 0.78)',
                border: `1px solid ${
                  stage.highlight ? 'rgba(11, 16, 20, 0.45)' : 'var(--border-paper)'
                }`,
                borderRadius: 'var(--radius)',
                padding: '1.5rem',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))',
                gap: '1.5rem',
                alignItems: 'flex-start',
                boxShadow: stage.highlight
                  ? '0 6px 20px rgba(11, 16, 20, 0.08)'
                  : '0 2px 8px rgba(11, 16, 20, 0.03)',
                position: 'relative',
              }}
            >
              {/* Left Column: Number, Title, Status */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 12,
                      fontWeight: 700,
                      background: stage.highlight ? 'var(--obsidian-ink)' : 'rgba(11, 16, 20, 0.08)',
                      color: stage.highlight ? 'var(--paper-warm)' : 'var(--paper-text-dark)',
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-xs)',
                    }}
                  >
                    STAGE {stage.step}
                  </span>

                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 10,
                      fontWeight: 700,
                      color: 'var(--paper-text-muted)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                    }}
                  >
                    // {stage.status}
                  </span>

                  {stage.highlight && (
                    <span
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: 9,
                        fontWeight: 700,
                        background: '#FF6268',
                        color: '#FFFFFF',
                        padding: '1px 6px',
                        borderRadius: 2,
                        textTransform: 'uppercase',
                      }}
                    >
                      DETERMINISTIC CORE
                    </span>
                  )}
                </div>

                <h3
                  style={{
                    margin: '0 0 4px',
                    fontFamily: 'var(--font-display)',
                    fontSize: 18,
                    fontWeight: 700,
                    color: 'var(--paper-text-dark)',
                    lineHeight: 1.25,
                  }}
                >
                  {stage.title}
                </h3>

                <div
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: 11,
                    color: 'var(--paper-text-muted)',
                  }}
                >
                  {stage.subtitle}
                </div>
              </div>

              {/* Right Column: Mechanism & OpenCV Quality Distinction */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <p
                  style={{
                    margin: 0,
                    fontSize: 13,
                    color: 'var(--paper-text-dark)',
                    lineHeight: 1.6,
                  }}
                >
                  {stage.mechanism}
                </p>

                {/* Explicit OpenCV Quality Measurement Distinction */}
                {stage.qualityNote && (
                  <div
                    style={{
                      background: 'rgba(255, 180, 84, 0.12)',
                      border: '1px solid rgba(255, 180, 84, 0.4)',
                      borderRadius: 'var(--radius-xs)',
                      padding: '8px 12px',
                      fontSize: 11,
                      color: 'var(--paper-text-dark)',
                      lineHeight: 1.5,
                      fontFamily: 'var(--font-mono)',
                    }}
                  >
                    <strong style={{ color: '#B45309' }}>⚠ AUDIT DISTINCTION:</strong>{' '}
                    {stage.qualityNote}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Distinct Implemented vs Planned Capabilities Matrix */}
        <div
          style={{
            background: '#FFFFFF',
            border: '1px solid var(--border-paper)',
            borderRadius: 'var(--radius)',
            padding: '2rem',
            boxShadow: '0 4px 16px rgba(11, 16, 20, 0.04)',
          }}
        >
          <div style={{ marginBottom: '1.5rem' }}>
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
                color: 'var(--paper-text-muted)',
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                marginBottom: 4,
              }}
            >
              SYSTEM BOUNDARIES & CAPABILITY DISCLOSURE
            </div>
            <h3
              style={{
                margin: 0,
                fontFamily: 'var(--font-display)',
                fontSize: 20,
                fontWeight: 700,
                color: 'var(--paper-text-dark)',
              }}
            >
              Distinguishing Implemented Capabilities from Future Scope
            </h3>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 320px), 1fr))',
              gap: '1.5rem',
            }}
          >
            {CAPABILITIES.map(cap => (
              <div
                key={cap.category}
                style={{
                  background: cap.isImplemented ? 'rgba(25, 211, 197, 0.04)' : 'rgba(11, 16, 20, 0.03)',
                  border: `1px solid ${
                    cap.isImplemented ? 'rgba(25, 211, 197, 0.35)' : 'var(--border-paper)'
                  }`,
                  borderRadius: 'var(--radius-xs)',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 11,
                      fontWeight: 700,
                      color: 'var(--paper-text-dark)',
                    }}
                  >
                    {cap.category}
                  </span>

                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 9,
                      fontWeight: 700,
                      padding: '2px 6px',
                      borderRadius: 2,
                      background: cap.isImplemented ? 'var(--obsidian-ink)' : 'rgba(11, 16, 20, 0.12)',
                      color: cap.isImplemented ? 'var(--paper-warm)' : 'var(--paper-text-muted)',
                    }}
                  >
                    {cap.statusTag}
                  </span>
                </div>

                <ul
                  style={{
                    margin: 0,
                    paddingLeft: '1.25rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 6,
                    fontSize: 12,
                    color: 'var(--paper-text-dark)',
                    lineHeight: 1.5,
                  }}
                >
                  {cap.items.map(item => (
                    <li key={item}>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
