-- ============================================================================
-- Seed: Knowledge Base (Action Catalog, Safety Rules, Historical Incidents)
-- Targets: 12 Actions (10-15 target), 12 Safety Rules (10-15 target), 7 Historical Cases (5-10 target)
-- ============================================================================

-- 1. Action Catalog (12 Actions: PWR_*, ADCS_*, TCS_*, COMMS_*, PL_*, OBC_*, EPS_*)
INSERT INTO action_catalog (action_code, subsystem_code, action_name, description, risk_level, default_parameters, is_reversible)
VALUES
    ('EPS_SHED_NON_ESSENTIAL', 'EPS', 'Shed Non-Essential Bus Loads', 'Disconnects secondary payloads and heaters to relieve battery discharge stress.', 'LOW', '{"subsystems": ["PL", "COMMS_HIGH_PWR"]}', TRUE),
    ('EPS_ENABLE_SOLAR_TRACK', 'EPS', 'Enable Solar Array Peak Tracking', 'Orients solar array gimbal drive to normal incidence vector.', 'LOW', '{"tracking_mode": "MAX_POWER"}', TRUE),
    ('PWR_REDUCE_PAYLOAD_DRAIN', 'EPS', 'Reduce Payload Power Draw', 'Throttles high-power optical/radar instruments to standby baseline.', 'LOW', '{"power_reduction_pct": 50}', TRUE),
    ('ADCS_DESATURATE_WHEELS', 'ADCS', 'Desaturate Reaction Wheels', 'Applies magnetic torquer pulses to dump accumulated angular momentum.', 'MEDIUM', '{"target_rpm": 1200, "duration_sec": 45}', TRUE),
    ('ADCS_SWITCH_STANDBY_IMU', 'ADCS', 'Switch to Standby Inertial Measurement Unit', 'Isolates degraded primary gyro and transitions attitude filter to IMU-B.', 'MEDIUM', '{"imu_channel": "IMU_B"}', TRUE),
    ('ADCS_ENTER_SUN_POINT', 'ADCS', 'Enter Safe Sun-Pointing Attitude', 'Commands body-axis slew toward solar ephemeris vector for power preservation.', 'LOW', '{"slew_rate_deg_s": 0.5}', TRUE),
    ('TCS_ACTIVATE_SUPPLEMENTAL_HEATER', 'TCS', 'Activate Supplemental Radiator Heaters', 'Energizes survival heater loop during deep eclipse to prevent fuel freezing.', 'LOW', '{"heater_zone": "HYDRAZINE_MANIFOLD", "target_temp_c": 15}', TRUE),
    ('TCS_SLEW_RADIATOR_SHADE', 'TCS', 'Slew Radiator Shade Panels', 'Adjusts reflective thermal louvers to prevent high Earth albedo overheating.', 'LOW', '{"louver_angle_deg": 45}', TRUE),
    ('COMMS_SWITCH_OMNI_ANTENNA', 'COMMS', 'Switch to Low-Gain Omni Antenna', 'Restores omnidirectional beacon in case of high-gain directional pointing loss.', 'LOW', '{"antenna": "LGA_NADIR"}', TRUE),
    ('COMMS_BOOST_TRANSMIT_POWER', 'COMMS', 'Boost Downlink RF Amplifier Power', 'Steps up travelling-wave tube amplifier during critical contingency pass.', 'MEDIUM', '{"power_level_dbm": 33}', TRUE),
    ('PL_POWER_CYCLE_INSTRUMENT', 'PL', 'Power Cycle Primary Science Payload', 'Executes hard power reset to clear latch-up or SEU condition on payload FPGA.', 'HIGH', '{"reboot_delay_sec": 10}', TRUE),
    ('OBC_FLUSH_WATCHDOG_FAULTS', 'OBC', 'Clear and Flush Watchdog Fault Counters', 'Resets non-critical soft fault latches after swarm consensus verification.', 'LOW', '{"counter_mask": "0xFFFF"}', FALSE)
ON CONFLICT (action_code) DO NOTHING;

