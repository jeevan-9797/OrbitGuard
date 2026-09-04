import React, { useState, useEffect, useRef } from 'react';
import {
  Cpu,
  Radio,
  Network,
  Compass,
  CheckCircle2,
  Loader2,
  Rocket,
  Terminal,
  RotateCcw,
  Sparkles,
  ShieldCheck,
} from 'lucide-react';
import { sound } from '../utils/audio';

export interface StartupRoutineModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface StepLog {
  id: string;
  time: string;
  text: string;
  type: 'info' | 'pass' | 'accent' | 'header';
}

type StepKey = 'avionics' | 'orbitguard' | 'consensus' | 'calibration';

interface StepConfig {
  key: StepKey;
  number: string;
  title: string;
  subtitle: string;
  icon: React.ElementType;
  logs: { text: string; type: 'info' | 'pass' | 'accent' }[];
  durationMs: number;
}

const STARTUP_STEPS: StepConfig[] = [
  {
    key: 'avionics',
    number: '01',
    title: 'Avionics Self-Test',
    subtitle: 'Bus voltage rails, dual OBC memory checksum & register parity',
    icon: Cpu,
    durationMs: 750,
    logs: [
      { text: '[BUS_POWER] Sampling 28.4V unregulated solar bus voltage: NOMINAL (+0.1V margin)', type: 'info' },
      { text: '[OBC_VERIFY] Dual flight computers OBC-1 and OBC-2 memory CRC-32 register check: 0 bitflips', type: 'info' },
      { text: '[BATT_CELLS] LiFePO4 8-cell balancing circuit calibrated. Delta V: 4.2mV', type: 'info' },
      { text: '[AVIONICS_PASS] Core avionics self-test complete. Primary subsystem rails LOCKED.', type: 'pass' },
    ],
  },
  {
    key: 'orbitguard',
    number: '02',
    title: 'OrbitGuard Ping & Small Packet Test',
    subtitle: 'Digital twin telemetry gateway ping & 64-byte diagnostic packet roundtrip',
    icon: Radio,
    durationMs: 800,
    logs: [
      { text: '[PING_INIT] Dispatching diagnostic ICMP ping to OrbitGuard digital twin gateway...', type: 'info' },
      { text: '[TX_PACKET] Transmitting 64-byte aerospace telemetry test frame (SYN-ORION-098)...', type: 'accent' },
      { text: '[RX_REPLY] OrbitGuard payload echo received: RTT = 16.4ms | Jitter: 0.8ms | Packet Loss: 0.0%', type: 'info' },
      { text: '[ORBITGUARD_PASS] OrbitGuard digital twin gateway synchronization CONFIRMED.', type: 'pass' },
    ],
  },
  {
    key: 'consensus',
    number: '03',
    title: 'Agent Consensus Handshake',
    subtitle: 'Raft-BFT swarm agreement across Thermal, AOCS, Propulsion & FDIR',
    icon: Network,
    durationMs: 750,
    logs: [
      { text: '[BFT_INIT] Broadcasting Raft-BFT epoch synchronizer across multi-agent mesh...', type: 'info' },
      { text: '[PEER_ACK] Agent Alpha (Thermal), Agent Beta (AOCS), Agent Gamma (Prop) online.', type: 'info' },
      { text: '[SUPERVISORY] Agent Delta (FDIR) verified Byzantine Fault Tolerance threshold (4/4 nodes).', type: 'accent' },
      { text: '[CONSENSUS_PASS] Multi-agent swarm consensus handshake verified. 4/4 QUORUM ACHIEVED.', type: 'pass' },
    ],
  },
  {
    key: 'calibration',
    number: '04',
    title: 'Calibrate the Sensors',
    subtitle: 'Tri-axial fiber optic gyro zero-bias, Fine Sun Sensor & Star Tracker alignment',
    icon: Compass,
    durationMs: 800,
    logs: [
      { text: '[GYRO_CALIB] Nulling tri-axial Fiber Optic Gyro zero-rate bias (drift < 0.0008 deg/hr).', type: 'info' },
      { text: '[SUN_SENSOR] Normalizing Fine Sun Sensor photodiodes against 1,361 W/m² solar constant.', type: 'info' },
      { text: '[STAR_TRACKER] Aligning quaternion orientation vector against FK6 astronomical catalog.', type: 'accent' },
      { text: '[CALIBRATION_PASS] Sensor suite zero-baseline calibration completed. All telemetry channels LOCKED.', type: 'pass' },
    ],
  },
];

