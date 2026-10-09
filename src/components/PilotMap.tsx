import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, useMap } from 'react-leaflet';
import { motion, AnimatePresence } from 'framer-motion';
import L from 'leaflet';
import type { Segment } from '../api/types';
import { verdictMeta, formatDate } from '../utils/display';
import { useSegments } from '../hooks/useSegments';
import { SegmentChain } from './SegmentChain';
import { VerdictBadge } from './VerdictBadge';
import 'leaflet/dist/leaflet.css';

// Status colors strictly adhering to Urban Evidence Lab tokens
const STATUS_COLORS: Record<string, string> = {
  BARRIER: '#FF6268',        // Barrier coral
  CLEAR_OBSERVED: '#19D3C5', // Signal teal
  INCONCLUSIVE: '#FFB454',   // Survey amber
  UNVERIFIED: '#A6B0BB',     // Evidence grey
};

// Subtle smooth recenter without jarring fly-to or zoom leaps
function MapSoftPan({ lat, lon }: { lat: number; lon: number }) {
  const map = useMap();
  useEffect(() => {
    map.panTo([lat, lon], { animate: true, duration: 0.6 });
  }, [lat, lon, map]);
  return null;
}

interface CoordinatedDrawerProps {
  segment: Segment;
  onClose: () => void;
}

