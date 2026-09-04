import json
import sys
from pathlib import Path


# ==============================
# DETECTION THRESHOLDS
# ==============================

BATTERY_MIN = 20.0
TEMPERATURE_MAX = 80.0
CPU_LOAD_MAX = 95.0
REACTION_WHEEL_MAX = 6000.0


# ==============================
# ANOMALY DETECTOR
# ==============================

def detect_anomalies(telemetry_data):

    telemetry = telemetry_data["telemetry"]

    anomalies = []

    # Low battery
    if telemetry["battery_voltage"] < BATTERY_MIN:
        anomalies.append({
            "type": "LOW_BATTERY",
            "severity": "HIGH",
            "value": telemetry["battery_voltage"],
            "threshold": BATTERY_MIN,
            "parameter": "battery_voltage"
        })

    # High temperature
    if telemetry["temperature"] > TEMPERATURE_MAX:
        anomalies.append({
            "type": "HIGH_TEMPERATURE",
            "severity": "HIGH",
            "value": telemetry["temperature"],
            "threshold": TEMPERATURE_MAX,
            "parameter": "temperature"
        })

    # High CPU load
    if telemetry["cpu_load"] > CPU_LOAD_MAX:
        anomalies.append({
            "type": "HIGH_CPU_LOAD",
            "severity": "MEDIUM",
            "value": telemetry["cpu_load"],
            "threshold": CPU_LOAD_MAX,
            "parameter": "cpu_load"
        })

    # Reaction wheel overload
    if telemetry["reaction_wheel_rpm"] > REACTION_WHEEL_MAX:
        anomalies.append({
            "type": "REACTION_WHEEL_OVERLOAD",
            "severity": "HIGH",
            "value": telemetry["reaction_wheel_rpm"],
            "threshold": REACTION_WHEEL_MAX,
            "parameter": "reaction_wheel_rpm"
        })

    return anomalies


# ==============================
# LOAD TELEMETRY FILE
# ==============================

def load_telemetry(file_name):

    file_path = Path("data/telemetry") / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Telemetry file not found: {file_path}"
        )

    with open(file_path, "r") as file:
        return json.load(file)


# ==============================
# MAIN PROGRAM
# ==============================

if __name__ == "__main__":

    # Check command-line argument
    if len(sys.argv) != 2:

        print("Usage:")
        print("python ai_ml/detector/detector.py <filename>")
        print()
        print("Example:")
        print("python ai_ml/detector/detector.py low_battery.json")
        sys.exit(1)

    file_name = sys.argv[1]

    try:
        telemetry_data = load_telemetry(file_name)

    except FileNotFoundError as error:
        print(f"ERROR: {error}")
        sys.exit(1)

    anomalies = detect_anomalies(telemetry_data)

    print("\n================================")
    print("     ORBITGUARD DETECTOR")
    print("================================\n")

    print(f"Satellite: {telemetry_data['satellite_id']}")
    print(f"Timestamp: {telemetry_data['timestamp']}\n")

    if not anomalies:

        print("✓ No anomalies detected.")

    else:

        print(f"⚠ Detected {len(anomalies)} anomaly/anomalies:\n")

        for anomaly in anomalies:

            print(f"Type       : {anomaly['type']}")
            print(f"Severity   : {anomaly['severity']}")
            print(f"Parameter  : {anomaly['parameter']}")
            print(f"Value      : {anomaly['value']}")
            print(f"Threshold  : {anomaly['threshold']}")
            print()

    # Machine-readable output
    detector_output = {
        "satellite_id": telemetry_data["satellite_id"],
        "timestamp": telemetry_data["timestamp"],
        "anomaly_detected": len(anomalies) > 0,
        "anomalies": anomalies
    }

    print("=== DETECTOR JSON OUTPUT ===")
    print(json.dumps(detector_output, indent=2))