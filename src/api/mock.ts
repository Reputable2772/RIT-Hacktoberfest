/**
 * Saakshi Pedestrian Accessibility & Transit Planner
 * Mock API Layer — Contract Version 2.0.0
 * Provides offline simulation conforming 1-to-1 with the backend contract.
 */

import type {
  HealthResponse,
  DemoLocation,
  JourneyOption,
  ObservationPoint,
  GemmaVisualAnalysis,
  CustomJourneyRequest,
  SortCriterion,
  AnalyzeResponse,
  SampleImage,
  BenchmarkResponse,
  Segment,
} from './types';

const delay = (ms: number) => new Promise(r => setTimeout(r, ms));

// Health Response
export const mockHealth: HealthResponse = {
  status: 'ok',
  app: 'saakshi',
  version: '2.0.0',
  configured_model: 'gemma-4-26b-a4b-it',
};

// 3.2 Canonical Demo Locations (Mode A)
export const mockLocations: DemoLocation[] = [
  {
    id: 'LOC_A',
    key: 'A',
    name: 'MG Road Metro Station',
    short_name: 'MG Road (A)',
    canonical_name: 'MG Road Metro Station, Mahatma Gandhi Road, Ashok Nagar, Bengaluru',
    lat: 12.975526,
    lon: 77.606790,
    place_ref: 'BMRCL:MAGR',
    osm_ref: 'node/MG_Road_Metro',
    description: 'MG Road / Church Street commercial pedestrian precinct; BMRCL Purple Line Station.',
    accessible_entrances: ['MAGR_A', 'MAGR_B', 'MAGR_C', 'MAGR_D'],
  },
  {
    id: 'LOC_B',
    key: 'B',
    name: 'Cubbon Park Metro Station',
    short_name: 'Cubbon Park (B)',
    canonical_name: 'Cubbon Park Metro Station, Kasturba Road, Bengaluru',
    lat: 12.980958,
    lon: 77.597570,
    place_ref: 'BMRCL:CBPK',
    osm_ref: 'node/Cubbon_Park_Metro',
    description: 'Kasturba Road / Cubbon Park recreational and government precinct; BMRCL Purple Line Station.',
    accessible_entrances: ['CBPK_A', 'CBPK_B', 'CBPK_D'],
  },
  {
    id: 'LOC_C',
    key: 'C',
    name: 'Nadaprabhu Kempegowda Station, Majestic',
    short_name: 'Majestic (C)',
    canonical_name: 'Nadaprabhu Kempegowda Station Majestic / Kempegowda Bus Station (KBS), Bengaluru',
    lat: 12.975708,
    lon: 77.572876,
    place_ref: 'BMRCL:KGWA',
    osm_ref: 'node/Majestic_Interchange',
    description: 'Central transit interchange connecting BMRCL Purple/Green lines and BMTC bus terminals.',
    accessible_entrances: ['KGWA_A', 'KGWA_B', 'KGWA_C', 'KGWA_D', 'KGWA_E'],
  },
];

// In-memory cache for dynamic analysis findings (simulates server ANALYSIS_CACHE)
const observationAnalysisCache: Record<string, GemmaVisualAnalysis> = {};
const segmentAnalysisCache: Record<string, GemmaVisualAnalysis> = {};

// 3.4 Prepared Street View Observation Points
export const mockObservations: ObservationPoint[] = [
  {
    id: 'OBS_1',
    name: 'MG Road Metro Entrance A / Church Street',
    location: 'MG Road (Point A)',
    lat: 12.975420,
    lon: 77.606510,
    image_filename: 'data/street_view/a_to_b/0001.png',
    image_url: '/images/sample_clear.jpg',
    image_available: true,
    status: 'ready_for_analysis',
    analysis: null,
  },
  {
    id: 'OBS_2',
    name: 'Kasturba Road / Cubbon Park Walkway',
    location: 'Kasturba Road connector (A <-> B)',
    lat: 12.978900,
    lon: 77.600900,
    image_filename: 'data/street_view/a_to_b/0011.png',
    image_url: '/images/sample_barrier.jpg',
    image_available: true,
    status: 'ready_for_analysis',
    analysis: null,
  },
  {
    id: 'OBS_3',
    name: 'Cubbon Park Metro Entrance B / Kasturba Cross',
    location: 'Cubbon Park (Point B)',
    lat: 12.980800,
    lon: 77.597400,
    image_filename: 'data/street_view/b_to_c/0001.png',
    image_url: '/images/sample_clear.jpg',
    image_available: true,
    status: 'ready_for_analysis',
    analysis: null,
  },
  {
    id: 'OBS_4',
    name: 'Ambedkar Veedhi Pedestrian Corridor',
    location: 'Vidhana Soudha connector (B <-> C)',
    lat: 12.978200,
    lon: 77.591000,
    image_filename: 'data/street_view/b_to_c/0015.png',
    image_url: '/images/sample_barrier.jpg',
    image_available: true,
    status: 'ready_for_analysis',
    analysis: null,
  },
  {
    id: 'OBS_5',
    name: 'Majestic KBS Underpass & Footway',
    location: 'Kempegowda Interchange (Point C)',
    lat: 12.975800,
    lon: 77.573200,
    image_filename: 'data/street_view/c_to_a/0020.png',
    image_url: '/images/sample_inconclusive.jpg',
    image_available: true,
    status: 'ready_for_analysis',
    analysis: null,
  },
];

