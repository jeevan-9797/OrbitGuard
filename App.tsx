/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ActiveScreen, AutonomyMode, AgentStatus } from './types';
import { INITIAL_AGENTS } from './data/mockFlightData';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { OrbitalTwinScreen } from './components/OrbitalTwinScreen';
import { AgentMeshScreen } from './components/AgentMeshScreen';
import { ChaosAnomalyLabScreen } from './components/ChaosAnomalyLabScreen';
import { AnalyticsScreen } from './components/AnalyticsScreen';
import { sound } from './utils/audio';

export default function App() {
  const [activeScreen, setActiveScreen] = useState<ActiveScreen>('orbital-twin');
  const [autonomyMode, setAutonomyMode] = useState<AutonomyMode>('L4');
  const [agents, setAgents] = useState<AgentStatus[]>(INITIAL_AGENTS);
  const [agentAlertCount, setAgentAlertCount] = useState<{ crit: number; warn: number }>({
    crit: 0,
    warn: 2,
  });
  const [selectedPresetId, setSelectedPresetId] = useState<string>('thermal');
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);

  // Toggle isolation for an agent
  const handleToggleAgentIsolation = (agentId: string) => {
    setAgents((prev) => {
      const nextAgents = prev.map((agent) => {
        if (agent.id === agentId) {
          const nextIsolated = !agent.isolated;
          return {
            ...agent,
            isolated: nextIsolated,
            state: (nextIsolated ? 'isolated' : 'nominal') as AgentStatus['state'],
          };
        }
        return agent;
      });
      const isolatedCount = nextAgents.filter((a) => a.isolated).length;
      setTimeout(() => {
        setAgentAlertCount({
          crit: isolatedCount >= 2 ? 1 : 0,
          warn: isolatedCount > 0 ? isolatedCount : 1,
        });
      }, 0);
      return nextAgents;
    });
  };

  const handleUpdateAlertCount = React.useCallback((crit: number, warn: number) => {
    setAgentAlertCount({ crit, warn });
  }, []);

  const handleSelectScreen = (screen: ActiveScreen) => {
    setActiveScreen(screen);
  };

  const handleSelectPresetAndGoToSandbox = (presetId: string) => {
    setSelectedPresetId(presetId);
    setActiveScreen('anomaly-lab');
  };

  const handleOpenOverrideDeck = () => {
    setActiveScreen('agent-mesh');
    setAutonomyMode('OVERRIDE');
    sound.playWarning();
  };

  const isolatedCount = agents.filter((a) => a.isolated).length;

  return (
    <div className="min-h-screen bg-[#05070a] text-slate-300 font-sans flex flex-col selection:bg-cyan-500/30">
      {/* Top Main Navigation Header */}
      <Header
        activeScreen={activeScreen}
        onSelectScreen={handleSelectScreen}
        autonomyMode={autonomyMode}
        agentAlertCount={agentAlertCount}
        isolatedAgentCount={isolatedCount}
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        sidebarOpen={sidebarOpen}
      />

      {/* Main Workspace with Sidebar + Responsive Content Area */}
      <div className="flex flex-1 pt-16">
        {/* Left Sidebar Navigation */}
        <Sidebar
          activeScreen={activeScreen}
          onSelectScreen={handleSelectScreen}
          onOpenOverrideDeck={handleOpenOverrideDeck}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        {/* Content Viewport (offset by sidebar width on desktop) */}
        <main className="flex-1 lg:ml-64 p-3 sm:p-4 lg:p-6 max-w-7xl mx-auto w-full overflow-x-hidden flex flex-col justify-between">
          <AnimatePresence mode="wait">
            {activeScreen === 'orbital-twin' && (
              <motion.div
                key="orbital-twin"
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.15 }}
              >
                <OrbitalTwinScreen
                  agents={agents}
                  onSelectScreen={handleSelectScreen}
                  onSelectPreset={handleSelectPresetAndGoToSandbox}
                  activeAnomalySeverity={agentAlertCount.crit > 0 ? 3 : 0}
                  activeAnomalyPresetId={selectedPresetId}
                />
              </motion.div>
            )}

            {activeScreen === 'agent-mesh' && (
              <motion.div
                key="agent-mesh"
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.15 }}
              >
                <AgentMeshScreen
                  agents={agents}
                  onToggleAgentIsolation={handleToggleAgentIsolation}
                  autonomyMode={autonomyMode}
                  onChangeAutonomyMode={setAutonomyMode}
                />
              </motion.div>
            )}

            {activeScreen === 'anomaly-lab' && (
              <motion.div
                key="anomaly-lab"
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.15 }}
              >
                <ChaosAnomalyLabScreen
                  selectedPresetId={selectedPresetId}
                  onPresetChange={setSelectedPresetId}
                  onUpdateAlertCount={handleUpdateAlertCount}
                />
              </motion.div>
            )}

            {activeScreen === 'analytics' && (
              <motion.div
                key="analytics"
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.15 }}
              >
                <AnalyticsScreen />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Bento Grid System Footer */}
          <footer className="mt-8 border-t border-[#1e293b] bg-[#0f172a]/60 backdrop-blur-md rounded-2xl py-3 px-6 text-[10px] text-slate-500 font-mono flex flex-wrap justify-between items-center gap-4 shadow-inner">
            <div className="flex flex-wrap items-center gap-4">
              <span className="text-slate-400 font-semibold">OPERATOR: FLT-DIR CHEN.E</span>
              <span className="text-slate-600">//</span>
              <span>VERSION: 4.1.0-STABLE · BENTO OPS CONSOLE</span>
              <span className="text-slate-600">//</span>
              <span className="text-cyan-400">TELEMETRY BUS: 100Hz RT-SYNC</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5 text-slate-300">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                UPLINK_ENCRYPTED (AES-256)
              </span>
              <span className="bg-[#1e293b] border border-cyan-500/20 px-2.5 py-0.5 rounded-full uppercase font-bold text-[9px] tracking-wider text-cyan-400">
                SECURE // L4
              </span>
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
}
