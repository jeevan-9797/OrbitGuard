-- ============================================================================
-- SATELLITE MULTI-AGENT AI SYSTEM — SUPABASE COMPLETE ONE-CLICK SETUP
-- File: database/supabase_all_in_one.sql
-- Production-shaped, verified monolithic PostgreSQL / Supabase Schema & Seeds
-- ============================================================================

-- STEP 1: TABLES, INDEXES & CONSTRAINTS
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


-- STEP 2: SEED KNOWLEDGE (MODES, ACTIONS, SAFETY RULES, RUNBOOKS)
-- ============================================================================
-- Seed Data: Knowledge & Configuration
-- File: database/seed/knowledge.sql
-- ============================================================================

-- 1. OPERATING MODES
INSERT INTO operating_modes (mode_code, description, constraints) VALUES
('NOMINAL', 'Standard orbit operations with payload active and standard power draw.', 
 '{"max_payload_power_w": 250, "attitude_pointing_accuracy_deg": 0.5, "thermal_margin_c": 15}'::jsonb),
('PAYLOAD_OPS', 'High-throughput science observation and imaging mission mode.', 
 '{"max_payload_power_w": 400, "attitude_pointing_accuracy_deg": 0.1, "thermal_margin_c": 10}'::jsonb),
('SAFE_HOLD', 'Survival mode: payload powered off, solar arrays sun-pointing, low-rate comms.', 
 '{"max_payload_power_w": 0, "heater_override": true, "comms_rate_kbps": 9.6}'::jsonb),
('DETUMBLE', 'Rate damping via magnetorquers after separation or anomalous spin.', 
 '{"max_angular_rate_deg_s": 5.0, "payload_enabled": false}'::jsonb),
('COMM_PASS', 'Ground station downlink mode with high-power transmitter active.', 
 '{"transmitter_power_w": 45, "solar_pointing_tolerance_deg": 5.0}'::jsonb),
('ORBIT_RAISE', 'Propulsive maneuvering mode; electric thrusters engaged.', 
 '{"thruster_active": true, "max_continuous_burn_min": 45}'::jsonb)
ON CONFLICT (mode_code) DO UPDATE SET 
    description = EXCLUDED.description,
    constraints = EXCLUDED.constraints;

-- 2. ACTION CATALOG (12 Allowed Actions with Preconditions, Effects, Rollback)
INSERT INTO action_catalog (action_code, description, preconditions, effects, rollback, risk_level, enabled) VALUES
('PWR_SHED_PAYLOAD', 'Disconnect primary payload power bus to mitigate severe electrical/thermal overload.',
 '{"subsystem": "EPS", "allow_in_mode": ["NOMINAL", "PAYLOAD_OPS", "SAFE_HOLD"]}'::jsonb,
 '{"power_draw_delta_w": -200, "thermal_dissipation_delta_c_per_min": -0.8}'::jsonb,
 '{"action_code": "PWR_RESTORE_PAYLOAD", "requires_thermal_margin_c": 20}'::jsonb,
 'LOW', true),

('REDUCE_POWER_LOAD', 'Shed non-critical electrical loads and throttle payload power consumption.',
 '{"subsystem": "EPS", "allow_in_mode": ["NOMINAL", "PAYLOAD_OPS", "SAFE_HOLD"]}'::jsonb,
 '{"power_draw_delta_w": -180, "target_options": ["NON_CRITICAL_PAYLOAD", "COMM_TRANSMITTER", "THERMAL_HEATERS"]}'::jsonb,
 '{"action_code": "RESTORE_POWER_LOAD"}'::jsonb,
 'LOW', true),

('PWR_HEATER_DUTY_CYCLE_SET', 'Adjust battery thermal conditioning heater duty cycle percentage.',
 '{"subsystem": "TCS", "duty_cycle_range": [0, 100]}'::jsonb,
 '{"battery_temp_slope_c_per_hr": 2.5}'::jsonb,
 '{"action_code": "PWR_HEATER_DUTY_CYCLE_SET", "duty_cycle": 50}'::jsonb,
 'LOW', true),

('PWR_BATTERY_CHARGE_RATE_SET', 'Throttle maximum battery charge current from solar arrays.',
 '{"subsystem": "EPS", "rate_range_amps": [0.5, 10.0]}'::jsonb,
 '{"charge_current_delta_a": -3.0, "battery_joule_heating_delta_w": -15}'::jsonb,
 '{"action_code": "PWR_BATTERY_CHARGE_RATE_SET", "rate_amps": 6.0}'::jsonb,
 'MEDIUM', true),

('ADCS_RW_SPEED_DESAT', 'Activate magnetorquers to desaturate reaction wheel momentum.',
 '{"subsystem": "ADCS", "magnetic_field_magnitude_ut_min": 15.0}'::jsonb,
 '{"wheel_momentum_reduction_pct": 80, "torque_nm": 0.05}'::jsonb,
 '{"action_code": "ADCS_RESUME_NOMINAL_RW"}'::jsonb,
 'LOW', true),

