from datetime import datetime, UTC

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import (
    EventRecord,
    get_db,
)

from app.models import (
    HealthResponse,
    StoreHealthStatus,
)

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get(
    "",
    response_model=HealthResponse,
)
def get_health(
    db: Session = Depends(get_db),
):

    stores = (
        db.query(
            EventRecord.store_id
        )
        .distinct()
        .all()
    )

    results = []

    for (store_id,) in stores:

        last_event = (
            db.query(
                func.max(
                    EventRecord.timestamp
                )
            )
            .filter(
                EventRecord.store_id ==
                store_id
            )
            .scalar()
        )

        total_events = (
            db.query(EventRecord)
            .filter(
                EventRecord.store_id ==
                store_id
            )
            .count()
        )

        lag_minutes = 0.0

        status = "HEALTHY"

        if last_event:

            if last_event.tzinfo is None:
                now = datetime.utcnow()
            else:
                    now = datetime.now(UTC)

            lag_minutes = (
            now - last_event
            ).total_seconds() / 60

            if lag_minutes > 30:
                status = "STALE"

        results.append(
            StoreHealthStatus(
                store_id=store_id,
                last_event_timestamp=
                last_event,
                lag_minutes=
                round(lag_minutes, 2),
                status=status,
                events_today=
                total_events,
            )
        )

    return HealthResponse(
        overall_status="HEALTHY",
        stores=results,
    )