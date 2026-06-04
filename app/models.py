from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ConfigDict,
)

VALID_EVENT_TYPES = {
    "ENTRY",
    "EXIT",
    "ZONE_ENTER",
    "ZONE_EXIT",
    "ZONE_DWELL",
    "BILLING_QUEUE_JOIN",
    "BILLING_QUEUE_ABANDON",
    "REENTRY",
}


# ============================================================
# Event Models
# ============================================================

class EventMetadata(BaseModel):
    queue_depth: Optional[int] = None
    sku_zone: Optional[str] = None
    session_seq: int = Field(..., gt=0)


class StoreEvent(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    event_id: str

    store_id: str

    camera_id: str

    visitor_id: str

    event_type: str

    timestamp: datetime

    zone_id: Optional[str] = None

    dwell_ms: int = Field(
        default=0,
        ge=0
    )

    is_staff: bool = False

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )

    metadata: EventMetadata

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str):

        if v not in VALID_EVENT_TYPES:
            raise ValueError(
                f"Invalid event_type '{v}'"
            )

        return v


# ============================================================
# Ingestion
# ============================================================

class IngestRequest(BaseModel):

    events: list[StoreEvent] = Field(
        max_length=500
    )


class IngestResponse(BaseModel):

    accepted: int

    rejected: int

    duplicates: int

    errors: list[str] = []


# ============================================================
# Metrics
# ============================================================

class MetricsResponse(BaseModel):

    store_id: str

    unique_visitors: int

    conversion_rate: float

    avg_dwell_ms_by_zone: dict[str, float]

    queue_depth: int

    abandonment_rate: float

    total_transactions: int

    avg_basket_value: float


# ============================================================
# Funnel
# ============================================================

class FunnelStage(BaseModel):

    name: str

    visitors: int

    dropoff_pct: float

    conversion_pct: float


class FunnelResponse(BaseModel):

    store_id: str

    stages: list[FunnelStage]


# ============================================================
# Heatmap
# ============================================================

class HeatmapZone(BaseModel):

    zone_id: str

    visit_count: int

    avg_dwell_ms: float

    normalised_score: int


class HeatmapResponse(BaseModel):

    store_id: str

    data_confidence: str

    zones: list[HeatmapZone]


# ============================================================
# Anomalies
# ============================================================

class Anomaly(BaseModel):

    type: str

    severity: str

    value: float

    detected_at: datetime

    suggested_action: str

    zone_id: Optional[str] = None


class AnomaliesResponse(BaseModel):

    store_id: str

    anomalies: list[Anomaly]


# ============================================================
# Health
# ============================================================

class StoreHealthStatus(BaseModel):

    store_id: str

    last_event_timestamp: Optional[datetime]

    lag_minutes: float

    status: str

    events_today: int


class HealthResponse(BaseModel):

    overall_status: str

    stores: list[StoreHealthStatus]