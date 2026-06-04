from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import (
    EventRecord,
    POSTransaction,
    get_db,
)

from app.models import (
    FunnelResponse,
    FunnelStage,
)

router = APIRouter(
    prefix="/funnel",
    tags=["Funnel"],
)


@router.get(
    "/{store_id}",
    response_model=FunnelResponse,
)
def get_funnel(
    store_id: str,
    db: Session = Depends(get_db),
):

    entries = (
        db.query(
            func.count(
                func.distinct(
                    EventRecord.visitor_id
                )
            )
        )
        .filter(
            EventRecord.store_id == store_id,
            EventRecord.event_type == "ENTRY",
        )
        .scalar()
        or 0
    )

    zone_visitors = (
        db.query(
            func.count(
                func.distinct(
                    EventRecord.visitor_id
                )
            )
        )
        .filter(
            EventRecord.store_id == store_id,
            EventRecord.event_type == "ZONE_ENTER",
        )
        .scalar()
        or 0
    )

    billing_visitors = (
        db.query(
            func.count(
                func.distinct(
                    EventRecord.visitor_id
                )
            )
        )
        .filter(
            EventRecord.store_id == store_id,
            EventRecord.event_type == "BILLING_QUEUE_JOIN",
        )
        .scalar()
        or 0
    )

    transactions = (
        db.query(
            POSTransaction
        )
        .filter(
            POSTransaction.store_id == store_id
        )
        .count()
    )

    def pct(current, previous):
        if previous == 0:
            return 0.0
        return round((current / previous) * 100, 2)

    stages = [
        FunnelStage(
            name="ENTRY",
            visitors=entries,
            dropoff_pct=0,
            conversion_pct=100,
        ),
        FunnelStage(
            name="ZONE_VISIT",
            visitors=zone_visitors,
            dropoff_pct=100 - pct(zone_visitors, entries),
            conversion_pct=pct(zone_visitors, entries),
        ),
        FunnelStage(
            name="BILLING_QUEUE",
            visitors=billing_visitors,
            dropoff_pct=100 - pct(billing_visitors, zone_visitors),
            conversion_pct=pct(billing_visitors, zone_visitors),
        ),
        FunnelStage(
            name="PURCHASE",
            visitors=transactions,
            dropoff_pct=100 - pct(transactions, billing_visitors),
            conversion_pct=pct(transactions, billing_visitors),
        ),
    ]

    return FunnelResponse(
        store_id=store_id,
        stages=stages,
    )