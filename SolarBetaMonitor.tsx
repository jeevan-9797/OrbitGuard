import React, { useState } from 'react';
import { SolarBetaData } from '../utils/orbitalCalculations';
import { Sun, Clock, Zap, ArrowUpRight, ArrowDownRight, RotateCw, Play, Pause, AlertTriangle, ShieldCheck } from 'lucide-react';
import { sound } from '../utils/audio';

interface SolarBetaMonitorProps {
  solarBetaData: SolarBetaData;
  isLiveTime: boolean;
  onToggleLiveTime: (live: boolean) => void;
  manualDayOffset: number;
  onManualDayOffsetChange: (days: number) => void;
  onResetToLive: () => void;
}

export const SolarBetaMonitor: React.FC<SolarBetaMonitorProps> = ({
  solarBetaData,
  isLiveTime,
  onToggleLiveTime,
  manualDayOffset,
  onManualDayOffsetChange,
  onResetToLive,
}) => {
  const [isAutoCycling, setIsAutoCycling] = useState<boolean>(false);
  const cycleIntervalRef = React.useRef<number | null>(null);

  // Toggle auto-cycling through seasonal beta variation
  const toggleAutoCycle = () => {
    sound.playClick();
    if (isAutoCycling) {
      if (cycleIntervalRef.current) clearInterval(cycleIntervalRef.current);
      setIsAutoCycling(false);
    } else {
      onToggleLiveTime(false);
      setIsAutoCycling(true);
      cycleIntervalRef.current = window.setInterval(() => {
        onManualDayOffsetChange((manualDayOffset + 0.4) % 60);
      }, 100);
    }
  };

  React.useEffect(() => {
    if (isLiveTime && isAutoCycling) {
      if (cycleIntervalRef.current) clearInterval(cycleIntervalRef.current);
      setIsAutoCycling(false);
    }
  }, [isLiveTime, isAutoCycling]);

  React.useEffect(() => {
    return () => {
      if (cycleIntervalRef.current) clearInterval(cycleIntervalRef.current);
    };
  }, []);

  const beta = solarBetaData.betaDeg;
  const isPositive = beta >= 0;
  const crit = solarBetaData.criticalBetaDeg;
  const isContinuousSun = Math.abs(beta) >= crit;

  // Meter position percentage on scale from -90 to +90
  const betaPercent = ((beta + 90) / 180) * 100;
  const critLowerPercent = ((-crit + 90) / 180) * 100;
  const critUpperPercent = ((crit + 90) / 180) * 100;

  return (
    <div className="bg-[#0f172a] border border-[#1e293b] rounded-3xl p-5 shadow-xl flex flex-col gap-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1e293b] pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-400">
            <Sun size={18} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-amber-400">SOLAR β MONITOR //</span>
              <span className="font-semibold text-xs uppercase text-white tracking-wide">
                Real-Time Astronomical Telemetry
              </span>
            </div>
            <span className="text-[10px] font-mono text-slate-400">
              Live Sun Vector · Orbital Plane Intersect · J2 Nodal Precession
            </span>
          </div>
        </div>

        {/* Live vs Manual Mode Pill */}
        <div className="flex items-center gap-2 bg-[#05070a] p-1 rounded-xl border border-[#1e293b]">
          <button
            onClick={() => {
              sound.playClick();
              onResetToLive();
            }}
            className={`px-3 py-1 text-[10px] font-mono uppercase rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${
              isLiveTime
                ? 'bg-emerald-500 text-black font-bold shadow-md shadow-emerald-500/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${isLiveTime ? 'bg-black' : 'bg-emerald-400 animate-ping'}`} />
            LIVE UTC SYNC
          </button>
          <button
            onClick={() => {
              sound.playClick();
              onToggleLiveTime(false);
            }}
            className={`px-3 py-1 text-[10px] font-mono uppercase rounded-lg transition-all cursor-pointer ${
              !isLiveTime
                ? 'bg-cyan-500 text-black font-bold shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            VARIABLE SCRUB
          </button>
        </div>
      </div>

      {/* Main Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Primary Beta Value */}
        <div className="bg-[#05070a] border border-[#1e293b] p-4 rounded-2xl flex flex-col justify-between relative overflow-hidden">
          <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 uppercase">
            <span>Current Beta Angle (β)</span>
            <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${
              isContinuousSun
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                : 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
            }`}>
              {isContinuousSun ? 'FULL SUNLIGHT' : 'ECLIPSE CYCLING'}
            </span>
          </div>

          <div className="my-2 flex items-baseline gap-2">
            <span className="text-3xl font-mono font-bold text-amber-400">
              {isPositive ? '+' : ''}{beta.toFixed(2)}°
            </span>
            <span className="text-xs font-mono text-slate-400 flex items-center">
              {solarBetaData.dailyDriftDeg >= 0 ? (
                <ArrowUpRight size={14} className="text-emerald-400" />
              ) : (
                <ArrowDownRight size={14} className="text-rose-400" />
              )}
              {Math.abs(solarBetaData.dailyDriftDeg).toFixed(2)}°/day
            </span>
          </div>

          <span className="text-[10px] font-mono text-slate-400">
            Critical Threshold β*: ±{crit.toFixed(1)}°
          </span>
        </div>

        {/* Eclipse vs Sunlit Duration */}
        <div className="bg-[#05070a] border border-[#1e293b] p-4 rounded-2xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 uppercase">
            <span>Orbit Eclipse Duration</span>
            <span className="text-slate-300 font-mono">T = {solarBetaData.orbitPeriodMin.toFixed(1)}m</span>
          </div>

          <div className="my-2 flex items-baseline gap-2">
            <span className="text-3xl font-mono font-bold text-white">
              {solarBetaData.eclipseDurationMin.toFixed(1)}
              <span className="text-sm font-normal text-slate-400 ml-1">min</span>
            </span>
            <span className="text-xs font-mono text-slate-400">
              / {(solarBetaData.sunlitFraction * 100).toFixed(0)}% Sunlit
            </span>
          </div>

          <div className="w-full bg-[#1e293b] h-2 rounded-full overflow-hidden flex">
            <div
              className="bg-amber-400 h-full"
              style={{ width: `${solarBetaData.sunlitFraction * 100}%` }}
              title="Sunlit fraction"
            />
            <div
              className="bg-rose-500 h-full"
              style={{ width: `${(1 - solarBetaData.sunlitFraction) * 100}%` }}
              title="Umbral shadow fraction"
            />
          </div>
        </div>

        {/* Nodal Precession & Sun Coordinates */}
        <div className="bg-[#05070a] border border-[#1e293b] p-4 rounded-2xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 uppercase">
            <span>Orbital Precession</span>
            <span className="text-cyan-400 font-mono">J2 FIELD</span>
          </div>

          <div className="my-1 space-y-1 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-slate-400">RAAN (Ω):</span>
              <span className="text-white font-bold">{solarBetaData.raanDeg.toFixed(1)}°</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Sun Dec (δ☉):</span>
              <span className="text-amber-300 font-bold">{solarBetaData.sunDeclinationDeg > 0 ? '+' : ''}{solarBetaData.sunDeclinationDeg.toFixed(1)}°</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Nodal Rate:</span>
              <span className="text-emerald-400 font-bold">{solarBetaData.nodalPrecessionDegPerDay.toFixed(2)}°/day</span>
            </div>
          </div>

          <span className="text-[9px] font-mono text-slate-500">
            Epoch: {solarBetaData.currentUtcIso.substring(0, 19).replace('T', ' ')} UTC
          </span>
        </div>
      </div>

      {/* Beta Arc Range Visualizer */}
      <div className="bg-[#05070a] border border-[#1e293b] p-4 rounded-2xl flex flex-col gap-2">
        <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 uppercase">
          <span>Beta Arc Range Spectrum (-90° to +90°)</span>
          <span>{isContinuousSun ? 'Full Sunlit Orbit (No Eclipse)' : 'Partial Shadow Traversal'}</span>
        </div>

        {/* Range Bar */}
        <div className="relative h-6 w-full bg-[#1e293b] rounded-lg overflow-hidden flex items-center">
          {/* Eclipse Region in center (-crit to +crit) */}
          <div
            className="absolute top-0 bottom-0 bg-cyan-950/80 border-x border-cyan-500/40"
            style={{
              left: `${critLowerPercent}%`,
              width: `${critUpperPercent - critLowerPercent}%`,
            }}
          />

          {/* Zero Center Line */}
          <div className="absolute top-0 bottom-0 left-1/2 w-0.5 bg-slate-600 z-0" />

          {/* Current Value Marker Pin */}
          <div
            className="absolute top-0 bottom-0 w-2.5 bg-amber-400 shadow-lg shadow-amber-400/50 rounded-sm z-10 transition-all duration-75"
            style={{
              left: `calc(${Math.max(2, Math.min(98, betaPercent))}% - 5px)`,
            }}
          />
        </div>

        <div className="flex justify-between text-[9px] font-mono text-slate-500 pt-0.5">
          <span>-90° (Sun Overhead South)</span>
          <span className="text-slate-400">-67.2° [β*]</span>
          <span className="text-slate-300 font-bold">0° (Coplanar with Sun)</span>
          <span className="text-slate-400">+67.2° [β*]</span>
          <span>+90° (Sun Overhead North)</span>
        </div>
      </div>

      {/* Variable Beta Scrub Slider (when not locked to live UTC) */}
      {!isLiveTime && (
        <div className="bg-cyan-500/10 border border-cyan-500/30 p-4 rounded-2xl flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              <span className="text-xs font-mono font-bold text-cyan-300 uppercase">
                Variable Beta Simulator / Seasonal Scrub
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={toggleAutoCycle}
                className="px-2.5 py-1 text-[10px] font-mono rounded-lg bg-cyan-500 text-black font-bold uppercase flex items-center gap-1 cursor-pointer hover:bg-cyan-400 transition-colors"
              >
                {isAutoCycling ? <Pause size={12} /> : <Play size={12} />}
                {isAutoCycling ? 'Pause Cycle' : 'Auto Sweep Beta'}
              </button>
              <button
                onClick={onResetToLive}
                className="px-2.5 py-1 text-[10px] font-mono rounded-lg bg-[#0f172a] text-slate-300 border border-[#1e293b] hover:text-white cursor-pointer"
              >
                Reset to Live UTC
              </button>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-[10px] font-mono text-slate-400 whitespace-nowrap">
              Epoch Offset: <strong className="text-white">+{manualDayOffset.toFixed(1)} Days</strong>
            </span>
            <input
              type="range"
              min="0"
              max="60"
              step="0.2"
              value={manualDayOffset}
              onChange={(e) => onManualDayOffsetChange(parseFloat(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer"
            />
            <span className="text-[10px] font-mono text-cyan-400 font-bold whitespace-nowrap">
              β: {beta > 0 ? '+' : ''}{beta.toFixed(1)}°
            </span>
          </div>

          <p className="text-[11px] text-slate-300 leading-relaxed">
            Drag the scrub slider to simulate how the satellite's orbital plane regresses relative to the Sun over weeks. Watch how the beta angle transitions from deep shadow crossings (β ≈ 0°) to 100% full continuous sunlight (β &gt; +67°), altering onboard thermal loads and solar array power!
          </p>
        </div>
      )}
    </div>
  );
};