// Initial Base Journey Options
function buildBaseJourneys(): Record<string, JourneyOption[]> {
  const isObs2Analyzed = !!observationAnalysisCache['OBS_2'];
  const obs2Score = isObs2Analyzed ? observationAnalysisCache['OBS_2'].calculated_accessibility_score : 70;

  return {
    'A->B': [
      {
        id: 'J_AB_METRO',
        journey_key: 'A->B',
        origin_key: 'A',
        destination_key: 'B',
        origin_name: 'MG Road Metro Station',
        destination_name: 'Cubbon Park Metro Station',
        primary_mode: 'metro',
        title: 'BMRCL Purple Line Metro (Direct)',
        summary: 'Elevator-accessible direct metro connection between MG Road and Cubbon Park. 1 stop.',
        total_duration_minutes: 9,
        total_walking_distance_meters: 210,
        total_transfers: 0,
        estimated_wait_time_minutes: 3,
        total_fare_inr: 10.0,
        accessibility_score: 94.0,
        accessibility_verdict: 'Highly Accessible',
        accessibility_concerns: [],
        recommendation_reasons: [
          'Fastest transit option (9 min total door-to-door).',
          'Elevator access verified at both MG Road and Cubbon Park stations.',
        ],
        data_provenance: {
          metro_schedule: 'verified_bmrcl_gtfs',
          walking_segments: 'estimated_walking_speed',
          accessibility: 'google_street_view_and_survey',
        },
        limitations: [
          'Platform gaps exist between train and platform (~7cm horizontal, 3cm vertical).',
        ],
        segments: [
          {
            id: 'AB_M_1',
            mode: 'walking',
            from_name: 'MG Road Station Entrance A',
            to_name: 'MG Road Platform 1',
            from_lat: 12.975526,
            from_lon: 77.606790,
            to_lat: 12.975429,
            to_lon: 77.607260,
            distance_meters: 110,
            duration_minutes: 2,
            transit_line: null,
            agency: 'Pedestrian',
            num_intermediate_stops: 0,
            intermediate_stops: [],
            fare_inr: null,
            headway_minutes: null,
            data_source: 'estimated_walking_speed',
            wheelchair_accessible: true,
            pedestrian_concerns: [],
            polyline: [
              [12.975526, 77.606790],
              [12.975429, 77.607260],
            ],
          },
          {
            id: 'AB_M_2',
            mode: 'metro',
            from_name: 'MG Road Metro Station',
            to_name: 'Cubbon Park Metro Station',
            from_lat: 12.975429,
            from_lon: 77.607260,
            to_lat: 12.980958,
            to_lon: 77.597570,
            distance_meters: 1300,
            duration_minutes: 4,
            transit_line: 'Purple Line',
            agency: 'BMRCL',
            num_intermediate_stops: 0,
            intermediate_stops: [],
            fare_inr: 10.0,
            headway_minutes: 5,
            data_source: 'verified_bmrcl_gtfs',
            wheelchair_accessible: true,
            pedestrian_concerns: [],
            polyline: [
              [12.975429, 77.607260],
              [12.978200, 77.602000],
              [12.980958, 77.597570],
            ],
          },
          {
            id: 'AB_M_3',
            mode: 'walking',
            from_name: 'Cubbon Park Concourse',
            to_name: 'Cubbon Park Kasturba Gate',
            from_lat: 12.980958,
            from_lon: 77.597570,
            to_lat: 12.981300,
            to_lon: 77.597800,
            distance_meters: 100,
            duration_minutes: 2,
            transit_line: null,
            agency: 'Pedestrian',
            num_intermediate_stops: 0,
            intermediate_stops: [],
            fare_inr: null,
            headway_minutes: null,
            data_source: 'estimated_walking_speed',
            wheelchair_accessible: true,
            pedestrian_concerns: [],
            polyline: [
              [12.980958, 77.597570],
              [12.981300, 77.597800],
            ],
          },
        ],
        observations: [],
      },
      {
        id: 'J_AB_WALK',
        journey_key: 'A->B',
        origin_key: 'A',
        destination_key: 'B',
        origin_name: 'MG Road Metro Station',
        destination_name: 'Cubbon Park Metro Station',
        primary_mode: 'walking',
        title: 'Kasturba Road Footpath Corridor (Direct Walk)',
        summary: 'Direct pedestrian walk along MG Road and Kasturba Road past Cubbon Park perimeter.',
        total_duration_minutes: 18,
        total_walking_distance_meters: 1450,
        total_transfers: 0,
        estimated_wait_time_minutes: 0,
        total_fare_inr: 0.0,
        accessibility_score: obs2Score,
        accessibility_verdict:
          obs2Score < 50
            ? 'Significant Physical Barriers'
            : obs2Score < 80
            ? 'Moderate Accessibility'
            : 'Highly Accessible',
        accessibility_concerns: isObs2Analyzed
          ? ['Severe vehicular encroachment on footpath', 'Missing curb cut at Kasturba junction']
          : ['Footpath quality unverified by vision model'],
        recommendation_reasons: ['Zero transit waiting time.', 'Scenic tree-lined park promenade.'],
        data_provenance: {
          walking_speed: 'pedestrian_survey_speed',
          imagery: 'street_view_point_obs_2',
        },
        limitations: [
          'High vehicle exhaust during peak hours.',
          'Sidewalk width narrows below 60cm near Queen Victoria statue.',
        ],
        segments: [
          {
            id: 'AB_W_1',
            mode: 'walking',
            from_name: 'MG Road Anil Kumble Circle',
            to_name: 'Cubbon Park Walkway (OBS_2)',
            from_lat: 12.975526,
            from_lon: 77.606790,
            to_lat: 12.978900,
            to_lon: 77.600900,
            distance_meters: 750,
            duration_minutes: 9,
            transit_line: null,
            agency: 'Pedestrian',
            num_intermediate_stops: 0,
            intermediate_stops: [],
            fare_inr: 0,
            headway_minutes: null,
            data_source: 'estimated_walking_speed',
            wheelchair_accessible: false,
            pedestrian_concerns: ['Narrowed pavement', 'Parked motorcycles'],
            polyline: [
              [12.975526, 77.606790],
              [12.976800, 77.604500],
              [12.978900, 77.600900],
            ],
          },
          {
            id: 'AB_W_2',
            mode: 'walking',
            from_name: 'Cubbon Park Walkway (OBS_2)',
            to_name: 'Cubbon Park Metro Station',
            from_lat: 12.978900,
            from_lon: 77.600900,
            to_lat: 12.980958,
            to_lon: 77.597570,
            distance_meters: 700,
            duration_minutes: 9,
            transit_line: null,
            agency: 'Pedestrian',
            num_intermediate_stops: 0,
            intermediate_stops: [],
            fare_inr: 0,
            headway_minutes: null,
            data_source: 'estimated_walking_speed',
            wheelchair_accessible: true,
            pedestrian_concerns: [],
            polyline: [
              [12.978900, 77.600900],
              [12.980200, 77.599000],
              [12.980958, 77.597570],
            ],
          },
        ],
        observations: [],
      },
      {
        id: 'J_AB_BUS',
        journey_key: 'A->B',
        origin_key: 'A',
        destination_key: 'B',
        origin_name: 'MG Road Metro Station',
        destination_name: 'Cubbon Park Metro Station',
        primary_mode: 'bus',
        title: 'BMTC Route 138 / 314E Bus',
        summary: 'BMTC frequent trunk bus service via Anil Kumble Circle to General Post Office stop.',
        total_duration_minutes: 14,
        total_walking_distance_meters: 320,
        total_transfers: 0,
        estimated_wait_time_minutes: 5,
        total_fare_inr: 15.0,
        accessibility_score: 72.0,
        accessibility_verdict: 'Moderate Accessibility',
        accessibility_concerns: ['High-floor bus entrance requires stepping up two 25cm steps.'],
        recommendation_reasons: ['Low fare option.', 'Frequent departure every 6 minutes.'],
        data_provenance: {
          bus_schedule: 'bmtc_gtfs_static',
        },
        limitations: ['Non-air-conditioned standard bus without hydraulic kneeling ramp.'],
        segments: [
          {
            id: 'AB_B_1',
            mode: 'walking',
            from_name: 'MG Road Station',
            to_name: 'BRV Parade Grounds Bus Stop',
            from_lat: 12.975526,
            from_lon: 77.606790,
            to_lat: 12.976100,
            to_lon: 77.605200,
            distance_meters: 180,
            duration_minutes: 3,
            transit_line: null,
            agency: 'Pedestrian',
            num_intermediate_stops: 0,
            intermediate_stops: [],
            fare_inr: null,
            headway_minutes: null,
            data_source: 'estimated_walking_speed',
            wheelchair_accessible: true,
            pedestrian_concerns: [],
            polyline: [
              [12.975526, 77.606790],
              [12.976100, 77.605200],
            ],
          },
          {
            id: 'AB_B_2',
            mode: 'bus',
            from_name: 'BRV Parade Grounds Bus Stop',
            to_name: 'GPO / Cubbon Park Station',
            from_lat: 12.976100,
            from_lon: 77.605200,
            to_lat: 12.980800,
            to_lon: 77.598200,
            distance_meters: 1200,
            duration_minutes: 8,
            transit_line: 'Route 138',
            agency: 'BMTC',
            num_intermediate_stops: 1,
            intermediate_stops: ['Raj Bhavan Circle'],
            fare_inr: 15.0,
            headway_minutes: 6,
            data_source: 'bmtc_gtfs_static',
            wheelchair_accessible: false,
            pedestrian_concerns: ['High bus entry step'],
            polyline: [
              [12.976100, 77.605200],
              [12.979000, 77.601500],
              [12.980800, 77.598200],
            ],
          },
        ],
        observations: [],
      },
    ],
    'B->C': [
      {
        id: 'J_BC_METRO',
        journey_key: 'B->C',
        origin_key: 'B',
        destination_key: 'C',
        origin_name: 'Cubbon Park Metro Station',
        destination_name: 'Nadaprabhu Kempegowda Station, Majestic',
        primary_mode: 'metro',
        title: 'BMRCL Purple Line Metro (Direct)',
        summary: 'Direct underground metro ride to Majestic Central Interchange. 2 stops.',
        total_duration_minutes: 12,
        total_walking_distance_meters: 280,
        total_transfers: 0,
        estimated_wait_time_minutes: 4,
        total_fare_inr: 15.0,
        accessibility_score: 92.0,
        accessibility_verdict: 'Highly Accessible',
        accessibility_concerns: [],
        recommendation_reasons: [
          'Direct rapid transit bypasses Anand Rao Circle traffic bottleneck.',
          'Tactile ground guides inside Majestic interchange.',
        ],
        data_provenance: {
          metro_schedule: 'verified_bmrcl_gtfs',
        },
        limitations: ['Majestic station involves large concourse walking distances (~150m).'],
        segments: [
          {
            id: 'BC_M_1',
            mode: 'metro',
            from_name: 'Cubbon Park Metro',
            to_name: 'Majestic Metro',
            from_lat: 12.980958,
            from_lon: 77.597570,
            to_lat: 12.975708,
            to_lon: 77.572876,
            distance_meters: 2900,
            duration_minutes: 6,
            transit_line: 'Purple Line',
            agency: 'BMRCL',
            num_intermediate_stops: 1,
            intermediate_stops: ['Sir M. Visvesvaraya Station'],
            fare_inr: 15.0,
            headway_minutes: 5,
            data_source: 'verified_bmrcl_gtfs',
            wheelchair_accessible: true,
            pedestrian_concerns: [],
            polyline: [
              [12.980958, 77.597570],
              [12.978000, 77.585000],
              [12.975708, 77.572876],
            ],
          },
        ],
        observations: [],
      },
    ],
    'C->A': [
      {
        id: 'J_CA_METRO',
        journey_key: 'C->A',
        origin_key: 'C',
        destination_key: 'A',
        origin_name: 'Nadaprabhu Kempegowda Station, Majestic',
        destination_name: 'MG Road Metro Station',
        primary_mode: 'metro',
        title: 'BMRCL Purple Line Metro (Direct Eastbound)',
        summary: 'Fast direct transit connecting Majestic to MG Road. 3 stops.',
        total_duration_minutes: 15,
        total_walking_distance_meters: 310,
        total_transfers: 0,
        estimated_wait_time_minutes: 4,
        total_fare_inr: 20.0,
        accessibility_score: 95.0,
        accessibility_verdict: 'Highly Accessible',
        accessibility_concerns: [],
        recommendation_reasons: ['Fastest door-to-door corridor connection.'],
        data_provenance: { metro_schedule: 'verified_bmrcl_gtfs' },
        limitations: [],
        segments: [
          {
            id: 'CA_M_1',
            mode: 'metro',
            from_name: 'Majestic Metro',
            to_name: 'MG Road Metro',
            from_lat: 12.975708,
            from_lon: 77.572876,
            to_lat: 12.975526,
            to_lon: 77.606790,
            distance_meters: 4200,
            duration_minutes: 9,
            transit_line: 'Purple Line',
            agency: 'BMRCL',
            num_intermediate_stops: 2,
            intermediate_stops: ['Sir M. Visvesvaraya', 'Cubbon Park'],
            fare_inr: 20.0,
            headway_minutes: 5,
            data_source: 'verified_bmrcl_gtfs',
            wheelchair_accessible: true,
            pedestrian_concerns: [],
            polyline: [
              [12.975708, 77.572876],
              [12.978000, 77.585000],
              [12.980958, 77.597570],
              [12.975526, 77.606790],
            ],
          },
        ],
        observations: [],
      },
    ],
  };
}

