import { useState } from 'react';
import { motion } from 'framer-motion';
import type { AnalyzeResponse } from '../api/types';
import { VerdictBadge } from './VerdictBadge';
import { formatDate, truncateHash } from '../utils/display';

interface Props {
  result: AnalyzeResponse;
  focusedObservation: string | null;
  onFocusObservation: (obs: string) => void;
  selectedStageFilter?: number | null;
}

function CopyHashButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  return (
    <button
      type="button"
      onClick={copy}
      aria-label={`Copy SHA-256 fingerprint ${text}`}
      style={{
        background: 'rgba(25, 211, 197, 0.1)',
        border: '1px solid var(--border-teal)',
        borderRadius: 'var(--radius-xs)',
        color: 'var(--signal-teal)',
        cursor: 'pointer',
        padding: '2px 8px',
        fontSize: 11,
        fontWeight: 600,
        fontFamily: 'var(--font-mono)',
      }}
    >
      {copied ? '✓ COPIED' : 'COPY HASH'}
    </button>
  );
}

function RetakeGuide() {
  return (
    <div
      style={{
        padding: '1.25rem',
        borderRadius: 'var(--radius)',
        border: '1px solid var(--border-amber)',
        background: 'var(--survey-amber-dim)',
      }}
    >
      <div
        style={{
          fontFamily: 'var(--font-mono)',
          fontWeight: 700,
          color: 'var(--survey-amber)',
          fontSize: 12,
          marginBottom: '0.625rem',
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
        }}
      >
        <span>📷</span>
        <span>Retake Protocol for Inconclusive Evidence</span>
      </div>
      <ul
        style={{
          margin: 0,
          paddingLeft: '1.25rem',
          fontSize: 12,
          color: 'var(--text)',
          lineHeight: 1.7,
        }}
      >
        <li>Maintain consistent camera height of 1.0–1.2 m perpendicular to footpath slope.</li>
        <li>Avoid harsh single-point headlights, direct lens flare, or extreme dusk shadows.</li>
        <li>Capture the full lateral width between the curb edge and the property line.</li>
        <li>Include a stable architectural reference (lamppost, curbstone) to ground scale.</li>
      </ul>
    </div>
  );
}

