-- ============================================================================
-- Migration 004: Context Aggregation Functions and AI/ML Contracts
-- Implements build_incident_context() for real-time multi-agent reasoning
-- ============================================================================

CREATE OR REPLACE FUNCTION build_incident_context(p_incident_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_incident RECORD;
    v_satellite RECORD;
    v_trends JSONB;
    v_deviations JSONB;
    v_safety_violations JSONB;
    v_result JSONB;
BEGIN
    -- 1. Fetch incident metadata
    SELECT * INTO v_incident
    FROM incidents
    WHERE id = p_incident_id;

    IF NOT FOUND THEN
        RETURN jsonb_build_object('error', 'Incident not found');
    END IF;

    -- 2. Fetch associated satellite metadata
    SELECT * INTO v_satellite
    FROM satellites
    WHERE id = v_incident.satellite_id;

    -- 3. Calculate recent trends over the past 15 minutes window ('recent_trends_15m')
    SELECT jsonb_agg(sub)
    INTO v_trends
    FROM (
        SELECT 
            t.metric_name,
            ROUND(AVG(t.metric_value), 3) AS avg_value,
            ROUND(MIN(t.metric_value), 3) AS min_value,
            ROUND(MAX(t.metric_value), 3) AS max_value,
            ROUND(MAX(t.metric_value) - MIN(t.metric_value), 3) AS delta_spread,
            COUNT(*) AS sample_count
        FROM telemetry t
        WHERE t.satellite_id = v_incident.satellite_id
          AND t.captured_at >= (v_incident.opened_at - INTERVAL '15 minutes')
          AND t.captured_at <= v_incident.opened_at
        GROUP BY t.metric_name
    ) sub;

    -- 4. Calculate baseline deviations against established nominal bands ('metric_deviations')
    SELECT jsonb_agg(dev)
    INTO v_deviations
    FROM (
        SELECT 
            t.metric_name,
            ROUND(AVG(t.metric_value), 3) AS current_val,
            b.mean_val AS baseline_mean,
            b.min_nominal,
            b.max_nominal,
            CASE 
                WHEN AVG(t.metric_value) > b.max_nominal THEN ROUND(AVG(t.metric_value) - b.max_nominal, 3)
                WHEN AVG(t.metric_value) < b.min_nominal THEN ROUND(AVG(t.metric_value) - b.min_nominal, 3)
                ELSE 0.0
            END AS deviation_magnitude
        FROM telemetry t
        JOIN subsystems s ON t.subsystem_id = s.id
        LEFT JOIN telemetry_baselines b 
          ON s.subsystem_code = b.subsystem_code 
         AND t.metric_name = b.metric_name
        WHERE t.satellite_id = v_incident.satellite_id
          AND t.captured_at >= (v_incident.opened_at - INTERVAL '5 minutes')
        GROUP BY t.metric_name, b.mean_val, b.min_nominal, b.max_nominal
    ) dev;

    -- 5. Compile unified AI contract context object
    v_result := jsonb_build_object(
        'incident_id', v_incident.id,
        'incident_number', v_incident.incident_number,
        'satellite_name', v_satellite.name,
        'orbit_altitude_km', v_satellite.altitude_km,
        'opened_at', v_incident.opened_at,
        'state', v_incident.state,
        'recent_trends_15m', COALESCE(v_trends, '[]'::jsonb),
        'metric_deviations', COALESCE(v_deviations, '[]'::jsonb)
    );

    RETURN v_result;
END;
$$;