// 3.3 GET /api/journeys
export async function mockGetJourneys(sort: SortCriterion = 'fastest'): Promise<Record<string, JourneyOption[]>> {
  await delay(250);
  const data = buildBaseJourneys();

  // Apply sorting
  for (const key of Object.keys(data)) {
    data[key].sort((a, b) => {
      switch (sort) {
        case 'fastest':
          return a.total_duration_minutes - b.total_duration_minutes;
        case 'least_walking':
          return a.total_walking_distance_meters - b.total_walking_distance_meters;
        case 'fewest_transfers':
          return a.total_transfers - b.total_transfers;
        case 'best_accessibility':
          return b.accessibility_score - a.accessibility_score;
        default:
          return 0;
      }
    });
  }

  return data;
}

// 3.4 GET /api/observations
export async function mockGetObservations(): Promise<ObservationPoint[]> {
  await delay(200);
  return mockObservations.map(obs => ({
    ...obs,
    status: observationAnalysisCache[obs.id] ? 'analysis_completed' : 'ready_for_analysis',
    analysis: observationAnalysisCache[obs.id] || null,
  }));
}

// 3.5 POST /api/analyze-observation/{obs_id}
export async function mockAnalyzeObservation(obsId: string): Promise<GemmaVisualAnalysis> {
  await delay(1200);

  let result: GemmaVisualAnalysis;

  if (obsId === 'OBS_2' || obsId === 'OBS_4') {
    result = {
      image_id: obsId,
      location_id: 'Kasturba Road connector (A <-> B)',
      status: 'completed',
      inference_source: 'live_gemma_api',
      model_used: 'gemma-4-26b-a4b-it',
      evidence_status: 'BARRIER',
      sidewalk: {
        criterion: 'sidewalk',
        label: 'Sidewalk Continuity',
        status: 'present',
        confidence: 'high',
        explanation: 'Sidewalk pavers are interrupted by broken utility trenches and uneven curbing.',
      },
      curb_ramps: {
        criterion: 'curb_ramps',
        label: 'Curb Ramps',
        status: 'absent',
        confidence: 'high',
        explanation: 'High unramped sidewalk curb ~22cm creates an impassable barrier for wheelchairs.',
      },
      tactile_paving: {
        criterion: 'tactile_paving',
        label: 'Tactile Paving',
        status: 'absent',
        confidence: 'high',
        explanation: 'Zero tactile warning blister or directional pavers present.',
      },
      pedestrian_crossings: {
        criterion: 'pedestrian_crossings',
        label: 'Pedestrian Crossings',
        status: 'absent',
        confidence: 'medium',
        explanation: 'Crossing at junction lacks marked zebra stripes or pedestrian signalization.',
      },
      obstructions: {
        criterion: 'obstructions',
        label: 'Obstructions & Encroachment',
        status: 'present',
        confidence: 'high',
        explanation: 'Parked motorcycles and commercial delivery crates obstruct 75% of usable footpath line.',
      },
      surface_damage: {
        criterion: 'surface_damage',
        label: 'Surface Damage',
        status: 'present',
        confidence: 'high',
        explanation: 'Displaced granite slabs with exposed mud and a 15cm trip hazard gap.',
      },
      calculated_accessibility_score: 28.0,
      summary: 'Critical physical barriers: high unramped curb and heavy vehicle encroachment block passage.',
      limitations: [
        'Assessment based on single daytime image angle.',
        'Dynamic vehicle parking may fluctuate throughout the day.',
      ],
    };
  } else {
    result = {
      image_id: obsId,
      location_id: 'MG Road (Point A)',
      status: 'completed',
      inference_source: 'live_gemma_api',
      model_used: 'gemma-4-26b-a4b-it',
      evidence_status: 'NO_BARRIER_OBSERVED',
      sidewalk: {
        criterion: 'sidewalk',
        label: 'Sidewalk Continuity',
        status: 'present',
        confidence: 'high',
        explanation: 'Paved cobblestone Church Street pedestrian precinct provides wide, continuous walkway.',
      },
      curb_ramps: {
        criterion: 'curb_ramps',
        label: 'Curb Ramps',
        status: 'present',
        confidence: 'medium',
        explanation: 'Level flush transition between pedestrianized street and entrance gate.',
      },
      tactile_paving: {
        criterion: 'tactile_paving',
        label: 'Tactile Paving',
        status: 'absent',
        confidence: 'high',
        explanation: 'Tactile guidance pavers not observed on main decorative stone surface.',
      },
      pedestrian_crossings: {
        criterion: 'pedestrian_crossings',
        label: 'Pedestrian Crossings',
        status: 'present',
        confidence: 'high',
        explanation: 'Signalized crossing at Anil Kumble circle.',
      },
      obstructions: {
        criterion: 'obstructions',
        label: 'Obstructions & Encroachment',
        status: 'absent',
        confidence: 'high',
        explanation: 'Wide pedestrian precinct clear of vehicles or construction debris.',
      },
      surface_damage: {
        criterion: 'surface_damage',
        label: 'Surface Damage',
        status: 'absent',
        confidence: 'medium',
        explanation: 'Pavement is intact and level.',
      },
      calculated_accessibility_score: 88.0,
      summary: 'Pedestrian plaza offers barrier-free access with level transitions.',
      limitations: ['Assessment based on static camera perspective.'],
    };
  }

  observationAnalysisCache[obsId] = result;
  return result;
}

