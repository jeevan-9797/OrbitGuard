# Satellite Multi-Agent AI System - Database Architecture

## Overview
This database architecture provides the relational and analytical telemetry backbone for autonomous satellite constellation operations, multi-agent fault detection, isolation, and recovery (FDIR), safety interlocks, and aerospace knowledge bases.

## Schema Architecture

### Core Tables (11)
- `satellites`: Fleet orbital parameters (NORAD ID, altitude, inclination, autonomy mode).
- `subsystems`: Subsystem hierarchy (EPS, ADCS, PROP, TCS, COMMS, OBC, PL).
- `telemetry`: High-frequency time-series sensor telemetry streams.
- `anomalies`: Anomaly detections, telemetry threshold breaches, and excursions.
- `incidents`: Flight director incident tracking, MTTR metrics, and root causes.
- `safety_rules`: Mission-critical safety interlocks (`SR-PWR-*`, `SR-ADCS-*`, `SR-PROP-*`, etc.).
- `agent_runs`: Swarm reasoning cycles and hypotheses (`primary_hypothesis`, `hypotheses`).
- `recovery_plans`: Multi-step recovery action proposals (`order`, `action_code`, `parameters`).
- `validations`: Byzantine and interlock consensus approvals.
- `command_executions`: On-orbit command dispatch logs and uplink acknowledgments.
- `audit_events`: Tamper-evident flight ledger audit trail.

### Knowledge & Configuration Tables (6)
- `action_catalog`: Pre-approved aerospace action primitives (`PWR_*`, `ADCS_*`, `TCS_*`, etc.).
- `operating_modes`: Flight operational modes (Safe Sun-Point, Payload Ops, Orbit Station-Keeping).
- `telemetry_baselines`: Statistical nominal bands (mean, std dev, min/max limits).
- `historical_incidents`: Past on-orbit case studies (`Orbit 1420`, `Orbit 2185`, etc.).
- `runbook_templates`: Standardized procedural contingency trees.
- `system_config`: Autonomous swarm configuration parameters.

## Verification
To run the automated schema and dataset verification suite:
```bash
python3 verify_database.py
```
