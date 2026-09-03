-- ============================================================================
-- Migration 001: Initial Core Schema
-- Satellite Multi-Agent AI System
-- ============================================================================

-- Enable pgcrypto for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Satellites
CREATE TABLE IF NOT EXISTS satellites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    mode TEXT NOT NULL DEFAULT 'NOMINAL',
    status TEXT NOT NULL DEFAULT 'ONLINE' CHECK (status IN ('ONLINE', 'DEGRADED', 'CRITICAL', 'SAFE_HOLD', 'OFFLINE')),
    risk_score NUMERIC(4, 3) NOT NULL DEFAULT 0.0 CHECK (risk_score >= 0.0 AND risk_score <= 1.0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Subsystems
CREATE TABLE IF NOT EXISTS subsystems (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    satellite_id UUID NOT NULL REFERENCES satellites(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'HEALTHY' CHECK (status IN ('HEALTHY', 'DEGRADED', 'FAULT', 'OFF')),
    health_score NUMERIC(5, 2) NOT NULL DEFAULT 100.0 CHECK (health_score >= 0.0 AND health_score <= 100.0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_subsystem_satellite_name UNIQUE (satellite_id, name)
);

-- 3. Telemetry (Time-series operational telemetry stream)
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

-- 4. Anomalies (Flagged abnormal conditions)
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

-- 5. Incidents (Central operational case tracking)
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
    current_plan_id UUID, -- Foreign key to recovery_plans added below
    resolution_code TEXT,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- 6. Agent Runs (Traceability and observability of multi-agent reasoning)
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

-- 7. Recovery Plans (Candidate and chosen recovery strategies)
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

-- Circular FK from incidents.current_plan_id to recovery_plans(id)
ALTER TABLE incidents
    ADD CONSTRAINT fk_incident_current_plan
    FOREIGN KEY (current_plan_id)
    REFERENCES recovery_plans(id)
    ON DELETE SET NULL;

-- 8. Safety Rules (Deterministic safety policy catalog)
CREATE TABLE IF NOT EXISTS safety_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    condition TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'CRITICAL_BLOCKER' CHECK (severity IN ('WARNING', 'CRITICAL_BLOCKER')),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9. Validations (Output of safety gate evaluations)
CREATE TABLE IF NOT EXISTS validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES recovery_plans(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('PASSED', 'FAILED', 'WARNING')),
    passed_rules JSONB NOT NULL DEFAULT '[]'::jsonb,
    failed_rules JSONB NOT NULL DEFAULT '[]'::jsonb,
    validator_version TEXT NOT NULL DEFAULT 'v1.0.0',
    validated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 10. Command Executions (Simulator dispatch and before/after verification)
CREATE TABLE IF NOT EXISTS command_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES recovery_plans(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'EXECUTING', 'SUCCESS', 'FAILED', 'ROLLED_BACK')),
    command JSONB NOT NULL DEFAULT '{}'::jsonb,
    before_state JSONB NOT NULL DEFAULT '{}'::jsonb,
    after_state JSONB NOT NULL DEFAULT '{}'::jsonb,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 11. Audit Events (Append-only immutable event timeline)
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
-- CORE TELEMETRY & WORKFLOW INDEXES
-- ============================================================================

-- Telemetry high-throughput time-series indexes
CREATE INDEX IF NOT EXISTS idx_telemetry_satellite_time 
    ON telemetry (satellite_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_telemetry_subsystem_metric_time 
    ON telemetry (subsystem_id, metric, timestamp DESC);

-- Anomaly detection query index
CREATE INDEX IF NOT EXISTS idx_anomalies_satellite_started 
    ON anomalies (satellite_id, started_at DESC);

-- Incident operational dashboard index
CREATE INDEX IF NOT EXISTS idx_incidents_state_opened 
    ON incidents (state, opened_at DESC);

-- Immutable audit trail chronological replay index
CREATE INDEX IF NOT EXISTS idx_audit_events_incident_time 
    ON audit_events (incident_id, timestamp ASC);

-- Multi-agent workflow visualization index
CREATE INDEX IF NOT EXISTS idx_agent_runs_incident_started 
    ON agent_runs (incident_id, started_at ASC);
