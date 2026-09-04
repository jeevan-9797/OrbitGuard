-- ============================================================================
-- Migration 002: Knowledge and Configuration Schema
-- Satellite Multi-Agent AI System
-- ============================================================================

-- 1. Action Catalog (Closed vocabulary of valid actions for AI planner)
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

-- 2. Operating Modes (Satellite flight modes and constraints)
CREATE TABLE IF NOT EXISTS operating_modes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mode_code TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    constraints JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Telemetry Baselines (Statistical normal reference ranges for metrics)
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

-- 4. Historical Incidents (Curated reference cases for few-shot AI retrieval)
CREATE TABLE IF NOT EXISTS historical_incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario TEXT NOT NULL,
    anomaly_type TEXT NOT NULL,
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
    diagnosis JSONB NOT NULL DEFAULT '{}'::jsonb,
    resolution JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Runbook Templates (Deterministic contingency procedures)
CREATE TABLE IF NOT EXISTS runbook_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario TEXT NOT NULL UNIQUE,
    steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    verification JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. System Configuration (Dynamic application and demo parameters)
CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    version INT NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