('ADCS_RW_WHEEL_OFFLOAD', 'Transfer angular momentum away from degraded reaction wheel RW-2 to RW-1/RW-3.',
 '{"subsystem": "ADCS", "wheel_id": "RW-2", "healthy_wheels_count_min": 2}'::jsonb,
 '{"wheel_load_reduction_pct": 60, "vibration_amp_reduction": 0.04}'::jsonb,
 '{"action_code": "ADCS_EQUALIZE_RW_LOAD"}'::jsonb,
 'MEDIUM', true),

('ADCS_SWITCH_MAGNETORQUER_ONLY', 'Transition attitude control loop exclusively to magnetic torquers, parking reaction wheels.',
 '{"subsystem": "ADCS", "mode": "SAFE_HOLD"}'::jsonb,
 '{"wheel_speed_rpm": 0, "pointing_jitter_deg": 1.2}'::jsonb,
 '{"action_code": "ADCS_SPINUP_RW_ARRAY"}'::jsonb,
 'HIGH', true),

('TCS_LOUVER_OPEN', 'Open thermal radiator louvers to increase radiant heat rejection into deep space.',
 '{"subsystem": "TCS", "space_facing_clearance": true}'::jsonb,
 '{"thermal_rejection_increase_w": 120, "chassis_temp_delta_c_per_min": -0.5}'::jsonb,
 '{"action_code": "TCS_LOUVER_CLOSE"}'::jsonb,
 'LOW', true),

('TCS_LOUVER_CLOSE', 'Close thermal radiator louvers to conserve heat during eclipse or safe-hold.',
 '{"subsystem": "TCS"}'::jsonb,
 '{"thermal_rejection_decrease_w": 100}'::jsonb,
 '{"action_code": "TCS_LOUVER_OPEN"}'::jsonb,
 'LOW', true),

('COMMS_TRANSMITTER_LOW_POWER', 'Reduce S-band transmitter amplification from 25W to 5W.',
 '{"subsystem": "COMMS", "ground_link_margin_db_min": 3.0}'::jsonb,
 '{"power_draw_delta_w": -40, "amplifier_temp_delta_c": -12}'::jsonb,
 '{"action_code": "COMMS_TRANSMITTER_HIGH_POWER"}'::jsonb,
 'LOW', true),

('PL_CAMERA_STANDBY', 'Transition multispectral camera instrument into low-power sensor standby.',
 '{"subsystem": "PAYLOAD", "imaging_buffer_flushed": true}'::jsonb,
 '{"power_draw_delta_w": -110, "detector_temp_stabilized": true}'::jsonb,
 '{"action_code": "PL_CAMERA_ACTIVATE"}'::jsonb,
 'LOW', true),

('OBC_PROCESSOR_THROTTLE_DOWN', 'Lower main flight computer CPU clock frequency from 400MHz to 100MHz.',
 '{"subsystem": "OBC", "attitude_loop_rate_hz_min": 10}'::jsonb,
 '{"processor_power_w": -8, "obc_temp_delta_c": -5}'::jsonb,
 '{"action_code": "OBC_PROCESSOR_MAX_CLOCK"}'::jsonb,
 'MEDIUM', true),

('EPS_SOLAR_ARRAY_OFFPOINT', 'Intentionally off-point solar array gimbal angle by 30 deg to lower solar heat absorption.',
 '{"subsystem": "EPS", "battery_soc_pct_min": 75}'::jsonb,
 '{"solar_heat_input_delta_w": -180, "generation_delta_w": -90}'::jsonb,
 '{"action_code": "EPS_SOLAR_ARRAY_SUN_TRACK"}'::jsonb,
 'HIGH', true)
ON CONFLICT (action_code) DO UPDATE SET
    description = EXCLUDED.description,
    preconditions = EXCLUDED.preconditions,
    effects = EXCLUDED.effects,
    rollback = EXCLUDED.rollback,
    risk_level = EXCLUDED.risk_level,
    enabled = EXCLUDED.enabled;

-- 3. SAFETY RULES (12 Guardrail Constraints)
INSERT INTO safety_rules (rule_code, name, condition, severity, enabled) VALUES
('SR-TCS-001', 'Critical Battery Max Temperature Limit', 
 'battery_temperature <= 45.0', 'CRITICAL_BLOCKER', true),

('SR-TCS-002', 'Battery Heater Inhibit on Elevated Temperature', 
 'heater_duty_cycle == 0 WHEN battery_temperature > 35.0', 'CRITICAL_BLOCKER', true),

('SR-EPS-001', 'Minimum Battery State of Charge (SoC)', 
 'battery_soc_pct >= 40.0', 'CRITICAL_BLOCKER', true),

('SR-EPS-002', 'Maximum Bus Current Draw', 
 'bus_current_a <= 28.0', 'CRITICAL_BLOCKER', true),

