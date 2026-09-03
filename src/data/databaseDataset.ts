// ============================================================================
// Ingested Database Dataset & Schema Model
// Corresponds to /database/schema.sql and seed data
// Smart Horizon 48-Hour Hackathon | Team 098 | Topic: DST-1
// Principal Investigators:
//   1. L Steven Dylan
//   2. Karan Sai S
//   3. Kemisetti Hemachandra
//   4. Jeevan M
//   5. Jyotiraditya Pradip Khuman
// (c) 2026 Team 098. All rights reserved. Patent Pending.
// ============================================================================

export const MISSION_CONSORTIUM_SEAL = {
  team: '098',
  topic: 'DST-1',
  investigators: [
    'L Steven Dylan',
    'Karan Sai S',
    'Kemisetti Hemachandra',
    'Jeevan M',
    'Jyotiraditya Pradip Khuman',
  ],
  system: 'ASTRA-7 Autonomous Constellation FDIR & Propellantless Twin',
} as const;

export interface SeedSatellite {
  id: string;
  name: string;
  noradId: number;
  designator: string;
  orbitType: string;
  altitudeKm: number;
  inclinationDeg: number;
  status: 'NOMINAL' | 'PAYLOAD_OPS' | 'COMM_PASS';
  autonomyMode: 'L4_AUTONOMOUS' | 'HITL_SUPERVISED';
  subsystemsCount: number;
  subsystems: Array<{ code: string; name: string; status: string; health: number }>;
}

export interface SeedAction {
  code: string;
  subsystem: string;
  name: string;
  description: string;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  parameters: Record<string, any>;
  isReversible: boolean;
}

export interface SeedSafetyRule {
  code: string;
  name: string;
  subsystem: string;
  condition: string;
  enforcement: 'STRICT_INTERLOCK' | 'WARNING_FLAG';
  description: string;
}

export interface SeedHistoricalIncident {
  caseCode: string;
  orbit: string;
  subsystem: string;
  rootCause: string;
  resolution: string;
  recoveryStrategy: string;
  mttrSeconds: number;
  lessonsLearned: string;
}

export interface SeedScenario {
  scenarioKey: 'SCENARIO_A' | 'SCENARIO_B';
  title: string;
  anomalyType: string;
  anomalyCode: string;
  severity: string;
  triggerMetric: string;
  observedValue: number;
  nominalValue: number;
  unit: string;
  primaryHypothesis: string;
  hypotheses: Array<{ id: string; cause: string; confidence: number }>;
  needsEvidence: boolean;
  recoveryPlan: {
    title: string;
    proposedBy: string;
    riskScore: number;
    actions: Array<{
      order: number;
      actionCode: string;
      parameters: Record<string, any>;
    }>;
  };
}

