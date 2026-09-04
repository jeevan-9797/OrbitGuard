import React, { useState, useEffect, useRef } from 'react';
import {
  HISTORICAL_ORBIT_CASES,
  SAFETY_RULES,
  ACTION_CATALOG,
  FLEET_SATELLITES,
  SeedHistoricalIncident,
} from '../data/databaseDataset';
import { sound } from '../utils/audio';
import {
  Play,
  Pause,
  RotateCcw,
  FastForward,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  Zap,
  Clock,
  Cpu,
  Activity,
  History,
  Terminal,
  Layers,
  ChevronRight,
  Info,
  Radio,
  Compass,
  Flame,
  ArrowRight,
  Sliders,
  Check,
  X,
} from 'lucide-react';

export interface SimCaseConfig {
  id: string;
  caseCode: string;
  orbit: string;
  subsystem: 'ADCS' | 'TCS' | 'PROP' | 'OBC' | 'EPS' | 'COMMS';
  title: string;
  environment: string;
  satelliteName: string;
  noradId: number;
  metricLabel: string;
  metricUnit: string;
  nominalValue: number;
  anomalyPeakValue: number;
  criticalThreshold: number;
  nominalTolerance: number;
  direction: 'higher' | 'lower'; // higher means above threshold is bad, lower means below threshold is bad
  mttrSeconds: number;
  strategy: string;
  safetyRuleCode: string;
  actionCode: string;
  actionParams: Record<string, any>;
  primaryHypothesis: string;
  hypotheses: Array<{ id: string; cause: string; confidence: number }>;
  rootCause: string;
  resolution: string;
  lessonsLearned: string;
}

