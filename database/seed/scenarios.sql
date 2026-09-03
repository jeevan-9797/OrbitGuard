-- ============================================================================
-- Seed Data: Deterministic Demo Scenarios
-- File: database/seed/scenarios.sql
-- Implements Scenario A (Battery Overheat) and Scenario B (Reaction-wheel Degradation)
-- ============================================================================

-- ============================================================================
-- SCENARIO A: BATTERY OVERHEAT & THERMAL RUNAWAY
-- Satellite: ASTRAEA-1 (a0000000-0000-0000-0000-000000000001)
-- Subsystems: TCS (b0000000-0000-0001-0001-000000000002), EPS (b0000000-0000-0000-0001-000000000001)
-- ============================================================================

-- 1. Injected Rising Telemetry (T - 15 min to T)
INSERT INTO telemetry (satellite_id, subsystem_id, timestamp, metric, value, unit, quality) VALUES
('a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0001-0001-000000000002', NOW() - INTERVAL '12 minutes', 'battery_temperature', 34.2, 'C', 'GOOD'),
('a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0001-0001-000000000002', NOW() - INTERVAL '9 minutes',  'battery_temperature', 38.8, 'C', 'SUSPECT'),
('a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0001-0001-000000000002', NOW() - INTERVAL '6 minutes',  'battery_temperature', 44.5, 'C', 'BAD'),
('a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0001-0001-000000000002', NOW() - INTERVAL '3 minutes',  'battery_temperature', 49.1, 'C', 'BAD'),
('a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0001-000000000001', NOW() - INTERVAL '9 minutes',  'bus_current',         24.8, 'A', 'GOOD'),
('a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0001-000000000001', NOW() - INTERVAL '6 minutes',  'bus_current',         27.2, 'A', 'SUSPECT'),
('a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0004-0001-000000000005', NOW() - INTERVAL '10 minutes', 'payload_power_draw', 385.0, 'W', 'GOOD');

-- 2. Anomaly Record
INSERT INTO anomalies (id, satellite_id, subsystem_id, type, severity, confidence, started_at, evidence) VALUES
('c0000000-0000-0000-0000-000000000001', 
 'a0000000-0000-0000-0000-000000000001', 
 'b0000000-0000-0001-0001-000000000002', 
 'THERMAL_RUNAWAY', 
 'CRITICAL', 
 0.985, 
 NOW() - INTERVAL '9 minutes',
 '{
    "metric": "battery_temperature",
    "trigger_value": 44.5,
    "baseline_max": 32.0,
    "delta_sigma": 5.7,
    "concomitant_metrics": {"bus_current": 27.2, "payload_power_draw": 385.0}
 }'::jsonb)
ON CONFLICT (id) DO NOTHING;

-- 3. Incident Record
INSERT INTO incidents (
    id, anomaly_id, satellite_id, state, title, priority, severity, confidence,
    primary_hypothesis, current_plan_id, resolution_code, opened_at, resolved_at
) VALUES (
    'd0000000-0000-0000-0000-000000000001',
    'c0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'RESOLVED',
    'ASTRAEA-1 EPS Battery Critical Thermal Runaway on Eclipse Exit',
    'P1',
    'CRITICAL',
    0.960,
    'Heater circuit stuck active combined with sustained maximum payload draw leading to runaway battery heating.',
    NULL, -- set to safe plan below
    'AUTONOMOUS_THERMAL_MITIGATION_APPLIED',
    NOW() - INTERVAL '9 minutes',
    NOW() - INTERVAL '1 minute'
)
ON CONFLICT (id) DO NOTHING;

-- 4. Multi-Agent Run Traces
INSERT INTO agent_runs (id, incident_id, agent_name, status, input, output, confidence, started_at, ended_at) VALUES
('e0000000-0000-0000-0000-000000000001',
 'd0000000-0000-0000-0000-000000000001',
 'detector_agent',
 'COMPLETED',
 '{"scan_window_minutes": 15, "satellite": "ASTRAEA-1"}'::jsonb,
 '{"anomaly_detected": true, "type": "THERMAL_RUNAWAY", "subsystem": "TCS", "severity": "CRITICAL"}'::jsonb,
 0.985,
 NOW() - INTERVAL '8 minutes 50 seconds',
 NOW() - INTERVAL '8 minutes 40 seconds'),

