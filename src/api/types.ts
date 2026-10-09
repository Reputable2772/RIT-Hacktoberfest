/**
 * Saakshi Pedestrian Accessibility & Transit Planner
 * API Type Definitions — Version 2.0.0
 * Matches FastAPI Pydantic Models 1-to-1
 */

// --- ENUMS & PRIMITIVES ---

export type AssessmentStatus = 'BARRIER' | 'NO_BARRIER_OBSERVED' | 'INCONCLUSIVE';
export type BarrierVisibility = 'clear' | 'partial' | 'uncertain';
export type FeatureStatus = 'present' | 'absent' | 'unknown';
export type ConfidenceRating = 'high' | 'medium' | 'low';
export type TransitMode = 'metro' | 'bus' | 'walking' | 'mixed';
export type SortCriterion = 'fastest' | 'least_walking' | 'fewest_transfers' | 'best_accessibility';
export type InferenceSource = 'live_local_gemma' | 'live_gemma_api' | 'offline_demo' | 'unavailable';
export type ObservationStatus = 'ready_for_analysis' | 'analysis_completed' | 'image_uncollected';

// --- SYSTEM HEALTH ---

export interface HealthResponse {
  status: string;
  app: string;
  version: string;
  configured_model: string;
}

// --- LOCATIONS ---

export interface DemoLocation {
  id: string; // e.g. "LOC_A"
  key: string; // "A" | "B" | "C"
  name: string;
  short_name: string;
  canonical_name: string;
  lat: number;
  lon: number;
  place_ref: string;
  osm_ref: string;
  description: string;
  accessible_entrances: string[];
}

// --- ROUTE & TRANSIT MODELS ---

export interface RouteSegment {
  id: string;
  mode: TransitMode;
  from_name: string;
  to_name: string;
  from_lat: number;
  from_lon: number;
  to_lat: number;
  to_lon: number;
  distance_meters: number;
  duration_minutes: number;
  transit_line: string | null;
  agency: string | null;
  num_intermediate_stops: number;
  intermediate_stops: string[];
  fare_inr: number | null;
  headway_minutes: number | null;
  data_source: string;
  wheelchair_accessible: boolean;
  pedestrian_concerns: string[];
  polyline: [number, number][]; // [lat, lon] tuples
}

export interface JourneyOption {
  id: string;
  journey_key: string; // "A->B" | "B->C" | "C->A" | "CUSTOM"
  origin_key: string;
  destination_key: string;
  origin_name: string;
  destination_name: string;
  primary_mode: TransitMode;
  title: string;
  summary: string;
  total_duration_minutes: number;
  total_walking_distance_meters: number;
  total_transfers: number;
  estimated_wait_time_minutes: number;
  total_fare_inr: number;
  segments: RouteSegment[];
  observations: PedestrianObservation[];
  accessibility_score: number; // 0.0 - 100.0
  accessibility_verdict: string; // "Highly Accessible" | "Moderate Accessibility" | "Significant Physical Barriers" | "Unassessed"
  accessibility_concerns: string[];
  data_provenance: Record<string, string>;
  recommendation_reasons: string[];
  limitations: string[];
}

// --- ACCESSIBILITY & OBSERVATIONS ---

export interface AccessibilityCriterionFinding {
  criterion: 'sidewalk' | 'curb_ramps' | 'tactile_paving' | 'pedestrian_crossings' | 'obstructions' | 'surface_damage';
  label: string;
  status: FeatureStatus; // "present" | "absent" | "unknown"
  confidence: ConfidenceRating; // "high" | "medium" | "low"
  explanation: string;
}

export interface GemmaVisualAnalysis {
  image_id: string;
  location_id?: string | null;
  segment_id?: string | null;
  status: string; // "completed" | "image_unavailable" | "runtime_unavailable" | "unassessed"
  inference_source: InferenceSource;
  model_used: string;
  evidence_status?: AssessmentStatus | null;
  sidewalk: AccessibilityCriterionFinding;
  curb_ramps: AccessibilityCriterionFinding;
  tactile_paving: AccessibilityCriterionFinding;
  pedestrian_crossings: AccessibilityCriterionFinding;
  obstructions: AccessibilityCriterionFinding;
  surface_damage: AccessibilityCriterionFinding;
  calculated_accessibility_score: number;
  summary: string;
  limitations: string[];
}

