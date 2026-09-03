import json
import hashlib
import sys
from pathlib import Path

from ai_ml.detector.detector import detect_anomalies


# ============================================================
# TELEMETRY LOADING
# ============================================================

def load_telemetry(file_name):
    file_path = Path("data/telemetry") / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Telemetry file not found: {file_path}"
        )

    with open(file_path, "r") as file:
        return json.load(file)


# ============================================================
# INCIDENT ID
# ============================================================

def generate_incident_id(satellite_id, timestamp):
    """
    Generate a deterministic incident ID from satellite + timestamp.
    The same telemetry event always produces the same ID.
    """

    raw = f"{satellite_id}:{timestamp}"

    digest = hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()[:6].upper()

    return f"INC-{digest}"


# ============================================================
# TELEMETRY MAPPING
# ============================================================

def map_telemetry_to_backend(telemetry):
    """
    Convert our AIML telemetry format into the backend telemetry format.

    IMPORTANT:
    We only send values that actually exist.
    We do NOT fabricate missing telemetry.
    """

    mapped = {}

    # Direct mappings
    if "temperature" in telemetry:
        mapped["battery_temp"] = telemetry["temperature"]

    if "battery_voltage" in telemetry:
        mapped["battery_voltage"] = telemetry["battery_voltage"]

    if "reaction_wheel_rpm" in telemetry:
        mapped["wheel_speed"] = telemetry["reaction_wheel_rpm"]

    if "solar_power" in telemetry:
        mapped["solar_power"] = telemetry["solar_power"]

    # These fields are intentionally NOT fabricated:
    #
    # battery_soc
    # attitude_error
    # comm_snr
    #
    # They will only be included if real telemetry is available.

    return mapped


# ============================================================
# BUILD TELEMETRY HISTORY
# ============================================================

def build_telemetry_history(telemetry_data):
    """
    Create the telemetry_history structure expected by the
    backend Diagnostic Agent.
    """

    telemetry = telemetry_data["telemetry"]

    mapped = map_telemetry_to_backend(telemetry)

    mapped["satellite_id"] = telemetry_data["satellite_id"]
    mapped["timestamp"] = telemetry_data["timestamp"]

    return [mapped]


# ============================================================
# BUILD ANOMALY EVENT
# ============================================================

def build_anomaly_event(telemetry_data, anomalies):
    """
    Convert detector output into the backend AnomalyEvent format.
    """

    satellite_id = telemetry_data["satellite_id"]
    timestamp = telemetry_data["timestamp"]

    incident_id = generate_incident_id(
        satellite_id,
        timestamp
    )

    # No anomaly detected
    if not anomalies:
        return None

    primary_anomaly = anomalies[0]

    evidence = [
        {
            "metric": primary_anomaly["parameter"],
            "value": primary_anomaly["value"],
            "threshold": primary_anomaly["threshold"]
        }
    ]

    anomaly_event = {
        "incident_id": incident_id,
        "satellite_id": satellite_id,
        "anomaly_type": primary_anomaly["type"],
        "severity": primary_anomaly["severity"],

        # Our detector is deterministic.
        # Therefore its detection confidence is 1.0.
        "confidence": 1.0,

        "status": "DETECTED",

        "started_at": timestamp,

        "evidence": evidence
    }

    return anomaly_event


# ============================================================
# BUILD COMPLETE BACKEND PAYLOAD
# ============================================================

def build_backend_payload(telemetry_data, anomalies):
    """
    Build the complete payload required by the backend
    Diagnostic Agent.
    """

    anomaly_event = build_anomaly_event(
        telemetry_data,
        anomalies
    )

    if anomaly_event is None:
        return None

    telemetry_history = build_telemetry_history(
        telemetry_data
    )

    payload = {
        "anomaly_event": anomaly_event,
        "telemetry_history": telemetry_history
    }

    return payload


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage:")
        print(
            "python -m ai_ml.integration.backend_adapter "
            "<filename>"
        )
        print()
        print("Example:")
        print(
            "python -m ai_ml.integration.backend_adapter "
            "low_battery.json"
        )
        sys.exit(1)

    file_name = sys.argv[1]

    try:
        telemetry_data = load_telemetry(file_name)

    except FileNotFoundError as error:
        print(f"ERROR: {error}")
        sys.exit(1)

    # Run our deterministic detector
    anomalies = detect_anomalies(
        telemetry_data
    )

    # Build backend-compatible payload
    payload = build_backend_payload(
        telemetry_data,
        anomalies
    )

    print("\n================================")
    print("     ORBITGUARD BACKEND ADAPTER")
    print("================================\n")

    if payload is None:
        print("No anomaly detected.")
        print("Nothing to send to the backend.")
        sys.exit(0)

    print("Backend Diagnostic Agent Payload:")
    print()

    print(
        json.dumps(
            payload,
            indent=2
        )
    )