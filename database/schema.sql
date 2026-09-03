-- ============================================================================
-- Satellite Multi-Agent AI System - Complete Consolidated Schema
-- Smart Horizon 48-Hour Hackathon | Team 098 | Topic: DST-1
-- Authors & Inventors:
--   1. L Steven Dylan
--   2. Karan Sai S
--   3. Kemisetti Hemachandra
--   4. Jeevan M
--   5. Jyotiraditya Pradip Khuman
-- Copyright (c) 2026 Team 098. All rights reserved. Patent Pending.
-- Core Tables (11) + Knowledge/Config Tables (6) = 17 Tables Total
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- CORE TABLES (11)
-- ============================================================================

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

-- 3. Telemetry (High-throughput metric streams)
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

-- 7. Agent Runs (Swarm cycles)
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

-- 9. Validations
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

-- ============================================================================
-- KNOWLEDGE AND CONFIGURATION TABLES (6)
-- ============================================================================

-- 12. Action Catalog
CREATE TABLE IF NOT EXISTS action_catalog (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action_code VARCHAR(64) UNIQUE NOT NULL,
    subsystem_code VARCHAR(32) NOT NULL,
    action_name VARCHAR(128) NOT NULL,
    description TEXT,
    risk_level VARCHAR(16) DEFAULT 'LOW',
    default_parameters JSONB DEFAULT '{}'::jsonb,
    is_reversible BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 13. Operating Modes
CREATE TABLE IF NOT EXISTS operating_modes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mode_code VARCHAR(32) UNIQUE NOT NULL,
    mode_name VARCHAR(64) NOT NULL,
    power_budget_w NUMERIC(8, 2),
    thermal_envelope VARCHAR(64),
    allowed_subsystems JSONB DEFAULT '[]'::jsonb,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 14. Telemetry Baselines
CREATE TABLE IF NOT EXISTS telemetry_baselines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subsystem_code VARCHAR(32) NOT NULL,
    metric_name VARCHAR(64) NOT NULL,
    orbit_phase VARCHAR(32) DEFAULT 'ANY',
    mean_val NUMERIC(12, 4) NOT NULL,
    std_dev NUMERIC(12, 4) NOT NULL,
    min_nominal NUMERIC(12, 4) NOT NULL,
    max_nominal NUMERIC(12, 4) NOT NULL,
    unit VARCHAR(24),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(subsystem_code, metric_name, orbit_phase)
);

-- 15. Historical Incidents
CREATE TABLE IF NOT EXISTS historical_incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_code VARCHAR(64) UNIQUE NOT NULL,
    orbit_number VARCHAR(32),
    subsystem_code VARCHAR(32) NOT NULL,
    root_cause TEXT NOT NULL,
    resolution_summary TEXT NOT NULL,
    recovery_strategy VARCHAR(128),
    mttr_seconds NUMERIC(8, 2),
    lessons_learned TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 16. Runbook Templates
CREATE TABLE IF NOT EXISTS runbook_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_code VARCHAR(64) UNIQUE NOT NULL,
    subsystem_code VARCHAR(32) NOT NULL,
    title VARCHAR(128) NOT NULL,
    trigger_criteria JSONB DEFAULT '{}'::jsonb,
    action_sequence JSONB DEFAULT '[]'::jsonb,
    fallback_sequence JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 17. System Config
CREATE TABLE IF NOT EXISTS system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(64) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
