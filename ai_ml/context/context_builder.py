import json
import sys
from pathlib import Path


# ==========================================
# EXPECTED TELEMETRY RANGES
# ==========================================

EXPECTED_RANGES = {
    "battery_voltage": (22.0, 28.0),
    "temperature": (0.0, 80.0),
    "cpu_load": (0.0, 95.0),
    "reaction_wheel_rpm": (0.0, 6000.0),
}


# ==========================================
# LOAD TELEMETRY
# ==========================================

def load_telemetry(file_name):
    file_path = Path("data/telemetry") / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Telemetry file not found: {file_path}"
        )

    with open(file_path, "r") as file:
        return json.load(file)


# ==========================================
# LOAD PREVIOUS TELEMETRY
# ==========================================

def load_previous_telemetry():
    """
    Load the normal telemetry sample so that
    we can calculate changes/trends.
    """

    file_path = Path("data/telemetry_sample.json")

    if not file_path.exists():
        return None

    with open(file_path, "r") as file:
        return json.load(file)


# ==========================================
# BUILD TRENDS
# ==========================================

def build_trends(current, previous):
    trends = {}

    if previous is None:
        return trends

    current_telemetry = current["telemetry"]
    previous_telemetry = previous["telemetry"]

    for parameter in current_telemetry:

        if parameter not in previous_telemetry:
            continue

        current_value = current_telemetry[parameter]
        previous_value = previous_telemetry[parameter]

        # Only calculate trends for numeric values
        if not isinstance(current_value, (int, float)):
            continue

        if not isinstance(previous_value, (int, float)):
            continue

        change = current_value - previous_value

        if change > 0:
            direction = "increasing"
        elif change < 0:
            direction = "decreasing"
        else:
            direction = "stable"

        trends[parameter] = {
            "current": current_value,
            "previous": previous_value,
            "change": round(change, 3),
            "direction": direction
        }

    return trends


# ==========================================
# BUILD DEVIATIONS
# ==========================================

def build_deviations(telemetry):
    deviations = []

    for parameter, expected_range in EXPECTED_RANGES.items():

        if parameter not in telemetry:
            continue

        value = telemetry[parameter]

        minimum = expected_range[0]
        maximum = expected_range[1]

        if value < minimum:

            deviations.append({
                "parameter": parameter,
                "value": value,
                "expected_range": [
                    minimum,
                    maximum
                ],
                "deviation": "below_normal"
            })

        elif value > maximum:

            deviations.append({
                "parameter": parameter,
                "value": value,
                "expected_range": [
                    minimum,
                    maximum
                ],
                "deviation": "above_normal"
            })

    return deviations


# ==========================================
# BUILD POWER BALANCE
# ==========================================

def build_power_balance(telemetry):
    solar_power = telemetry.get("solar_power")
    power_consumption = telemetry.get("power_consumption")

    if solar_power is None or power_consumption is None:
        return None

    net_power = solar_power - power_consumption

    return {
        "solar_power": solar_power,
        "consumption": power_consumption,
        "net": round(net_power, 3)
    }


# ==========================================
# BUILD INCIDENT CONTEXT
# ==========================================

def build_incident_context(telemetry_data, anomalies):

    telemetry = telemetry_data["telemetry"]

    # Determine primary anomaly
    if anomalies:
        primary_anomaly = anomalies[0]

        incident_type = primary_anomaly["type"]
        severity = primary_anomaly["severity"]

    else:
        incident_type = "NONE"
        severity = "NONE"

    previous_telemetry = load_previous_telemetry()

    trends = build_trends(
        telemetry_data,
        previous_telemetry
    )

    deviations = build_deviations(telemetry)

    power_balance = build_power_balance(telemetry)

    context = {
        "satellite_id": telemetry_data["satellite_id"],

        "incident": {
            "type": incident_type,
            "severity": severity
        },

        "current_state": {
            "battery_voltage": telemetry.get("battery_voltage"),
            "battery_current": telemetry.get("battery_current"),
            "temperature": telemetry.get("temperature"),
            "cpu_load": telemetry.get("cpu_load"),
            "reaction_wheel_rpm": telemetry.get("reaction_wheel_rpm"),
            "solar_power": telemetry.get("solar_power"),
            "power_consumption": telemetry.get("power_consumption"),
            "communication_available": telemetry.get(
                "communication_available"
            )
        },

        "trends": trends,

        "power_balance": power_balance,

        "deviations": deviations,

        "recent_events": [
            f"{anomaly['type']} detected"
            for anomaly in anomalies
        ],

        "historical_evidence": []
    }

    return context


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    if len(sys.argv) != 2:

        print("Usage:")
        print(
            "python ai_ml/context/context_builder.py "
            "<filename>"
        )

        print()
        print("Example:")
        print(
            "python ai_ml/context/context_builder.py "
            "low_battery.json"
        )

        sys.exit(1)

    file_name = sys.argv[1]

    try:
        telemetry_data = load_telemetry(file_name)

    except FileNotFoundError as error:

        print(f"ERROR: {error}")
        sys.exit(1)

    # Import detector
    from ai_ml.detector.detector import detect_anomalies

    anomalies = detect_anomalies(telemetry_data)

    context = build_incident_context(
        telemetry_data,
        anomalies
    )

    print("\n================================")
    print("     ORBITGUARD CONTEXT BUILDER")
    print("================================\n")

    print(json.dumps(context, indent=2))