import React from 'react';
import { ActiveScreen } from '../types';
import { sound } from '../utils/audio';
import { Globe, Cpu, AlertTriangle, Activity, SlidersHorizontal, ShieldAlert, Wifi } from 'lucide-react';

interface SidebarProps {
  activeScreen: ActiveScreen;
  onSelectScreen: (screen: ActiveScreen) => void;
  onOpenOverrideDeck?: () => void;
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeScreen,
  onSelectScreen,
  onOpenOverrideDeck,
  isOpen = true,
  onClose,
}) => {
  const navItems = [
    {
      id: 'orbital-twin' as ActiveScreen,
      num: '01',
      label: 'Orbital Twin & Telemetry',
      sub: 'Live CAD wireframe & ground track',
      icon: Globe,
    },
    {
      id: 'agent-mesh' as ActiveScreen,
      num: '02',
      label: 'Autonomous Agent Mesh',
      sub: 'Raft-BFT consensus & reasoning',
      icon: Cpu,
    },
    {
      id: 'anomaly-lab' as ActiveScreen,
      num: '03',
      label: 'Chaos & Anomaly Lab',
      sub: 'Real-time sandbox & trajectory',
      icon: AlertTriangle,
      badge: 'SANDBOX',
    },
    {
      id: 'analytics' as ActiveScreen,
      num: '04',
      label: 'Telemetry Stream & Analytics',
      sub: 'Multi-channel oscilloscopes & KPIs',
      icon: Activity,
    },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-black/60 z-30 lg:hidden backdrop-blur-xs"
        />
      )}

      <aside
        className={`fixed top-16 left-0 bottom-0 z-40 w-64 bg-[#0f172a] border-r border-[#1e293b] flex flex-col justify-between transition-transform duration-200 shadow-2xl ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex flex-col flex-1 overflow-y-auto">
          {/* Section title */}
          <div className="px-5 pt-4 pb-3 flex items-center justify-between border-b border-[#1e293b]">
            <span className="font-mono text-[10px] text-slate-400 uppercase tracking-widest font-semibold">
              BENTO FLIGHT MATRIX
            </span>
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
          </div>

          {/* Navigation Items */}
          <div className="py-3 px-3 flex flex-col gap-1.5">
            {navItems.map((item) => {
              const isActive = activeScreen === item.id;
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    sound.playClick();
                    onSelectScreen(item.id);
                    if (onClose) onClose();
                  }}
                  className={`w-full text-left p-3 rounded-2xl transition-all flex items-start gap-3 cursor-pointer ${
                    isActive
                      ? 'bg-[#1e293b] border border-cyan-500/30 text-white shadow-lg'
                      : 'text-slate-400 hover:bg-[#1e293b]/50 hover:text-slate-200'
                  }`}
                >
                  <Icon
                    size={16}
                    className={`mt-0.5 shrink-0 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`}
                  />
                  <div className="flex flex-col flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[10px] text-cyan-400 font-bold">
                        {item.num} //
                      </span>
                      {item.badge && (
                        <span className="px-1.5 py-0.5 text-[8px] rounded-full bg-cyan-500/20 text-cyan-300 font-bold tracking-tighter border border-cyan-500/30">
                          {item.badge}
                        </span>
                      )}
                    </div>
                    <span className="font-semibold text-xs truncate text-slate-100">
                      {item.label}
                    </span>
                    <span className="text-[10px] text-slate-400 truncate">
                      {item.sub}
                    </span>
                  </div>
                </button>
              );
            })}

            {/* Manual Override Deck quick-action */}
            <div className="pt-3 mt-2 border-t border-[#1e293b]">
              <button
                onClick={() => {
                  sound.playWarning();
                  if (onOpenOverrideDeck) onOpenOverrideDeck();
                  if (onClose) onClose();
                }}
                className="w-full text-left p-3.5 rounded-2xl bg-[#05070a] border border-amber-500/30 hover:border-amber-500/60 text-slate-200 transition-all group cursor-pointer shadow-sm"
              >
                <div className="flex items-center gap-2 text-amber-400">
                  <SlidersHorizontal size={14} className="group-hover:rotate-45 transition-transform" />
                  <span className="font-mono text-[10px] uppercase font-bold">
                    05 // OVERRIDE DECK
                  </span>
                </div>
                <div className="text-[11px] font-semibold text-white mt-1">
                  Direct Hardware Actuators
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  Manual RCS, Attitude & MCR Seize
                </div>
              </button>
            </div>
          </div>
        </div>

        {/* Bottom Status Box */}
        <div className="p-3.5 m-3 rounded-2xl border border-[#1e293b] bg-[#05070a] flex flex-col gap-2 shadow-inner">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Wifi size={13} className="text-green-400" />
              GROUND LINK
            </span>
            <span className="font-mono text-green-400 text-[10px] font-bold">
              X-BAND LOCKED
            </span>
          </div>
          <div className="text-[10px] text-slate-400 font-mono flex justify-between">
            <span>8.4 GHz • 42 Mbps</span>
            <span className="text-cyan-400">BER: 1.2e-9</span>
          </div>

          <button
            onClick={() => {
              sound.playWarning();
              alert('EMERGENCY SAFE MODE: Satellite attitude oriented towards Sun, non-essential payloads depowered, transmitter set to beacon low-rate.');
            }}
            className="mt-1 w-full py-2 px-2.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 hover:bg-rose-500/20 text-[11px] font-mono uppercase font-bold flex items-center justify-center gap-2 transition-colors cursor-pointer"
          >
            <ShieldAlert size={13} />
            EMERGENCY SAFE MODE
          </button>

          <div className="text-[9px] text-slate-500 font-mono text-center pt-0.5">
            CORE NODE v4.18.2-rt · AES-256 SECURED
          </div>
        </div>
      </aside>
    </>
  );
};
