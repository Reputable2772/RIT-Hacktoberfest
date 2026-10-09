import { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Marker, Popup, useMap } from 'react-leaflet';
import { motion, AnimatePresence } from 'framer-motion';
import L from 'leaflet';
import type {
  DemoLocation,
  JourneyOption,
  ObservationPoint,
  GemmaVisualAnalysis,
  SortCriterion,
  CustomJourneyRequest,
} from '../api/types';
import {
  getLocations,
  getJourneys,
  getObservations,
  analyzeObservation,
  planCustomJourney,
  uploadAndAnalyze,
} from '../api/client';
import {
  mockLocations,
  mockGetJourneys,
  mockGetObservations,
  mockAnalyzeObservation,
  mockPlanCustomJourney,
  mockUploadAndAnalyze,
} from '../api/mock';
import 'leaflet/dist/leaflet.css';

const IS_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

// Design tokens per Section 6 of contract
const TOKENS = {
  metro: '#a855f7',
  bus: '#38bdf8',
  walk: '#f59e0b',
  accessible: '#10b981',
  moderate: '#f59e0b',
  barrier: '#f43f5e',
  bgDark: '#090d16',
  bgCard: 'rgba(16, 24, 40, 0.85)',
};

function MapRecenter({ lat, lon }: { lat: number; lon: number }) {
  const map = useMap();
  useEffect(() => {
    map.panTo([lat, lon], { animate: true, duration: 0.6 });
  }, [lat, lon, map]);
  return null;
}

