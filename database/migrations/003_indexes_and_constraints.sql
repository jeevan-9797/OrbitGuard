-- ============================================================================
-- Migration 003: Indexes and Performance Constraints
-- Satellite Multi-Agent AI System
-- ============================================================================

-- Telemetry performance indexes (High-frequency dashboard queries)
CREATE INDEX IF NOT EXISTS idx_telemetry_satellite_time 
    ON telemetry (satellite_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_telemetry_subsystem_metric_time 
    ON telemetry (subsystem_id, metric, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_telemetry_metric_time 
    ON telemetry (metric, timestamp DESC);

-- Anomalies index for active detection queries
CREATE INDEX IF NOT EXISTS idx_anomalies_satellite_started 
    ON anomalies (satellite_id, started_at DESC);

-- Incident dashboard indexes
CREATE INDEX IF NOT EXISTS idx_incidents_state_opened 
    ON incidents (state, opened_at DESC);

CREATE INDEX IF NOT EXISTS idx_incidents_satellite 
    ON incidents (satellite_id, opened_at DESC);

-- Audit timeline index (Strict chronological ordering for post-mortem)
CREATE INDEX IF NOT EXISTS idx_audit_events_incident_time 
    ON audit_events (incident_id, timestamp ASC);

-- Multi-agent runs index (Chronological workflow visualization)
CREATE INDEX IF NOT EXISTS idx_agent_runs_incident_started 
    ON agent_runs (incident_id, started_at ASC);

-- Recovery plans, validations, and command execution lookup indexes
CREATE INDEX IF NOT EXISTS idx_recovery_plans_incident 
    ON recovery_plans (incident_id, version DESC);

CREATE INDEX IF NOT EXISTS idx_validations_plan 
    ON validations (plan_id);

CREATE INDEX IF NOT EXISTS idx_command_executions_plan 
    ON command_executions (plan_id);

-- Knowledge retrieval indexes
CREATE INDEX IF NOT EXISTS idx_baselines_lookup 
    ON telemetry_baselines (satellite_id, mode_code, metric);

CREATE INDEX IF NOT EXISTS idx_historical_scenario 
    ON historical_incidents (anomaly_type);