export const SIMULATION_CASES: SimCaseConfig[] = [
  {
    id: 'case-adcs-rw',
    caseCode: 'HIST-CASE-02',
    orbit: 'Orbit 2185',
    subsystem: 'ADCS',
    title: 'Reaction Wheel RW-2 Bearing Friction & Cold Soak',
    environment: 'Eclipse-to-Sunlight Dawn Thermal Gradient',
    satelliteName: 'ORION',
    noradId: 59124,
    metricLabel: 'RW-2 Motor Current',
    metricUnit: 'A',
    nominalValue: 0.42,
    anomalyPeakValue: 4.85,
    criticalThreshold: 3.2,
    nominalTolerance: 0.1,
    direction: 'higher',
    mttrSeconds: 3.2,
    strategy: 'AUTONOMOUS_L4',
    safetyRuleCode: 'SR-ADCS-01',
    actionCode: 'ADCS_DITHER_RW',
    actionParams: { wheel_id: 'RW-2', dither_freq_hz: 12.5, pulse_count: 5, torque_nm: 0.08 },
    primaryHypothesis: 'Thermal gradient across RW-2 housing caused lubricant viscosity spike and boundary lubrication friction.',
    hypotheses: [
      { id: 'HYP-01', cause: 'Lubricant cold-soak viscosity gradient across RW-2 ball race', confidence: 0.94 },
      { id: 'HYP-02', cause: 'Motor winding phase-to-phase micro short circuit', confidence: 0.04 },
      { id: 'HYP-03', cause: 'Flywheel mechanical debris foreign object intrusion', confidence: 0.02 },
    ],
    rootCause: 'RW-2 bearing friction spike due to cold soak thermal gradient at terminator crossing.',
    resolution: 'Injected 5-pulse oscillatory dithering to redistribute lubricant film across raceway.',
    lessonsLearned: 'Periodic bearing warm-up exercise routine integrated into orbit sunrise event checklist.',
  },
  {
    id: 'case-tcs-blanket',
    caseCode: 'HIST-CASE-01',
    orbit: 'Orbit 1420',
    subsystem: 'TCS',
    title: 'Thermal Blanket MLI Degradation & Eclipse Freeze',
    environment: 'High-Latitude 35-minute Umbra Eclipse Shadow',
    satelliteName: 'ORBIT-GUARD-1',
    noradId: 59125,
    metricLabel: 'Hydrazine Manifold Temp',
    metricUnit: '°C',
    nominalValue: 18.5,
    anomalyPeakValue: -8.2,
    criticalThreshold: 2.0,
    nominalTolerance: 2.0,
    direction: 'lower',
    mttrSeconds: 1.8,
    strategy: 'AUTONOMOUS_L4',
    safetyRuleCode: 'SR-PWR-01',
    actionCode: 'TCS_ACTIVATE_SUPPLEMENTAL_HEATER',
    actionParams: { heater_zone: 'HYDRAZINE_MANIFOLD', target_temp_c: 15, duty_cycle_pct: 85 },
    primaryHypothesis: 'Micrometeoroid perforated multi-layer insulation (MLI) blanket on North radiator panel, causing excessive radiative heat leakage.',
    hypotheses: [
      { id: 'HYP-01', cause: 'MLI radiative thermal insulation breach in deep eclipse shadow', confidence: 0.96 },
      { id: 'HYP-02', cause: 'Primary survival line HTR-1 thermistor circuit open fault', confidence: 0.03 },
      { id: 'HYP-03', cause: 'Propellant line telemetry sensor calibration bias shift', confidence: 0.01 },
    ],
    rootCause: 'Thermal blanket degradation caused excessive heat leakage in eclipse.',
    resolution: 'Switched to redundant heater line HTR-2 and commanded 4-deg roll offset.',
    lessonsLearned: 'Multi-layer insulation requires orbital albedo model correction in onboard thermal mesh.',
  },
  {
    id: 'case-prop-drag',
    caseCode: 'HIST-CASE-04',
    orbit: 'Orbit 4110',
    subsystem: 'PROP',
    title: 'Thermospheric Density Surge & 14m Perigee Loss',
    environment: 'Solar Storm Geomagnetic Kp=8.2 Atmospheric Expansion',
    satelliteName: 'SPECTRA-LEO-3',
    noradId: 59127,
    metricLabel: 'Orbital Perigee Deviation',
    metricUnit: 'm',
    nominalValue: 0.0,
    anomalyPeakValue: -14.2,
    criticalThreshold: -5.0,
    nominalTolerance: 1.0,
    direction: 'lower',
    mttrSeconds: 4.1,
    strategy: 'AUTONOMOUS_L4',
    safetyRuleCode: 'SR-ADCS-03',
    actionCode: 'PROP_STATION_KEEP',
    actionParams: { delta_v_m_s: 0.22, pulse_count: 2, burn_duration_sec: 1.4, manifold: 'RCS_A' },
    primaryHypothesis: 'Solar CME event heated neutral thermosphere, expanding scale height and quadrupling ballistic drag coefficient.',
    hypotheses: [
      { id: 'HYP-01', cause: 'Kp=8.2 atmospheric expansion drag force surge at 540km perigee', confidence: 0.95 },
      { id: 'HYP-02', cause: 'Propellant manifold slow gas venting thruster leak', confidence: 0.03 },
      { id: 'HYP-03', cause: 'GPS navigation receiver carrier phase cycle slip', confidence: 0.02 },
    ],
    rootCause: 'Upper thermosphere density surge caused unexpected 14m perigee drop.',
    resolution: 'Dispatched autonomous two-pulse RCS station-keeping burn (+0.22 m/s).',
    lessonsLearned: 'Coupled real-time space weather Kp index feed directly into onboard orbit predictor.',
  },
  {
    id: 'case-obc-seu',
    caseCode: 'HIST-CASE-05',
    orbit: 'Orbit 4890',
    subsystem: 'OBC',
    title: 'Star Tracker Radiation SEU in South Atlantic Anomaly',
    environment: 'South Atlantic Anomaly (SAA) Trapped Proton Belt',
    satelliteName: 'ORION',
    noradId: 59124,
    metricLabel: 'Attitude Quaternion Norm Error',
    metricUnit: 'ΔQ',
    nominalValue: 1.000,
    anomalyPeakValue: 1.482,
    criticalThreshold: 1.015,
    nominalTolerance: 0.005,
    direction: 'higher',
    mttrSeconds: 0.65,
    strategy: 'AUTONOMOUS_L4',
    safetyRuleCode: 'SR-OBC-01',
    actionCode: 'ADCS_SWITCH_STANDBY_IMU',
    actionParams: { isolate_unit: 'STR-A', active_unit: 'STR-B', reset_watchdog: true },
    primaryHypothesis: 'Trapped radiation proton bit-flip in Star Tracker STR-A attitude quaternion matrix RAM.',
    hypotheses: [
      { id: 'HYP-01', cause: 'Single-Event Upset (SEU) in star identification algorithm RAM buffer', confidence: 0.97 },
      { id: 'HYP-02', cause: 'Optical sensor blinding from stray lunar reflective glint', confidence: 0.02 },
      { id: 'HYP-03', cause: 'Thermal expansion misalignment between star tracker bench and gyro', confidence: 0.01 },
    ],
    rootCause: 'Single-event upset in star tracker quaternions processing RAM.',
    resolution: 'Swarm consensus quorum rejected bogus attitude quaternion; switched to secondary STR-B.',
    lessonsLearned: 'Implemented triple modular redundancy voting across agent nodes.',
  },
  {
    id: 'case-eps-thermal',
    caseCode: 'HIST-CASE-06',
    orbit: 'Orbit 5214',
    subsystem: 'EPS',
    title: 'Battery Cell #4 Thermal Excursion at High Beta Angle',
    environment: 'Seasonal High Solar Beta Angle (β=68°) Continuous Sunlight',
    satelliteName: 'GEO-RELAY-1',
    noradId: 59128,
    metricLabel: 'Battery Cell #4 Temperature',
    metricUnit: '°C',
    nominalValue: 21.5,
    anomalyPeakValue: 56.4,
    criticalThreshold: 45.0,
    nominalTolerance: 3.0,
    direction: 'higher',
    mttrSeconds: 6.8,
    strategy: 'HITL_APPROVED',
    safetyRuleCode: 'SR-PWR-02',
    actionCode: 'PWR_SHED_NONESSENTIAL',
    actionParams: { shed_watts: 180, isolate_payload: true, solar_array_offset_deg: 8.0 },
    primaryHypothesis: 'Continuous solar heating without orbital eclipse cooling cycle triggered thermal accumulation in battery module cell #4.',
    hypotheses: [
      { id: 'HYP-01', cause: 'Internal cell resistance thermal accumulation under high-beta solar geometry', confidence: 0.92 },
      { id: 'HYP-02', cause: 'Charge controller over-current shunt regulator thermal bleed', confidence: 0.06 },
      { id: 'HYP-03', cause: 'Radiator thermal heat-pipe dry-out failure', confidence: 0.02 },
    ],
    rootCause: 'Battery cell #4 thermal excursion during high-beta angle sunlight pass.',
    resolution: 'Executed automated load shed and articulated array off-pointing by 8 degrees.',
    lessonsLearned: 'Ground control verified safe recovery margin before re-enabling payload.',
  },
  {
    id: 'case-comms-drift',
    caseCode: 'HIST-CASE-07',
    orbit: 'Orbit 6105',
    subsystem: 'COMMS',
    title: 'Transponder Local Oscillator Thermal Frequency Drift',
    environment: 'High-Power Downlink Ground Pass Thermal Soak',
    satelliteName: 'POLAR-MET-2',
    noradId: 59126,
    metricLabel: 'Carrier Frequency Offset',
    metricUnit: 'kHz',
    nominalValue: 0.0,
    anomalyPeakValue: 48.2,
    criticalThreshold: 18.0,
    nominalTolerance: 3.0,
    direction: 'higher',
    mttrSeconds: 1.4,
    strategy: 'AUTONOMOUS_L4',
    safetyRuleCode: 'SR-COMMS-01',
    actionCode: 'COMMS_BOOST_TRANSMIT_POWER',
    actionParams: { dac_varactor_counts: 1420, freq_correction_khz: -48.2, power_level_dbm: 33 },
    primaryHypothesis: 'Temperature gradient across RF chassis shifted TCXO local oscillator frequency outside ground receiver tracking window.',
    hypotheses: [
      { id: 'HYP-01', cause: 'Transponder TCXO quartz crystal temperature-frequency curve drift', confidence: 0.96 },
      { id: 'HYP-02', cause: 'Ground tracking antenna Doppler compensation software error', confidence: 0.03 },
      { id: 'HYP-03', cause: 'RF output power amplifier impedance mismatch reflections', confidence: 0.01 },
    ],
    rootCause: 'Transponder thermal frequency drift causing ground receiver lock loss.',
    resolution: 'Recalibrated local oscillator via onboard temperature lookup table.',
    lessonsLearned: 'Oscillator crystal thermal drift lookup matrix preloaded into agent knowledge base.',
  },
];

