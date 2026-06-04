from __future__ import annotations

import json
import uuid
import portalocker
from pathlib import Path
from datetime import datetime, UTC
from typing import Optional

from pydantic import BaseModel, Field, field_validator


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


class EventMetadata(BaseModel):
    queue_depth: Optional[int] = None
    sku_zone: Optional[str] = None
    session_seq: int = Field(..., gt=0)


class StoreEvent(BaseModel):
    event_id: str
    store_id: str
    camera_id: str
    visitor_id: str

    event_type: str

    timestamp: datetime

    zone_id: Optional[str] = None

    dwell_ms: int = Field(default=0, ge=0)

    is_staff: bool = False

    confidence: float = Field(..., ge=0.0, le=1.0)

    metadata: EventMetadata

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, value: str) -> str:
        if value not in VALID_EVENT_TYPES:
            raise ValueError(
                f"Invalid event_type '{value}'. "
                f"Allowed: {sorted(VALID_EVENT_TYPES)}"
            )
        return value

    @field_validator("timestamp")
    @classmethod
    def ensure_utc_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware UTC")
        return value


def utc_now() -> datetime:
    return datetime.now(UTC)


def make_event(
    *,
    store_id: str,
    camera_id: str,
    visitor_id: str,
    event_type: str,
    confidence: float,
    session_seq: int,
    zone_id: str | None = None,
    dwell_ms: int = 0,
    is_staff: bool = False,
    queue_depth: int | None = None,
    sku_zone: str | None = None,
    timestamp: datetime | None = None,
) -> StoreEvent:
    """
    Factory function used throughout the pipeline.
    """

    if timestamp is None:
        timestamp = utc_now()

    return StoreEvent(
        event_id=str(uuid.uuid4()),
        store_id=store_id,
        camera_id=camera_id,
        visitor_id=visitor_id,
        event_type=event_type,
        timestamp=timestamp,
        zone_id=zone_id,
        dwell_ms=dwell_ms,
        is_staff=is_staff,
        confidence=confidence,
        metadata=EventMetadata(
            queue_depth=queue_depth,
            sku_zone=sku_zone,
            session_seq=session_seq,
        ),
    )


def event_to_json(event: StoreEvent) -> str:
    """
    Convert event to JSON string.
    """

    return json.dumps(
        event.model_dump(mode="json"),
        separators=(",", ":"),
    )


def write_event(
    event: StoreEvent,
    output_file: str | Path,
) -> None:

    output_path = Path(output_file)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_line = event_to_json(event)

    try:
        with portalocker.Lock(
            str(output_path),
            mode="a",
            timeout=10,
            encoding="utf-8",
        ) as fp:

            fp.write(json_line)
            fp.write("\n")
            fp.flush()

    except OSError as exc:
        raise RuntimeError(
            f"Failed writing event to {output_path}"
        ) from exc


def write_events(
    events: list[StoreEvent],
    output_file: str | Path,
) -> None:

    output_path = Path(output_file)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        with portalocker.Lock(
            str(output_path),
            mode="a",
            timeout=10,
            encoding="utf-8",
        ) as fp:

            for event in events:
                fp.write(event_to_json(event))
                fp.write("\n")

            fp.flush()

    except OSError as exc:
        raise RuntimeError(
            f"Failed writing batch events to {output_path}"
        ) from exc


if __name__ == "__main__":

    sample = make_event(
        store_id="STORE_001",
        camera_id="CAM_3_ENTRY",
        visitor_id="VIS_123",
        event_type="ENTRY",
        confidence=0.94,
        session_seq=1,
    )

    write_event(
        sample,
        "events.jsonl",
    )

    print("Sample event written.")