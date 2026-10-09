import { useState } from 'react';
import { UploadZone } from './UploadZone';
import { CentralEvidenceStage } from './CentralEvidenceStage';
import { EvidenceTimelineNavigator } from './EvidenceTimelineNavigator';
import { PipelineTracker } from './PipelineTracker';
import { ResultPanel } from './ResultPanel';
import { useAnalyze } from '../hooks/useAnalyze';

export function AnalyzeSection() {
  const [file, setFile] = useState<File | null>(null);
  const [focusedObservation, setFocusedObservation] = useState<string | null>(null);
  const [selectedStage, setSelectedStage] = useState<number>(1);
  const { status, result, error, analyze, cancel, reset } = useAnalyze();

  const isAnalyzing = status === 'analyzing';
  const isDone = status === 'done';
  const isError = status === 'error';
  const isCancelled = status === 'cancelled';

  function handleAnalyze() {
    if (file) {
      setFocusedObservation(null);
      analyze(file);
    }
  }

  function handleReset() {
    setFile(null);
    setFocusedObservation(null);
    setSelectedStage(1);
    reset();
  }

  return (
    <section
      id="analyze"
      aria-label="Evidence Analysis Workspace"
      style={{ padding: '6rem 0 5rem', position: 'relative', zIndex: 2 }}
    >
      <div className="section-container">
        {/* Workspace Editorial Header */}
        <div style={{ marginBottom: '2.5rem' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              fontWeight: 600,
              color: 'var(--signal-teal)',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              marginBottom: '0.75rem',
            }}
          >
            <span>FIELD INSPECTION WORKSTATION</span>
            <span style={{ color: 'var(--border-medium)' }}>//</span>
            <span>DUAL-WITNESS PROTOCOL</span>
          </div>

          <h2
            style={{
              fontSize: 'clamp(2rem, 4vw, 2.75rem)',
              fontWeight: 700,
              margin: '0 0 0.75rem',
              color: 'var(--text)',
              lineHeight: 1.15,
            }}
          >
            Evidence Analysis Workspace
          </h2>
          <p
            style={{
              color: 'var(--evidence-grey)',
              margin: 0,
              maxWidth: 680,
              fontSize: '1.05rem',
              lineHeight: 1.6,
            }}
          >
            Inspect street-level pedestrian photographs against quantitative quality filters,
            independent computer-vision witnesses (OpenCV and Gemma 4), and deterministic decision gates.
            No route safety inferences are ever generated.
          </p>
        </div>

        {/* WORKSPACE LAYOUT */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Top Control Bar: Upload / Select & Actions */}
          <div
            style={{
              background: 'var(--deep-surface)',
              border: '1px solid var(--border-fine)',
              borderRadius: 'var(--radius)',
              padding: '1.25rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}
          >
            <UploadZone
              onFile={newFile => {
                setFile(newFile);
                setFocusedObservation(null);
                setSelectedStage(1);
                reset();
              }}
              onReset={handleReset}
              selectedFile={file}
              disabled={isAnalyzing}
            />

            {/* Execution Buttons if File is Selected */}
            {file && (
              <div
                style={{
                  display: 'flex',
                  gap: '0.75rem',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  borderTop: '1px solid var(--border-fine)',
                  paddingTop: '1rem',
                }}
              >
                <button
                  id="analyze-submit-btn"
                  type="button"
                  onClick={handleAnalyze}
                  disabled={isAnalyzing}
                  aria-disabled={isAnalyzing}
                  style={{
                    flex: '1 1 220px',
                    padding: '0.75rem 1.5rem',
                    background: isAnalyzing
                      ? 'var(--raised-surface)'
                      : 'var(--signal-teal)',
                    color: isAnalyzing ? 'var(--evidence-grey)' : 'var(--obsidian-ink)',
                    border: isAnalyzing
                      ? '1px solid var(--border-fine)'
                      : '1px solid var(--signal-teal)',
                    borderRadius: 'var(--radius-xs)',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    fontSize: 13,
                    letterSpacing: '0.04em',
                    cursor: isAnalyzing ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 8,
                    transition: 'opacity 0.15s, background-color 0.15s',
                  }}
                  onMouseOver={e => {
                    if (!isAnalyzing) {
                      (e.currentTarget as HTMLElement).style.opacity = '0.9';
                    }
                  }}
                  onMouseOut={e => {
                    (e.currentTarget as HTMLElement).style.opacity = '1';
                  }}
                >
                  <span>{isAnalyzing ? '⏳' : '⌖'}</span>
                  <span>
                    {isAnalyzing
                      ? 'INSPECTION IN PROGRESS…'
                      : 'EXECUTE DUAL-WITNESS VERIFICATION'}
                  </span>
                </button>

                <button
                  type="button"
                  onClick={handleReset}
                  disabled={isAnalyzing}
                  style={{
                    padding: '0.75rem 1rem',
                    background: 'transparent',
                    border: '1px solid var(--border-fine)',
                    borderRadius: 'var(--radius-xs)',
                    color: 'var(--evidence-grey)',
                    cursor: isAnalyzing ? 'not-allowed' : 'pointer',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 12,
                  }}
                >
                  [ Clear / Reset ]
                </button>
              </div>
            )}
          </div>

          {/* In-Flight Pipeline Tracker */}
          {isAnalyzing && (
            <PipelineTracker active={isAnalyzing} onCancel={cancel} />
          )}

          {/* Cancelled Banner */}
          {isCancelled && (
            <div
              role="status"
              className="lab-panel"
              style={{
                padding: '1rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontFamily: 'var(--font-mono)',
                fontSize: 12,
                color: 'var(--evidence-grey)',
              }}
            >
              <span>INSPECTION REQUEST CANCELLED BY USER</span>
              <button
                type="button"
                onClick={handleReset}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--signal-teal)',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontFamily: 'inherit',
                }}
              >
                [ Reset Workstation ]
              </button>
            </div>
          )}

          {/* Error Banner */}
          {isError && error && (
            <div
              role="alert"
              style={{
                padding: '1rem 1.25rem',
                borderRadius: 'var(--radius)',
                background: 'var(--barrier-coral-dim)',
                border: '1px solid var(--border-coral)',
                fontFamily: 'var(--font-mono)',
                fontSize: 12.5,
              }}
            >
              <div
                style={{
                  fontWeight: 700,
                  color: 'var(--barrier-coral)',
                  marginBottom: 4,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span>⚠</span>
                <span>PIPELINE VERIFICATION FAILURE</span>
              </div>
              <div style={{ color: 'var(--text)', marginBottom: 10, lineHeight: 1.5 }}>
                {error}
              </div>
              <button
                type="button"
                onClick={handleAnalyze}
                style={{
                  background: 'var(--barrier-coral)',
                  border: 'none',
                  borderRadius: 'var(--radius-xs)',
                  color: '#fff',
                  cursor: 'pointer',
                  padding: '6px 14px',
                  fontWeight: 700,
                  fontSize: 11,
                  fontFamily: 'var(--font-mono)',
                }}
              >
                [ Retry Request ]
              </button>
            </div>
          )}

          {/* Central Image Canvas (The Primary Object) */}
          {file && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <CentralEvidenceStage
                file={file}
                result={result}
                isAnalyzing={isAnalyzing}
                focusedObservation={focusedObservation}
                onClearFocus={() => setFocusedObservation(null)}
                onReplaceFile={handleReset}
              />

              {/* Stage Navigator Timeline */}
              {isDone && result && (
                <EvidenceTimelineNavigator
                  result={result}
                  isAnalyzing={isAnalyzing}
                  selectedStage={selectedStage}
                  onSelectStage={setSelectedStage}
                />
              )}
            </div>
          )}

          {/* Dossier Results Output */}
          {isDone && result && (
            <ResultPanel
              result={result}
              focusedObservation={focusedObservation}
              onFocusObservation={obs => {
                setFocusedObservation(obs);
                // Scroll smoothly up to the evidence stage if on mobile
                const el = document.getElementById('analyze');
                if (el && window.innerWidth < 768) {
                  el.scrollIntoView({ behavior: 'smooth' });
                }
              }}
              selectedStageFilter={selectedStage}
            />
          )}
        </div>
      </div>
    </section>
  );
}