export const OrbitalCaseSimulatorScreen: React.FC = () => {
  const [selectedCaseId, setSelectedCaseId] = useState<string>('case-adcs-rw');
  const [simTime, setSimTime] = useState<number>(0.0); // 0.0 to 10.0 seconds
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1.0); // 0.5x, 1x, 2x, 4x
  const [isHitlMode, setIsHitlMode] = useState<boolean>(false);
  const [hitlApproved, setHitlApproved] = useState<boolean>(false);
  const [interlockEnforced, setInterlockEnforced] = useState<boolean>(true);

  const activeCase = SIMULATION_CASES.find((c) => c.id === selectedCaseId) || SIMULATION_CASES[0];
  const activeRule = SAFETY_RULES.find((r) => r.code === activeCase.safetyRuleCode) || SAFETY_RULES[0];
  const activeAction = ACTION_CATALOG.find((a) => a.code === activeCase.actionCode) || ACTION_CATALOG[0];

  const requestRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number | null>(null);
  const prevPhaseRef = useRef<string>('NOMINAL');

  // Total simulation window is 10.0 seconds
  const SIM_MAX_TIME = 10.0;
  const ANOMALY_START = 2.0;
  const ANOMALY_PEAK = 3.6;
  const RECOVERY_START = isHitlMode && !hitlApproved ? 7.5 : 5.2;
  const RECOVERY_END = RECOVERY_START + activeCase.mttrSeconds;

  // Determine current flight phase
  let currentPhase: 'NOMINAL' | 'ANOMALY_BREACH' | 'SWARM_REASONING' | 'HITL_WAIT' | 'ACTION_EXEC' | 'RECOVERY_VERIFIED' = 'NOMINAL';
  if (simTime < ANOMALY_START) {
    currentPhase = 'NOMINAL';
  } else if (simTime < ANOMALY_PEAK) {
    currentPhase = 'ANOMALY_BREACH';
  } else if (simTime < RECOVERY_START) {
    if (isHitlMode && !hitlApproved && simTime >= 4.5) {
      currentPhase = 'HITL_WAIT';
    } else {
      currentPhase = 'SWARM_REASONING';
    }
  } else if (simTime < RECOVERY_END) {
    currentPhase = 'ACTION_EXEC';
  } else {
    currentPhase = 'RECOVERY_VERIFIED';
  }

  // Play audio triggers on phase transitions
  useEffect(() => {
    if (prevPhaseRef.current !== currentPhase) {
      if (currentPhase === 'ANOMALY_BREACH') {
        sound.playWarning();
      } else if (currentPhase === 'ACTION_EXEC') {
        if (activeCase.subsystem === 'PROP') {
          sound.playThruster();
        } else {
          sound.playClick();
        }
      } else if (currentPhase === 'RECOVERY_VERIFIED') {
        sound.playRemediated();
      }
      prevPhaseRef.current = currentPhase;
    }
  }, [currentPhase, activeCase.subsystem]);

  // Calculate dynamic telemetry value at simTime
  const calculateMetric = (t: number): number => {
    const nominal = activeCase.nominalValue;
    const peak = activeCase.anomalyPeakValue;
    const noise = Math.sin(t * 12.0) * 0.015 * (Math.abs(peak - nominal) || 1);

    if (t <= ANOMALY_START) {
      return nominal + noise;
    }
    if (t > ANOMALY_START && t <= ANOMALY_PEAK) {
      const progress = (t - ANOMALY_START) / (ANOMALY_PEAK - ANOMALY_START);
      // Smooth cubic curve to peak
      const ease = progress * progress * (3 - 2 * progress);
      return nominal + (peak - nominal) * ease + noise;
    }
    if (t > ANOMALY_PEAK && t <= RECOVERY_START) {
      // Hovering near peak
      const jitter = Math.sin(t * 18.0) * 0.03 * (peak - nominal);
      return peak + jitter;
    }
    if (t > RECOVERY_START && t <= RECOVERY_END) {
      const progress = (t - RECOVERY_START) / (RECOVERY_END - RECOVERY_START);
      // Damped exponential decay back to nominal
      const decay = Math.exp(-progress * 3.5);
      const val = nominal + (peak - nominal) * decay;
      return val + noise * (1 - progress);
    }
    // Fully recovered
    return nominal + noise * 0.5;
  };

  const currentMetricValue = calculateMetric(simTime);

  // Animation Loop
  useEffect(() => {
    const animate = (time: number) => {
      if (lastTimeRef.current !== null && isPlaying) {
        const deltaSeconds = ((time - lastTimeRef.current) / 1000) * playbackSpeed;
        setSimTime((prev) => {
          const next = prev + deltaSeconds;
          if (next >= SIM_MAX_TIME) {
            setIsPlaying(false);
            return SIM_MAX_TIME;
          }
          return next;
        });
      }
      lastTimeRef.current = time;
      if (isPlaying) {
        requestRef.current = requestAnimationFrame(animate);
      }
    };

    if (isPlaying) {
      requestRef.current = requestAnimationFrame(animate);
    }

    return () => {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };
  }, [isPlaying, playbackSpeed, hitlApproved, isHitlMode]);

  const handleTogglePlay = () => {
    sound.playClick();
    if (simTime >= SIM_MAX_TIME) {
      setSimTime(0.0);
    }
    setIsPlaying(!isPlaying);
  };

  const handleReset = () => {
    sound.playClick();
    setIsPlaying(false);
    setSimTime(0.0);
    setHitlApproved(false);
  };

  const handleStep = (direction: 'forward' | 'back') => {
    sound.playClick();
    setIsPlaying(false);
    setSimTime((prev) => {
      const step = direction === 'forward' ? 0.5 : -0.5;
      return Math.min(SIM_MAX_TIME, Math.max(0.0, prev + step));
    });
  };

  const handleSelectCase = (caseId: string) => {
    sound.playClick();
    setSelectedCaseId(caseId);
    setSimTime(0.0);
    setIsPlaying(false);
    setHitlApproved(false);
  };

  const handleApproveHitl = () => {
    sound.playClick();
    setHitlApproved(true);
    if (!isPlaying) {
      setIsPlaying(true);
    }
  };

  // Generate SVG telemetry wave points
  const pointsCount = 100;
  const wavePoints: [number, number][] = [];
  const svgWidth = 600;
  const svgHeight = 160;

  // Min & max for graph scaling
  const minVal = Math.min(activeCase.nominalValue, activeCase.anomalyPeakValue, activeCase.criticalThreshold) * 1.15;
  const maxVal = Math.max(activeCase.nominalValue, activeCase.anomalyPeakValue, activeCase.criticalThreshold) * 1.15;
  const range = maxVal - minVal || 1;

  for (let i = 0; i <= pointsCount; i++) {
    const t = (i / pointsCount) * SIM_MAX_TIME;
    const v = calculateMetric(t);
    const x = (t / SIM_MAX_TIME) * svgWidth;
    const y = svgHeight - ((v - minVal) / range) * (svgHeight - 30) - 15;
    wavePoints.push([x, y]);
  }

  const svgPathData = wavePoints.reduce(
    (acc, curr, idx) => (idx === 0 ? `M ${curr[0]} ${curr[1]}` : `${acc} L ${curr[0]} ${curr[1]}`),
    ''
  );

  const currentX = (simTime / SIM_MAX_TIME) * svgWidth;
  const currentY = svgHeight - ((currentMetricValue - minVal) / range) * (svgHeight - 30) - 15;
  const threshY = svgHeight - ((activeCase.criticalThreshold - minVal) / range) * (svgHeight - 30) - 15;
  const nominalY = svgHeight - ((activeCase.nominalValue - minVal) / range) * (svgHeight - 30) - 15;

  const isMetricCritical =
    activeCase.direction === 'higher'
      ? currentMetricValue >= activeCase.criticalThreshold
      : currentMetricValue <= activeCase.criticalThreshold;

  return (
    <div className="w-full flex flex-col gap-5">
      {/* Top Banner & Control Deck */}
      <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-wrap items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-400">
            <History size={22} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base text-white font-bold tracking-wide font-mono uppercase">
                INGESTED ORBITAL FLIGHT INCIDENT SIMULATOR
              </h2>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-cyan-500/15 text-cyan-300 font-bold border border-cyan-500/30">
                L4 AUTONOMY & REPLAY ENGINE
              </span>
            </div>
            <span className="font-mono text-xs text-slate-400">
              Simulating physics dynamics, AI hypothesis ranking, safety interlocks, and telemetry convergence
            </span>
          </div>
        </div>

        {/* Global Controls */}
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-[#05070a] border border-[#1e293b] rounded-xl p-1 gap-1">
            <button
              onClick={() => handleStep('back')}
              title="Step -0.5s"
              className="px-2 py-1 text-slate-400 hover:text-white text-xs font-mono rounded hover:bg-slate-800 transition-all cursor-pointer"
            >
              -0.5s
            </button>
            <button
              onClick={handleTogglePlay}
              className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 font-mono text-xs font-bold transition-all cursor-pointer ${
                isPlaying
                  ? 'bg-amber-500 text-black shadow-md'
                  : 'bg-cyan-500 text-black hover:bg-cyan-400 shadow-md'
              }`}
            >
              {isPlaying ? <Pause size={14} /> : <Play size={14} />}
              {isPlaying ? 'PAUSE' : 'PLAY SIM'}
            </button>
            <button
              onClick={() => handleStep('forward')}
              title="Step +0.5s"
              className="px-2 py-1 text-slate-400 hover:text-white text-xs font-mono rounded hover:bg-slate-800 transition-all cursor-pointer"
            >
              +0.5s
            </button>
            <button
              onClick={handleReset}
              title="Reset to T=0s"
              className="p-1.5 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition-all cursor-pointer"
            >
              <RotateCcw size={14} />
            </button>
          </div>

          <div className="flex items-center bg-[#05070a] border border-[#1e293b] rounded-xl p-1 font-mono text-xs">
            {[0.5, 1.0, 2.0, 4.0].map((spd) => (
              <button
                key={spd}
                onClick={() => {
                  sound.playClick();
                  setPlaybackSpeed(spd);
                }}
                className={`px-2 py-1 rounded transition-all cursor-pointer ${
                  playbackSpeed === spd
                    ? 'bg-cyan-500 text-black font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {spd}x
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Case Selector Carousel */}
      <div className="flex flex-col gap-2">
        <span className="font-mono text-xs text-slate-400 uppercase font-semibold flex items-center gap-2">
          <Layers size={14} className="text-cyan-400" />
          SELECT INGESTED FLIGHT CASE FOR SIMULATION (DATABASE: historical_incidents)
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-2.5">
          {SIMULATION_CASES.map((item) => {
            const isSelected = item.id === selectedCaseId;
            return (
              <button
                key={item.id}
                onClick={() => handleSelectCase(item.id)}
                className={`p-3 rounded-xl text-left font-mono transition-all cursor-pointer border flex flex-col justify-between gap-2 ${
                  isSelected
                    ? 'bg-cyan-500/10 border-cyan-500 text-white shadow-lg ring-1 ring-cyan-500/50'
                    : 'bg-[#0f172a] border-[#1e293b] text-slate-400 hover:border-slate-700 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-cyan-300">{item.caseCode}</span>
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
                    {item.subsystem}
                  </span>
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-200 line-clamp-1">{item.title}</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">{item.orbit}</div>
                </div>
                <div className="flex items-center justify-between text-[10px] text-emerald-400 font-bold pt-1 border-t border-[#1e293b]">
                  <span>MTTR: {item.mttrSeconds}s</span>
                  <span className={item.strategy.includes('L4') ? 'text-cyan-400' : 'text-amber-400'}>
                    {item.strategy.replace('_', ' ')}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Simulation Viewport Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column: Dynamics, Oscilloscope & Visual Satellite (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-4">
          {/* Active Case Meta Card */}
          <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col gap-3 shadow-lg">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1e293b] pb-2.5">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm font-bold text-white">{activeCase.title}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-500/20 text-cyan-300 font-bold">
                    {activeCase.caseCode}
                  </span>
                </div>
                <span className="font-mono text-xs text-slate-400">
                  Target: <strong>{activeCase.satelliteName}</strong> (NORAD #{activeCase.noradId}) | Subsystem:{' '}
                  <strong>{activeCase.subsystem}</strong> | {activeCase.environment}
                </span>
              </div>
              <div className="flex items-center gap-2 font-mono text-xs">
                <span className="text-slate-400">Time:</span>
                <span className="text-base font-bold text-cyan-300 bg-[#05070a] px-2.5 py-1 rounded border border-[#1e293b]">
                  T +{simTime.toFixed(2)}s
                </span>
              </div>
            </div>

            {/* Timeline Scrubber */}
            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between font-mono text-[11px] text-slate-400">
                <span>0.0s (Nominal)</span>
                <span>2.0s (Onset)</span>
                <span>{RECOVERY_START.toFixed(1)}s (Dispatch)</span>
                <span>{RECOVERY_END.toFixed(1)}s (Verified)</span>
                <span>10.0s (Safe)</span>
              </div>
              <input
                type="range"
                min="0"
                max={SIM_MAX_TIME}
                step="0.05"
                value={simTime}
                onChange={(e) => {
                  setSimTime(parseFloat(e.target.value));
                  setIsPlaying(false);
                }}
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
              />
            </div>

            {/* Phase Status Banner */}
            <div
              className={`p-3 rounded-xl font-mono text-xs flex items-center justify-between border ${
                currentPhase === 'NOMINAL'
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  : currentPhase === 'ANOMALY_BREACH'
                  ? 'bg-rose-500/15 border-rose-500/40 text-rose-300 animate-pulse'
                  : currentPhase === 'SWARM_REASONING'
                  ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                  : currentPhase === 'HITL_WAIT'
                  ? 'bg-purple-500/20 border-purple-500/40 text-purple-200 animate-pulse'
                  : currentPhase === 'ACTION_EXEC'
                  ? 'bg-cyan-500/15 border-cyan-500/40 text-cyan-300'
                  : 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300'
              }`}
            >
              <div className="flex items-center gap-2">
                {currentPhase === 'NOMINAL' && <CheckCircle2 size={16} />}
                {currentPhase === 'ANOMALY_BREACH' && <AlertTriangle size={16} />}
                {currentPhase === 'SWARM_REASONING' && <Cpu size={16} />}
                {currentPhase === 'HITL_WAIT' && <Clock size={16} />}
                {currentPhase === 'ACTION_EXEC' && <Zap size={16} />}
                {currentPhase === 'RECOVERY_VERIFIED' && <ShieldCheck size={16} />}
                <span className="font-bold">
                  PHASE:{' '}
                  {currentPhase === 'NOMINAL'
                    ? 'STEADY NOMINAL STATE'
                    : currentPhase === 'ANOMALY_BREACH'
                    ? 'ANOMALY ONSET & TELEMETRY BREACH'
                    : currentPhase === 'SWARM_REASONING'
                    ? 'SWARM CONSENSUS & HYPOTHESIS ISOLATION'
                    : currentPhase === 'HITL_WAIT'
                    ? 'GROUND CONTROLLER AUTHORIZATION REQUIRED'
                    : currentPhase === 'ACTION_EXEC'
                    ? `DISPATCHING [${activeCase.actionCode}]`
                    : `NOMINAL ENVELOPE RESTORED (MTTR: ${activeCase.mttrSeconds}s)`}
                </span>
              </div>

              {currentPhase === 'HITL_WAIT' && (
                <button
                  onClick={handleApproveHitl}
                  className="px-3 py-1 rounded bg-purple-500 hover:bg-purple-400 text-black font-bold text-xs transition-all cursor-pointer shadow-md"
                >
                  AUTHORIZE DISPATCH
                </button>
              )}
            </div>
          </div>

          {/* Oscilloscope SVG Waveform */}
          <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col gap-3 shadow-lg">
            <div className="flex items-center justify-between font-mono">
              <div>
                <span className="text-xs text-slate-400 uppercase font-bold">
                  High-Rate Telemetry Stream: {activeCase.metricLabel}
                </span>
                <div className="flex items-center gap-3 mt-0.5 text-xs">
                  <span className="text-slate-300">
                    Current:{' '}
                    <strong
                      className={
                        isMetricCritical
                          ? 'text-rose-400 text-sm font-bold'
                          : 'text-cyan-300 text-sm font-bold'
                      }
                    >
                      {currentMetricValue.toFixed(3)} {activeCase.metricUnit}
                    </strong>
                  </span>
                  <span className="text-slate-400">
                    Nominal: {activeCase.nominalValue.toFixed(2)} {activeCase.metricUnit}
                  </span>
                  <span className="text-rose-400/80">
                    Limit: {activeCase.criticalThreshold.toFixed(2)} {activeCase.metricUnit}
                  </span>
                </div>
              </div>

              <div className="text-right text-[11px] font-mono text-slate-400">
                <span>Sampling: 10 Hz</span>
                <span className="block text-emerald-400">B-Tree Indexed</span>
              </div>
            </div>

            {/* SVG Graph Canvas */}
            <div className="relative w-full h-[180px] bg-[#05070a] border border-[#1e293b] rounded-xl overflow-hidden p-2">
              <svg
                viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                className="w-full h-full overflow-visible"
                preserveAspectRatio="none"
              >
                {/* Background Grid Lines */}
                <line x1="0" y1={svgHeight * 0.25} x2={svgWidth} y2={svgHeight * 0.25} stroke="#1e293b" strokeDasharray="3 3" />
                <line x1="0" y1={svgHeight * 0.5} x2={svgWidth} y2={svgHeight * 0.5} stroke="#1e293b" strokeDasharray="3 3" />
                <line x1="0" y1={svgHeight * 0.75} x2={svgWidth} y2={svgHeight * 0.75} stroke="#1e293b" strokeDasharray="3 3" />

                {/* Vertical Phase Marker Lines */}
                <line
                  x1={(ANOMALY_START / SIM_MAX_TIME) * svgWidth}
                  y1="0"
                  x2={(ANOMALY_START / SIM_MAX_TIME) * svgWidth}
                  y2={svgHeight}
                  stroke="#ef4444"
                  strokeWidth="1"
                  strokeDasharray="2 2"
                  opacity="0.6"
                />
                <line
                  x1={(RECOVERY_START / SIM_MAX_TIME) * svgWidth}
                  y1="0"
                  x2={(RECOVERY_START / SIM_MAX_TIME) * svgWidth}
                  y2={svgHeight}
                  stroke="#06b6d4"
                  strokeWidth="1"
                  strokeDasharray="2 2"
                  opacity="0.6"
                />

                {/* Critical Threshold Line */}
                <line
                  x1="0"
                  y1={threshY}
                  x2={svgWidth}
                  y2={threshY}
                  stroke="#f43f5e"
                  strokeWidth="1.5"
                  strokeDasharray="4 4"
                />

                {/* Nominal Target Line */}
                <line
                  x1="0"
                  y1={nominalY}
                  x2={svgWidth}
                  y2={nominalY}
                  stroke="#10b981"
                  strokeWidth="1"
                  strokeDasharray="2 2"
                  opacity="0.7"
                />

                {/* Continuous Telemetry Path */}
                <path
                  d={svgPathData}
                  fill="none"
                  stroke={isMetricCritical ? '#f43f5e' : '#06b6d4'}
                  strokeWidth="2"
                  className="transition-colors duration-200"
                />

                {/* Progress Needle & Active Ball */}
                <line
                  x1={currentX}
                  y1="0"
                  x2={currentX}
                  y2={svgHeight}
                  stroke="#38bdf8"
                  strokeWidth="2"
                />
                <circle
                  cx={currentX}
                  cy={currentY}
                  r="5"
                  fill={isMetricCritical ? '#f43f5e' : '#06b6d4'}
                  stroke="#ffffff"
                  strokeWidth="1.5"
                  className="animate-pulse"
                />
              </svg>

              {/* Graphical Legends overlay */}
              <div className="absolute top-2 left-3 font-mono text-[10px] text-rose-400 bg-[#05070a]/80 px-2 py-0.5 rounded border border-rose-500/20">
                --- CRITICAL THRESHOLD ({activeCase.criticalThreshold} {activeCase.metricUnit})
              </div>
              <div className="absolute bottom-2 left-3 font-mono text-[10px] text-emerald-400 bg-[#05070a]/80 px-2 py-0.5 rounded border border-emerald-500/20">
                --- NOMINAL BASELINE ({activeCase.nominalValue} {activeCase.metricUnit})
              </div>
            </div>
          </div>

          {/* Subsystem & Spacecraft Animated Schematic */}
          <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col gap-3 shadow-lg">
            <div className="flex items-center justify-between font-mono text-xs border-b border-[#1e293b] pb-2">
              <span className="text-white font-bold flex items-center gap-1.5">
                <Compass size={15} className="text-cyan-400" />
                ON-ORBIT SUBSYSTEM STATE & ATTITUDE VISUALIZER
              </span>
              <span className="text-slate-400">
                Orbit: {activeCase.orbit} // Subsystem: {activeCase.subsystem}
              </span>
            </div>

            {/* Dynamic Spacecraft SVG Schematic */}
            <div className="relative w-full h-[200px] bg-[#05070a] border border-[#1e293b] rounded-xl flex items-center justify-center p-4 overflow-hidden">
              <svg viewBox="0 0 400 200" className="w-full h-full max-w-[460px]">
                <defs>
                  <linearGradient id="solarGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#0284c7" />
                    <stop offset="100%" stopColor="#0369a1" />
                  </linearGradient>
                  <radialGradient id="frictionGlow" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="#ef4444" stopOpacity="0.9" />
                    <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
                  </radialGradient>
                  <radialGradient id="heaterGlow" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="#f97316" stopOpacity="0.8" />
                    <stop offset="100%" stopColor="#f97316" stopOpacity="0" />
                  </radialGradient>
                </defs>

                {/* Solar Arrays Left & Right */}
                <rect x="40" y="70" width="90" height="60" rx="3" fill="url(#solarGrad)" stroke="#38bdf8" strokeWidth="1" />
                <line x1="70" y1="70" x2="70" y2="130" stroke="#0ea5e9" strokeWidth="1" />
                <line x1="100" y1="70" x2="100" y2="130" stroke="#0ea5e9" strokeWidth="1" />
                <line x1="40" y1="100" x2="130" y2="100" stroke="#0ea5e9" strokeWidth="1" />

                <rect x="270" y="70" width="90" height="60" rx="3" fill="url(#solarGrad)" stroke="#38bdf8" strokeWidth="1" />
                <line x1="300" y1="70" x2="300" y2="130" stroke="#0ea5e9" strokeWidth="1" />
                <line x1="330" y1="70" x2="330" y2="130" stroke="#0ea5e9" strokeWidth="1" />
                <line x1="270" y1="100" x2="360" y2="100" stroke="#0ea5e9" strokeWidth="1" />

                {/* Array Booms */}
                <line x1="130" y1="100" x2="160" y2="100" stroke="#94a3b8" strokeWidth="3" />
                <line x1="240" y1="100" x2="270" y2="100" stroke="#94a3b8" strokeWidth="3" />

                {/* Satellite Bus Chassis */}
                <rect x="160" y="60" width="80" height="80" rx="6" fill="#1e293b" stroke="#475569" strokeWidth="2" />

                {/* Nadir Payload Antenna / Dish */}
                <path d="M 200 140 L 200 165" stroke="#94a3b8" strokeWidth="2" />
                <path d="M 185 165 Q 200 180 215 165" stroke="#38bdf8" strokeWidth="2" fill="none" />

                {/* ADCS RW-2 Reaction Wheel Indicator */}
                <circle cx="200" cy="100" r="22" fill="#0f172a" stroke="#64748b" strokeWidth="2" />
                <circle
                  cx="200"
                  cy="100"
                  r="14"
                  fill={activeCase.subsystem === 'ADCS' && isMetricCritical ? '#ef4444' : '#0284c7'}
                  className={isPlaying ? 'animate-spin' : ''}
                  style={{ animationDuration: isMetricCritical ? '0.2s' : '1.2s' }}
                />

                {/* Subsystem Anomaly Dynamic Highlights */}
                {activeCase.subsystem === 'ADCS' && isMetricCritical && (
                  <circle cx="200" cy="100" r="32" fill="url(#frictionGlow)" className="animate-pulse" />
                )}

                {activeCase.subsystem === 'TCS' && (
                  <rect
                    x="165"
                    y="65"
                    width="70"
                    height="70"
                    rx="4"
                    fill={currentPhase === 'ACTION_EXEC' || currentPhase === 'RECOVERY_VERIFIED' ? 'url(#heaterGlow)' : '#38bdf8'}
                    fillOpacity={isMetricCritical ? '0.3' : '0.1'}
                    stroke={currentPhase === 'ACTION_EXEC' ? '#f97316' : '#38bdf8'}
                    strokeWidth="2"
                    strokeDasharray={isMetricCritical ? '4 2' : 'none'}
                  />
                )}

                {activeCase.subsystem === 'PROP' && currentPhase === 'ACTION_EXEC' && (
                  <>
                    <polygon points="150,100 135,92 135,108" fill="#38bdf8" className="animate-pulse" />
                    <polygon points="250,100 265,92 265,108" fill="#38bdf8" className="animate-pulse" />
                  </>
                )}

                {activeCase.subsystem === 'COMMS' && (
                  <circle
                    cx="200"
                    cy="165"
                    r={isMetricCritical ? 18 : 12}
                    fill="none"
                    stroke={isMetricCritical ? '#ef4444' : '#06b6d4'}
                    strokeWidth="1.5"
                    strokeDasharray="3 3"
                    className="animate-ping"
                  />
                )}
              </svg>

              {/* Subsystem State Label Badge */}
              <div className="absolute bottom-2 right-2 bg-[#0a1120]/90 border border-[#1e293b] px-2.5 py-1 rounded-lg font-mono text-[10px] flex items-center gap-1.5">
                <span className="text-slate-400">Component:</span>
                <span className="text-cyan-300 font-bold">{activeCase.actionParams.wheel_id || activeCase.subsystem}</span>
                <span className="text-slate-400">|</span>
                <span className={isMetricCritical ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold'}>
                  {isMetricCritical ? 'FAULT STATE' : 'NOMINAL OP'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: AI Swarm Deliberation & Ingested Database Contracts (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          {/* Swarm AI Contract 1: Hypothesis Generation */}
          <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col gap-3 shadow-lg">
            <div className="flex items-center justify-between border-b border-[#1e293b] pb-2">
              <span className="font-mono text-xs font-bold text-white flex items-center gap-1.5">
                <Cpu size={15} className="text-cyan-400" />
                AI CONTRACT: agent_runs.output
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-500/15 text-cyan-300 font-bold">
                SWARM CONSENSUS
              </span>
            </div>

            <div className="p-3 rounded-xl bg-[#05070a] border border-[#1e293b] flex flex-col gap-2 font-mono text-xs">
              <div className="flex items-center justify-between text-slate-400 text-[11px]">
                <span>Status: {simTime >= ANOMALY_PEAK ? 'DIAGNOSTIC QUORUM REACHED' : 'MONITORING'}</span>
                <span className="text-cyan-300">Confidence: {(activeCase.hypotheses[0].confidence * 100).toFixed(0)}%</span>
              </div>

              <div>
                <span className="text-slate-400 text-[10px] uppercase font-bold block">Primary Hypothesis</span>
                <p className="text-cyan-200 text-xs mt-0.5 leading-relaxed bg-[#0b1120] p-2.5 rounded-lg border border-cyan-500/20">
                  "{activeCase.primaryHypothesis}"
                </p>
              </div>

              <div className="flex flex-col gap-1 mt-1">
                <span className="text-slate-400 text-[10px] uppercase font-bold">Hypothesis Ranking Matrix:</span>
                {activeCase.hypotheses.map((hyp) => (
                  <div key={hyp.id} className="flex flex-col gap-0.5 bg-[#0b1120] p-2 rounded border border-[#1e293b]">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-slate-300 font-medium truncate max-w-[220px]">{hyp.cause}</span>
                      <span className="font-bold text-cyan-300">{(hyp.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden mt-0.5">
                      <div
                        className="h-full bg-cyan-400 transition-all duration-300"
                        style={{ width: `${hyp.confidence * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Swarm AI Contract 2: Safety Interlock Validation */}
          <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col gap-3 shadow-lg">
            <div className="flex items-center justify-between border-b border-[#1e293b] pb-2">
              <span className="font-mono text-xs font-bold text-white flex items-center gap-1.5">
                <ShieldCheck size={15} className="text-emerald-400" />
                SAFETY INTERLOCK: safety_rules
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/15 text-emerald-300 font-bold">
                {activeRule.enforcement}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-[#05070a] border border-[#1e293b] flex flex-col gap-2 font-mono text-xs">
              <div className="flex items-center justify-between">
                <span className="text-emerald-300 font-bold">{activeRule.code}: {activeRule.name}</span>
                <span className="text-slate-400 text-[10px]">{activeRule.subsystem}</span>
              </div>

              <div className="p-2 rounded bg-[#0b1120] border border-[#1e293b] text-cyan-300 text-xs">
                <code>CONDITION: {activeRule.condition}</code>
              </div>

              <div className="flex items-center justify-between pt-1 border-t border-[#1e293b] text-[11px]">
                <span className="text-slate-400">Interlock Check:</span>
                <span className="text-emerald-400 font-bold flex items-center gap-1">
                  <CheckCircle2 size={12} />
                  PRE-CONDITION MET (DISPATCH SAFE)
                </span>
              </div>
            </div>
          </div>

          {/* Swarm AI Contract 3: Recovery Plan Action Dispatch */}
          <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col gap-3 shadow-lg">
            <div className="flex items-center justify-between border-b border-[#1e293b] pb-2">
              <span className="font-mono text-xs font-bold text-white flex items-center gap-1.5">
                <Zap size={15} className="text-amber-400" />
                RECOVERY ACTION: recovery_plans.actions
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/15 text-amber-300 font-bold">
                {activeAction.riskLevel} RISK
              </span>
            </div>

            <div className="p-3 rounded-xl bg-[#05070a] border border-[#1e293b] flex flex-col gap-2 font-mono text-xs">
              <div className="flex items-center justify-between">
                <span className="text-cyan-300 font-bold">{activeAction.code}</span>
                <span className={activeAction.isReversible ? 'text-emerald-400 text-[10px]' : 'text-amber-400 text-[10px]'}>
                  {activeAction.isReversible ? '✓ Reversible' : '⚠ Non-Reversible'}
                </span>
              </div>
              <p className="text-slate-300 text-[11px] leading-relaxed">{activeAction.description}</p>

              <div>
                <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">
                  Dispatched Parameters (JSON payload):
                </span>
                <pre className="p-2 rounded bg-[#0b1120] border border-[#1e293b] text-[11px] text-amber-300 overflow-x-auto">
                  {JSON.stringify(activeCase.actionParams, null, 2)}
                </pre>
              </div>
            </div>
          </div>

          {/* Case History & Lessons Learned */}
          <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col gap-3 shadow-lg">
            <div className="flex items-center justify-between border-b border-[#1e293b] pb-2">
              <span className="font-mono text-xs font-bold text-white flex items-center gap-1.5">
                <Info size={15} className="text-slate-400" />
                FLIGHT CASE LESSONS & RESOLUTION
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300">
                DATABASE: historical_incidents
              </span>
            </div>

            <div className="flex flex-col gap-2 text-xs font-mono">
              <div className="bg-[#05070a] p-2.5 rounded-xl border border-[#1e293b]">
                <span className="text-slate-400 text-[10px] uppercase font-bold block">Resolution Dispatched:</span>
                <p className="text-slate-200 text-xs mt-0.5">{activeCase.resolution}</p>
              </div>

              <div className="bg-[#05070a] p-2.5 rounded-xl border border-[#1e293b]">
                <span className="text-amber-400 text-[10px] uppercase font-bold block">Operational Lesson Learned:</span>
                <p className="text-amber-200/90 text-xs mt-0.5">{activeCase.lessonsLearned}</p>
              </div>

              <div className="flex items-center justify-between pt-1 text-[11px] text-slate-400">
                <span>Database Audit MTTR: <strong className="text-emerald-400">{activeCase.mttrSeconds}s</strong></span>
                <span>Strategy: <strong className="text-cyan-300">{activeCase.strategy}</strong></span>
              </div>
            </div>
          </div>

          {/* "What-If" Human Flight Controller Experimentation Controls */}
          <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col gap-3 shadow-lg">
            <span className="font-mono text-xs font-bold text-white flex items-center gap-1.5 border-b border-[#1e293b] pb-2">
              <Sliders size={15} className="text-cyan-400" />
              FLIGHT CONTROLLER "WHAT-IF" EXPERIMENTATION
            </span>

            <div className="flex flex-col gap-2 font-mono text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#05070a] border border-[#1e293b]">
                <div>
                  <span className="font-bold text-slate-200 block">Supervisor Mode</span>
                  <span className="text-[10px] text-slate-400">
                    {isHitlMode ? 'HITL (Manual ground confirmation required)' : 'Autonomous L4 (Immediate on-orbit dispatch)'}
                  </span>
                </div>
                <button
                  onClick={() => {
                    sound.playClick();
                    setIsHitlMode(!isHitlMode);
                    setHitlApproved(false);
                  }}
                  className={`px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                    isHitlMode
                      ? 'bg-purple-500 text-black shadow-md'
                      : 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  }`}
                >
                  {isHitlMode ? 'HITL MODE' : 'L4 AUTO'}
                </button>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#05070a] border border-[#1e293b]">
                <div>
                  <span className="font-bold text-slate-200 block">Safety Interlock Enforcement</span>
                  <span className="text-[10px] text-slate-400">
                    {interlockEnforced ? 'Rules strictly verified before commanding' : 'Interlock checks bypassed (Risk testing)'}
                  </span>
                </div>
                <button
                  onClick={() => {
                    sound.playClick();
                    setInterlockEnforced(!interlockEnforced);
                  }}
                  className={`px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                    interlockEnforced
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      : 'bg-rose-500 text-white shadow-md'
                  }`}
                >
                  {interlockEnforced ? 'STRICT [ON]' : 'BYPASS [OFF]'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