export function ResultPanel({
  result,
  focusedObservation,
  onFocusObservation,
  selectedStageFilter,
}: Props) {
  const [limitationsOpen, setLimitationsOpen] = useState(false);

  const quality = result.quality || { passed: false, blur_score: null, exposure_score: null, notes: [] };
  const witnessA = result.witness_a || { name: 'OpenCV (Geometric & Edge)', result: 'Evaluated', score: null, observations: [] };
  const witnessB = result.witness_b || { name: 'Gemma 4 (Vision-Language)', result: result.verdict, score: null, observations: [] };
  const gateReasons = result.gate_reasons || [];

  const captureFormatted = result.captured_at
    ? formatDate(result.captured_at)
    : null;

  // Filter visibility helper
  const showSection = (stageId: number) => {
    return !selectedStageFilter || selectedStageFilter === 1 || selectedStageFilter === stageId;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
      }}
      aria-label="Structured Evidence Dossier"
    >
      {/* Dossier Header & Final Verdict Banner */}
      <div
        style={{
          background:
            result.verdict === 'BARRIER'
              ? 'var(--barrier-coral-dim)'
              : result.verdict === 'CLEAR_OBSERVED'
              ? 'var(--signal-teal-dim)'
              : 'var(--survey-amber-dim)',
          border: `1px solid ${
            result.verdict === 'BARRIER'
              ? 'var(--border-coral)'
              : result.verdict === 'CLEAR_OBSERVED'
              ? 'var(--border-teal)'
              : 'var(--border-amber)'
          }`,
          borderRadius: 'var(--radius)',
          padding: '1.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.875rem',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 8,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
                fontWeight: 700,
                color: 'var(--text-dim)',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
              }}
            >
              FINAL AUDIT VERDICT:
            </span>
            <VerdictBadge verdict={result.verdict} size="large" />
          </div>

          {result.confidence !== null && (
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 12,
                color: 'var(--text)',
              }}
            >
              CONFIDENCE SCORE:{' '}
              <strong style={{ color: 'var(--signal-teal)' }}>
                {(result.confidence * 100).toFixed(0)}%
              </strong>
            </div>
          )}
        </div>

        {result.barrier_type && (
          <div style={{ fontSize: 13, color: 'var(--text)' }}>
            <span style={{ color: 'var(--evidence-grey)' }}>Detected Obstacle Type: </span>
            <strong>{result.barrier_type}</strong>
          </div>
        )}

        <div style={{ fontSize: 13.5, lineHeight: 1.6, color: 'var(--text)' }}>
          {result.verdict === 'CLEAR_OBSERVED' ? (
            <div>
              <strong>No physical barrier observed within the capture frame.</strong>
              <div
                style={{
                  fontSize: 12,
                  color: 'var(--evidence-grey)',
                  marginTop: 4,
                  lineHeight: 1.5,
                }}
              >
                Clear continuous paving identified at {captureFormatted ?? 'image timestamp'}.
                <strong> Note:</strong> this visual observation does not certify the route as accessible
                for all mobility devices, nor does it guarantee present conditions.
              </div>
            </div>
          ) : (
            result.description
          )}
        </div>
      </div>

      {/* Stage 02: Image Quality Pre-Gate Assessment */}
      {showSection(2) && (
        <div
          className="lab-panel"
          style={{
            padding: '1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            <span style={{ color: 'var(--evidence-grey)' }}>
              STAGE 02 // QUALITY PRE-GATE
            </span>
            <span
              style={{
                padding: '2px 8px',
                borderRadius: 'var(--radius-xs)',
                fontSize: 10,
                fontWeight: 700,
                background: quality.passed
                  ? 'var(--signal-teal-dim)'
                  : 'var(--barrier-coral-dim)',
                color: quality.passed
                  ? 'var(--signal-teal)'
                  : 'var(--barrier-coral)',
                border: `1px solid ${
                  quality.passed ? 'var(--border-teal)' : 'var(--border-coral)'
                }`,
              }}
            >
              {quality.passed ? '✓ PRE-GATE PASSED' : '✗ QUALITY REFUSED'}
            </span>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
              gap: '0.625rem',
              background: 'var(--raised-surface)',
              padding: '8px 12px',
              borderRadius: 'var(--radius-xs)',
              border: '1px solid var(--border-fine)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            <div style={{ fontSize: 11 }}>
              <span style={{ color: 'var(--evidence-grey)' }}>Blur Variance: </span>
              <strong style={{ color: 'var(--text)' }}>
                {quality.blur_score !== null && quality.blur_score !== undefined
                  ? quality.blur_score.toFixed(3)
                  : 'N/A'}
              </strong>
            </div>

            <div style={{ fontSize: 11 }}>
              <span style={{ color: 'var(--evidence-grey)' }}>Exposure Index: </span>
              <strong style={{ color: 'var(--text)' }}>
                {quality.exposure_score !== null && quality.exposure_score !== undefined
                  ? quality.exposure_score.toFixed(3)
                  : 'N/A'}
              </strong>
            </div>
          </div>

          <div
            style={{
              fontSize: 11,
              color: 'var(--text-dim)',
              lineHeight: 1.5,
              fontStyle: 'italic',
            }}
          >
            * Technical note: Blur and exposure statistics evaluate photograph legibility only.
            They are pre-gate filter thresholds, not independent semantic proof of a barrier.
          </div>

          {quality.notes && quality.notes.length > 0 && (
            <ul
              style={{
                margin: 0,
                paddingLeft: '1.25rem',
                fontSize: 12,
                color: 'var(--evidence-grey)',
                lineHeight: 1.6,
              }}
            >
              {quality.notes.map((note, idx) => (
                <li key={idx}>{note}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Stage 03 & 04: Dual Witnesses (OpenCV & Gemma 4) */}
      {(showSection(3) || showSection(4)) && (
        <div
          className="lab-panel"
          style={{
            padding: '1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.875rem',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              flexWrap: 'wrap',
              gap: 6,
            }}
          >
            <span style={{ color: 'var(--evidence-grey)' }}>
              STAGE 03 & 04 // DUAL INDEPENDENT WITNESSES
            </span>

            {result.witness_agreement !== 'NOT_EVALUATED' && (
              <span
                style={{
                  fontSize: 10,
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-xs)',
                  background:
                    result.witness_agreement === 'AGREE'
                      ? 'var(--signal-teal-dim)'
                      : 'var(--survey-amber-dim)',
                  color:
                    result.witness_agreement === 'AGREE'
                      ? 'var(--signal-teal)'
                      : 'var(--survey-amber)',
                  border: `1px solid ${
                    result.witness_agreement === 'AGREE'
                      ? 'var(--border-teal)'
                      : 'var(--border-amber)'
                  }`,
                }}
              >
                CORROBORATION: {result.witness_agreement}
              </span>
            )}
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 240px), 1fr))',
              gap: '0.75rem',
            }}
          >
            {/* Witness A: OpenCV Classical Vision */}
            {showSection(3) && (
              <div
                style={{
                  background: 'var(--raised-surface)',
                  border: '1px solid var(--border-fine)',
                  borderRadius: 'var(--radius-xs)',
                  padding: '0.875rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4,
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      color: 'var(--signal-teal)',
                    }}
                  >
                    WITNESS A // {witnessA.name}
                  </span>
                  {witnessA.score !== undefined &&
                    witnessA.score !== null && (
                      <span style={{ fontSize: 11, color: 'var(--evidence-grey)' }}>
                        {(witnessA.score * 100).toFixed(0)}%
                      </span>
                    )}
                </div>

                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginTop: 2 }}>
                  {witnessA.result}
                </div>

                {witnessA.observations &&
                  witnessA.observations.length > 0 && (
                    <ul
                      style={{
                        margin: '4px 0 0',
                        paddingLeft: '1rem',
                        fontSize: 12,
                        color: 'var(--evidence-grey)',
                        lineHeight: 1.5,
                      }}
                    >
                      {witnessA.observations.map((obs, i) => (
                        <li key={i}>{obs}</li>
                      ))}
                    </ul>
                  )}
              </div>
            )}

            {/* Witness B: Gemma 4 Multimodal Vision */}
            {showSection(4) && (
              <div
                style={{
                  background: 'var(--raised-surface)',
                  border: '1px solid var(--border-fine)',
                  borderRadius: 'var(--radius-xs)',
                  padding: '0.875rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4,
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      color: '#93C5FD',
                    }}
                  >
                    WITNESS B // {witnessB.name}
                  </span>
                  <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>
                    SEMANTIC
                  </span>
                </div>

                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginTop: 2 }}>
                  Classification: {witnessB.result}
                </div>

                {witnessB.observations &&
                  witnessB.observations.length > 0 && (
                    <div style={{ marginTop: 4, display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <span
                        style={{
                          fontSize: 11,
                          fontFamily: 'var(--font-mono)',
                          color: 'var(--text-dim)',
                        }}
                      >
                        Interactive Observations (Click to focus):
                      </span>
                      {witnessB.observations.map((obs, i) => {
                        const isFocused = focusedObservation === obs;
                        return (
                          <button
                            key={i}
                            type="button"
                            onClick={() => onFocusObservation(obs)}
                            style={{
                              background: isFocused
                                ? 'var(--signal-teal-dim)'
                                : 'rgba(11, 16, 20, 0.4)',
                              border: `1px solid ${
                                isFocused
                                  ? 'var(--border-teal)'
                                  : 'var(--border-fine)'
                              }`,
                              borderRadius: 'var(--radius-xs)',
                              padding: '4px 8px',
                              textAlign: 'left',
                              cursor: 'pointer',
                              fontSize: 12,
                              color: isFocused ? 'var(--signal-teal)' : 'var(--text)',
                              lineHeight: 1.4,
                              display: 'flex',
                              alignItems: 'center',
                              gap: 6,
                              transition: 'border-color 0.15s, background-color 0.15s',
                            }}
                          >
                            <span style={{ color: 'var(--signal-teal)', fontFamily: 'var(--font-mono)' }}>
                              {isFocused ? '⌖' : '○'}
                            </span>
                            <span>{obs}</span>
                          </button>
                        );
                      })}
                    </div>
                  )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Stage 05: Deterministic Decision Gate Reasoning */}
      {showSection(5) && gateReasons.length > 0 && (
        <div
          className="lab-panel"
          style={{
            padding: '1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.625rem',
          }}
        >
          <div
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              fontWeight: 700,
              color: 'var(--evidence-grey)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            STAGE 05 // DETERMINISTIC GATE DECISION RULES
          </div>

          <ul
            style={{
              margin: 0,
              paddingLeft: '1.25rem',
              fontSize: 12.5,
              color: 'var(--text)',
              lineHeight: 1.7,
            }}
          >
            {gateReasons.map((reason, i) => (
              <li key={i}>
                <span style={{ color: 'var(--signal-teal)', fontFamily: 'var(--font-mono)' }}>
                  ✓
                </span>{' '}
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Retake Guide when INCONCLUSIVE */}
      {result.verdict === 'INCONCLUSIVE' && <RetakeGuide />}

      {/* Provenance & SHA-256 Fingerprint */}
      <div
        className="lab-panel"
        style={{
          padding: '0.875rem 1rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '1rem',
          fontSize: 12,
          flexWrap: 'wrap',
          fontFamily: 'var(--font-mono)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          <span style={{ color: 'var(--evidence-grey)' }}>SHA-256 FINGERPRINT:</span>
          <code style={{ color: 'var(--signal-teal)' }}>
            {truncateHash(result.photo_hash, 16)}
          </code>
          <CopyHashButton text={result.photo_hash} />
        </div>

        <div style={{ color: 'var(--text-dim)' }}>
          SOURCE MODEL // {result.source}
        </div>
      </div>

      {/* Collapsible Audit Limitations & Caveats */}
      {result.limitations.length > 0 && (
        <div className="lab-panel" style={{ overflow: 'hidden' }}>
          <button
            type="button"
            aria-expanded={limitationsOpen}
            aria-controls="limitations-list"
            onClick={() => setLimitationsOpen(!limitationsOpen)}
            style={{
              width: '100%',
              background: 'none',
              border: 'none',
              padding: '0.75rem 1rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              color: 'var(--text)',
              fontSize: 12.5,
              fontWeight: 600,
              fontFamily: 'var(--font-mono)',
              cursor: 'pointer',
            }}
          >
            <span>AUDIT LIMITATIONS & PROTOCOL CAVEATS ({result.limitations.length})</span>
            <span style={{ fontSize: 11, color: 'var(--evidence-grey)' }}>
              {limitationsOpen ? '▲ COLLAPSE' : '▼ EXPAND'}
            </span>
          </button>

          {limitationsOpen && (
            <div
              id="limitations-list"
              style={{
                padding: '0 1rem 0.875rem 1rem',
                borderTop: '1px solid var(--border-fine)',
              }}
            >
              <ul
                style={{
                  margin: '0.5rem 0 0',
                  paddingLeft: '1.25rem',
                  fontSize: 12,
                  color: 'var(--evidence-grey)',
                  lineHeight: 1.7,
                }}
              >
                {result.limitations.map((lim, i) => (
                  <li key={i}>{lim}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Permanent Civic Legal Notice */}
      <div
        role="note"
        aria-label="Civic Decision Support Notice"
        style={{
          padding: '0.625rem 0.875rem',
          borderRadius: 'var(--radius-xs)',
          background: 'rgba(166, 176, 187, 0.05)',
          border: '1px solid var(--border-fine)',
          fontSize: 11,
          color: 'var(--evidence-grey)',
          lineHeight: 1.5,
          fontFamily: 'var(--font-body)',
        }}
      >
        <strong>Civic Decision Support Notice:</strong> Saakshi documents observable surface conditions
        in a singular visual capture. It does not provide continuous pedestrian navigation, calculate
        disability accessibility certification, or promise that any walkway is free of dynamic obstructions.
      </div>
    </motion.div>
  );
}