export const FLEET_SATELLITES: SeedSatellite[] = [
  {
    id: 'a0000000-0000-0000-0000-000000000001',
    name: 'ASTRA-7',
    noradId: 59124,
    designator: '2024-042A',
    orbitType: 'LEO',
    altitudeKm: 541.80,
    inclinationDeg: 97.450,
    status: 'NOMINAL',
    autonomyMode: 'L4_AUTONOMOUS',
    subsystemsCount: 5,
    subsystems: [
      { code: 'EPS', name: 'Electrical Power System & Batteries', status: 'HEALTHY', health: 99.4 },
      { code: 'ADCS', name: 'Attitude Determination & Reaction Wheels', status: 'HEALTHY', health: 98.8 },
      { code: 'PROP', name: 'Hydrazine Thrusters & Monopropellant', status: 'HEALTHY', health: 97.9 },
      { code: 'TCS', name: 'Thermal Control System & Radiators', status: 'HEALTHY', health: 99.1 },
      { code: 'COMMS', name: 'X-Band & S-Band Transceiver Array', status: 'HEALTHY', health: 99.8 },
    ],
  },
  {
    id: 'a0000000-0000-0000-0000-000000000002',
    name: 'ORBIT-GUARD-1',
    noradId: 59125,
    designator: '2024-042B',
    orbitType: 'LEO',
    altitudeKm: 542.10,
    inclinationDeg: 97.450,
    status: 'NOMINAL',
    autonomyMode: 'L4_AUTONOMOUS',
    subsystemsCount: 5,
    subsystems: [
      { code: 'EPS', name: 'Electrical Power System', status: 'HEALTHY', health: 98.5 },
      { code: 'ADCS', name: 'Attitude Control', status: 'HEALTHY', health: 97.4 },
      { code: 'PROP', name: 'Propulsion Subsystem', status: 'HEALTHY', health: 99.0 },
      { code: 'TCS', name: 'Thermal Control', status: 'HEALTHY', health: 98.0 },
      { code: 'PL', name: 'SAR Radar Payload', status: 'HEALTHY', health: 99.5 },
    ],
  },
  {
    id: 'a0000000-0000-0000-0000-000000000003',
    name: 'ORBIT-GUARD-2',
    noradId: 59126,
    designator: '2024-042C',
    orbitType: 'LEO',
    altitudeKm: 540.90,
    inclinationDeg: 97.450,
    status: 'NOMINAL',
    autonomyMode: 'L4_AUTONOMOUS',
    subsystemsCount: 5,
    subsystems: [
      { code: 'EPS', name: 'Electrical Power System', status: 'HEALTHY', health: 99.2 },
      { code: 'ADCS', name: 'Attitude Control', status: 'HEALTHY', health: 98.1 },
      { code: 'PROP', name: 'Propulsion Subsystem', status: 'HEALTHY', health: 98.6 },
      { code: 'TCS', name: 'Thermal Control', status: 'HEALTHY', health: 97.9 },
      { code: 'COMMS', name: 'Swarm Inter-Satellite Link', status: 'HEALTHY', health: 99.9 },
    ],
  },
  {
    id: 'a0000000-0000-0000-0000-000000000004',
    name: 'LEO-SENTINEL-A',
    noradId: 59201,
    designator: '2024-055A',
    orbitType: 'LEO',
    altitudeKm: 545.00,
    inclinationDeg: 97.500,
    status: 'NOMINAL',
    autonomyMode: 'HITL_SUPERVISED',
    subsystemsCount: 5,
    subsystems: [
      { code: 'EPS', name: 'Electrical Power System', status: 'HEALTHY', health: 99.0 },
      { code: 'ADCS', name: 'Attitude Determination', status: 'HEALTHY', health: 99.1 },
      { code: 'PROP', name: 'Orbit Raising Thrusters', status: 'HEALTHY', health: 97.2 },
      { code: 'OBC', name: 'Onboard Computer / FDIR', status: 'HEALTHY', health: 99.7 },
      { code: 'PL', name: 'Multispectral Optical Camera', status: 'HEALTHY', health: 98.4 },
    ],
  },
  {
    id: 'a0000000-0000-0000-0000-000000000005',
    name: 'LEO-SENTINEL-B',
    noradId: 59202,
    designator: '2024-055B',
    orbitType: 'LEO',
    altitudeKm: 544.80,
    inclinationDeg: 97.500,
    status: 'NOMINAL',
    autonomyMode: 'HITL_SUPERVISED',
    subsystemsCount: 5,
    subsystems: [
      { code: 'EPS', name: 'Electrical Power System', status: 'HEALTHY', health: 98.7 },
      { code: 'ADCS', name: 'Attitude Determination', status: 'HEALTHY', health: 98.3 },
      { code: 'TCS', name: 'Active Loop Heat Pipes', status: 'HEALTHY', health: 99.0 },
      { code: 'OBC', name: 'Onboard Computer / FDIR', status: 'HEALTHY', health: 99.6 },
      { code: 'PL', name: 'Hyperspectral Imager', status: 'HEALTHY', health: 99.1 },
    ],
  },
  {
    id: 'a0000000-0000-0000-0000-000000000006',
    name: 'SWARM-RELAY-1',
    noradId: 59310,
    designator: '2024-068A',
    orbitType: 'LEO',
    altitudeKm: 538.50,
    inclinationDeg: 97.400,
    status: 'NOMINAL',
    autonomyMode: 'L4_AUTONOMOUS',
    subsystemsCount: 5,
    subsystems: [
      { code: 'EPS', name: 'Power Distribution Unit', status: 'HEALTHY', health: 99.4 },
      { code: 'ADCS', name: 'Attitude Stabilization', status: 'HEALTHY', health: 98.9 },
      { code: 'COMMS', name: 'Ka-Band Inter-Satellite Link', status: 'HEALTHY', health: 99.5 },
      { code: 'TCS', name: 'Passive Thermal Louvers', status: 'HEALTHY', health: 99.2 },
      { code: 'OBC', name: 'Fault Protection Unit', status: 'HEALTHY', health: 99.8 },
    ],
  },
  {
    id: 'a0000000-0000-0000-0000-000000000007',
    name: 'SWARM-RELAY-2',
    noradId: 59311,
    designator: '2024-068B',
    orbitType: 'LEO',
    altitudeKm: 538.20,
    inclinationDeg: 97.400,
    status: 'NOMINAL',
    autonomyMode: 'L4_AUTONOMOUS',
    subsystemsCount: 5,
    subsystems: [
      { code: 'EPS', name: 'Power Distribution Unit', status: 'HEALTHY', health: 99.5 },
      { code: 'ADCS', name: 'Attitude Stabilization', status: 'HEALTHY', health: 98.7 },
      { code: 'COMMS', name: 'Ka-Band Inter-Satellite Link', status: 'HEALTHY', health: 99.7 },
      { code: 'TCS', name: 'Passive Thermal Louvers', status: 'HEALTHY', health: 99.0 },
      { code: 'OBC', name: 'Fault Protection Unit', status: 'HEALTHY', health: 99.9 },
    ],
  },
];