('SR-ADCS-001', 'Reaction Wheel Maximum Velocity Limit', 
 'wheel_speed_rpm <= 5800.0', 'CRITICAL_BLOCKER', true),

('SR-ADCS-002', 'RW Vibration Threshold on Mechanical Fault', 
 'wheel_vibration_g <= 0.25', 'WARNING', true),

('SR-ADCS-003', 'Minimum Earth Pointing Tolerance during Science', 
 'attitude_pointing_error_deg <= 1.0 WHEN mode == "PAYLOAD_OPS"', 'WARNING', true),

('SR-COMMS-001', 'Transmitter Overheat Protection', 
 'transmitter_temp_c <= 65.0', 'CRITICAL_BLOCKER', true),

('SR-MODE-001', 'Payload Prohibited in Safe Hold Mode', 
 'payload_power_w == 0 WHEN mode == "SAFE_HOLD"', 'CRITICAL_BLOCKER', true),

('SR-EXEC-001', 'Rollback Specification Required for High-Risk Actions', 
 'has_valid_rollback == true WHEN risk_level == "HIGH"', 'CRITICAL_BLOCKER', true),

('SR-OBC-001', 'Watchdog Heartbeat Margin Minimum', 
 'obc_loop_latency_ms <= 120', 'WARNING', true),

('SR-EPS-003', 'Maximum Battery Charge Voltage Safeguard', 
 'battery_voltage_v <= 32.8', 'CRITICAL_BLOCKER', true)
ON CONFLICT (rule_code) DO UPDATE SET
    name = EXCLUDED.name,
    condition = EXCLUDED.condition,
    severity = EXCLUDED.severity,
    enabled = EXCLUDED.enabled;

-- 4. HISTORICAL INCIDENTS (Curated AI Reference Cases)
INSERT INTO historical_incidents (scenario, anomaly_type, evidence, diagnosis, resolution) VALUES
('Orbit 1420 Eclipse Exit Thermal Spike', 'THERMAL_RUNAWAY',
 '{"battery_temperature": 52.4, "baseline_max": 35.0, "heater_relay_state": "CLOSED_STUCK", "ambient_flux": "SUNLIT"}'::jsonb,
 '{"root_cause": "Heater relay contacts micro-welded closed upon eclipse exit, driving continuous heating during maximum solar flux.", "confidence": 0.96}'::jsonb,
 '{"recovery_actions": ["PWR_HEATER_DUTY_CYCLE_SET(0)", "PWR_SHED_PAYLOAD()", "TCS_LOUVER_OPEN()"], "time_to_recover_min": 14}'::jsonb),

('Orbit 2108 RW-2 Bearing Micro-Spallation', 'REACTION_WHEEL_FRICTION',
 '{"wheel_motor_current_a": 1.45, "nominal_current_a": 0.40, "wheel_temperature_c": 58.2, "bearing_drag_nm": 0.08}'::jsonb,
 '{"root_cause": "Dry lubricant breakdown in reaction wheel #2 bearing causing elevated torque resistance and vibration spikes.", "confidence": 0.91}'::jsonb,
 '{"recovery_actions": ["ADCS_RW_WHEEL_OFFLOAD(RW-2)", "ADCS_RW_SPEED_DESAT()"], "time_to_recover_min": 22}'::jsonb),

('Orbit 0892 EPS Bus Undervoltage Transient', 'POWER_DROP',
 '{"bus_voltage_v": 24.2, "nominal_voltage_v": 28.0, "battery_discharge_rate_a": 18.5, "solar_current_a": 0.2}'::jsonb,
 '{"root_cause": "Solar array drive mechanism slip caused mispointing by 45 degrees relative to Sun vector.", "confidence": 0.88}'::jsonb,
 '{"recovery_actions": ["PWR_SHED_PAYLOAD()", "EPS_SOLAR_ARRAY_ROTATE_SUN()"], "time_to_recover_min": 9}'::jsonb),

('Orbit 3314 S-Band PA Thermal Overdrive', 'TRANSMITTER_OVERHEAT',
 '{"amplifier_temp_c": 71.0, "rf_power_output_w": 28.0, "vswr_ratio": 2.4}'::jsonb,
 '{"root_cause": "Prolonged high-power downlink pass without active attitude cooling off-pointing.", "confidence": 0.94}'::jsonb,
 '{"recovery_actions": ["COMMS_TRANSMITTER_LOW_POWER()", "TCS_LOUVER_OPEN()"], "time_to_recover_min": 11}'::jsonb),

('Orbit 4120 ADCS Rate Sensor Jitter', 'ATTITUDE_JITTER',
 '{"body_rate_pitch_deg_s": 1.8, "target_rate": 0.02, "gyro_kalman_residual": 0.65}'::jsonb,
 '{"root_cause": "IMU optical sensor calibration drift following geomagnetic solar storm event.", "confidence": 0.89}'::jsonb,
 '{"recovery_actions": ["ADCS_SWITCH_MAGNETORQUER_ONLY()", "OBC_PROCESSOR_THROTTLE_DOWN()"], "time_to_recover_min": 35}'::jsonb);

