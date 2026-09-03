import React from 'react';
import { SolarBetaData } from '../utils/orbitalCalculations';
import { sound } from '../utils/audio';
import { Sun, Moon, Calendar, RefreshCw, Sliders, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { VideogameLoadingSlider } from './VideogameLoadingSlider';

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
  const {
    betaDeg,
    criticalBetaDeg,
    isCurrentlyInShadow,
    raanDeg,
    orbitPeriodMin,
    sunlitPercent,
    eclipseDurationMin,
  } = solarBetaData;

  const isFullSunlight = Math.abs(betaDeg) >= criticalBetaDeg;

  // Scale betaDeg (-90 to +90) to 0% to 100% on the slider track
  const betaPercent = Math.max(0, Math.min(100, ((betaDeg + 90) / 180) * 100));
  const critNegativePercent = ((-criticalBetaDeg + 90) / 180) * 100;
  const critPositivePercent = ((criticalBetaDeg + 90) / 180) * 100;

  return (
    <div className="bg-[#0f172a] border border-[#1e293b] p-5 rounded-3xl flex flex-col gap-4 shadow-xl hover:border-cyan-500/30 transition-all">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1e293b] pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400">
            <Sun size={18} />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-amber-400">
                SOLAR BETA (β) MONITOR //
              </span>
              <span className="text-xs uppercase text-slate-100 font-semibold">
                Real-Time Astronomical Solar Ephemeris & Orbit Illumination
              </span>
              <span
                className={`px-2 py-0.5 rounded-full text-[9px] font-mono font-bold border ${
                  isFullSunlight
                    ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                    : 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30'
                }`}
              >
                {isFullSunlight ? 'FULL SUNLIGHT REGIME' : 'ECLIPSING ORBIT'}
              </span>
            </div>
            <span className="font-mono text-[10px] text-slate-400">
              ORBIT-SUN ANGLE · CRITICAL THRESHOLD ±{criticalBetaDeg.toFixed(1)}° · UMBRA OCCULTATION
            </span>
          </div>
        </div>

        {/* Live Synchronization Switcher */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <div className="flex items-center bg-[#05070a] p-1 rounded-xl border border-[#1e293b]">
            <button
              onClick={() => {
                sound.playClick();
                onToggleLiveTime(true);
                onResetToLive();
              }}
              className={`px-3 py-1 rounded-lg text-[10px] uppercase font-bold cursor-pointer transition-all flex items-center gap-1.5 ${
                isLiveTime
                  ? 'bg-green-500 text-black shadow-xs'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  isLiveTime ? 'bg-black animate-pulse' : 'bg-slate-500'
                }`}
              />
              LIVE IST SYNC
            </button>
            <button
              onClick={() => {
                sound.playClick();
                onToggleLiveTime(false);
              }}
              className={`px-3 py-1 rounded-lg text-[10px] uppercase font-bold cursor-pointer transition-all flex items-center gap-1.5 ${
                !isLiveTime
                  ? 'bg-cyan-500 text-black shadow-xs'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Sliders size={11} />
              SEASONAL SIM
            </button>
          </div>

          {!isLiveTime && (
            <button
              onClick={onResetToLive}
              className="p-1.5 rounded-lg bg-[#05070a] border border-[#1e293b] text-slate-400 hover:text-white cursor-pointer transition-colors"
              title="Reset to Live IST"
            >
              <RefreshCw size={13} />
            </button>
          )}
        </div>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
        {/* Metric 1: Beta Angle */}
        <div className="bg-[#05070a] p-3.5 rounded-2xl border border-[#1e293b] flex flex-col justify-between shadow-xs">
          <div className="flex items-center justify-between text-slate-400 text-[10px]">
            <span>SOLAR BETA ANGLE (β)</span>
            <span className="text-amber-400 font-bold">ARC-DEG</span>
          </div>
          <div className="text-xl font-bold text-amber-300 my-1">
            {betaDeg > 0 ? '+' : ''}
            {betaDeg.toFixed(2)}°
          </div>
          <div className="text-[9.5px] text-slate-400">
            Critical Threshold: ±{criticalBetaDeg.toFixed(1)}°
          </div>
        </div>

        {/* Metric 2: Orbit Illumination */}
        <div className="bg-[#05070a] p-3.5 rounded-2xl border border-[#1e293b] flex flex-col justify-between shadow-xs">
          <div className="flex items-center justify-between text-slate-400 text-[10px]">
            <span>SUNLIT FRACTION</span>
            <span className="text-green-400 font-bold">PER PERIOD</span>
          </div>
          <div className="text-xl font-bold text-slate-100 my-1">
            {sunlitPercent}%
          </div>
          <div className="text-[9.5px] text-slate-400">
            {(orbitPeriodMin - eclipseDurationMin).toFixed(1)}m of {orbitPeriodMin}m orbit
          </div>
        </div>

        {/* Metric 3: Eclipse Duration */}
        <div className="bg-[#05070a] p-3.5 rounded-2xl border border-[#1e293b] flex flex-col justify-between shadow-xs">
          <div className="flex items-center justify-between text-slate-400 text-[10px]">
            <span>ECLIPSE UMBRA TIME</span>
            <span className="text-rose-400 font-bold">BATTERY DRAW</span>
          </div>
          <div className="text-xl font-bold text-rose-400 my-1">
            {eclipseDurationMin} min
          </div>
          <div className="text-[9.5px] text-slate-400">
            {isFullSunlight ? '0m (Full Daylight)' : 'Penumbra / Umbra transit'}
          </div>
        </div>

        {/* Metric 4: RAAN */}
        <div className="bg-[#05070a] p-3.5 rounded-2xl border border-[#1e293b] flex flex-col justify-between shadow-xs">
          <div className="flex items-center justify-between text-slate-400 text-[10px]">
            <span>ORBIT NODE (RAAN Ω)</span>
            <span className="text-cyan-400 font-bold">PRECESSION</span>
          </div>
          <div className="text-xl font-bold text-cyan-300 my-1">
            {raanDeg.toFixed(1)}°
          </div>
          <div className="text-[9.5px] text-slate-400">
            Drift: +0.9856°/day (SSO)
          </div>
        </div>
      </div>

      {/* Interactive Visual Beta Angle Arc Track */}
      <div className="bg-[#05070a] p-4 rounded-2xl border border-[#1e293b] flex flex-col gap-2">
        <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
          <span>-90° (South Solar Pole)</span>
          <span className="text-amber-300 font-bold">
            CURRENT β: {betaDeg > 0 ? '+' : ''}{betaDeg.toFixed(2)}°
          </span>
          <span>+90° (North Solar Pole)</span>
        </div>

        {/* Scale Gauge Track */}
        <div className="relative h-6 w-full bg-[#0f172a] rounded-xl border border-[#1e293b] overflow-hidden flex items-center">
          {/* Shaded Eclipsing Center Band */}
          <div
            className="absolute top-0 bottom-0 bg-rose-500/15 border-x border-rose-500/40"
            style={{
              left: `${critNegativePercent}%`,
              width: `${critPositivePercent - critNegativePercent}%`,
            }}
          />

          {/* Center 0° line */}
          <div className="absolute top-0 bottom-0 left-1/2 w-0.5 bg-slate-600"></div>

          {/* Left Critical Threshold Marker */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-amber-400/80"
            style={{ left: `${critNegativePercent}%` }}
          />

          {/* Right Critical Threshold Marker */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-amber-400/80"
            style={{ left: `${critPositivePercent}%` }}
          />

          {/* Current Solar Beta Indicator Needle */}
          <div
            className="absolute top-0 bottom-0 w-3 -ml-1.5 flex items-center justify-center transition-all duration-150"
            style={{ left: `${betaPercent}%` }}
          >
            <div className="w-2.5 h-full bg-amber-400 rounded-sm shadow-[0_0_10px_rgba(251,191,36,0.8)]"></div>
          </div>
        </div>

        <div className="flex justify-between items-center text-[9px] font-mono text-slate-400 px-1">
          <span>Full Sun (|β| &gt; 67.2°)</span>
          <span className="text-rose-400">Eclipsing Zone (-67.2° &lt; β &lt; +67.2°)</span>
          <span>Full Sun (|β| &gt; 67.2°)</span>
        </div>
      </div>

      {/* Seasonal Slider for Simulation Mode */}
      {!isLiveTime && (
        <div className="bg-[#05070a] p-3.5 rounded-2xl border border-yellow-500/30 flex flex-col gap-2 font-mono text-xs">
          <div className="flex justify-between items-center">
            <span className="text-yellow-400 font-bold flex items-center gap-1.5">
              <Calendar size={13} />
              SEASONAL EPOCH OFFSET: {manualDayOffset >= 0 ? '+' : ''}{manualDayOffset} DAYS
            </span>
            <span className="text-slate-400 text-[10px]">
              SOLSTICE / EQUINOX PREVIEW SLIDER
            </span>
          </div>
          <VideogameLoadingSlider
            id="seasonal-epoch-slider"
            min={-182}
            max={182}
            step={1}
            value={manualDayOffset}
            onChange={(val) => onManualDayOffsetChange(val)}
            ticks={[
              { value: -182, label: '-6 Mo (Winter)' },
              { value: 0, label: '0 Days (Present)' },
              { value: 182, label: '+6 Mo (Summer)' },
            ]}
            ariaLabel="Seasonal Epoch Offset"
          />
        </div>
      )}
    </div>
  );
};