export const ACTION_CATALOG: SeedAction[] = [
  {
    code: 'EPS_SHED_NON_ESSENTIAL',
    subsystem: 'EPS',
    name: 'Shed Non-Essential Bus Loads',
    description: 'Disconnects secondary payloads and heaters to relieve battery discharge stress.',
    riskLevel: 'LOW',
    parameters: { subsystems: ['PL', 'COMMS_HIGH_PWR'] },
    isReversible: true,
  },
  {
    code: 'EPS_ENABLE_SOLAR_TRACK',
    subsystem: 'EPS',
    name: 'Enable Solar Array Peak Tracking',
    description: 'Orients solar array gimbal drive to normal incidence vector.',
    riskLevel: 'LOW',
    parameters: { tracking_mode: 'MAX_POWER' },
    isReversible: true,
  },
  {
    code: 'PWR_REDUCE_PAYLOAD_DRAIN',
    subsystem: 'EPS',
    name: 'Reduce Payload Power Draw',
    description: 'Throttles high-power optical/radar instruments to standby baseline.',
    riskLevel: 'LOW',
    parameters: { power_reduction_pct: 50 },
    isReversible: true,
  },
  {
    code: 'ADCS_DESATURATE_WHEELS',
    subsystem: 'ADCS',
    name: 'Desaturate Reaction Wheels',
    description: 'Applies magnetic torquer pulses to dump accumulated angular momentum.',
    riskLevel: 'MEDIUM',
    parameters: { target_rpm: 1200, duration_sec: 45 },
    isReversible: true,
  },
  {
    code: 'ADCS_SWITCH_STANDBY_IMU',
    subsystem: 'ADCS',
    name: 'Switch to Standby Inertial Measurement Unit',
    description: 'Isolates degraded primary gyro and transitions attitude filter to IMU-B.',
    riskLevel: 'MEDIUM',
    parameters: { imu_channel: 'IMU_B' },
    isReversible: true,
  },
  {
    code: 'ADCS_ENTER_SUN_POINT',
    subsystem: 'ADCS',
    name: 'Enter Safe Sun-Pointing Attitude',
    description: 'Commands body-axis slew toward solar ephemeris vector for power preservation.',
    riskLevel: 'LOW',
    parameters: { slew_rate_deg_s: 0.5 },
    isReversible: true,
  },
  {
    code: 'TCS_ACTIVATE_SUPPLEMENTAL_HEATER',
    subsystem: 'TCS',
    name: 'Activate Supplemental Radiator Heaters',
    description: 'Energizes survival heater loop during deep eclipse to prevent fuel freezing.',
    riskLevel: 'LOW',
    parameters: { heater_zone: 'HYDRAZINE_MANIFOLD', target_temp_c: 15 },
    isReversible: true,
  },
  {
    code: 'TCS_SLEW_RADIATOR_SHADE',
    subsystem: 'TCS',
    name: 'Slew Radiator Shade Panels',
    description: 'Adjusts reflective thermal louvers to prevent high Earth albedo overheating.',
    riskLevel: 'LOW',
    parameters: { louver_angle_deg: 45 },
    isReversible: true,
  },
  {
    code: 'COMMS_SWITCH_OMNI_ANTENNA',
    subsystem: 'COMMS',
    name: 'Switch to Low-Gain Omni Antenna',
    description: 'Restores omnidirectional beacon in case of high-gain directional pointing loss.',
    riskLevel: 'LOW',
    parameters: { antenna: 'LGA_NADIR' },
    isReversible: true,
  },
  {
    code: 'COMMS_BOOST_TRANSMIT_POWER',
    subsystem: 'COMMS',
    name: 'Boost Downlink RF Amplifier Power',
    description: 'Steps up travelling-wave tube amplifier during critical contingency pass.',
    riskLevel: 'MEDIUM',
    parameters: { power_level_dbm: 33 },
    isReversible: true,
  },
  {
    code: 'PL_POWER_CYCLE_INSTRUMENT',
    subsystem: 'PL',
    name: 'Power Cycle Primary Science Payload',
    description: 'Executes hard power reset to clear latch-up or SEU condition on payload FPGA.',
    riskLevel: 'HIGH',
    parameters: { reboot_delay_sec: 10 },
    isReversible: true,
  },
  {
    code: 'OBC_FLUSH_WATCHDOG_FAULTS',
    subsystem: 'OBC',
    name: 'Clear and Flush Watchdog Fault Counters',
    description: 'Resets non-critical soft fault latches after swarm consensus verification.',
    riskLevel: 'LOW',
    parameters: { counter_mask: '0xFFFF' },
    isReversible: false,
  },
];