-- 5. RUNBOOK TEMPLATES (Deterministic Contingency Procedures)
INSERT INTO runbook_templates (scenario, steps, warnings, verification) VALUES
('Thermal Runaway Mitigation',
 '[
    {"step": 1, "action": "PWR_SHED_PAYLOAD", "description": "Isolate high-draw science instruments to drop internal thermal dissipation."},
    {"step": 2, "action": "PWR_HEATER_DUTY_CYCLE_SET", "parameters": {"duty_cycle": 0}, "description": "Force heater commanded power to 0% duty cycle."},
    {"step": 3, "action": "TCS_LOUVER_OPEN", "description": "Expose auxiliary radiative surfaces to deep space sink."},
    {"step": 4, "action": "PWR_BATTERY_CHARGE_RATE_SET", "parameters": {"rate_amps": 2.0}, "description": "Reduce electrochemical charging heating."}
  ]'::jsonb,
 '[
    "Do not shed payload if in active mission-critical autonomous reentry sequence.",
    "Verify bus voltage remains above 26.0V when shedding load."
  ]'::jsonb,
 '{"metric": "battery_temperature", "target_slope_c_per_min": -0.3, "target_temp_c": 32.0}'::jsonb),

('Reaction Wheel Friction Degradation Contingency',
 '[
    {"step": 1, "action": "ADCS_RW_WHEEL_OFFLOAD", "parameters": {"wheel_id": "RW-2"}, "description": "Shift angular momentum to redundant wheels."},
    {"step": 2, "action": "ADCS_RW_SPEED_DESAT", "description": "Fire magnetorquers against Earth magnetic field to bleed net momentum."},
    {"step": 3, "action": "ADCS_SWITCH_MAGNETORQUER_ONLY", "description": "If vibration exceeds 0.3g, park reaction wheels and rely on torquers."}
  ]'::jsonb,
 '[
    "Magnetic desaturation is only effective below 1000km LEO altitude.",
    "Expect pointing accuracy degradation from 0.05 deg to 1.5 deg while on torquers."
  ]'::jsonb,
 '{"metric": "wheel_vibration_g", "target_max": 0.08, "motor_current_max_a": 0.5}'::jsonb);

-- 6. SYSTEM CONFIGURATION
INSERT INTO system_config (key, value, version) VALUES
('telemetry_stream_rate_ms', '{"default_rate_ms": 1000, "fast_telemetry_ms": 250, "anomaly_zoom_ms": 100}'::jsonb, 1),
('demo_mode', '{"current_scenario": "SCENARIO_A", "available_scenarios": ["SCENARIO_A", "SCENARIO_B"], "auto_recover": false}'::jsonb, 1),
('safety_gate_mode', '{"strict_mode": true, "allow_operator_bypass": true, "required_approvals": 1}'::jsonb, 1),
('agent_confidence_thresholds', '{"detection_min": 0.80, "diagnosis_min": 0.75, "plan_auto_approve_min": 0.95}'::jsonb, 1)
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    version = system_config.version + 1,
    updated_at = NOW();


-- STEP 3: SEED FLEET SPACECRAFT & SUBSYSTEMS (REQUIRED FOR FOREIGN KEYS)
-- ============================================================================
-- Seed Data: Satellites and Subsystems
-- File: database/seed/satellites.sql
-- Deterministic UUIDs used for reproducible cross-table linking and demo resets
-- ============================================================================

-- 1. SATELLITES (6 Constellation Satellites)
INSERT INTO satellites (id, name, mode, status, risk_score, created_at) VALUES
('a0000000-0000-0000-0000-000000000001', 'ASTRAEA-1', 'NOMINAL', 'ONLINE', 0.120, NOW() - INTERVAL '30 days'),
('a0000000-0000-0000-0000-000000000002', 'BOREAS-2', 'NOMINAL', 'ONLINE', 0.180, NOW() - INTERVAL '28 days'),
('a0000000-0000-0000-0000-000000000003', 'CHRONOS-3', 'PAYLOAD_OPS', 'ONLINE', 0.050, NOW() - INTERVAL '25 days'),
('a0000000-0000-0000-0000-000000000004', 'DAEDALUS-4', 'NOMINAL', 'ONLINE', 0.080, NOW() - INTERVAL '20 days'),
('a0000000-0000-0000-0000-000000000005', 'EOS-5', 'PAYLOAD_OPS', 'ONLINE', 0.150, NOW() - INTERVAL '15 days'),
('a0000000-0000-0000-0000-000000000006', 'FORNAX-6', 'COMM_PASS', 'ONLINE', 0.040, NOW() - INTERVAL '10 days')
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    mode = EXCLUDED.mode,
    status = EXCLUDED.status,
    risk_score = EXCLUDED.risk_score;

-- 2. SUBSYSTEMS (6 Subsystems per Satellite = 36 Subsystem records)