// 3.6 POST /api/custom-journey (Mode B)
export async function mockPlanCustomJourney(request: CustomJourneyRequest): Promise<JourneyOption[]> {
  await delay(700);

  const walkingDistance = 480;
  const busDuration = 26;
  const customScore = segmentAnalysisCache['CUSTOM_WALK_1']
    ? segmentAnalysisCache['CUSTOM_WALK_1'].calculated_accessibility_score
    : 50.0;

  return [
    {
      id: 'CUSTOM_BUS_1',
      journey_key: 'CUSTOM',
      origin_key: 'ORIGIN',
      destination_key: 'DEST',
      origin_name: request.origin_name || 'Origin',
      destination_name: request.dest_name || 'Destination',
      primary_mode: 'bus',
      title: 'BMTC Direct Bus Corridor',
      summary: `BMTC connection matching stops nearest to ${request.origin_name} and ${request.dest_name}.`,
      total_duration_minutes: busDuration + 8,
      total_walking_distance_meters: walkingDistance,
      total_transfers: 0,
      estimated_wait_time_minutes: 6,
      total_fare_inr: 25.0,
      accessibility_score: customScore,
      accessibility_verdict:
        customScore >= 80 ? 'Highly Accessible' : customScore >= 50 ? 'Unassessed' : 'Significant Physical Barriers',
      accessibility_concerns: segmentAnalysisCache['CUSTOM_WALK_1']
        ? ['Sidewalk physical obstructions recorded from user photo audit.']
        : ['Visual evidence not yet audited for walking connectors. Upload a photo to audit.'],
      recommendation_reasons: ['Direct GTFS-matched public transit without transfers.'],
      data_provenance: {
        bus_stops: 'gtfs_stop_matched_spatial_estimate',
      },
      limitations: [
        'Walking connector walkability has not been fully verified with imagery. Upload a photo to audit.',
      ],
      segments: [
        {
          id: 'CUSTOM_WALK_1',
          mode: 'walking',
          from_name: request.origin_name,
          to_name: 'Nearest BMTC Bus Stop',
          from_lat: request.origin_lat,
          from_lon: request.origin_lon,
          to_lat: request.origin_lat + 0.0018,
          to_lon: request.origin_lon + 0.0012,
          distance_meters: 220,
          duration_minutes: 4,
          transit_line: null,
          agency: 'Pedestrian',
          num_intermediate_stops: 0,
          intermediate_stops: [],
          fare_inr: null,
          headway_minutes: null,
          data_source: 'estimated_walking_speed',
          wheelchair_accessible: customScore >= 70,
          pedestrian_concerns: [],
          polyline: [
            [request.origin_lat, request.origin_lon],
            [request.origin_lat + 0.0018, request.origin_lon + 0.0012],
          ],
        },
        {
          id: 'CUSTOM_BUS_SEG_2',
          mode: 'bus',
          from_name: 'Nearest BMTC Bus Stop',
          to_name: 'Destination BMTC Bus Stop',
          from_lat: request.origin_lat + 0.0018,
          from_lon: request.origin_lon + 0.0012,
          to_lat: request.dest_lat - 0.0015,
          to_lon: request.dest_lon - 0.0010,
          distance_meters: 4800,
          duration_minutes: busDuration,
          transit_line: 'Route 201G',
          agency: 'BMTC',
          num_intermediate_stops: 5,
          intermediate_stops: ['Stop 1', 'Stop 2', 'Stop 3', 'Stop 4', 'Stop 5'],
          fare_inr: 25.0,
          headway_minutes: 8,
          data_source: 'gtfs_stop_matched_spatial_estimate',
          wheelchair_accessible: false,
          pedestrian_concerns: [],
          polyline: [
            [request.origin_lat + 0.0018, request.origin_lon + 0.0012],
            [(request.origin_lat + request.dest_lat) / 2, (request.origin_lon + request.dest_lon) / 2],
            [request.dest_lat - 0.0015, request.dest_lon - 0.0010],
          ],
        },
        {
          id: 'CUSTOM_WALK_3',
          mode: 'walking',
          from_name: 'Destination BMTC Bus Stop',
          to_name: request.dest_name,
          from_lat: request.dest_lat - 0.0015,
          from_lon: request.dest_lon - 0.0010,
          to_lat: request.dest_lat,
          to_lon: request.dest_lon,
          distance_meters: 260,
          duration_minutes: 4,
          transit_line: null,
          agency: 'Pedestrian',
          num_intermediate_stops: 0,
          intermediate_stops: [],
          fare_inr: null,
          headway_minutes: null,
          data_source: 'estimated_walking_speed',
          wheelchair_accessible: true,
          pedestrian_concerns: [],
          polyline: [
            [request.dest_lat - 0.0015, request.dest_lon - 0.0010],
            [request.dest_lat, request.dest_lon],
          ],
        },
      ],
      observations: [],
    },
  ];
}

