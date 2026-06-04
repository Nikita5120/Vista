from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import (
    EventRecord,
    get_db,
)

from app.models import (
    IngestRequest,
    IngestResponse,
)

router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


@router.post(
    "/ingest",
    response_model=IngestResponse,
)
def ingest_events(
    payload: IngestRequest,
    db: Session = Depends(get_db),
):

    accepted = 0
    rejected = 0
    duplicates = 0

    errors: list[str] = []

    for event in payload.events:

        try:

            existing = db.get(
                EventRecord,
                event.event_id,
            )

            if existing:
                duplicates += 1
                continue

            record = EventRecord(
                event_id=event.event_id,
                store_id=event.store_id,
                camera_id=event.camera_id,
                visitor_id=event.visitor_id,
                event_type=event.event_type,
                timestamp=event.timestamp,
                zone_id=event.zone_id,
                dwell_ms=event.dwell_ms,
                is_staff=event.is_staff,
                confidence=event.confidence,
                queue_depth=event.metadata.queue_depth,
                session_seq=event.metadata.session_seq,
            )

            db.add(record)

            accepted += 1

        except Exception as exc:

            rejected += 1

            errors.append(
                f"{event.event_id}: {str(exc)}"
            )

    db.commit()

    return IngestResponse(
        accepted=accepted,
        rejected=rejected,
        duplicates=duplicates,
        errors=errors,
    )