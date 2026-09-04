-- ============================================================================
-- Seed: Scenarios & AI/ML Contracts
-- Includes SCENARIO A: BATTERY OVERHEAT and SCENARIO B: REACTION-WHEEL DEGRADATION
-- ============================================================================

-- ----------------------------------------------------------------------------
-- SCENARIO A: BATTERY OVERHEAT (THERMAL_RUNAWAY)
-- ----------------------------------------------------------------------------

-- Anomaly: Thermal Runaway
INSERT INTO anomalies (id, satellite_id, anomaly_code, anomaly_type, severity, confidence, description, metric_name, observed_value, expected_value, started_at)
VALUES (
    'c0000000-0001-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'ANOM-TH-001',
    'THERMAL_RUNAWAY',
    'CRITICAL',
    98.50,
    'SCENARIO A: BATTERY OVERHEAT - Rapid thermal runaway excursion in Battery Cell #04 exceeding critical 48°C threshold.',
    'EPS_BATT_TEMP_CELL04',
    48.90,
    21.20,
    NOW() - INTERVAL '10 minutes'
) ON CONFLICT (id) DO NOTHING;

-- Incident record
INSERT INTO incidents (id, incident_number, satellite_id, primary_anomaly_id, title, state, severity, lead_agent, root_cause, opened_at)
VALUES (
    'd0000000-0001-0000-0000-000000000001',
    'INC-2024-001',
    'a0000000-0000-0000-0000-000000000001',
    'c0000000-0001-0000-0000-000000000001',
    'SCENARIO A: BATTERY OVERHEAT Thermal Runaway Excursion',
    'MITIGATING',
    'CRITICAL',
    'Agent Alpha::Thermal',
    'Radiator panel receiving unexpected Earth albedo reflection at low elevation combined with heavy bus discharge.',
    NOW() - INTERVAL '10 minutes'
) ON CONFLICT (id) DO NOTHING;

-- Agent Run satisfying AI/ML Contract 1 (output with primary_hypothesis, hypotheses, needs_evidence: false)
INSERT INTO agent_runs (id, incident_id, agent_name, role, step_type, input_context, output, confidence_score, duration_ms, started_at, completed_at)
VALUES (
    'e0000000-0001-0000-0000-000000000001',
    'd0000000-0001-0000-0000-000000000001',
    'Agent Alpha::Thermal',
    'DIAGNOSTICIAN',
    'HYPOTHESIS_GENERATION',
    '{"telemetry_window_s": 300, "trigger_metric": "EPS_BATT_TEMP_CELL04"}'::jsonb,
    '{
        "primary_hypothesis": "Radiator face receiving albedo heat flux causing localized cell #04 thermal runaway",
        "hypotheses": [
            {"id": "H1", "cause": "Albedo reflection leak on radiator", "confidence": 0.89},
            {"id": "H2", "cause": "Internal short in battery cell", "confidence": 0.11}
        ],
        "needs_evidence": false
    }'::jsonb,
    98.50,
    420,
    NOW() - INTERVAL '9 minutes',
    NOW() - INTERVAL '8 minutes 50 seconds'
) ON CONFLICT (id) DO NOTHING;

-- Recovery Plan satisfying AI/ML Contract 2 (actions with order: 1, action_code: "REDUCE_POWER_LOAD", parameters)
INSERT INTO recovery_plans (id, incident_id, proposed_by_agent, plan_title, actions, status, estimated_risk_score)
VALUES (
    'f0000000-0001-0000-0000-000000000001',
    'd0000000-0001-0000-0000-000000000001',
    'Agent Delta::FDIR',
    'SCENARIO A Emergency Thermal Mitigation Plan',
    '[
        {
            "order": 1,
            "action_code": "REDUCE_POWER_LOAD",
            "parameters": {
                "subsystem": "PL",
                "shed_percentage": 50,
                "hold_duration_sec": 300
            }
        },
        {
            "order": 2,
            "action_code": "TCS_SLEW_RADIATOR_SHADE",
            "parameters": {
                "louver_angle_deg": 45
            }
        }
    ]'::jsonb,
    'EXECUTING',
    15.0
) ON CONFLICT (id) DO NOTHING;