-- Subsystems for ASTRAEA-1 (Demo Scenario A Host)
INSERT INTO subsystems (id, satellite_id, name, status, health_score) VALUES
('b0000000-0000-0000-0001-000000000001', 'a0000000-0000-0000-0000-000000000001', 'EPS', 'HEALTHY', 98.5),
('b0000000-0000-0001-0001-000000000002', 'a0000000-0000-0000-0000-000000000001', 'TCS', 'HEALTHY', 97.0),
('b0000000-0000-0002-0001-000000000003', 'a0000000-0000-0000-0000-000000000001', 'ADCS', 'HEALTHY', 99.0),
('b0000000-0000-0003-0001-000000000004', 'a0000000-0000-0000-0000-000000000001', 'COMMS', 'HEALTHY', 100.0),
('b0000000-0000-0004-0001-000000000005', 'a0000000-0000-0000-0000-000000000001', 'PAYLOAD', 'HEALTHY', 98.0),
('b0000000-0000-0005-0001-000000000006', 'a0000000-0000-0000-0000-000000000001', 'OBC', 'HEALTHY', 100.0)
ON CONFLICT (id) DO UPDATE SET status = EXCLUDED.status, health_score = EXCLUDED.health_score;

-- Subsystems for BOREAS-2 (Demo Scenario B Host)
INSERT INTO subsystems (id, satellite_id, name, status, health_score) VALUES
('b0000000-0000-0000-0002-000000000001', 'a0000000-0000-0000-0000-000000000002', 'EPS', 'HEALTHY', 99.0),
('b0000000-0000-0001-0002-000000000002', 'a0000000-0000-0000-0000-000000000002', 'TCS', 'HEALTHY', 99.5),
('b0000000-0000-0002-0002-000000000003', 'a0000000-0000-0000-0000-000000000002', 'ADCS', 'HEALTHY', 94.0),
('b0000000-0000-0003-0002-000000000004', 'a0000000-0000-0000-0000-000000000002', 'COMMS', 'HEALTHY', 99.0),
('b0000000-0000-0004-0002-000000000005', 'a0000000-0000-0000-0000-000000000002', 'PAYLOAD', 'HEALTHY', 97.5),
('b0000000-0000-0005-0002-000000000006', 'a0000000-0000-0000-0000-000000000002', 'OBC', 'HEALTHY', 100.0)
ON CONFLICT (id) DO UPDATE SET status = EXCLUDED.status, health_score = EXCLUDED.health_score;

-- Subsystems for CHRONOS-3
INSERT INTO subsystems (id, satellite_id, name, status, health_score) VALUES
('b0000000-0000-0000-0003-000000000001', 'a0000000-0000-0000-0000-000000000003', 'EPS', 'HEALTHY', 99.5),
('b0000000-0000-0001-0003-000000000002', 'a0000000-0000-0000-0000-000000000003', 'TCS', 'HEALTHY', 98.0),
('b0000000-0000-0002-0003-000000000003', 'a0000000-0000-0000-0000-000000000003', 'ADCS', 'HEALTHY', 98.5),
('b0000000-0000-0003-0003-000000000004', 'a0000000-0000-0000-0000-000000000003', 'COMMS', 'HEALTHY', 100.0),
('b0000000-0000-0004-0003-000000000005', 'a0000000-0000-0000-0000-000000000003', 'PAYLOAD', 'HEALTHY', 100.0),
('b0000000-0000-0005-0003-000000000006', 'a0000000-0000-0000-0000-000000000003', 'OBC', 'HEALTHY', 100.0)
ON CONFLICT (id) DO UPDATE SET status = EXCLUDED.status, health_score = EXCLUDED.health_score;

-- Subsystems for DAEDALUS-4
INSERT INTO subsystems (id, satellite_id, name, status, health_score) VALUES
('b0000000-0000-0000-0004-000000000001', 'a0000000-0000-0000-0000-000000000004', 'EPS', 'HEALTHY', 99.0),
('b0000000-0000-0001-0004-000000000002', 'a0000000-0000-0000-0000-000000000004', 'TCS', 'HEALTHY', 100.0),
('b0000000-0000-0002-0004-000000000003', 'a0000000-0000-0000-0000-000000000004', 'ADCS', 'HEALTHY', 97.0),
('b0000000-0000-0003-0004-000000000004', 'a0000000-0000-0000-0000-000000000004', 'COMMS', 'HEALTHY', 99.0),
('b0000000-0000-0004-0004-000000000005', 'a0000000-0000-0000-0000-000000000004', 'PAYLOAD', 'HEALTHY', 98.0),
('b0000000-0000-0005-0004-000000000006', 'a0000000-0000-0000-0000-000000000004', 'OBC', 'HEALTHY', 99.0)
ON CONFLICT (id) DO UPDATE SET status = EXCLUDED.status, health_score = EXCLUDED.health_score;

