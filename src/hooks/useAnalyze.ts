import { useState, useCallback, useRef } from 'react';
import type { AnalyzeResponse } from '../api/types';
import { analyzeImage } from '../api/client';
import { mockAnalyzeImage } from '../api/mock';

const IS_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

export type AnalyzeStatus = 'idle' | 'analyzing' | 'done' | 'error' | 'cancelled';

export interface UseAnalyzeReturn {
  status: AnalyzeStatus;
  result: AnalyzeResponse | null;
  error: string | null;
  analyze: (image: File, segmentId?: string) => void;
  cancel: () => void;
  reset: () => void;
}

export function useAnalyze(): UseAnalyzeReturn {
  const [status, setStatus] = useState<AnalyzeStatus>('idle');
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const analyze = useCallback((image: File, segmentId?: string) => {
    if (abortRef.current) abortRef.current.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    setStatus('analyzing');
    setResult(null);
    setError(null);

    const run = IS_MOCK
      ? () => mockAnalyzeImage(image)
      : () => analyzeImage(image, segmentId, ctrl.signal);

    run()
      .then(data => {
        if (ctrl.signal.aborted) return;
        setResult(data);
        setStatus('done');
      })
      .catch(err => {
        if (err?.name === 'AbortError' || ctrl.signal.aborted) {
          setStatus('cancelled');
          return;
        }
        const msg =
          err instanceof Error ? err.message : 'Unexpected error. Please try again.';
        setError(msg);
        setStatus('error');
      });
  }, []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setStatus('cancelled');
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setStatus('idle');
    setResult(null);
    setError(null);
  }, []);

  return { status, result, error, analyze, cancel, reset };
}