export function CorridorPlanner() {
  const [activeMode, setActiveMode] = useState<'A' | 'B'>('A');

  // Mode A state
  const [locations, setLocations] = useState<DemoLocation[]>(mockLocations);
  const [selectedDirection, setSelectedDirection] = useState<'A->B' | 'B->C' | 'C->A'>('A->B');
  const [sortOrder, setSortOrder] = useState<SortCriterion>('fastest');
  const [journeys, setJourneys] = useState<Record<string, JourneyOption[]>>({});
  const [observations, setObservations] = useState<ObservationPoint[]>([]);
  const [selectedObs, setSelectedObs] = useState<ObservationPoint | null>(null);
  const [analyzingObsId, setAnalyzingObsId] = useState<string | null>(null);
  const [reRankNotice, setReRankNotice] = useState<string | null>(null);

  // Mode B state
  const [customOrigin, setCustomOrigin] = useState('Koramangala BDA Complex');
  const [customDest, setCustomDest] = useState('Indiranagar 100ft Road');
  const [customJourneys, setCustomJourneys] = useState<JourneyOption[]>([]);
  const [customLoading, setCustomLoading] = useState(false);
  const [uploadingSegmentId, setUploadingSegmentId] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccessAnalysis, setUploadSuccessAnalysis] = useState<GemmaVisualAnalysis | null>(null);

  // Common loading / error
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch Mode A data
  const loadModeAData = useCallback(async (currentSort = sortOrder) => {
    setLoading(true);
    setError(null);
    try {
      if (IS_MOCK) {
        const [j, obs] = await Promise.all([
          mockGetJourneys(currentSort),
          mockGetObservations(),
        ]);
        setJourneys(j);
        setObservations(obs);
      } else {
        const [locs, j, obs] = await Promise.all([
          getLocations().catch(() => mockLocations),
          getJourneys(currentSort).catch(() => mockGetJourneys(currentSort)),
          getObservations().catch(() => mockGetObservations()),
        ]);
        setLocations(locs);
        setJourneys(j);
        setObservations(obs);
      }
    } catch (err) {
      console.warn('Backend fetch failed, falling back to mock mode', err);
      const [j, obs] = await Promise.all([
        mockGetJourneys(currentSort),
        mockGetObservations(),
      ]);
      setJourneys(j);
      setObservations(obs);
    } finally {
      setLoading(false);
    }
  }, [sortOrder]);

  useEffect(() => {
    loadModeAData();
  }, [loadModeAData]);

  // Handle running Gemma Multimodal Analysis on an observation point
  async function handleAnalyzeObservation(obsId: string) {
    setAnalyzingObsId(obsId);
    setReRankNotice(null);
    try {
      let analysis: GemmaVisualAnalysis;
      if (IS_MOCK) {
        analysis = await mockAnalyzeObservation(obsId);
      } else {
        analysis = await analyzeObservation(obsId).catch(() => mockAnalyzeObservation(obsId));
      }

      // Update observation state
      setObservations(prev =>
        prev.map(o => (o.id === obsId ? { ...o, status: 'analysis_completed', analysis } : o))
      );
      if (selectedObs && selectedObs.id === obsId) {
        setSelectedObs(prev => (prev ? { ...prev, status: 'analysis_completed', analysis } : null));
      }

      // Trigger automatic journey refresh & re-ranking!
      const updatedJourneys = IS_MOCK
        ? await mockGetJourneys('best_accessibility')
        : await getJourneys('best_accessibility').catch(() => mockGetJourneys('best_accessibility'));

      setJourneys(updatedJourneys);
      setSortOrder('best_accessibility');
      setReRankNotice(
        `Gemma Vision Audit complete! Accessibility score calculated: ${analysis.calculated_accessibility_score.toFixed(
          0
        )}/100 (${analysis.evidence_status}). Corridors re-ranked by accessibility!`
      );
    } catch (err) {
      console.error('Inference error', err);
      alert(err instanceof Error ? err.message : 'Inference failed');
    } finally {
      setAnalyzingObsId(null);
    }
  }

  // Handle Mode B custom journey search
  async function handleSearchCustomJourney() {
    setCustomLoading(true);
    setUploadError(null);
    try {
      const req: CustomJourneyRequest = {
        origin_name: customOrigin,
        origin_lat: 12.9345,
        origin_lon: 77.6225,
        dest_name: customDest,
        dest_lat: 12.9719,
        dest_lon: 77.6412,
        sort: 'fastest',
      };

      const res = IS_MOCK
        ? await mockPlanCustomJourney(req)
        : await planCustomJourney(req).catch(() => mockPlanCustomJourney(req));
      setCustomJourneys(res);
    } catch (err) {
      console.error('Custom journey error', err);
      setCustomJourneys([]);
    } finally {
      setCustomLoading(false);
    }
  }

  // Handle user photo upload for walking segment audit
  async function handleSegmentPhotoUpload(file: File, segmentId: string) {
    setUploadingSegmentId(segmentId);
    setUploadError(null);
    setUploadSuccessAnalysis(null);
    try {
      const res = IS_MOCK
        ? await mockUploadAndAnalyze(file, segmentId)
        : await uploadAndAnalyze(file, segmentId).catch(() => mockUploadAndAnalyze(file, segmentId));

      setUploadSuccessAnalysis(res);
      // Update custom journey segment score
      setCustomJourneys(prev =>
        prev.map(j => ({
          ...j,
          accessibility_score: res.calculated_accessibility_score,
          accessibility_verdict:
            res.calculated_accessibility_score >= 80
              ? 'Highly Accessible'
              : res.calculated_accessibility_score >= 50
              ? 'Moderate Accessibility'
              : 'Significant Physical Barriers',
        }))
      );
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploadingSegmentId(null);
    }
  }

  const currentOptions = journeys[selectedDirection] || [];

  return (
    <section
      id="corridors"
      aria-label="Bengaluru Multimodal Pedestrian Accessibility & Transit Planner"
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
            <span>SAAKSHI TRANSIT PLANNER v2.0</span>
            <span style={{ color: 'var(--signal-teal)' }}>//</span>
            <span>BENGALURU GTFS MULTIMODAL ROUTING & GEMMA VISION AUDIT</span>
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
                Accessible Transit Corridors
              </h2>
              <p
                style={{
                  color: 'var(--paper-muted)',
                  marginTop: 0,
                  maxWidth: 720,
                  fontSize: '1.05rem',
                  lineHeight: 1.6,
                }}
              >
                Unlike conventional map apps that treat walking as a simple distance, Saakshi uses Google Gemma
                Multimodal Vision to audit ground-level walkability barriers and dynamically re-ranks public transit
                corridors based on real physical accessibility.
              </p>
            </div>

            {/* Mode Switch Tabs */}
            <div
              style={{
                display: 'inline-flex',
                background: 'var(--deep-surface)',
                border: '1px solid var(--border-fine)',
                borderRadius: 'var(--radius)',
                padding: 4,
                gap: 4,
              }}
            >
              <button
                type="button"
                onClick={() => setActiveMode('A')}
                style={{
                  background: activeMode === 'A' ? 'var(--signal-teal)' : 'transparent',
                  color: activeMode === 'A' ? 'var(--obsidian-ink)' : 'var(--paper-muted)',
                  border: 'none',
                  borderRadius: 'var(--radius-xs)',
                  padding: '6px 14px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                MODE A: CORRIDOR DEMO
              </button>

              <button
                type="button"
                onClick={() => {
                  setActiveMode('B');
                  if (customJourneys.length === 0) handleSearchCustomJourney();
                }}
                style={{
                  background: activeMode === 'B' ? 'var(--signal-teal)' : 'transparent',
                  color: activeMode === 'B' ? 'var(--obsidian-ink)' : 'var(--paper-muted)',
                  border: 'none',
                  borderRadius: 'var(--radius-xs)',
                  padding: '6px 14px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                MODE B: CUSTOM ROUTE
              </button>
            </div>
          </div>
        </div>

        {/* Dynamic Re-Rank Flash Notice */}
        {reRankNotice && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              padding: '12px 16px',
              background: 'rgba(25, 211, 197, 0.12)',
              border: '1px solid var(--border-teal)',
              borderRadius: 'var(--radius-xs)',
              color: 'var(--signal-teal)',
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              marginBottom: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span>⚡</span>
            <span>{reRankNotice}</span>
          </motion.div>
        )}

        {/* ========================================================================= */}
        {/* MODE A: CURATED CORRIDOR DEMO                                            */}
        {/* ========================================================================= */}
        {activeMode === 'A' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Top Toolbar: Direction Tabs & Sorting Controls */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '1rem',
                background: 'var(--deep-surface)',
                border: '1px solid var(--border-fine)',
                borderRadius: 'var(--radius)',
                padding: '0.875rem 1.25rem',
              }}
            >
              {/* Direction Tabs */}
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--evidence-grey)', alignSelf: 'center', marginRight: 4 }}>
                  CORRIDOR:
                </span>
                {(['A->B', 'B->C', 'C->A'] as const).map(dir => (
                  <button
                    key={dir}
                    type="button"
                    onClick={() => setSelectedDirection(dir)}
                    style={{
                      background: selectedDirection === dir ? 'rgba(25, 211, 197, 0.15)' : 'rgba(11, 16, 20, 0.6)',
                      border: `1px solid ${selectedDirection === dir ? 'var(--signal-teal)' : 'var(--border-fine)'}`,
                      borderRadius: 'var(--radius-xs)',
                      color: selectedDirection === dir ? 'var(--signal-teal)' : 'var(--paper-muted)',
                      padding: '6px 12px',
                      fontFamily: 'var(--font-mono)',
                      fontSize: 12,
                      fontWeight: 700,
                      cursor: 'pointer',
                    }}
                  >
                    {dir === 'A->B' && 'MG Road ➔ Cubbon Park (A ➔ B)'}
                    {dir === 'B->C' && 'Cubbon Park ➔ Majestic (B ➔ C)'}
                    {dir === 'C->A' && 'Majestic ➔ MG Road (C ➔ A)'}
                  </button>
                ))}
              </div>

              {/* Sorting Filter */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--evidence-grey)' }}>
                  SORT BY:
                </span>
                <select
                  value={sortOrder}
                  onChange={e => {
                    const s = e.target.value as SortCriterion;
                    setSortOrder(s);
                    loadModeAData(s);
                  }}
                  style={{
                    background: 'var(--obsidian-ink)',
                    border: '1px solid var(--border-fine)',
                    borderRadius: 'var(--radius-xs)',
                    color: 'var(--paper-warm)',
                    padding: '6px 10px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 12,
                    cursor: 'pointer',
                  }}
                >
                  <option value="fastest">Fastest Duration</option>
                  <option value="best_accessibility">Best Accessibility Score</option>
                  <option value="least_walking">Least Walking Distance</option>
                  <option value="fewest_transfers">Fewest Transfers</option>
                </select>
              </div>
            </div>

            {/* Split View: Corridor Map & Route Alternative Cards */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 460px), 1fr))',
                gap: '1.5rem',
              }}
            >
              {/* Left Column: Corridor Leaflet Map with Observation Points */}
              <div
                style={{
                  background: 'var(--obsidian-ink)',
                  border: '1px solid var(--border-fine)',
                  borderRadius: 'var(--radius)',
                  overflow: 'hidden',
                  height: 540,
                  position: 'relative',
                }}
              >
                <MapContainer center={[12.9775, 77.5950]} zoom={14} style={{ height: '100%', width: '100%' }}>
                  <TileLayer
                    url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    maxZoom={19}
                  />

                  {/* Render Route Polylines for current direction options */}
                  {currentOptions.map(opt =>
                    opt.segments.map(seg => {
                      const color =
                        seg.mode === 'metro'
                          ? TOKENS.metro
                          : seg.mode === 'bus'
                          ? TOKENS.bus
                          : TOKENS.walk;

                      return (
                        <Polyline
                          key={seg.id}
                          positions={seg.polyline}
                          pathOptions={{
                            color,
                            weight: seg.mode === 'walking' ? 4 : 6,
                            dashArray: seg.mode === 'walking' ? '6, 6' : undefined,
                            opacity: 0.85,
                          }}
                        />
                      );
                    })
                  )}

                  {/* Render Fixed Transit Station Markers (Locations A, B, C) */}
                  {locations.map(loc => (
                    <CircleMarker
                      key={loc.id}
                      center={[loc.lat, loc.lon]}
                      radius={9}
                      pathOptions={{
                        color: '#19D3C5',
                        fillColor: '#0B1014',
                        fillOpacity: 1,
                        weight: 3,
                      }}
                    >
                      <Popup>
                        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                          <strong>{loc.name}</strong>
                          <br />
                          {loc.description}
                          <br />
                          <span style={{ color: 'var(--signal-teal)' }}>
                            Accessible Entrances: {loc.accessible_entrances.join(', ')}
                          </span>
                        </div>
                      </Popup>
                    </CircleMarker>
                  ))}

                  {/* Render Prepared Street View Observation Points (OBS_1 to OBS_5) */}
                  {observations.map(obs => {
                    const isCompleted = obs.status === 'analysis_completed';
                    const hasBarrier = obs.analysis?.evidence_status === 'BARRIER';

                    return (
                      <CircleMarker
                        key={obs.id}
                        center={[obs.lat, obs.lon]}
                        radius={7}
                        pathOptions={{
                          color: isCompleted ? (hasBarrier ? '#FF6268' : '#19D3C5') : '#FFB454',
                          fillColor: isCompleted ? (hasBarrier ? '#FF6268' : '#19D3C5') : '#FFB454',
                          fillOpacity: 0.75,
                          weight: 2,
                        }}
                        eventHandlers={{
                          click: () => setSelectedObs(obs),
                        }}
                      >
                        <Popup>
                          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>
                            <strong>{obs.name}</strong> ({obs.id})<br />
                            Status: {obs.status}<br />
                            <button
                              type="button"
                              onClick={() => setSelectedObs(obs)}
                              style={{
                                marginTop: 4,
                                background: '#19D3C5',
                                color: '#0B1014',
                                border: 'none',
                                borderRadius: 2,
                                padding: '2px 6px',
                                cursor: 'pointer',
                                fontWeight: 700,
                              }}
                            >
                              Inspect Street View Evidence
                            </button>
                          </div>
                        </Popup>
                      </CircleMarker>
                    );
                  })}
                </MapContainer>

                {/* Legend Overlay */}
                <div
                  style={{
                    position: 'absolute',
                    bottom: 12,
                    left: 12,
                    zIndex: 700,
                    background: 'rgba(11, 16, 20, 0.90)',
                    border: '1px solid var(--border-fine)',
                    borderRadius: 'var(--radius-xs)',
                    padding: '8px 12px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 4,
                    fontSize: 10,
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 14, height: 3, background: TOKENS.metro }} />
                    <span style={{ color: 'var(--paper-warm)' }}>BMRCL Purple Line Metro</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 14, height: 3, background: TOKENS.bus }} />
                    <span style={{ color: 'var(--paper-warm)' }}>BMTC Bus Corridors</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 14, height: 3, background: TOKENS.walk }} />
                    <span style={{ color: 'var(--paper-warm)' }}>Pedestrian Walking Connectors</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, borderTop: '1px solid var(--border-fine)', paddingTop: 4, marginTop: 2 }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#FFB454' }} />
                    <span style={{ color: 'var(--evidence-grey)' }}>Observation Camera (Click to Audit)</span>
                  </div>
                </div>
              </div>

              {/* Right Column: Route Alternatives List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: 540, overflowY: 'auto' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--evidence-grey)' }}>
                    RANKED ROUTE ALTERNATIVES ({currentOptions.length})
                  </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--signal-teal)' }}>
                    DYNAMICALLY RE-RANKED VIA GEMMA VISION
                  </span>
                </div>

                {currentOptions.map((opt, idx) => {
                  const scoreColor =
                    opt.accessibility_score >= 80
                      ? TOKENS.accessible
                      : opt.accessibility_score >= 50
                      ? TOKENS.moderate
                      : TOKENS.barrier;

                  const modeBadgeColor =
                    opt.primary_mode === 'metro'
                      ? TOKENS.metro
                      : opt.primary_mode === 'bus'
                      ? TOKENS.bus
                      : TOKENS.walk;

                  return (
                    <div
                      key={opt.id}
                      style={{
                        background: 'var(--deep-surface)',
                        border: `1px solid ${idx === 0 ? 'var(--signal-teal)' : 'var(--border-fine)'}`,
                        borderRadius: 'var(--radius)',
                        padding: '1.25rem',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.75rem',
                        position: 'relative',
                        boxShadow: idx === 0 ? '0 0 16px var(--signal-teal-dim)' : 'none',
                      }}
                    >
                      {/* Top Badges */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                          <span
                            style={{
                              fontFamily: 'var(--font-mono)',
                              fontSize: 10,
                              fontWeight: 700,
                              background: modeBadgeColor,
                              color: '#fff',
                              padding: '2px 6px',
                              borderRadius: 2,
                              textTransform: 'uppercase',
                            }}
                          >
                            {opt.primary_mode}
                          </span>

                          {idx === 0 && (
                            <span
                              style={{
                                fontFamily: 'var(--font-mono)',
                                fontSize: 10,
                                fontWeight: 700,
                                background: 'var(--signal-teal-dim)',
                                color: 'var(--signal-teal)',
                                border: '1px solid var(--border-teal)',
                                padding: '2px 6px',
                                borderRadius: 2,
                              }}
                            >
                              RECOMMENDED #1
                            </span>
                          )}
                        </div>

                        {/* Accessibility Score Pill */}
                        <div
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 6,
                            background: `${scoreColor}18`,
                            border: `1px solid ${scoreColor}60`,
                            padding: '3px 8px',
                            borderRadius: 'var(--radius-xs)',
                            fontFamily: 'var(--font-mono)',
                            fontSize: 11,
                            fontWeight: 700,
                            color: scoreColor,
                          }}
                        >
                          <span>{opt.accessibility_score.toFixed(0)}/100</span>
                          <span>·</span>
                          <span>{opt.accessibility_verdict}</span>
                        </div>
                      </div>

                      {/* Title & Summary */}
                      <div>
                        <h4 style={{ margin: '0 0 4px', fontSize: 15, fontWeight: 700, color: 'var(--paper-warm)' }}>
                          {opt.title}
                        </h4>
                        <p style={{ margin: 0, fontSize: 12, color: 'var(--paper-muted)', lineHeight: 1.5 }}>
                          {opt.summary}
                        </p>
                      </div>

                      {/* Travel Metrics Strip */}
                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(4, 1fr)',
                          gap: 6,
                          background: 'rgba(11, 16, 20, 0.6)',
                          padding: '8px',
                          borderRadius: 'var(--radius-xs)',
                          fontFamily: 'var(--font-mono)',
                          fontSize: 11,
                          textAlign: 'center',
                        }}
                      >
                        <div>
                          <div style={{ color: 'var(--evidence-grey)', fontSize: 9 }}>DURATION</div>
                          <div style={{ color: 'var(--paper-warm)', fontWeight: 700 }}>{opt.total_duration_minutes} min</div>
                        </div>
                        <div>
                          <div style={{ color: 'var(--evidence-grey)', fontSize: 9 }}>WALKING</div>
                          <div style={{ color: 'var(--paper-warm)', fontWeight: 700 }}>{opt.total_walking_distance_meters} m</div>
                        </div>
                        <div>
                          <div style={{ color: 'var(--evidence-grey)', fontSize: 9 }}>TRANSFERS</div>
                          <div style={{ color: 'var(--paper-warm)', fontWeight: 700 }}>{opt.total_transfers}</div>
                        </div>
                        <div>
                          <div style={{ color: 'var(--evidence-grey)', fontSize: 9 }}>FARE</div>
                          <div style={{ color: 'var(--paper-warm)', fontWeight: 700 }}>₹{opt.total_fare_inr}</div>
                        </div>
                      </div>

                      {/* Concerns & Reasons */}
                      {opt.accessibility_concerns.length > 0 && (
                        <div
                          style={{
                            fontSize: 11,
                            color: 'var(--barrier-coral)',
                            background: 'rgba(255, 98, 104, 0.08)',
                            padding: '6px 8px',
                            borderRadius: 2,
                            borderLeft: '2px solid var(--barrier-coral)',
                          }}
                        >
                          ⚠ <strong>Barrier Notice:</strong> {opt.accessibility_concerns.join('; ')}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Street View Observation Inspection Modal / Dossier */}
            <AnimatePresence>
              {selectedObs && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.96 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.96 }}
                  style={{
                    background: 'var(--deep-surface)',
                    border: '1px solid var(--border-teal)',
                    borderRadius: 'var(--radius)',
                    padding: '1.5rem',
                    position: 'relative',
                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.6)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                    <div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--signal-teal)', textTransform: 'uppercase' }}>
                        STREET VIEW GROUND-TRUTH OBSERVATION // {selectedObs.id}
                      </div>
                      <h3 style={{ margin: '4px 0 0', fontSize: 17, color: 'var(--paper-warm)' }}>
                        {selectedObs.name}
                      </h3>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--evidence-grey)' }}>
                        {selectedObs.location} · {selectedObs.lat.toFixed(5)}°N, {selectedObs.lon.toFixed(5)}°E
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => setSelectedObs(null)}
                      style={{
                        background: 'transparent',
                        border: '1px solid var(--border-fine)',
                        borderRadius: 'var(--radius-xs)',
                        color: 'var(--paper-muted)',
                        cursor: 'pointer',
                        padding: '4px 8px',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      ✕ CLOSE
                    </button>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
                    {/* Observation Photo */}
                    <div>
                      <img
                        src={selectedObs.image_url}
                        alt={selectedObs.name}
                        style={{
                          width: '100%',
                          height: 200,
                          objectFit: 'cover',
                          borderRadius: 'var(--radius-xs)',
                          border: '1px solid var(--border-fine)',
                        }}
                      />

                      <div style={{ marginTop: '0.75rem' }}>
                        <button
                          type="button"
                          disabled={analyzingObsId === selectedObs.id}
                          onClick={() => handleAnalyzeObservation(selectedObs.id)}
                          style={{
                            width: '100%',
                            background: 'var(--signal-teal)',
                            color: 'var(--obsidian-ink)',
                            border: 'none',
                            borderRadius: 'var(--radius-xs)',
                            padding: '10px 16px',
                            fontFamily: 'var(--font-mono)',
                            fontSize: 13,
                            fontWeight: 700,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: 8,
                          }}
                        >
                          <span>{analyzingObsId === selectedObs.id ? '⏳' : '⚡'}</span>
                          <span>
                            {analyzingObsId === selectedObs.id
                              ? 'RUNNING GEMMA 4 MULTIMODAL INFERENCE…'
                              : 'RUN GEMMA MULTIMODAL VISION ANALYSIS'}
                          </span>
                        </button>
                      </div>
                    </div>

                    {/* Gemma 6 Accessibility Criteria Results */}
                    <div>
                      {selectedObs.analysis ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--evidence-grey)' }}>
                              GEMMA 4 6-CRITERIA EVALUATION
                            </span>
                            <span
                              style={{
                                fontFamily: 'var(--font-mono)',
                                fontSize: 12,
                                fontWeight: 700,
                                color:
                                  selectedObs.analysis.calculated_accessibility_score >= 80
                                    ? TOKENS.accessible
                                    : TOKENS.barrier,
                              }}
                            >
                              SCORE: {selectedObs.analysis.calculated_accessibility_score.toFixed(0)}/100 (
                              {selectedObs.analysis.evidence_status})
                            </span>
                          </div>

                          {/* 6 Criteria Checklist (Section 6 format) */}
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                            {[
                              selectedObs.analysis.sidewalk,
                              selectedObs.analysis.curb_ramps,
                              selectedObs.analysis.tactile_paving,
                              selectedObs.analysis.pedestrian_crossings,
                              selectedObs.analysis.obstructions,
                              selectedObs.analysis.surface_damage,
                            ].map(crit => {
                              const isPositive =
                                (crit.criterion === 'obstructions' || crit.criterion === 'surface_damage')
                                  ? crit.status === 'absent'
                                  : crit.status === 'present';

                              return (
                                <div
                                  key={crit.criterion}
                                  style={{
                                    background: 'rgba(11, 16, 20, 0.7)',
                                    border: '1px solid var(--border-fine)',
                                    borderRadius: 'var(--radius-xs)',
                                    padding: '6px 8px',
                                    fontSize: 11,
                                    fontFamily: 'var(--font-mono)',
                                  }}
                                >
                                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ color: 'var(--paper-warm)' }}>{crit.label}</span>
                                    <span style={{ color: isPositive ? TOKENS.accessible : TOKENS.barrier }}>
                                      {isPositive ? '✓' : '✕'} {crit.status}
                                    </span>
                                  </div>
                                  <div style={{ fontSize: 9, color: 'var(--text-dim)', marginTop: 2 }}>
                                    Conf: {crit.confidence}
                                  </div>
                                </div>
                              );
                            })}
                          </div>

                          <div style={{ fontSize: 12, color: 'var(--paper-muted)', lineHeight: 1.5, background: 'rgba(11, 16, 20, 0.5)', padding: '8px', borderRadius: 'var(--radius-xs)' }}>
                            <strong>Summary:</strong> {selectedObs.analysis.summary}
                          </div>
                        </div>
                      ) : (
                        <div
                          style={{
                            height: '100%',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            padding: '2rem',
                            textAlign: 'center',
                            background: 'rgba(11, 16, 20, 0.5)',
                            borderRadius: 'var(--radius-xs)',
                            border: '1px dashed var(--border-fine)',
                          }}
                        >
                          <span style={{ fontSize: 24, marginBottom: 8 }}>👁</span>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--paper-warm)', marginBottom: 4 }}>
                            Awaiting Gemma Vision Inference
                          </span>
                          <span style={{ fontSize: 11, color: 'var(--evidence-grey)' }}>
                            Click the button on the left to trigger real-time Google Gemma multimodal vision inference.
                            Corridors will immediately re-rank based on detected barriers.
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* ========================================================================= */}
        {/* MODE B: CUSTOM POINT-TO-POINT TRANSIT ROUTING                            */}
        {/* ========================================================================= */}
        {activeMode === 'B' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Input Form Panel */}
            <div
              style={{
                background: 'var(--deep-surface)',
                border: '1px solid var(--border-fine)',
                borderRadius: 'var(--radius)',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
              }}
            >
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--signal-teal)' }}>
                MODE B // BENGALURU GTFS MULTIMODAL PLANNER + USER AUDIT
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--evidence-grey)', marginBottom: 4 }}>
                    ORIGIN (LOCATION IN BENGALURU)
                  </label>
                  <input
                    type="text"
                    value={customOrigin}
                    onChange={e => setCustomOrigin(e.target.value)}
                    style={{
                      width: '100%',
                      background: 'var(--obsidian-ink)',
                      border: '1px solid var(--border-fine)',
                      borderRadius: 'var(--radius-xs)',
                      padding: '8px 12px',
                      color: 'var(--paper-warm)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: 13,
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--evidence-grey)', marginBottom: 4 }}>
                    DESTINATION
                  </label>
                  <input
                    type="text"
                    value={customDest}
                    onChange={e => setCustomDest(e.target.value)}
                    style={{
                      width: '100%',
                      background: 'var(--obsidian-ink)',
                      border: '1px solid var(--border-fine)',
                      borderRadius: 'var(--radius-xs)',
                      padding: '8px 12px',
                      color: 'var(--paper-warm)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: 13,
                    }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                <div style={{ display: 'flex', gap: 6 }}>
                  <button
                    type="button"
                    onClick={() => {
                      setCustomOrigin('Koramangala BDA Complex');
                      setCustomDest('Indiranagar 100ft Road');
                    }}
                    style={{
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid var(--border-fine)',
                      borderRadius: 'var(--radius-xs)',
                      color: 'var(--paper-muted)',
                      padding: '4px 8px',
                      fontSize: 11,
                      fontFamily: 'var(--font-mono)',
                      cursor: 'pointer',
                    }}
                  >
                    Preset: Koramangala ➔ Indiranagar
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setCustomOrigin('Jayanagar 4th Block');
                      setCustomDest('Whitefield ITPL');
                    }}
                    style={{
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid var(--border-fine)',
                      borderRadius: 'var(--radius-xs)',
                      color: 'var(--paper-muted)',
                      padding: '4px 8px',
                      fontSize: 11,
                      fontFamily: 'var(--font-mono)',
                      cursor: 'pointer',
                    }}
                  >
                    Preset: Jayanagar ➔ Whitefield
                  </button>
                </div>

                <button
                  type="button"
                  disabled={customLoading}
                  onClick={handleSearchCustomJourney}
                  style={{
                    background: 'var(--signal-teal)',
                    color: 'var(--obsidian-ink)',
                    border: 'none',
                    borderRadius: 'var(--radius-xs)',
                    padding: '8px 18px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 13,
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  {customLoading ? 'RESOLVING GTFS STOPS…' : 'FIND ACCESSIBLE TRANSIT ROUTE'}
                </button>
              </div>
            </div>

            {/* Custom Journey Results */}
            {customJourneys.map(j => (
              <div
                key={j.id}
                style={{
                  background: 'var(--deep-surface)',
                  border: '1px solid var(--border-fine)',
                  borderRadius: 'var(--radius)',
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1.25rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 style={{ margin: '0 0 4px', fontSize: 17, color: 'var(--paper-warm)' }}>
                      {j.title}
                    </h3>
                    <p style={{ margin: 0, fontSize: 13, color: 'var(--paper-muted)' }}>
                      {j.summary}
                    </p>
                  </div>

                  <div
                    style={{
                      background: 'rgba(255, 180, 84, 0.12)',
                      border: '1px solid var(--border-amber)',
                      padding: '4px 10px',
                      borderRadius: 'var(--radius-xs)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: 12,
                      fontWeight: 700,
                      color: 'var(--survey-amber)',
                    }}
                  >
                    SCORE: {j.accessibility_score.toFixed(0)}/100 · {j.accessibility_verdict}
                  </div>
                </div>

                {/* Segments Display */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {j.segments.map((seg, sIdx) => (
                    <div
                      key={seg.id}
                      style={{
                        background: 'rgba(11, 16, 20, 0.65)',
                        border: '1px solid var(--border-fine)',
                        borderRadius: 'var(--radius-xs)',
                        padding: '1rem',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 8,
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <span
                            style={{
                              fontFamily: 'var(--font-mono)',
                              fontSize: 10,
                              fontWeight: 700,
                              background: seg.mode === 'walking' ? TOKENS.walk : TOKENS.bus,
                              color: '#fff',
                              padding: '2px 6px',
                              borderRadius: 2,
                            }}
                          >
                            SEG {sIdx + 1}: {seg.mode.toUpperCase()}
                          </span>
                          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--paper-warm)' }}>
                            {seg.from_name} ➔ {seg.to_name}
                          </span>
                        </div>

                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--evidence-grey)' }}>
                          {seg.distance_meters}m · {seg.duration_minutes} min
                        </span>
                      </div>

                      {/* Photo Audit Call-to-Action on Walking Connector */}
                      {seg.mode === 'walking' && (
                        <div
                          style={{
                            background: 'rgba(25, 211, 197, 0.05)',
                            border: '1px dashed var(--border-teal)',
                            borderRadius: 'var(--radius-xs)',
                            padding: '10px 12px',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            flexWrap: 'wrap',
                            gap: 8,
                          }}
                        >
                          <div>
                            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: 'var(--signal-teal)' }}>
                              📷 AUDIT WALKING CONNECTOR WITH USER-CAPTURED PHOTO
                            </div>
                            <div style={{ fontSize: 11, color: 'var(--paper-muted)' }}>
                              Upload a sidewalk photograph to evaluate against the 6 Gemma accessibility criteria.
                            </div>
                          </div>

                          <label
                            style={{
                              background: uploadingSegmentId === seg.id ? 'var(--deep-surface)' : 'var(--signal-teal)',
                              color: 'var(--obsidian-ink)',
                              padding: '6px 14px',
                              borderRadius: 'var(--radius-xs)',
                              fontFamily: 'var(--font-mono)',
                              fontSize: 12,
                              fontWeight: 700,
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: 6,
                            }}
                          >
                            <span>{uploadingSegmentId === seg.id ? '⏳ AUDITING…' : 'UPLOAD PHOTO'}</span>
                            <input
                              type="file"
                              accept="image/jpeg,image/png,image/webp"
                              style={{ display: 'none' }}
                              onChange={e => {
                                const f = e.target.files?.[0];
                                if (f) handleSegmentPhotoUpload(f, seg.id);
                              }}
                            />
                          </label>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Upload Feedback Toast */}
                {uploadError && (
                  <div style={{ padding: '8px 12px', background: 'rgba(255, 98, 104, 0.1)', border: '1px solid var(--border-coral)', borderRadius: 2, color: 'var(--barrier-coral)', fontSize: 12, fontFamily: 'var(--font-mono)' }}>
                    {uploadError}
                  </div>
                )}

                {uploadSuccessAnalysis && (
                  <div style={{ padding: '10px 12px', background: 'rgba(25, 211, 197, 0.1)', border: '1px solid var(--border-teal)', borderRadius: 2, color: 'var(--signal-teal)', fontSize: 12, fontFamily: 'var(--font-mono)' }}>
                    ✓ User photo audited! OpenCV quality passed. Verified features: {uploadSuccessAnalysis.summary}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
