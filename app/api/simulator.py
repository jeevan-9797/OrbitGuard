from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.detector import (
    analyse_telemetry,
    clear_incidents,
    get_open_incidents,
)

from app.simulator.telemetry import (
    generate_normal_telemetry,
    get_telemetry_history,
    inject_anomaly,
    reset_simulator,
)


router = APIRouter(
    prefix="/api",
    tags=["simulator"],
)


class InjectRequest(BaseModel):

    satellite_id: str = Field(
        ...,
        examples=["SAT-01"],
    )

    anomaly_type: str = Field(
        ...,
        examples=[
            "low_battery",
            "battery_overheat",
            "wheel_degradation",
        ],
        description=(
            "One of: low_battery, "
            "battery_overheat, wheel_degradation"
        ),
    )


@router.post("/simulate/reset")
def reset():

    reset_simulator()
    clear_incidents()

    return {
        "status": "reset",
    }


@router.post("/simulate/inject")
def inject(request: InjectRequest):

    try:

        result = inject_anomaly(
            request.satellite_id,
            request.anomaly_type,
        )

        return result

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get("/telemetry/{satellite_id}")
def get_telemetry(
    satellite_id: str,
    window: int = Query(
        default=30,
        ge=1,
        le=120,
    ),
    generate: int = Query(
        default=0,
        ge=0,
        le=120,
    ),
):

    generated_readings = []

    for _ in range(generate):

        snapshot = generate_normal_telemetry(
            satellite_id
        )

        generated_readings.append(
            snapshot
        )

        analyse_telemetry(
            snapshot
        )

    history = get_telemetry_history(
        satellite_id,
        limit=window,
    )

    anomalies = []

    for incident in get_open_incidents():

        if (
            incident.satellite_id
            == satellite_id
        ):
            anomalies.append(
                incident
            )

    return {
        "satellite_id": satellite_id,
        "readings": len(
            generated_readings
        ),
        "telemetry": history,
        "anomalies_detected": [
            anomaly.model_dump(
                mode="json"
            )
            for anomaly in anomalies
        ],
        "open_incidents": [
            incident.model_dump(
                mode="json"
            )
            for incident in anomalies
        ],
    }