import React, { useState, useEffect, useRef } from 'react';
import { TwinLayer, AgentStatus, ActiveScreen } from '../types';
import { sound } from '../utils/audio';
import {
  RotateCw,
  RotateCcw,
  RefreshCw,
  ZoomIn,
  ZoomOut,
  AlertCircle,
  ArrowRight,
  ShieldCheck,
  Globe,
  Box,
  Columns,
} from 'lucide-react';
import { EarthOrbitalTwin3D } from './EarthOrbitalTwin3D';
import { SolarBetaMonitor } from './SolarBetaMonitor';
import { calculateSolarBeta, SolarBetaData, PHYSICAL_ORBITAL_VELOCITY_KM_S } from '../utils/orbitalCalculations';

interface OrbitalTwinScreenProps {
  agents: AgentStatus[];
  onSelectScreen: (screen: ActiveScreen) => void;
  onSelectPreset?: (presetId: string) => void;
  activeAnomalySeverity?: number;
  activeAnomalyPresetId?: string | null;
}

export const OrbitalTwinScreen: React.FC<OrbitalTwinScreenProps> = ({
  agents,
  onSelectScreen,
  onSelectPreset,
  activeAnomalySeverity = 0,
  activeAnomalyPresetId = null,
}) => {
  // Digital Twin View Mode: 3D Earth Orbit vs Detailed Bus CAD vs Split
  const [twinViewMode, setTwinViewMode] = useState<'earth-orbit' | 'bus-cad' | 'split'>('earth-orbit');

  // Real-Life Live Time Monitoring & Variable Solar Beta State
  const [isLiveTime, setIsLiveTime] = useState<boolean>(true);
  const [liveDate, setLiveDate] = useState<Date>(() => new Date());
  const [manualDayOffset, setManualDayOffset] = useState<number>(0);
  const [solarBetaData, setSolarBetaData] = useState<SolarBetaData>(() =>
    calculateSolarBeta(new Date())
  );

  // CAD State for Bus close-up
  const [activeLayer, setActiveLayer] = useState<TwinLayer>('wireframe');
  const [rotationAngle, setRotationAngle] = useState({ yaw: 25, pitch: -15 });
  const [zoomLevel, setZoomLevel] = useState(1);
  const [selectedCallout, setSelectedCallout] = useState<string | null>(null);
  const [showOrbitVectors, setShowOrbitVectors] = useState(true);
  const [showTelemetryVectors, setShowTelemetryVectors] = useState(true);

  // Drag interaction on CAD
  const isDraggingRef = useRef(false);
  const lastMousePosRef = useRef({ x: 0, y: 0 });

  // Ground track live animation
  const [satellitePosition, setSatellitePosition] = useState({ lat: 24.5, lon: -42.8 });
  const [aosSeconds, setAosSeconds] = useState(384);

  // Sparkline history for battery temp
  const [batteryHistory, setBatteryHistory] = useState<number[]>([
    21.1, 21.2, 21.2, 21.3, 21.2, 21.4, 21.3, 21.2, 21.3, 21.2, 21.4, 21.3, 21.2, 21.5, 21.3,
  ]);

  // Live simulation & real-time astronomical ephemeris tick
  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      setLiveDate(now);

      const targetDate = isLiveTime
        ? now
        : new Date(now.getTime() + manualDayOffset * 86400 * 1000);
      setSolarBetaData(calculateSolarBeta(targetDate));

      // Advance AOS countdown
      setAosSeconds((prev) => (prev > 1 ? prev - 1 : 420));

      // Advance satellite ground position along inclined orbit
      setSatellitePosition((prev) => {
        let newLon = prev.lon + 0.35;
        if (newLon > 180) newLon = -180;
        const newLat = 70 * Math.sin((newLon * Math.PI) / 90);
        return { lat: newLat, lon: newLon };
      });

      // Update battery history
      setBatteryHistory((prev) => {
        const baseTemp = activeAnomalyPresetId === 'thermal' ? 21.2 + (activeAnomalySeverity * 6.5) : 21.2;
        const jitter = (Math.random() - 0.5) * 0.4;
        const nextVal = Math.round((baseTemp + jitter) * 10) / 10;
        return [...prev.slice(1), nextVal];
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isLiveTime, manualDayOffset, activeAnomalyPresetId, activeAnomalySeverity]);

  const handleManualDayOffsetChange = (days: number) => {
    setManualDayOffset(days);
    const targetDate = new Date(liveDate.getTime() + days * 86400 * 1000);
    setSolarBetaData(calculateSolarBeta(targetDate));
  };

  const handleResetToLive = () => {
    sound.playClick();
    setIsLiveTime(true);
    setManualDayOffset(0);
    const now = new Date();
    setLiveDate(now);
    setSolarBetaData(calculateSolarBeta(now));
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    isDraggingRef.current = true;
    lastMousePosRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDraggingRef.current) return;
    const deltaX = e.clientX - lastMousePosRef.current.x;
    const deltaY = e.clientY - lastMousePosRef.current.y;
    lastMousePosRef.current = { x: e.clientX, y: e.clientY };

    setRotationAngle((prev) => ({
      yaw: (prev.yaw + deltaX * 0.8) % 360,
      pitch: Math.max(-60, Math.min(60, prev.pitch - deltaY * 0.5)),
    }));
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `T-${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  const getMapCoords = (lat: number, lon: number) => {
    const x = ((lon + 180) / 360) * 100;
    const y = ((90 - lat) / 180) * 100;
    return { x: Math.max(2, Math.min(98, x)), y: Math.max(5, Math.min(95, y)) };
  };

  const satCoords = getMapCoords(satellitePosition.lat, satellitePosition.lon);

  const stations = [
    { name: 'Svalbard [SG-1]', lat: 78.2, lon: 15.6, active: true },
    { name: 'Fairbanks [FB-3]', lat: 64.8, lon: -147.7, active: false },
    { name: 'McMurdo [MC-2]', lat: -77.8, lon: 166.6, active: false },
  ];

  return (
    <div className="w-full flex flex-col gap-4">
      {/* Top Status Strip */}
      <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-wrap items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center gap-3">
          <span className="w-2.5 h-2.5 rounded-full bg-green-400 animate-ping"></span>
          <div className="flex flex-col">
            <span className="font-bold text-sm text-white tracking-wide flex items-center gap-2">
              ASTRA-7 NORAD ID 59421
              <span className="px-2 py-0.5 text-[9px] rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-mono">
                TLE-2026.142
              </span>
            </span>
            <span className="font-mono text-[10px] text-slate-400">
              PROPAGATOR: SGP4 PRECISION ORBIT FILTER · SYNCHRONIZED
            </span>
          </div>
        </div>

        <div className="flex items-center flex-wrap gap-6 text-xs font-mono">
          <div className="flex flex-col">
            <span className="text-[10px] text-slate-400">ALTITUDE (MSL)</span>
            <span className="text-cyan-400 font-bold">541.80 km</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] text-slate-400">VELOCITY</span>
            <span className="text-slate-200 font-semibold">{PHYSICAL_ORBITAL_VELOCITY_KM_S.toFixed(3)} km/s (Mach 22.3)</span>
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-slate-400">SOLAR BETA (β)</span>
              {isLiveTime ? (
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" title="Real-time live UTC synchronization" />
              ) : (
                <span className="px-1 text-[8px] bg-cyan-500/20 text-cyan-300 font-bold rounded">SIM</span>
              )}
            </div>
            <span className="text-amber-400 font-semibold flex items-center gap-1">
              {solarBetaData.betaDeg > 0 ? '+' : ''}{solarBetaData.betaDeg.toFixed(2)}°
              <span className="text-[9px] text-slate-300 font-normal">
                [{solarBetaData.isCurrentlyInShadow ? 'UMBRA' : 'SUNLIT'}]
              </span>
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] text-slate-400">BATTERY SOC</span>
            <span className="text-green-400 font-bold">98.2% [28.4V REG]</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] text-slate-400">OPERATING MODE</span>
            <span className="text-cyan-300 font-bold">SCI-OBS // HYPERSPEC</span>
          </div>
        </div>
      </div>

      {/* Main Grid: CAD Digital Twin on Left / Ground Track & Subsystems on Right */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
        {/* Left: Interactive CAD Digital Twin */}
        <div className="xl:col-span-7 bg-[#0f172a] border border-[#1e293b] rounded-3xl flex flex-col overflow-hidden relative shadow-xl hover:border-cyan-500/30 transition-all">
          <div className="p-4 border-b border-[#1e293b] flex flex-wrap items-center justify-between gap-3 bg-[#0a1120]/80">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-cyan-400">CAD-7 //</span>
              <span className="font-semibold text-xs uppercase text-slate-200">
                Digital Twin Wireframe
              </span>
              <span className={`text-[9px] px-2 py-0.5 rounded-full font-mono font-bold border ${
                twinViewMode === 'earth-orbit'
                  ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                  : 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30'
              }`}>
                {twinViewMode === 'earth-orbit'
                  ? '3D EARTH ORBIT (ANIMATED)'
                  : twinViewMode === 'bus-cad'
                  ? 'BUS SUBSYSTEM CAD'
                  : 'DUAL VIEW'}
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center bg-[#05070a] p-1 rounded-xl border border-[#1e293b]">
                <button
                  onClick={() => {
                    sound.playClick();
                    setTwinViewMode('earth-orbit');
                  }}
                  className={`px-2.5 py-1 text-[10px] font-mono uppercase rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${
                    twinViewMode === 'earth-orbit'
                      ? 'bg-emerald-500 text-black font-bold shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Globe size={13} />
                  3D EARTH ORBIT
                </button>
                <button
                  onClick={() => {
                    sound.playClick();
                    setTwinViewMode('bus-cad');
                  }}
                  className={`px-2.5 py-1 text-[10px] font-mono uppercase rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${
                    twinViewMode === 'bus-cad'
                      ? 'bg-cyan-500 text-black font-bold shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Box size={13} />
                  BUS CAD
                </button>
                <button
                  onClick={() => {
                    sound.playClick();
                    setTwinViewMode('split');
                  }}
                  className={`px-2.5 py-1 text-[10px] font-mono uppercase rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${
                    twinViewMode === 'split'
                      ? 'bg-cyan-500 text-black font-bold shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Columns size={13} />
                  DUAL
                </button>
              </div>

              {(twinViewMode === 'bus-cad' || twinViewMode === 'split') && (
                <div className="flex items-center bg-[#05070a] p-1 rounded-xl border border-[#1e293b]">
                  {(
                    [
                      { id: 'wireframe', label: 'STRUCT' },
                      { id: 'thermal', label: 'THERM' },
                      { id: 'mag', label: 'B-FLD' },
                      { id: 'power', label: 'BUS' },
                    ] as const
                  ).map((layer) => (
                    <button
                      key={layer.id}
                      onClick={() => {
                        sound.playClick();
                        setActiveLayer(layer.id);
                      }}
                      className={`px-2 py-1 text-[10px] font-mono uppercase rounded-lg transition-all cursor-pointer ${
                        activeLayer === layer.id
                          ? 'bg-cyan-500 text-black font-bold shadow-sm'
                          : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      {layer.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* 3D Earth Orbit Viewport */}
          {(twinViewMode === 'earth-orbit' || twinViewMode === 'split') && (
            <div className="w-full">
              <EarthOrbitalTwin3D
                currentDate={isLiveTime ? liveDate : new Date(liveDate.getTime() + manualDayOffset * 86400 * 1000)}
                solarBetaData={solarBetaData}
                activeAnomalyPresetId={activeAnomalyPresetId}
                activeAnomalySeverity={activeAnomalySeverity}
              />
            </div>
          )}

          {/* Bus CAD Subsystem Viewport */}
          {(twinViewMode === 'bus-cad' || twinViewMode === 'split') && (
            <div className="w-full relative border-t border-[#1e293b]/80">
              {twinViewMode === 'split' && (
                <div className="bg-[#05070a] px-4 py-1.5 border-b border-[#1e293b] flex items-center justify-between text-[10px] font-mono text-slate-400">
                  <span className="flex items-center gap-1.5 text-cyan-400 font-bold">
                    <Box size={12} /> SATELLITE CHASSIS CAD // {activeLayer.toUpperCase()} SUBSYSTEMS
                  </span>
                  <span>DRAG TO ROTATE 3D SATELLITE WIREFRAME</span>
                </div>
              )}
              <div
                className="relative h-[380px] sm:h-[420px] w-full bg-gradient-to-b from-[#05070a] via-[#0a1120] to-[#05070a] select-none cursor-grab active:cursor-grabbing overflow-hidden flex items-center justify-center"
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
              >
                <div
                  className="absolute inset-0 opacity-15 pointer-events-none"
                  style={{
                    backgroundImage:
                      'linear-gradient(to right, #4cd7f6 1px, transparent 1px), linear-gradient(to bottom, #4cd7f6 1px, transparent 1px)',
                    backgroundSize: '32px 32px',
                  }}
                />

                {showOrbitVectors && (
                  <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-40">
                    <ellipse
                      cx="50%"
                      cy="50%"
                      rx="220"
                      ry="90"
                      fill="none"
                      stroke="#4cd7f6"
                      strokeWidth="1"
                      strokeDasharray="4 4"
                      transform={`rotate(${rotationAngle.pitch}, 250, 230)`}
                    />
                    <ellipse
                      cx="50%"
                      cy="50%"
                      rx="280"
                      ry="120"
                      fill="none"
                      stroke="#4edea3"
                      strokeWidth="0.8"
                      strokeDasharray="8 4"
                      transform={`rotate(${rotationAngle.yaw * 0.2}, 250, 230)`}
                    />
                  </svg>
                )}

                <div
                  className="transition-transform duration-75"
                  style={{
                    transform: `scale(${zoomLevel}) rotateX(${rotationAngle.pitch}deg) rotateY(${rotationAngle.yaw}deg)`,
                    transformStyle: 'preserve-3d',
                  }}
                >
                  <svg width="420" height="340" viewBox="0 0 420 340" className="overflow-visible">
                    <defs>
                      <linearGradient id="busGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop
                          offset="0%"
                          stopColor={
                            activeLayer === 'thermal'
                              ? '#ffb4ab'
                              : activeLayer === 'power'
                              ? '#ffb95f'
                              : activeLayer === 'mag'
                              ? '#4edea3'
                              : '#4cd7f6'
                          }
                          stopOpacity="0.8"
                        />
                        <stop offset="100%" stopColor="#051424" stopOpacity="0.9" />
                      </linearGradient>

                      <linearGradient id="solarGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.8" />
                        <stop offset="50%" stopColor="#010f1f" stopOpacity="0.9" />
                        <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.8" />
                      </linearGradient>

                      <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                        <feGaussianBlur stdDeviation="3" result="blur" />
                        <feComposite in="SourceGraphic" in2="blur" operator="over" />
                      </filter>
                    </defs>

                    {/* Left Solar Wing */}
                    <g id="solar-left" className="cursor-pointer" onClick={() => setSelectedCallout('solar-left')}>
                      <rect
                        x="20"
                        y="130"
                        width="120"
                        height="70"
                        fill="url(#solarGrad)"
                        stroke="#4cd7f6"
                        strokeWidth="1.5"
                        rx="3"
                      />
                      <line x1="60" y1="130" x2="60" y2="200" stroke="#4cd7f6" strokeWidth="0.8" strokeDasharray="2 2" />
                      <line x1="100" y1="130" x2="100" y2="200" stroke="#4cd7f6" strokeWidth="0.8" strokeDasharray="2 2" />
                      <line x1="20" y1="165" x2="140" y2="165" stroke="#4cd7f6" strokeWidth="0.8" />
                      <line x1="140" y1="165" x2="175" y2="165" stroke="#869397" strokeWidth="3" />
                    </g>

                    {/* Right Solar Wing */}
                    <g id="solar-right" className="cursor-pointer" onClick={() => setSelectedCallout('solar-right')}>
                      <rect
                        x="280"
                        y="130"
                        width="120"
                        height="70"
                        fill="url(#solarGrad)"
                        stroke="#4cd7f6"
                        strokeWidth="1.5"
                        rx="3"
                      />
                      <line x1="320" y1="130" x2="320" y2="200" stroke="#4cd7f6" strokeWidth="0.8" strokeDasharray="2 2" />
                      <line x1="360" y1="130" x2="360" y2="200" stroke="#4cd7f6" strokeWidth="0.8" strokeDasharray="2 2" />
                      <line x1="280" y1="165" x2="400" y2="165" stroke="#4cd7f6" strokeWidth="0.8" />
                      <line x1="245" y1="165" x2="280" y2="165" stroke="#869397" strokeWidth="3" />
                    </g>

                    {/* Central Bus Chassis */}
                    <g id="satellite-core">
                      <polygon
                        points="210,90 250,115 210,140 170,115"
                        fill="#1c2b3c"
                        stroke={activeLayer === 'thermal' ? '#ffb4ab' : '#4cd7f6'}
                        strokeWidth="1.5"
                      />
                      <polygon
                        points="170,115 210,140 210,210 170,185"
                        fill="url(#busGrad)"
                        stroke={activeLayer === 'thermal' ? '#ffb4ab' : '#4cd7f6'}
                        strokeWidth="1.5"
                      />
                      <polygon
                        points="210,140 250,115 250,185 210,210"
                        fill="#122131"
                        stroke={activeLayer === 'thermal' ? '#ffb4ab' : '#4cd7f6'}
                        strokeWidth="1.5"
                      />

                      {activeLayer === 'thermal' && (
                        <g filter="url(#glow)">
                          <circle cx="190" cy="160" r="14" fill="#ffb4ab" fillOpacity="0.4" stroke="#ffb4ab" />
                          <path d="M 190 145 Q 210 160 210 190" fill="none" stroke="#ffb4ab" strokeWidth="2" strokeDasharray="3 3" />
                          <text x="175" y="195" fill="#ffb4ab" fontSize="9" fontFamily="monospace">LOOP #1 CRIT</text>
                        </g>
                      )}

                      {activeLayer === 'mag' && (
                        <g filter="url(#glow)">
                          <ellipse cx="210" cy="160" rx="45" ry="30" fill="none" stroke="#4edea3" strokeWidth="1.5" strokeDasharray="4 2" />
                          <ellipse cx="210" cy="160" rx="70" ry="45" fill="none" stroke="#4edea3" strokeWidth="1" strokeDasharray="6 4" opacity="0.6" />
                        </g>
                      )}

                      {activeLayer === 'power' && (
                        <g filter="url(#glow)">
                          <line x1="140" y1="165" x2="190" y2="160" stroke="#ffb95f" strokeWidth="2" strokeDasharray="4 2" />
                          <line x1="280" y1="165" x2="230" y2="160" stroke="#ffb95f" strokeWidth="2" strokeDasharray="4 2" />
                          <circle cx="210" cy="160" r="8" fill="#ffb95f" opacity="0.8" />
                          <text x="180" y="225" fill="#ffb95f" fontSize="9" fontFamily="monospace">28.4V REG BUS</text>
                        </g>
                      )}

                      <ellipse cx="210" cy="70" rx="28" ry="12" fill="#0d1c2d" stroke="#acedff" strokeWidth="1.5" />
                      <line x1="210" y1="70" x2="210" y2="90" stroke="#acedff" strokeWidth="2" />
                      <circle cx="210" cy="58" r="3" fill="#4cd7f6" />

                      <polygon points="166,112 160,108 162,118" fill="#ffb95f" stroke="#ffb95f" />
                      <polygon points="254,112 260,108 258,118" fill="#ffb95f" stroke="#ffb95f" />
                      <polygon points="166,188 160,192 162,182" fill="#ffb95f" stroke="#ffb95f" />
                      <polygon points="254,188 260,192 258,182" fill="#ffb95f" stroke="#ffb95f" />
                    </g>

                    {showTelemetryVectors && (
                      <>
                        <g
                          className="cursor-pointer"
                          onClick={() => setSelectedCallout('solar')}
                          transform="translate(60, 95)"
                        >
                          <line x1="20" y1="35" x2="20" y2="15" stroke="#4cd7f6" strokeWidth="1" strokeDasharray="2 2" />
                          <rect x="0" y="0" width="105" height="20" rx="3" fill="#010f1f" stroke="#4cd7f6" strokeWidth="1" />
                          <text x="6" y="14" fill="#4cd7f6" fontSize="9" fontFamily="monospace" fontWeight="bold">
                            SOLAR α // 2,420W
                          </text>
                        </g>

                        <g
                          className="cursor-pointer"
                          onClick={() => setSelectedCallout('antenna')}
                          transform="translate(250, 35)"
                        >
                          <line x1="0" y1="25" x2="-25" y2="30" stroke="#acedff" strokeWidth="1" strokeDasharray="2 2" />
                          <rect x="0" y="0" width="115" height="20" rx="3" fill="#010f1f" stroke="#acedff" strokeWidth="1" />
                          <text x="6" y="14" fill="#acedff" fontSize="9" fontFamily="monospace" fontWeight="bold">
                            X-BAND // LOCKED
                          </text>
                        </g>

                        <g
                          className="cursor-pointer"
                          onClick={() => setSelectedCallout('rcs')}
                          transform="translate(270, 220)"
                        >
                          <line x1="0" y1="0" x2="-25" y2="-25" stroke="#ffb95f" strokeWidth="1" strokeDasharray="2 2" />
                          <rect x="0" y="0" width="120" height="20" rx="3" fill="#010f1f" stroke="#ffb95f" strokeWidth="1" />
                          <text x="6" y="14" fill="#ffb95f" fontSize="9" fontFamily="monospace" fontWeight="bold">
                            N2H4 RES // 18.4kg
                          </text>
                        </g>

                        <g
                          className="cursor-pointer"
                          onClick={() => setSelectedCallout('battery')}
                          transform="translate(45, 230)"
                        >
                          <line x1="60" y1="0" x2="135" y2="-40" stroke="#4edea3" strokeWidth="1" strokeDasharray="2 2" />
                          <rect x="0" y="0" width="120" height="20" rx="3" fill="#010f1f" stroke="#4edea3" strokeWidth="1" />
                          <text x="6" y="14" fill="#4edea3" fontSize="9" fontFamily="monospace" fontWeight="bold">
                            CRYO-LOOP // 21.2°C
                          </text>
                        </g>
                      </>
                    )}
                  </svg>
                </div>

                {selectedCallout && (
                  <div className="absolute top-4 left-4 max-w-xs p-3 rounded-2xl bg-[#010f1f]/95 border border-cyan-400 text-xs shadow-xl backdrop-blur-md z-20">
                    <div className="flex items-center justify-between pb-1 border-b border-[#1e293b]">
                      <span className="font-mono text-cyan-400 font-bold uppercase">
                        SUBSYSTEM PIN: {selectedCallout}
                      </span>
                      <button
                        onClick={() => setSelectedCallout(null)}
                        className="text-slate-400 hover:text-white"
                      >
                        ✕
                      </button>
                    </div>
                    <div className="py-2 text-[11px] text-slate-300 space-y-1">
                      {selectedCallout === 'solar' && (
                        <p>Solar Array Drive Assembly (SADA) operating at +14.2° incident angle. High efficiency multi-junction InGaP cells.</p>
                      )}
                      {selectedCallout === 'battery' && (
                        <p>8-cell LiFePO4 battery pack with redundant active heat pipes. Operating margin +12.4°C below safety cutoff.</p>
                      )}
                      {selectedCallout === 'rcs' && (
                        <p>Monopropellant Hydrazine blowdown system. Tank pressure 18.2 bar. Delta-V capability remaining: 44.8 m/s.</p>
                      )}
                      {selectedCallout === 'antenna' && (
                        <p>0.8m parabolic gimbaled reflector pointing to Svalbard ground terminal. EIRP: 34.2 dBW.</p>
                      )}
                    </div>
                    <div className="flex justify-end pt-1">
                      <button
                        onClick={() => {
                          sound.playClick();
                          onSelectScreen('anomaly-lab');
                          if (onSelectPreset) onSelectPreset(selectedCallout === 'battery' ? 'thermal' : 'adcs');
                        }}
                        className="text-[10px] text-amber-400 hover:underline font-mono flex items-center gap-1 cursor-pointer"
                      >
                        Test in Sandbox <ArrowRight size={10} />
                      </button>
                    </div>
                  </div>
                )}

                <div className="absolute bottom-3 right-3 flex items-center gap-1 bg-[#010f1f]/80 p-1 rounded-xl border border-[#1e293b] backdrop-blur-xs">
                  <button
                    onClick={() => {
                      sound.playClick();
                      setRotationAngle((prev) => ({ ...prev, yaw: prev.yaw - 15 }));
                    }}
                    title="Rotate Left -15°"
                    className="p-1 text-slate-400 hover:text-cyan-400 transition-colors cursor-pointer"
                  >
                    <RotateCcw size={14} />
                  </button>
                  <button
                    onClick={() => {
                      sound.playClick();
                      setRotationAngle((prev) => ({ ...prev, yaw: prev.yaw + 15 }));
                    }}
                    title="Rotate Right +15°"
                    className="p-1 text-slate-400 hover:text-cyan-400 transition-colors cursor-pointer"
                  >
                    <RotateCw size={14} />
                  </button>
                  <div className="w-px h-3 bg-[#1e293b]"></div>
                  <button
                    onClick={() => {
                      sound.playClick();
                      setZoomLevel((prev) => Math.min(1.6, prev + 0.15));
                    }}
                    title="Zoom In"
                    className="p-1 text-slate-400 hover:text-cyan-400 transition-colors cursor-pointer"
                  >
                    <ZoomIn size={14} />
                  </button>
                  <button
                    onClick={() => {
                      sound.playClick();
                      setZoomLevel((prev) => Math.max(0.6, prev - 0.15));
                    }}
                    title="Zoom Out"
                    className="p-1 text-slate-400 hover:text-cyan-400 transition-colors cursor-pointer"
                  >
                    <ZoomOut size={14} />
                  </button>
                  <div className="w-px h-3 bg-[#1e293b]"></div>
                  <button
                    onClick={() => {
                      sound.playClick();
                      setRotationAngle({ yaw: 25, pitch: -15 });
                      setZoomLevel(1);
                    }}
                    title="Reset View"
                    className="p-1 text-slate-400 hover:text-cyan-400 transition-colors cursor-pointer"
                  >
                    <RefreshCw size={13} />
                  </button>
                </div>

                <div className="absolute bottom-3 left-3 flex items-center gap-2 text-[10px] font-mono">
                  <button
                    onClick={() => setShowOrbitVectors(!showOrbitVectors)}
                    className={`px-2 py-0.5 rounded-lg border ${
                      showOrbitVectors
                        ? 'border-cyan-400 text-cyan-400 bg-cyan-500/10'
                        : 'border-[#1e293b] text-slate-400'
                    }`}
                  >
                    ORBIT PATH
                  </button>
                  <button
                    onClick={() => setShowTelemetryVectors(!showTelemetryVectors)}
                    className={`px-2 py-0.5 rounded-lg border ${
                      showTelemetryVectors
                        ? 'border-green-400 text-green-400 bg-green-500/10'
                        : 'border-[#1e293b] text-slate-400'
                    }`}
                  >
                    PINS & CALLOUTS
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right: Orbital Ground Track & Telemetry Subsystems */}
        <div className="xl:col-span-5 flex flex-col gap-4">
          {/* Sub-Satellite Orbital Ground Track */}
          <div className="bg-[#0f172a] border border-[#1e293b] rounded-3xl flex flex-col overflow-hidden shadow-xl hover:border-cyan-500/30 transition-all">
            <div className="p-4 border-b border-[#1e293b] flex items-center justify-between bg-[#0a1120]/80">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-green-400">MAP-01 //</span>
                <span className="font-semibold text-xs uppercase text-slate-200">
                  Sub-Satellite Orbital Ground Track
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-green-400 font-bold bg-green-500/10 px-2.5 py-0.5 rounded-full border border-green-500/30 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-ping"></span>
                  AOS {formatTime(aosSeconds)}
                </span>
              </div>
            </div>

            <div className="relative h-[220px] w-full bg-[#05070a] overflow-hidden">
              <img
                alt="Mercator Projection Ground Track Map"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuCHY-XJOeqHXCx6FjdGvlf0-8mGZ-nkZhKC0cOTsJXSJwzBZynvZZK3TcgjwdwUvs5uvR6pQIq-kWvSy6NIA86kInmCqn64hOANVWmydDRZkisP95RQz0qT5n8ZfzEYze3Xfrp7GE_Iwm4xd1ejFZ6O6JiRYJcQ73tBGCZanYIe0P9cPuqaK8EFBWckO_EOgz4Xe8D6JYCIsvnRvNVPtjM6_QLcFUrLGBXpx8Q4h0j6nptSfs308Ayp"
                className="w-full h-full object-cover opacity-65"
              />

              <svg className="absolute inset-0 w-full h-full pointer-events-none">
                <path
                  d="M 0,160 Q 90,40 180,110 T 360,150 T 540,60"
                  fill="none"
                  stroke="#4cd7f6"
                  strokeWidth="1.5"
                  strokeDasharray="4 3"
                  opacity="0.7"
                />

                <path
                  d="M 0,130 Q 90,20 180,90 T 360,130 T 540,40"
                  fill="none"
                  stroke="#4edea3"
                  strokeWidth="1.2"
                  strokeDasharray="2 3"
                  opacity="0.5"
                />

                {stations.map((st, i) => {
                  const pos = getMapCoords(st.lat, st.lon);
                  return (
                    <g key={i} transform={`translate(${pos.x}%, ${pos.y}%)`}>
                      <circle
                        r="16"
                        fill={st.active ? '#4edea3' : '#4cd7f6'}
                        fillOpacity="0.12"
                        stroke={st.active ? '#4edea3' : '#4cd7f6'}
                        strokeWidth="0.8"
                        strokeDasharray="2 2"
                      />
                      <rect x="-2" y="-2" width="4" height="4" fill={st.active ? '#4edea3' : '#d4e4fa'} />
                    </g>
                  );
                })}

                <g style={{ transform: `translate(${satCoords.x}%, ${satCoords.y}%)` }}>
                  <ellipse
                    rx="26"
                    ry="15"
                    fill="#4cd7f6"
                    fillOpacity="0.2"
                    stroke="#4cd7f6"
                    strokeWidth="1"
                    strokeDasharray="3 2"
                  />
                  <polygon
                    points="0,-6 6,0 0,6 -6,0"
                    fill="#4cd7f6"
                    stroke="#ffffff"
                    strokeWidth="1.2"
                  />
                  <circle r="1" fill="#010f1f" />
                </g>
              </svg>

              <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between text-[9px] font-mono text-slate-300 bg-[#05070a]/90 px-3 py-1.5 rounded-xl border border-[#1e293b] backdrop-blur-md">
                <div>
                  POS: <span className="text-cyan-400 font-bold">{satellitePosition.lat.toFixed(1)}°N, {Math.abs(satellitePosition.lon).toFixed(1)}°W</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-400"></span> Svalbard SG-1 (Next Contact)
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Subsystem Telemetry Gauges Strip */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col justify-between shadow-md hover:border-cyan-500/40 transition-colors">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-slate-400 uppercase">
                  BATT CORE TEMP
                </span>
                <span className="text-xs font-mono font-bold text-green-400">
                  {batteryHistory[batteryHistory.length - 1]}°C
                </span>
              </div>
              <div className="h-9 my-1">
                <svg className="w-full h-full overflow-visible" viewBox="0 0 140 30">
                  <polyline
                    fill="none"
                    stroke="#22c55e"
                    strokeWidth="2"
                    points={batteryHistory
                      .map((val, idx) => {
                        const x = (idx / (batteryHistory.length - 1)) * 140;
                        const y = 30 - ((val - 20) / 10) * 30;
                        return `${x},${Math.max(2, Math.min(28, y))}`;
                      })
                      .join(' ')}
                  />
                </svg>
              </div>
              <span className="text-[9px] font-mono text-slate-400">
                Safety margin: +18.8°C nominal
              </span>
            </div>

            <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col justify-between shadow-md hover:border-cyan-500/40 transition-colors">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-slate-400 uppercase">
                  24H DRAG DECAY
                </span>
                <span className="text-xs font-mono font-bold text-cyan-400">
                  -4.2 m / 24h
                </span>
              </div>
              <div className="w-full bg-[#05070a] h-2 rounded-full my-2 overflow-hidden border border-[#1e293b]">
                <div className="bg-cyan-400 h-full rounded-full" style={{ width: '28%' }}></div>
              </div>
              <span className="text-[9px] font-mono text-green-400">
                Auto-Stationkeep Armed
              </span>
            </div>

            <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col justify-between shadow-md hover:border-cyan-500/40 transition-colors">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-slate-400 uppercase">
                  RCS THRUST DUTY
                </span>
                <span className="text-xs font-mono font-bold text-amber-400">
                  0.04%
                </span>
              </div>
              <div className="flex items-center gap-1 my-2">
                {[1, 2, 3, 4, 5, 6, 7, 8].map((seg) => (
                  <div
                    key={seg}
                    className={`h-2 flex-1 rounded-sm ${
                      seg <= 1 ? 'bg-amber-400' : 'bg-[#05070a]'
                    }`}
                  />
                ))}
              </div>
              <span className="text-[9px] font-mono text-slate-400">
                Pulse duration: 50ms min
              </span>
            </div>

            <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col justify-between shadow-md hover:border-cyan-500/40 transition-colors">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-slate-400 uppercase">
                  REG BUS VOLTS
                </span>
                <span className="text-xs font-mono font-bold text-white">
                  28.42 V
                </span>
              </div>
              <div className="text-[11px] font-mono text-green-400 my-1">
                Load: 412 W (96.4% eff)
              </div>
              <span className="text-[9px] font-mono text-slate-400">
                Ripple: 12mV RMS
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Real-Time Live Time Monitoring & Variable Solar Beta Telemetry Console */}
      <SolarBetaMonitor
        solarBetaData={solarBetaData}
        isLiveTime={isLiveTime}
        onToggleLiveTime={setIsLiveTime}
        manualDayOffset={manualDayOffset}
        onManualDayOffsetChange={handleManualDayOffsetChange}
        onResetToLive={handleResetToLive}
      />

      {/* Bottom Section: Active Reasoning Agent Mesh Strip + Sandbox Bento Accent Card */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Agent Cards */}
        <div className="lg:col-span-8 bg-[#0f172a] border border-[#1e293b] p-5 rounded-3xl flex flex-col gap-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-[#1e293b] pb-3">
            <div className="flex items-center gap-2">
              <ShieldCheck size={16} className="text-green-400" />
              <span className="font-semibold text-xs uppercase text-white tracking-wide">
                Autonomous Reasoning Swarm Mesh (4 Nodes Active)
              </span>
            </div>
            <button
              onClick={() => {
                sound.playClick();
                onSelectScreen('agent-mesh');
              }}
              className="text-[11px] font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer transition-colors"
            >
              Inspect Swarm Details <ArrowRight size={12} />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
            {agents.map((agent) => (
              <div
                key={agent.id}
                className="bg-[#05070a] border border-[#1e293b] p-3.5 rounded-2xl flex flex-col justify-between hover:border-cyan-500/40 transition-all shadow-sm"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono text-[10px] font-bold text-cyan-400">
                    {agent.name}
                  </span>
                  <span
                    className={`w-2 h-2 rounded-full ${
                      agent.isolated
                        ? 'bg-rose-500'
                        : agent.state === 'active_correction'
                        ? 'bg-amber-400 animate-pulse'
                        : 'bg-green-400'
                    }`}
                  />
                </div>
                <div className="font-mono text-[9px] text-slate-400 uppercase mb-1">
                  {agent.subsystem}
                </div>
                <div className="text-[10px] text-slate-300 line-clamp-2 mb-2">
                  {agent.description}
                </div>
                <div className="text-[9px] font-mono text-green-400 flex justify-between pt-1 border-t border-[#1e293b]">
                  <span>CONF: {agent.confidence}%</span>
                  <span className="uppercase text-slate-400">{agent.state}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sandbox Callout Card */}
        <div className="lg:col-span-4 bg-gradient-to-br from-cyan-500 via-cyan-400 to-cyan-500 rounded-3xl p-6 text-black shadow-xl shadow-cyan-900/30 flex flex-col justify-between relative overflow-hidden">
          <div
            className="absolute inset-0 opacity-10 pointer-events-none"
            style={{
              backgroundImage:
                'linear-gradient(to right, #000 1px, transparent 1px), linear-gradient(to bottom, #000 1px, transparent 1px)',
              backgroundSize: '20px 20px',
            }}
          />

          <div className="relative z-10">
            <div className="flex items-center gap-2 text-black font-bold mb-2">
              <AlertCircle size={18} />
              <span className="font-mono text-xs uppercase tracking-wider font-extrabold">
                CHAOS & ANOMALY LAB // SANDBOX
              </span>
            </div>
            <p className="text-xs text-slate-900 font-medium leading-relaxed mb-4">
              Stress-test the autonomous satellite digital twin. Inject thermal leaks, attitude desync, and thermospheric drag decay to observe multi-agent closed-loop recovery curves in real-time.
            </p>
          </div>

          <button
            onClick={() => {
              sound.playClick();
              onSelectScreen('anomaly-lab');
            }}
            className="relative z-10 w-full py-3 px-4 rounded-xl bg-black text-white hover:bg-slate-900 text-xs font-mono font-bold uppercase flex items-center justify-center gap-2 transition-all cursor-pointer shadow-lg shadow-black/20"
          >
            Launch Anomaly Sandbox & Trajectory
            <ArrowRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
};
