-- ============================================================================
-- Migration 001: Initial Core Schema for Satellite Multi-Agent AI System
-- Authors & Inventors (Smart Horizon Hackathon | Team 098 | Topic DST-1):
--   1. L Steven Dylan
--   2. Karan Sai S
--   3. Kemisetti Hemachandra
--   4. Jeevan M
--   5. Jyotiraditya Pradip Khuman
-- Copyright (c) 2026 Team 098. All rights reserved. Patent Pending.
-- 11 Core Tables: satellites, subsystems, telemetry, anomalies, incidents,
-- agent_runs, recovery_plans, safety_rules, validations, command_executions, audit_events
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Satellites
CREATE TABLE IF NOT EXISTS satellites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(64) NOT NULL UNIQUE,
    norad_id INTEGER,
    international_designator VARCHAR(32),
    orbit_type VARCHAR(32) DEFAULT 'LEO',
    altitude_km NUMERIC(8, 2) DEFAULT 550.00,
    inclination_deg NUMERIC(6, 3) DEFAULT 97.500,
    status VARCHAR(32) DEFAULT 'NOMINAL',
    autonomy_mode VARCHAR(32) DEFAULT 'L4_AUTONOMOUS',
    launch_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Subsystems
CREATE TABLE IF NOT EXISTS subsystems (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    satellite_id UUID REFERENCES satellites(id) ON DELETE CASCADE,
    subsystem_code VARCHAR(32) NOT NULL,
    name VARCHAR(64) NOT NULL,
    status VARCHAR(32) DEFAULT 'HEALTHY',
    health_score NUMERIC(5, 2) DEFAULT 100.00,
    criticality VARCHAR(16) DEFAULT 'MISSION_CRITICAL',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(satellite_id, subsystem_code)
);

-- 3. Telemetry (Time-series metrics)
CREATE TABLE IF NOT EXISTS telemetry (
    id BIGSERIAL PRIMARY KEY,
    satellite_id UUID REFERENCES satellites(id) ON DELETE CASCADE,
    subsystem_id UUID REFERENCES subsystems(id) ON DELETE CASCADE,
    metric_name VARCHAR(64) NOT NULL,
    metric_value NUMERIC(12, 4) NOT NULL,
    unit VARCHAR(24),
    raw_status VARCHAR(24) DEFAULT 'NOMINAL',
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Anomalies
CREATE TABLE IF NOT EXISTS anomalies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    satellite_id UUID REFERENCES satellites(id) ON DELETE CASCADE,
    subsystem_id UUID REFERENCES subsystems(id) ON DELETE SET NULL,
    anomaly_code VARCHAR(64) NOT NULL,
    anomaly_type VARCHAR(64) NOT NULL,
    severity VARCHAR(24) DEFAULT 'MEDIUM',
    confidence NUMERIC(5, 2) DEFAULT 95.00,
    description TEXT,
    metric_name VARCHAR(64),
    observed_value NUMERIC(12, 4),
    expected_value NUMERIC(12, 4),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- 5. Incidents
CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_number VARCHAR(32) UNIQUE NOT NULL,
    satellite_id UUID REFERENCES satellites(id) ON DELETE CASCADE,
    primary_anomaly_id UUID REFERENCES anomalies(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    state VARCHAR(32) DEFAULT 'OPEN',
    severity VARCHAR(24) DEFAULT 'HIGH',
    lead_agent VARCHAR(64),
    root_cause TEXT,
    mttr_seconds NUMERIC(8, 2),
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- 6. Safety Rules
CREATE TABLE IF NOT EXISTS safety_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_code VARCHAR(32) UNIQUE NOT NULL,
    rule_name VARCHAR(128) NOT NULL,
    subsystem_code VARCHAR(32),
    condition_expr TEXT NOT NULL,
    enforcement_level VARCHAR(32) DEFAULT 'STRICT_INTERLOCK',
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Agent Runs (Multi-Agent Swarm execution cycles)
CREATE TABLE IF NOT EXISTS agent_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    agent_name VARCHAR(64) NOT NULL,
    role VARCHAR(64) NOT NULL,
    step_type VARCHAR(32) NOT NULL,
    input_context JSONB DEFAULT '{}'::jsonb,
    output JSONB DEFAULT '{}'::jsonb,
    confidence_score NUMERIC(5, 2),
    duration_ms INTEGER,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- 8. Recovery Plans
CREATE TABLE IF NOT EXISTS recovery_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    proposed_by_agent VARCHAR(64) NOT NULL,
    plan_title VARCHAR(255) NOT NULL,
    actions JSONB NOT NULL DEFAULT '[]'::jsonb,
    status VARCHAR(32) DEFAULT 'PROPOSED',
    estimated_delta_v NUMERIC(8, 4) DEFAULT 0.0,
    estimated_risk_score NUMERIC(5, 2) DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. Validations (Safety interlocks & consensus)
CREATE TABLE IF NOT EXISTS validations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recovery_plan_id UUID REFERENCES recovery_plans(id) ON DELETE CASCADE,
    validator_agent VARCHAR(64) NOT NULL,
    validation_status VARCHAR(32) NOT NULL,
    safety_rule_id UUID REFERENCES safety_rules(id) ON DELETE SET NULL,
    details TEXT,
    validated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. Command Executions
CREATE TABLE IF NOT EXISTS command_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recovery_plan_id UUID REFERENCES recovery_plans(id) ON DELETE CASCADE,
    action_code VARCHAR(64) NOT NULL,
    execution_order INTEGER NOT NULL,
    execution_status VARCHAR(32) DEFAULT 'PENDING',
    dispatched_to VARCHAR(64),
    response_payload JSONB DEFAULT '{}'::jsonb,
    executed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- 11. Audit Events
CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID REFERENCES incidents(id) ON DELETE SET NULL,
    actor VARCHAR(64) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    payload JSONB DEFAULT '{}'::jsonb,
    event_time TIMESTAMPTZ DEFAULT NOW()
);
