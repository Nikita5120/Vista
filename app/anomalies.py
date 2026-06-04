from datetime import datetime, UTC

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import (
    EventRecord,
    get_db,
)

from app.models import (
    Anomaly,
    AnomaliesResponse,
)

router = APIRouter(
    prefix="/anomalies",
    tags=["Anomalies"],
)


@router.get(
    "/{store_id}",
    response_model=AnomaliesResponse,
)
def detect_anomalies(
    store_id: str,
    db: Session = Depends(get_db),
):

    anomalies = []

    queue_abandons = (
        db.query(EventRecord)
        .filter(
            EventRecord.store_id == store_id,
            EventRecord.event_type ==
            "BILLING_QUEUE_ABANDON"
        )
        .count()
    )

    queue_joins = (
        db.query(EventRecord)
        .filter(
            EventRecord.store_id == store_id,
            EventRecord.event_type ==
            "BILLING_QUEUE_JOIN"
        )
        .count()
    )

    if queue_joins > 0:

        abandonment_rate = (
            queue_abandons /
            queue_joins
        ) * 100

        if abandonment_rate > 30:

            anomalies.append(
                Anomaly(
                    type="HIGH_ABANDONMENT",
                    severity="HIGH",
                    value=abandonment_rate,
                    detected_at=datetime.now(UTC),
                    suggested_action=
                    "Investigate checkout delays",
                )
            )

    zone_dwell = (
        db.query(
            EventRecord.zone_id,
            func.avg(
                EventRecord.dwell_ms
            )
        )
        .filter(
            EventRecord.store_id == store_id,
            EventRecord.zone_id.isnot(None),
        )
        .group_by(
            EventRecord.zone_id
        )
        .all()
    )

    for zone, avg_dwell in zone_dwell:

        if avg_dwell and avg_dwell > 600000:

            anomalies.append(
                Anomaly(
                    type="EXCESSIVE_DWELL",
                    severity="MEDIUM",
                    value=avg_dwell,
                    zone_id=zone,
                    detected_at=datetime.now(UTC),
                    suggested_action=
                    "Inspect customer congestion",
                )
            )

    return AnomaliesResponse(
        store_id=store_id,
        anomalies=anomalies,
    )