export const SAFETY_RULES: SeedSafetyRule[] = [
  {
    code: 'SR-PWR-01',
    name: 'Battery State of Charge Lower Bound',
    subsystem: 'EPS',
    condition: 'battery_soc_pct >= 25.0',
    enforcement: 'STRICT_INTERLOCK',
    description: 'Prevents payload operation if battery charge drops below safe survival threshold.',
  },
  {
    code: 'SR-PWR-02',
    name: 'Maximum Continuous Bus Current',
    subsystem: 'EPS',
    condition: 'bus_current_amps <= 28.0',
    enforcement: 'STRICT_INTERLOCK',
    description: 'Trips fast circuit breakers if total electrical load exceeds wiring rating.',
  },
  {
    code: 'SR-ADCS-01',
    name: 'Maximum Reaction Wheel RPM',
    subsystem: 'ADCS',
    condition: 'reaction_wheel_rpm <= 4800',
    enforcement: 'STRICT_INTERLOCK',
    description: 'Enforces maximum structural spin rate on reaction wheel flywheels to avoid bearing damage.',
  },
  {
    code: 'SR-ADCS-02',
    name: 'Star Tracker Lunar Exclusion Angle',
    subsystem: 'ADCS',
    condition: 'star_tracker_sun_exclusion_deg >= 30.0',
    enforcement: 'WARNING_FLAG',
    description: 'Prevents optical blindings from direct solar or lunar intrusion.',
  },
  {
    code: 'SR-ADCS-03',
    name: 'Maximum Angular Slewing Rate',
    subsystem: 'ADCS',
    condition: 'angular_rate_deg_s <= 3.0',
    enforcement: 'STRICT_INTERLOCK',
    description: 'Limits body slew rates to prevent structural flex excitation in solar arrays.',
  },
  {
    code: 'SR-TCS-01',
    name: 'Battery Cell Temperature Upper Ceiling',
    subsystem: 'TCS',
    condition: 'battery_cell_temp_c <= 45.0',
    enforcement: 'STRICT_INTERLOCK',
    description: 'Commands emergency load shedding if battery thermal runaway condition is threatened.',
  },
  {
    code: 'SR-TCS-02',
    name: 'Propellant Line Minimum Freezing Margin',
    subsystem: 'TCS',
    condition: 'propellant_temp_c >= 5.0',
    enforcement: 'STRICT_INTERLOCK',
    description: 'Requires survival heater engagement before monopropellant reaches solidification point.',
  },
  {
    code: 'SR-PROP-01',
    name: 'Thruster Chamber Overpressure Inhibit',
    subsystem: 'PROP',
    condition: 'chamber_pressure_bar <= 22.0',
    enforcement: 'STRICT_INTERLOCK',
    description: 'Locks out fuel injection valves if manifold pressure spikes above burst margin.',
  },
  {
    code: 'SR-PROP-02',
    name: 'Simultaneous Dual Branch Isolation',
    subsystem: 'PROP',
    condition: 'active_branch_count >= 1',
    enforcement: 'STRICT_INTERLOCK',
    description: 'Prohibits isolating both primary and redundant hydrazine manifold branches concurrently.',
  },
  {
    code: 'SR-COMMS-01',
    name: 'Ground Contact RF Muting During Pyros',
    subsystem: 'COMMS',
    condition: 'rf_silence_flag == FALSE',
    enforcement: 'WARNING_FLAG',
    description: 'Ensures high-gain transmitters do not induce EMI during ordinance or deployable events.',
  },
  {
    code: 'SR-PL-01',
    name: 'Direct Sunlight Instrument Shutter Interlock',
    subsystem: 'PL',
    condition: 'camera_sun_pointing_angle_deg >= 45.0',
    enforcement: 'STRICT_INTERLOCK',
    description: 'Maintains optical baffle doors closed during unfavorable solar aspect angles.',
  },
  {
    code: 'SR-OBC-01',
    name: 'Autonomous Reconfiguration Rate Limiter',
    subsystem: 'OBC',
    condition: 'reconfigs_per_hour <= 3',
    enforcement: 'STRICT_INTERLOCK',
    description: 'Prevents oscillating FDIR loops from cycling power repeatedly within a single orbit.',
  },
];

