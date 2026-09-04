import React, { useState, useEffect } from 'react';
import { ActiveScreen, AutonomyMode } from '../types';
import { sound } from '../utils/audio';
import { Volume2, VolumeX, Menu, X, Zap } from 'lucide-react';

interface HeaderProps {
  activeScreen: ActiveScreen;
  onSelectScreen: (screen: ActiveScreen) => void;
  autonomyMode: AutonomyMode;
  agentAlertCount: { crit: number; warn: number };
  isolatedAgentCount: number;
  onToggleSidebar?: () => void;
  sidebarOpen?: boolean;
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
  const [metSeconds, setMetSeconds] = useState(142 * 86400 + 8 * 3600 + 44 * 60 + 12);
  const [soundOn, setSoundOn] = useState(sound.enabled);

  useEffect(() => {
    const interval = setInterval(() => {
      setMetSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const formatMET = (totalSec: number) => {
    const days = Math.floor(totalSec / 86400);
    const hours = Math.floor((totalSec % 86400) / 3600);
    const mins = Math.floor((totalSec % 3600) / 60);
    const secs = totalSec % 60;
    return `UTC MET T+${days}:${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  const toggleSound = () => {
    sound.enabled = !sound.enabled;
    setSoundOn(sound.enabled);
    if (sound.enabled) {
      sound.playClick();
    }
  };

  const navItems: { id: ActiveScreen; label: string }[] = [
    { id: 'orbital-twin', label: 'Orbital Twin & Telemetry' },
    { id: 'agent-mesh', label: 'Autonomous Agent Mesh' },
    { id: 'anomaly-lab', label: 'Chaos & Anomaly Lab' },
    { id: 'analytics', label: 'Telemetry Stream & Analytics' },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-[#0f172a]/95 backdrop-blur-xl border-b border-[#1e293b] shadow-2xl">
      <div className="w-full h-full px-4 sm:px-6 flex items-center justify-between gap-4">
        {/* Left branding & Bento MET */}
        <div className="flex items-center gap-4 sm:gap-6">
          {/* Mobile sidebar toggle */}
          <button
            onClick={onToggleSidebar}
            className="lg:hidden p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800"
            aria-label="Toggle Navigation"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>

          <div
            onClick={() => {
              sound.playClick();
              onSelectScreen('orbital-twin');
            }}
            className="flex items-center gap-3 cursor-pointer group"
          >
            {/* Bento Accent Logo Icon */}
            <div className="w-8 h-8 bg-cyan-500 rounded-xl flex items-center justify-center shadow-lg shadow-cyan-500/20 shrink-0 group-hover:scale-105 transition-transform">
              <Zap className="w-4 h-4 text-black" fill="currentColor" />
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-sm tracking-tight text-white uppercase group-hover:text-cyan-300">
                ASTRA <span className="text-cyan-400">TRAJECTORY LAB</span>
              </span>
              <span className="font-mono text-[9px] text-slate-400 tracking-wider">
                TWIN-7 // SEC-9 · BENTO CONSOLE
              </span>
            </div>
          </div>

          <div className="h-6 w-px bg-[#1e293b] hidden xl:block"></div>

          {/* Bento Status Indicator Chips */}
          <div className="hidden xl:flex items-center gap-4 text-xs font-semibold uppercase tracking-wider">
            <div className="flex items-center gap-2 text-slate-300">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              <span className="text-[11px] font-mono">Core: Synchronized</span>
            </div>
            <div className="flex items-center gap-2 text-slate-300">
              <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse"></span>
              <span className="text-[11px] font-mono">Sandbox: Active</span>
            </div>
          </div>

          <div className="h-6 w-px bg-[#1e293b] hidden 2xl:block"></div>

          <div className="hidden 2xl:flex items-center gap-3">
            <div className="flex flex-col">
              <span className="font-mono text-[9px] text-slate-500 uppercase tracking-widest">
                MISSION ELAPSED TIME
              </span>
              <span className="font-mono text-xs text-green-400 tracking-wider font-semibold">
                {formatMET(metSeconds)}
              </span>
            </div>
          </div>
        </div>

        {/* Center navigation tabs styled with Bento Pills */}
        <nav className="hidden lg:flex items-center h-full gap-2">
          {navItems.map((item) => {
            const isActive = activeScreen === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  sound.playClick();
                  onSelectScreen(item.id);
                }}
                className={`flex items-center px-3 py-1.5 rounded-xl font-mono text-xs uppercase transition-all relative cursor-pointer ${
                  isActive
                    ? 'bg-cyan-500/15 text-cyan-400 font-bold border border-cyan-500/30 shadow-xs'
                    : 'text-slate-400 hover:text-white hover:bg-[#1e293b]/60'
                }`}
              >
                {item.label}
                {item.id === 'anomaly-lab' && (
                  <span className="ml-1.5 px-1.5 py-0.5 text-[8px] rounded-md bg-cyan-500/20 text-cyan-300 font-bold tracking-tighter border border-cyan-500/30">
                    SANDBOX
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Right status badges & Flight Director */}
        <div className="flex items-center gap-3">
          {/* Audio toggle button */}
          <button
            onClick={toggleSound}
            title={soundOn ? 'Mute Mission Audio' : 'Enable Mission Audio'}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            {soundOn ? <Volume2 size={16} className="text-cyan-400" /> : <VolumeX size={16} />}
          </button>

          {/* Autonomy Badge */}
          {autonomyMode === 'OVERRIDE' ? (
            <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-xl bg-rose-500/20 border border-rose-500/50 text-rose-400 animate-pulse">
              <span className="w-2 h-2 rounded-full bg-rose-500"></span>
              <span className="font-mono text-[10px] uppercase font-bold">
                AGENT MESH SEIZED
              </span>
            </div>
          ) : isolatedAgentCount > 0 ? (
            <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-xl bg-amber-500/15 border border-amber-500/40 text-amber-400">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
              <span className="font-mono text-[10px] uppercase">
                {4 - isolatedAgentCount}/4 AGENTS ACTIVE
              </span>
            </div>
          ) : (
            <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-xl bg-slate-900 border border-[#1e293b] text-slate-300">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
              <span className="font-mono text-[10px] uppercase text-green-400 font-semibold">
                4/4 AGENTS NOMINAL
              </span>
            </div>
          )}

          {/* Alerts Badge */}
          <div
            className={`hidden sm:flex items-center gap-2 px-3 py-1 rounded-xl ${
              agentAlertCount.crit > 0
                ? 'bg-rose-500/20 border border-rose-500 text-rose-400 animate-pulse'
                : 'bg-slate-900 border border-[#1e293b] text-slate-400'
            }`}
          >
            <span className="font-mono text-[10px] uppercase font-bold">
              ALERTS: <span className={agentAlertCount.crit > 0 ? 'text-rose-400' : 'text-slate-300'}>{agentAlertCount.crit} CRIT</span> / {agentAlertCount.warn} WARN
            </span>
          </div>

          {/* Flight Director Profile */}
          <div className="flex items-center gap-3 pl-2 border-l border-[#1e293b]">
            <div className="text-right hidden sm:block">
              <div className="font-mono text-[10px] text-white font-bold uppercase">
                FLT-DIR // CHEN.E
              </div>
              <div className="font-mono text-[9px] text-cyan-400">
                192.168.0.1 // NODE 7
              </div>
            </div>
            <img
              alt="Profile of Flight Director Chen.E"
              className="w-8 h-8 rounded-full object-cover ring-2 ring-cyan-500/50 shadow-md"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuALX2wf7JlWmAB4qcbVt9Qyqyv6_FDtjZux-k9TZluY0DCTr-leNi442A5GeknBa7qsHppeALl03VkLPnjanhDB6JJwvAl7Nr_IpE-u3iaYHDyQPz3V-7EZY416OkNqfyKCWb5w1L3hO92mfHDOrdPGZWJA5wNm57LPaeqV7dog1z99pzF0VkmPhaoySjPep8-xIJA6SXd8UutZv1fkYSPDrAehqXc9Tqll5Bf2DVDY0nt7ojbnIrZ9"
            />
          </div>
        </div>
      </div>
    </header>
  );
};