-- Subsystems for EOS-5
INSERT INTO subsystems (id, satellite_id, name, status, health_score) VALUES
('b0000000-0000-0000-0005-000000000001', 'a0000000-0000-0000-0000-000000000005', 'EPS', 'HEALTHY', 98.0),
('b0000000-0000-0001-0005-000000000002', 'a0000000-0000-0000-0000-000000000005', 'TCS', 'HEALTHY', 96.5),
('b0000000-0000-0002-0005-000000000003', 'a0000000-0000-0000-0000-000000000005', 'ADCS', 'HEALTHY', 98.0),
('b0000000-0000-0003-0005-000000000004', 'a0000000-0000-0000-0000-000000000005', 'COMMS', 'HEALTHY', 100.0),
('b0000000-0000-0004-0005-000000000005', 'a0000000-0000-0000-0000-000000000005', 'PAYLOAD', 'HEALTHY', 97.0),
('b0000000-0000-0005-0005-000000000006', 'a0000000-0000-0000-0000-000000000005', 'OBC', 'HEALTHY', 100.0)
ON CONFLICT (id) DO UPDATE SET status = EXCLUDED.status, health_score = EXCLUDED.health_score;

-- Subsystems for FORNAX-6
INSERT INTO subsystems (id, satellite_id, name, status, health_score) VALUES
('b0000000-0000-0000-0006-000000000001', 'a0000000-0000-0000-0000-000000000006', 'EPS', 'HEALTHY', 100.0),
('b0000000-0000-0001-0006-000000000002', 'a0000000-0000-0000-0000-000000000006', 'TCS', 'HEALTHY', 99.0),
('b0000000-0000-0002-0006-000000000003', 'a0000000-0000-0000-0000-000000000006', 'ADCS', 'HEALTHY', 99.5),
('b0000000-0000-0003-0006-000000000004', 'a0000000-0000-0000-0000-000000000006', 'COMMS', 'HEALTHY', 99.0),
('b0000000-0000-0004-0006-000000000005', 'a0000000-0000-0000-0000-000000000006', 'PAYLOAD', 'HEALTHY', 100.0),
('b0000000-0000-0005-0006-000000000006', 'a0000000-0000-0000-0000-000000000006', 'OBC', 'HEALTHY', 100.0)
ON CONFLICT (id) DO UPDATE SET status = EXCLUDED.status, health_score = EXCLUDED.health_score;


-- STEP 4: SEED TELEMETRY BASELINES & INITIAL STREAMS
-- ============================================================================
-- Seed Data: Telemetry Baselines and Initial Telemetry Streams
-- File: database/seed/telemetry.sql
-- ============================================================================

-- 1. TELEMETRY BASELINES FOR DEMO SATELLITES IN 'NOMINAL' MODE

-- ASTRAEA-1 (Scenario A Base)
INSERT INTO telemetry_baselines (satellite_id, mode_code, subsystem_id, metric, min_val, max_val, mean, stddev) VALUES
-- EPS
('a0000000-0000-0000-0000-000000000001', 'NOMINAL', 'b0000000-0000-0000-0001-000000000001', 'battery_voltage', 28.0, 32.4, 30.2, 0.4),
('a0000000-0000-0000-0000-000000000001', 'NOMINAL', 'b0000000-0000-0000-0001-000000000001', 'battery_soc_pct', 70.0, 98.0, 85.0, 3.5),
('a0000000-0000-0000-0000-000000000001', 'NOMINAL', 'b0000000-0000-0000-0001-000000000001', 'bus_current', 8.0, 16.0, 12.1, 1.2),
('a0000000-0000-0000-0000-000000000001', 'NOMINAL', 'b0000000-0000-0000-0001-000000000001', 'solar_array_current', 0.0, 22.0, 15.4, 2.8),
-- TCS
('a0000000-0000-0000-0000-000000000001', 'NOMINAL', 'b0000000-0000-0001-0001-000000000002', 'battery_temperature', 15.0, 32.0, 23.5, 2.1),
('a0000000-0000-0000-0000-000000000001', 'NOMINAL', 'b0000000-0000-0001-0001-000000000002', 'chassis_temp', 10.0, 28.0, 18.2, 1.5),
('a0000000-0000-0000-0000-000000000001', 'NOMINAL', 'b0000000-0000-0001-0001-000000000002', 'heater_duty_cycle', 0.0, 60.0, 25.0, 8.0),
-- ADCS
('a0000000-0000-0000-0000-000000000001', 'NOMINAL', 'b0000000-0000-0002-0001-000000000003', 'wheel_speed_rpm', 1500.0, 3800.0, 2600.0, 320.0),
('a0000000-0000-0000-0000-000000000001', 'NOMINAL', 'b0000000-0000-0002-0001-000000000003', 'wheel_vibration_g', 0.01, 0.06, 0.03, 0.008),
('a0000000-0000-0000-0000-000000000001', 'NOMINAL', 'b0000000-0000-0002-0001-000000000003', 'attitude_pointing_error', 0.01, 0.25, 0.08, 0.03),
-- COMMS
('a0000000-0000-0000-0000-000000000001', 'NOMINAL', 'b0000000-0000-0003-0001-000000000004', 'transmitter_temp', 22.0, 48.0, 35.0, 3.2),
('a0000000-0000-0000-0000-000000000001', 'NOMINAL', 'b0000000-0000-0003-0001-000000000004', 'rf_output_power', 5.0, 25.0, 15.0, 1.5),
-- PAYLOAD
('a0000000-0000-0000-0000-000000000001', 'NOMINAL', 'b0000000-0000-0004-0001-000000000005', 'payload_power_draw', 50.0, 220.0, 140.0, 15.0),
-- OBC
('a0000000-0000-0000-0000-000000000001', 'NOMINAL', 'b0000000-0000-0005-0001-000000000006', 'cpu_load_pct', 15.0, 55.0, 32.0, 6.0),
('a0000000-0000-0000-0000-000000000001', 'NOMINAL', 'b0000000-0000-0005-0001-000000000006', 'obc_temperature', 20.0, 42.0, 28.5, 2.4)
ON CONFLICT (satellite_id, mode_code, metric) DO UPDATE SET
    min_val = EXCLUDED.min_val,
    max_val = EXCLUDED.max_val,
    mean = EXCLUDED.mean,
    stddev = EXCLUDED.stddev;