function CoordinatedDrawer({ segment, onClose }: CoordinatedDrawerProps) {
  const meta = verdictMeta(segment.status);
  const [photoZoom, setPhotoZoom] = useState(false);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <motion.aside
      initial={{ opacity: 0, x: 24 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 24 }}
      transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
      role="dialog"
      aria-modal="true"
      aria-label={`Spatial evidence dossier: ${segment.name}`}
      style={{
        position: 'absolute',
        top: 0,
        right: 0,
        bottom: 0,
        width: 'min(380px, 100%)',
        background: 'rgba(11, 16, 20, 0.95)',
        backdropFilter: 'blur(16px)',
        borderLeft: '1px solid var(--border-fine)',
        padding: '1.25rem',
        zIndex: 850,
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
        overflowY: 'auto',
        boxShadow: '-8px 0 24px rgba(0, 0, 0, 0.6)',
      }}
    >
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
        <div>
          <div
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 10,
              color: 'var(--evidence-grey)',
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              marginBottom: 4,
            }}
          >
            SPATIAL EVIDENCE RECORD // {segment.id}
          </div>
          <h3
            style={{
              margin: 0,
              fontFamily: 'var(--font-display)',
              fontWeight: 700,
              fontSize: 16,
              color: 'var(--paper-warm)',
              lineHeight: 1.3,
            }}
          >
            {segment.name}
          </h3>
        </div>

        <button
          type="button"
          onClick={onClose}
          aria-label="Close segment dossier"
          style={{
            background: 'rgba(255, 255, 255, 0.06)',
            border: '1px solid var(--border-fine)',
            borderRadius: 'var(--radius-xs)',
            color: 'var(--paper-muted)',
            cursor: 'pointer',
            padding: '4px 8px',
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            lineHeight: 1,
          }}
        >
          ✕ ESC
        </button>
      </div>

      {/* Verdict & Confidence Strip */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <VerdictBadge verdict={segment.status} />

        {segment.confidence !== null ? (
          <div
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              color: 'var(--signal-teal)',
              background: 'var(--signal-teal-dim)',
              border: '1px solid var(--border-teal)',
              padding: '2px 8px',
              borderRadius: 'var(--radius-xs)',
            }}
          >
            CONF: {(segment.confidence * 100).toFixed(0)}%
          </div>
        ) : (
          <div
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              color: 'var(--evidence-grey)',
              background: 'var(--evidence-grey-dim)',
              border: '1px solid var(--border-fine)',
              padding: '2px 8px',
              borderRadius: 'var(--radius-xs)',
            }}
          >
            UNRATED
          </div>
        )}
      </div>

      {/* Real Available Image Evidence */}
      <div>
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--evidence-grey)',
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
            marginBottom: 6,
          }}
        >
          PHOTOGRAPHIC EVIDENCE AT SECTOR
        </div>

        {segment.image_url ? (
          <div
            style={{
              position: 'relative',
              borderRadius: 'var(--radius-xs)',
              overflow: 'hidden',
              border: '1px solid var(--border-fine)',
              background: 'var(--deep-surface)',
              cursor: 'pointer',
            }}
            onClick={() => setPhotoZoom(!photoZoom)}
            title="Click to toggle zoomed optical view"
          >
            <img
              src={segment.image_url}
              alt={`Field survey photograph for ${segment.name}`}
              style={{
                width: '100%',
                height: photoZoom ? 220 : 130,
                objectFit: 'cover',
                display: 'block',
                transition: 'height 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
              }}
            />
            {/* Corner optical reticles */}
            <div
              style={{
                position: 'absolute',
                top: 4,
                left: 4,
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                color: 'var(--signal-teal)',
                lineHeight: 1,
              }}
            >
              ⌜
            </div>
            <div
              style={{
                position: 'absolute',
                bottom: 4,
                right: 4,
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                color: 'var(--signal-teal)',
                lineHeight: 1,
              }}
            >
              ⌟
            </div>
            <div
              style={{
                position: 'absolute',
                bottom: 4,
                left: 4,
                background: 'rgba(11, 16, 20, 0.85)',
                padding: '2px 6px',
                borderRadius: 'var(--radius-xs)',
                fontFamily: 'var(--font-mono)',
                fontSize: 9,
                color: 'var(--paper-muted)',
              }}
            >
              IN-SITU FIELD PHOTOGRAPH (CLICK TO {photoZoom ? 'SHRINK' : 'EXPAND'})
            </div>
          </div>
        ) : (
          <div
            style={{
              padding: '1.25rem',
              borderRadius: 'var(--radius-xs)',
              border: '1px dashed var(--border-fine)',
              background: 'rgba(25, 35, 42, 0.4)',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              gap: 4,
            }}
          >
            <span style={{ fontSize: 18, color: 'var(--evidence-grey)' }}>∅</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--paper-muted)' }}>
              NO PHOTOGRAPHIC EVIDENCE LOGGED
            </span>
            <span style={{ fontSize: 11, color: 'var(--evidence-grey)', lineHeight: 1.4 }}>
              Sector geometry imported from GIS grid. Field camera verification pending.
            </span>
          </div>
        )}
      </div>

      {/* Chronological Timestamps (Capture vs. Analysis) */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 6,
          background: 'var(--deep-surface)',
          padding: '0.75rem',
          borderRadius: 'var(--radius-xs)',
          border: '1px solid var(--border-fine)',
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--evidence-grey)' }}>CAPTURE TIMESTAMP:</span>
          <span style={{ color: segment.captured_at ? 'var(--paper-warm)' : 'var(--text-dim)' }}>
            {segment.captured_at ? formatDate(segment.captured_at) : 'NOT RECORDED'}
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--evidence-grey)' }}>GATE VERIFICATION:</span>
          <span style={{ color: segment.last_verified ? 'var(--paper-warm)' : 'var(--text-dim)' }}>
            {segment.last_verified ? formatDate(segment.last_verified) : 'PENDING AUDIT'}
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--evidence-grey)' }}>CENTROID:</span>
          <span style={{ color: 'var(--signal-teal)' }}>
            {segment.lat.toFixed(5)}°N, {segment.lon.toFixed(5)}°E
          </span>
        </div>
      </div>

      {/* Provenance Card */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 4,
          background: 'rgba(18, 26, 32, 0.5)',
          padding: '0.75rem',
          borderRadius: 'var(--radius-xs)',
          border: '1px solid var(--border-fine)',
        }}
      >
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--evidence-grey)',
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
          }}
        >
          DATA PROVENANCE & CHAIN OF CUSTODY
        </div>
        <div style={{ fontSize: 12, color: 'var(--paper-muted)', lineHeight: 1.4 }}>
          {segment.provenance ?? 'OpenStreetMap vector lineation // Verified by OpenForge Civic Pilot'}
        </div>
      </div>

      {/* Public Transit (BMTC / BMRCL) & Routing Honest Disclosure */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 6,
          background: 'rgba(255, 180, 84, 0.05)',
          border: '1px solid var(--border-amber)',
          padding: '0.75rem',
          borderRadius: 'var(--radius-xs)',
          fontSize: 11,
          lineHeight: 1.5,
        }}
      >
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            fontWeight: 700,
            color: 'var(--survey-amber)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            display: 'flex',
            alignItems: 'center',
            gap: 4,
          }}
        >
          <span>◈</span> TRANSIT (BMTC / BMRCL) & ROUTING PROVENANCE
        </div>

        <div style={{ color: 'var(--paper-muted)' }}>
          {segment.transit_note ??
            'BMTC & BMRCL transit live timetables are uncoupled from this pilot segment. No real-time schedule feed active.'}
        </div>

        <div style={{ color: 'var(--evidence-grey)', borderTop: '1px solid var(--border-fine)', paddingTop: 4 }}>
          <strong>Pedestrian routing:</strong> Point-to-point routing engine is intentionally excluded. Saakshi-Access
          verifies physical corridor obstructions only; route calculations are never provided.
        </div>
      </div>

      {/* Limitations Disclaimer */}
      <div
        role="note"
        style={{
          fontSize: 11,
          color: 'var(--evidence-grey)',
          padding: '0.75rem',
          background: 'rgba(11, 16, 20, 0.8)',
          borderRadius: 'var(--radius-xs)',
          border: '1px solid var(--border-fine)',
          lineHeight: 1.5,
          marginTop: 'auto',
        }}
      >
        <strong style={{ color: 'var(--survey-amber)' }}>Civic Decision Support Notice:</strong>{' '}
        This record reflects in-situ camera observations at the timestamp stated. It is not an accessibility certification
        or municipal guarantee. Do not encode absence of verified barriers as a permanent clearance guarantee.
      </div>
    </motion.aside>
  );
}

