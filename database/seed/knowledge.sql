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