// 3.7 POST /api/upload-and-analyze?segment_id=...
export async function mockUploadAndAnalyze(image: File, segmentId: string): Promise<GemmaVisualAnalysis> {
  await delay(1400);

  if (image.name.toLowerCase().includes('inconclusive') || image.name.toLowerCase().includes('blur')) {
    throw new Error('Image failed quality check: Image is severely blurred (Laplacian variance 42.1 < 100.0). Please hold camera steady.');
  }

  const isBarrier = image.name.toLowerCase().includes('barrier');

  const analysis: GemmaVisualAnalysis = {
    image_id: `UPLOAD_${Date.now()}`,
    segment_id: segmentId,
    status: 'completed',
    inference_source: 'live_gemma_api',
    model_used: 'gemma-4-26b-a4b-it',
    evidence_status: isBarrier ? 'BARRIER' : 'NO_BARRIER_OBSERVED',
    sidewalk: {
      criterion: 'sidewalk',
      label: 'Sidewalk Continuity',
      status: 'present',
      confidence: 'high',
      explanation: isBarrier ? 'Pavement slabs cracked with broken curb edges.' : 'Continuous paved sidewalk.',
    },
    curb_ramps: {
      criterion: 'curb_ramps',
      label: 'Curb Ramps',
      status: isBarrier ? 'absent' : 'present',
      confidence: 'high',
      explanation: isBarrier ? 'Unramped 18cm vertical drop.' : 'Gradual asphalt curb ramp present.',
    },
    tactile_paving: {
      criterion: 'tactile_paving',
      label: 'Tactile Paving',
      status: 'absent',
      confidence: 'high',
      explanation: 'No directional or warning tactile tiles present.',
    },
    pedestrian_crossings: {
      criterion: 'pedestrian_crossings',
      label: 'Pedestrian Crossings',
      status: 'present',
      confidence: 'medium',
      explanation: 'Unsignalized pedestrian zebra crossing visible.',
    },
    obstructions: {
      criterion: 'obstructions',
      label: 'Obstructions & Encroachment',
      status: isBarrier ? 'present' : 'absent',
      confidence: 'high',
      explanation: isBarrier ? 'Two-wheelers parked across sidewalk reducing clear path.' : 'Path is clear of debris or vehicles.',
    },
    surface_damage: {
      criterion: 'surface_damage',
      label: 'Surface Damage',
      status: isBarrier ? 'present' : 'absent',
      confidence: 'medium',
      explanation: isBarrier ? 'Uneven tiles and potholes present.' : 'Uniform paved surface.',
    },
    calculated_accessibility_score: isBarrier ? 34.0 : 86.0,
    summary: isBarrier
      ? 'Physical obstructions and curb steps detected. Walking connector accessibility degraded.'
      : 'Continuous sidewalk with passable surface verified by Gemma.',
    limitations: ['Verified from user-submitted photograph.'],
  };

  segmentAnalysisCache[segmentId] = analysis;
  return analysis;
}

