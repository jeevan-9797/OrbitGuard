import React, { useState } from 'react';
import { ActiveScreen, AutonomyMode } from '../types';
import { sound } from '../utils/audio';
import {
  Satellite,
  Radio,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Volume2,
  VolumeX,
  Menu,
  X,
  Orbit,
  Cpu,
  Flame,
  Activity,
  PanelLeftClose,
  Wind,
} from 'lucide-react';

interface HeaderProps {
  activeScreen: ActiveScreen;
  onSelectScreen: (screen: ActiveScreen) => void;
  autonomyMode: AutonomyMode;
  agentAlertCount: { crit: number; warn: number };
  isolatedAgentCount: number;
  onToggleSidebar: () => void;
  sidebarOpen: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  activeScreen,
  onSelectScreen,
  autonomyMode,
  agentAlertCount,
  isolatedAgentCount,
  onToggleSidebar,
  sidebarOpen,
}) => {
  const [audioEnabled, setAudioEnabled] = useState(sound.enabled);

  const toggleAudio = () => {
    const next = !audioEnabled;
    sound.enabled = next;
    setAudioEnabled(next);
    if (next) sound.playClick();
  };

  const navItems: { id: ActiveScreen; label: string; icon: React.ElementType }[] = [
    { id: 'orbital-twin', label: 'Orbital Twin', icon: Orbit },
    { id: 'agent-mesh', label: 'Agent Mesh', icon: Cpu },
    { id: 'anomaly-lab', label: 'Chaos Lab', icon: Flame },
    { id: 'propellantless', label: 'Propellantless', icon: Wind },
    { id: 'analytics', label: 'Analytics', icon: Activity },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-[#0a1120]/90 border-b border-[#1e293b] backdrop-blur-md z-40 px-4 flex items-center justify-between">
      {/* Left: Branding & Mobile/Desktop Nav Dock Toggle */}
      <div className="flex items-center gap-3">
        <button
          id="header-toggle-sidebar"
          onClick={() => {
            sound.playClick();
            onToggleSidebar();
          }}
          className={`p-2 sm:px-2.5 sm:py-1.5 rounded-xl border transition-all cursor-pointer flex items-center gap-2 font-mono text-xs ${
            sidebarOpen
              ? 'bg-amber-500/20 border-amber-500/50 text-amber-300 shadow-xs'
              : 'bg-[#0f172a] border-[#1e293b] text-slate-300 hover:text-white hover:bg-[#1e293b]'
          }`}
          title={sidebarOpen ? "Retract navigation sidebar" : "Open navigation sidebar"}
        >
          {sidebarOpen ? (
            <PanelLeftClose size={18} className="text-amber-400" />
          ) : (
            <Menu size={18} className="text-cyan-400" />
          )}
          <span className="hidden md:inline text-[11px] font-bold tracking-wider">
            {sidebarOpen ? 'RETRACT DOCK' : 'CONSOLES'}
          </span>
        </button>

        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-sm">
            <Satellite size={20} />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-white tracking-wider font-display-hero">
                ASTRA-7
              </span>
              <span className="px-2 py-0.5 rounded-full text-[9px] font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                TWIN-OPS
              </span>
            </div>
            <span className="text-[10px] font-mono text-slate-400 hidden sm:inline">
              AUTONOMOUS DIGITAL TWIN & SWARM MESH
            </span>
          </div>
        </div>
      </div>

      {/* Center: Top Screen Navigation (Desktop) */}
      <nav className="hidden md:flex items-center gap-1.5 bg-[#05070a] p-1 rounded-2xl border border-[#1e293b]">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeScreen === item.id;
          return (
            <button
              key={item.id}
              onClick={() => {
                sound.playClick();
                onSelectScreen(item.id);
              }}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-mono font-semibold flex items-center gap-2 transition-all cursor-pointer ${
                isActive
                  ? 'bg-cyan-500 text-black shadow-md'
                  : 'text-slate-400 hover:text-white hover:bg-[#0f172a]'
              }`}
            >
              <Icon size={14} />
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* Right: Autonomy Badge, Alert Pill & Audio Switch */}
      <div className="flex items-center gap-3 text-xs font-mono">
        {/* Swarm Status Indicator */}
        <div className="hidden sm:flex items-center gap-2 bg-[#05070a] px-3 py-1.5 rounded-xl border border-[#1e293b]">
          <span className="text-slate-400 text-[10px]">SWARM:</span>
          {isolatedAgentCount > 0 ? (
            <span className="text-amber-400 font-bold flex items-center gap-1">
              <AlertTriangle size={12} />
              {isolatedAgentCount} ISOLATED
            </span>
          ) : (
            <span className="text-green-400 font-bold flex items-center gap-1">
              <ShieldCheck size={12} />
              4/4 QUORUM
            </span>
          )}
        </div>

        {/* Autonomy Mode Badge */}
        <span
          className={`px-2.5 py-1 rounded-xl text-[10px] font-bold tracking-wide uppercase border flex items-center gap-1.5 ${
            autonomyMode === 'OVERRIDE'
              ? 'bg-rose-500/20 text-rose-400 border-rose-500/40 animate-pulse'
              : autonomyMode === 'HITL'
              ? 'bg-amber-500/20 text-amber-400 border-amber-500/40'
              : 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40'
          }`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
          {autonomyMode === 'OVERRIDE' ? 'MANUAL' : autonomyMode}
        </span>

        {/* Audio FX Toggle */}
        <button
          onClick={toggleAudio}
          className={`p-2 rounded-xl border transition-all cursor-pointer ${
            audioEnabled
              ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30 hover:bg-cyan-500/20'
              : 'bg-[#05070a] text-slate-500 border-[#1e293b] hover:text-slate-300'
          }`}
          title={audioEnabled ? 'Mute Audio Effects' : 'Enable Mission Control Sound Effects'}
        >
          {audioEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
        </button>
      </div>
    </header>
  );
};
