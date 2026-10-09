import { useCallback, useRef, useState, useEffect } from 'react';
import type { SampleImage } from '../api/types';
import { getSamples } from '../api/client';
import { mockGetSamples, mockSamples } from '../api/mock';

const IS_MOCK = import.meta.env.VITE_USE_MOCK === 'true';
const MAX_FILE_SIZE = 15 * 1024 * 1024; // 15MB
const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

interface Props {
  onFile: (file: File) => void;
  onReset: () => void;
  selectedFile: File | null;
  disabled?: boolean;
}

export function UploadZone({ onFile, onReset, selectedFile, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [samples, setSamples] = useState<SampleImage[]>([]);
  const [loadingSample, setLoadingSample] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    const fn = IS_MOCK ? mockGetSamples : () => getSamples(ctrl.signal);
    fn()
      .then(setSamples)
      .catch(() => {
        setSamples(mockSamples);
      });
    return () => ctrl.abort();
  }, []);

  const validateAndSelect = useCallback(
    (file: File) => {
      setValidationError(null);
      if (!ACCEPTED_TYPES.includes(file.type)) {
        setValidationError(
          `Unsupported file format (${file.type || 'unknown'}). Please provide JPEG, PNG, or WebP imagery.`
        );
        return;
      }
      if (file.size > MAX_FILE_SIZE) {
        setValidationError(
          `Image size (${(file.size / (1024 * 1024)).toFixed(1)} MB) exceeds the 15 MB workstation limit.`
        );
        return;
      }
      onFile(file);
    },
    [onFile]
  );

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;
      validateAndSelect(files[0]);
    },
    [validateAndSelect]
  );

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) setDragging(true);
  };
  const onDragLeave = () => setDragging(false);
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (!disabled) handleFiles(e.dataTransfer.files);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      inputRef.current?.click();
    }
  };

  async function loadSampleUrl(url: string, label: string) {
    if (disabled) return;
    setLoadingSample(label);
    setValidationError(null);
    try {
      const res = await fetch(url);
      const blob = await res.blob();
      const file = new File(
        [blob],
        `${label.toLowerCase().replace(/[^a-z0-9]+/g, '_')}.jpg`,
        {
          type: blob.type || 'image/jpeg',
        }
      );
      validateAndSelect(file);
    } catch (err) {
      console.error('Failed to load verification test case', err);
      setValidationError('Failed to load sample image file.');
    } finally {
      setLoadingSample(null);
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Hidden input */}
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        aria-label="Upload footpath photograph for audit"
        style={{ display: 'none' }}
        onChange={e => handleFiles(e.target.files)}
        disabled={disabled}
      />

      {/* Intake Dropzone if no file selected yet */}
      {!selectedFile && (
        <div
          role="button"
          tabIndex={disabled ? -1 : 0}
          aria-label="Upload footpath image — click or drag and drop"
          aria-disabled={disabled}
          onClick={() => !disabled && inputRef.current?.click()}
          onKeyDown={!disabled ? onKeyDown : undefined}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          style={{
            border: `1px dashed ${
              dragging
                ? 'var(--signal-teal)'
                : 'var(--border-medium)'
            }`,
            borderRadius: 'var(--radius)',
            padding: '2.5rem 1.5rem',
            textAlign: 'center',
            cursor: disabled ? 'not-allowed' : 'pointer',
            transition: 'border-color 0.15s, background-color 0.15s',
            background: dragging
              ? 'var(--signal-teal-dim)'
              : 'var(--deep-surface)',
            position: 'relative',
            opacity: disabled ? 0.6 : 1,
          }}
        >
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 'var(--radius-xs)',
              background: 'rgba(25, 211, 197, 0.08)',
              border: '1px solid var(--border-teal)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 0.75rem',
              color: 'var(--signal-teal)',
              fontFamily: 'var(--font-mono)',
              fontSize: 18,
            }}
          >
            ⌖
          </div>

          <div
            style={{
              fontFamily: 'var(--font-display)',
              fontWeight: 700,
              fontSize: 16,
              color: 'var(--text)',
              marginBottom: 4,
            }}
          >
            Select or drag street-level evidence photo
          </div>

          <p
            style={{
              margin: '0 0 0.875rem',
              fontSize: 13,
              color: 'var(--evidence-grey)',
              lineHeight: 1.5,
            }}
          >
            Direct eye-level perspective of footpath segment. JPEG, PNG, or WebP up to 15 MB.
          </p>

          <div
            style={{
              display: 'inline-block',
              background: 'var(--raised-surface)',
              border: '1px solid var(--border-fine)',
              borderRadius: 'var(--radius-xs)',
              padding: '6px 14px',
              fontSize: 12,
              fontWeight: 600,
              fontFamily: 'var(--font-mono)',
              color: 'var(--text)',
            }}
          >
            [ Browse Local Storage ]
          </div>
        </div>
      )}

      {/* Validation Error Banner */}
      {validationError && (
        <div
          role="alert"
          style={{
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-xs)',
            background: 'var(--barrier-coral-dim)',
            border: '1px solid var(--border-coral)',
            color: 'var(--barrier-coral)',
            fontSize: 12,
            fontFamily: 'var(--font-mono)',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <span>⚠ VALIDATION ERROR:</span>
          <span>{validationError}</span>
        </div>
      )}

      {/* Quick Test-Case Selectors */}
      <div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '0.625rem',
          }}
        >
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              color: 'var(--evidence-grey)',
              fontFamily: 'var(--font-mono)',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
            }}
          >
            Benchmark Inspection Test Cases
          </span>
          <span
            style={{
              fontSize: 10,
              color: 'var(--text-dim)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            STAGED PILOT V1
          </span>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(135px, 1fr))',
            gap: '0.625rem',
          }}
        >
          {samples.map(sample => (
            <button
              key={sample.id}
              type="button"
              onClick={() => loadSampleUrl(sample.url, sample.label)}
              disabled={disabled || loadingSample !== null}
              style={{
                background: 'var(--deep-surface)',
                border: '1px solid var(--border-fine)',
                borderRadius: 'var(--radius-xs)',
                padding: '0.5rem',
                textAlign: 'left',
                cursor: disabled ? 'not-allowed' : 'pointer',
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
                transition: 'border-color 0.15s, background-color 0.15s',
              }}
              onMouseOver={e => {
                if (!disabled) {
                  (e.currentTarget as HTMLElement).style.borderColor = 'var(--signal-teal)';
                  (e.currentTarget as HTMLElement).style.background = 'var(--raised-surface)';
                }
              }}
              onMouseOut={e => {
                (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-fine)';
                (e.currentTarget as HTMLElement).style.background = 'var(--deep-surface)';
              }}
            >
              <div
                style={{
                  width: '100%',
                  aspectRatio: '16 / 11',
                  borderRadius: 'var(--radius-xs)',
                  overflow: 'hidden',
                  background: 'var(--obsidian-ink)',
                  position: 'relative',
                }}
              >
                <img
                  src={sample.url}
                  alt={sample.label}
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                    display: 'block',
                  }}
                  loading="lazy"
                />
                {loadingSample === sample.label && (
                  <div
                    style={{
                      position: 'absolute',
                      inset: 0,
                      background: 'rgba(11, 16, 20, 0.8)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 11,
                      color: 'var(--signal-teal)',
                      fontFamily: 'var(--font-mono)',
                    }}
                  >
                    Loading…
                  </div>
                )}
              </div>

              <span
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: 'var(--text)',
                  lineHeight: 1.3,
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                }}
              >
                {sample.label}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
