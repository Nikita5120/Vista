# CHOICES.md

## Model Selection

### YOLOv8

Selected because it provides:

* Fast inference
* Strong person detection performance
* Easy deployment

### ByteTrack

Selected because it provides:

* Stable multi-object tracking
* Identity preservation across frames
* Real-time performance

## Event Schema Design

The provided event schema was adopted to ensure compatibility with evaluation requirements.

Generated events include:

* ENTRY
* ZONE_ENTER
* BILLING_QUEUE_JOIN

Each event contains:

* Visitor ID
* Timestamp
* Camera ID
* Store ID
* Confidence Score

## API Architecture

FastAPI was selected because:

* Lightweight
* High performance
* Automatic OpenAPI documentation
* Easy integration with analytics services

## Database Choice

SQLite was selected for:

* Simplicity
* Local execution
* Fast development and testing

The design can be migrated to PostgreSQL for production deployments.