-- BOREAS-2 (Scenario B Base)
INSERT INTO telemetry_baselines (satellite_id, mode_code, subsystem_id, metric, min_val, max_val, mean, stddev) VALUES
('a0000000-0000-0000-0000-000000000002', 'NOMINAL', 'b0000000-0000-0002-0002-000000000003', 'wheel_speed_rpm', 1200.0, 3600.0, 2400.0, 280.0),
('a0000000-0000-0000-0000-000000000002', 'NOMINAL', 'b0000000-0000-0002-0002-000000000003', 'wheel_vibration_g', 0.01, 0.05, 0.025, 0.005),
('a0000000-0000-0000-0000-000000000002', 'NOMINAL', 'b0000000-0000-0002-0002-000000000003', 'wheel_motor_current', 0.15, 0.45, 0.28, 0.04),
('a0000000-0000-0000-0000-000000000002', 'NOMINAL', 'b0000000-0000-0001-0002-000000000002', 'battery_temperature', 14.0, 30.0, 22.0, 1.8),
('a0000000-0000-0000-0000-000000000002', 'NOMINAL', 'b0000000-0000-0000-0002-000000000001', 'battery_voltage', 28.2, 32.2, 30.1, 0.3)
ON CONFLICT (satellite_id, mode_code, metric) DO UPDATE SET
    min_val = EXCLUDED.min_val,
    max_val = EXCLUDED.max_val,
    mean = EXCLUDED.mean,
    stddev = EXCLUDED.stddev;


-- 2. DETERMINISTIC NORMAL TELEMETRY SEED (Sample window: T - 30 min to T - 1 min)
-- Provides nominal curves for dashboard charts before incident injection

INSERT INTO telemetry (satellite_id, subsystem_id, timestamp, metric, value, unit, quality)
SELECT 
    'a0000000-0000-0000-0000-000000000001'::uuid,
    'b0000000-0000-0001-0001-000000000002'::uuid, -- TCS
    NOW() - (mins || ' minutes')::interval,
    'battery_temperature',
    ROUND((23.0 + (RANDOM() * 1.5 - 0.75))::numeric, 2),
    'C',
    'GOOD'
FROM generate_series(1, 30) AS mins;

INSERT INTO telemetry (satellite_id, subsystem_id, timestamp, metric, value, unit, quality)
SELECT 
    'a0000000-0000-0000-0000-000000000001'::uuid,
    'b0000000-0000-0000-0001-000000000001'::uuid, -- EPS
    NOW() - (mins || ' minutes')::interval,
    'battery_voltage',
    ROUND((30.4 - (mins * 0.02) + (RANDOM() * 0.1))::numeric, 2),
    'V',
    'GOOD'
FROM generate_series(1, 30) AS mins;

INSERT INTO telemetry (satellite_id, subsystem_id, timestamp, metric, value, unit, quality)
SELECT 
    'a0000000-0000-0000-0000-000000000001'::uuid,
    'b0000000-0000-0004-0001-000000000005'::uuid, -- PAYLOAD
    NOW() - (mins || ' minutes')::interval,
    'payload_power_draw',
    ROUND((145.0 + (RANDOM() * 10.0 - 5.0))::numeric, 2),
    'W',
    'GOOD'
FROM generate_series(1, 30) AS mins;

-- BOREAS-2 Nominal Attitude readings
INSERT INTO telemetry (satellite_id, subsystem_id, timestamp, metric, value, unit, quality)
SELECT 
    'a0000000-0000-0000-0000-000000000002'::uuid,
    'b0000000-0000-0002-0002-000000000003'::uuid, -- ADCS
    NOW() - (mins || ' minutes')::interval,
    'wheel_vibration_g',
    ROUND((0.025 + (RANDOM() * 0.006 - 0.003))::numeric, 4),
    'g',
    'GOOD'
