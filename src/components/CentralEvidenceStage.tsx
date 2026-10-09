import { useState, useEffect } from 'react';
import type { AnalyzeResponse } from '../api/types';
import { formatDate, truncateHash } from '../utils/display';

interface Props {
  file: File | null;
  result: AnalyzeResponse | null;
  isAnalyzing: boolean;
  focusedObservation: string | null;
  onClearFocus: () => void;
  onReplaceFile: () => void;
}

export function CentralEvidenceStage({
  file,
  result,
  isAnalyzing,
  focusedObservation,
  onClearFocus,
  onReplaceFile,
}: Props) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState(false);

  useEffect(() => {
    if (!file) {
      setImageUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setImageUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const copyHash = async () => {
    if (!result?.photo_hash) return;
    try {
      await navigator.clipboard.writeText(result.photo_hash);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    } catch {
      // clipboard fallback
    }
  };

  if (!imageUrl) return null;

  return (
    <div
      style={{
        position: 'relative',
        background: 'var(--obsidian-ink)',
        border: '1px solid var(--border-medium)',
        borderRadius: 'var(--radius)',
        overflow: 'hidden',
        boxShadow: '0 8px 30px rgba(0, 0, 0, 0.45)',
      }}
    >
      {/* Top Technical Metadata Rail */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '0.5rem 1rem',
          background: 'rgba(18, 26, 32, 0.95)',
          borderBottom: '1px solid var(--border-fine)',
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: 'var(--evidence-grey)',
          flexWrap: 'wrap',
          gap: 6,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ color: 'var(--signal-teal)' }}>EVIDENCE_STAGE</span>
          <span>//</span>
          <span
            style={{
              color: 'var(--text)',
              fontWeight: 600,
              maxWidth: 200,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {file?.name}
          </span>
          {file && (
            <span style={{ color: 'var(--text-dim)' }}>
              ({(file.size / 1024).toFixed(0)} KB)
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {isAnalyzing && (
            <span
              style={{
                color: 'var(--signal-teal)',
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
              INSPECTION_IN_FLIGHT
            </span>
          )}

          <button
            type="button"
            onClick={onReplaceFile}
            style={{
              background: 'transparent',
              border: '1px solid var(--border-fine)',
              color: 'var(--evidence-grey)',
              padding: '2px 8px',
              borderRadius: 'var(--radius-xs)',
              cursor: 'pointer',
              fontSize: 10,
              fontFamily: 'var(--font-mono)',
            }}
          >
            Replace Image
          </button>
        </div>
      </div>

      {/* Main Image Viewport with Corner Registration Crosshairs */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          minHeight: 340,
          maxHeight: 520,
          background: '#060A0E',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {/* Corner Registration Optical Crosshairs */}
        <div
          aria-hidden="true"
          style={{
            position: 'absolute',
            top: 10,
            left: 10,
            fontFamily: 'var(--font-mono)',
            fontSize: 16,
            color: 'var(--signal-teal)',
            opacity: 0.6,
            lineHeight: 1,
            pointerEvents: 'none',
          }}
        >
          ⌜
        </div>
        <div
          aria-hidden="true"
          style={{
            position: 'absolute',
            top: 10,
            right: 10,
            fontFamily: 'var(--font-mono)',
            fontSize: 16,
            color: 'var(--signal-teal)',
            opacity: 0.6,
            lineHeight: 1,
            pointerEvents: 'none',
          }}
        >
          ⌝
        </div>
        <div
          aria-hidden="true"
          style={{
            position: 'absolute',
            bottom: 46,
            left: 10,
            fontFamily: 'var(--font-mono)',
            fontSize: 16,
            color: 'var(--signal-teal)',
            opacity: 0.6,
            lineHeight: 1,
            pointerEvents: 'none',
          }}
        >
          ⌞
        </div>
        <div
          aria-hidden="true"
          style={{
            position: 'absolute',
            bottom: 46,
            right: 10,
            fontFamily: 'var(--font-mono)',
            fontSize: 16,
            color: 'var(--signal-teal)',
            opacity: 0.6,
            lineHeight: 1,
            pointerEvents: 'none',
          }}
        >
          ⌟
        </div>

        {/* Primary Photograph */}
        <img
          src={imageUrl}
          alt="Footpath verification evidence under inspection"
          style={{
            width: '100%',
            maxHeight: 520,
            objectFit: 'contain',
            display: 'block',
            transition: 'opacity 0.25s ease',
          }}
        />

        {/* Thin Presentation Scanline during evaluation */}
        {isAnalyzing && (
          <div
            className="scan-line"
            aria-hidden="true"
            style={{ position: 'absolute', zIndex: 10 }}
          />
        )}

        {/* Focused Observation Reticle Banner (when user clicks an observation) */}
        {focusedObservation && (
          <div
            style={{
              position: 'absolute',
              top: '1.25rem',
              left: '1.25rem',
              right: '1.25rem',
              background: 'rgba(11, 16, 20, 0.92)',
              border: '1px solid var(--border-teal)',
              backdropFilter: 'blur(8px)',
              borderRadius: 'var(--radius-xs)',
              padding: '0.625rem 0.875rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              zIndex: 20,
              gap: 8,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ color: 'var(--signal-teal)', fontFamily: 'var(--font-mono)' }}>⌖</span>
              <span
                style={{
                  fontSize: 12,
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--text)',
                }}
              >
                FOCUSED OBSERVATION: <strong>{focusedObservation}</strong>
              </span>
            </div>

            <button
              type="button"
              onClick={onClearFocus}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--evidence-grey)',
                cursor: 'pointer',
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
              }}
            >
              ✕ Clear focus
            </button>
          </div>
        )}
      </div>

      {/* Bottom Telemetry Bar: Separate Capture Time vs Analysis Time */}
      <div
        style={{
          padding: '0.625rem 1rem',
          background: 'var(--deep-surface)',
          borderTop: '1px solid var(--border-fine)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '0.75rem',
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
        }}
      >
        {/* Temporal Evidence Stamp */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          <span style={{ color: 'var(--evidence-grey)' }}>IMAGE CAPTURE DATE:</span>
          {result?.captured_at ? (
            <strong style={{ color: 'var(--text)' }}>
              {formatDate(result.captured_at)}
            </strong>
          ) : (
            <span
              style={{
                color: 'var(--survey-amber)',
                background: 'var(--survey-amber-dim)',
                padding: '1px 6px',
                borderRadius: 'var(--radius-xs)',
              }}
            >
              TIMESTAMP UNKNOWN IN METADATA
            </span>
          )}
        </div>

        {/* Photo SHA-256 Fingerprint */}
        {result?.photo_hash && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ color: 'var(--evidence-grey)' }}>HASH:</span>
            <code style={{ color: 'var(--signal-teal)' }}>
              {truncateHash(result.photo_hash, 12)}
            </code>
            <button
              type="button"
              onClick={copyHash}
              style={{
                background: 'rgba(25, 211, 197, 0.1)',
                border: '1px solid var(--border-teal)',
                color: 'var(--signal-teal)',
                borderRadius: 'var(--radius-xs)',
                cursor: 'pointer',
                padding: '1px 6px',
                fontSize: 10,
                fontFamily: 'var(--font-mono)',
              }}
            >
              {copiedHash ? '✓ Copied' : 'Copy'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
