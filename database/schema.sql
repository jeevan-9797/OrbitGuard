-- ============================================================================
-- Complete Master Schema: Satellite Multi-Agent AI System
-- File: database/schema.sql
-- Production-shaped, hackathon-sized monolithic PostgreSQL / Supabase Schema
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- 1. KNOWLEDGE & CONFIGURATION TABLES
-- ============================================================================

-- Operating Modes
CREATE TABLE IF NOT EXISTS operating_modes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mode_code TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    constraints JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Action Catalog (Closed vocabulary for AI planner)
CREATE TABLE IF NOT EXISTS action_catalog (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_code TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    preconditions JSONB NOT NULL DEFAULT '{}'::jsonb,
    effects JSONB NOT NULL DEFAULT '{}'::jsonb,
    rollback JSONB NOT NULL DEFAULT '{}'::jsonb,
    risk_level TEXT NOT NULL DEFAULT 'LOW' CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Safety Rules (Deterministic safety policy catalog)
CREATE TABLE IF NOT EXISTS safety_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    condition TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'CRITICAL_BLOCKER' CHECK (severity IN ('WARNING', 'CRITICAL_BLOCKER')),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Historical Incidents (Curated reference cases for few-shot AI retrieval)
CREATE TABLE IF NOT EXISTS historical_incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario TEXT NOT NULL,
    anomaly_type TEXT NOT NULL,
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
    diagnosis JSONB NOT NULL DEFAULT '{}'::jsonb,
    resolution JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Runbook Templates (Deterministic contingency procedures)
CREATE TABLE IF NOT EXISTS runbook_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario TEXT NOT NULL UNIQUE,
    steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    verification JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- System Configuration
CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    version INT NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 2. FLEET & TELEMETRY CORE TABLES
-- ============================================================================

-- Satellites
CREATE TABLE IF NOT EXISTS satellites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    mode TEXT NOT NULL DEFAULT 'NOMINAL' REFERENCES operating_modes(mode_code) ON UPDATE CASCADE,
    status TEXT NOT NULL DEFAULT 'ONLINE' CHECK (status IN ('ONLINE', 'DEGRADED', 'CRITICAL', 'SAFE_HOLD', 'OFFLINE')),
    risk_score NUMERIC(4, 3) NOT NULL DEFAULT 0.0 CHECK (risk_score >= 0.0 AND risk_score <= 1.0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Subsystems
CREATE TABLE IF NOT EXISTS subsystems (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    satellite_id UUID NOT NULL REFERENCES satellites(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'HEALTHY' CHECK (status IN ('HEALTHY', 'DEGRADED', 'FAULT', 'OFF')),
    health_score NUMERIC(5, 2) NOT NULL DEFAULT 100.0 CHECK (health_score >= 0.0 AND health_score <= 100.0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_subsystem_satellite_name UNIQUE (satellite_id, name)
);

-- Telemetry Baselines
CREATE TABLE IF NOT EXISTS telemetry_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    satellite_id UUID REFERENCES satellites(id) ON DELETE CASCADE,
    mode_code TEXT NOT NULL REFERENCES operating_modes(mode_code) ON UPDATE CASCADE,
    subsystem_id UUID REFERENCES subsystems(id) ON DELETE CASCADE,
    metric TEXT NOT NULL,
    min_val DOUBLE PRECISION NOT NULL,
    max_val DOUBLE PRECISION NOT NULL,
    mean DOUBLE PRECISION NOT NULL,
    stddev DOUBLE PRECISION NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_baseline_entry UNIQUE (satellite_id, mode_code, metric)
);

-- Telemetry Streams
CREATE TABLE IF NOT EXISTS telemetry (
    id BIGSERIAL PRIMARY KEY,
    satellite_id UUID NOT NULL REFERENCES satellites(id) ON DELETE CASCADE,
    subsystem_id UUID REFERENCES subsystems(id) ON DELETE SET NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metric TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit TEXT NOT NULL,
    quality TEXT NOT NULL DEFAULT 'GOOD' CHECK (quality IN ('GOOD', 'SUSPECT', 'BAD'))
);

-- ============================================================================
-- 3. DETECTION & INCIDENT WORKFLOW CORE TABLES
-- ============================================================================

-- Anomalies
CREATE TABLE IF NOT EXISTS anomalies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    satellite_id UUID NOT NULL REFERENCES satellites(id) ON DELETE CASCADE,
    subsystem_id UUID REFERENCES subsystems(id) ON DELETE SET NULL,
    type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    confidence NUMERIC(4, 3) NOT NULL DEFAULT 1.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- Incidents
CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anomaly_id UUID REFERENCES anomalies(id) ON DELETE SET NULL,
    satellite_id UUID NOT NULL REFERENCES satellites(id) ON DELETE CASCADE,
    state TEXT NOT NULL DEFAULT 'DETECTED' CHECK (state IN (
        'DETECTED', 'INVESTIGATING', 'DIAGNOSED', 'PLANNING',
        'VALIDATING', 'APPROVED', 'REJECTED', 'EXECUTING',
        'VERIFYING', 'RESOLVED', 'FAILED'
    )),
    title TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'P2' CHECK (priority IN ('P1', 'P2', 'P3', 'P4')),
    severity TEXT NOT NULL DEFAULT 'MEDIUM' CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    confidence NUMERIC(4, 3) CHECK (confidence >= 0.0 AND confidence <= 1.0),
    primary_hypothesis TEXT,
    current_plan_id UUID, -- Circular reference added below
    resolution_code TEXT,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- Agent Runs
CREATE TABLE IF NOT EXISTS agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'RUNNING' CHECK (status IN ('RUNNING', 'COMPLETED', 'FAILED')),
    input JSONB NOT NULL DEFAULT '{}'::jsonb,
    output JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence NUMERIC(4, 3) CHECK (confidence >= 0.0 AND confidence <= 1.0),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);

-- Recovery Plans
CREATE TABLE IF NOT EXISTS recovery_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    version INT NOT NULL DEFAULT 1,
    rationale TEXT NOT NULL,
    actions JSONB NOT NULL DEFAULT '[]'::jsonb,
    risk_level TEXT NOT NULL DEFAULT 'LOW' CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'EXTREME')),
    selected BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_plan_incident_version UNIQUE (incident_id, version)
);

