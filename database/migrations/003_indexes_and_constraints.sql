-- ============================================================================
-- Migration 003: Performance Indexes and Constraints
-- ============================================================================

-- Telemetry high-frequency retrieval indexes
CREATE INDEX IF NOT EXISTS idx_telemetry_satellite_time
    ON telemetry(satellite_id, captured_at DESC);

CREATE INDEX IF NOT EXISTS idx_telemetry_subsystem_metric_time
    ON telemetry(subsystem_id, metric_name, captured_at DESC);

-- Anomaly detection & incident triage indexes
CREATE INDEX IF NOT EXISTS idx_anomalies_satellite_started
    ON anomalies(satellite_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_incidents_state_opened
    ON incidents(state, opened_at DESC);

-- Incident audit trail & agent run sequence indexes
CREATE INDEX IF NOT EXISTS idx_audit_events_incident_time
    ON audit_events(incident_id, event_time ASC);

CREATE INDEX IF NOT EXISTS idx_agent_runs_incident_started
    ON agent_runs(incident_id, started_at ASC);

-- Additional lookup indexes for telemetry baselines and action catalog
CREATE INDEX IF NOT EXISTS idx_telemetry_baselines_lookup
    ON telemetry_baselines(subsystem_code, metric_name);

CREATE INDEX IF NOT EXISTS idx_action_catalog_code
    ON action_catalog(action_code);
