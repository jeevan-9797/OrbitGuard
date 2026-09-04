import json
import sys
import time
from pathlib import Path

import requests

from ai_ml.detector.detector import detect_anomalies


# ============================================================
# BACKEND CONFIGURATION
# ============================================================

BACKEND_URL = "http://127.0.0.1:8001"
SATELLITE_ID = "SAT-01"


# ============================================================
# LOAD AIML TELEMETRY
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
# MAP AIML ANOMALY TO BACKEND ANOMALY TYPE
# ============================================================

def map_anomaly_type(anomaly_type):

    mapping = {
        "HIGH_TEMPERATURE": "battery_overheat",
        "LOW_BATTERY": "low_battery",
        "REACTION_WHEEL_OVERLOAD": "wheel_degradation",
        "WHEEL_DEGRADATION": "wheel_degradation",
        "battery_overheat": "battery_overheat",
        "low_battery": "low_battery",
        "wheel_degradation": "wheel_degradation",
    }

    backend_anomaly = mapping.get(anomaly_type)

    if backend_anomaly is None:
        raise ValueError(
            f"Unsupported AIML anomaly type: "
            f"{anomaly_type}"
        )

    return backend_anomaly


# ============================================================
# CHECK BACKEND
# ============================================================

def check_backend():

    response = requests.get(
        f"{BACKEND_URL}/api/health",
        timeout=5,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# RESET BACKEND SIMULATOR
# ============================================================

def reset_backend():

    response = requests.post(
        f"{BACKEND_URL}/api/simulate/reset",
        timeout=5,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# INJECT ANOMALY
# ============================================================

def inject_anomaly(anomaly_type):

    backend_anomaly = map_anomaly_type(
        anomaly_type
    )

    payload = {
        "satellite_id": SATELLITE_ID,
        "anomaly_type": backend_anomaly,
    }

    response = requests.post(
        f"{BACKEND_URL}/api/simulate/inject",
        json=payload,
        timeout=5,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# GENERATE TELEMETRY
# ============================================================

def generate_telemetry():

    # Give the simulator time to apply
    # the injected scenario.
    time.sleep(1)

    response = requests.get(
        f"{BACKEND_URL}/api/telemetry/{SATELLITE_ID}",
        params={
            "window": 5,
            "generate": 5,
        },
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# GET INCIDENTS
# ============================================================

def get_incidents():

    response = requests.get(
        f"{BACKEND_URL}/api/incidents",
        timeout=5,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# ANALYZE INCIDENT
# ============================================================

def analyze_incident(incident_id):

    payload = {
        "incident_id": incident_id
    }

    response = requests.post(
        f"{BACKEND_URL}/api/incidents/analyze",
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# FIND LATEST INCIDENT
# ============================================================

def find_latest_incident(incidents):

    if not incidents:
        return None

    return incidents[0]


# ============================================================
# MAIN AIML → BACKEND PIPELINE
# ============================================================

def run_pipeline(file_name):

    print("\n========================================")
    print("      ORBITGUARD AIML PIPELINE")
    print("========================================\n")

    # --------------------------------------------------------
    # 1. Load AIML telemetry
    # --------------------------------------------------------

    print("[1/7] Loading AIML telemetry...")

    telemetry_data = load_telemetry(
        file_name
    )

    print(
        f"Satellite: "
        f"{telemetry_data['satellite_id']}"
    )

    # --------------------------------------------------------
    # 2. Run AIML detector
    # --------------------------------------------------------

    print(
        "\n[2/7] Running AIML anomaly detector..."
    )

    anomalies = detect_anomalies(
        telemetry_data
    )

    if not anomalies:

        print(
            "No anomaly detected by AIML."
        )

        print(
            "Pipeline stopped."
        )

        return

    primary_anomaly = anomalies[0]

    print(
        f"Detected: "
        f"{primary_anomaly['type']}"
    )

    print(
        f"Severity: "
        f"{primary_anomaly['severity']}"
    )

    print(
        f"Value: "
        f"{primary_anomaly['value']}"
    )

    print(
        f"Threshold: "
        f"{primary_anomaly['threshold']}"
    )

    # --------------------------------------------------------
    # 3. Check backend
    # --------------------------------------------------------

    print(
        "\n[3/7] Connecting to backend..."
    )

    health = check_backend()

    print(
        "Backend:",
        health,
    )

    # --------------------------------------------------------
    # 4. Reset backend simulator
    # --------------------------------------------------------

    print(
        "\n[4/7] Resetting backend simulator..."
    )

    reset_result = reset_backend()

    print(
        "Reset:",
        reset_result.get(
            "status",
            "unknown",
        ),
    )

    # --------------------------------------------------------
    # 5. Inject matching backend scenario
    # --------------------------------------------------------

    print(
        "\n[5/7] Injecting AIML anomaly into backend..."
    )

    injection_result = inject_anomaly(
        primary_anomaly["type"]
    )

    print(
        "Backend anomaly:",
        injection_result["anomaly_type"],
    )

    # --------------------------------------------------------
    # 6. Generate backend telemetry
    # --------------------------------------------------------

    print(
        "\n[6/7] Generating backend telemetry..."
    )

    telemetry_result = generate_telemetry()

    print(
        "Generated/returned readings:",
        telemetry_result["readings"],
    )

    print(
        "Backend anomalies detected:",
        len(
            telemetry_result[
                "anomalies_detected"
            ]
        ),
    )

    # --------------------------------------------------------
    # 7. Retrieve and analyze incident
    # --------------------------------------------------------

    print(
        "\n[7/7] Retrieving backend incident..."
    )

    incidents = get_incidents()

    incident = find_latest_incident(
        incidents
    )

    if incident is None:

        print(
            "\nERROR: Backend did not create "
            "an incident."
        )

        return

    incident_id = incident[
        "incident_id"
    ]

    print(
        f"Incident ID: {incident_id}"
    )

    print(
        "\nSending incident to Diagnostic Agent..."
    )

    analysis = analyze_incident(
        incident_id
    )

    print(
        "\n========================================"
    )

    print(
        "       ANALYSIS COMPLETE"
    )

    print(
        "========================================\n"
    )

    print(
        json.dumps(
            analysis,
            indent=2,
        )
    )


# ============================================================
# COMMAND LINE ENTRY POINT
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) != 2:

        print("Usage:")

        print(
            "python -m "
            "ai_ml.integration.backend_adapter "
            "<filename>"
        )

        print()

        print("Example:")

        print(
            "python -m "
            "ai_ml.integration.backend_adapter "
            "low_battery.json"
        )

        sys.exit(1)

    file_name = sys.argv[1]

    try:

        run_pipeline(file_name)

    except requests.exceptions.ConnectionError:

        print(
            "\nERROR: Could not connect to backend."
        )

        print(
            "Make sure the backend is running on "
            f"{BACKEND_URL}"
        )

        sys.exit(1)

    except requests.exceptions.HTTPError as error:

        print(
            "\nERROR: Backend returned an HTTP error:"
        )

        print(error)

        sys.exit(1)

    except FileNotFoundError as error:

        print(
            f"\nERROR: {error}"
        )

        sys.exit(1)

    except Exception as error:

        print(
            f"\nERROR: Pipeline failed: {error}"
        )

        sys.exit(1)