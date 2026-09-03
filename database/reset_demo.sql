-- ============================================================================
-- Demo Reset Script & Function
-- File: database/reset_demo.sql
-- Resets the database to a clean, reproducible state for live demonstrations
-- ============================================================================

-- Function callable from backend or Supabase RPC: SELECT reset_demo();
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
SELECT reset_demo();