-- Add circular FK for current_plan_id
ALTER TABLE incidents
    DROP CONSTRAINT IF EXISTS fk_incident_current_plan;

ALTER TABLE incidents
    ADD CONSTRAINT fk_incident_current_plan
    FOREIGN KEY (current_plan_id)
    REFERENCES recovery_plans(id)
    ON DELETE SET NULL;

-- Validations (Safety Gate)
CREATE TABLE IF NOT EXISTS validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES recovery_plans(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('PASSED', 'FAILED', 'WARNING')),
    passed_rules JSONB NOT NULL DEFAULT '[]'::jsonb,
    failed_rules JSONB NOT NULL DEFAULT '[]'::jsonb,
    validator_version TEXT NOT NULL DEFAULT 'v1.0.0',
    validated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Command Executions
CREATE TABLE IF NOT EXISTS command_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES recovery_plans(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'EXECUTING', 'SUCCESS', 'FAILED', 'ROLLED_BACK')),
    command JSONB NOT NULL DEFAULT '{}'::jsonb,
    before_state JSONB NOT NULL DEFAULT '{}'::jsonb,
    after_state JSONB NOT NULL DEFAULT '{}'::jsonb,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Audit Events (Append-only)
CREATE TABLE IF NOT EXISTS audit_events (
    id BIGSERIAL PRIMARY KEY,
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'ANOMALY_DETECTED',
        'INCIDENT_OPENED',
        'AGENT_STARTED',
        'AGENT_COMPLETED',
        'PLAN_GENERATED',
        'VALIDATION_COMPLETED',
        'PLAN_REJECTED',
        'PLAN_APPROVED',
        'COMMAND_EXECUTED',
        'OUTCOME_VERIFIED',
        'RUNBOOK_GENERATED',
        'INCIDENT_RESOLVED',
        'MANUAL_OVERRIDE'
    )),
    actor TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 4. PERFORMANCE INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_telemetry_satellite_time ON telemetry (satellite_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_subsystem_metric_time ON telemetry (subsystem_id, metric, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_metric_time ON telemetry (metric, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_anomalies_satellite_started ON anomalies (satellite_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_incidents_state_opened ON incidents (state, opened_at DESC);
CREATE INDEX IF NOT EXISTS idx_incidents_satellite ON incidents (satellite_id, opened_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_incident_time ON audit_events (incident_id, timestamp ASC);
CREATE INDEX IF NOT EXISTS idx_agent_runs_incident_started ON agent_runs (incident_id, started_at ASC);
CREATE INDEX IF NOT EXISTS idx_recovery_plans_incident ON recovery_plans (incident_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_validations_plan ON validations (plan_id);
CREATE INDEX IF NOT EXISTS idx_command_executions_plan ON command_executions (plan_id);
CREATE INDEX IF NOT EXISTS idx_baselines_lookup ON telemetry_baselines (satellite_id, mode_code, metric);
CREATE INDEX IF NOT EXISTS idx_historical_scenario ON historical_incidents (anomaly_type);

-- ============================================================================
-- 5. AI/ML & BACKEND RPC FUNCTIONS
-- ============================================================================

-- Function: build_incident_context(UUID)
-- Returns token-efficient aggregated context for LLM reasoning
CREATE OR REPLACE FUNCTION build_incident_context(p_incident_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_incident RECORD;
    v_satellite RECORD;
    v_anomaly RECORD;
    v_subsystem RECORD;
    v_telemetry_deviations JSONB;
    v_recent_trends JSONB;
    v_similar_cases JSONB;
    v_allowed_actions JSONB;
BEGIN
    SELECT * INTO v_incident FROM incidents WHERE id = p_incident_id;
    IF NOT FOUND THEN
        RETURN jsonb_build_object('error', 'Incident not found', 'incident_id', p_incident_id);
    END IF;

    SELECT * INTO v_satellite FROM satellites WHERE id = v_incident.satellite_id;
    SELECT * INTO v_anomaly FROM anomalies WHERE id = v_incident.anomaly_id;
    IF v_anomaly.subsystem_id IS NOT NULL THEN
        SELECT * INTO v_subsystem FROM subsystems WHERE id = v_anomaly.subsystem_id;
    END IF;

    -- Deviations vs baselines
    WITH latest_readings AS (
        SELECT DISTINCT ON (metric) metric, value AS current_value, unit, quality, timestamp
        FROM telemetry
        WHERE satellite_id = v_incident.satellite_id AND timestamp >= NOW() - INTERVAL '30 minutes'
        ORDER BY metric, timestamp DESC
    ),
    metric_analysis AS (
        SELECT 
            lr.metric, lr.current_value, lr.unit, lr.quality,
            tb.min_val AS baseline_min, tb.max_val AS baseline_max, tb.mean AS baseline_mean,
            ROUND(
                CASE WHEN tb.stddev IS NOT NULL AND tb.stddev > 0 
                     THEN ((lr.current_value - tb.mean) / tb.stddev)::numeric 
                     ELSE 0::numeric END, 2
            ) AS z_score,
            CASE
                WHEN tb.max_val IS NOT NULL AND lr.current_value > tb.max_val THEN 'ELEVATED'
                WHEN tb.min_val IS NOT NULL AND lr.current_value < tb.min_val THEN 'DEPRESSED'
                ELSE 'NOMINAL'
            END AS range_status
        FROM latest_readings lr
        LEFT JOIN telemetry_baselines tb 
            ON tb.satellite_id = v_incident.satellite_id 
           AND tb.metric = lr.metric 
           AND tb.mode_code = v_satellite.mode
    )
    SELECT COALESCE(
        jsonb_agg(
            jsonb_build_object(
                'metric', metric, 'current_value', current_value, 'unit', unit, 'quality', quality,
                'range_status', range_status,
                'baseline', jsonb_build_object('min', baseline_min, 'max', baseline_max, 'mean', baseline_mean),
                'z_score', z_score
            )
        ), '[]'::jsonb
    ) INTO v_telemetry_deviations FROM metric_analysis;

    -- Trends over 15m
    WITH agg_stats AS (
        SELECT metric, ROUND(MIN(value)::numeric, 2) AS min_15m, ROUND(MAX(value)::numeric, 2) AS max_15m,
               ROUND(AVG(value)::numeric, 2) AS avg_15m, COUNT(*) AS sample_count
        FROM telemetry
        WHERE satellite_id = v_incident.satellite_id AND timestamp >= NOW() - INTERVAL '15 minutes'
        GROUP BY metric
    )
    SELECT COALESCE(
        jsonb_object_agg(metric, jsonb_build_object('min', min_15m, 'max', max_15m, 'avg', avg_15m, 'samples', sample_count)),
        '{}'::jsonb
    ) INTO v_recent_trends FROM agg_stats;

    -- Similar historical cases
    SELECT COALESCE(
        jsonb_agg(
            jsonb_build_object('scenario', scenario, 'anomaly_type', anomaly_type, 'diagnosis', diagnosis, 'resolution', resolution)
        ), '[]'::jsonb
    ) INTO v_similar_cases
    FROM (
        SELECT scenario, anomaly_type, diagnosis, resolution
        FROM historical_incidents
        WHERE v_anomaly.type IS NOT NULL AND anomaly_type = v_anomaly.type LIMIT 3
    ) sub;

    -- Allowed actions
    SELECT COALESCE(
        jsonb_agg(
            jsonb_build_object('action_code', action_code, 'description', description, 'risk_level', risk_level)
        ), '[]'::jsonb
    ) INTO v_allowed_actions FROM action_catalog WHERE enabled = TRUE;

    RETURN jsonb_build_object(
        'incident', jsonb_build_object('id', v_incident.id, 'title', v_incident.title, 'state', v_incident.state, 'priority', v_incident.priority, 'severity', v_incident.severity, 'opened_at', v_incident.opened_at),
        'satellite', jsonb_build_object('id', v_satellite.id, 'name', v_satellite.name, 'mode', v_satellite.mode, 'risk_score', v_satellite.risk_score),
        'subsystem', CASE WHEN v_subsystem.id IS NOT NULL THEN jsonb_build_object('name', v_subsystem.name, 'health_score', v_subsystem.health_score, 'status', v_subsystem.status) ELSE NULL END,
        'anomaly', CASE WHEN v_anomaly.id IS NOT NULL THEN jsonb_build_object('type', v_anomaly.type, 'severity', v_anomaly.severity, 'evidence', v_anomaly.evidence) ELSE NULL END,
        'metric_deviations', v_telemetry_deviations,
        'recent_trends_15m', v_recent_trends,
        'similar_historical_cases', v_similar_cases,
        'action_catalog', v_allowed_actions
    );
END;
$$;
