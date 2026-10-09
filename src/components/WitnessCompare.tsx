import type { Witness, WitnessAgreement } from '../api/types';

interface Props {
  witnessA: Witness;
  witnessB: Witness;
  agreement: WitnessAgreement | undefined;
}

export function WitnessCompare({ witnessA, witnessB, agreement }: Props) {
  // Only render agreement indicator when backend explicitly sends AGREE or DISAGREE
  const showAgreement = agreement === 'AGREE' || agreement === 'DISAGREE';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: 'var(--text)' }}>
          Witness comparison
        </h3>
        {showAgreement && (
          <span
            aria-label={`Witnesses ${agreement === 'AGREE' ? 'agree' : 'disagree'}`}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 5,
              padding: '3px 10px', borderRadius: 999, fontSize: 13, fontWeight: 600,
              background: agreement === 'AGREE' ? 'var(--green-dim)' : 'var(--red-dim)',
              border: `1px solid ${agreement === 'AGREE' ? 'var(--green)' : 'var(--red)'}`,
              color: agreement === 'AGREE' ? 'var(--green)' : 'var(--red)',
            }}
          >
            {agreement === 'AGREE' ? '✓ Agree' : '✗ Disagree'}
          </span>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
        {([witnessA, witnessB] as Witness[]).map((w, i) => (
          <div
            key={i}
            className="glass"
            style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontFamily: 'Space Grotesk', fontWeight: 700, color: 'var(--teal)', fontSize: 13 }}>
                {w.name}
              </span>
              {w.score !== undefined && w.score !== null && (
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  Score: {(w.score * 100).toFixed(0)}%
                </span>
              )}
            </div>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)' }}>
              {w.result}
            </div>
            {w.observations && w.observations.length > 0 && (
              <ul style={{ margin: 0, padding: '0 0 0 1rem', color: 'var(--text-muted)', fontSize: 13 }}>
                {w.observations.map((obs, j) => (
                  <li key={j}>{obs}</li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
