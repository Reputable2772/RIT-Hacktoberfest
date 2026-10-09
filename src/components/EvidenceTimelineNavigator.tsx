import type { AnalyzeResponse } from '../api/types';

interface Props {
  result: AnalyzeResponse | null;
  isAnalyzing: boolean;
  selectedStage: number;
  onSelectStage: (stage: number) => void;
}

export function EvidenceTimelineNavigator({
  result,
  isAnalyzing,
  selectedStage,
  onSelectStage,
}: Props) {
  const stages = [
    {
      id: 1,
      label: '01 Intake',
      status: result ? 'COMPLETE' : isAnalyzing ? 'IN_PROGRESS' : 'IDLE',
    },
    {
      id: 2,
      label: '02 Pre-Gate Quality',
      status: result
        ? (result.quality?.passed ?? (result as any).image_quality?.passed)
          ? 'PASSED'
          : 'REFUSED'
        : isAnalyzing
        ? 'IN_PROGRESS'
        : 'IDLE',
      color: result
        ? (result.quality?.passed ?? (result as any).image_quality?.passed)
          ? 'var(--signal-teal)'
          : 'var(--barrier-coral)'
        : undefined,
    },
    {
      id: 3,
      label: '03 OpenCV (Witness A)',
      status: result ? 'EVALUATED' : isAnalyzing ? 'IN_PROGRESS' : 'IDLE',
    },
    {
      id: 4,
      label: '04 Gemma 4 (Witness B)',
      status: result ? 'EVALUATED' : isAnalyzing ? 'IN_PROGRESS' : 'IDLE',
    },
    {
      id: 5,
      label: '05 Gate Verdict',
      status: result ? result.verdict : isAnalyzing ? 'IN_PROGRESS' : 'IDLE',
      color: result
        ? result.verdict === 'BARRIER'
          ? 'var(--barrier-coral)'
          : result.verdict === 'CLEAR_OBSERVED'
          ? 'var(--signal-teal)'
          : result.verdict === 'INCONCLUSIVE'
          ? 'var(--survey-amber)'
          : 'var(--evidence-grey)'
        : undefined,
    },
  ];

  return (
    <div
      role="tablist"
      aria-label="Evidence Stage Navigation"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.375rem',
        overflowX: 'auto',
        padding: '0.375rem',
        background: 'var(--deep-surface)',
        border: '1px solid var(--border-fine)',
        borderRadius: 'var(--radius)',
      }}
    >
      {stages.map(st => {
        const isSelected = selectedStage === st.id;

        return (
          <button
            key={st.id}
            role="tab"
            aria-selected={isSelected}
            type="button"
            onClick={() => onSelectStage(st.id)}
            style={{
              flex: 1,
              minWidth: 120,
              padding: '0.5rem 0.625rem',
              background: isSelected
                ? 'var(--raised-surface)'
                : 'transparent',
              border: `1px solid ${
                isSelected
                  ? 'var(--border-medium)'
                  : 'transparent'
              }`,
              borderRadius: 'var(--radius-xs)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
              textAlign: 'left',
              transition: 'background-color 0.15s, border-color 0.15s',
            }}
          >
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                color: isSelected ? 'var(--text)' : 'var(--evidence-grey)',
                fontWeight: 600,
                whiteSpace: 'nowrap',
              }}
            >
              {st.label}
            </span>

            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
                fontWeight: 700,
                color: st.color ?? (isAnalyzing ? 'var(--signal-teal)' : 'var(--text-dim)'),
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                whiteSpace: 'nowrap',
              }}
            >
              {st.status}
            </span>
          </button>
        );
      })}
    </div>
  );
}