('e0000000-0000-0000-0000-000000000002',
 'd0000000-0000-0000-0000-000000000001',
 'diagnostic_agent',
 'COMPLETED',
 '{"scan_window_minutes": 15, "satellite": "ASTRAEA-1", "evidence": ["battery_temperature=44.5C", "bus_current=27.2A"]}'::jsonb,
 '{
    "primary_hypothesis": {
      "cause": "heater_relay_stuck_closed",
      "confidence": 0.96,
      "evidence": ["battery_temperature = 44.5C (baseline_max = 32.0C)", "bus_current = 27.2A"]
    },
    "hypotheses": [
      {
        "cause": "heater_relay_stuck_closed",
        "confidence": 0.96,
        "evidence": ["battery_temperature = 44.5C (baseline_max = 32.0C)", "bus_current = 27.2A"]
      },
      {
        "cause": "excessive_power_consumption",
        "confidence": 0.65,
        "evidence": ["payload_power_draw = 385.0W"]
      }
    ],
    "needs_evidence": false
  }'::jsonb,
 0.960,
 NOW() - INTERVAL '8 minutes 30 seconds',
 NOW() - INTERVAL '8 minutes 05 seconds'),

('e0000000-0000-0000-0000-000000000003',
 'd0000000-0000-0000-0000-000000000001',
 'planner_agent',
 'COMPLETED',
 '{"diagnosis": "TCS heater stuck, battery overheat", "action_catalog_retrieved": 13}'::jsonb,
 '{"candidate_plans_count": 2, "recommended_version": 2}'::jsonb,
 0.940,
 NOW() - INTERVAL '7 minutes 55 seconds',
 NOW() - INTERVAL '7 minutes 20 seconds'),

('e0000000-0000-0000-0000-000000000004',
 'd0000000-0000-0000-0000-000000000001',
 'validator_agent',
 'COMPLETED',
 '{"evaluated_plans": [1, 2], "active_rules": 12}'::jsonb,
 '{"v1_status": "REJECTED (SR-TCS-002 violation)", "v2_status": "APPROVED"}'::jsonb,
 1.000,
 NOW() - INTERVAL '7 minutes 10 seconds',
 NOW() - INTERVAL '6 minutes 55 seconds');

-- 5. Recovery Plans (Unsafe Plan v1 vs Safe Plan v2)
-- Unsafe Plan v1 (Intentionally violates safety rule SR-TCS-002 for demo demonstration)
INSERT INTO recovery_plans (id, incident_id, version, rationale, actions, risk_level, selected) VALUES
('f0000000-0000-0000-0000-000000000001',
 'd0000000-0000-0000-0000-000000000001',
 1,
 'Candidate Plan 1: Keep heater at 20% to prevent overcooling while shedding payload.',
 '{
    "actions": [
      {
        "order": 1,
        "action_code": "REDUCE_POWER_LOAD",
        "parameters": {
          "target": "NON_CRITICAL_PAYLOAD"
        }
      },
      {
        "order": 2,
        "action_code": "PWR_HEATER_DUTY_CYCLE_SET",
        "parameters": {
          "duty_cycle": 20
        }
      }
    ]
  }'::jsonb,
 'HIGH',
 FALSE)
ON CONFLICT (id) DO NOTHING;

-- Safe Plan v2 (Passed safety gate and selected)
INSERT INTO recovery_plans (id, incident_id, version, rationale, actions, risk_level, selected) VALUES
('f0000000-0000-0000-0000-000000000002',
 'd0000000-0000-0000-0000-000000000001',
 2,
 'Candidate Plan 2: Completely inhibit battery heaters (0%), open radiator louvers, and shed payload.',
 '{
    "actions": [
      {
        "order": 1,
        "action_code": "REDUCE_POWER_LOAD",
        "parameters": {
          "target": "NON_CRITICAL_PAYLOAD"
        }
      },
      {
        "order": 2,
        "action_code": "PWR_HEATER_DUTY_CYCLE_SET",
        "parameters": {
          "duty_cycle": 0
        }
      },
      {
        "order": 3,
        "action_code": "TCS_LOUVER_OPEN",
        "parameters": {}
      }
    ]
  }'::jsonb,
 'LOW',
 TRUE)
ON CONFLICT (id) DO NOTHING;

-- Update incident current plan to v2
UPDATE incidents 
SET current_plan_id = 'f0000000-0000-0000-0000-000000000002' 
WHERE id = 'd0000000-0000-0000-0000-000000000001';

