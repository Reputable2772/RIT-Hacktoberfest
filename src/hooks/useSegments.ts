import { useState, useEffect } from 'react';
import type { Segment } from '../api/types';
import { getSegments } from '../api/client';
import { mockGetSegments } from '../api/mock';

const IS_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

export interface UseSegmentsReturn {
  segments: Segment[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useSegments(): UseSegmentsReturn {
  const [segments, setSegments] = useState<Segment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    setError(null);

    const run = IS_MOCK
      ? () => mockGetSegments()
      : () => getSegments(ctrl.signal);

    run()
      .then(d => {
        if (ctrl.signal.aborted) return;
        setSegments(d);
        setLoading(false);
      })
      .catch(err => {
        if (ctrl.signal.aborted) return;
        setError(err instanceof Error ? err.message : 'Failed to load segments.');
        setLoading(false);
      });

    return () => ctrl.abort();
  }, [tick]);

  return { segments, loading, error, refetch: () => setTick((t: number) => t + 1) };
}
