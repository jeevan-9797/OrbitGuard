import React, { useState, useEffect } from 'react';
import { TelemetryIncident } from '../types';
import { INITIAL_INCIDENTS } from '../data/mockFlightData';
import { sound } from '../utils/audio';
import {
  Download,
  Activity,
  BatteryCharging,
  Compass,
  Cpu,
  Flame,
  Radio,
  Pause,
  Play,
  Filter,
} from 'lucide-react';

export const AnalyticsScreen: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'1orbit' | '24h' | '7d' | 'lifetime'>('24h');
  const [subsystemFilter, setSubsystemFilter] = useState<string>('ALL');
  const [incidents, setIncidents] = useState<TelemetryIncident[]>(INITIAL_INCIDENTS);
  const [oscilloscopePaused, setOscilloscopePaused] = useState<boolean>(false);

  // Live sweep offset for oscilloscopes
  const [sweepOffset, setSweepOffset] = useState<number>(0);

  useEffect(() => {
    if (oscilloscopePaused) return;
    const interval = setInterval(() => {
      setSweepOffset((prev) => (prev + 1) % 100);
    }, 150);
    return () => clearInterval(interval);
  }, [oscilloscopePaused]);

  // Handle Export HDF5 real file download
  const handleExportHdf5 = () => {
    sound.playClick();
    const exportData = {
      satellite: 'ASTRA-7 (TWIN-7 // SEC-9)',
      norad_id: 59421,
      export_timestamp: new Date().toISOString(),
      time_range: timeRange,
      telemetry: {
        orbit_altitude_km: 541.8,
        velocity_km_s: 7.614,
        battery_soc_pct: 98.2,
        bus_voltage_v: 28.42,
        hydrazine_reserves_kg: 18.4,
        agent_actions_24h: 1482,
        inter_agent_consensus_ms: 8.2,
      },
      incident_ledger: incidents,
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `ASTRA7_TELEMETRY_EXPORT_${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const filteredIncidents = subsystemFilter === 'ALL'
    ? incidents
    : incidents.filter((i) => i.subsystem.toUpperCase().includes(subsystemFilter));

  return (
    <div className="w-full flex flex-col gap-4">
      {/* Header Bar: Title, Filters & Export - Bento Ribbon */}
      <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-wrap items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 shadow-sm">
            <Activity size={20} />
          </div>
          <div className="flex flex-col">
            <span className="text-sm text-white font-semibold uppercase tracking-wide">
              MISSION TELEMETRY STREAM & AUTONOMOUS AGENT DYNAMICS
            </span>
            <span className="font-mono text-[11px] text-slate-400">
              LONG-RANGE FLIGHT TRENDS · OSCILLOSCOPE TRACES · POST-MORTEM LEDGER
            </span>
          </div>
        </div>

        <div className="flex items-center flex-wrap gap-3 font-mono text-xs">
          {/* Time range selector */}
          <div className="flex items-center bg-[#05070a] p-1 rounded-xl border border-[#1e293b] text-[11px]">
            {(
              [
                { id: '1orbit', label: '1 ORBIT (94m)' },
                { id: '24h', label: '24 HOURS' },
                { id: '7d', label: '7 DAYS' },
                { id: 'lifetime', label: 'LIFETIME (142d)' },
              ] as const
            ).map((t) => (
              <button
                key={t.id}
                onClick={() => {
                  sound.playClick();
                  setTimeRange(t.id);
                }}
                className={`px-3 py-1 rounded-lg transition-all cursor-pointer ${
                  timeRange === t.id
                    ? 'bg-cyan-500 text-black font-bold shadow-xs'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Export HDF5 Button */}
          <button
            onClick={handleExportHdf5}
            className="px-4 py-2 rounded-xl bg-cyan-500/15 border border-cyan-500/40 hover:bg-cyan-500 hover:text-black text-cyan-400 font-bold flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
          >
            <Download size={13} />
            EXPORT HDF5 / JSON
          </button>
        </div>
      </div>

      {/* High-Density 5-Column Flight KPI Matrix - Bento Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 font-mono">
        {/* KPI 1: EPS Battery Array */}
        <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col justify-between hover:border-green-400/50 transition-all shadow-xl">
          <div className="flex items-center justify-between text-slate-400 text-[10px]">
            <span className="flex items-center gap-1.5">
              <BatteryCharging size={13} className="text-green-400" />
              EPS / BATTERY ARRAY
            </span>
            <span className="text-green-400 font-bold bg-green-500/10 px-1.5 py-0.5 rounded border border-green-500/30">NOMINAL</span>
          </div>
          <div className="text-xl font-bold text-white my-1.5">98.2% SOH</div>
          <div className="text-[10px] text-slate-400">
            28.42V Reg · 1,420 Cycles · 21.2°C
          </div>
        </div>

        {/* KPI 2: LEO Ephemeris */}
        <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col justify-between hover:border-cyan-400/50 transition-all shadow-xl">
          <div className="flex items-center justify-between text-slate-400 text-[10px]">
            <span className="flex items-center gap-1.5">
              <Compass size={13} className="text-cyan-400" />
              LEO EPHEMERIS
            </span>
            <span className="text-cyan-400 font-bold bg-cyan-500/10 px-1.5 py-0.5 rounded border border-cyan-500/30">541.8 km</span>
          </div>
          <div className="text-xl font-bold text-white my-1.5">7.614 km/s</div>
          <div className="text-[10px] text-slate-400">
            Decay: -4.2m/24h · Sunlit Phase
          </div>
        </div>

        {/* KPI 3: Neural Agent Swarm */}
        <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col justify-between hover:border-cyan-400/50 transition-all shadow-xl">
          <div className="flex items-center justify-between text-slate-400 text-[10px]">
            <span className="flex items-center gap-1.5">
              <Cpu size={13} className="text-cyan-400" />
              AGENTIC SWARM
            </span>
            <span className="text-green-400 font-bold bg-green-500/10 px-1.5 py-0.5 rounded border border-green-500/30">100% UNTETHERED</span>
          </div>
          <div className="text-xl font-bold text-white my-1.5">1,482 Actions</div>
          <div className="text-[10px] text-slate-400">
            0 Ground Assists · 8.2ms Quorum
          </div>
        </div>

        {/* KPI 4: RCS Hydrazine */}
        <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col justify-between hover:border-amber-400/50 transition-all shadow-xl">
          <div className="flex items-center justify-between text-slate-400 text-[10px]">
            <span className="flex items-center gap-1.5">
              <Flame size={13} className="text-amber-400" />
              RCS HYDRAZINE N2H4
            </span>
            <span className="text-amber-400 font-bold bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/30">86% REMAIN</span>
          </div>
          <div className="text-xl font-bold text-white my-1.5">18.4 kg</div>
          <div className="text-[10px] text-slate-400">
            Tank: 18.2 bar · ΔV: 44.8 m/s
          </div>
        </div>

        {/* KPI 5: RF Telemetry Link */}
        <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col justify-between hover:border-green-400/50 transition-all shadow-xl">
          <div className="flex items-center justify-between text-slate-400 text-[10px]">
            <span className="flex items-center gap-1.5">
              <Radio size={13} className="text-green-400" />
              RF TELEMETRY LINK
            </span>
            <span className="text-green-400 font-bold bg-green-500/10 px-1.5 py-0.5 rounded border border-green-500/30">LOCKED</span>
          </div>
          <div className="text-xl font-bold text-white my-1.5">99.98%</div>
          <div className="text-[10px] text-slate-400">
            SNR: 19.2 dB · X-Band 8.4GHz
          </div>
        </div>
      </div>

      {/* Synchronized Multi-Channel Telemetry Oscilloscope Strip - Bento Panel */}
      <div className="bg-[#0f172a] border border-[#1e293b] p-5 rounded-3xl flex flex-col gap-4 shadow-xl">
        <div className="flex items-center justify-between border-b border-[#1e293b]/60 pb-3">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-cyan-400">OSC-04 //</span>
            <span className="text-xs uppercase text-slate-200 font-semibold tracking-wide">
              Synchronized 4-Channel Telemetry Oscilloscope (Real-Time Waveforms)
            </span>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="text-[10px] text-slate-400">TIMEBASE: 100ms/div</span>
            <button
              onClick={() => setOscilloscopePaused(!oscilloscopePaused)}
              className="p-1.5 rounded-lg bg-[#05070a] border border-[#1e293b] text-slate-400 hover:text-white cursor-pointer transition-colors"
              title={oscilloscopePaused ? 'Resume Trace' : 'Hold Trace'}
            >
              {oscilloscopePaused ? <Play size={13} className="text-green-400" /> : <Pause size={13} />}
            </button>
          </div>
        </div>

        {/* 4 Oscilloscope Channels Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {/* CH 01: EPS Thermal Matrix */}
          <div className="bg-[#05070a] border border-[#1e293b] rounded-2xl p-4 flex flex-col justify-between shadow-sm">
            <div className="flex items-center justify-between text-[11px] font-mono mb-2">
              <span className="text-cyan-400 font-bold">CH 01 // EPS 8-CELL THERMAL MATRIX</span>
              <span className="text-green-400 font-bold">21.2°C AVG</span>
            </div>
            <div className="h-24 w-full relative overflow-hidden bg-[#0f172a]/60 rounded-xl border border-[#1e293b]/60 shadow-inner">
              <svg className="w-full h-full" viewBox="0 0 400 90" preserveAspectRatio="none">
                {/* Safe nominal corridor band */}
                <rect x="0" y="25" width="400" height="40" fill="#22c55e" fillOpacity="0.08" />
                {/* Live sweeping sine wave */}
                <path
                  d={`M 0,${45 + Math.sin((sweepOffset * 0.1)) * 10} Q 100,${30 + Math.sin((sweepOffset * 0.1) + 1) * 12} 200,${50 + Math.cos((sweepOffset * 0.1) + 2) * 8} T 400,${45 + Math.sin((sweepOffset * 0.1) + 3) * 10}`}
                  fill="none"
                  stroke="#22d3ee"
                  strokeWidth="2"
                />
              </svg>
            </div>
            <div className="flex justify-between text-[9px] font-mono text-slate-400 mt-2">
              <span>Lower: +18.0°C</span>
              <span>Nominal Corridor (±2.5σ)</span>
              <span>Upper: +28.0°C</span>
            </div>
          </div>

          {/* CH 02: Semi-Major Axis Altitude */}
          <div className="bg-[#05070a] border border-[#1e293b] rounded-2xl p-4 flex flex-col justify-between shadow-sm">
            <div className="flex items-center justify-between text-[11px] font-mono mb-2">
              <span className="text-green-400 font-bold">CH 02 // SEMI-MAJOR AXIS ORBIT (km)</span>
              <span className="text-slate-200 font-bold">541.80 km</span>
            </div>
            <div className="h-24 w-full relative overflow-hidden bg-[#0f172a]/60 rounded-xl border border-[#1e293b]/60 shadow-inner">
              <svg className="w-full h-full" viewBox="0 0 400 90" preserveAspectRatio="none">
                <line x1="0" y1="45" x2="400" y2="45" stroke="#334155" strokeWidth="1" strokeDasharray="4 4" />
                {/* Altitude trace */}
                <path
                  d={`M 0,${45 + Math.sin((sweepOffset * 0.05)) * 4} L 150,${46 + Math.sin((sweepOffset * 0.05) + 1) * 3} L 250,${38} L 400,${42}`}
                  fill="none"
                  stroke="#22c55e"
                  strokeWidth="2"
                />
                {/* Micro RCS firing indicator */}
                <circle cx="250" cy="38" r="3" fill="#fbbf24" />
                <text x="256" y="34" fill="#fbbf24" fontSize="8" fontFamily="monospace">RCS +ΔV</text>
              </svg>
            </div>
            <div className="flex justify-between text-[9px] font-mono text-slate-400 mt-2">
              <span>Perigee: 541.2km</span>
              <span>Apogee Boost Scheduled</span>
              <span>Apogee: 542.4km</span>
            </div>
          </div>

          {/* CH 03: Solar Harvest vs Bus Load */}
          <div className="bg-[#05070a] border border-[#1e293b] rounded-2xl p-4 flex flex-col justify-between shadow-sm">
            <div className="flex items-center justify-between text-[11px] font-mono mb-2">
              <span className="text-amber-400 font-bold">CH 03 // SOLAR HARVEST vs BUS LOAD (W)</span>
              <span className="text-amber-400 font-bold">2,420W / 412W</span>
            </div>
            <div className="h-24 w-full relative overflow-hidden bg-[#0f172a]/60 rounded-xl border border-[#1e293b]/60 shadow-inner">
              <svg className="w-full h-full" viewBox="0 0 400 90" preserveAspectRatio="none">
                {/* Solar curve */}
                <path
                  d="M 0,20 Q 200,15 300,75 L 400,75"
                  fill="none"
                  stroke="#fbbf24"
                  strokeWidth="2"
                />
                {/* Bus load curve */}
                <line x1="0" y1="65" x2="400" y2="65" stroke="#38bdf8" strokeWidth="1.5" strokeDasharray="3 3" />
              </svg>
            </div>
            <div className="flex justify-between text-[9px] font-mono text-slate-400 mt-2">
              <span>Day: 2,420W Harvest</span>
              <span>Penumbra / Umbra Transition</span>
              <span>Eclipse: 0W (Batt Power)</span>
            </div>
          </div>

          {/* CH 04: Reaction Wheel Array Speeds */}
          <div className="bg-[#05070a] border border-[#1e293b] rounded-2xl p-4 flex flex-col justify-between shadow-sm">
            <div className="flex items-center justify-between text-[11px] font-mono mb-2">
              <span className="text-cyan-400 font-bold">CH 04 // REACTION WHEEL ARRAY (RPM)</span>
              <span className="text-green-400 font-bold">2,400 RPM</span>
            </div>
            <div className="h-24 w-full relative overflow-hidden bg-[#0f172a]/60 rounded-xl border border-[#1e293b]/60 shadow-inner">
              <svg className="w-full h-full" viewBox="0 0 400 90" preserveAspectRatio="none">
                <path
                  d={`M 0,${50 + Math.sin(sweepOffset * 0.15) * 6} Q 120,${45 + Math.cos(sweepOffset * 0.15) * 8} 250,${48} T 400,${50}`}
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="2"
                />
              </svg>
            </div>
            <div className="flex justify-between text-[9px] font-mono text-slate-400 mt-2">
              <span>RW-1: 2,380 RPM</span>
              <span>RW-2: 2,410 RPM</span>
              <span>RW-3: 2,400 RPM</span>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Grid: Incident Log & Agent Post-Mortem Table (Left) + Subsystem Degradation Radar (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Incident Log Table (8 cols on LG) - Bento Panel */}
        <div className="lg:col-span-8 bg-[#0f172a] border border-[#1e293b] p-5 rounded-3xl flex flex-col gap-4 shadow-xl">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1e293b]/60 pb-3">
            <span className="text-xs uppercase text-slate-200 font-semibold tracking-wide">
              Telemetry Incident Log & Agent Post-Mortem (Last 24 Hours)
            </span>

            {/* Subsystem filter */}
            <div className="flex items-center gap-1.5 font-mono text-xs">
              <Filter size={12} className="text-slate-400" />
              {(['ALL', 'THERMAL', 'ADCS', 'PROPULSION'] as const).map((sub) => (
                <button
                  key={sub}
                  onClick={() => setSubsystemFilter(sub)}
                  className={`px-2.5 py-1 rounded-lg text-[9px] uppercase cursor-pointer transition-all ${
                    subsystemFilter === sub
                      ? 'bg-cyan-500 text-black font-bold shadow-xs'
                      : 'bg-[#05070a] text-slate-400 border border-[#1e293b] hover:text-white'
                  }`}
                >
                  {sub}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#1e293b] text-slate-400 text-[10px] uppercase">
                  <th className="pb-2.5">EVENT ID</th>
                  <th className="pb-2.5">SUBSYSTEM</th>
                  <th className="pb-2.5">SOURCE</th>
                  <th className="pb-2.5">TRIGGER ROOT CAUSE</th>
                  <th className="pb-2.5">RESPONSE</th>
                  <th className="pb-2.5">REMEDIATOR</th>
                  <th className="pb-2.5 text-right">STATUS</th>
                </tr>
              </thead>
              <tbody>
                {filteredIncidents.map((inc) => (
                  <tr
                    key={inc.id}
                    className="border-b border-[#1e293b]/40 hover:bg-[#05070a]/60 transition-colors"
                  >
                    <td className="py-2.5 text-cyan-400 font-bold text-[10px]">{inc.id}</td>
                    <td className="py-2.5 text-slate-100 font-semibold">{inc.subsystem}</td>
                    <td className="py-2.5">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[8px] font-bold ${
                          inc.type === 'CHAOS'
                            ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                            : 'bg-green-500/15 text-green-400 border border-green-500/30'
                        }`}
                      >
                        {inc.type}
                      </span>
                    </td>
                    <td className="py-2.5 text-slate-300 text-[11px]">{inc.triggerRoot}</td>
                    <td className="py-2.5 text-cyan-400 text-[10px]">{inc.responseTime}</td>
                    <td className="py-2.5 text-slate-200 text-[10px]">{inc.remediator}</td>
                    <td className="py-2.5 text-right">
                      <span className="px-2 py-0.5 rounded-full text-[9px] bg-green-500/15 text-green-400 font-bold border border-green-500/30">
                        {inc.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Subsystem Degradation Radar & Health (4 cols on LG) - Bento Panel */}
        <div className="lg:col-span-4 bg-[#0f172a] border border-[#1e293b] p-5 rounded-3xl flex flex-col justify-between shadow-xl">
          <div>
            <div className="flex items-center justify-between border-b border-[#1e293b]/60 pb-3 mb-4">
              <span className="text-xs uppercase text-slate-200 font-semibold tracking-wide">
                Degradation & Health Radar
              </span>
              <span className="text-[10px] font-mono text-green-400 font-bold bg-green-500/10 px-2 py-0.5 rounded-full border border-green-500/30">
                98.1% OVERALL SOH
              </span>
            </div>

            {/* Radar Polygon SVG */}
            <div className="relative h-44 w-full flex items-center justify-center bg-[#05070a] rounded-2xl border border-[#1e293b] p-2 shadow-inner">
              <svg className="w-full h-full" viewBox="0 0 200 180">
                {/* Concentric circles */}
                <circle cx="100" cy="90" r="60" fill="none" stroke="#1e293b" strokeWidth="1" strokeDasharray="3 3" />
                <circle cx="100" cy="90" r="40" fill="none" stroke="#1e293b" strokeWidth="1" strokeDasharray="3 3" />
                <circle cx="100" cy="90" r="20" fill="none" stroke="#1e293b" strokeWidth="1" />

                {/* Axes */}
                <line x1="100" y1="30" x2="100" y2="150" stroke="#334155" strokeWidth="1" />
                <line x1="40" y1="90" x2="160" y2="90" stroke="#334155" strokeWidth="1" />

                {/* Radar Polygon Shape */}
                <polygon
                  points="100,34 156,90 100,146 44,90"
                  fill="#22d3ee"
                  fillOpacity="0.2"
                  stroke="#22d3ee"
                  strokeWidth="2"
                />

                {/* Labels */}
                <text x="100" y="24" fill="#22d3ee" fontSize="8" fontFamily="monospace" textAnchor="middle">
                  SOLAR (94%)
                </text>
                <text x="165" y="93" fill="#22c55e" fontSize="8" fontFamily="monospace">
                  BATT (98%)
                </text>
                <text x="100" y="162" fill="#fbbf24" fontSize="8" fontFamily="monospace" textAnchor="middle">
                  NOZZLE (91%)
                </text>
                <text x="35" y="93" fill="#38bdf8" fontSize="8" fontFamily="monospace" textAnchor="end">
                  STR (99%)
                </text>
              </svg>
            </div>
          </div>

          {/* Wear Rate Breakdown */}
          <div className="flex flex-col gap-2 pt-3 border-t border-[#1e293b] font-mono text-[10px]">
            <div className="flex justify-between">
              <span className="text-slate-400">Projected Operational Life:</span>
              <span className="text-green-400 font-bold">12.4 Years remaining</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Annual Radiation Dose:</span>
              <span className="text-cyan-400 font-bold">1.24 kRad (Within 25 kRad budget)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