-- ----------------------------------------------------------------------------
-- SCENARIO B: REACTION-WHEEL DEGRADATION (REACTION_WHEEL_FRICTION)
-- ----------------------------------------------------------------------------

-- Anomaly: Reaction Wheel Degradation & Friction
INSERT INTO anomalies (id, satellite_id, anomaly_code, anomaly_type, severity, confidence, description, metric_name, observed_value, expected_value, started_at)
VALUES (
    'c0000000-0002-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'ANOM-ADCS-002',
    'REACTION_WHEEL_FRICTION',
    'HIGH',
    96.20,
    'SCENARIO B: REACTION-WHEEL DEGRADATION - Bearing friction buildup on RW-2 resulting in tachometer jitter and pointing vector drift.',
    'ADCS_RW2_BEARING_FRICTION_NM',
    0.045,
    0.005,
    NOW() - INTERVAL '5 minutes'
) ON CONFLICT (id) DO NOTHING;

-- Incident record
INSERT INTO incidents (id, incident_number, satellite_id, primary_anomaly_id, title, state, severity, lead_agent, root_cause, opened_at)
VALUES (
    'd0000000-0002-0000-0000-000000000001',
    'INC-2024-002',
    'a0000000-0000-0000-0000-000000000001',
    'c0000000-0002-0000-0000-000000000001',
    'SCENARIO B: REACTION-WHEEL DEGRADATION Bearing Friction',
    'RESOLVED',
    'HIGH',
    'Agent Beta::AOCS',
    'Cold soak lubricant migration causing RW-2 bearing torque resistance and 14 deg/s drift.',
    NOW() - INTERVAL '5 minutes',
    NOW() - INTERVAL '1 minute'
) ON CONFLICT (id) DO NOTHING;

-- Agent Run for Scenario B
INSERT INTO agent_runs (id, incident_id, agent_name, role, step_type, input_context, output, confidence_score, duration_ms, started_at, completed_at)
VALUES (
    'e0000000-0002-0000-0000-000000000001',
    'd0000000-0002-0000-0000-000000000001',
    'Agent Beta::AOCS',
    'DIAGNOSTICIAN',
    'HYPOTHESIS_GENERATION',
    '{"telemetry_window_s": 180, "trigger_metric": "ADCS_RW2_BEARING_FRICTION_NM"}'::jsonb,
    '{
        "primary_hypothesis": "Reaction wheel RW-2 bearing friction elevation requiring magnetic desaturation",
        "hypotheses": [
            {"id": "H1", "cause": "RW-2 lubrication migration due to thermal cold-soak", "confidence": 0.94},
            {"id": "H2", "cause": "Tachometer encoder optical dirt", "confidence": 0.06}
        ],
        "needs_evidence": false
    }'::jsonb,
    96.20,
    310,
    NOW() - INTERVAL '4 minutes 30 seconds',
    NOW() - INTERVAL '4 minutes 20 seconds'
) ON CONFLICT (id) DO NOTHING;

-- Recovery Plan for Scenario B
INSERT INTO recovery_plans (id, incident_id, proposed_by_agent, plan_title, actions, status, estimated_risk_score)
VALUES (
    'f0000000-0002-0000-0000-000000000001',
    'd0000000-0002-0000-0000-000000000001',
    'Agent Beta::AOCS',
    'SCENARIO B Reaction Wheel Desaturation Sequence',
    '[
        {
            "order": 1,
            "action_code": "REDUCE_POWER_LOAD",
            "parameters": {
                "subsystem": "EPS",
                "shed_percentage": 0,
                "note": "Maintain stable bus during magnetic torquer pulse"
            }
        },
        {
            "order": 2,
            "action_code": "ADCS_DESATURATE_WHEELS",
            "parameters": {
                "target_rpm": 1400,
                "duration_sec": 45
            }
        }
    ]'::jsonb,
    'COMPLETED',
    5.0
) ON CONFLICT (id) DO NOTHING;
