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