// 3.8 POST /api/analyze (Standalone Single-Image Analysis)
export async function mockAnalyzeImage(image: File): Promise<AnalyzeResponse> {
  await delay(1500);
  const name = image.name.toLowerCase();
  if (name.includes('clear')) {
    return mockAnalyzeResponseClear;
  }
  if (name.includes('inconclusive') || name.includes('blur')) {
    return mockAnalyzeResponseInconclusive;
  }
  return mockAnalyzeResponseBarrier;
}

// Legacy Mock Artifacts
export const mockSamples: SampleImage[] = [
  { id: 'sample-1', url: '/images/sample_barrier.jpg', label: 'Obstruction (Motorcycle & Delivery Boxes)' },
  { id: 'sample-2', url: '/images/sample_clear.jpg', label: 'Clear Footpath (Unobstructed Paved Slabs)' },
  { id: 'sample-3', url: '/images/sample_inconclusive.jpg', label: 'Low Light / Glare (Motion Blur & Shadow)' },
];

export const mockAnalyzeResponseBarrier: AnalyzeResponse = {
  verdict: 'BARRIER',
  barrier_type: 'Vehicle & Cargo Obstruction',
  description: 'A parked motorcycle and stacked delivery boxes encroach across the pedestrian walkway, reducing usable walking width to under 45 cm.',
  confidence: 0.88,
  quality: { blur_score: 0.09, exposure_score: 0.76, passed: true, notes: ['Image sharpness adequate', 'Even ambient exposure across walkway'] },
  witness_a: { name: 'OpenCV (Geometric & Edge)', result: 'Physical obstacle detected', score: 0.84 },
  witness_b: {
    name: 'Gemma 4 (Vision-Language)',
    result: 'BARRIER',
    observations: ['Two-wheeled motor vehicle positioned across footpath slabs', 'Cardboard cargo boxes further reduce clearance'],
  },
  witness_agreement: 'AGREE',
  gate_reasons: [
    'Both independent witnesses flagged physical barrier',
    'Combined confidence score exceeds 0.75 decision threshold',
    'Image quality passed minimum verification gate',
  ],
  captured_at: '2026-10-09T08:30:00Z',
  capture_date_source: 'image_metadata',
  source: 'mock_pilot_v1',
  limitations: [
    'Mock pilot demonstration record — not an in-situ guarantee',
    'Reflects captured timestamp only; conditions may have changed',
    'Decision support for urban audit only; not route guidance',
  ],
  photo_hash: 'sha256-4c9b81f18e907d739828e1d24490f23a9b1c7849e8a56214a1c0d4812ef62b10',
};