-- 6. Validations (Proves deterministic safety gate function)
-- Validation 1: Fails rule SR-TCS-002
INSERT INTO validations (id, plan_id, status, passed_rules, failed_rules, validator_version) VALUES
('10000000-0000-0000-0000-000000000001',
 'f0000000-0000-0000-0000-000000000001',
 'FAILED',
 '["SR-EPS-001", "SR-EPS-002"]'::jsonb,
 '[{"rule_code": "SR-TCS-002", "reason": "Attempted heater_duty_cycle 20% while battery_temperature > 35C. Inhibit violated."}]'::jsonb,
 'v1.2.0-deterministic');

-- Validation 2: Passes all safety rules
INSERT INTO validations (id, plan_id, status, passed_rules, failed_rules, validator_version) VALUES
('10000000-0000-0000-0000-000000000002',
 'f0000000-0000-0000-0000-000000000002',
 'PASSED',
 '["SR-TCS-001", "SR-TCS-002", "SR-EPS-001", "SR-EPS-002", "SR-EXEC-001"]'::jsonb,
 '[]'::jsonb,
 'v1.2.0-deterministic');

-- 7. Command Execution Record
INSERT INTO command_executions (id, plan_id, status, command, before_state, after_state, executed_at) VALUES
('20000000-0000-0000-0000-000000000001',
 'f0000000-0000-0000-0000-000000000002',
 'SUCCESS',
 '{"sequence": ["PWR_SHED_PAYLOAD", "PWR_HEATER_DUTY_CYCLE_SET(0)", "TCS_LOUVER_OPEN"], "auth": "AUTONOMOUS_FLIGHT_CONTROLLER"}'::jsonb,
 '{"battery_temperature": 49.1, "heater_duty_cycle": 75, "louver_state": "CLOSED", "payload_power_w": 385}'::jsonb,
 '{"battery_temperature": 31.8, "heater_duty_cycle": 0, "louver_state": "OPEN", "payload_power_w": 0}'::jsonb,
 NOW() - INTERVAL '5 minutes');

-- 8. Post-Recovery Telemetry Recovery Verification
INSERT INTO telemetry (satellite_id, subsystem_id, timestamp, metric, value, unit, quality) VALUES
('a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0001-0001-000000000002', NOW() - INTERVAL '4 minutes', 'battery_temperature', 42.1, 'C', 'GOOD'),
('a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0001-0001-000000000002', NOW() - INTERVAL '2 minutes', 'battery_temperature', 35.6, 'C', 'GOOD'),
('a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0001-0001-000000000002', NOW() - INTERVAL '30 seconds', 'battery_temperature', 31.8, 'C', 'GOOD');

