import { useState, useEffect } from 'react';
import type { BenchmarkResponse } from '../api/types';
import { getBenchmark } from '../api/client';
import { mockGetBenchmark } from '../api/mock';

const IS_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

export interface UseBenchmarkReturn {
  data: BenchmarkResponse | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useBenchmark(): UseBenchmarkReturn {
  const [data, setData] = useState<BenchmarkResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    setError(null);

    const run = IS_MOCK
      ? () => mockGetBenchmark()
      : () => getBenchmark(ctrl.signal);

    run()
      .then(d => {
        if (ctrl.signal.aborted) return;
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        if (ctrl.signal.aborted) return;
        setError(err instanceof Error ? err.message : 'Failed to load benchmark data.');
        setLoading(false);
      });

    return () => ctrl.abort();
  }, [tick]);

  return { data, loading, error, refetch: () => setTick((t: number) => t + 1) };
}
