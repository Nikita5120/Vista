from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import (
    EventRecord,
    get_db,
)

from app.models import (
    HeatmapResponse,
    HeatmapZone,
)

router = APIRouter(
    prefix="/heatmap",
    tags=["Heatmap"],
)


@router.get(
    "/{store_id}",
    response_model=HeatmapResponse,
)
def get_heatmap(
    store_id: str,
    db: Session = Depends(get_db),
):

    rows = (
        db.query(
            EventRecord.zone_id,
            func.count(EventRecord.event_id),
            func.avg(EventRecord.dwell_ms),
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

    max_visits = max(
        [r[1] for r in rows],
        default=1
    )

    zones = []

    for zone_id, visits, avg_dwell in rows:

        score = int(
            (visits / max_visits) * 100
        )

        zones.append(
            HeatmapZone(
                zone_id=zone_id,
                visit_count=visits,
                avg_dwell_ms=round(
                    avg_dwell or 0,
                    2
                ),
                normalised_score=score,
            )
        )

    return HeatmapResponse(
        store_id=store_id,
        data_confidence="HIGH",
        zones=zones,
    )