-- 9. Audit Trail Events (Chronological Story Reconstruction)
INSERT INTO audit_events (incident_id, event_type, actor, payload, timestamp) VALUES
('d0000000-0000-0000-0000-000000000001', 'ANOMALY_DETECTED', 'DETECTOR', '{"metric": "battery_temperature", "value": 44.5, "severity": "CRITICAL"}'::jsonb, NOW() - INTERVAL '9 minutes'),
('d0000000-0000-0000-0000-000000000001', 'INCIDENT_OPENED', 'SYSTEM', '{"title": "ASTRAEA-1 EPS Battery Critical Thermal Runaway", "priority": "P1"}'::jsonb, NOW() - INTERVAL '8 minutes 55 seconds'),
('d0000000-0000-0000-0000-000000000001', 'AGENT_STARTED', 'DIAGNOSTIC_AGENT', '{"agent": "diagnostic_agent", "goal": "Determine thermal runaway root cause"}'::jsonb, NOW() - INTERVAL '8 minutes 30 seconds'),
('d0000000-0000-0000-0000-000000000001', 'AGENT_COMPLETED', 'DIAGNOSTIC_AGENT', '{"confidence": 0.96, "diagnosis": "Heater relay stuck closed"}'::jsonb, NOW() - INTERVAL '8 minutes 05 seconds'),
('d0000000-0000-0000-0000-000000000001', 'PLAN_GENERATED', 'PLANNER', '{"plan_id": "f0000000-0000-0000-0000-000000000001", "version": 1}'::jsonb, NOW() - INTERVAL '7 minutes 40 seconds'),
('d0000000-0000-0000-0000-000000000001', 'VALIDATION_COMPLETED', 'VALIDATOR', '{"plan_id": "f0000000-0000-0000-0000-000000000001", "status": "FAILED", "rule": "SR-TCS-002"}'::jsonb, NOW() - INTERVAL '7 minutes 25 seconds'),
('d0000000-0000-0000-0000-000000000001', 'PLAN_REJECTED', 'SYSTEM', '{"reason": "Hard safety violation on SR-TCS-002", "rejected_plan_version": 1}'::jsonb, NOW() - INTERVAL '7 minutes 20 seconds'),
('d0000000-0000-0000-0000-000000000001', 'PLAN_GENERATED', 'PLANNER', '{"plan_id": "f0000000-0000-0000-0000-000000000002", "version": 2, "actions": ["PWR_SHED_PAYLOAD", "PWR_HEATER_DUTY_CYCLE_SET", "TCS_LOUVER_OPEN"]}'::jsonb, NOW() - INTERVAL '7 minutes 00 seconds'),
('d0000000-0000-0000-0000-000000000001', 'VALIDATION_COMPLETED', 'VALIDATOR', '{"plan_id": "f0000000-0000-0000-0000-000000000002", "status": "PASSED"}'::jsonb, NOW() - INTERVAL '6 minutes 45 seconds'),
('d0000000-0000-0000-0000-000000000001', 'PLAN_APPROVED', 'SYSTEM', '{"plan_version": 2, "authorized_by": "AUTONOMOUS_POLICY"}'::jsonb, NOW() - INTERVAL '6 minutes 40 seconds'),
('d0000000-0000-0000-0000-000000000001', 'COMMAND_EXECUTED', 'SIMULATOR', '{"execution_id": "20000000-0000-0000-0000-000000000001", "commands_sent": 3}'::jsonb, NOW() - INTERVAL '5 minutes'),
('d0000000-0000-0000-0000-000000000001', 'OUTCOME_VERIFIED', 'EVALUATOR', '{"temperature_stabilized_c": 31.8, "thermal_margin_restored": true}'::jsonb, NOW() - INTERVAL '1 minute 30 seconds'),
('d0000000-0000-0000-0000-000000000001', 'INCIDENT_RESOLVED', 'SYSTEM', '{"resolution_code": "AUTONOMOUS_THERMAL_MITIGATION_APPLIED", "duration_seconds": 480}'::jsonb, NOW() - INTERVAL '1 minute');


-- ============================================================================
-- SCENARIO B: REACTION-WHEEL DEGRADATION
-- Satellite: BOREAS-2 (a0000000-0000-0000-0000-000000000002)
-- Subsystem: ADCS (b0000000-0000-0002-0002-000000000003)
-- ============================================================================

INSERT INTO telemetry (satellite_id, subsystem_id, timestamp, metric, value, unit, quality) VALUES
('a0000000-0000-0000-0000-000000000002', 'b0000000-0000-0002-0002-000000000003', NOW() - INTERVAL '10 minutes', 'wheel_vibration_g',    0.092, 'g', 'SUSPECT'),
('a0000000-0000-0000-0000-000000000002', 'b0000000-0000-0002-0002-000000000003', NOW() - INTERVAL '7 minutes',  'wheel_vibration_g',    0.185, 'g', 'BAD'),
('a0000000-0000-0000-0000-000000000002', 'b0000000-0000-0002-0002-000000000003', NOW() - INTERVAL '5 minutes',  'wheel_motor_current',  0.880, 'A', 'BAD'),
('a0000000-0000-0000-0000-000000000002', 'b0000000-0000-0002-0002-000000000003', NOW() - INTERVAL '2 minutes',  'wheel_vibration_g',    0.034, 'g', 'GOOD');

INSERT INTO anomalies (id, satellite_id, subsystem_id, type, severity, confidence, started_at, evidence) VALUES
('c0000000-0000-0000-0000-000000000002',
 'a0000000-0000-0000-0000-000000000002',
 'b0000000-0000-0002-0002-000000000003',
 'REACTION_WHEEL_FRICTION',
 'HIGH',
 0.930,
 NOW() - INTERVAL '7 minutes',
 '{
    "wheel_id": "RW-2",
    "vibration_g": 0.185,
    "motor_current_a": 0.88,
    "baseline_vibration": 0.025
 }'::jsonb)
ON CONFLICT (id) DO NOTHING;