export const mockAnalyzeResponseClear: AnalyzeResponse = {
  verdict: 'CLEAR_OBSERVED',
  barrier_type: null,
  description: 'Continuous paved pedestrian sidewalk observed with no blocking obstacles or physical barriers within the captured camera frame.',
  confidence: 0.93,
  quality: { blur_score: 0.05, exposure_score: 0.81, passed: true, notes: ['Sharp edge delineation on concrete tiles', 'Natural daylight illumination'] },
  witness_a: { name: 'OpenCV (Geometric & Edge)', result: 'Unobstructed path trajectory', score: 0.91 },
  witness_b: {
    name: 'Gemma 4 (Vision-Language)',
    result: 'CLEAR_OBSERVED',
    observations: ['Sidewalk surface is uniform and level', 'No vehicles or construction debris encroaching on walking line'],
  },
  witness_agreement: 'AGREE',
  gate_reasons: ['Both witnesses independently found no barrier present', 'Quality verification checks passed'],
  captured_at: '2026-10-09T09:15:00Z',
  capture_date_source: 'image_metadata',
  source: 'mock_pilot_v1',
  limitations: ['Observation valid at capture time only', 'Not a navigation guarantee'],
  photo_hash: 'sha256-78e20da594382c7df8b0938472491a938fe743901bce5849d03847210e829374',
};