const LEGEND_ITEMS = [
  { status: 'BARRIER', label: 'Barrier observed', color: '#FF6268' },
  { status: 'CLEAR_OBSERVED', label: 'Clear observed (at capture)', color: '#19D3C5' },
  { status: 'INCONCLUSIVE', label: 'Inconclusive / Refused', color: '#FFB454' },
  { status: 'UNVERIFIED', label: 'Unverified segment (missing data)', color: '#A6B0BB' },
];

const DEFAULT_CENTER: L.LatLngExpression = [12.9740, 77.6070];

export function PilotMap() {
  const { segments, loading, error, refetch } = useSegments();
  const [selectedId, setSelectedId] = useState<string | null>('seg-1');
  const [tileError, setTileError] = useState(false);

  const selected = segments.find(s => s.id === selectedId) ?? null;

  return (
    <section
      id="map"
      aria-label="Pilot Corridor Spatial Evidence Explorer"
      style={{ padding: '5.5rem 0 4.5rem', position: 'relative', zIndex: 2 }}
    >
      <div className="section-container">
        {/* Section Header */}
        <div style={{ marginBottom: '2rem' }}>
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
            <span>CARTOGRAPHIC EVIDENCE EXPLORER</span>
            <span style={{ color: 'var(--signal-teal)' }}>//</span>
            <span>BLR-CENTRAL PILOT CORRIDOR</span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h2
                style={{
                  fontSize: 'clamp(2rem, 4vw, 2.75rem)',
                  fontWeight: 700,
                  margin: 0,
                  color: 'var(--paper-warm)',
                  lineHeight: 1.15,
                }}
              >
                Pilot Map
              </h2>
              <p
                style={{
                  color: 'var(--paper-muted)',
                  marginTop: '0.5rem',
                  maxWidth: 680,
                  fontSize: '1rem',
                  lineHeight: 1.6,
                }}
              >
                Audited footpath geometry across the Bengaluru Central pilot corridor. Select any segment on the map or
                corridor chain to inspect real photographic evidence, timestamps, provenance, and transit disclosures.
                <strong> Point-to-point routing and safety certifications are strictly excluded.</strong>
              </p>
            </div>

            {/* Datum Stamp */}
            <div
              style={{
                background: 'var(--deep-surface)',
                border: '1px solid var(--border-fine)',
                borderRadius: 'var(--radius-xs)',
                padding: '0.5rem 0.875rem',
                display: 'flex',
                flexDirection: 'column',
                gap: 2,
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
              }}
            >
              <span style={{ color: 'var(--evidence-grey)' }}>DATUM & CRS:</span>
              <span style={{ color: 'var(--signal-teal)', fontWeight: 600 }}>WGS84 EPSG:4326 // BLR</span>
              <span style={{ color: 'var(--text-dim)', fontSize: 10 }}>12.9740°N, 77.6070°E</span>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div
            role="status"
            className="lab-panel"
            style={{ color: 'var(--paper-muted)', padding: '3rem', textAlign: 'center', fontFamily: 'var(--font-mono)' }}
          >
            RETRIEVING VECTOR CORRIDOR GEOMETRY & AUDIT LOGS…
          </div>
        )}

        {/* Error State */}
        {error && (
          <div
            role="alert"
            style={{
              padding: '1.25rem',
              background: 'var(--barrier-coral-dim)',
              border: '1px solid var(--border-coral)',
              borderRadius: 'var(--radius-xs)',
              fontSize: 14,
              marginBottom: '1.5rem',
            }}
          >
            <div style={{ fontWeight: 700, color: 'var(--barrier-coral)', marginBottom: 4 }}>
              Failed to load pilot corridor segments
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
              RETRY CONNECTION
            </button>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && segments.length === 0 && (
          <div
            className="lab-panel"
            style={{ padding: '3rem', textAlign: 'center', color: 'var(--evidence-grey)', fontSize: 14 }}
          >
            No pilot segments registered in active database.
          </div>
        )}

        {/* Main Explorer Surface */}
        {!loading && segments.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Integrated Corridor Traversal Chain */}
            <div
              style={{
                background: 'var(--deep-surface)',
                border: '1px solid var(--border-fine)',
                borderRadius: 'var(--radius)',
                padding: '0.875rem 1rem',
              }}
            >
              <SegmentChain
                segments={segments}
                selectedId={selectedId}
                onSelect={id => setSelectedId(id)}
              />
            </div>

            {/* Cartographic Canvas */}
            <div
              style={{
                position: 'relative',
                borderRadius: 'var(--radius)',
                overflow: 'hidden',
                height: 520,
                border: '1px solid var(--border-fine)',
                background: 'var(--obsidian-ink)',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.45)',
              }}
            >
              {/* Corner Reticles */}
              <div
                style={{
                  position: 'absolute',
                  top: 8,
                  left: 8,
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                  color: 'var(--signal-teal)',
                  zIndex: 750,
                  pointerEvents: 'none',
                }}
              >
                ⌜
              </div>
              <div
                style={{
                  position: 'absolute',
                  top: 8,
                  right: 8,
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                  color: 'var(--signal-teal)',
                  zIndex: 750,
                  pointerEvents: 'none',
                }}
              >
                ⌝
              </div>
              <div
                style={{
                  position: 'absolute',
                  bottom: 8,
                  left: 8,
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                  color: 'var(--signal-teal)',
                  zIndex: 750,
                  pointerEvents: 'none',
                }}
              >
                ⌞
              </div>
              <div
                style={{
                  position: 'absolute',
                  bottom: 8,
                  right: 8,
                  fontFamily: 'var(--font-mono)',
                  fontSize: 12,
                  color: 'var(--signal-teal)',
                  zIndex: 750,
                  pointerEvents: 'none',
                }}
              >
                ⌟
              </div>

              {/* Tile Offline Warning */}
              {tileError && (
                <div
                  style={{
                    position: 'absolute',
                    top: 12,
                    left: 12,
                    right: 12,
                    zIndex: 900,
                    background: 'rgba(18, 26, 32, 0.94)',
                    backdropFilter: 'blur(8px)',
                    border: '1px solid var(--border-amber)',
                    borderRadius: 'var(--radius-xs)',
                    padding: '8px 12px',
                    fontSize: 12,
                    color: 'var(--survey-amber)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <span>⚠</span>
                  <span>
                    Basemap tiles temporarily unreachable. Vector footpath coordinates, markers, and audit logs remain
                    active.
                  </span>
                </div>
              )}

              {/* Map Container */}
              <MapContainer
                center={DEFAULT_CENTER}
                zoom={15}
                style={{ height: '100%', width: '100%' }}
                zoomControl
              >
                <TileLayer
                  url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors'
                  maxZoom={19}
                  eventHandlers={{
                    tileerror: () => setTileError(true),
                  }}
                />

                {selected && <MapSoftPan lat={selected.lat} lon={selected.lon} />}

                {segments.map(seg => {
                  const baseColor = STATUS_COLORS[seg.status] ?? '#A6B0BB';
                  const isSelected = seg.id === selectedId;
                  const isBarrier = seg.status === 'BARRIER';
                  const positions: L.LatLngExpression[] = seg.polyline.map(([lat, lon]) => [lat, lon]);

                  return (
                    <span key={seg.id}>
                      {/* Base polyline */}
                      <Polyline
                        positions={positions}
                        pathOptions={{
                          color: isSelected ? '#19D3C5' : baseColor,
                          weight: isSelected ? 8 : 5,
                          opacity: isSelected ? 1 : 0.8,
                          lineCap: 'round',
                          lineJoin: 'round',
                        }}
                        eventHandlers={{
                          click: () => setSelectedId(seg.id),
                        }}
                      />

                      {/* Selected segment subtle pulse outline */}
                      {isSelected && (
                        <Polyline
                          positions={positions}
                          pathOptions={{
                            color: '#19D3C5',
                            weight: 12,
                            opacity: 0.35,
                            lineCap: 'round',
                          }}
                        />
                      )}

                      {/* Barrier or centroid indicator */}
                      {isBarrier && (
                        <CircleMarker
                          center={[seg.lat, seg.lon] as L.LatLngExpression}
                          radius={7}
                          pathOptions={{
                            color: '#FF6268',
                            fillColor: '#FF6268',
                            fillOpacity: 0.65,
                            weight: 2,
                          }}
                          eventHandlers={{ click: () => setSelectedId(seg.id) }}
                        />
                      )}
                    </span>
                  );
                })}
              </MapContainer>

              {/* Coordinated Detail Drawer */}
              <AnimatePresence>
                {selected && (
                  <CoordinatedDrawer
                    segment={selected}
                    onClose={() => setSelectedId(null)}
                  />
                )}
              </AnimatePresence>

              {/* High-craft Legend Overlay */}
              <div
                style={{
                  position: 'absolute',
                  bottom: 16,
                  left: 16,
                  zIndex: 700,
                  background: 'rgba(11, 16, 20, 0.92)',
                  backdropFilter: 'blur(8px)',
                  border: '1px solid var(--border-fine)',
                  borderRadius: 'var(--radius-xs)',
                  padding: '0.625rem 0.875rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.375rem',
                  boxShadow: '0 4px 16px rgba(0, 0, 0, 0.5)',
                }}
              >
                <div
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: 9,
                    color: 'var(--evidence-grey)',
                    letterSpacing: '0.06em',
                    textTransform: 'uppercase',
                    marginBottom: 2,
                  }}
                >
                  VECTOR CLASSIFICATION KEY
                </div>

                {LEGEND_ITEMS.map(item => (
                  <div key={item.status} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11 }}>
                    <div
                      style={{
                        width: 16,
                        height: 4,
                        background: item.color,
                        borderRadius: 1,
                        flexShrink: 0,
                      }}
                    />
                    <span style={{ color: 'var(--paper-muted)', fontFamily: 'var(--font-mono)', fontSize: 10 }}>
                      {item.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Keyboard-Accessible Segment Directory */}
            <div>
              <div
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 11,
                  fontWeight: 600,
                  color: 'var(--evidence-grey)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  marginBottom: '0.75rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span>ACCESSIBLE CORRIDOR INDEX ({segments.length} SECTORS)</span>
                <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>SELECT TO OPEN DOSSIER</span>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                  gap: '0.75rem',
                }}
              >
                {segments.map((seg, idx) => {
                  const meta = verdictMeta(seg.status);
                  const isSelected = seg.id === selectedId;

                  return (
                    <button
                      key={seg.id}
                      type="button"
                      onClick={() => setSelectedId(seg.id)}
                      style={{
                        background: isSelected ? 'var(--deep-surface)' : 'rgba(18, 26, 32, 0.55)',
                        border: `1px solid ${isSelected ? 'var(--signal-teal)' : 'var(--border-fine)'}`,
                        borderRadius: 'var(--radius)',
                        padding: '0.875rem 1rem',
                        textAlign: 'left',
                        cursor: 'pointer',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 6,
                        transition: 'all 0.15s cubic-bezier(0.16, 1, 0.3, 1)',
                        boxShadow: isSelected ? '0 0 12px var(--signal-teal-dim)' : 'none',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--evidence-grey)' }}>
                          SEC-{String(idx + 1).padStart(2, '0')} // {seg.id}
                        </span>

                        <span
                          className={meta.colorClass}
                          style={{
                            fontSize: 10,
                            fontWeight: 700,
                            padding: '1px 6px',
                            borderRadius: 'var(--radius-xs)',
                            fontFamily: 'var(--font-mono)',
                          }}
                        >
                          {meta.label}
                        </span>
                      </div>

                      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--paper-warm)' }}>
                        {seg.name}
                      </div>

                      <div
                        style={{
                          fontSize: 11,
                          color: 'var(--evidence-grey)',
                          display: 'flex',
                          justifyContent: 'space-between',
                          marginTop: 2,
                          fontFamily: 'var(--font-mono)',
                        }}
                      >
                        <span>
                          {seg.captured_at ? formatDate(seg.captured_at) : 'No capture date'}
                        </span>
                        {seg.confidence !== null && (
                          <span style={{ color: 'var(--signal-teal)' }}>
                            {(seg.confidence * 100).toFixed(0)}% conf
                          </span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