export interface ObservationPoint {
  id: string; // "OBS_1"
  name: string;
  location: string;
  lat: number;
  lon: number;
  image_filename: string;
  image_url: string;
  image_available: boolean;
  status: ObservationStatus;
  analysis: GemmaVisualAnalysis | null;
}

export interface PedestrianObservation {
  id: string;
  name: string;
  location_desc: string;
  lat: number;
  lon: number;
  journey_associations: string[];
  streetview_available: boolean;
  inspection_status: string;
  capture_date?: string | null;
  imagery_reference: string;
  imagery_source: string;
  sidewalk: AccessibilityCriterionFinding;
  curb_ramps: AccessibilityCriterionFinding;
  tactile_paving: AccessibilityCriterionFinding;
  pedestrian_crossings: AccessibilityCriterionFinding;
  obstructions: AccessibilityCriterionFinding;
  surface_damage: AccessibilityCriterionFinding;
  accessibility_score: number;
  summary_verdict: string;
  limitations: string[];
}

// --- SINGLE-IMAGE ANALYSIS (Task 1) ---

export interface VisibleBarrier {
  type: string;
  description: string;
  location: string;
  visibility: BarrierVisibility;
}

export interface ModelObservations {
  visible_barriers: VisibleBarrier[];
  visible_features: string[];
  uncertain_observations: string[];
  limitations: string[];
}

export interface ImageQualityResult {
  passed: boolean;
  laplacian_variance: number;
  mean_brightness: number;
  issues: string[];
}

export interface AnalysisResponse {
  status: AssessmentStatus;
  observations: ModelObservations;
  image_quality: ImageQualityResult;
  limitations: string[];
  reason: string;
}

// --- REQUEST BODIES ---

export interface CustomJourneyRequest {
  origin_name: string;
  origin_lat: number;
  origin_lon: number;
  dest_name: string;
  dest_lat: number;
  dest_lon: number;
  sort?: SortCriterion;
}

// --- LEGACY & BENCHMARK COMPATIBILITY TYPES ---

export type Verdict = 'BARRIER' | 'CLEAR_OBSERVED' | 'INCONCLUSIVE' | 'UNVERIFIED';
export type WitnessAgreement = 'AGREE' | 'DISAGREE' | 'NOT_EVALUATED';
export type CaptureDateSource = 'in_app_capture' | 'image_metadata' | 'unknown';

export interface ImageQuality {
  blur_score: number | null;
  exposure_score: number | null;
  passed: boolean;
  notes: string[];
}

export interface Witness {
  name: string;
  result: string;
  score?: number | null;
  observations?: string[];
}

export interface AnalyzeResponse {
  verdict: Verdict;
  barrier_type: string | null;
  description: string;
  confidence: number | null;
  quality: ImageQuality;
  witness_a: Witness;
  witness_b: Witness;
  witness_agreement: WitnessAgreement;
  gate_reasons: string[];
  captured_at: string | null;
  capture_date_source: CaptureDateSource;
  source: string;
  limitations: string[];
  photo_hash: string;
}

export interface SampleImage {
  id: string;
  url: string;
  label: string;
}

export interface BenchmarkPerMode {
  correct: number;
  missed_barriers: number;
  inconclusive_count: number;
  false_reassurance_count: number;
  false_reassurance_rate: number;
}

export interface BenchmarkResponse {
  n: number;
  correct: number;
  missed_barriers: number;
  false_reassurance_count: number;
  false_reassurance_rate: number;
  inconclusive_count: number;
  per_mode: {
    classical: BenchmarkPerMode;
    gemma: BenchmarkPerMode;
    combined: BenchmarkPerMode;
  } | null;
}

export interface Segment {
  id: string;
  name: string;
  lat: number;
  lon: number;
  polyline: [number, number][];
  status: Verdict;
  last_verified: string | null;
  confidence: number | null;
  image_url?: string | null;
  captured_at?: string | null;
  provenance?: string;
  limitations?: string[];
  transit_note?: string;
}