FROM generate_series(1, 30) AS mins;

INSERT INTO telemetry (satellite_id, subsystem_id, timestamp, metric, value, unit, quality)
SELECT 
    'a0000000-0000-0000-0000-000000000002'::uuid,
    'b0000000-0000-0002-0002-000000000003'::uuid, -- ADCS
    NOW() - (mins || ' minutes')::interval,
    'wheel_speed_rpm',
    ROUND((2400.0 + (RANDOM() * 80.0 - 40.0))::numeric, 1),
    'RPM',
    'GOOD'
FROM generate_series(1, 30) AS mins;


-- STEP 5: STORED PROCEDURES (RESET PROCEDURE CALLABLE ON DEMAND)
-- ============================================================================
-- Demo Reset Script & Function
-- File: database/reset_demo.sql
-- Resets the database to a clean, reproducible state for live demonstrations
-- ============================================================================

-- Function callable from backend or Supabase RPC: -- SELECT reset_demo(); (Callable on demand)
CREATE OR REPLACE FUNCTION reset_demo()
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_start_time TIMESTAMPTZ := clock_timestamp();
BEGIN
    -- 1. Disconnect circular foreign keys before truncating
    UPDATE incidents SET current_plan_id = NULL;

    -- 2. Clear dynamic operational workflow tables in reverse dependency order
    DELETE FROM audit_events;
    DELETE FROM command_executions;
    DELETE FROM validations;
    DELETE FROM recovery_plans;
    DELETE FROM agent_runs;
    DELETE FROM incidents;
    DELETE FROM anomalies;

    -- 3. Clear anomalous telemetry (retain only normal baseline telemetry)
    DELETE FROM telemetry WHERE quality IN ('BAD', 'SUSPECT');

    -- 4. Reset Fleet and Subsystem health statuses
    UPDATE satellites 
    SET mode = 'NOMINAL',
        status = 'ONLINE',
        risk_score = 0.050;

    UPDATE subsystems
    SET status = 'HEALTHY',
        health_score = 100.0;

    -- 5. Restore System Config to default demo settings
    UPDATE system_config
    SET value = '{"current_scenario": "SCENARIO_A", "available_scenarios": ["SCENARIO_A", "SCENARIO_B"], "auto_recover": false}'::jsonb
    WHERE key = 'demo_mode';

    -- 6. Re-seed normal recent telemetry window for ASTRAEA-1 and BOREAS-2
    DELETE FROM telemetry WHERE timestamp >= NOW() - INTERVAL '30 minutes';

    INSERT INTO telemetry (satellite_id, subsystem_id, timestamp, metric, value, unit, quality)
    SELECT 
        'a0000000-0000-0000-0000-000000000001'::uuid,
        'b0000000-0000-0001-0001-000000000002'::uuid, -- TCS
        NOW() - (mins || ' minutes')::interval,
        'battery_temperature',
        ROUND((23.0 + (RANDOM() * 1.5 - 0.75))::numeric, 2),
        'C',
        'GOOD'
    FROM generate_series(1, 30) AS mins;

    INSERT INTO telemetry (satellite_id, subsystem_id, timestamp, metric, value, unit, quality)
    SELECT 
        'a0000000-0000-0000-0000-000000000001'::uuid,
        'b0000000-0000-0000-0001-000000000001'::uuid, -- EPS
        NOW() - (mins || ' minutes')::interval,
        'battery_voltage',
        ROUND((30.4 - (mins * 0.02) + (RANDOM() * 0.1))::numeric, 2),
        'V',
        'GOOD'
    FROM generate_series(1, 30) AS mins;

    INSERT INTO telemetry (satellite_id, subsystem_id, timestamp, metric, value, unit, quality)
    SELECT 
        'a0000000-0000-0000-0000-000000000002'::uuid,
        'b0000000-0000-0002-0002-000000000003'::uuid, -- ADCS
        NOW() - (mins || ' minutes')::interval,
        'wheel_vibration_g',
        ROUND((0.025 + (RANDOM() * 0.006 - 0.003))::numeric, 4),
        'g',
        'GOOD'
    FROM generate_series(1, 30) AS mins;

    -- Return JSON status summary
    RETURN jsonb_build_object(
        'status', 'SUCCESS',
        'message', 'Fleet reset to nominal state. Incident and audit history cleared.',
        'elapsed_ms', ROUND(EXTRACT(MILLISECONDS FROM (clock_timestamp() - v_start_time))::numeric, 2)
    );
END;
$$;

-- Executable reset block when running script directly
-- SELECT reset_demo(); (Callable on demand)


-- STEP 6: VERIFY FLEET SETUP
SELECT count(*) AS total_satellites FROM satellites;