export const HISTORICAL_ORBIT_CASES: SeedHistoricalIncident[] = [
  {
    caseCode: 'HIST-CASE-01',
    orbit: 'Orbit 1420',
    subsystem: 'TCS',
    rootCause: 'Thermal blanket degradation caused excessive heat leakage in eclipse.',
    resolution: 'Switched to redundant heater line HTR-2 and commanded 4-deg roll offset.',
    recoveryStrategy: 'AUTONOMOUS_L4',
    mttrSeconds: 1.8,
    lessonsLearned: 'Multi-layer insulation requires orbital albedo model correction.',
  },
  {
    caseCode: 'HIST-CASE-02',
    orbit: 'Orbit 2185',
    subsystem: 'ADCS',
    rootCause: 'RW-2 bearing friction spike due to cold soak thermal gradient.',
    resolution: 'Injected 5-pulse oscillatory dithering to redistribute lubricant film.',
    recoveryStrategy: 'AUTONOMOUS_L4',
    mttrSeconds: 3.2,
    lessonsLearned: 'Periodic bearing exercise routine added to orbit sunrise checklist.',
  },
  {
    caseCode: 'HIST-CASE-03',
    orbit: 'Orbit 3042',
    subsystem: 'EPS',
    rootCause: 'Solar array drive slip-ring micro-arcing causing voltage ripple.',
    resolution: 'Adjusted SADA step profile and synchronized clock to bus regulator.',
    recoveryStrategy: 'AUTONOMOUS_L4',
    mttrSeconds: 2.4,
    lessonsLearned: 'Capacitive filtering added in avionics telemetry bridge.',
  },
  {
    caseCode: 'HIST-CASE-04',
    orbit: 'Orbit 4110',
    subsystem: 'PROP',
    rootCause: 'Upper thermosphere density surge caused unexpected 14m perigee drop.',
    resolution: 'Dispatched autonomous two-pulse RCS station-keeping burn (+0.22 m/s).',
    recoveryStrategy: 'AUTONOMOUS_L4',
    mttrSeconds: 4.1,
    lessonsLearned: 'Coupled space weather Kp index feed into orbit predictor.',
  },
  {
    caseCode: 'HIST-CASE-05',
    orbit: 'Orbit 4890',
    subsystem: 'OBC',
    rootCause: 'Single-event upset in star tracker quaternions processing RAM.',
    resolution: 'Swarm consensus quorum rejected bogus attitude quaternion; switched to secondary STR.',
    recoveryStrategy: 'AUTONOMOUS_L4',
    mttrSeconds: 0.65,
    lessonsLearned: 'Implemented triple modular redundancy voting across agent nodes.',
  },
  {
    caseCode: 'HIST-CASE-06',
    orbit: 'Orbit 5214',
    subsystem: 'EPS',
    rootCause: 'Battery cell #4 thermal excursion during high-beta angle sunlight pass.',
    resolution: 'Executed automated load shed and articulated array off-pointing by 8 degrees.',
    recoveryStrategy: 'HITL_APPROVED',
    mttrSeconds: 6.8,
    lessonsLearned: 'Ground control verified safe recovery margin before re-enabling payload.',
  },
  {
    caseCode: 'HIST-CASE-07',
    orbit: 'Orbit 6105',
    subsystem: 'COMMS',
    rootCause: 'Transponder thermal frequency drift causing ground receiver lock loss.',
    resolution: 'Recalibrated local oscillator via onboard temperature lookup table.',
    recoveryStrategy: 'AUTONOMOUS_L4',
    mttrSeconds: 1.4,
    lessonsLearned: 'Oscillator crystal drift model preloaded into agent knowledge base.',
  },
];

