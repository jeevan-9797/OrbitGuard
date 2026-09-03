export type ActiveScreen = 'orbital-twin' | 'agent-mesh' | 'anomaly-lab' | 'analytics';

export type AutonomyMode = 'L4' | 'HITL' | 'OVERRIDE';

export type HITLThreshold = 'strict' | 'standard' | 'autonomous';

export type TwinLayer = 'wireframe' | 'thermal' | 'mag' | 'power';

export interface AnomalyPreset {
  id: string;
  presetNum: string;
  subsystem: string;
  title: string;
  description: string;
  severityDefault: number;
  severityLabel: string;
  detectionTime: number; // in seconds
  mitigationTime: number;
  recoveryTime: number;
  baselineMetric: string;
  faultMetric: string;
  remediatedMetric: string;
  deltaSummary: string;
  telemetryChannel: string;
  journalLogs: {
    time: string;
    agent: string;
    tag: string;
    tagColor: string;
    message: string;
  }[];
}

export interface CoTLogEntry {
  id: string;
  timestamp: string;
  agent: string;
  tag: string;
  tagColor: string;
  message: string;
}

export interface InterventionLedgerItem {
  id: string;
  timestamp: string;
  leadAgent: string;
  actionExecuted: string;
  resolutionTime: string;
  telemetryDelta: string;
  reverted?: boolean;
}

export interface TelemetryIncident {
  id: string;
  subsystem: string;
  type: 'REAL' | 'CHAOS';
  triggerRoot: string;
  responseTime: string;
  remediator: string;
  status: 'RESOLVED' | 'ACTIVE' | 'MITIGATING';
}

export interface HistoricalIncident {
  id: string;
  timestamp: string;
  subsystem: string;
  description: string;
  autonomyLevel: string;
  mttrSeconds: number;
  outcome: string;
}

export interface AgentStatus {
  id: 'alpha' | 'beta' | 'gamma' | 'delta';
  name: string;
  subsystem: string;
  role: string;
  state: 'nominal' | 'active_correction' | 'balancing' | 'standby' | 'isolated' | 'faulted';
  isolated: boolean;
  confidence: number;
  description: string;
}

export interface ManualPulseEvent {
  id: string;
  timestamp: number;
  timeStr: string;
  thruster: string;
  durationMs: number;
  deltaV: number;
  deltaAltMeters: number;
  angularRateDeg: number;
  fuelGrams: number;
}
