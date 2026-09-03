import React, { useState } from 'react';
import {
  FLEET_SATELLITES,
  ACTION_CATALOG,
  SAFETY_RULES,
  HISTORICAL_ORBIT_CASES,
  SCENARIO_DATASETS,
  SeedSatellite,
  SeedAction,
  SeedSafetyRule,
  SeedHistoricalIncident,
} from '../data/databaseDataset';
import {
  Database,
  Satellite,
  ShieldCheck,
  Zap,
  Clock,
  Cpu,
  Layers,
  CheckCircle2,
  AlertTriangle,
  FileCode,
  Activity,
  Terminal,
  RefreshCw,
} from 'lucide-react';
import { sound } from '../utils/audio';

type SubView = 'satellites' | 'actions' | 'rules' | 'historical' | 'scenarios' | 'schema';

export const DatabaseExplorerView: React.FC = () => {
  const [subView, setSubView] = useState<SubView>('satellites');
  const [selectedSat, setSelectedSat] = useState<SeedSatellite>(FLEET_SATELLITES[0]);
  const [selectedScenarioKey, setSelectedScenarioKey] = useState<'SCENARIO_A' | 'SCENARIO_B'>('SCENARIO_A');
  const [resetFeedback, setResetFeedback] = useState<string | null>(null);

  const selectedScenario = SCENARIO_DATASETS[selectedScenarioKey];

  const handleResetDemo = () => {
    sound.playClick();
    setResetFeedback('Resetting constellation demo baseline state via reset_demo()...');
    setTimeout(() => {
      setResetFeedback('Constellation baseline restored: All 7 satellites nominal, 35 subsystems 100% healthy.');
      setTimeout(() => setResetFeedback(null), 3500);
    }, 600);
  };

  return (
    <div className="w-full flex flex-col gap-4">
      {/* Sub-navigation & Overview Bar */}
      <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-wrap items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-400">
            <Database size={20} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-white font-semibold uppercase tracking-wide">
                RELATIONAL FLIGHT DATABASE & AI KNOWLEDGE BACKBONE
              </span>
              <span className="px-2 py-0.5 rounded-full text-[9px] font-mono bg-emerald-500/15 text-emerald-400 font-bold border border-emerald-500/30 flex items-center gap-1">
                <CheckCircle2 size={10} /> SCHEMA VERIFIED [17 TABLES]
              </span>
            </div>
            <span className="font-mono text-[11px] text-slate-400">
              11 CORE TABLES // 6 KNOWLEDGE TABLES // 6 OPTIMIZED B-TREE INDEXES // SCENARIOS A & B
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleResetDemo}
            className="px-3 py-1.5 rounded-xl bg-[#05070a] border border-[#1e293b] hover:border-cyan-500/50 text-slate-300 hover:text-white font-mono text-xs flex items-center gap-1.5 transition-all cursor-pointer"
          >
            <RefreshCw size={13} className="text-cyan-400" />
            RESET DEMO BASELINE
          </button>
        </div>
      </div>

      {resetFeedback && (
        <div className="px-4 py-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-mono text-xs flex items-center gap-2 animate-pulse">
          <Activity size={14} />
          {resetFeedback}
        </div>
      )}

      {/* View Selector Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-[#1e293b] pb-2 font-mono text-xs">
        <button
          onClick={() => {
            sound.playClick();
            setSubView('satellites');
          }}
          className={`px-3.5 py-2 rounded-xl flex items-center gap-2 transition-all cursor-pointer ${
            subView === 'satellites'
              ? 'bg-cyan-500 text-black font-bold shadow-md'
              : 'bg-[#0f172a] text-slate-400 hover:text-white border border-[#1e293b]'
          }`}
        >
          <Satellite size={14} />
          FLEET SATELLITES ({FLEET_SATELLITES.length})
        </button>

        <button
          onClick={() => {
            sound.playClick();
            setSubView('actions');
          }}
          className={`px-3.5 py-2 rounded-xl flex items-center gap-2 transition-all cursor-pointer ${
            subView === 'actions'
              ? 'bg-cyan-500 text-black font-bold shadow-md'
              : 'bg-[#0f172a] text-slate-400 hover:text-white border border-[#1e293b]'
          }`}
        >
          <Zap size={14} />
          ACTION CATALOG ({ACTION_CATALOG.length})
        </button>

        <button
          onClick={() => {
            sound.playClick();
            setSubView('rules');
          }}
          className={`px-3.5 py-2 rounded-xl flex items-center gap-2 transition-all cursor-pointer ${
            subView === 'rules'
              ? 'bg-cyan-500 text-black font-bold shadow-md'
              : 'bg-[#0f172a] text-slate-400 hover:text-white border border-[#1e293b]'
          }`}
        >
          <ShieldCheck size={14} />
          SAFETY INTERLOCK RULES ({SAFETY_RULES.length})
        </button>

        <button
          onClick={() => {
            sound.playClick();
            setSubView('historical');
          }}
          className={`px-3.5 py-2 rounded-xl flex items-center gap-2 transition-all cursor-pointer ${
            subView === 'historical'
              ? 'bg-cyan-500 text-black font-bold shadow-md'
              : 'bg-[#0f172a] text-slate-400 hover:text-white border border-[#1e293b]'
          }`}
        >
          <Clock size={14} />
          HISTORICAL CASES ({HISTORICAL_ORBIT_CASES.length})
        </button>

        <button
          onClick={() => {
            sound.playClick();
            setSubView('scenarios');
          }}
          className={`px-3.5 py-2 rounded-xl flex items-center gap-2 transition-all cursor-pointer ${
            subView === 'scenarios'
              ? 'bg-cyan-500 text-black font-bold shadow-md'
              : 'bg-[#0f172a] text-slate-400 hover:text-white border border-[#1e293b]'
          }`}
        >
          <Cpu size={14} />
          AI REASONING SCENARIOS (2)
        </button>

        <button
          onClick={() => {
            sound.playClick();
            setSubView('schema');
          }}
          className={`px-3.5 py-2 rounded-xl flex items-center gap-2 transition-all cursor-pointer ${
            subView === 'schema'
              ? 'bg-cyan-500 text-black font-bold shadow-md'
              : 'bg-[#0f172a] text-slate-400 hover:text-white border border-[#1e293b]'
          }`}
        >
          <Layers size={14} />
          DATABASE SCHEMA & AUDIT
        </button>
      </div>

      {/* Subview 1: Fleet Satellites */}
      {subView === 'satellites' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col gap-3 shadow-lg">
            <span className="font-mono text-xs text-slate-400 uppercase font-semibold">
              Constellation Nodes ({FLEET_SATELLITES.length} Seeded)
            </span>
            <div className="flex flex-col gap-2">
              {FLEET_SATELLITES.map((sat) => {
                const isSelected = sat.id === selectedSat.id;
                return (
                  <button
                    key={sat.id}
                    onClick={() => {
                      sound.playClick();
                      setSelectedSat(sat);
                    }}
                    className={`p-3 rounded-xl text-left font-mono transition-all cursor-pointer border ${
                      isSelected
                        ? 'bg-cyan-500/10 border-cyan-500 text-white shadow-md'
                        : 'bg-[#05070a] border-[#1e293b] text-slate-300 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-cyan-300">{sat.name}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        NORAD #{sat.noradId}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                      <span>Alt: {sat.altitudeKm} km</span>
                      <span>Inc: {sat.inclinationDeg}°</span>
                      <span className="text-emerald-400 font-semibold">{sat.status}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="lg:col-span-2 bg-[#0f172a] border border-[#1e293b] p-5 rounded-2xl flex flex-col gap-4 shadow-lg">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1e293b] pb-3">
              <div>
                <h3 className="text-lg font-bold text-white font-mono flex items-center gap-2">
                  <Satellite size={18} className="text-cyan-400" />
                  {selectedSat.name} // Telemetry Profile
                </h3>
                <span className="font-mono text-xs text-slate-400">
                  Designator: {selectedSat.designator} | Autonomy: {selectedSat.autonomyMode} | Orbit:{' '}
                  {selectedSat.orbitType}
                </span>
              </div>
              <span className="px-2.5 py-1 rounded-full text-xs font-mono bg-emerald-500/15 text-emerald-400 font-bold border border-emerald-500/30">
                ACTIVE ON-ORBIT
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 rounded-xl bg-[#05070a] border border-[#1e293b]">
                <span className="font-mono text-[10px] text-slate-400 block">Altitude</span>
                <span className="font-mono text-base font-bold text-cyan-300">{selectedSat.altitudeKm} km</span>
              </div>
              <div className="p-3 rounded-xl bg-[#05070a] border border-[#1e293b]">
                <span className="font-mono text-[10px] text-slate-400 block">Inclination</span>
                <span className="font-mono text-base font-bold text-slate-200">{selectedSat.inclinationDeg}°</span>
              </div>
              <div className="p-3 rounded-xl bg-[#05070a] border border-[#1e293b]">
                <span className="font-mono text-[10px] text-slate-400 block">Autonomy Mode</span>
                <span className="font-mono text-xs font-bold text-amber-300">{selectedSat.autonomyMode}</span>
              </div>
              <div className="p-3 rounded-xl bg-[#05070a] border border-[#1e293b]">
                <span className="font-mono text-[10px] text-slate-400 block">Subsystems</span>
                <span className="font-mono text-base font-bold text-emerald-400">
                  {selectedSat.subsystems.length} Monitored
                </span>
              </div>
            </div>

            <div>
              <span className="font-mono text-xs text-slate-400 uppercase font-semibold block mb-2">
                Subsystem Health & FDIR Telemetry Hierarchy
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {selectedSat.subsystems.map((sub, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-xl bg-[#05070a] border border-[#1e293b] flex items-center justify-between"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-mono text-[10px] font-bold">
                          {sub.code}
                        </span>
                        <span className="font-mono text-xs text-slate-200 font-medium">{sub.name}</span>
                      </div>
                      <span className="text-[10px] text-emerald-400 font-mono mt-0.5 block">
                        Status: {sub.status}
                      </span>
                    </div>
                    <span className="font-mono text-sm font-bold text-emerald-400">{sub.health}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Subview 2: Action Catalog */}
      {subView === 'actions' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {ACTION_CATALOG.map((action, i) => (
            <div
              key={i}
              className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col justify-between shadow-lg hover:border-cyan-500/40 transition-all"
            >
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-cyan-300 px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30">
                    {action.code}
                  </span>
                  <span
                    className={`font-mono text-[10px] font-bold px-2 py-0.5 rounded ${
                      action.riskLevel === 'HIGH'
                        ? 'bg-rose-500/20 text-rose-300'
                        : action.riskLevel === 'MEDIUM'
                        ? 'bg-amber-500/20 text-amber-300'
                        : 'bg-emerald-500/20 text-emerald-300'
                    }`}
                  >
                    {action.riskLevel} RISK
                  </span>
                </div>
                <h4 className="font-mono text-sm font-bold text-white">{action.name}</h4>
                <p className="text-xs text-slate-400 leading-relaxed">{action.description}</p>
              </div>

              <div className="mt-3 pt-3 border-t border-[#1e293b] flex items-center justify-between font-mono text-[11px]">
                <span className="text-slate-400">Subsystem: {action.subsystem}</span>
                <span className={action.isReversible ? 'text-emerald-400' : 'text-amber-400'}>
                  {action.isReversible ? '✓ Reversible' : '⚠ Non-Reversible'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Subview 3: Safety Interlock Rules */}
      {subView === 'rules' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {SAFETY_RULES.map((rule, i) => (
            <div
              key={i}
              className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col justify-between shadow-lg hover:border-cyan-500/40 transition-all"
            >
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-emerald-300 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30">
                    {rule.code}
                  </span>
                  <span
                    className={`font-mono text-[10px] font-bold px-2 py-0.5 rounded ${
                      rule.enforcement === 'STRICT_INTERLOCK'
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    }`}
                  >
                    {rule.enforcement}
                  </span>
                </div>
                <h4 className="font-mono text-sm font-bold text-white">{rule.name}</h4>
                <div className="p-2 rounded-lg bg-[#05070a] border border-[#1e293b] font-mono text-xs text-cyan-300">
                  <code>{rule.condition}</code>
                </div>
                <p className="text-xs text-slate-400">{rule.description}</p>
              </div>
              <div className="mt-3 pt-2 border-t border-[#1e293b] font-mono text-[10px] text-slate-500">
                Scope: Subsystem {rule.subsystem}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Subview 4: Historical Incidents */}
      {subView === 'historical' && (
        <div className="flex flex-col gap-3">
          {HISTORICAL_ORBIT_CASES.map((item, i) => (
            <div
              key={i}
              className="bg-[#0f172a] border border-[#1e293b] p-4 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-lg hover:border-cyan-500/40 transition-all"
            >
              <div className="flex items-start gap-3">
                <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 font-mono text-xs font-bold whitespace-nowrap">
                  {item.orbit}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-slate-200">{item.caseCode}</span>
                    <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300">
                      {item.subsystem}
                    </span>
                    <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                      {item.recoveryStrategy}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 mt-1 font-medium">{item.rootCause}</p>
                  <p className="text-xs text-slate-400 mt-0.5">Resolution: {item.resolution}</p>
                  <p className="text-[11px] text-amber-300/80 font-mono mt-1">Lesson: {item.lessonsLearned}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 self-end md:self-center">
                <div className="text-right">
                  <span className="font-mono text-[10px] text-slate-500 block">MTTR (sec)</span>
                  <span className="font-mono text-sm font-bold text-emerald-400">{item.mttrSeconds}s</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Subview 5: AI Reasoning Scenarios A & B */}
      {subView === 'scenarios' && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                sound.playClick();
                setSelectedScenarioKey('SCENARIO_A');
              }}
              className={`px-4 py-2 rounded-xl font-mono text-xs font-bold cursor-pointer transition-all ${
                selectedScenarioKey === 'SCENARIO_A'
                  ? 'bg-rose-500 text-white shadow-lg'
                  : 'bg-[#0f172a] text-slate-300 border border-[#1e293b]'
              }`}
            >
              SCENARIO A: BATTERY OVERHEAT (THERMAL_RUNAWAY)
            </button>
            <button
              onClick={() => {
                sound.playClick();
                setSelectedScenarioKey('SCENARIO_B');
              }}
              className={`px-4 py-2 rounded-xl font-mono text-xs font-bold cursor-pointer transition-all ${
                selectedScenarioKey === 'SCENARIO_B'
                  ? 'bg-amber-500 text-black shadow-lg'
                  : 'bg-[#0f172a] text-slate-300 border border-[#1e293b]'
              }`}
            >
              SCENARIO B: REACTION-WHEEL DEGRADATION (FRICTION)
            </button>
          </div>

          <div className="bg-[#0f172a] border border-[#1e293b] p-5 rounded-2xl flex flex-col gap-4 shadow-xl">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1e293b] pb-3">
              <div>
                <h3 className="font-mono text-base font-bold text-white">{selectedScenario.title}</h3>
                <span className="font-mono text-xs text-slate-400">
                  Anomaly Code: {selectedScenario.anomalyCode} // Type: {selectedScenario.anomalyType}
                </span>
              </div>
              <span className="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                {selectedScenario.severity} SEVERITY
              </span>
            </div>

            {/* Metric Breach */}
            <div className="p-3 rounded-xl bg-[#05070a] border border-[#1e293b] flex flex-wrap items-center justify-between gap-3">
              <span className="font-mono text-xs text-slate-400">
                Trigger Metric: <strong className="text-cyan-300">{selectedScenario.triggerMetric}</strong>
              </span>
              <div className="flex items-center gap-4 font-mono text-xs">
                <span>
                  Observed: <strong className="text-rose-400">{selectedScenario.observedValue} {selectedScenario.unit}</strong>
                </span>
                <span>
                  Nominal: <strong className="text-emerald-400">{selectedScenario.nominalValue} {selectedScenario.unit}</strong>
                </span>
              </div>
            </div>

            {/* AI Contract 1: Hypothesis Output */}
            <div className="p-4 rounded-xl bg-[#05070a] border border-[#1e293b] flex flex-col gap-2">
              <span className="font-mono text-[11px] uppercase tracking-wider text-slate-400 font-bold flex items-center gap-2">
                <Cpu size={14} className="text-cyan-400" />
                AI CONTRACT 1: agent_runs.output (Hypothesis Generation)
              </span>
              <div className="p-3 rounded-lg bg-[#0b1120] border border-cyan-500/30 text-xs font-mono">
                <p className="text-cyan-200">
                  <strong>primary_hypothesis:</strong> "{selectedScenario.primaryHypothesis}"
                </p>
                <div className="mt-2 text-slate-300">
                  <strong>hypotheses:</strong>
                  <ul className="list-disc list-inside mt-1 space-y-1">
                    {selectedScenario.hypotheses.map((h) => (
                      <li key={h.id}>
                        [{h.id}] {h.cause} — Confidence: {(h.confidence * 100).toFixed(0)}%
                      </li>
                    ))}
                  </ul>
                </div>
                <p className="mt-2 text-emerald-400">
                  <strong>needs_evidence:</strong> {selectedScenario.needsEvidence ? 'true' : 'false'}
                </p>
              </div>
            </div>

            {/* AI Contract 2: Recovery Plan Actions */}
            <div className="p-4 rounded-xl bg-[#05070a] border border-[#1e293b] flex flex-col gap-2">
              <span className="font-mono text-[11px] uppercase tracking-wider text-slate-400 font-bold flex items-center gap-2">
                <Zap size={14} className="text-amber-400" />
                AI CONTRACT 2: recovery_plans.actions (Ordered Action Primitives)
              </span>
              <div className="p-3 rounded-lg bg-[#0b1120] border border-amber-500/30 text-xs font-mono flex flex-col gap-2">
                <div className="flex items-center justify-between text-slate-300">
                  <span>Plan: <strong>{selectedScenario.recoveryPlan.title}</strong></span>
                  <span>Proposed By: {selectedScenario.recoveryPlan.proposedBy}</span>
                </div>
                <div className="space-y-2 mt-1">
                  {selectedScenario.recoveryPlan.actions.map((act) => (
                    <div
                      key={act.order}
                      className="p-2.5 rounded bg-[#05070a] border border-[#1e293b] flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-300 flex items-center justify-center font-bold text-[10px]">
                          {act.order}
                        </span>
                        <span className="font-bold text-cyan-300">{act.actionCode}</span>
                      </div>
                      <span className="text-[11px] text-slate-400">
                        params: {JSON.stringify(act.parameters)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Subview 6: Database Schema & Audit */}
      {subView === 'schema' && (
        <div className="bg-[#0f172a] border border-[#1e293b] p-5 rounded-2xl flex flex-col gap-4 shadow-xl">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1e293b] pb-3">
            <div>
              <h3 className="font-mono text-base font-bold text-white flex items-center gap-2">
                <Terminal size={18} className="text-cyan-400" />
                Database Schema Verification Audit
              </h3>
              <span className="font-mono text-xs text-slate-400">
                Automated Verification Suite: verify_database.py
              </span>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
              <CheckCircle2 size={13} /> VERIFICATION PASS
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-[#05070a] border border-[#1e293b] flex flex-col gap-2 font-mono text-xs">
              <span className="text-cyan-300 font-bold uppercase">11 Core Operational Tables</span>
              <ul className="space-y-1 text-slate-300">
                <li>• satellites (fleet metadata, orbit altitude, inclination)</li>
                <li>• subsystems (EPS, ADCS, PROP, TCS, COMMS, OBC, PL)</li>
                <li>• telemetry (high-rate time series sensor streams)</li>
                <li>• anomalies (confidence, threshold breach, severity)</li>
                <li>• incidents (state, MTTR metrics, root cause)</li>
                <li>• safety_rules (strict interlocks, conditions)</li>
                <li>• agent_runs (swarm cycles, hypotheses)</li>
                <li>• recovery_plans (ordered action sequences)</li>
                <li>• validations (interlock & Byzantine checks)</li>
                <li>• command_executions (on-orbit dispatch log)</li>
                <li>• audit_events (tamper-evident incident ledger)</li>
              </ul>
            </div>

            <div className="p-4 rounded-xl bg-[#05070a] border border-[#1e293b] flex flex-col gap-2 font-mono text-xs">
              <span className="text-cyan-300 font-bold uppercase">6 Knowledge & Config Tables</span>
              <ul className="space-y-1 text-slate-300">
                <li>• action_catalog (PWR_*, ADCS_*, TCS_*, etc.)</li>
                <li>• operating_modes (Safe Sun-Point, Payload Ops)</li>
                <li>• telemetry_baselines (mean, std dev, min/max)</li>
                <li>• historical_incidents (Orbit 1420 to 6105 cases)</li>
                <li>• runbook_templates (FDIR contingency procedures)</li>
                <li>• system_config (swarm consensus parameters)</li>
              </ul>
              <span className="text-emerald-400 font-bold uppercase mt-2">6 Performance Indexes</span>
              <ul className="space-y-0.5 text-slate-400 text-[11px]">
                <li>• idx_telemetry_satellite_time</li>
                <li>• idx_telemetry_subsystem_metric_time</li>
                <li>• idx_anomalies_satellite_started</li>
                <li>• idx_incidents_state_opened</li>
                <li>• idx_audit_events_incident_time</li>
                <li>• idx_agent_runs_incident_started</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