export const SCENARIO_DATASETS: Record<'SCENARIO_A' | 'SCENARIO_B', SeedScenario> = {
  SCENARIO_A: {
    scenarioKey: 'SCENARIO_A',
    title: 'SCENARIO A: BATTERY OVERHEAT',
    anomalyType: 'THERMAL_RUNAWAY',
    anomalyCode: 'ANOM-TH-001',
    severity: 'CRITICAL',
    triggerMetric: 'EPS_BATT_TEMP_CELL04',
    observedValue: 48.9,
    nominalValue: 21.2,
    unit: '°C',
    primaryHypothesis: 'Radiator face receiving albedo heat flux causing localized cell #04 thermal runaway',
    hypotheses: [
      { id: 'H1', cause: 'Albedo reflection leak on radiator', confidence: 0.89 },
      { id: 'H2', cause: 'Internal short in battery cell', confidence: 0.11 },
    ],
    needsEvidence: false,
    recoveryPlan: {
      title: 'SCENARIO A Emergency Thermal Mitigation Plan',
      proposedBy: 'Agent Delta::FDIR',
      riskScore: 15.0,
      actions: [
        {
          order: 1,
          actionCode: 'REDUCE_POWER_LOAD',
          parameters: { subsystem: 'PL', shed_percentage: 50, hold_duration_sec: 300 },
        },
        {
          order: 2,
          actionCode: 'TCS_SLEW_RADIATOR_SHADE',
          parameters: { louver_angle_deg: 45 },
        },
      ],
    },
  },
  SCENARIO_B: {
    scenarioKey: 'SCENARIO_B',
    title: 'SCENARIO B: REACTION-WHEEL DEGRADATION',
    anomalyType: 'REACTION_WHEEL_FRICTION',
    anomalyCode: 'ANOM-ADCS-002',
    severity: 'HIGH',
    triggerMetric: 'ADCS_RW2_BEARING_FRICTION_NM',
    observedValue: 0.045,
    nominalValue: 0.005,
    unit: 'N·m',
    primaryHypothesis: 'Reaction wheel RW-2 bearing friction elevation requiring magnetic desaturation',
    hypotheses: [
      { id: 'H1', cause: 'RW-2 lubrication migration due to thermal cold-soak', confidence: 0.94 },
      { id: 'H2', cause: 'Tachometer encoder optical dirt', confidence: 0.06 },
    ],
    needsEvidence: false,
    recoveryPlan: {
      title: 'SCENARIO B Reaction Wheel Desaturation Sequence',
      proposedBy: 'Agent Beta::AOCS',
      riskScore: 5.0,
      actions: [
        {
          order: 1,
          actionCode: 'REDUCE_POWER_LOAD',
          parameters: { subsystem: 'EPS', shed_percentage: 0, note: 'Maintain stable bus during magnetic torquer pulse' },
        },
        {
          order: 2,
          actionCode: 'ADCS_DESATURATE_WHEELS',
          parameters: { target_rpm: 1400, duration_sec: 45 },
        },
      ],
    },
  },
};
