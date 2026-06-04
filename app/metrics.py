from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.db import (
    EventRecord,
    POSTransaction,
    get_db,
)

from app.models import MetricsResponse

router = APIRouter(
    prefix="/metrics",
    tags=["Metrics"]
)


@router.get(
    "/{store_id}",
    response_model=MetricsResponse,
)
def get_metrics(
    store_id: str,
    db: Session = Depends(get_db),
):

    unique_visitors = (
        db.query(
            func.count(
                func.distinct(
                    EventRecord.visitor_id
                )
            )
        )
        .filter(
            EventRecord.store_id == store_id
        )
        .scalar()
        or 0
    )

    converted_visitors = (
        db.query(
            func.count(
                func.distinct(
                    EventRecord.visitor_id
                )
            )
        )
        .filter(
            EventRecord.store_id == store_id,
            EventRecord.event_type ==
            "BILLING_QUEUE_JOIN"
        )
        .scalar()
        or 0
    )

    conversion_rate = 0.0

    if unique_visitors > 0:
        conversion_rate = (
            converted_visitors /
            unique_visitors
        ) * 100

    dwell_rows = (
        db.query(
            EventRecord.zone_id,
            func.avg(
                EventRecord.dwell_ms
            )
        )
        .filter(
            EventRecord.store_id == store_id,
            EventRecord.zone_id.isnot(None)
        )
        .group_by(
            EventRecord.zone_id
        )
        .all()
    )

    avg_dwell_ms_by_zone = {
        zone: round(avg or 0, 2)
        for zone, avg in dwell_rows
    }

    queue_depth = (
        db.query(
            func.max(
                EventRecord.queue_depth
            )
        )
        .filter(
            EventRecord.store_id == store_id
        )
        .scalar()
        or 0
    )

    joins = (
        db.query(EventRecord)
        .filter(
            EventRecord.store_id == store_id,
            EventRecord.event_type ==
            "BILLING_QUEUE_JOIN"
        )
        .count()
    )

    abandons = (
        db.query(EventRecord)
        .filter(
            EventRecord.store_id == store_id,
            EventRecord.event_type ==
            "BILLING_QUEUE_ABANDON"
        )
        .count()
    )

    abandonment_rate = 0.0

    if joins > 0:
        abandonment_rate = (
            abandons / joins
        ) * 100

    total_transactions = (
        db.query(
            POSTransaction
        )
        .filter(
            POSTransaction.store_id ==
            store_id
        )
        .count()
    )

    avg_basket_value = (
        db.query(
            func.avg(
                POSTransaction.basket_value_inr
            )
        )
        .filter(
            POSTransaction.store_id ==
            store_id
        )
        .scalar()
        or 0
    )

    return MetricsResponse(
        store_id=store_id,
        unique_visitors=unique_visitors,
        conversion_rate=round(
            conversion_rate,
            2
        ),
        avg_dwell_ms_by_zone=
        avg_dwell_ms_by_zone,
        queue_depth=queue_depth,
        abandonment_rate=round(
            abandonment_rate,
            2
        ),
        total_transactions=
        total_transactions,
        avg_basket_value=round(
            avg_basket_value,
            2
        ),
    )

@router.get("/zones/{store_id}")
def zones(
    store_id: str,
    db: Session = Depends(get_db),
):

    rows = (
        db.query(
            EventRecord.zone_id,
            func.count()
        )
        .filter(
            EventRecord.store_id == store_id,
            EventRecord.zone_id.isnot(None)
        )
        .group_by(
            EventRecord.zone_id
        )
        .all()
    )

    return [
        {
            "zone": zone,
            "visits": visits,
        }
        for zone, visits in rows
    ]
@router.get("/events/{store_id}")
def recent_events(
    store_id: str,
    db: Session = Depends(get_db)
):

    rows = (
        db.query(EventRecord)
        .filter(
            EventRecord.store_id == store_id
        )
        .order_by(
            EventRecord.timestamp.desc()
        )
        .limit(20)
        .all()
    )

    return [
        {
            "visitor": r.visitor_id,
            "event": r.event_type,
            "zone": r.zone_id,
            "time": str(r.timestamp)
        }
        for r in rows
    ]