-- 2. Safety Rules (12 Rules: SR-*)
INSERT INTO safety_rules (rule_code, rule_name, subsystem_code, condition_expr, enforcement_level, description)
VALUES
    ('SR-PWR-01', 'Battery State of Charge Lower Bound', 'EPS', 'battery_soc_pct >= 25.0', 'STRICT_INTERLOCK', 'Prevents payload operation if battery charge drops below safe survival threshold.'),
    ('SR-PWR-02', 'Maximum Continuous Bus Current', 'EPS', 'bus_current_amps <= 28.0', 'STRICT_INTERLOCK', 'Trips fast circuit breakers if total electrical load exceeds wiring rating.'),
    ('SR-ADCS-01', 'Maximum Reaction Wheel RPM', 'ADCS', 'reaction_wheel_rpm <= 4800', 'STRICT_INTERLOCK', 'Enforces maximum structural spin rate on reaction wheel flywheels to avoid bearing damage.'),
    ('SR-ADCS-02', 'Star Tracker Lunar Exclusion Angle', 'ADCS', 'star_tracker_sun_exclusion_deg >= 30.0', 'WARNING_FLAG', 'Prevents optical blindings from direct solar or lunar intrusion.'),
    ('SR-ADCS-03', 'Maximum Angular Slewing Rate', 'ADCS', 'angular_rate_deg_s <= 3.0', 'STRICT_INTERLOCK', 'Limits body slew rates to prevent structural flex excitation in solar arrays.'),
    ('SR-TCS-01', 'Battery Cell Temperature Upper Ceiling', 'TCS', 'battery_cell_temp_c <= 45.0', 'STRICT_INTERLOCK', 'Commands emergency load shedding if battery thermal runaway condition is threatened.'),
    ('SR-TCS-02', 'Propellant Line Minimum Freezing Margin', 'TCS', 'propellant_temp_c >= 5.0', 'STRICT_INTERLOCK', 'Requires survival heater engagement before monopropellant reaches solidification point.'),
    ('SR-PROP-01', 'Thruster Chamber Overpressure Inhibit', 'PROP', 'chamber_pressure_bar <= 22.0', 'STRICT_INTERLOCK', 'Locks out fuel injection valves if manifold pressure spikes above burst margin.'),
    ('SR-PROP-02', 'Simultaneous Dual Branch Isolation', 'PROP', 'active_branch_count >= 1', 'STRICT_INTERLOCK', 'Prohibits isolating both primary and redundant hydrazine manifold branches concurrently.'),
    ('SR-COMMS-01', 'Ground Contact RF Muting During Pyros', 'COMMS', 'rf_silence_flag == FALSE', 'WARNING_FLAG', 'Ensures high-gain transmitters do not induce EMI during ordinance or deployable events.'),
    ('SR-PL-01', 'Direct Sunlight Instrument Shutter Interlock', 'PL', 'camera_sun_pointing_angle_deg >= 45.0', 'STRICT_INTERLOCK', 'Maintains optical baffle doors closed during unfavorable solar aspect angles.'),
    ('SR-OBC-01', 'Autonomous Reconfiguration Rate Limiter', 'OBC', 'reconfigs_per_hour <= 3', 'STRICT_INTERLOCK', 'Prevents oscillating FDIR loops from cycling power repeatedly within a single orbit.')
ON CONFLICT (rule_code) DO NOTHING;

-- 3. Historical Incidents (7 Cases: 'Orbit ...')
INSERT INTO historical_incidents (orbit_number, case_code, subsystem_code, root_cause, resolution_summary, recovery_strategy, mttr_seconds, lessons_learned)
VALUES
    ('Orbit 1420', 'HIST-CASE-01', 'TCS', 'Thermal blanket degradation caused excessive heat leakage in eclipse.', 'Switched to redundant heater line HTR-2 and commanded 4-deg roll offset.', 'AUTONOMOUS_L4', 1.80, 'Multi-layer insulation requires orbital albedo model correction.'),
    ('Orbit 2185', 'HIST-CASE-02', 'ADCS', 'RW-2 bearing friction spike due to cold soak thermal gradient.', 'Injected 5-pulse oscillatory dithering to redistribute lubricant film.', 'AUTONOMOUS_L4', 3.20, 'Periodic bearing exercise routine added to orbit sunrise checklist.'),
    ('Orbit 3042', 'HIST-CASE-03', 'EPS', 'Solar array drive slip-ring micro-arcing causing voltage ripple.', 'Adjusted SADA step profile and synchronized clock to bus regulator.', 'AUTONOMOUS_L4', 2.40, 'Capacitive filtering added in avionics telemetry bridge.'),
    ('Orbit 4110', 'HIST-CASE-04', 'PROP', 'Upper thermosphere density surge caused unexpected 14m perigee drop.', 'Dispatched autonomous two-pulse RCS station-keeping burn (+0.22 m/s).', 'AUTONOMOUS_L4', 4.10, 'Coupled space weather Kp index feed into orbit predictor.'),
    ('Orbit 4890', 'HIST-CASE-05', 'OBC', 'Single-event upset in star tracker quaternions processing RAM.', 'Swarm consensus quorum rejected bogus attitude quaternion; switched to secondary STR.', 'AUTONOMOUS_L4', 0.65, 'Implemented triple modular redundancy voting across agent nodes.'),
    ('Orbit 5214', 'HIST-CASE-06', 'EPS', 'Battery cell #4 thermal excursion during high-beta angle sunlight pass.', 'Executed automated load shed and articulated array off-pointing by 8 degrees.', 'HITL_APPROVED', 6.80, 'Ground control verified safe recovery margin before re-enabling payload.'),
    ('Orbit 6105', 'HIST-CASE-07', 'COMMS', 'Transponder thermal frequency drift causing ground receiver lock loss.', 'Recalibrated local oscillator via onboard temperature lookup table.', 'AUTONOMOUS_L4', 1.40, 'Oscillator crystal drift model preloaded into agent knowledge base.')
ON CONFLICT (case_code) DO NOTHING;