export const StartupRoutineModal: React.FC<StartupRoutineModalProps> = ({ isOpen, onClose }) => {
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [stepStatuses, setStepStatuses] = useState<Record<StepKey, 'pending' | 'running' | 'completed'>>({
    avionics: 'running',
    orbitguard: 'pending',
    consensus: 'pending',
    calibration: 'pending',
  });
  const [logs, setLogs] = useState<StepLog[]>([]);
  const [isAllComplete, setIsAllComplete] = useState<boolean>(false);
  const [startTime] = useState<number>(Date.now());
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  // Run the sequence
  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;

    // Reset sequence state
    setCurrentStepIndex(0);
    setIsAllComplete(false);
    setStepStatuses({
      avionics: 'running',
      orbitguard: 'pending',
      consensus: 'pending',
      calibration: 'pending',
    });

    const initialLog: StepLog = {
      id: 'init-0',
      time: '00:00.00',
      text: '=== ORION PRE-FLIGHT STARTUP SEQUENCE INITIATED ===',
      type: 'header',
    };
    setLogs([initialLog]);

    const runSequence = async () => {
      const getTimestamp = () => {
        const diff = (Date.now() - startTime) / 1000;
        const mins = Math.floor(diff / 60).toString().padStart(2, '0');
        const secs = (diff % 60).toFixed(2).padStart(5, '0');
        return `${mins}:${secs}`;
      };

      for (let i = 0; i < STARTUP_STEPS.length; i++) {
        if (!isMounted) return;
        const step = STARTUP_STEPS[i];

        // Mark step running
        setCurrentStepIndex(i);
        setStepStatuses((prev) => ({
          ...prev,
          [step.key]: 'running',
        }));

        // Push step header log
        setLogs((prev) => [
          ...prev,
          {
            id: `step-hdr-${step.key}`,
            time: getTimestamp(),
            text: `--- PHASE ${step.number}: ${step.title.toUpperCase()} ---`,
            type: 'header',
          },
        ]);

        // Output sub-logs incrementally within the step's duration
        const subInterval = step.durationMs / step.logs.length;
        for (let j = 0; j < step.logs.length; j++) {
          await new Promise((res) => setTimeout(res, subInterval));
          if (!isMounted) return;

          const logItem = step.logs[j];
          sound.playClick();
          setLogs((prev) => [
            ...prev,
            {
              id: `log-${step.key}-${j}`,
              time: getTimestamp(),
              text: logItem.text,
              type: logItem.type,
            },
          ]);
        }

        // Mark step complete
        setStepStatuses((prev) => ({
          ...prev,
          [step.key]: 'completed',
        }));
      }

      if (!isMounted) return;

      // Final readiness log
      await new Promise((res) => setTimeout(res, 200));
      setLogs((prev) => [
        ...prev,
        {
          id: 'ready-pass',
          time: getTimestamp(),
          text: '>>> ALL PRE-FLIGHT VERIFICATIONS NOMINAL: SYSTEM GO FOR FLIGHT <<<',
          type: 'pass',
        },
      ]);
      sound.playRemediated();
      setIsAllComplete(true);
    };

    runSequence();

    return () => {
      isMounted = false;
    };
  }, [isOpen]);

  const handleRestart = () => {
    sound.playClick();
    setCurrentStepIndex(0);
    setIsAllComplete(false);
    setStepStatuses({
      avionics: 'running',
      orbitguard: 'pending',
      consensus: 'pending',
      calibration: 'pending',
    });
    setLogs([
      {
        id: `restart-${Date.now()}`,
        time: '00:00.00',
        text: '=== RESTARTING PRE-FLIGHT STARTUP SEQUENCE ===',
        type: 'header',
      },
    ]);
  };

  const handleLaunchOrion = () => {
    sound.playRemediated();
    onClose();
  };

  if (!isOpen) return null;

  // Completed percentage
  const completedCount = Object.values(stepStatuses).filter((s) => s === 'completed').length;
  const progressPercent = Math.round((completedCount / STARTUP_STEPS.length) * 100);

  return (
    <div
      id="startup-routine-modal"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/85 backdrop-blur-md animate-fade-in"
    >
      <div className="bg-[#0b1120] border border-[#1e293b] w-full max-w-2xl rounded-3xl shadow-2xl flex flex-col overflow-hidden text-slate-100 relative">
        {/* Subtle accent glow */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500 via-emerald-400 to-green-500" />

        {/* Modal Header */}
        <div className="p-5 border-b border-[#1e293b] flex items-center justify-between bg-[#0f172a]/80">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-sm">
              <Rocket size={22} className="animate-pulse" />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="font-display-hero text-base font-bold text-white tracking-wide">
                  ORION STARTUP SEQUENCE
                </span>
                <span className="px-2 py-0.5 rounded-full text-[9px] font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                  SYSTEM BOOT
                </span>
              </div>
              <span className="text-[11px] font-mono text-slate-400">
                Pre-flight autonomous diagnostics & swarm consensus handshake
              </span>
            </div>
          </div>

          {/* Re-run button */}
          <button
            onClick={handleRestart}
            title="Re-run diagnostic sequence"
            className="px-2.5 py-1.5 rounded-xl bg-[#05070a] hover:bg-[#1e293b] border border-[#1e293b] text-slate-400 hover:text-white font-mono text-xs flex items-center gap-1.5 transition-all cursor-pointer"
          >
            <RotateCcw size={12} />
            <span className="hidden sm:inline">RE-RUN</span>
          </button>
        </div>

        {/* 4 Diagnostic Steps Status Cards */}
        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-2.5 bg-[#05070a]/60 border-b border-[#1e293b]">
          {STARTUP_STEPS.map((step, idx) => {
            const status = stepStatuses[step.key];
            const StepIcon = step.icon;
            const isCurrent = currentStepIndex === idx && status === 'running';

            return (
              <div
                key={step.key}
                className={`p-3 rounded-2xl border transition-all flex items-center justify-between gap-3 ${
                  status === 'completed'
                    ? 'bg-[#0f172a]/90 border-emerald-500/40 text-emerald-300'
                    : isCurrent
                    ? 'bg-cyan-950/40 border-cyan-500/50 text-cyan-200 ring-1 ring-cyan-500/30'
                    : 'bg-[#0f172a]/40 border-[#1e293b]/60 text-slate-400 opacity-70'
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <div
                    className={`p-2 rounded-xl border flex-shrink-0 ${
                      status === 'completed'
                        ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400'
                        : isCurrent
                        ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-400'
                        : 'bg-[#1e293b]/40 border-[#1e293b] text-slate-500'
                    }`}
                  >
                    <StepIcon size={16} />
                  </div>
                  <div className="flex flex-col min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] font-mono opacity-70">
                        {step.number}.
                      </span>
                      <span className="text-xs font-semibold truncate text-slate-100">
                        {step.title}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-400 truncate">
                      {status === 'completed'
                        ? 'Verified & Passed'
                        : isCurrent
                        ? 'Running diagnostics...'
                        : 'Standby'}
                    </span>
                  </div>
                </div>

                <div className="flex-shrink-0">
                  {status === 'completed' && (
                    <CheckCircle2 size={18} className="text-emerald-400" />
                  )}
                  {status === 'running' && (
                    <Loader2 size={18} className="text-cyan-400 animate-spin" />
                  )}
                  {status === 'pending' && (
                    <div className="w-4 h-4 rounded-full border border-slate-600/60" />
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Progress Bar */}
        <div className="px-5 pt-3 pb-1 flex items-center justify-between text-xs font-mono">
          <span className="text-slate-400 flex items-center gap-1.5">
            <Terminal size={13} className="text-cyan-400" />
            LIVE TELEMETRY BOOT LOGS
          </span>
          <span
            className={`font-bold ${
              isAllComplete ? 'text-emerald-400' : 'text-cyan-400'
            }`}
          >
            {progressPercent}% COMPLETE
          </span>
        </div>
        <div className="px-5 pb-2">
          <div className="w-full h-1.5 bg-[#1e293b] rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                isAllComplete
                  ? 'bg-gradient-to-r from-emerald-500 to-green-400'
                  : 'bg-gradient-to-r from-cyan-500 to-blue-500'
              }`}
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Terminal Dialog Box */}
        <div className="px-5 pb-4">
          <div
            ref={logContainerRef}
            className="h-44 sm:h-52 bg-[#05070a] border border-[#1e293b] rounded-2xl p-3 font-mono text-[11px] overflow-y-auto flex flex-col gap-1.5 shadow-inner"
          >
            {logs.map((log) => {
              if (log.type === 'header') {
                return (
                  <div
                    key={log.id}
                    className="text-cyan-400/90 font-bold border-t border-b border-[#1e293b]/60 py-0.5 my-0.5"
                  >
                    {log.text}
                  </div>
                );
              }

              return (
                <div
                  key={log.id}
                  className={`flex items-start gap-2 ${
                    log.type === 'pass'
                      ? 'text-emerald-400 font-semibold'
                      : log.type === 'accent'
                      ? 'text-cyan-300'
                      : 'text-slate-300'
                  }`}
                >
                  <span className="text-slate-500 text-[10px] select-none flex-shrink-0">
                    [{log.time}]
                  </span>
                  <span className="break-all">{log.text}</span>
                </div>
              );
            })}
            {!isAllComplete && (
              <div className="flex items-center gap-2 text-cyan-400 animate-pulse text-[10px] pt-1">
                <Loader2 size={11} className="animate-spin" />
                <span>Streaming live telemetry bus diagnostics...</span>
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer / Action Bar */}
        <div className="p-4 bg-[#0f172a] border-t border-[#1e293b] flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-[11px] font-mono text-slate-400">
            <ShieldCheck size={15} className={isAllComplete ? 'text-emerald-400' : 'text-slate-500'} />
            <span>
              {isAllComplete
                ? 'All 4 startup gates passed. Flight authorization granted.'
                : 'Awaiting completion of all 4 startup stages...'}
            </span>
          </div>

          {/* Launch ORION Green Button */}
          {isAllComplete ? (
            <button
              id="launch-orion-btn"
              onClick={handleLaunchOrion}
              className="px-6 py-3 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-black font-display-hero font-extrabold text-sm tracking-wider uppercase flex items-center gap-2.5 transition-all shadow-xl shadow-emerald-500/40 cursor-pointer animate-pulse"
            >
              <Rocket size={18} className="text-black" />
              <span>Launch ORION</span>
              <Sparkles size={16} className="text-black" />
            </button>
          ) : (
            <button
              disabled
              className="px-6 py-3 rounded-2xl bg-[#1e293b]/60 text-slate-500 font-display-hero font-bold text-xs tracking-wider uppercase flex items-center gap-2 cursor-not-allowed border border-[#1e293b]"
            >
              <Loader2 size={14} className="animate-spin" />
              <span>DIAGNOSTICS IN PROGRESS...</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
