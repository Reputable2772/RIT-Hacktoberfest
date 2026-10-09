import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { useBenchmark } from '../hooks/useBenchmark';

export function BenchmarkSection() {
  const { data, loading, error, refetch } = useBenchmark();
  const [showCliGuide, setShowCliGuide] = useState(false);

  // Check if real evaluated cases are present
  const hasEvaluatedCases = data !== null && data.n > 0;

  // Real comparative ablation data if genuinely available from backend
  const chartData =
    hasEvaluatedCases && data.per_mode
      ? [
          {
            name: 'Correct',
            Classical: data.per_mode.classical.correct,
            Gemma: data.per_mode.gemma.correct,
            Combined: data.per_mode.combined.correct,
          },
          {
            name: 'Missed barriers',
            Classical: data.per_mode.classical.missed_barriers,
            Gemma: data.per_mode.gemma.missed_barriers,
            Combined: data.per_mode.combined.missed_barriers,
          },
          {
            name: 'False reassurance',
            Classical: data.per_mode.classical.false_reassurance_count,
            Gemma: data.per_mode.gemma.false_reassurance_count,
            Combined: data.per_mode.combined.false_reassurance_count,
          },
          {
            name: 'Inconclusive / Refused',
            Classical: data.per_mode.classical.inconclusive_count,
            Gemma: data.per_mode.gemma.inconclusive_count,
            Combined: data.per_mode.combined.inconclusive_count,
          },
        ]
      : null;

  return (
    <section
      id="benchmark"
      aria-label="Evaluation Benchmark & False Reassurance Analysis"
      style={{ padding: '5.5rem 0 4.5rem', position: 'relative', zIndex: 2 }}
    >
      <div className="section-container">
        {/* Section Header */}
        <div style={{ marginBottom: '2.5rem' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              fontWeight: 600,
              color: 'var(--evidence-grey)',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              marginBottom: '0.75rem',
            }}
          >
            <span>SAFETY EVALUATION BENCHMARK</span>
            <span style={{ color: 'var(--signal-teal)' }}>//</span>
            <span>GROUND-TRUTH CORRIDOR SUITE</span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h2
                style={{
                  fontSize: 'clamp(2rem, 4vw, 2.75rem)',
                  fontWeight: 700,
                  margin: '0 0 0.5rem',
                  color: 'var(--paper-warm)',
                  lineHeight: 1.15,
                }}
              >
                How often does the system falsely reassure us?
              </h2>
              <p
                style={{
                  color: 'var(--paper-muted)',
                  marginTop: 0,
                  maxWidth: 680,
                  fontSize: '1.05rem',
                  lineHeight: 1.6,
                }}
              >
                In an urban accessibility audit, false assurance is the critical hazard: declaring an impassable footpath
                clear causes physical entrapment. Our evaluation harness measures false reassurance as the primary safety metric.
              </p>
            </div>

            {/* Sample Size Badge */}
            <div
              style={{
                background: 'var(--deep-surface)',
                border: '1px solid var(--border-fine)',
                borderRadius: 'var(--radius)',
                padding: '0.625rem 1.125rem',
                display: 'flex',
                flexDirection: 'column',
                gap: 2,
              }}
            >
              <span
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 10,
                  color: 'var(--evidence-grey)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                EVALUATION SAMPLE SIZE
              </span>
              <span
                className="count-num"
                style={{
                  fontSize: '1.5rem',
                  fontWeight: 700,
                  color: hasEvaluatedCases ? 'var(--signal-teal)' : 'var(--text-dim)',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {hasEvaluatedCases ? `n = ${data.n} cases` : 'n = 0 (Unpopulated)'}
              </span>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div
            role="status"
            className="lab-panel"
            style={{
              padding: '3rem',
              textAlign: 'center',
              color: 'var(--paper-muted)',
              fontFamily: 'var(--font-mono)',
              fontSize: 13,
            }}
          >
            RETRIEVING BENCHMARK TELEMETRY & CONFUSION MATRIX…
          </div>
        )}

        {/* Error State */}
        {error && (
          <div
            role="alert"
            style={{
              padding: '1.25rem',
              borderRadius: 'var(--radius-xs)',
              background: 'var(--barrier-coral-dim)',
              border: '1px solid var(--border-coral)',
              fontSize: 14,
              marginBottom: '1.5rem',
            }}
          >
            <div style={{ fontWeight: 700, color: 'var(--barrier-coral)', marginBottom: 4 }}>
              Failed to connect to benchmark evaluation service
            </div>
            <div style={{ color: 'var(--paper-muted)', marginBottom: 12 }}>{error}</div>
            <button
              type="button"
              onClick={refetch}
              style={{
                background: 'var(--barrier-coral)',
                border: 'none',
                borderRadius: 'var(--radius-xs)',
                color: '#fff',
                cursor: 'pointer',
                padding: '6px 14px',
                fontWeight: 600,
                fontSize: 12,
                fontFamily: 'var(--font-mono)',
              }}
            >
              RETRY TELEMETRY QUERY
            </button>
          </div>
        )}

        {/* State A: Evaluated Cases Available (n > 0) */}
        {!loading && hasEvaluatedCases && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}
          >
            {/* Visual Centerpiece: False Reassurance Card */}
            <div
              style={{
                background: 'rgba(255, 98, 104, 0.08)',
                border: '1px solid var(--border-coral)',
                borderRadius: 'var(--radius)',
                padding: '1.75rem',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '1.5rem',
                alignItems: 'center',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 10,
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.06em',
                      background: 'var(--barrier-coral-dim)',
                      color: 'var(--barrier-coral)',
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-xs)',
                      border: '1px solid var(--border-coral)',
                    }}
                  >
                    CRITICAL SAFETY INVARIANT
                  </span>
                </div>

                <h3
                  style={{
                    margin: 0,
                    fontFamily: 'var(--font-display)',
                    fontSize: '1.6rem',
                    fontWeight: 700,
                    color: 'var(--paper-warm)',
                  }}
                >
                  False-Reassurance Rate
                </h3>
                <p
                  style={{
                    margin: '0.5rem 0 0',
                    fontSize: 13,
                    color: 'var(--paper-muted)',
                    lineHeight: 1.6,
                    maxWidth: 540,
                  }}
                >
                  Percentage of true physical obstacles falsely classified as unobstructed by the pipeline.
                  A civic audit tool penalizes false clearance over all other confusion categories.
                </p>
              </div>

              <div>
                <div
                  className="count-num"
                  style={{
                    fontSize: 'clamp(2.75rem, 6vw, 4rem)',
                    fontWeight: 700,
                    color: 'var(--barrier-coral)',
                    lineHeight: 1,
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {(data.false_reassurance_rate * 100).toFixed(1)}%
                </div>
                <div
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: 12,
                    color: 'var(--paper-muted)',
                    marginTop: 8,
                  }}
                >
                  {data.false_reassurance_count} false clearances logged out of {data.n} ground-truth test cases
                </div>
              </div>
            </div>

            {/* Supporting Metrics Strip */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '1rem',
              }}
            >
              {/* Correct Detections */}
              <div
                style={{
                  background: 'var(--deep-surface)',
                  border: '1px solid var(--border-fine)',
                  borderRadius: 'var(--radius)',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4,
                }}
              >
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--evidence-grey)' }}>
                  CORRECT DETECTIONS
                </span>
                <span
                  className="count-num"
                  style={{
                    fontSize: '2rem',
                    fontWeight: 700,
                    color: 'var(--signal-teal)',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {data.correct}
                </span>
                <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                  Accurately classified test cases
                </span>
              </div>

              {/* Missed Barriers */}
              <div
                style={{
                  background: 'var(--deep-surface)',
                  border: '1px solid var(--border-fine)',
                  borderRadius: 'var(--radius)',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4,
                }}
              >
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--evidence-grey)' }}>
                  MISSED BARRIERS
                </span>
                <span
                  className="count-num"
                  style={{
                    fontSize: '2rem',
                    fontWeight: 700,
                    color: 'var(--barrier-coral)',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {data.missed_barriers}
                </span>
                <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                  Physical obstacles overlooked
                </span>
              </div>

              {/* Gate Refusals / Inconclusive */}
              <div
                style={{
                  background: 'var(--deep-surface)',
                  border: '1px solid var(--border-fine)',
                  borderRadius: 'var(--radius)',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4,
                }}
              >
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--evidence-grey)' }}>
                  GATE REFUSALS (INCONCLUSIVE)
                </span>
                <span
                  className="count-num"
                  style={{
                    fontSize: '2rem',
                    fontWeight: 700,
                    color: 'var(--survey-amber)',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {data.inconclusive_count}
                </span>
                <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                  Ambiguous cases refused by gate (safe fail)
                </span>
              </div>
            </div>

            {/* Error Breakdown / Confusion Matrix */}
            <div
              style={{
                background: 'var(--deep-surface)',
                border: '1px solid var(--border-fine)',
                borderRadius: 'var(--radius)',
                padding: '1.5rem',
              }}
            >
              <div
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 11,
                  color: 'var(--evidence-grey)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  marginBottom: '1rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span>SAFETY CONFUSION MATRIX // GROUND TRUTH VS GATE VERDICT</span>
                <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>SAFE FAIL PRINCIPLE</span>
              </div>

              <div style={{ overflowX: 'auto' }}>
                <table
                  style={{
                    width: '100%',
                    borderCollapse: 'collapse',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 12,
                  }}
                >
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-fine)', color: 'var(--evidence-grey)' }}>
                      <th style={{ textAlign: 'left', padding: '8px 12px' }}>GROUND TRUTH</th>
                      <th style={{ textAlign: 'center', padding: '8px 12px', color: 'var(--signal-teal)' }}>
                        VERDICT: BARRIER
                      </th>
                      <th style={{ textAlign: 'center', padding: '8px 12px', color: 'var(--barrier-coral)' }}>
                        VERDICT: CLEAR (HAZARD)
                      </th>
                      <th style={{ textAlign: 'center', padding: '8px 12px', color: 'var(--survey-amber)' }}>
                        GATE REFUSAL (INCONCLUSIVE)
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr style={{ borderBottom: '1px solid var(--border-fine)' }}>
                      <td style={{ padding: '10px 12px', color: 'var(--paper-warm)', fontWeight: 600 }}>
                        BARRIER PRESENT
                      </td>
                      <td style={{ textAlign: 'center', padding: '10px 12px', color: 'var(--signal-teal)' }}>
                        ✓ {data.correct - Math.max(0, data.correct - (data.missed_barriers || 0))} (Detected)
                      </td>
                      <td
                        style={{
                          textAlign: 'center',
                          padding: '10px 12px',
                          color: 'var(--barrier-coral)',
                          fontWeight: 700,
                          background: 'rgba(255, 98, 104, 0.1)',
                        }}
                      >
                        ⚠ {data.false_reassurance_count} (FALSE REASSURANCE)
                      </td>
                      <td style={{ textAlign: 'center', padding: '10px 12px', color: 'var(--survey-amber)' }}>
                        {data.inconclusive_count} (Safely Refused)
                      </td>
                    </tr>
                    <tr>
                      <td style={{ padding: '10px 12px', color: 'var(--paper-warm)', fontWeight: 600 }}>
                        CLEAR PATHWAY
                      </td>
                      <td style={{ textAlign: 'center', padding: '10px 12px', color: 'var(--evidence-grey)' }}>
                        Conservative False Flag
                      </td>
                      <td style={{ textAlign: 'center', padding: '10px 12px', color: 'var(--signal-teal)' }}>
                        ✓ Correct Clearance
                      </td>
                      <td style={{ textAlign: 'center', padding: '10px 12px', color: 'var(--survey-amber)' }}>
                        Safely Refused (Low Quality)
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Ablation Comparison Chart (rendered only if genuinely available) */}
            {chartData && (
              <div
                style={{
                  background: 'var(--deep-surface)',
                  border: '1px solid var(--border-fine)',
                  borderRadius: 'var(--radius)',
                  padding: '1.5rem',
                }}
              >
                <h3
                  style={{
                    margin: '0 0 1.25rem',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 12,
                    fontWeight: 600,
                    color: 'var(--paper-warm)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}
                >
                  Ablation Comparison — Classical vs. Gemma vs. Combined Gate
                </h3>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={chartData} margin={{ top: 8, right: 12, left: -16, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="name" tick={{ fill: 'var(--evidence-grey)', fontSize: 11 }} />
                    <YAxis tick={{ fill: 'var(--evidence-grey)', fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{
                        background: 'var(--deep-surface)',
                        border: '1px solid var(--border-fine)',
                        borderRadius: 4,
                        fontFamily: 'var(--font-mono)',
                        fontSize: 12,
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: 11, fontFamily: 'var(--font-mono)' }} />
                    <Bar dataKey="Classical" fill="#6366F1" radius={[2, 2, 0, 0]} />
                    <Bar dataKey="Gemma" fill="var(--signal-teal)" radius={[2, 2, 0, 0]} />
                    <Bar dataKey="Combined" fill="#10B981" radius={[2, 2, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </motion.div>
        )}

        {/* State B: Designed Intentional Empty State (n === 0 or Benchmark Unexecuted) */}
        {!loading && !hasEvaluatedCases && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '1.5rem',
            }}
          >
            {/* Architectural Laboratory Empty State Dossier */}
            <div
              style={{
                background: 'var(--deep-surface)',
                border: '1px solid var(--border-fine)',
                borderRadius: 'var(--radius)',
                padding: '2rem',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              {/* Corner optical reticles */}
              <div style={{ position: 'absolute', top: 8, left: 8, fontFamily: 'var(--font-mono)', color: 'var(--survey-amber)', fontSize: 12 }}>
                ⌜
              </div>
              <div style={{ position: 'absolute', top: 8, right: 8, fontFamily: 'var(--font-mono)', color: 'var(--survey-amber)', fontSize: 12 }}>
                ⌝
              </div>
              <div style={{ position: 'absolute', bottom: 8, left: 8, fontFamily: 'var(--font-mono)', color: 'var(--survey-amber)', fontSize: 12 }}>
                ⌞
              </div>
              <div style={{ position: 'absolute', bottom: 8, right: 8, fontFamily: 'var(--font-mono)', color: 'var(--survey-amber)', fontSize: 12 }}>
                ⌟
              </div>

              <div style={{ maxWidth: 720 }}>
                <div
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '3px 8px',
                    borderRadius: 'var(--radius-xs)',
                    background: 'var(--survey-amber-dim)',
                    border: '1px solid var(--border-amber)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 10,
                    fontWeight: 700,
                    color: 'var(--survey-amber)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.06em',
                    marginBottom: '1rem',
                  }}
                >
                  <span>◆</span>
                  <span>BENCHMARK SUITE INACTIVE // n = 0 CASES LOGGED</span>
                </div>

                <h3
                  style={{
                    margin: '0 0 0.75rem',
                    fontFamily: 'var(--font-display)',
                    fontSize: '1.5rem',
                    fontWeight: 700,
                    color: 'var(--paper-warm)',
                    lineHeight: 1.25,
                  }}
                >
                  No benchmark evaluation run recorded for active instance
                </h3>

                <p
                  style={{
                    color: 'var(--paper-muted)',
                    fontSize: 14,
                    lineHeight: 1.6,
                    margin: '0 0 1.25rem',
                  }}
                >
                  Saakshi-Access never plots fictional bars or displays zeroes as if an evaluation succeeded.
                  When no staged ground-truth evaluation run has been dispatched to <code style={{ color: 'var(--signal-teal)' }}>/api/benchmark</code>,
                  the benchmark telemetry remains in strict laboratory standby.
                </p>

                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '0.75rem',
                    alignItems: 'center',
                  }}
                >
                  <button
                    type="button"
                    onClick={() => setShowCliGuide(!showCliGuide)}
                    style={{
                      background: showCliGuide ? 'var(--signal-teal)' : 'var(--raised-surface)',
                      border: '1px solid var(--border-fine)',
                      borderRadius: 'var(--radius-xs)',
                      color: showCliGuide ? 'var(--obsidian-ink)' : 'var(--paper-warm)',
                      padding: '8px 16px',
                      fontFamily: 'var(--font-mono)',
                      fontSize: 12,
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <span>{showCliGuide ? '▼' : '▶'}</span>
                    <span>HOW TO EXECUTE THE BENCHMARK HARNESS</span>
                  </button>

                  <button
                    type="button"
                    onClick={refetch}
                    style={{
                      background: 'transparent',
                      border: '1px solid var(--border-fine)',
                      borderRadius: 'var(--radius-xs)',
                      color: 'var(--evidence-grey)',
                      padding: '8px 14px',
                      fontFamily: 'var(--font-mono)',
                      fontSize: 12,
                      cursor: 'pointer',
                    }}
                  >
                    REFRESH TELEMETRY STATUS
                  </button>
                </div>
              </div>

              {/* Execution Instructions Drawer / Panel */}
              {showCliGuide && (
                <div
                  style={{
                    marginTop: '1.5rem',
                    padding: '1.25rem',
                    background: 'var(--obsidian-ink)',
                    borderRadius: 'var(--radius-xs)',
                    border: '1px solid var(--border-fine)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 12,
                    lineHeight: 1.6,
                  }}
                >
                  <div style={{ color: 'var(--signal-teal)', fontWeight: 700, marginBottom: 8 }}>
                    // COMMAND-LINE BENCHMARK HARNESS PROTOCOL
                  </div>

                  <div style={{ color: 'var(--evidence-grey)', marginBottom: 12 }}>
                    The evaluation suite requires annotated test cases with ground-truth labels (barrier vs clear) to calculate
                    honest false-reassurance and refusal rates:
                  </div>

                  <ol style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--paper-warm)' }}>
                    <li style={{ marginBottom: 6 }}>
                      <span style={{ color: 'var(--evidence-grey)' }}>Stage ground-truth pedestrian images in test folder:</span>
                      <pre style={{ margin: '4px 0', color: 'var(--signal-teal)', background: 'rgba(25, 35, 42, 0.6)', padding: '4px 8px', borderRadius: 2 }}>
tests/data/annotated_corridor_cases.json
                      </pre>
                    </li>
                    <li style={{ marginBottom: 6 }}>
                      <span style={{ color: 'var(--evidence-grey)' }}>Run the automated evaluation harness:</span>
                      <pre style={{ margin: '4px 0', color: 'var(--signal-teal)', background: 'rgba(25, 35, 42, 0.6)', padding: '4px 8px', borderRadius: 2 }}>
pytest tests/test_benchmark.py --mode=combined --output=benchmark_results.json
                      </pre>
                    </li>
                    <li>
                      <span style={{ color: 'var(--evidence-grey)' }}>
                        Backend service automatically ingests results at <code style={{ color: 'var(--paper-warm)' }}>/api/benchmark</code>.
                      </span>
                    </li>
                  </ol>
                </div>
              )}
            </div>

            {/* Error Breakdown Blueprint: What the Benchmark Measures */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))',
                gap: '1rem',
              }}
            >
              <div
                style={{
                  background: 'rgba(18, 26, 32, 0.6)',
                  border: '1px solid var(--border-fine)',
                  borderRadius: 'var(--radius)',
                  padding: '1.25rem',
                }}
              >
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--barrier-coral)', fontWeight: 700, marginBottom: 4 }}>
                  METRIC 01 // FALSE REASSURANCE
                </div>
                <h4 style={{ margin: '0 0 6px', fontSize: 14, color: 'var(--paper-warm)' }}>
                  Barrier Present → Verdict Clear
                </h4>
                <p style={{ margin: 0, fontSize: 12, color: 'var(--paper-muted)', lineHeight: 1.5 }}>
                  The most catastrophic failure mode. The pedestrian relies on clearance advice and enters an impassable hazard.
                  Target: 0.0%.
                </p>
              </div>

              <div
                style={{
                  background: 'rgba(18, 26, 32, 0.6)',
                  border: '1px solid var(--border-fine)',
                  borderRadius: 'var(--radius)',
                  padding: '1.25rem',
                }}
              >
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--survey-amber)', fontWeight: 700, marginBottom: 4 }}>
                  METRIC 02 // SAFE GATE REFUSALS
                </div>
                <h4 style={{ margin: '0 0 6px', fontSize: 14, color: 'var(--paper-warm)' }}>
                  Ambiguous Evidence → Inconclusive
                </h4>
                <p style={{ margin: 0, fontSize: 12, color: 'var(--paper-muted)', lineHeight: 1.5 }}>
                  When image blur, glare, or witness disagreement creates doubt, the gate rejects classification instead of guessing.
                </p>
              </div>

              <div
                style={{
                  background: 'rgba(18, 26, 32, 0.6)',
                  border: '1px solid var(--border-fine)',
                  borderRadius: 'var(--radius)',
                  padding: '1.25rem',
                }}
              >
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--signal-teal)', fontWeight: 700, marginBottom: 4 }}>
                  METRIC 03 // ABLATION RIGOR
                </div>
                <h4 style={{ margin: '0 0 6px', fontSize: 14, color: 'var(--paper-warm)' }}>
                  Classical vs. Gemma vs. Combined
                </h4>
                <p style={{ margin: 0, fontSize: 12, color: 'var(--paper-muted)', lineHeight: 1.5 }}>
                  Verifies that the combined deterministic gate outperforms any single detector acting in isolation.
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </section>
  );
}
