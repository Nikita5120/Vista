# DESIGN.md

## System Design

The system follows an event-driven architecture.

Video streams from store cameras are processed using YOLOv8 for person detection and ByteTrack for multi-object tracking.

Detected customer activity is converted into structured business events such as:

* ENTRY
* ZONE_ENTER
* BILLING_QUEUE_JOIN

Events are ingested through FastAPI and stored in SQLite for analytics.

The analytics layer computes visitor metrics, conversion metrics, queue analytics, and zone popularity.

Results are visualized through a Streamlit dashboard.

## AI-Assisted Decisions

AI assistance was used for:

* Architecture planning
* API design guidance
* Documentation generation
* Dashboard design suggestions
* Event schema interpretation

Final implementation, debugging, testing, and integration were performed manually and validated through execution on provided sample videos.

## Scalability

The architecture is modular and supports additional cameras and event types without major redesign.