export const mockAnalyzeResponseInconclusive: AnalyzeResponse = {
  verdict: 'INCONCLUSIVE',
  barrier_type: null,
  description: 'Harsh artificial glare, motion blur, and deep shadows prevent unambiguous edge detection and obstacle segmentation.',
  confidence: 0.42,
  quality: { blur_score: 0.62, exposure_score: 0.28, passed: false, notes: ['Motion blur exceeds limit', 'High contrast glare obscures walking surface'] },
  witness_a: { name: 'OpenCV (Geometric & Edge)', result: 'Low confidence / ambiguous edges', score: 0.45 },
  witness_b: { name: 'Gemma 4 (Vision-Language)', result: 'INCONCLUSIVE', observations: ['Scene illumination is uneven with heavy backlight'] },
  witness_agreement: 'NOT_EVALUATED',
  gate_reasons: ['Image quality pre-gate check failed', 'Confidence fails minimum 0.70 threshold', 'Refusal gate triggered to prevent false reassurance'],
  captured_at: null,
  capture_date_source: 'unknown',
  source: 'mock_pilot_v1',
  limitations: ['Quality gate refused evaluation to prevent erroneous safety classification', 'Retake recommended under daylight'],
  photo_hash: 'sha256-a938df10928e4019283049182390481230498102394810293481029384019283',
};

export const mockBenchmark: BenchmarkResponse = {
  n: 0,
  correct: 0,
  missed_barriers: 0,
  false_reassurance_count: 0,
  false_reassurance_rate: 0,
  inconclusive_count: 0,
  per_mode: null,
};

export const mockSegments: Segment[] = [
  {
    id: 'seg-1',
    name: 'MG Road North Section (Pedestrian Zone)',
    lat: 12.9757,
    lon: 77.6074,
    polyline: [[12.9757, 77.6074], [12.9762, 77.6080], [12.9768, 77.6085]],
    status: 'BARRIER',
    last_verified: '2026-10-09T08:30:00Z',
    confidence: 0.88,
    image_url: '/images/sample_barrier.jpg',
    captured_at: '2026-10-09T08:30:00Z',
    provenance: 'Civic Field Pilot BLR-01 // WGS84 Centroid: 12.9762°N, 77.6080°E',
    limitations: ['Visual record valid strictly for capture moment; physical obstructions can shift dynamically.'],
    transit_note: 'BMTC bus stop within 80m (Trinity/MG Rd); real-time schedule feed not integrated for this pilot corridor.',
  },
  {
    id: 'seg-2',
    name: 'Brigade Road Stretch (Paved Footway)',
    lat: 12.9720,
    lon: 77.6080,
    polyline: [[12.9720, 77.6080], [12.9725, 77.6088], [12.9730, 77.6096]],
    status: 'CLEAR_OBSERVED',
    last_verified: '2026-10-09T09:15:00Z',
    confidence: 0.93,
    image_url: '/images/sample_clear.jpg',
    captured_at: '2026-10-09T09:15:00Z',
    provenance: 'Civic Field Pilot BLR-01 // WGS84 Centroid: 12.9725°N, 77.6088°E',
    limitations: ['Reflects clear path observed at camera capture; does not guarantee permanent clearance.'],
    transit_note: 'BMRCL MG Road Metro station 320m north; train arrival times not coupled to audit instrument.',
  },
  {
    id: 'seg-3',
    name: 'Church Street Segment (Shadowed Corridors)',
    lat: 12.9740,
    lon: 77.6055,
    polyline: [[12.9740, 77.6055], [12.9745, 77.6060], [12.9750, 77.6065]],
    status: 'INCONCLUSIVE',
    last_verified: null,
    confidence: null,
    image_url: '/images/sample_inconclusive.jpg',
    captured_at: '2026-10-09T07:45:00Z',
    provenance: 'Civic Field Pilot BLR-01 // WGS84 Centroid: 12.9745°N, 77.6060°E',
    limitations: ['Pre-gate filter refused evaluation due to optical glare and heavy shadowing.'],
    transit_note: 'Pedestrian plaza zone; public transit timetables not integrated into evidence pipeline.',
  },
  {
    id: 'seg-4',
    name: 'Residency Road East (Uninspected Segment)',
    lat: 12.9705,
    lon: 77.6065,
    polyline: [[12.9705, 77.6065], [12.9710, 77.6072], [12.9715, 77.6079]],
    status: 'UNVERIFIED',
    last_verified: null,
    confidence: null,
    image_url: null,
    captured_at: null,
    provenance: 'OpenStreetMap geometry registration only // Pending field sensor survey',
    limitations: ['No photographic evidence has been logged for this segment.'],
    transit_note: 'Corridor vector cataloged only; no transit or accessibility telemetry available.',
  },
];

export async function mockGetSamples(): Promise<SampleImage[]> {
  await delay(150);
  return mockSamples;
}

export async function mockGetBenchmark(): Promise<BenchmarkResponse> {
  await delay(150);
  return mockBenchmark;
}

export async function mockGetSegments(): Promise<Segment[]> {
  await delay(200);
  return mockSegments;
}
