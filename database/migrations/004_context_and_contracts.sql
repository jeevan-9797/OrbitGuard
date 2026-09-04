-- ============================================================================
-- Migration 004: Context Aggregator & AI/ML Contract Functions
-- File: database/migrations/004_context_and_contracts.sql
-- Implements build_incident_context() for compact, token-efficient LLM prompts
-- ============================================================================

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
    v_result JSONB;
BEGIN
    -- 1. Fetch Incident Header
    SELECT * INTO v_incident
    FROM incidents
    WHERE id = p_incident_id;

    IF NOT FOUND THEN
        RETURN jsonb_build_object('error', 'Incident not found', 'incident_id', p_incident_id);
    END IF;

    -- 2. Fetch Satellite Info
    SELECT * INTO v_satellite
    FROM satellites
    WHERE id = v_incident.satellite_id;

    -- 3. Fetch Associated Anomaly & Subsystem
    SELECT * INTO v_anomaly
    FROM anomalies
    WHERE id = v_incident.anomaly_id;

    IF v_anomaly.subsystem_id IS NOT NULL THEN
        SELECT * INTO v_subsystem
        FROM subsystems
        WHERE id = v_anomaly.subsystem_id;
    END IF;

    -- 4. Calculate Metric Deviations against Baselines
    WITH latest_readings AS (
        SELECT DISTINCT ON (metric)
            metric,
            value AS current_value,
            unit,
            quality,
            timestamp
        FROM telemetry
        WHERE satellite_id = v_incident.satellite_id
          AND timestamp >= NOW() - INTERVAL '30 minutes'
        ORDER BY metric, timestamp DESC
    ),
    metric_analysis AS (
        SELECT 
            lr.metric,
            lr.current_value,
            lr.unit,
            lr.quality,
            tb.min_val AS baseline_min,
            tb.max_val AS baseline_max,
            tb.mean AS baseline_mean,
            tb.stddev AS baseline_stddev,
            ROUND(
                CASE 
                    WHEN tb.stddev IS NOT NULL AND tb.stddev > 0 
                    THEN ((lr.current_value - tb.mean) / tb.stddev)::numeric 
                    ELSE 0::numeric 
                END, 2
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
                'metric', metric,
                'current_value', current_value,
                'unit', unit,
                'quality', quality,
                'range_status', range_status,
                'baseline', jsonb_build_object('min', baseline_min, 'max', baseline_max, 'mean', baseline_mean),
                'z_score', z_score
            )
        ), 
        '[]'::jsonb
    ) INTO v_telemetry_deviations
    FROM metric_analysis;

    -- 5. Calculate Aggregate Trends (peaks, averages over last 15 min window)
    WITH agg_stats AS (
        SELECT 
            metric,
            ROUND(MIN(value)::numeric, 2) AS min_15m,
            ROUND(MAX(value)::numeric, 2) AS max_15m,
            ROUND(AVG(value)::numeric, 2) AS avg_15m,
            COUNT(*) AS sample_count
        FROM telemetry
        WHERE satellite_id = v_incident.satellite_id
          AND timestamp >= NOW() - INTERVAL '15 minutes'
        GROUP BY metric
    )
    SELECT COALESCE(
        jsonb_object_agg(
            metric,
            jsonb_build_object('min', min_15m, 'max', max_15m, 'avg', avg_15m, 'samples', sample_count)
        ),
        '{}'::jsonb
    ) INTO v_recent_trends
    FROM agg_stats;

    -- 6. Retrieve Similar Historical Incidents
    SELECT COALESCE(
        jsonb_agg(
            jsonb_build_object(
                'scenario', scenario,
                'anomaly_type', anomaly_type,
                'diagnosis', diagnosis,
                'resolution', resolution
            )
        ),
        '[]'::jsonb
    ) INTO v_similar_cases
    FROM (
        SELECT scenario, anomaly_type, diagnosis, resolution
        FROM historical_incidents
        WHERE v_anomaly.type IS NOT NULL AND anomaly_type = v_anomaly.type
        LIMIT 3
    ) sub;

    -- 7. Retrieve Allowed Action Catalog for Current Mode
    SELECT COALESCE(
        jsonb_agg(
            jsonb_build_object(
                'action_code', action_code,
                'description', description,
                'preconditions', preconditions,
                'risk_level', risk_level
            )
        ),
        '[]'::jsonb
    ) INTO v_allowed_actions
    FROM action_catalog
    WHERE enabled = TRUE;

    -- 8. Assemble Compact Structured Output
    v_result := jsonb_build_object(
        'incident', jsonb_build_object(
            'id', v_incident.id,
            'title', v_incident.title,
            'state', v_incident.state,
            'priority', v_incident.priority,
            'severity', v_incident.severity,
            'opened_at', v_incident.opened_at
        ),
        'satellite', jsonb_build_object(
            'id', v_satellite.id,
            'name', v_satellite.name,
            'mode', v_satellite.mode,
            'risk_score', v_satellite.risk_score
        ),
        'subsystem', CASE 
            WHEN v_subsystem.id IS NOT NULL 
            THEN jsonb_build_object('name', v_subsystem.name, 'health_score', v_subsystem.health_score, 'status', v_subsystem.status)
            ELSE NULL 
        END,
        'anomaly', CASE 
            WHEN v_anomaly.id IS NOT NULL 
            THEN jsonb_build_object('type', v_anomaly.type, 'severity', v_anomaly.severity, 'evidence', v_anomaly.evidence, 'started_at', v_anomaly.started_at)
            ELSE NULL 
        END,
        'metric_deviations', v_telemetry_deviations,
        'recent_trends_15m', v_recent_trends,
        'similar_historical_cases', v_similar_cases,
        'action_catalog', v_allowed_actions
    );

    RETURN v_result;
END;
$$;
