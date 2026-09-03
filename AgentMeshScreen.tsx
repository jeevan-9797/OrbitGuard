import React, { useState, useEffect } from 'react';
import { AgentStatus, AutonomyMode, HITLThreshold, CoTLogEntry, InterventionLedgerItem, ManualPulseEvent } from '../types';
import { INITIAL_LEDGER_ITEMS } from '../data/mockFlightData';
import { sound } from '../utils/audio';
import { PulseTrajectoryGraph } from './PulseTrajectoryGraph';
import {
  Cpu,
  ShieldAlert,
  ShieldCheck,
  Zap,
  SlidersHorizontal,
  Flame,
  Power,
  RotateCw,
  Send,
  Pause,
  Play,
  Trash2,
  Lock,
  Unlock,
} from 'lucide-react';

interface AgentMeshScreenProps {
  agents: AgentStatus[];
  onToggleAgentIsolation: (agentId: string) => void;
  autonomyMode: AutonomyMode;
  onChangeAutonomyMode: (mode: AutonomyMode) => void;
}

export const AgentMeshScreen: React.FC<AgentMeshScreenProps> = ({
  agents,
  onToggleAgentIsolation,
  autonomyMode,
  onChangeAutonomyMode,
}) => {
  const [hitlThreshold, setHitlThreshold] = useState<HITLThreshold>('standard');
  const [selectedAgentNode, setSelectedAgentNode] = useState<string>('alpha');

  // CoT Live Stream
  const [cotLogs, setCotLogs] = useState<CoTLogEntry[]>([
    {
      id: 'cot-1',
      timestamp: '14:02:11.60',
      agent: 'Agent Alpha::Thermal',
      tag: 'OBSERVE',
      tagColor: 'bg-primary/20 text-primary',
      message: 'Monitoring battery pack cell #04 temperature gradient (+0.4°C/min inflection).',
    },
    {
      id: 'cot-2',
      timestamp: '14:02:11.64',
      agent: 'Agent Beta::AOCS',
      tag: 'CROSS-CHECK',
      tagColor: 'bg-primary-fixed/20 text-primary-fixed',
      message: 'Attitude vector allows +4.2° roll offset without obscuring primary star-tracker boresight.',
    },
    {
      id: 'cot-3',
      timestamp: '14:02:11.72',
      agent: 'SWARM_BFT',
      tag: 'CONSENSUS',
      tagColor: 'bg-secondary/20 text-secondary',
      message: 'Multi-agent vote unanimous: Execute micro-slew to shade radiator face. Latency 8.2ms.',
    },
    {
      id: 'cot-4',
      timestamp: '14:02:11.80',
      agent: 'Agent Beta::AOCS',
      tag: 'DISPATCH',
      tagColor: 'bg-primary text-on-primary',
      message: 'Torque pulse dispatched to RW-2 (+0.04 N·m). Stabilizing in 1.8 seconds.',
    },
  ]);

  const [streamPaused, setStreamPaused] = useState<boolean>(false);
  const [replInput, setReplInput] = useState<string>('');
  const [activeFilter, setActiveFilter] = useState<string>('ALL');

  // Ledger items
  const [ledgerItems, setLedgerItems] = useState<InterventionLedgerItem[]>(INITIAL_LEDGER_ITEMS);

  // Manual Override Deck State
  const [safetyInterlockArmed, setSafetyInterlockArmed] = useState<boolean>(false);
  const [selectedRcsThruster, setSelectedRcsThruster] = useState<string>('+X');
  const [rcsPulseDuration, setRcsPulseDuration] = useState<number>(100);
  const [heaterPwm, setHeaterPwm] = useState<number>(35);
  const [rcsStatusMsg, setRcsStatusMsg] = useState<string>('');
  const [mcrSeized, setMcrSeized] = useState<boolean>(autonomyMode === 'OVERRIDE');

  // Manual Pulses State for Live Trajectory Tracking
  const [manualPulses, setManualPulses] = useState<ManualPulseEvent[]>([
    {
      id: 'pulse-init-1',
      timestamp: 4.2,
      timeStr: '14:01:48.20',
      thruster: '+X',
      durationMs: 100,
      deltaV: 0.032,
      deltaAltMeters: 280,
      angularRateDeg: 0,
      fuelGrams: 4.2,
    },
  ]);

  // Simulate ongoing live CoT stream
  useEffect(() => {
    if (streamPaused || autonomyMode === 'OVERRIDE') return;

    const interval = setInterval(() => {
      const activeAgents = agents.filter((a) => !a.isolated);
      if (activeAgents.length === 0) return;

      const randomAgent = activeAgents[Math.floor(Math.random() * activeAgents.length)];
      const sampleActions = [
        { tag: 'OBSERVE', color: 'bg-primary/20 text-primary', msg: 'Subsystem telemetry packet validated against Kalman state estimate.' },
        { tag: 'CONSENSUS', color: 'bg-secondary/20 text-secondary', msg: `Raft-BFT heartbeat verified with peer nodes (${activeAgents.length}/4 active).` },
        { tag: 'EQUILIBRIUM', color: 'bg-primary-fixed/20 text-primary-fixed', msg: 'Thermal and power distribution within optimal Pareto boundary.' },
        { tag: 'TELEMETRY', color: 'bg-tertiary/20 text-tertiary', msg: 'Synchronizing epoch timestamps with Svalbard ground clock.' },
      ];
      const action = sampleActions[Math.floor(Math.random() * sampleActions.length)];

      const now = new Date();
      const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}.${String(Math.floor(now.getMilliseconds() / 10)).padStart(2, '0')}`;

      setCotLogs((prev) => [
        ...prev.slice(-40),
        {
          id: `cot-${Date.now()}`,
          timestamp: timeStr,
          agent: randomAgent.name,
          tag: action.tag,
          tagColor: action.color,
          message: action.msg,
        },
      ]);
    }, 4500);

    return () => clearInterval(interval);
  }, [streamPaused, autonomyMode, agents]);

  // REPL query execution
  const handleReplSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!replInput.trim()) return;

    sound.playClick();
    const query = replInput.trim();
    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}.00`;

    const userEntry: CoTLogEntry = {
      id: `cot-user-${Date.now()}`,
      timestamp: timeStr,
      agent: 'FLT-DIR CHEN.E',
      tag: 'PROMPT_QUERY',
      tagColor: 'bg-tertiary text-on-tertiary',
      message: `REASON_QUERY> "${query}"`,
    };

    let replyMsg = 'Simulated consensus verified: Subsystem states remain within ±0.2% nominal limits.';
    if (query.toLowerCase().includes('thermal') || query.toLowerCase().includes('temp')) {
      replyMsg = 'Agent Alpha responds: Radiator albedo dissipation rate is 14.8 W/m². Inversion safety margin: +18.2°C.';
    } else if (query.toLowerCase().includes('prop') || query.toLowerCase().includes('fuel') || query.toLowerCase().includes('rcs')) {
      replyMsg = 'Agent Gamma responds: Hydrazine reserve 18.4 kg. Next apogee station-keeping node requires 14.8g ΔV impulse.';
    } else if (query.toLowerCase().includes('attitude') || query.toLowerCase().includes('roll') || query.toLowerCase().includes('pointing')) {
      replyMsg = 'Agent Beta responds: Star tracker STR-1 boresight tracking 12 stars. RW momentum wheel speeds at 2,400 RPM nominal.';
    }

    const replyEntry: CoTLogEntry = {
      id: `cot-reply-${Date.now()}`,
      timestamp: timeStr,
      agent: 'SWARM_BFT',
      tag: 'CONSENSUS_REPLY',
      tagColor: 'bg-secondary text-on-secondary',
      message: replyMsg,
    };

    setCotLogs((prev) => [...prev, userEntry, replyEntry]);
    setReplInput('');
  };

  // Revert ledger action
  const handleRevertLedgerItem = (id: string) => {
    sound.playWarning();
    setLedgerItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, reverted: true, telemetryDelta: 'Reverted to Prior State' } : item))
    );
  };

  // Register manual pulse event and calculate kinetic trajectory perturbations
  const registerPulseEvent = (thruster: string, durationMs: number) => {
    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}.${String(Math.floor(now.getMilliseconds() / 10)).padStart(2, '0')}`;

    // Physical trajectory dynamics calculations
    const isPrograde = thruster === '+X';
    const isRetrograde = thruster === '-X';
    const deltaVVal = +(durationMs * 0.00032).toFixed(4);
    const signedDeltaV = isPrograde ? deltaVVal : isRetrograde ? -deltaVVal : 0;

    // Altitude delta: duration * 2.8 meters (for prograde/retrograde)
    const deltaAltMeters = isPrograde
      ? +(durationMs * 2.8).toFixed(1)
      : isRetrograde
      ? -(durationMs * 2.8).toFixed(1)
      : 0;

    // Angular rate: duration * 0.015 deg/s for roll
    const angularRateDeg = thruster.includes('Roll') ? +(durationMs * 0.015).toFixed(2) : 0;

    // Fuel consumption: ~0.042 g/ms hydrazine
    const fuelGrams = +(durationMs * 0.042).toFixed(2);

    // Compute relative timeline timestamp
    const lastTime = manualPulses.length > 0 ? manualPulses[manualPulses.length - 1].timestamp : 0;
    const relativeTime = +(lastTime + 4.0).toFixed(1);

    const newPulse: ManualPulseEvent = {
      id: `pulse-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
      timestamp: relativeTime,
      timeStr,
      thruster,
      durationMs,
      deltaV: signedDeltaV,
      deltaAltMeters,
      angularRateDeg,
      fuelGrams,
    };

    setManualPulses((prev) => [...prev, newPulse]);

    // Stream telemetry to Chain-of-Thought logs
    setCotLogs((prev) => [
      ...prev.slice(-38),
      {
        id: `cot-pulse-${Date.now()}`,
        timestamp: timeStr,
        agent: 'FLT-DIR::ACTUATOR',
        tag: 'THRUST_PULSE',
        tagColor: 'bg-amber-500/20 text-amber-300 font-bold',
        message: `Manual pulse executed on [${thruster}] for ${durationMs}ms. Kinetic ΔV: ${signedDeltaV >= 0 ? '+' : ''}${signedDeltaV} m/s (Δh: ${deltaAltMeters >= 0 ? '+' : ''}${deltaAltMeters}m).`,
      },
      {
        id: `cot-aocs-${Date.now() + 1}`,
        timestamp: timeStr,
        agent: 'Agent Beta::AOCS',
        tag: 'TRAJECTORY_DELTA',
        tagColor: 'bg-cyan-500/20 text-cyan-400',
        message: `Inertial measurement unit logs trajectory delta. Orbit state: a+${deltaAltMeters >= 0 ? '+' : ''}${deltaAltMeters}m, desaturation cycle queued.`,
      },
    ]);

    return newPulse;
  };

  // Clear all pulses and re-circularize
  const handleClearPulses = () => {
    setManualPulses([]);
    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}.00`;
    setCotLogs((prev) => [
      ...prev,
      {
        id: `cot-reset-${Date.now()}`,
        timestamp: timeStr,
        agent: 'Agent Beta::AOCS',
        tag: 'TRAJECTORY_RESET',
        tagColor: 'bg-green-500/20 text-green-400 font-bold',
        message: 'Manual trajectory perturbations cleared. Re-established nominal circular orbit at 541.80 km.',
      },
    ]);
  };

  // Autonomous Counter-Burn dispatched by Swarm
  const handleAutonomousCounterBurn = () => {
    const netAlt = manualPulses.reduce((acc, p) => acc + p.deltaAltMeters, 0);
    const counterThruster = netAlt > 0 ? '-X' : '+X';
    const counterDuration = Math.min(500, Math.max(50, Math.round(Math.abs(netAlt) / 2.8)));

    registerPulseEvent(counterThruster, counterDuration);
  };

  // Transmit RCS manual pulse
  const handleFireRcsPulse = () => {
    if (!safetyInterlockArmed) {
      sound.playWarning();
      setRcsStatusMsg('SAFETY INTERLOCK ENGAGED: Arm interlock first!');
      return;
    }
    sound.playThruster();
    const p = registerPulseEvent(selectedRcsThruster, rcsPulseDuration);
    setRcsStatusMsg(
      `TRANSMITTED: RCS ${selectedRcsThruster} fired for ${rcsPulseDuration}ms (${p.deltaV >= 0 ? '+' : ''}${p.deltaV} m/s ΔV). Trajectory graph updated.`
    );
    setTimeout(() => setRcsStatusMsg(''), 4500);
  };

  // Toggle MCR Seizure
  const handleToggleMcrSeizure = () => {
    sound.playWarning();
    const nextMode = autonomyMode === 'OVERRIDE' ? 'L4' : 'OVERRIDE';
    onChangeAutonomyMode(nextMode);
    setMcrSeized(nextMode === 'OVERRIDE');
  };

  const filteredLogs = activeFilter === 'ALL'
    ? cotLogs
    : cotLogs.filter((log) => log.agent.toUpperCase().includes(activeFilter));

  return (
    <div className="w-full flex flex-col gap-4">
      {/* Mesh Governance Horizon Bar - Bento Ribbon */}
      <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-wrap items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 shadow-sm">
            <Cpu size={20} />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="text-sm text-white font-semibold uppercase tracking-wide">
                MESH GOVERNANCE HORIZON // ARCHITECTURE
              </span>
              <span className="px-2 py-0.5 rounded-full text-[9px] font-mono bg-cyan-500/10 text-cyan-400 font-bold border border-cyan-500/30">
                RAFT-BFT v3.1 AEROSPACE
              </span>
            </div>
            <span className="font-mono text-[11px] text-slate-400">
              POLL RATE: 50Hz · HITL CONFIRMATION PROTOCOL · CRYPTO-SECURED
            </span>
          </div>
        </div>

        {/* Governance Mode Switcher */}
        <div className="flex items-center flex-wrap gap-3 font-mono text-xs">
          <div className="flex items-center bg-[#05070a] p-1 rounded-xl border border-[#1e293b]">
            {(
              [
                { id: 'L4' as AutonomyMode, label: 'L4 UNSUPERVISED' },
                { id: 'HITL' as AutonomyMode, label: 'SEMI-AUTONOMOUS (HITL)' },
                { id: 'OVERRIDE' as AutonomyMode, label: 'MANUAL OVERRIDE' },
              ] as const
            ).map((mode) => (
              <button
                key={mode.id}
                onClick={() => {
                  sound.playClick();
                  onChangeAutonomyMode(mode.id);
                  setMcrSeized(mode.id === 'OVERRIDE');
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all cursor-pointer ${
                  autonomyMode === mode.id
                    ? mode.id === 'OVERRIDE'
                      ? 'bg-rose-500 text-white font-bold shadow-md'
                      : 'bg-cyan-500 text-black font-bold shadow-md'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {mode.label}
              </button>
            ))}
          </div>

          {/* HITL Threshold Selector */}
          <div className="flex items-center gap-1.5 bg-[#05070a] px-3 py-1.5 rounded-xl border border-[#1e293b]">
            <span className="text-[10px] text-slate-400">HITL GATE:</span>
            {(['strict', 'standard', 'autonomous'] as const).map((lvl) => (
              <button
                key={lvl}
                onClick={() => {
                  sound.playClick();
                  setHitlThreshold(lvl);
                }}
                className={`px-2 py-0.5 rounded-lg text-[9px] uppercase cursor-pointer transition-all ${
                  hitlThreshold === lvl
                    ? 'bg-green-500 text-black font-bold shadow-xs'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Grid: Swarm Topology & Kill-Switches (Left) / FPGA Silicon & Hardware Deck (Right) */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
        {/* Left: Swarm Topology & Kill-Switches (7 Cols on XL) */}
        <div className="xl:col-span-7 flex flex-col gap-4">
          {/* Agent Swarm Topology Visualizer - Bento Card */}
          <div className="bg-[#0f172a] border border-[#1e293b] rounded-3xl flex flex-col overflow-hidden shadow-xl hover:border-cyan-500/30 transition-all">
            <div className="p-4 border-b border-[#1e293b] flex items-center justify-between bg-[#0a1120]/80">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-cyan-400">TOPOLOGY //</span>
                <span className="text-xs uppercase text-slate-200 font-semibold">
                  4-Node Raft Consensus Swarm Mesh
                </span>
              </div>
              <span className="text-[10px] font-mono text-green-400 bg-green-500/10 px-2 py-0.5 rounded-full border border-green-500/20">
                CONSENSUS LATENCY: 8.2ms · QUORUM VALID
              </span>
            </div>

            {/* Swarm SVG Graph */}
            <div className="relative h-64 bg-[#05070a] flex items-center justify-center p-4 overflow-hidden select-none">
              <svg className="w-full h-full" viewBox="0 0 500 240">
                {/* Background Consensus Ring */}
                <circle cx="250" cy="120" r="75" fill="none" stroke="#1e293b" strokeWidth="1.5" strokeDasharray="4 4" />
                <circle cx="250" cy="120" r="30" fill="#0f172a" stroke="#22d3ee" strokeWidth="2" />
                <text x="250" y="123" fill="#22d3ee" fontSize="9" fontFamily="monospace" textAnchor="middle" fontWeight="bold">
                  BFT BUS
                </text>

                {/* Node Alpha (Thermal) - Top (250, 45) */}
                <line x1="250" y1="120" x2="250" y2="45" stroke={agents[0].isolated ? '#f43f5e' : '#22d3ee'} strokeWidth="1.5" strokeDasharray={agents[0].isolated ? '3 3' : 'none'} />
                <g transform="translate(250, 45)" className="cursor-pointer" onClick={() => setSelectedAgentNode('alpha')}>
                  <circle r="22" fill={agents[0].isolated ? '#881337' : selectedAgentNode === 'alpha' ? '#1e293b' : '#0f172a'} stroke={agents[0].isolated ? '#f43f5e' : '#22d3ee'} strokeWidth="2" />
                  <text x="0" y="4" fill="#e2e8f0" fontSize="9" fontFamily="monospace" textAnchor="middle" fontWeight="bold">ALPHA</text>
                  <text x="0" y="32" fill="#94a3b8" fontSize="8" fontFamily="monospace" textAnchor="middle">THERMAL</text>
                </g>

                {/* Node Beta (AOCS) - Right (360, 120) */}
                <line x1="250" y1="120" x2="360" y2="120" stroke={agents[1].isolated ? '#f43f5e' : '#22d3ee'} strokeWidth="1.5" strokeDasharray={agents[1].isolated ? '3 3' : 'none'} />
                <g transform="translate(360, 120)" className="cursor-pointer" onClick={() => setSelectedAgentNode('beta')}>
                  <circle r="22" fill={agents[1].isolated ? '#881337' : selectedAgentNode === 'beta' ? '#1e293b' : '#0f172a'} stroke={agents[1].isolated ? '#f43f5e' : '#22d3ee'} strokeWidth="2" />
                  <text x="0" y="4" fill="#e2e8f0" fontSize="9" fontFamily="monospace" textAnchor="middle" fontWeight="bold">BETA</text>
                  <text x="0" y="32" fill="#94a3b8" fontSize="8" fontFamily="monospace" textAnchor="middle">AOCS</text>
                </g>

                {/* Node Gamma (Prop) - Bottom (250, 195) */}
                <line x1="250" y1="120" x2="250" y2="195" stroke={agents[2].isolated ? '#f43f5e' : '#22d3ee'} strokeWidth="1.5" strokeDasharray={agents[2].isolated ? '3 3' : 'none'} />
                <g transform="translate(250, 195)" className="cursor-pointer" onClick={() => setSelectedAgentNode('gamma')}>
                  <circle r="22" fill={agents[2].isolated ? '#881337' : selectedAgentNode === 'gamma' ? '#1e293b' : '#0f172a'} stroke={agents[2].isolated ? '#f43f5e' : '#22d3ee'} strokeWidth="2" />
                  <text x="0" y="4" fill="#e2e8f0" fontSize="9" fontFamily="monospace" textAnchor="middle" fontWeight="bold">GAMMA</text>
                  <text x="0" y="-26" fill="#94a3b8" fontSize="8" fontFamily="monospace" textAnchor="middle">PROP</text>
                </g>

                {/* Node Delta (FDIR) - Left (140, 120) */}
                <line x1="250" y1="120" x2="140" y2="120" stroke={agents[3].isolated ? '#f43f5e' : '#22d3ee'} strokeWidth="1.5" strokeDasharray={agents[3].isolated ? '3 3' : 'none'} />
                <g transform="translate(140, 120)" className="cursor-pointer" onClick={() => setSelectedAgentNode('delta')}>
                  <circle r="22" fill={agents[3].isolated ? '#881337' : selectedAgentNode === 'delta' ? '#1e293b' : '#0f172a'} stroke={agents[3].isolated ? '#f43f5e' : '#22d3ee'} strokeWidth="2" />
                  <text x="0" y="4" fill="#e2e8f0" fontSize="9" fontFamily="monospace" textAnchor="middle" fontWeight="bold">DELTA</text>
                  <text x="0" y="32" fill="#94a3b8" fontSize="8" fontFamily="monospace" textAnchor="middle">FDIR</text>
                </g>
              </svg>

              <div className="absolute bottom-2 right-2 text-[9px] font-mono text-slate-300 bg-[#05070a]/90 border border-[#1e293b] px-2.5 py-1 rounded-lg backdrop-blur-md">
                Click any node to inspect telemetry parameters
              </div>
            </div>
          </div>

          {/* Individual Agent Kill-Switch & Isolation Matrix - Bento Panel */}
          <div className="bg-[#0f172a] border border-[#1e293b] p-5 rounded-3xl flex flex-col gap-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-[#1e293b] pb-3">
              <span className="text-xs uppercase text-slate-200 font-semibold tracking-wide">
                Individual Agent Kill-Switch & Isolation Matrix
              </span>
              <span className="text-[10px] font-mono text-slate-400">
                FAIL-SAFE HARDWARE SEVERANCE
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  className={`p-4 rounded-2xl border flex flex-col justify-between transition-all shadow-sm ${
                    agent.isolated
                      ? 'bg-rose-950/20 border-rose-500/50'
                      : 'bg-[#05070a] border-[#1e293b] hover:border-cyan-500/40'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-cyan-400">
                        {agent.name}
                      </span>
                      <span className="text-[9px] font-mono text-slate-400 uppercase">
                        [{agent.subsystem}]
                      </span>
                    </div>
                    {/* Kill switch button */}
                    <button
                      onClick={() => {
                        sound.playWarning();
                        onToggleAgentIsolation(agent.id);
                      }}
                      className={`px-2.5 py-1 rounded-lg text-[10px] font-mono font-bold uppercase transition-all cursor-pointer ${
                        agent.isolated
                          ? 'bg-rose-500 text-white hover:bg-rose-600'
                          : 'bg-green-500/10 text-green-400 border border-green-500/40 hover:bg-green-500 hover:text-black'
                      }`}
                    >
                      {agent.isolated ? 'ISOLATED (RE-CONNECT)' : 'ONLINE (KILL)'}
                    </button>
                  </div>

                  <p className="text-[11px] text-slate-300 line-clamp-2 my-1">
                    {agent.description}
                  </p>

                  <div className="flex items-center justify-between text-[10px] font-mono pt-2 mt-2 border-t border-[#1e293b]">
                    <span className="text-green-400">CONFIDENCE: {agent.confidence}%</span>
                    <span className="text-slate-400 uppercase">STATE: {agent.state}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: FPGA Silicon & Hardware Actuation Deck (5 Cols on XL) */}
        <div className="xl:col-span-5 flex flex-col gap-4">
          {/* FPGA & Edge-AI Reasoning Budget - Bento Card */}
          <div className="bg-[#0f172a] border border-[#1e293b] rounded-3xl flex flex-col overflow-hidden shadow-xl hover:border-cyan-500/30 transition-all">
            <div className="p-4 border-b border-[#1e293b] flex items-center justify-between bg-[#0a1120]/80">
              <span className="text-xs uppercase text-slate-200 font-semibold tracking-wide">
                Rad-Hard Neural Silicon & Edge-AI Budget
              </span>
              <span className="text-[10px] font-mono text-cyan-400 font-bold bg-cyan-500/10 px-2 py-0.5 rounded-full border border-cyan-500/30">
                XILINX VERSAL SPACE
              </span>
            </div>

            <div className="p-4 flex flex-col sm:flex-row items-center gap-4">
              {/* Rad-Hard Silicon Image */}
              <img
                alt="Rad-Hard Space-Grade Neural Silicon"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuDYubI-u2p4l-hXv5RGc1mLz4ooArlzIgO3qjRVTJMcFwGgaeSdZY5wLpXznn6Tlr3E3fsAFK5NEKAB_6xcA-7HP9eXEzXqgABYV7iFMFnrc-i-SOJaM2wLVG149F-bASAjgBGjA-L069YYTg6JBI6JiOZdfge31zI5qiyfHeNigTjOn_kaR2RXeQE9lTBT_LvndhVfC6xgwBU9dK890GughHkM4I6DmGKblHIFhBPrpBz6FCKQd_h6"
                className="w-28 h-28 object-contain rounded-2xl border border-[#1e293b] bg-[#05070a] p-1.5 shadow-md"
              />

              {/* Specs Grid */}
              <div className="flex-1 w-full grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="bg-[#05070a] p-3 rounded-xl border border-[#1e293b]">
                  <div className="text-[10px] text-slate-400">NPU COMPUTE LOAD</div>
                  <div className="text-green-400 font-bold text-sm">38.4%</div>
                </div>
                <div className="bg-[#05070a] p-3 rounded-xl border border-[#1e293b]">
                  <div className="text-[10px] text-slate-400">CORE POWER</div>
                  <div className="text-cyan-400 font-bold text-sm">12.1 Watts</div>
                </div>
                <div className="bg-[#05070a] p-3 rounded-xl border border-[#1e293b]">
                  <div className="text-[10px] text-slate-400">THROUGHPUT</div>
                  <div className="text-slate-200 font-semibold text-xs">420 msgs/s</div>
                </div>
                <div className="bg-[#05070a] p-3 rounded-xl border border-[#1e293b]">
                  <div className="text-[10px] text-slate-400">PACKET LOSS</div>
                  <div className="text-green-400 font-bold text-xs">0.000%</div>
                </div>
              </div>
            </div>
          </div>

          {/* Flight Director Manual Override Deck & Hardware Actuators (Terminals 01-04) - Bento Card */}
          <div className="bg-[#0f172a] border border-[#1e293b] rounded-3xl flex flex-col overflow-hidden shadow-xl hover:border-amber-500/30 transition-all">
            <div className="p-4 border-b border-[#1e293b] flex items-center justify-between bg-[#0a1120]/80">
              <div className="flex items-center gap-2 text-amber-400">
                <SlidersHorizontal size={16} />
                <span className="text-xs uppercase font-bold tracking-wide">
                  DIRECT HARDWARE ACTUATION DECK
                </span>
              </div>
              <button
                onClick={handleToggleMcrSeizure}
                className={`px-2.5 py-1 rounded-lg text-[10px] font-mono font-bold uppercase transition-all cursor-pointer ${
                  mcrSeized
                    ? 'bg-rose-500 text-white animate-pulse shadow-md'
                    : 'bg-rose-500/10 text-rose-400 border border-rose-500/40 hover:bg-rose-500 hover:text-white'
                }`}
              >
                {mcrSeized ? 'MCR SEIZED (RESTORE L4)' : 'SEIZE MANUAL CONTROL'}
              </button>
            </div>

            <div className="p-4 flex flex-col gap-3 font-mono text-xs">
              {/* Terminal 01: Direct RCS Thrusters */}
              <div className="bg-[#05070a] p-3.5 rounded-2xl border border-[#1e293b] flex flex-col gap-2.5 shadow-sm">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-cyan-400 font-bold flex items-center gap-1.5">
                    <Flame size={13} />
                    01 // RCS THRUSTER QUAD FIRE
                  </span>
                  {/* Safety Interlock */}
                  <button
                    onClick={() => {
                      sound.playClick();
                      setSafetyInterlockArmed(!safetyInterlockArmed);
                    }}
                    className={`px-2.5 py-1 rounded-lg text-[9px] font-bold uppercase flex items-center gap-1 cursor-pointer transition-all ${
                      safetyInterlockArmed
                        ? 'bg-rose-500 text-white animate-pulse'
                        : 'bg-[#0f172a] text-slate-400 border border-[#1e293b]'
                    }`}
                  >
                    {safetyInterlockArmed ? <Unlock size={10} /> : <Lock size={10} />}
                    {safetyInterlockArmed ? 'INTERLOCK ARMED' : 'INTERLOCK SAFE'}
                  </button>
                </div>

                {/* Thruster Selectors */}
                <div className="grid grid-cols-6 gap-1">
                  {(['+X', '-X', '+Y', '-Y', 'Roll ↺', 'Roll ↻'] as const).map((thrust) => (
                    <button
                      key={thrust}
                      onClick={() => {
                        sound.playClick();
                        setSelectedRcsThruster(thrust);
                      }}
                      className={`py-1 text-[10px] rounded-lg border transition-all cursor-pointer ${
                        selectedRcsThruster === thrust
                          ? 'bg-cyan-500 text-black font-bold border-cyan-400 shadow-xs'
                          : 'bg-[#0f172a] text-slate-400 border-[#1e293b] hover:text-white'
                      }`}
                    >
                      {thrust}
                    </button>
                  ))}
                </div>

                {/* Pulse duration & Transmit */}
                <div className="flex items-center gap-2 pt-1">
                  <span className="text-[10px] text-slate-400">PULSE:</span>
                  {([50, 100, 250, 500] as const).map((ms) => (
                    <button
                      key={ms}
                      onClick={() => setRcsPulseDuration(ms)}
                      className={`px-2 py-0.5 rounded-md text-[9px] transition-all cursor-pointer ${
                        rcsPulseDuration === ms
                          ? 'bg-green-500 text-black font-bold shadow-xs'
                          : 'bg-[#0f172a] text-slate-400 border border-[#1e293b]'
                      }`}
                    >
                      {ms}ms
                    </button>
                  ))}
                  <button
                    onClick={handleFireRcsPulse}
                    className="ml-auto px-3 py-1 rounded-lg bg-amber-400 text-black font-bold text-[10px] uppercase hover:bg-amber-300 transition-all cursor-pointer shadow-sm"
                  >
                    FIRE PULSE
                  </button>
                </div>

                {rcsStatusMsg && (
                  <div className="text-[10px] text-amber-300 bg-amber-500/10 p-2 rounded-xl border border-amber-500/30">
                    {rcsStatusMsg}
                  </div>
                )}
              </div>

              {/* Terminal 02: Thermal Heater PWM & SADA Slew */}
              <div className="bg-[#05070a] p-3.5 rounded-2xl border border-[#1e293b] flex flex-col gap-2.5 shadow-sm">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-green-400 font-bold flex items-center gap-1.5">
                    <Power size={13} />
                    02 // THERMAL HEATER PWM SLIDER
                  </span>
                  <span className="text-green-400 font-bold text-xs">{heaterPwm}% DUTY</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={heaterPwm}
                  onChange={(e) => setHeaterPwm(parseInt(e.target.value))}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
                <div className="flex justify-between text-[8px] text-slate-400 font-mono">
                  <span>0% (Heaters OFF)</span>
                  <span>50% (Nominal)</span>
                  <span>100% (Emergency Pre-Eclipse)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Live Trajectory Telemetry After Manually Fired Pulses - Bento Panel */}
      <PulseTrajectoryGraph
        pulses={manualPulses}
        onFirePulse={(thruster, durationMs) => {
          registerPulseEvent(thruster, durationMs);
        }}
        onClearPulses={handleClearPulses}
        onAutonomousCounterBurn={handleAutonomousCounterBurn}
        autonomyMode={autonomyMode}
        isInterlockArmed={safetyInterlockArmed}
      />

      {/* Live Multi-Agent Reasoning Stream (Chain-of-Thought / CoT) & Interactive REPL - Bento Panel */}
      <div className="bg-[#0f172a] border border-[#1e293b] p-5 rounded-3xl flex flex-col gap-4 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1e293b] pb-3">
          <div className="flex items-center gap-2">
            <Zap size={15} className="text-cyan-400" />
            <span className="text-xs uppercase text-white font-semibold tracking-wide">
              Live Multi-Agent Reasoning Stream (Chain-of-Thought Engine)
            </span>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs">
            {/* Filter buttons */}
            {(['ALL', 'ALPHA', 'BETA', 'GAMMA', 'DELTA'] as const).map((filter) => (
              <button
                key={filter}
                onClick={() => setActiveFilter(filter)}
                className={`px-2.5 py-0.5 rounded-lg text-[9px] uppercase cursor-pointer transition-all ${
                  activeFilter === filter
                    ? 'bg-cyan-500 text-black font-bold shadow-xs'
                    : 'bg-[#05070a] text-slate-400 hover:text-white border border-[#1e293b]'
                }`}
              >
                {filter}
              </button>
            ))}

            <div className="w-px h-3 bg-[#1e293b]"></div>

            <button
              onClick={() => setStreamPaused(!streamPaused)}
              className="p-1 rounded text-slate-400 hover:text-white transition-colors"
              title={streamPaused ? 'Resume Stream' : 'Pause Stream'}
            >
              {streamPaused ? <Play size={13} className="text-green-400" /> : <Pause size={13} />}
            </button>
            <button
              onClick={() => setCotLogs([])}
              className="p-1 rounded text-slate-400 hover:text-rose-400 transition-colors"
              title="Clear Stream"
            >
              <Trash2 size={13} />
            </button>
          </div>
        </div>

        {/* Streaming Logs */}
        <div className="h-56 overflow-y-auto bg-[#05070a] p-4 rounded-2xl border border-[#1e293b] flex flex-col gap-2 font-mono text-xs shadow-inner">
          {filteredLogs.map((log) => (
            <div
              key={log.id}
              className="flex items-start gap-2 py-1 border-b border-[#1e293b]/50 last:border-0 hover:bg-[#0f172a]/50 px-1 rounded transition-colors"
            >
              <span className="text-slate-500 text-[10px] shrink-0 font-mono">{log.timestamp}</span>
              <span className="text-cyan-400 font-semibold shrink-0 text-[11px]">{log.agent}</span>
              <span className={`px-1.5 py-0.2 rounded-sm text-[8px] font-bold uppercase shrink-0 ${log.tagColor}`}>
                {log.tag}
              </span>
              <span className="text-slate-200 text-[11px] leading-tight">{log.message}</span>
            </div>
          ))}
        </div>

        {/* Interactive REPL Prompt */}
        <form onSubmit={handleReplSubmit} className="flex gap-2 font-mono text-xs">
          <span className="py-2.5 px-3 rounded-xl bg-[#05070a] border border-[#1e293b] text-cyan-400 font-bold text-xs select-none">
            REASON_QUERY&gt;
          </span>
          <input
            type="text"
            value={replInput}
            onChange={(e) => setReplInput(e.target.value)}
            placeholder="Query swarm reasoning, test hypothesis, or command simulation parameter..."
            className="flex-1 px-4 py-2.5 rounded-xl bg-[#05070a] border border-[#1e293b] text-white placeholder:text-slate-500 focus:outline-hidden focus:border-cyan-400 transition-all"
          />
          <button
            type="submit"
            className="px-5 py-2.5 rounded-xl bg-cyan-500 text-black font-bold uppercase hover:bg-cyan-400 transition-all flex items-center gap-1.5 cursor-pointer shadow-md"
          >
            <Send size={13} />
            EVALUATE
          </button>
        </form>
      </div>

      {/* Autonomous Intervention Ledger - Bento Panel */}
      <div className="bg-[#0f172a] border border-[#1e293b] p-5 rounded-3xl flex flex-col gap-4 shadow-xl">
        <div className="flex items-center justify-between border-b border-[#1e293b] pb-3">
          <span className="text-xs uppercase text-white font-semibold tracking-wide">
            Autonomous Intervention Ledger (Last 24 Hours)
          </span>
          <span className="text-[10px] font-mono text-slate-400">
            ALL EXECUTIONS SECURED ON CRYPTO-LOG
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#1e293b] text-slate-400 text-[10px] uppercase">
                <th className="pb-2.5">TIMESTAMP</th>
                <th className="pb-2.5">LEAD AGENT</th>
                <th className="pb-2.5">ACTION EXECUTED</th>
                <th className="pb-2.5">RESOLUTION</th>
                <th className="pb-2.5">TELEMETRY DELTA</th>
                <th className="pb-2.5 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody>
              {ledgerItems.map((item) => (
                <tr
                  key={item.id}
                  className="border-b border-[#1e293b]/40 hover:bg-[#05070a]/60 transition-colors"
                >
                  <td className="py-2.5 text-slate-400 text-[10px]">{item.timestamp}</td>
                  <td className="py-2.5 text-cyan-400 font-semibold">{item.leadAgent}</td>
                  <td className="py-2.5 text-slate-200">{item.actionExecuted}</td>
                  <td className="py-2.5 text-green-400">{item.resolutionTime}</td>
                  <td className={`py-2.5 ${item.reverted ? 'text-rose-400 line-through' : 'text-cyan-400'}`}>
                    {item.telemetryDelta}
                  </td>
                  <td className="py-2.5 text-right">
                    <button
                      onClick={() => handleRevertLedgerItem(item.id)}
                      disabled={item.reverted}
                      className={`px-2.5 py-1 rounded-lg text-[9px] uppercase font-bold cursor-pointer transition-all ${
                        item.reverted
                          ? 'bg-[#1e293b]/30 text-slate-500 cursor-not-allowed'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/40 hover:bg-rose-500 hover:text-white'
                      }`}
                    >
                      {item.reverted ? 'REVERTED' : 'REVERT'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