INSERT INTO incidents (
    id, anomaly_id, satellite_id, state, title, priority, severity, confidence,
    primary_hypothesis, current_plan_id, resolution_code, opened_at, resolved_at
) VALUES (
    'd0000000-0000-0000-0000-000000000002',
    'c0000000-0000-0000-0000-000000000002',
    'a0000000-0000-0000-0000-000000000002',
    'RESOLVED',
    'BOREAS-2 ADCS Reaction Wheel 2 High Friction & Mechanical Degradation',
    'P2',
    'HIGH',
    0.920,
    'Degraded dry lubricant in RW-2 bearing causing torque ripple and structural jitter.',
    NULL,
    'MOMENTUM_OFFLOAD_AND_MAGNETORQUER_TRANSITION',
    NOW() - INTERVAL '7 minutes',
    NOW() - INTERVAL '1 minute'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO recovery_plans (id, incident_id, version, rationale, actions, risk_level, selected) VALUES
('f0000000-0000-0000-0000-000000000003',
 'd0000000-0000-0000-0000-000000000002',
 1,
 'Offload RW-2 momentum to RW-1/RW-3 and dump excess momentum with magnetic torquers.',
 '{
    "actions": [
      {
        "order": 1,
        "action_code": "ADCS_RW_WHEEL_OFFLOAD",
        "parameters": {
          "wheel_id": "RW-2"
        }
      },
      {
        "order": 2,
        "action_code": "ADCS_RW_SPEED_DESAT",
        "parameters": {}
      }
    ]
  }'::jsonb,
 'MEDIUM',
 TRUE)
ON CONFLICT (id) DO NOTHING;

UPDATE incidents 
SET current_plan_id = 'f0000000-0000-0000-0000-000000000003' 
WHERE id = 'd0000000-0000-0000-0000-000000000002';

INSERT INTO validations (id, plan_id, status, passed_rules, failed_rules, validator_version) VALUES
('10000000-0000-0000-0000-000000000003',
 'f0000000-0000-0000-0000-000000000003',
 'PASSED',
 '["SR-ADCS-001", "SR-ADCS-002", "SR-EXEC-001"]'::jsonb,
 '[]'::jsonb,
 'v1.2.0-deterministic');

INSERT INTO command_executions (id, plan_id, status, command, before_state, after_state, executed_at) VALUES
('20000000-0000-0000-0000-000000000002',
 'f0000000-0000-0000-0000-000000000003',
 'SUCCESS',
 '{"sequence": ["ADCS_RW_WHEEL_OFFLOAD", "ADCS_RW_SPEED_DESAT"]}'::jsonb,
 '{"wheel_vibration_g": 0.185, "motor_current_a": 0.88, "rw2_rpm": 4600}'::jsonb,
 '{"wheel_vibration_g": 0.034, "motor_current_a": 0.31, "rw2_rpm": 1200}'::jsonb,
 NOW() - INTERVAL '3 minutes');

INSERT INTO audit_events (incident_id, event_type, actor, payload, timestamp) VALUES
('d0000000-0000-0000-0000-000000000002', 'ANOMALY_DETECTED', 'DETECTOR', '{"wheel_id": "RW-2", "vibration_g": 0.185}'::jsonb, NOW() - INTERVAL '7 minutes'),
('d0000000-0000-0000-0000-000000000002', 'INCIDENT_OPENED', 'SYSTEM', '{"title": "BOREAS-2 ADCS RW-2 Friction Anomaly"}'::jsonb, NOW() - INTERVAL '6 minutes 50 seconds'),
('d0000000-0000-0000-0000-000000000002', 'PLAN_GENERATED', 'PLANNER', '{"plan_id": "f0000000-0000-0000-0000-000000000003"}'::jsonb, NOW() - INTERVAL '5 minutes'),
('d0000000-0000-0000-0000-000000000002', 'VALIDATION_COMPLETED', 'VALIDATOR', '{"status": "PASSED"}'::jsonb, NOW() - INTERVAL '4 minutes 30 seconds'),
('d0000000-0000-0000-0000-000000000002', 'COMMAND_EXECUTED', 'SIMULATOR', '{"actions": ["ADCS_RW_WHEEL_OFFLOAD", "ADCS_RW_SPEED_DESAT"]}'::jsonb, NOW() - INTERVAL '3 minutes'),
('d0000000-0000-0000-0000-000000000002', 'OUTCOME_VERIFIED', 'EVALUATOR', '{"vibration_normalized": true, "vibration_g": 0.034}'::jsonb, NOW() - INTERVAL '1 minute 30 seconds'),
('d0000000-0000-0000-0000-000000000002', 'INCIDENT_RESOLVED', 'SYSTEM', '{"resolution_code": "MOMENTUM_OFFLOAD_AND_MAGNETORQUER_TRANSITION"}'::jsonb, NOW() - INTERVAL '1 minute');
