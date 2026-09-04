-- ============================================================================
-- Migration 002: Knowledge and Configuration Tables
-- 6 Tables: action_catalog, operating_modes, telemetry_baselines,
-- historical_incidents, runbook_templates, system_config
-- ============================================================================

-- 1. Action Catalog
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

-- 2. Operating Modes
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

-- 3. Telemetry Baselines
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

-- 4. Historical Incidents
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

-- 5. Runbook Templates
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

-- 6. System Config
CREATE TABLE IF NOT EXISTS system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(64) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
