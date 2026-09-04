-- ============================================================================
-- Reset Demo Procedure
-- Restores all satellites, telemetry, and scenarios to initial baseline state
-- ============================================================================

CREATE OR REPLACE FUNCTION reset_demo()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    -- 1. Reset command executions and recovery validations
    DELETE FROM command_executions;
    DELETE FROM validations;
    DELETE FROM recovery_plans;
    DELETE FROM agent_runs;

    -- 2. Reset audit events and incidents
    DELETE FROM audit_events;
    DELETE FROM incidents;
    DELETE FROM anomalies;

    -- 3. Restore satellite health scores and states to nominal
    UPDATE satellites
    SET status = 'NOMINAL',
        autonomy_mode = 'L4_AUTONOMOUS',
        altitude_km = 541.80,
        updated_at = NOW();

    UPDATE subsystems
    SET status = 'HEALTHY',
        health_score = 100.00,
        updated_at = NOW();

    -- 4. Re-inject nominal telemetry baseline
    INSERT INTO telemetry (satellite_id, subsystem_id, metric_name, metric_value, unit, raw_status, captured_at)
    VALUES
        ('a0000000-0000-0000-0000-000000000001', 'b0000000-0001-0000-0000-000000000001', 'EPS_BATT_TEMP_CELL04', 21.2, '°C', 'NOMINAL', NOW()),
        ('a0000000-0000-0000-0000-000000000001', 'b0000000-0001-0000-0000-000000000002', 'ADCS_GYRO_Z_RATE', 0.00, 'deg/s', 'NOMINAL', NOW()),
        ('a0000000-0000-0000-0000-000000000001', 'b0000000-0001-0000-0000-000000000003', 'fuel_mass_remaining_kg', 42.18, 'kg', 'NOMINAL', NOW());

    RAISE NOTICE 'Satellite Multi-Agent AI System demo state successfully reset to nominal baseline.';
END;
$$;
